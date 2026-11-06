#!/usr/bin/env python3
"""Hook PreToolUse: impede editar à mão arquivos derivados (out/, STEP, IFC, STL, DXF).

O modelo paramétrico em models/*.py é a única fonte da verdade.
"""
import json
import sys
from pathlib import Path

data = json.load(sys.stdin)
fp = (data.get("tool_input") or {}).get("file_path") or ""
if not fp:
    sys.exit(0)
p = Path(fp)
if "out" in p.parts or p.suffix.lower() in {".step", ".stp", ".ifc", ".stl", ".dxf", ".3mf"}:
    print(f"Bloqueado: '{fp}' é derivado. Altere o modelo em models/*.py e reexporte "
          "com a ferramenta mcp__cad__export.", file=sys.stderr)
    sys.exit(2)
