#!/usr/bin/env python3
"""Hook PreToolUse: só permite editar arquivos dentro do escopo ativo (.claude/escopo.json).

Escopo é definido pelo comando /escopo. Sem escopo ativo, só arquivos de planejamento
(docs/use-cases, pendências, backlog, openspec) e modelos CAD (models/) podem ser editados.
"""
import fnmatch
import json
import sys
from pathlib import Path

data = json.load(sys.stdin)
fp = (data.get("tool_input") or {}).get("file_path") or (data.get("tool_input") or {}).get("notebook_path") or ""
if not fp:
    sys.exit(0)
root = Path(data.get("cwd") or ".").resolve()
try:
    rel = Path(fp).resolve().relative_to(root).as_posix()
except ValueError:
    sys.exit(0)  # fora do projeto (ex.: scratchpad): não é assunto deste hook

SEMPRE = [
    "docs/use-cases/**", "docs/pendencias.md", "docs/BACKLOG.md",
    "openspec/**", "models/**", ".claude/escopo.json",
]

arq = root / ".claude" / "escopo.json"
escopo = {}
if arq.exists():
    try:
        escopo = json.loads(arq.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("Bloqueado: .claude/escopo.json inválido. Redefina com /escopo.", file=sys.stderr)
        sys.exit(2)

permitidos = list(SEMPRE)
for m in escopo.get("modulos", []):
    permitidos += [f"src/modules/{m}/**"]
permitidos += escopo.get("extras", [])


def casa(padrao: str) -> bool:
    if padrao.endswith("/**"):
        base = padrao[:-3]
        return rel == base or rel.startswith(base + "/")
    return fnmatch.fnmatch(rel, padrao)


if any(casa(p) for p in permitidos):
    sys.exit(0)

if escopo:
    atual = f"UC {escopo.get('uc', '?')}, mudança {escopo.get('mudanca', '?')}, módulos {escopo.get('modulos', [])}, extras {escopo.get('extras', [])}"
else:
    atual = "nenhum escopo ativo (só planejamento e models/)"
print(f"Bloqueado pelo escopo: '{rel}' está fora do escopo atual ({atual}). "
      "Não contorne com Bash. Pare e pergunte ao usuário se deve ampliar o escopo com /escopo.",
      file=sys.stderr)
sys.exit(2)
