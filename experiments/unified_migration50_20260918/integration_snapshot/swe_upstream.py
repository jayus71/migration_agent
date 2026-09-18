"""Pinned SWE-agent 1.1.0 with native tools inside a kernel-restricted worker.

The native agent, default history processors, parser, editor, shell and submit
review run together in one persistent process. Only LLM requests and allowlisted
public-test requests cross to the host controller. This is deliberately a native
shell baseline, not a claim of identical tools to the five-tool controls.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import ctypes
import errno
import difflib
import hashlib
import io
import json
import os
from pathlib import Path
import selectors
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import threading
import tarfile
import time
from typing import Any

SWE_COMMIT = "0f3acafacabc0def8cc76b4e48acb4b6cf302cb9"
SWE_LABEL = "SWE-agent 1.1.0 + isolated native shell"


class SWEMessageTransport:
    """Preserve native history while adapting its wire format to Chat APIs.

    Upstream 1.1.0 predates DeepSeek thinking and drops reasoning_content when
    constructing history. Match actual responses by complete content/tool-call
    identity, in reverse chronological order, including tool-free assistants.
    No reasoning is reconstructed from parsed thoughts or other messages.
    """
    def __init__(self):
        self.responses: list[dict] = []

    @staticmethod
    def _message(message: dict) -> dict:
        result = copy.deepcopy(message)
        result.pop("cache_control", None)
        content = result.get("content")
        if isinstance(content, list):
            if any(not isinstance(part, dict) or part.get("type") != "text" or
                   not isinstance(part.get("text"), str) for part in content):
                raise ValueError("Native SWE transport expects text-only content blocks")
            result["content"] = "".join(part["text"] for part in content)
        return result

    @classmethod
    def _key(cls, message: dict) -> str:
        plain = cls._message(message)
        return json.dumps({"content": plain.get("content") or "",
                           "tool_calls": plain.get("tool_calls") or []}, sort_keys=True)

    def remember(self, message: dict) -> None:
        self.responses.append(copy.deepcopy(message))

    def prepare(self, messages: list[dict]) -> list[dict]:
        result = [self._message(item) for item in messages]
        cursor = len(self.responses)
        for item in reversed(result):
            if item.get("role") != "assistant":
                continue
            key = self._key(item)
            for index in range(cursor - 1, -1, -1):
                actual = self.responses[index]
                if self._key(actual) == key:
                    cursor = index
                    if "reasoning_content" in actual:
                        item["reasoning_content"] = actual["reasoning_content"]
                    break
        return result


def _dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _hashes(root: Path) -> dict[str, str]:
    paths = [root / "candidate.py"]
    paths += sorted((root / "torch4ms").rglob("*.py"))
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths if p.is_file() and not p.is_symlink()}


def _git(root: Path, *args: str, env: dict | None = None) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], env=env,
                            capture_output=True, text=True, timeout=30, check=True)
    return result.stdout.strip()


def _restrict_process_controls() -> None:
    """Prevent native shell children from signalling unrelated host processes.

    Signal zero remains available for pexpect liveness checks. The outside
    controller owns timeout termination of this worker's process group.
    """
    sec = ctypes.CDLL("libseccomp.so.2")
    class Compare(ctypes.Structure):
        _fields_ = [("arg", ctypes.c_uint), ("op", ctypes.c_int),
                    ("datum_a", ctypes.c_uint64), ("datum_b", ctypes.c_uint64)]
    sec.seccomp_init.argtypes = [ctypes.c_uint32]
    sec.seccomp_init.restype = ctypes.c_void_p
    sec.seccomp_rule_add_array.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int,
                                         ctypes.c_uint, ctypes.POINTER(Compare)]
    sec.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    sec.seccomp_load.argtypes = [ctypes.c_void_p]
    sec.seccomp_release.argtypes = [ctypes.c_void_p]
    ctx = sec.seccomp_init(0x7FFF0000)
    if not ctx:
        raise RuntimeError("Process-control seccomp initialization failed")
    try:
        for name, argument in (("kill", 1), ("tkill", 1), ("tgkill", 2), ("pidfd_send_signal", 1),
                ("rt_sigqueueinfo", None), ("rt_tgsigqueueinfo", None), ("pidfd_getfd", None),
                ("shmget", None), ("shmat", None), ("msgget", None), ("semget", None)):
            number = sec.seccomp_syscall_resolve_name(name.encode())
            if number < 0:
                continue
            comparison = Compare(argument or 0, 1, 0, 0)
            if sec.seccomp_rule_add_array(ctx, 0x00050000 | errno.EPERM, number,
                    0 if argument is None else 1, None if argument is None else ctypes.byref(comparison)) != 0:
                raise RuntimeError("Process-control seccomp rule failed")
        if sec.seccomp_load(ctx) != 0:
            raise RuntimeError("Process-control seccomp activation failed")
    finally:
        sec.seccomp_release(ctx)


def _descendants(parent: int) -> set[int]:
    """Enumerate the worker's process tree; never act on unrelated processes."""
    parents = {}
    for path in Path("/proc").iterdir():
        if not path.name.isdigit():
            continue
        try:
            fields = (path / "stat").read_text().rsplit(")", 1)[1].split()
            parents[int(path.name)] = int(fields[1])
        except (OSError, ValueError, IndexError):
            continue
    found = {parent}
    while True:
        expanded = found | {pid for pid, ppid in parents.items() if ppid in found}
        if expanded == found:
            return found
        found = expanded


def _pidfd_open(pid: int) -> int:
    # Older Conda Python builds omit os.pidfd_open despite a supporting kernel.
    libc = ctypes.CDLL(None, use_errno=True)
    fd = libc.syscall(434, pid, 0)
    if fd < 0:
        raise OSError(ctypes.get_errno(), "pidfd_open")
    return fd


def _pidfd_signal(fd: int, number: int) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.syscall(424, fd, number, 0, 0) < 0:
        raise OSError(ctypes.get_errno(), "pidfd_send_signal")


def _validate_workspace(root: Path) -> None:
    """Reject links/special files before a host verifier snapshots shell edits."""
    paths = [root / n for n in ("source.py", "candidate.py", "task.json")
             if (root / n).exists() or (root / n).is_symlink()]
    if not (root / "candidate.py").is_file() or not (root / "task.json").is_file():
        raise ValueError("Required public files are missing")
    for name in ("torch4ms", "scratch_tests"):
        base = root / name
        if base.is_symlink():
            raise ValueError("Public workspace contains a directory link")
        if not base.exists():
            continue
        paths.append(base)
        for directory, dirs, files in os.walk(base, followlinks=False):
            paths.extend(Path(directory) / n for n in dirs + files)
    for path in paths:
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
            raise ValueError("Public workspace contains a link or special file")
        if stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
            raise ValueError("Public workspace contains a hard-linked file")


def prepare_overlay(upstream: Path, destination: Path, private: Path) -> dict:
    """Export pristine pinned files, recording environment-only adaptations."""
    if _git(upstream, "rev-parse", "HEAD") != SWE_COMMIT:
        raise RuntimeError("SWE upstream must be pinned at " + SWE_COMMIT)
    destination.mkdir(parents=True, exist_ok=False)
    archive = subprocess.run(["git", "-C", str(upstream), "archive", "--format=tar", SWE_COMMIT,
                              "sweagent", "tools", "config"], capture_output=True, check=True, timeout=30).stdout
    selected = []
    with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
        for member in bundle.getmembers():
            target = destination / member.name
            if not target.resolve().is_relative_to(destination.resolve()):
                raise RuntimeError("Unexpected archive traversal")
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                raise RuntimeError("Unexpected non-file in SWE pinned source: " + member.name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(bundle.extractfile(member).read())
            target.chmod(member.mode)
            selected.append(member.name)
    (destination / "trajectories").mkdir()
    replacements = {
        "/root/model.patch": str(private / "model.patch"),
        "/root/tools": str(private / "tools"),
        "/root/state.json": str(private / "state.json"),
        "/root/.swe-agent-env": str(private / "registry.json"),
        "/root/.bashrc": str(private / "startup.sh"),
        "/tmp/sweagent_model.patch": str(private / "model.patch"),
        "/tmp/sweagent_tools": str(private / "tools"),
        "/tmp/sweagent_state.json": str(private / "state.json"),
        "/tmp/.swe-agent-env": str(private / "registry.json"),
        "/home/whj/.bashrc": str(private / "startup.sh"),
    }
    edits = []
    for name in selected:
        target = destination / name
        try:
            original = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        changed = original
        for old, new in replacements.items():
            changed = changed.replace(old, new)
        if name == "tools/edit_anthropic/install.sh":
            # Dependencies are preinstalled into a read-only vendor directory.
            changed = "python -c 'import tree_sitter, tree_sitter_languages'\n"
        if changed != original:
            target.write_text(changed, encoding="utf-8")
            edits.append({"path": name, "before_sha256": hashlib.sha256(original.encode()).hexdigest(),
                          "after_sha256": hashlib.sha256(changed.encode()).hexdigest(),
                          "diff": "".join(difflib.unified_diff(original.splitlines(True), changed.splitlines(True), fromfile=name, tofile=name))})
    return {"upstream_commit": SWE_COMMIT, "source_origin": "git archive of pinned commit; installed edits ignored",
            "installed_diff_ignored": _git(upstream, "diff", "HEAD", "--", "sweagent", "tools", "config"),
            "environment_edits": edits,
            "files_sha256": {n: hashlib.sha256((destination / n).read_bytes()).hexdigest() for n in selected}}


class SWEAgentNative:
    """Persistent upstream DefaultAgent; external feedback follows native submit.

    initialize performs setup only. The first repair call starts autonomous
    investigation and repair; subsequent calls append external acceptance
    feedback to the same native history. There is no per-stage call slicing.
    """
    label = SWE_LABEL
    method = "swe_native_isolated"

    def __init__(self, agent: Any, *, upstream_root: str | Path, python: str | Path,
                 target_python: str | Path, vendor: str | Path) -> None:
        if getattr(agent.config, "memory_policy", "native") != "native":
            raise ValueError("Native SWE-agent must retain its own history processing")
        self.agent = agent
        self.upstream = Path(upstream_root).resolve()
        self.python = Path(python).resolve()
        self.target_python = Path(target_python).resolve()
        self.vendor = Path(vendor).resolve()
        self.root = agent.tools.root
        self.private = agent.log_dir / "swe_private"
        self.overlay = agent.log_dir / "swe_upstream"
        self.process: subprocess.Popen | None = None
        self.selector: selectors.BaseSelector | None = None
        self.stderr = None
        self.pending = False
        self.last_error: str | None = None
        self.first_edit: dict | None = None
        self.attempt = 0
        self.events = 0
        self._paused: dict[int, int] = {}
        self._pty_pairs: list[tuple[int, int]] = []

    def usage(self) -> dict:
        return self.agent.usage()

    def _record(self, kind: str, data: dict) -> None:
        self.events += 1
        _dump(self.agent.log_dir / f"swe_event_{self.events:04d}_{kind}.json", data)

    def _send(self, value: dict) -> None:
        assert self.process and self.process.stdin
        self.process.stdin.write(json.dumps(value, ensure_ascii=False) + "\n")
        self.process.stdin.flush()

    def pause(self) -> None:
        """Freeze all native descendants while outside acceptance reads files."""
        if not self.process or self.process.poll() is not None:
            return
        for _ in range(16):
            new = _descendants(self.process.pid) - self._paused.keys()
            if not new:
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline:
                    states = []
                    for pid in self._paused:
                        try:
                            states.append((Path("/proc") / str(pid) / "stat").read_text().rsplit(")", 1)[1].split()[0])
                        except FileNotFoundError:
                            pass
                    if all(state in {"T", "t", "Z", "X"} for state in states):
                        return
                    time.sleep(.005)
                raise RuntimeError("Native worker did not acknowledge process freeze")
            parents = {}
            for pid in new:
                try:
                    parents[pid] = int((Path('/proc') / str(pid) / 'stat').read_text().rsplit(')', 1)[1].split()[1])
                except (OSError, ValueError, IndexError):
                    pass
            def depth(pid):
                visited = set()
                while pid in parents and pid not in visited:
                    visited.add(pid)
                    pid = parents[pid]
                return len(visited)
            # Stop waiting parents before children; otherwise bash can consume
            # a child's stop notification before its own SIGSTOP takes effect.
            for pid in sorted(new, key=depth):
                try:
                    fd = _pidfd_open(pid)
                    _pidfd_signal(fd, signal.SIGSTOP)
                    self._paused[pid] = fd
                    deadline = time.monotonic() + 2
                    while True:
                        try:
                            state = (Path('/proc') / str(pid) / 'stat').read_text().rsplit(')', 1)[1].split()[0]
                        except FileNotFoundError:
                            break
                        if state in {'T', 't', 'Z', 'X'}:
                            break
                        if time.monotonic() >= deadline:
                            raise RuntimeError('Native process did not acknowledge suspension')
                        time.sleep(.001)
                except ProcessLookupError:
                    continue
        raise RuntimeError("Native worker process tree did not stabilize")

    def resume(self) -> None:
        # Resume descendants before their waiting parents. A shell resumed
        # while a foreground child is still stopped can report a stopped job
        # and return 128 + SIGSTOP before the public-test output arrives.
        parents = {}
        for pid in self._paused:
            try:
                parents[pid] = int((Path("/proc") / str(pid) / "stat").read_text().rsplit(")", 1)[1].split()[1])
            except (OSError, ValueError, IndexError):
                pass
        def depth(pid):
            ancestors = set()
            while pid in parents and pid not in ancestors:
                ancestors.add(pid)
                pid = parents[pid]
            return len(ancestors)
        for pid in sorted(self._paused, key=depth, reverse=True):
            fd = self._paused[pid]
            try:
                _pidfd_signal(fd, signal.SIGCONT)
                deadline = time.monotonic() + 2
                while True:
                    try:
                        state = (Path('/proc') / str(pid) / 'stat').read_text().rsplit(')', 1)[1].split()[0]
                    except FileNotFoundError:
                        break
                    if state not in {'T', 't'}:
                        break
                    if time.monotonic() >= deadline:
                        raise RuntimeError('Native process did not acknowledge continuation')
                    time.sleep(.001)
            except ProcessLookupError:
                pass
            finally:
                os.close(fd)
        self._paused.clear()

    def _prepare(self, observation: dict) -> list[str]:
        from .sandbox import runtime_reads
        self.private.mkdir(parents=True, exist_ok=False)
        for name in ("tools", "tmp", "native_trajectory", "bin"):
            (self.private / name).mkdir()
        self.manifest = prepare_overlay(self.upstream, self.overlay, self.private)
        self.manifest.update({"method": self.method, "label": self.label,
            "tools": "upstream native bash, file editor, submit review; allowlisted public test bridge",
            "history": "upstream default.yaml history_processors; complete persistent native history",
            "provider_transport": "lossless text-block joining; cache metadata removed on wire only; actual assistant reasoning_content restored from complete response identities",
            "response_handling": "native parser and native requery handling receive provider content and tool_calls unchanged; no adapter truncation recovery",
            "additional_prompt": "public task/backend contract and actual execution-interface description only; no classification, health encouragement or investigation strategy",
            "public_test_process_control": "freeze complete process tree for verification; resume descendants before their waiting parents",
            "checkpoints": "native submission followed by external feedback, at most four; no stage call quota",
            "diagnosis": "pre-edit trajectory snapshot at first observed production change",
            "isolation": "entire native worker starts under Landlock and seccomp before upstream imports"})
        _dump(self.agent.log_dir / "baseline_manifest.json", self.manifest)
        # A new anonymous Git history contains only public files, never the
        # original repository's fault commits, branches, remotes or patch index.
        repo = self.private / "repo.git"
        _git(self.root, "init", "--bare", str(repo))
        env = {"PATH": "/usr/bin:/bin", "GIT_DIR": str(repo), "GIT_WORK_TREE": str(self.root),
               "GIT_AUTHOR_NAME": "Public task", "GIT_AUTHOR_EMAIL": "task@invalid",
               "GIT_COMMITTER_NAME": "Public task", "GIT_COMMITTER_EMAIL": "task@invalid"}
        (repo / "info/exclude").write_text(".runtime/\n.git/\n__pycache__/\n*.pyc\n")
        names = [n for n in ("source.py", "candidate.py", "task.json", "torch4ms", "scratch_tests") if (self.root / n).exists()]
        _git(self.root, "add", "--", *names, env=env)
        _git(self.root, "commit", "-m", "Public task snapshot", env=env)
        (self.private / "startup.sh").write_text("")
        for name in ("requests.fifo", "responses.fifo"):
            os.mkfifo(self.private / name, 0o600)
        helper = self.private / "bin/run_public_test"
        helper.write_text("#!" + str(self.python) + "\n" + _PUBLIC_HELPER.replace("BRIDGE_DIRECTORY", repr(str(self.private))))
        helper.chmod(0o700)
        public_spec = json.loads((self.root / "task.json").read_text())
        config = {"workspace": str(self.root), "private": str(self.private), "overlay": str(self.overlay),
                  "observation": observation, "target_python": str(self.target_python),
                  "task_kind": public_spec.get("task_kind", "framework_migration"),
                  "has_source": (self.root / "source.py").exists(),
                  "model": self.agent.config.model or "shared-model", "named_tests": sorted(self.agent.tools.named_tests)}
        self._pty_pairs = [os.openpty() for _ in range(4)]
        config["pty_pairs"] = self._pty_pairs
        config_path = self.agent.log_dir / "swe_worker_config.json"
        _dump(config_path, config)
        reads = runtime_reads(self.python) + runtime_reads(self.target_python) + [str(self.root), str(self.overlay),
                 str(self.vendor), str(Path(__file__).resolve()), str(config_path)]
        writes = [str(self.private), str(self.root / "candidate.py"), str(self.root / "torch4ms"),
                  str(self.root / "scratch_tests"), "/dev/null", "/dev/urandom", "/dev/random"]
        sandbox = Path(__file__).with_name("sandbox.py")
        self.child_env = {"PATH": str(self.private / "bin") + ":" + str(self.python.parent) + ":/usr/bin:/bin",
            "PYTHONPATH": str(self.root) + ":" + str(self.overlay) + ":" + str(self.vendor), "PYTHONDONTWRITEBYTECODE": "1",
            "TMPDIR": str(self.private / "tmp"), "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
            "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "TOKENIZERS_PARALLELISM": "false",
            "MS_CACHE_PATH": str(self.private / "tmp"), "GLOG_logtostderr": "1", "LITELLM_LOCAL_MODEL_COST_MAP": "True",
            "SWE_AGENT_CONFIG_ROOT": str(self.overlay), "SWE_AGENT_TRAJECTORY_DIR": str(self.private / "native_trajectory"),
            "GIT_DIR": str(repo), "GIT_WORK_TREE": str(self.root), "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null"}
        return [str(self.python), str(sandbox), "--read", *reads, "--write", *writes,
                "--exec", str(self.python), str(Path(__file__).resolve()), "--worker", str(config_path)]

    def _serve(self) -> dict:
        from .agent import BudgetExhausted
        assert self.process and self.process.stdout and self.selector
        while True:
            remaining = self.agent.remaining_seconds()
            if remaining <= 0:
                self.last_error = "time_budget_exhausted"
                self.close()
                return {"kind": "failed", "status": self.last_error}
            if not self.selector.select(timeout=min(remaining, 1.0)):
                if self.process.poll() is not None:
                    return {"kind": "failed", "status": self.last_error or "worker_exit"}
                continue
            line = self.process.stdout.readline()
            if not line:
                return {"kind": "failed", "status": self.last_error or "worker_exit"}
            try:
                packet = json.loads(line)
            except ValueError:
                self._record("nonprotocol_stdout", {"text": line[:8000]})
                continue
            kind, data = packet.get("kind"), packet.get("data", {})
            self._record(str(kind), data)
            if kind in {"ready", "checkpoint", "failed"}:
                self.pending = kind != "failed"
                self.pause()
                try:
                    _validate_workspace(self.root)
                except ValueError:
                    self.last_error = "invalid_workspace"
                    data["status"] = self.last_error
                return {"kind": kind, **data}
            if kind == "first_edit":
                self.first_edit = data
                self._send({"ok": True})
            elif kind == "model":
                try:
                    result = self.agent.complete(data["messages"], tool_schemas=data["tools"],
                                                 stage="swe_native", attempt=self.attempt)
                    self._send({"ok": True, "response": result})
                except BudgetExhausted as exc:
                    self.last_error = str(exc)
                    self._send({"ok": False, "error": self.last_error})
                except Exception:
                    self.last_error = "api_error"
                    self._send({"ok": False, "error": "api_error"})
            elif kind == "test":
                name = data.get("name")
                if name not in self.agent.tools.named_tests:
                    self._send({"ok": False, "error": "Unknown public test"})
                    continue
                try:
                    self.pause()
                    _validate_workspace(self.root)
                    result = self.agent.tools.execute("run_test", {"test": name},
                        remaining_seconds=self.agent.remaining_seconds())
                    response = {"ok": True, "result": result}
                except Exception as exc:
                    response = {"ok": False, "error": type(exc).__name__}
                finally:
                    self.resume()
                self._send(response)
            else:
                self._send({"ok": False, "error": "Unknown worker message"})

    def initialize(self, observation: dict) -> Any:
        from .agent import StageResult
        command = self._prepare(observation)
        self.stderr = (self.agent.log_dir / "swe_worker.stderr").open("w")
        self.process = subprocess.Popen(command, cwd=self.root, env=self.child_env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr, text=True, bufsize=1, start_new_session=True,
            pass_fds=tuple(fd for pair in self._pty_pairs for fd in pair))
        for pair in self._pty_pairs:
            for fd in pair:
                os.close(fd)
        self._pty_pairs = []
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        result = self._serve()
        return StageResult("ready" if result["kind"] == "ready" else result.get("status", "infrastructure_error"),
                           result, None, 0, self.usage(), [])

    def repair(self, observation: dict, attempt: int = 1) -> Any:
        from .agent import StageResult
        if attempt < 1 or attempt > 4:
            raise ValueError("At most four external submission checkpoints are permitted")
        if not self.pending:
            raise RuntimeError("Native SWE worker is not awaiting checkpoint feedback")
        self.attempt = attempt
        start, before = self.agent.calls, _hashes(self.root)
        self.pending = False
        self.resume()
        self._send({"continue": True, "observation": observation, "attempt": attempt})
        result = self._serve()
        after = _hashes(self.root)
        changed = sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))
        status = self.last_error or result.get("status", "completed")
        return StageResult(status, result, None, self.agent.calls - start, self.usage(), changed)

    def close(self) -> None:
        if self.process and self.process.poll() is None:
            self.pause()
            for pid, fd in self._paused.items():
                try:
                    _pidfd_signal(fd, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            self.process.wait(timeout=10)
        for fd in self._paused.values():
            os.close(fd)
        self._paused.clear()
        for pair in self._pty_pairs:
            for fd in pair:
                os.close(fd)
        self._pty_pairs = []
        if self.selector:
            self.selector.close()
        if self.stderr:
            self.stderr.close()


_PUBLIC_HELPER = '''import fcntl
import json
import sys
from pathlib import Path
directory = Path(BRIDGE_DIRECTORY)
with (directory / "bridge.lock").open("w") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    with (directory / "requests.fifo").open("w") as request:
        request.write(json.dumps({"name": sys.argv[1] if len(sys.argv) == 2 else ""}) + "\\n")
    with (directory / "responses.fifo").open() as response:
        print(response.readline().strip())
'''


def _worker(config: dict) -> None:
    """All of this executes after inherited filesystem/network restrictions."""
    protocol_out, protocol_in = sys.stdout, sys.stdin
    sys.stdout = sys.stderr
    lock = threading.Lock()
    # pexpect normally opens arbitrary /dev/pts entries. Supply dedicated PTYs
    # inherited from the controller so the sandbox grants no host tty paths.
    import pty
    pty_pairs = list(config["pty_pairs"])
    def isolated_pty_fork():
        if not pty_pairs:
            raise RuntimeError("Dedicated native shell PTY pool exhausted")
        master, slave = pty_pairs.pop(0)
        pid = os.fork()
        if pid == 0:
            os.close(master)
            os.login_tty(slave)
            return 0, -1
        os.close(slave)
        return pid, master
    pty.fork = isolated_pty_fork

    def rpc(kind: str, data: dict) -> dict:
        with lock:
            protocol_out.write(json.dumps({"kind": kind, "data": data}, ensure_ascii=False) + "\n")
            protocol_out.flush()
            line = protocol_in.readline()
            if not line:
                raise EOFError("Controller closed")
            return json.loads(line)

    from swerex.deployment.local import LocalDeployment
    from sweagent.agent.agents import DefaultAgent, DefaultAgentConfig
    from sweagent.agent.models import AbstractModel, GenericAPIModelConfig, InstanceStats, LiteLLMModel
    from sweagent.agent.problem_statement import TextProblemStatement
    from sweagent.environment.swe_env import SWEEnv
    from sweagent.tools.tools import ToolHandler
    from sweagent.utils.log import get_logger
    import yaml

    class SharedModel(AbstractModel):
        def __init__(self, tools):
            self.config = GenericAPIModelConfig(name=config["model"], per_instance_cost_limit=0)
            self.stats = InstanceStats()
            self.tools = tools
            self.logger = get_logger("shared-controller-model")
            self.transport = SWEMessageTransport()
            self.last_response = None

        def query(self, history, action_prompt="> "):
            native_messages = LiteLLMModel._history_to_messages(self, history)
            messages = self.transport.prepare(native_messages)
            answer = rpc("model", {"messages": messages, "native_messages": native_messages,
                                   "tools": self.tools.tools})
            if not answer.get("ok"):
                from sweagent.exceptions import CostLimitExceededError
                raise CostLimitExceededError(answer.get("error", "controller_error"))
            response = answer["response"]
            self.last_response = copy.deepcopy(response)
            usage = response.get("usage", {})
            self.stats.api_calls += 1
            self.stats.tokens_sent += usage.get("prompt_tokens", 0)
            self.stats.tokens_received += usage.get("completion_tokens", 0)
            message = response["choices"][0]["message"]
            self.transport.remember(message)
            return {"message": message.get("content") or "", "tool_calls": message.get("tool_calls")}

    private = Path(config["private"])
    def public_bridge():
        while True:
            try:
                with (private / "requests.fifo").open() as stream:
                    request = json.loads(stream.readline())
                name = request.get("name")
                answer = rpc("test", {"name": name}) if name in config["named_tests"] else {"ok": False, "error": "Unknown public test"}
                with (private / "responses.fifo").open("w") as stream:
                    stream.write(json.dumps(answer) + "\n")
            except (EOFError, BrokenPipeError):
                return
            except Exception:
                continue
    threading.Thread(target=public_bridge, daemon=True).start()
    raw = yaml.safe_load((Path(config["overlay"]) / "config/default.yaml").read_text())["agent"]
    raw["model"] = {"name": config["model"], "per_instance_cost_limit": 0}
    cfg = DefaultAgentConfig.model_validate(raw)
    native = DefaultAgent(templates=cfg.templates, tools=ToolHandler(cfg.tools),
        history_processors=cfg.history_processors, model=SharedModel(cfg.tools),
        max_requeries=cfg.max_requeries, action_sampler_config=cfg.action_sampler)
    env = SWEEnv(deployment=LocalDeployment(), repo=None,
                 post_startup_commands=["cd " + shlex.quote(config["workspace"]),
                                        "export ROOT=" + shlex.quote(config["workspace"])])
    env.start()
    migration = config["task_kind"] == "framework_migration"
    contract = ("This is a program migration task. " if migration else
                "This is a library unit task. ")
    contract += ("source.py and task.json define intended behavior. " if config["has_source"] else
                 "task.json defines the public task and acceptance contract. No reference implementation is supplied. ")
    if migration:
        declared = json.loads((Path(config['workspace']) / 'task.json').read_text()).get('target_framework', 'torch4ms/MindSpore')
        contract += (f"Target forward values, gradients and parameter updates must execute through {declared}; "
                     "preserve genuine target computation and public acceptance instrumentation. ")
    else:
        contract += "Preserve the public API and behavior specified by the task; do not manipulate acceptance instrumentation. "
    problem = (contract + "candidate.py and torch4ms are editable, while source.py and task.json are immutable. "
        "Scratch scripts are writable under scratch_tests. The target interpreter is " + config["target_python"] + ". "
        "Run the public verifier directly in bash, for example: run_public_test " + config["named_tests"][0] + ". "
        "Available test names are " + json.dumps(config["named_tests"]) + ". "
        "This command tests your current editable workspace through an external controller and returns real observations. "
        "The verifier implementation is outside the public workspace. "
        "The controller checks acceptance after native submit and returns observations for another attempt when needed. "
        "Public initial observation:\n" + json.dumps(config["observation"], ensure_ascii=False))
    native.setup(env=env, problem_statement=TextProblemStatement(text=problem, id="public-migration"),
                 output_dir=private / "native_trajectory")
    command = rpc("ready", {"status": "ready"})
    first_edit = False
    while command.get("continue"):
        attempt = command["attempt"]
        if attempt > 1:
            native._append_history({"role": "user", "content": "External acceptance observation after your submission:\n" +
                json.dumps(command["observation"], ensure_ascii=False),
                "agent": native.name, "message_type": "external_verifier_feedback"})
        while True:
            before = _hashes(Path(config["workspace"]))
            history_before = copy.deepcopy(native.history)
            step = native.step()
            after = _hashes(Path(config["workspace"]))
            if not first_edit and before != after:
                first_edit = True
                rpc("first_edit", {"history_before": history_before, "triggering_step": step.model_dump(),
                    "triggering_provider_response": native.model.last_response,
                    "before_hashes": before, "after_hashes": after, "attempt": attempt,
                    "scoring_note": "Model's recorded pre-edit reasoning; no category or location supplied"})
            native.save_trajectory()
            if step.done:
                command = rpc("checkpoint", {"status": step.exit_status, "history": native.history,
                    "trajectory": native.trajectory, "info": native.info, "attempt": attempt})
                break


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", type=Path, required=True)
    args = parser.parse_args()
    try:
        # Orphaned shell descendants stay attributable to this worker for
        # external freeze/cleanup, including children that create sessions.
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(36, 1, 0, 0, 0) != 0:  # PR_SET_CHILD_SUBREAPER
            raise OSError(ctypes.get_errno(), "PR_SET_CHILD_SUBREAPER")
        _restrict_process_controls()
        _worker(json.loads(args.worker.read_text()))
    except Exception:
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
