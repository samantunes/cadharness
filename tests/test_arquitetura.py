"""Regras de fronteira de docs/architecture.md §3. Atualize DEPENDENCIAS junto com a tabela do doc."""
import ast
from pathlib import Path

import pytest

MODULES = Path(__file__).resolve().parent.parent / "src" / "modules"

DEPENDENCIAS = {
    "nucleo": set(),
    "verificacao": {"nucleo"},
    "exportacao": {"nucleo"},
    "resolvedor": {"nucleo"},
    "intencoes": {"resolvedor"},
    "backend_ifc": {"intencoes", "nucleo"},
    "revit": {"intencoes"},
}


def _modulos():
    if not MODULES.exists():
        return []
    return sorted(p.name for p in MODULES.iterdir() if p.is_dir() and not p.name.startswith(("_", ".")))


def _imports(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            yield node.module
        elif isinstance(node, ast.Import):
            yield from (a.name for a in node.names)


def test_todo_modulo_esta_declarado():
    for m in _modulos():
        assert m in DEPENDENCIAS, f"Módulo '{m}' não está em docs/architecture.md §2"


def test_todo_modulo_tem_module_md():
    for m in _modulos():
        assert (MODULES / m / "MODULE.md").exists(), f"src/modules/{m}/MODULE.md ausente"


@pytest.mark.parametrize("modulo", _modulos() or ["<nenhum>"])
def test_fronteiras(modulo):
    if modulo == "<nenhum>":
        pytest.skip("src/modules ainda vazio")
    erros = []
    for py in (MODULES / modulo).rglob("*.py"):
        for imp in _imports(py):
            partes = imp.split(".")
            if partes[0] != "modules" or len(partes) < 2 or partes[1] == modulo:
                continue
            alvo = partes[1]
            if alvo not in DEPENDENCIAS.get(modulo, set()):
                erros.append(f"{py.relative_to(MODULES)}: depende de '{alvo}' (não permitido)")
            elif len(partes) > 2:
                erros.append(f"{py.relative_to(MODULES)}: importa '{imp}' — use só a API pública 'modules.{alvo}'")
    assert not erros, "\n".join(erros)
