"""Convenção de modelo: um script Python que define `build(**params) -> list[Component]`.

Unidades: milímetros. Gravidade: -Z. O modelo é a fonte da verdade; exports são derivados.
"""
from __future__ import annotations

import inspect
import runpy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Densidades em kg/m³ (valores nominais; ajuste no CLAUDE.md do projeto se necessário)
MATERIALS: dict[str, float] = {
    "aco": 7850.0,
    "aluminio": 2700.0,
    "inox": 8000.0,
    "concreto": 2400.0,
    "concreto_armado": 2500.0,
    "bloco_ceramico": 1400.0,
    "madeira_pinus": 500.0,
    "madeira_eucalipto": 750.0,
    "mdf": 750.0,
    "compensado": 600.0,
    "vidro": 2500.0,
    "gesso": 1000.0,
    "pla": 1240.0,
    "abs": 1050.0,
    "petg": 1270.0,
}


@dataclass
class Component:
    """Uma peça do modelo: um sólido build123d + metadados físicos/BIM."""

    name: str
    shape: Any  # build123d Part/Solid/Compound
    material: str = "aco"
    ifc_class: str = "IfcBuildingElementProxy"
    props: dict[str, Any] = field(default_factory=dict)

    @property
    def density(self) -> float:
        if self.material not in MATERIALS:
            raise KeyError(
                f"Material '{self.material}' desconhecido em '{self.name}'. "
                f"Use um de: {sorted(MATERIALS)}"
            )
        return MATERIALS[self.material]


def _parse_value(raw: str) -> Any:
    for cast in (int, float):
        try:
            return cast(raw)
        except ValueError:
            pass
    if raw.lower() in ("true", "false"):
        return raw.lower() == "true"
    return raw


def parse_params(items: list[str] | None) -> dict[str, Any]:
    """Converte ['largura=1200', 'nome=x'] em dict tipado."""
    out: dict[str, Any] = {}
    for item in items or []:
        key, _, val = item.partition("=")
        out[key.strip()] = _parse_value(val.strip())
    return out


def load_model(path: str | Path, params: dict[str, Any] | None = None) -> tuple[list[Component], dict[str, Any]]:
    """Executa o script do modelo e retorna (componentes, parâmetros efetivos)."""
    path = Path(path)
    ns = runpy.run_path(str(path), run_name="__cadmodel__")
    build = ns.get("build")
    if not callable(build):
        raise ValueError(f"{path} precisa definir build(**params) -> list[Component]")
    defaults = {
        k: v.default
        for k, v in inspect.signature(build).parameters.items()
        if v.default is not inspect.Parameter.empty
    }
    effective = {**defaults, **(params or {})}
    unknown = set(params or {}) - set(defaults)
    if unknown:
        raise ValueError(f"Parâmetros desconhecidos: {sorted(unknown)}. Disponíveis: {sorted(defaults)}")
    comps = list(build(**effective))
    names = [c.name for c in comps]
    dup = {n for n in names if names.count(n) > 1}
    if dup:
        raise ValueError(f"Nomes de componentes duplicados: {sorted(dup)}")
    for c in comps:
        if not isinstance(c, Component):
            raise TypeError(f"build() deve retornar Component, recebeu {type(c).__name__}")
        _ = c.density  # valida material cedo
    return comps, effective
