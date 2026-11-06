"""Análises físicas e geométricas. Toda cota/massa reportada pelo agente deve vir daqui."""
from __future__ import annotations

import itertools
import math
import tomllib
from pathlib import Path
from typing import Any

import numpy as np

from .model import Component

MM3_TO_M3 = 1e-9
G = 9.81


def _r(x: float, n: int = 3) -> float:
    return round(float(x), n)


def _vec(v) -> list[float]:
    return [_r(v.X), _r(v.Y), _r(v.Z)]


def _bbox(shape) -> dict[str, list[float]]:
    bb = shape.bounding_box()
    return {"min": _vec(bb.min), "max": _vec(bb.max), "size": _vec(bb.size)}


def component_info(c: Component) -> dict[str, Any]:
    from build123d import CenterOf

    vol = c.shape.volume
    return {
        "name": c.name,
        "material": c.material,
        "ifc_class": c.ifc_class,
        "valid": bool(c.shape.is_valid),
        "solids": len(c.shape.solids()),
        "volume_mm3": _r(vol, 1),
        "area_mm2": _r(c.shape.area, 1),
        "mass_kg": _r(vol * MM3_TO_M3 * c.density, 4),
        "center_of_mass": _vec(c.shape.center(CenterOf.MASS)),
        "bbox": _bbox(c.shape),
        "props": c.props,
    }


def mass_properties(comps: list[Component], loads: list[dict] | None = None) -> dict[str, Any]:
    """Massa total, centro de massa e tensor de inércia (kg·m²) em torno do CM global."""
    from build123d import CenterOf

    total = 0.0
    moment = np.zeros(3)
    parts = []
    for c in comps:
        m = c.shape.volume * MM3_TO_M3 * c.density
        cm = np.array(tuple(c.shape.center(CenterOf.MASS)))
        parts.append((c, m, cm))
        total += m
        moment += m * cm
    for ld in loads or []:
        m = float(ld["massa_kg"])
        total += m
        moment += m * np.array(ld["posicao"], dtype=float)
    if total <= 0:
        raise ValueError("Massa total nula")
    com = moment / total

    # Inércia: matrix_of_inertia do OCC é por densidade unitária em torno do CM da peça (mm^5).
    inertia = np.zeros((3, 3))
    for c, m, cm in parts:
        local = np.array(c.shape.matrix_of_inertia) * c.density * MM3_TO_M3  # kg·mm²
        d = cm - com
        inertia += local + m * (np.dot(d, d) * np.eye(3) - np.outer(d, d))
    inertia *= 1e-6  # kg·m²
    return {
        "mass_kg": _r(total, 4),
        "weight_N": _r(total * G, 2),
        "center_of_mass_mm": [_r(x) for x in com],
        "inertia_kg_m2": [[_r(x, 5) for x in row] for row in inertia],
        "loads_included": len(loads or []),
    }


def interferences(comps: list[Component], tol_mm3: float = 1.0) -> list[dict[str, Any]]:
    """Pares de peças cujos sólidos se interpenetram (volume de interseção > tol)."""
    out = []
    for a, b in itertools.combinations(comps, 2):
        ba, bb = a.shape.bounding_box(), b.shape.bounding_box()
        if (ba.max.X < bb.min.X or bb.max.X < ba.min.X or ba.max.Y < bb.min.Y
                or bb.max.Y < ba.min.Y or ba.max.Z < bb.min.Z or bb.max.Z < ba.min.Z):
            continue
        inter = a.shape & b.shape
        vol = inter.volume if inter is not None else 0.0
        if vol > tol_mm3:
            out.append({"a": a.name, "b": b.name, "volume_mm3": _r(vol, 2),
                        "bbox": _bbox(inter)})
    return out


def clearance(comps: list[Component], a: str, b: str) -> dict[str, Any]:
    """Distância mínima entre duas peças (0 = contato ou interferência)."""
    by = {c.name: c for c in comps}
    for n in (a, b):
        if n not in by:
            raise KeyError(f"Componente '{n}' não existe. Disponíveis: {sorted(by)}")
    d = by[a].shape.distance_to(by[b].shape)
    return {"a": a, "b": b, "distance_mm": _r(d)}


def _support_points(comps: list[Component], tol: float = 0.5) -> np.ndarray:
    zmin = min(c.shape.bounding_box().min.Z for c in comps)
    pts = []
    for c in comps:
        if c.shape.bounding_box().min.Z > zmin + tol:
            continue
        verts, _ = c.shape.tessellate(0.2, 0.2)
        pts.extend((v.X, v.Y) for v in verts if v.Z <= zmin + tol)
    return np.array(pts), zmin


def stability(comps: list[Component], loads: list[dict] | None = None) -> dict[str, Any]:
    """Estabilidade estática apoiado no plano mais baixo (gravidade -Z).

    Retorna se a projeção do CM cai dentro do polígono de apoio, a margem até a borda
    e o ângulo de tombamento aproximado (atan(margem / altura do CM)).
    """
    from shapely.geometry import MultiPoint, Point

    mp = mass_properties(comps, loads)
    com = mp["center_of_mass_mm"]
    pts, zmin = _support_points(comps)
    hull = MultiPoint([tuple(p) for p in pts]).convex_hull
    p = Point(com[0], com[1])
    inside = hull.geom_type == "Polygon" and hull.contains(p)
    margin = hull.exterior.distance(p) if hull.geom_type == "Polygon" else 0.0
    margin = margin if inside else -margin
    h = com[2] - zmin
    tip = math.degrees(math.atan2(margin, h)) if h > 0 and inside else 0.0
    return {
        "stable": bool(inside),
        "center_of_mass_mm": com,
        "support_polygon_area_mm2": _r(hull.area, 1),
        "support_polygon_xy": [[_r(x, 1), _r(y, 1)] for x, y in
                                (hull.exterior.coords if hull.geom_type == "Polygon" else [])],
        "margin_mm": _r(margin, 2),
        "com_height_mm": _r(h, 2),
        "tip_angle_deg": _r(tip, 2),
        "mass_kg": mp["mass_kg"],
    }


def summary(comps: list[Component], params: dict[str, Any]) -> dict[str, Any]:
    from build123d import Compound

    whole = Compound(children=[c.shape for c in comps])
    return {
        "params": params,
        "n_components": len(comps),
        "bbox": _bbox(whole),
        "components": [component_info(c) for c in comps],
        "mass": mass_properties(comps),
    }


# --------------------------------------------------------------------------- spec


def load_spec(path: str | Path) -> dict[str, Any]:
    with open(path, "rb") as f:
        return tomllib.load(f)


def check_spec(comps: list[Component], spec: dict[str, Any]) -> dict[str, Any]:
    """Verifica o modelo contra um arquivo de requisitos (.spec.toml). Ver README."""
    from build123d import Compound

    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: Any):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    by = {c.name: c for c in comps}
    lim = spec.get("limites", {})
    rules = spec.get("regras", {})
    loads = spec.get("carga", [])

    for c in comps:
        if not c.shape.is_valid or c.shape.volume <= 0:
            add(f"solido_valido:{c.name}", False, "sólido inválido ou volume nulo")
    if all(ch["ok"] for ch in checks):
        add("solidos_validos", True, f"{len(comps)} componentes")

    for req in spec.get("componentes", {}).get("obrigatorios", []):
        add(f"componente_existe:{req}", req in by, sorted(by) if req not in by else "ok")

    if "bbox_max" in lim:
        size = Compound(children=[c.shape for c in comps]).bounding_box().size
        got = [size.X, size.Y, size.Z]
        add("bbox_max", all(g <= m + 1e-6 for g, m in zip(got, lim["bbox_max"])),
            {"atual": [_r(x) for x in got], "max": lim["bbox_max"]})

    if "massa_kg" in lim:
        lo, hi = lim["massa_kg"]
        m = mass_properties(comps)["mass_kg"]
        add("massa_kg", lo <= m <= hi, {"atual": m, "faixa": [lo, hi]})

    if rules.get("sem_interferencia"):
        inter = interferences(comps, tol_mm3=rules.get("tolerancia_interferencia_mm3", 1.0))
        add("sem_interferencia", not inter, inter or "nenhuma")

    if rules.get("estavel"):
        st = stability(comps, loads)
        need = rules.get("margem_estabilidade_min_mm", 0.0)
        add("estavel", st["stable"] and st["margin_mm"] >= need,
            {k: st[k] for k in ("stable", "margin_mm", "tip_angle_deg", "center_of_mass_mm")}
            | {"margem_min": need, "cargas": len(loads)})

    for f in spec.get("folga", []):
        a, b = f["entre"]
        try:
            d = clearance(comps, a, b)["distance_mm"]
        except KeyError as e:
            add(f"folga:{a}~{b}", False, str(e))
            continue
        lo, hi = f.get("min_mm", 0.0), f.get("max_mm", math.inf)
        add(f"folga:{a}~{b}", lo <= d <= hi, {"atual": d, "min": lo, "max": None if hi == math.inf else hi})

    axes = {"x": 0, "y": 1, "z": 2}
    for cota in spec.get("cota", []):
        n = cota["componente"]
        if n not in by:
            add(f"cota:{n}.{cota['eixo']}", False, f"componente inexistente; disponíveis {sorted(by)}")
            continue
        s = by[n].shape.bounding_box().size
        got = [s.X, s.Y, s.Z][axes[cota["eixo"].lower()]]
        tol = cota.get("tol", 0.1)
        add(f"cota:{n}.{cota['eixo']}", abs(got - cota["valor"]) <= tol,
            {"atual": _r(got), "nominal": cota["valor"], "tol": tol})

    return {"ok": all(c["ok"] for c in checks), "n_checks": len(checks),
            "failed": [c["check"] for c in checks if not c["ok"]], "checks": checks}
