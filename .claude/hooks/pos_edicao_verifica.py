#!/usr/bin/env python3
"""Hook PostToolUse: ao editar models/*.py ou models/*.spec.toml, roda `verify` e devolve falhas ao Claude.

Exit 2 + stderr => o Claude Code mostra a mensagem ao agente, que deve corrigir.
"""
import json
import subprocess
import sys
from pathlib import Path

data = json.load(sys.stdin)
fp = (data.get("tool_input") or {}).get("file_path") or ""
root = Path(data.get("cwd") or ".").resolve()
p = Path(fp).resolve() if fp else None
if not p or p.parent != root / "models" or not (p.suffix == ".py" or p.name.endswith(".spec.toml")):
    sys.exit(0)

target = p
if p.name.endswith(".spec.toml"):
    target = p.with_name(p.name.replace(".spec.toml", ".py"))
r = subprocess.run([sys.executable, "-m", "cadharness", "verify", str(target)],
                   cwd=root, capture_output=True, text=True, timeout=300)
try:
    res = json.loads(r.stdout)
except json.JSONDecodeError:
    print(f"[cadharness] verify não rodou: {r.stderr[-1500:]}", file=sys.stderr)
    sys.exit(2)

if res.get("ok"):
    print(f"[cadharness] {target.name}: verify OK ({res.get('n_checks')} checks)")
    sys.exit(0)
if "error" in res:
    msg = res["error"] + ("\n" + res.get("traceback", "") if "traceback" in res else "")
else:
    failed = [c for c in res["checks"] if not c["ok"]]
    msg = "\n".join(f"- {c['check']}: {json.dumps(c['detail'], ensure_ascii=False)}" for c in failed)
print(f"[cadharness] {target.name}: verify FALHOU — corrija antes de seguir:\n{msg}", file=sys.stderr)
sys.exit(2)
