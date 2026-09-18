"""One accounted call to the configured experimental model; no credentials logged."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

root = Path('/media/main/whj/projects/torch4ms/maintext-ablations-20260918')
now = datetime.now(timezone.utc)
path = root / ('transport_health_' + now.strftime('%Y%m%dT%H%M%SZ') + '.json')
request = {'model': 'deepseek-v4-flash', 'thinking': {'type': 'enabled'},
           'reasoning_effort': 'high', 'max_tokens': 256, 'stream': False,
           'messages': [{'role': 'user', 'content': 'Reply OK.'}]}
record = {'timestamp': now.isoformat(), 'request': request,
          'purpose': 'Transport health only; excluded from repair results'}
base = os.environ['AUTOFIX_LLM_BASE_URL'].rstrip('/')
url = base if base.endswith('/chat/completions') else base + '/chat/completions'
req = urllib.request.Request(url, data=json.dumps(request).encode(), headers={
    'Authorization': 'Bearer ' + os.environ['AUTOFIX_LLM_API_KEY'], 'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req, timeout=60) as response:
        record.update(status=response.status, response=json.loads(response.read()))
except urllib.error.HTTPError as exc:
    record.update(status=exc.code, usage=None)
    exc.close()
except Exception as exc:
    record.update(status=None, error_type=type(exc).__name__, usage=None)
with path.open('x') as stream:
    json.dump(record, stream, indent=2)
print(json.dumps({'path': str(path), 'status': record['status'],
    'model': record.get('response', {}).get('model'),
    'usage': record.get('response', {}).get('usage')}))
