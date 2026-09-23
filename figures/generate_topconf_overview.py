#!/usr/bin/env python3
"""Generate an aesthetically stunning, top-conference quality method overview figure for LaDiM.

Aesthetic & Scientific Standards (ICLR / NeurIPS / ICML):
- NO top title banner (delegated to LaTeX caption).
- Handcrafted vector illustrations: cute AI agent robots for Translator, Verifier, Repair.
- Deterministic verification engine icon (precision gears + verification shield) for Orchestrator (NO LLM!).
- Highly restrained text & arrows: high signal-to-noise ratio, clean left-to-right flow, single feedback loop.
- Cross-framework, cross-language, repository-scale generalization clearly represented.
- Fully editable PowerPoint (.pptx) and vector PDF/PNG export.
"""
from pathlib import Path
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

ROOT = Path(__file__).resolve().parents[1]
SVG_PATH = ROOT / "figures/slim_v4_overview.svg"
PPTX_PATH = ROOT / "figures/hierarchical_feedback_architecture.pptx"

WIDTH = 1120
HEIGHT = 500

def get_robot_avatar_svg(cx, cy, scale=1.0, theme="blue"):
    """Generate a cute modern vector robot avatar for an LLM agent."""
    colors = {
        "blue": {"body": "#DBEAFE", "stroke": "#3B82F6", "visor": "#1E293B", "eye": "#60A5FA", "antenna": "#2563EB"},
        "indigo": {"body": "#E0E7FF", "stroke": "#6366F1", "visor": "#1E293B", "eye": "#818CF8", "antenna": "#4F46E5"},
        "green": {"body": "#DCFCE7", "stroke": "#10B981", "visor": "#1E293B", "eye": "#34D399", "antenna": "#059669"},
        "amber": {"body": "#FEF3C7", "stroke": "#F59E0B", "visor": "#1E293B", "eye": "#FBBF24", "antenna": "#D97706"},
    }[theme]
    
    s = f'''<g transform="translate({cx}, {cy}) scale({scale})">
  <!-- Antenna -->
  <line x1="0" y1="-16" x2="0" y2="-23" stroke="{colors['antenna']}" stroke-width="2" stroke-linecap="round"/>
  <circle cx="0" cy="-25" r="3" fill="{colors['antenna']}"/>
  <!-- Ears / Headphones -->
  <rect x="-19" y="-12" width="4" height="10" rx="2" fill="{colors['stroke']}"/>
  <rect x="15" y="-12" width="4" height="10" rx="2" fill="{colors['stroke']}"/>
  <!-- Head -->
  <rect x="-16" y="-17" width="32" height="22" rx="7" fill="{colors['body']}" stroke="{colors['stroke']}" stroke-width="1.8"/>
  <!-- Visor -->
  <rect x="-12" y="-13" width="24" height="13" rx="4" fill="{colors['visor']}"/>
  <!-- Glowing Eyes -->
  <circle cx="-6" cy="-6.5" r="2.2" fill="{colors['eye']}"/>
  <circle cx="6" cy="-6.5" r="2.2" fill="{colors['eye']}"/>
  <!-- Cute blush -->
  <circle cx="-9.5" cy="-2" r="1.2" fill="#F43F5E" opacity="0.6"/>
  <circle cx="9.5" cy="-2" r="1.2" fill="#F43F5E" opacity="0.6"/>
</g>'''
    return s

def get_engine_icon_svg(cx, cy, scale=1.0):
    """Generate a precision mechanical verification engine icon (Gears + Shield, NO robot!)."""
    return f'''<g transform="translate({cx}, {cy}) scale({scale})">
  <!-- Small background gear -->
  <circle cx="8" cy="-6" r="10" fill="#FEF3C7" stroke="#D97706" stroke-width="1.5" stroke-dasharray="3,2"/>
  <circle cx="8" cy="-6" r="4" fill="#F59E0B"/>
  <!-- Main gear -->
  <circle cx="-6" cy="-4" r="13" fill="#FFFBEB" stroke="#B45309" stroke-width="1.8" stroke-dasharray="4,2"/>
  <circle cx="-6" cy="-4" r="5" fill="#D97706"/>
  <!-- Verification Shield -->
  <path d="M 0 -2 L 11 3 L 11 11 C 11 17 0 21 0 21 C 0 21 -11 17 -11 11 L -11 3 Z" fill="#10B981" stroke="#047857" stroke-width="1.5"/>
  <!-- Checkmark inside shield -->
  <path d="M -5 9 L -1 13 L 5 6" fill="none" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
</g>'''

def generate_svg():
    """Build the clean, high-aesthetic publication SVG."""
    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}" style="font-family:\'Times New Roman\', \'Liberation Serif\', Times, serif;">')
    
    # Definitions: Gradients, Markers & Standard Filters
    s.append('''<defs>
  <marker id="arrow-slate" markerWidth="7" markerHeight="5" refX="6" refY="2.5" orient="auto">
    <polygon points="0 0, 7 2.5, 0 5" fill="#475569"/>
  </marker>
  <marker id="arrow-blue" markerWidth="7" markerHeight="5" refX="6" refY="2.5" orient="auto">
    <polygon points="0 0, 7 2.5, 0 5" fill="#2563EB"/>
  </marker>
  <marker id="arrow-green" markerWidth="7" markerHeight="5" refX="6" refY="2.5" orient="auto">
    <polygon points="0 0, 7 2.5, 0 5" fill="#059669"/>
  </marker>
  <marker id="arrow-amber" markerWidth="7" markerHeight="5" refX="6" refY="2.5" orient="auto">
    <polygon points="0 0, 7 2.5, 0 5" fill="#D97706"/>
  </marker>
  <marker id="arrow-purple" markerWidth="7" markerHeight="5" refX="6" refY="2.5" orient="auto">
    <polygon points="0 0, 7 2.5, 0 5" fill="#7C3AED"/>
  </marker>
  <filter id="shadow" x="-3%" y="-3%" width="106%" height="106%">
    <feGaussianBlur in="SourceAlpha" stdDeviation="2"/>
    <feOffset dx="0" dy="1.5" result="offsetblur"/>
    <feComponentTransfer>
      <feFuncA type="linear" slope="0.06"/>
    </feComponentTransfer>
    <feMerge> 
      <feMergeNode/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
</defs>''')

    # Background canvas
    s.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#FFFFFF"/>')

    # =========================================================================
    # ROW 1: MAIN MIGRATION PIPELINE (y: 20 to 275)
    # =========================================================================

    # 1. Source Codebase Card (x: 20, y: 20, w: 210, h: 255)
    s.append('''<!-- Card 1: Source Codebase -->
<g id="card-source" filter="url(#shadow)">
  <rect x="20" y="20" width="210" height="255" rx="8" ry="8" fill="#F8FAFC" stroke="#CBD5E1" stroke-width="1.4"/>
  <path d="M 20 28 Q 20 20 28 20 L 222 20 Q 230 20 230 28 L 230 52 L 20 52 Z" fill="#E2E8F0"/>
  <text x="32" y="41" font-size="13" font-weight="bold" fill="#0F172A">Source Codebase</text>
  <rect x="156" y="27" width="66" height="18" rx="4" ry="4" fill="#475569"/>
  <text x="189" y="40" font-size="9.5" font-weight="bold" fill="#FFFFFF" text-anchor="middle">(Ls, Fs)</text>

  <!-- Repository File Structure Mini-IDE Card -->
  <rect x="30" y="62" width="190" height="98" rx="5" ry="5" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1"/>
  <!-- File tab bar -->
  <rect x="30" y="62" width="190" height="20" rx="5" ry="5" fill="#F1F5F9"/>
  <text x="40" y="76" font-size="9" font-weight="bold" fill="#475569">📁 Repository P</text>
  <text x="135" y="76" font-size="8.5" fill="#64748B">Python / Java</text>
  <!-- Tree view lines -->
  <text x="38" y="97" font-size="9" fill="#475569">├── models/ (nn.Module / layers)</text>
  <text x="38" y="112" font-size="9" fill="#475569">├── train_step.py (forward &amp; loss)</text>
  <text x="38" y="127" font-size="9" fill="#475569">├── optim.py (optimizer &amp; lr)</text>
  <text x="38" y="142" font-size="9" fill="#475569">└── pipeline.ipynb (notebook cells)</text>

  <!-- Cross-Language & Framework Support Badge -->
  <rect x="30" y="168" width="190" height="34" rx="4" ry="4" fill="#F1F5F9" stroke="#CBD5E1" stroke-width="0.8"/>
  <text x="125" y="183" font-size="9.5" font-weight="bold" fill="#334155" text-anchor="middle">Cross-Language &amp; Framework</text>
  <text x="125" y="196" font-size="9" fill="#64748B" text-anchor="middle">PyTorch • Java (DJL) • C++</text>

  <!-- Task Definition Box -->
  <rect x="30" y="210" width="190" height="52" rx="4" ry="4" fill="#EEF2FF" stroke="#C7D2FE" stroke-width="0.8"/>
  <text x="125" y="226" font-size="9.5" font-weight="bold" fill="#3730A3" text-anchor="middle">Migration Task Specification</text>
  <text x="125" y="244" font-size="10" font-weight="bold" fill="#4338CA" text-anchor="middle">T = (P, Ls, Fs, Lt, Ft, W)</text>
  <text x="125" y="256" font-size="8" fill="#6366F1" text-anchor="middle">Multi-File Editable Scope W</text>
</g>''')

    # Arrow 1: Source -> Translator
    s.append('''<!-- Arrow: Source -> Translator -->
<line x1="230" y1="145" x2="253" y2="145" stroke="#475569" stroke-width="1.8" marker-end="url(#arrow-slate)"/>
<text x="242" y="137" font-size="8.5" font-weight="bold" fill="#64748B" text-anchor="middle">T</text>
''')

    # 2. Translator Card (x: 255, y: 20, w: 175, h: 255)
    s.append(f'''<!-- Card 2: Translator -->
<g id="card-translator" filter="url(#shadow)">
  <rect x="255" y="20" width="175" height="255" rx="8" ry="8" fill="#F8FAFC" stroke="#CBD5E1" stroke-width="1.4"/>
  <path d="M 255 28 Q 255 20 263 20 L 422 20 Q 430 20 430 28 L 430 52 L 255 52 Z" fill="#E2E8F0"/>
  {get_robot_avatar_svg(275, 41, scale=0.85, theme="indigo")}
  <text x="295" y="41" font-size="13" font-weight="bold" fill="#0F172A">Translator</text>
  <rect x="366" y="27" width="56" height="18" rx="4" ry="4" fill="#4F46E5"/>
  <text x="394" y="40" font-size="9" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Role AT</text>

  <!-- Action Box -->
  <rect x="265" y="62" width="155" height="84" rx="5" ry="5" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1"/>
  <text x="273" y="80" font-size="10" font-weight="bold" fill="#1E293B">Zero-Shot Translation</text>
  <text x="273" y="97" font-size="9" fill="#475569">• Cross-framework API map</text>
  <text x="273" y="112" font-size="9" fill="#475569">• Target syntax synthesis</text>
  <text x="273" y="127" font-size="9" fill="#475569">• Module topology preserve</text>
  <text x="273" y="140" font-size="8.5" fill="#64748B">Queries LLM M with AT</text>

  <!-- Output Badge -->
  <rect x="265" y="156" width="155" height="106" rx="5" ry="5" fill="#F0FDF4" stroke="#86EFAC" stroke-width="1"/>
  <text x="342" y="176" font-size="10.5" font-weight="bold" fill="#166534" text-anchor="middle">Initial Candidate P̂^(0)</text>
  <text x="342" y="196" font-size="9" fill="#15803D" text-anchor="middle">Executable target code</text>
  <text x="342" y="210" font-size="8.5" fill="#475569" text-anchor="middle">May have hidden semantic drift</text>
  <rect x="275" y="222" width="135" height="22" rx="4" ry="4" fill="#16A34A"/>
  <text x="342" y="237" font-size="9" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Forward to Verifier ➔</text>
</g>''')

    # Arrow 2: Translator -> Verifier
    s.append('''<!-- Arrow: Translator -> Verifier -->
<line x1="430" y1="145" x2="453" y2="145" stroke="#475569" stroke-width="1.8" marker-end="url(#arrow-slate)"/>
<rect x="433" y="128" width="18" height="14" rx="2" ry="2" fill="#F1F5F9" stroke="#94A3B8" stroke-width="0.8"/>
<text x="442" y="138" font-size="8.5" font-weight="bold" fill="#334155" text-anchor="middle">P̂</text>
''')

    # 3. Verifier Agent Card (x: 455, y: 20, w: 375, h: 255)
    s.append(f'''<!-- Card 3: Verifier Agent -->
<g id="card-verifier" filter="url(#shadow)">
  <rect x="455" y="20" width="375" height="255" rx="8" ry="8" fill="#F0F7FF" stroke="#93C5FD" stroke-width="1.4"/>
  <path d="M 455 28 Q 455 20 463 20 L 822 20 Q 830 20 830 28 L 830 52 L 455 52 Z" fill="#DBEAFE"/>
  {get_robot_avatar_svg(475, 41, scale=0.85, theme="blue")}
  <text x="495" y="41" font-size="13" font-weight="bold" fill="#1E40AF">Verifier Agent: Layered Diagnosis</text>
  <rect x="710" y="27" width="55" height="18" rx="4" ry="4" fill="#2563EB"/>
  <text x="737" y="40" font-size="9" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Role AV</text>
  <rect x="770" y="27" width="52" height="18" rx="4" ry="4" fill="#64748B"/>
  <text x="796" y="40" font-size="8.5" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Read-Only</text>

  <!-- 4-Tier Causal Ladder Container -->
  <g id="ladder-rungs">
    <!-- Level 1: Execution Discrepancy -->
    <rect x="465" y="62" width="355" height="36" rx="4" ry="4" fill="#FEF2F2" stroke="#FCA5A5" stroke-width="1"/>
    <rect x="471" y="68" width="105" height="24" rx="3" ry="3" fill="#EF4444"/>
    <text x="523" y="84" font-size="9" font-weight="bold" fill="#FFFFFF" text-anchor="middle">1. Execution d_exec</text>
    <text x="585" y="84" font-size="10" font-weight="bold" fill="#991B1B">1[e_t ≠ ê_t]</text>
    <text x="655" y="84" font-size="9" fill="#7F1D1D">Exceptions, missing APIs, shape errors</text>

    <!-- Level 2: Forward Values Discrepancy -->
    <rect x="465" y="103" width="355" height="36" rx="4" ry="4" fill="#FFFBEB" stroke="#FCD34D" stroke-width="1"/>
    <rect x="471" y="109" width="105" height="24" rx="3" ry="3" fill="#F59E0B"/>
    <text x="523" y="125" font-size="9" font-weight="bold" fill="#FFFFFF" text-anchor="middle">2. Forward d_fwd</text>
    <text x="585" y="125" font-size="10" font-weight="bold" fill="#92400E">v_t − v̂_t</text>
    <text x="655" y="125" font-size="9" fill="#78350F">Loss divergence, activations, reductions</text>

    <!-- Level 3: Gradient Discrepancy -->
    <rect x="465" y="144" width="355" height="36" rx="4" ry="4" fill="#FAF5FF" stroke="#D8B4FE" stroke-width="1"/>
    <rect x="471" y="150" width="105" height="24" rx="3" ry="3" fill="#9333EA"/>
    <text x="523" y="166" font-size="9" font-weight="bold" fill="#FFFFFF" text-anchor="middle">3. Gradient d_grad</text>
    <text x="585" y="166" font-size="10" font-weight="bold" fill="#6B21A8">g_t − ĝ_t</text>
    <text x="655" y="166" font-size="9" fill="#581C87">Autodiff graph cuts, parameter registration</text>

    <!-- Level 4: Parameter Update Discrepancy -->
    <rect x="465" y="185" width="355" height="36" rx="4" ry="4" fill="#F0FDF4" stroke="#86EFAC" stroke-width="1"/>
    <rect x="471" y="191" width="105" height="24" rx="3" ry="3" fill="#16A34A"/>
    <text x="523" y="207" font-size="9" font-weight="bold" fill="#FFFFFF" text-anchor="middle">4. Update d_upd</text>
    <text x="585" y="207" font-size="10" font-weight="bold" fill="#166534">Δθ_t − Δθ̂_t</text>
    <text x="655" y="207" font-size="9" fill="#14532D">Optimizer rules, momentum, weight decay</text>
  </g>

  <!-- Verifier Actions -->
  <rect x="465" y="227" width="355" height="38" rx="4" ry="4" fill="#FFFFFF" stroke="#BFDBFE" stroke-width="0.8"/>
  <text x="642" y="242" font-size="9.5" font-weight="bold" fill="#1E40AF" text-anchor="middle">Synthesizes distinguishing scratch tests</text>
  <text x="642" y="256" font-size="8.5" fill="#475569" text-anchor="middle">Isolates root cause &amp; produces structured diagnostic evidence E</text>
</g>''')

    # Arrow 3: Evidence Handoff (Verifier -> Repair)
    s.append('''<!-- Evidence Handoff Arrow -->
<line x1="830" y1="145" x2="883" y2="145" stroke="#059669" stroke-width="2" marker-end="url(#arrow-green)"/>
<rect x="836" y="125" width="42" height="16" rx="3" ry="3" fill="#FFFFFF" stroke="#059669" stroke-width="1.2"/>
<text x="857" y="136" font-size="8.5" font-weight="bold" fill="#059669" text-anchor="middle">Evidence E</text>
''')

    # 4. Repair Agent Card (x: 885, y: 20, w: 215, h: 255)
    s.append(f'''<!-- Card 4: Repair Agent -->
<g id="card-repair" filter="url(#shadow)">
  <rect x="885" y="20" width="215" height="255" rx="8" ry="8" fill="#F0FDF4" stroke="#86EFAC" stroke-width="1.4"/>
  <path d="M 885 28 Q 885 20 893 20 L 1092 20 Q 1100 20 1100 28 L 1100 52 L 885 52 Z" fill="#DCFCE7"/>
  {get_robot_avatar_svg(905, 41, scale=0.85, theme="green")}
  <text x="925" y="41" font-size="13" font-weight="bold" fill="#15803D">Repair Agent</text>
  <rect x="998" y="27" width="48" height="18" rx="4" ry="4" fill="#059669"/>
  <text x="1022" y="40" font-size="9" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Role AR</text>
  <rect x="1050" y="27" width="45" height="18" rx="4" ry="4" fill="#047857"/>
  <text x="1072" y="40" font-size="8.5" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Scope W</text>

  <!-- Evidence Receipt -->
  <rect x="895" y="62" width="195" height="52" rx="4" ry="4" fill="#FFFFFF" stroke="#86EFAC" stroke-width="0.8"/>
  <text x="903" y="78" font-size="9.5" font-weight="bold" fill="#166534">Attributed Evidence E</text>
  <text x="903" y="93" font-size="9" fill="#475569">• Verified fault location &amp; cause</text>
  <text x="903" y="106" font-size="9" fill="#475569">• Distinguishing test assertions</text>

  <!-- Workspace Refinement -->
  <rect x="895" y="122" width="195" height="66" rx="4" ry="4" fill="#FFFFFF" stroke="#86EFAC" stroke-width="0.8"/>
  <text x="903" y="138" font-size="9.5" font-weight="bold" fill="#166534">Interactive Code Patching</text>
  <text x="903" y="153" font-size="9" fill="#475569">• Edits production files in scope W</text>
  <text x="903" y="167" font-size="9" fill="#475569">• Runs local syntax &amp; unit tests</text>
  <text x="903" y="181" font-size="9" fill="#475569">• Validates candidate invariants</text>

  <!-- Submit Button -->
  <rect x="900" y="198" width="185" height="34" rx="5" ry="5" fill="#15803D"/>
  <text x="992" y="219" font-size="11" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Submit Candidate P̂^(k)</text>
  <text x="992" y="246" font-size="8.5" fill="#15803D" text-anchor="middle">Dispatched for verification</text>
</g>''')

    # =========================================================================
    # ROW 2: SYSTEM ENVIRONMENT & REPOSITORY FOUNDATION (y: 300 to 480)
    # =========================================================================

    # 5. Orchestrator Card (Deterministic Verification Engine - NO LLM!)
    s.append(f'''<!-- Card 5: Orchestrator -->
<g id="card-orchestrator" filter="url(#shadow)">
  <rect x="20" y="300" width="580" height="180" rx="8" ry="8" fill="#FFFBEB" stroke="#FCD34D" stroke-width="1.4"/>
  <path d="M 20 308 Q 20 300 28 300 L 592 300 Q 600 300 600 308 L 600 332 L 20 332 Z" fill="#FEF3C7"/>
  {get_engine_icon_svg(36, 316, scale=0.8)}
  <text x="54" y="321" font-size="13" font-weight="bold" fill="#92400E">Orchestrator O (Differential Verification Engine)</text>
  <rect x="365" y="306" width="160" height="18" rx="3" ry="3" fill="#D97706"/>
  <text x="445" y="319" font-size="9" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Deterministic Harness (No LLM)</text>
  <rect x="532" y="306" width="60" height="18" rx="3" ry="3" fill="#78350F"/>
  <text x="562" y="319" font-size="9" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Budget B</text>

  <!-- Sub-block 1: Target Execution (Lt, Ft) -->
  <rect x="30" y="342" width="225" height="92" rx="5" ry="5" fill="#FFFFFF" stroke="#FDE68A" stroke-width="1"/>
  <text x="38" y="359" font-size="10" font-weight="bold" fill="#92400E">Target Execution Engine (Lt, Ft)</text>
  <text x="38" y="375" font-size="9" fill="#475569">• MindSpore, JAX, PyTorch execution</text>
  <text x="38" y="389" font-size="9" fill="#475569">• Per-step synchronization with (Ls, Fs)</text>
  <text x="38" y="403" font-size="9" fill="#475569">• Extracts: (e_t, v_t, g_t, Δθ_t) vs (ê_t, v̂_t, ĝ_t, Δθ̂_t)</text>
  <text x="38" y="419" font-size="8.5" fill="#64748B">Framework-agnostic adapter interface</text>

  <!-- Sub-block 2: Multi-Stage Tolerance Verification & Acceptance -->
  <rect x="265" y="342" width="325" height="92" rx="5" ry="5" fill="#FFFFFF" stroke="#FDE68A" stroke-width="1"/>
  <text x="273" y="359" font-size="10" font-weight="bold" fill="#92400E">Multi-Stage Tolerance Verification</text>
  <text x="273" y="375" font-size="9" fill="#475569">Numerical bounds: |d_j| ≤ α + β |x_j| for all training tensors</text>
  
  <!-- Decision pills -->
  <rect x="273" y="388" width="150" height="34" rx="4" ry="4" fill="#F0FDF4" stroke="#86EFAC" stroke-width="1"/>
  <text x="348" y="402" font-size="9" font-weight="bold" fill="#166534" text-anchor="middle">All Checks Pass (d ≃ 0)?</text>
  <text x="348" y="415" font-size="10.5" font-weight="bold" fill="#15803D" text-anchor="middle">✓ Accepted Migration</text>

  <rect x="432" y="388" width="150" height="34" rx="4" ry="4" fill="#FFFBEB" stroke="#FCD34D" stroke-width="1"/>
  <text x="507" y="402" font-size="9" font-weight="bold" fill="#B45309" text-anchor="middle">Residual Differences (d ≄ 0)?</text>
  <text x="507" y="415" font-size="9.5" font-weight="bold" fill="#D97706" text-anchor="middle">Returns Measurements S.m</text>

  <!-- Shared budget note -->
  <text x="310" y="456" font-size="9" fill="#92400E" text-anchor="middle">Manages shared model call allowance b and task submission budget B</text>
</g>''')

    # 6. Repository Coordination Card (x: 620, y: 300, w: 480, h: 180)
    s.append('''<!-- Card 6: Repository Coordination -->
<g id="card-repository" filter="url(#shadow)">
  <rect x="620" y="300" width="480" height="180" rx="8" ry="8" fill="#FAF5FF" stroke="#DDD6FE" stroke-width="1.4"/>
  <path d="M 620 308 Q 620 300 628 300 L 1092 300 Q 1100 300 1100 308 L 1100 332 L 620 332 Z" fill="#EDE9FE"/>
  <text x="632" y="321" font-size="13" font-weight="bold" fill="#5B21B6">Repository Coordination &amp; Context Management C</text>
  <rect x="990" y="306" width="102" height="18" rx="3" ry="3" fill="#7C3AED"/>
  <text x="1041" y="319" font-size="9" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Multi-File Scope</text>

  <!-- 4 Modular Sub-cards -->
  <!-- 1. Dependency Graph -->
  <rect x="630" y="342" width="225" height="58" rx="4" ry="4" fill="#FFFFFF" stroke="#E9D5FF" stroke-width="0.8"/>
  <text x="638" y="358" font-size="9.5" font-weight="bold" fill="#6B21A8">1. Dependency Graph Map(T)</text>
  <text x="638" y="373" font-size="8.5" fill="#475569">Multi-file symbols, imports, calls</text>
  <text x="638" y="386" font-size="8.5" fill="#475569">Shared interfaces &amp; notebook cells</text>

  <!-- 2. Work Units -->
  <rect x="865" y="342" width="225" height="58" rx="4" ry="4" fill="#FFFFFF" stroke="#E9D5FF" stroke-width="0.8"/>
  <text x="873" y="358" font-size="9.5" font-weight="bold" fill="#6B21A8">2. Work Units &amp; Scopes</text>
  <text x="873" y="373" font-size="8.5" fill="#475569">Proposed sub-task decomposition</text>
  <text x="873" y="386" font-size="8.5" fill="#475569">Prerequisite checkpoint ordering</text>

  <!-- 3. Selective Invalidation -->
  <rect x="630" y="408" width="225" height="58" rx="4" ry="4" fill="#FFFFFF" stroke="#E9D5FF" stroke-width="0.8"/>
  <text x="638" y="424" font-size="9.5" font-weight="bold" fill="#6B21A8">3. Caller Invalidation</text>
  <text x="638" y="439" font-size="8.5" fill="#475569">Code edit invalidates affected callers</text>
  <text x="638" y="452" font-size="8.5" fill="#475569">Checkpoints mark verified invariants</text>

  <!-- 4. Context Archiving -->
  <rect x="865" y="408" width="225" height="58" rx="4" ry="4" fill="#FFFFFF" stroke="#E9D5FF" stroke-width="0.8"/>
  <text x="873" y="424" font-size="9.5" font-weight="bold" fill="#6B21A8">4. Context Archiving &amp; Rebuilding</text>
  <text x="873" y="439" font-size="8.5" fill="#475569">Archives observations across limit</text>
  <text x="873" y="452" font-size="8.5" fill="#475569">Rebuilds active context around plan &amp; E</text>
</g>''')

    # =========================================================================
    # RESTRAINED CONNECTORS BETWEEN TIERS (Zero visual clutter!)
    # =========================================================================
    
    # Candidate Submission: Repair Agent down to Orchestrator
    s.append('''<!-- Candidate Submission: Repair -> Orchestrator -->
<path d="M 992 275 L 992 290 L 565 290 L 565 298" fill="none" stroke="#059669" stroke-width="1.8" marker-end="url(#arrow-green)"/>
<rect x="730" y="282" width="96" height="15" rx="3" ry="3" fill="#F0FDF4" stroke="#86EFAC" stroke-width="0.8"/>
<text x="778" y="293" font-size="8.5" font-weight="bold" fill="#15803D" text-anchor="middle">Candidate P̂^(k)</text>
''')

    # Measurement Feedback Loop: Orchestrator up to Verifier Agent (Dashed Blue Arrow)
    s.append('''<!-- Feedback: Orchestrator -> Verifier Agent -->
<path d="M 500 300 L 500 277" fill="none" stroke="#2563EB" stroke-width="1.6" stroke-dasharray="3,2" marker-end="url(#arrow-blue)"/>
<rect x="440" y="282" width="105" height="15" rx="3" ry="3" fill="#EFF6FF" stroke="#93C5FD" stroke-width="0.8"/>
<text x="492" y="293" font-size="8" font-weight="bold" fill="#1E40AF" text-anchor="middle">Discrepancies d_t</text>
''')

    # Context Coordination: Repository Management <-> Repair Agent (Dashed Purple Arrow)
    s.append('''<!-- Repository Coordination <-> Repair Agent -->
<path d="M 945 300 L 945 277" fill="none" stroke="#7C3AED" stroke-width="1.6" stroke-dasharray="3,2" marker-end="url(#arrow-purple)"/>
<rect x="910" y="282" width="70" height="15" rx="3" ry="3" fill="#FAF5FF" stroke="#DDD6FE" stroke-width="0.8"/>
<text x="945" y="293" font-size="8" font-weight="bold" fill="#6B21A8" text-anchor="middle">Context C</text>
''')

    s.append('</svg>')
    
    svg_content = '\n'.join(s)
    SVG_PATH.write_text(svg_content, encoding='utf-8')
    print(f"Generated: {SVG_PATH.relative_to(ROOT)}")


def generate_pptx():
    """Build the matching native, fully editable PowerPoint (.pptx)."""
    prs = pptx.Presentation()
    prs.slide_width = Inches(WIDTH / 96.0)
    prs.slide_height = Inches(HEIGHT / 96.0)
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    def add_card(left, top, width, height, bg_rgb, border_rgb, title, header_bg_rgb, title_color_rgb):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left/96.0), Inches(top/96.0), Inches(width/96.0), Inches(height/96.0))
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_rgb
        shape.line.color.rgb = border_rgb
        shape.line.width = Pt(1.2)
        
        header = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left/96.0), Inches(top/96.0), Inches(width/96.0), Inches(32/96.0))
        header.fill.solid()
        header.fill.fore_color.rgb = header_bg_rgb
        header.line.fill.background()
        tf = header.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.text = f"  {title}"
        p.font.name = "Times New Roman"
        p.font.size = Pt(11.5)
        p.font.bold = True
        p.font.color.rgb = title_color_rgb
        return shape

    def add_textbox(left, top, width, height, text, font_size=9.5, bold=False, color_rgb=RGBColor(30, 41, 59), align=PP_ALIGN.LEFT):
        txBox = slide.shapes.add_textbox(Inches(left/96.0), Inches(top/96.0), Inches(width/96.0), Inches(height/96.0))
        tf = txBox.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.TOP
        p = tf.paragraphs[0]
        p.text = text
        p.font.name = "Times New Roman"
        p.font.size = Pt(font_size)
        p.font.bold = bold
        p.font.color.rgb = color_rgb
        p.alignment = align
        return txBox

    def add_pill(left, top, width, height, text, bg_rgb, text_rgb=RGBColor(255, 255, 255), font_size=8.5):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left/96.0), Inches(top/96.0), Inches(width/96.0), Inches(height/96.0))
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_rgb
        shape.line.fill.background()
        tf = shape.text_frame
        tf.word_wrap = False
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.text = text
        p.font.name = "Times New Roman"
        p.font.size = Pt(font_size)
        p.font.bold = True
        p.font.color.rgb = text_rgb
        p.alignment = PP_ALIGN.CENTER
        return shape

    # Card 1: Source Codebase
    add_card(20, 20, 210, 255, RGBColor(248, 250, 252), RGBColor(203, 213, 225), "Source Codebase", RGBColor(226, 232, 240), RGBColor(15, 23, 42))
    add_pill(156, 26, 66, 18, "(Ls, Fs)", RGBColor(71, 85, 105))
    add_textbox(28, 58, 195, 95, "Multi-File Repository P:\n├── models/ (nn.Module / layers)\n├── train_step.py (forward & loss)\n├── optim.py (optimizer & lr)\n└── pipeline.ipynb (notebook cells)", 8.5)
    add_textbox(28, 165, 195, 35, "Cross-Language & Framework:\nPython (PyTorch) • Java (DJL) • C++", 8.5, True, RGBColor(51, 65, 85), PP_ALIGN.CENTER)
    add_textbox(28, 210, 195, 45, "Migration Task Specification:\nT = (P, Ls, Fs, Lt, Ft, W)", 9, True, RGBColor(67, 56, 202), PP_ALIGN.CENTER)

    # Card 2: Translator
    add_card(255, 20, 175, 255, RGBColor(248, 250, 252), RGBColor(203, 213, 225), "Translator", RGBColor(226, 232, 240), RGBColor(15, 23, 42))
    add_pill(366, 26, 56, 18, "Role AT", RGBColor(79, 70, 229))
    add_textbox(263, 62, 160, 80, "Zero-Shot Translation:\n• Cross-framework API map\n• Target syntax synthesis\n• Module topology preserve", 8.5)
    add_pill(275, 165, 135, 22, "Initial Candidate P̂^(0)", RGBColor(240, 253, 244), RGBColor(22, 101, 52), 9)
    add_textbox(263, 195, 160, 45, "Executable target code\nMay contain semantic drift\nForward to Verifier", 8, False, RGBColor(21, 128, 61), PP_ALIGN.CENTER)

    # Card 3: Verifier Agent
    add_card(455, 20, 375, 255, RGBColor(240, 247, 255), RGBColor(147, 197, 253), "Verifier Agent: Layered Diagnosis", RGBColor(219, 234, 254), RGBColor(30, 64, 175))
    add_pill(710, 26, 55, 18, "Role AV", RGBColor(37, 99, 235))
    add_pill(770, 26, 52, 18, "Read-Only", RGBColor(100, 116, 139))
    
    ladder_items = [
        ("1. Execution d_exec", "1[e_t ≠ ê_t]", "Exceptions, missing APIs, shape errors", RGBColor(239, 68, 68), RGBColor(254, 242, 242), RGBColor(153, 27, 27)),
        ("2. Forward d_fwd", "v_t − v̂_t", "Loss divergence, activations, reductions", RGBColor(245, 158, 11), RGBColor(255, 251, 235), RGBColor(146, 64, 14)),
        ("3. Gradient d_grad", "g_t − ĝ_t", "Autodiff graph cuts, parameter registration", RGBColor(147, 51, 234), RGBColor(250, 245, 255), RGBColor(107, 33, 168)),
        ("4. Update d_upd", "Δθ_t − Δθ̂_t", "Optimizer rules, momentum, weight decay", RGBColor(22, 163, 74), RGBColor(240, 253, 244), RGBColor(22, 101, 52)),
    ]
    for idx, (pill_txt, eq_txt, desc_txt, pill_col, bg_col, text_col) in enumerate(ladder_items):
        y_pos = 60 + idx * 40
        box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(465/96.0), Inches(y_pos/96.0), Inches(355/96.0), Inches(32/96.0))
        box.fill.solid()
        box.fill.fore_color.rgb = bg_col
        box.line.color.rgb = pill_col
        box.line.width = Pt(0.8)
        add_pill(471, y_pos + 4, 105, 22, pill_txt, pill_col, RGBColor(255, 255, 255), 8)
        add_textbox(585, y_pos + 5, 60, 20, eq_txt, 9, True, text_col)
        add_textbox(655, y_pos + 5, 160, 20, desc_txt, 8, False, text_col)

    add_textbox(465, 225, 355, 25, "Synthesizes scratch tests • Isolates root cause & emits Evidence E", 8.5, True, RGBColor(30, 64, 175), PP_ALIGN.CENTER)

    # Card 4: Repair Agent
    add_card(885, 20, 215, 255, RGBColor(240, 253, 244), RGBColor(134, 239, 172), "Repair Agent", RGBColor(220, 252, 231), RGBColor(21, 128, 61))
    add_pill(998, 26, 48, 18, "Role AR", RGBColor(5, 150, 105))
    add_pill(1050, 26, 45, 18, "Scope W", RGBColor(4, 120, 87))
    add_textbox(895, 62, 195, 50, "Attributed Evidence E:\n• Verified fault location & cause\n• Distinguishing test assertions", 8.5)
    add_textbox(895, 122, 195, 65, "Interactive Code Patching:\n• Edits files in scope W\n• Local syntax & unit tests\n• Validates candidate invariants", 8.5)
    add_pill(900, 200, 185, 28, "Submit Candidate P̂^(k)", RGBColor(21, 128, 61), RGBColor(255, 255, 255), 10)

    # Card 5: Orchestrator (Deterministic - NO LLM)
    add_card(20, 300, 580, 180, RGBColor(255, 251, 235), RGBColor(252, 211, 77), "Orchestrator O (Differential Verification Engine)", RGBColor(254, 243, 199), RGBColor(146, 64, 14))
    add_pill(365, 306, 160, 18, "Deterministic Harness (No LLM)", RGBColor(217, 119, 6))
    add_pill(532, 306, 60, 18, "Budget B", RGBColor(120, 53, 15))
    add_textbox(30, 342, 225, 88, "Target Execution (Lt, Ft):\n• MindSpore, JAX, PyTorch adapters\n• Per-step synchronization with (Ls, Fs)\n• Extracts (e_t, v_t, g_t, Δθ_t) vs (ê_t, v̂_t, ĝ_t, Δθ̂_t)", 8)
    add_textbox(265, 342, 325, 45, "Multi-Stage Tolerance Verification:\nNumerical bounds: |d_j| ≤ α + β |x_j| for all training tensors", 8.5)
    add_pill(273, 388, 150, 26, "✓ Accepted Migration", RGBColor(22, 163, 74), RGBColor(255, 255, 255), 9)
    add_pill(432, 388, 150, 26, "Measurements S.m (d ≄ 0)", RGBColor(217, 119, 6), RGBColor(255, 255, 255), 9)
    add_textbox(30, 442, 560, 25, "Manages shared model call allowance b and task submission budget B", 8, False, RGBColor(146, 64, 14), PP_ALIGN.CENTER)

    # Card 6: Repository Coordination
    add_card(620, 300, 480, 180, RGBColor(250, 245, 255), RGBColor(221, 214, 254), "Repository Coordination & Context Management C", RGBColor(237, 233, 254), RGBColor(91, 33, 182))
    add_pill(990, 306, 102, 18, "Multi-File Scope", RGBColor(124, 58, 237))
    add_textbox(630, 342, 225, 55, "1. Dependency Graph Map(T):\nMulti-file symbols, imports, calls\nShared interfaces & notebook cells", 8)
    add_textbox(865, 342, 225, 55, "2. Work Units & Scopes:\nProposed sub-task decomposition\nPrerequisite checkpoint ordering", 8)
    add_textbox(630, 408, 225, 55, "3. Caller Invalidation:\nCode edit invalidates affected callers\nCheckpoints mark verified invariants", 8)
    add_textbox(865, 408, 225, 55, "4. Context Archiving & Rebuilding:\nArchives observations across limit\nRebuilds active context around plan & E", 8)

    prs.save(str(PPTX_PATH))
    print(f"Generated: {PPTX_PATH.relative_to(ROOT)}")


def main():
    generate_svg()
    generate_pptx()


if __name__ == "__main__":
    main()
