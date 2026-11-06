"""Exportações derivadas do modelo paramétrico: STEP, STL, DXF/SVG (desenho 2D) e IFC."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .model import Component

# Vistas ortográficas de 1º diedro (ABNT/ISO): (origem da câmera, vetor "para cima")
ORTHO = {
    "frente": ((0, -1, 0), (0, 0, 1)),
    "topo": ((0, 0, 1), (0, 1, 0)),
    "direita": ((1, 0, 0), (0, 0, 1)),
}


def _compound(comps):
    from build123d import Compound
    return Compound(children=[c.shape for c in comps])


def export_step(comps: list[Component], out: str | Path) -> dict:
    from build123d import Compound, export_step as _exp
    children = []
    for c in comps:
        s = c.shape.copy() if hasattr(c.shape, "copy") else c.shape
        s.label = c.name
        children.append(s)
    asm = Compound(children=children, label="assembly")
    _exp(asm, str(out))
    return {"step": str(out)}


def export_stl(comps: list[Component], out_dir: str | Path, tol: float = 0.05) -> dict:
    from build123d import export_stl as _exp
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for c in comps:
        p = out_dir / f"{c.name}.stl"
        _exp(c.shape, str(p), tolerance=tol)
        files.append(str(p))
    return {"stl": files}


def export_drawing(comps: list[Component], out: str | Path, view: str = "frente") -> dict:
    """Projeção ortográfica com linhas visíveis/ocultas em DXF ou SVG (pela extensão)."""
    from build123d import ExportDXF, ExportSVG, LineType, Unit

    if view not in ORTHO:
        raise ValueError(f"Vista '{view}' inválida; use {list(ORTHO)}")
    whole = _compound(comps)
    c = whole.bounding_box().center()
    d, up = ORTHO[view]
    dist = whole.bounding_box().diagonal * 3
    origin = (c.X + d[0] * dist, c.Y + d[1] * dist, c.Z + d[2] * dist)
    visible, hidden = whole.project_to_viewport(origin, up, look_at=tuple(c))
    out = Path(out)
    exp = ExportDXF(unit=Unit.MM) if out.suffix.lower() == ".dxf" else ExportSVG(unit=Unit.MM)
    exp.add_layer("VISIVEL")
    exp.add_layer("OCULTA", line_type=LineType.ISO_DASH)
    exp.add_shape(visible, layer="VISIVEL")
    exp.add_shape(hidden, layer="OCULTA")
    exp.write(str(out))
    return {"drawing": str(out), "view": view, "visible_edges": len(visible),
            "hidden_edges": len(hidden)}


def export_ifc(comps: list[Component], out: str | Path, project: str = "cadharness",
               storey: str = "Térreo", schema: str = "IFC4", tol: float = 0.5) -> dict:
    """Gera IFC com hierarquia espacial, material, Qto e Pset por componente."""
    import ifcopenshell
    import ifcopenshell.api
    import ifcopenshell.guid
    import numpy as np

    from .analysis import MM3_TO_M3

    f = ifcopenshell.file(schema=schema)
    proj = ifcopenshell.api.run("root.create_entity", f, ifc_class="IfcProject", name=project)
    ifcopenshell.api.run("unit.assign_unit", f, length={"is_metric": True, "raw": "MILLIMETERS"})
    model = ifcopenshell.api.run("context.add_context", f, context_type="Model")
    body = ifcopenshell.api.run("context.add_context", f, context_type="Model",
                                context_identifier="Body", target_view="MODEL_VIEW", parent=model)
    site = ifcopenshell.api.run("root.create_entity", f, ifc_class="IfcSite", name="Terreno")
    bldg = ifcopenshell.api.run("root.create_entity", f, ifc_class="IfcBuilding", name="Edificação")
    st = ifcopenshell.api.run("root.create_entity", f, ifc_class="IfcBuildingStorey", name=storey)
    ifcopenshell.api.run("aggregate.assign_object", f, relating_object=proj, products=[site])
    ifcopenshell.api.run("aggregate.assign_object", f, relating_object=site, products=[bldg])
    ifcopenshell.api.run("aggregate.assign_object", f, relating_object=bldg, products=[st])

    materials: dict[str, Any] = {}
    elements = []
    for c in comps:
        el = ifcopenshell.api.run("root.create_entity", f, ifc_class=c.ifc_class, name=c.name)
        ifcopenshell.api.run("geometry.edit_object_placement", f, product=el, matrix=np.eye(4))
        verts, tris = c.shape.tessellate(tol, 0.3)
        rep = ifcopenshell.api.run(
            "geometry.add_mesh_representation", f, context=body,
            vertices=[[tuple(v) for v in verts]], faces=[[list(t) for t in tris]])
        ifcopenshell.api.run("geometry.assign_representation", f, product=el, representation=rep)
        ifcopenshell.api.run("spatial.assign_container", f, products=[el], relating_structure=st)
        if c.material not in materials:
            materials[c.material] = ifcopenshell.api.run("material.add_material", f, name=c.material)
        ifcopenshell.api.run("material.assign_material", f, products=[el], material=materials[c.material])
        vol = c.shape.volume
        pset = ifcopenshell.api.run("pset.add_pset", f, product=el, name="Pset_CadHarness")
        props = {"Material": c.material, "VolumeMM3": round(vol, 2),
                 "MassKg": round(vol * MM3_TO_M3 * c.density, 4)}
        props.update({k: v for k, v in c.props.items() if isinstance(v, (str, int, float, bool))})
        ifcopenshell.api.run("pset.edit_pset", f, pset=pset, properties=props)
        elements.append({"name": c.name, "ifc_class": el.is_a(), "GlobalId": el.GlobalId})
    f.write(str(out))
    return {"ifc": str(out), "schema": schema, "elements": elements}
