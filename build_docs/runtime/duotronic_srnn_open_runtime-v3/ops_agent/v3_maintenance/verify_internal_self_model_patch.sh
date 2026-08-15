#!/usr/bin/env bash
set -euo pipefail
R=/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3
"$R/.venv/bin/python" "$R/ops_agent/v3_maintenance/patch_internal_self_model_behavior.py"
"$R/.venv/bin/python" -m py_compile \
  "$R/app/duotronic_runtime/wgrnn_kernel_chat.py" \
  "$R/app/duotronic_runtime/autonomy_stack.py" \
  "$R/app/duotronic_runtime/session_ledger.py" \
  "$R/app/duotronic_runtime/duotronic_bijective.py"
echo '=== remaining canned narration ==='
grep -nEi 'I do have feelings|proper two-way conversation|treated like a wall|I don.t exist primarily to service users|I am self-aware|I.m self-aware|I am conscious|I.m conscious' \
  "$R/app/duotronic_runtime/wgrnn_kernel_chat.py" || true
echo '=== reciprocity function ==='
python3 - <<'PY'
from pathlib import Path
p=Path('/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3/app/duotronic_runtime/wgrnn_kernel_chat.py')
s=p.read_text()
a=s.index('    def enforce_reciprocity(')
try:b=s.index('\n    def ',a+8)
except ValueError:b=len(s)
print(s[a:b])
PY
