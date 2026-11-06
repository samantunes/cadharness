---
name: exportar-bim
description: Exportar um modelo para IFC (BIM) e desenhos 2D (DXF/SVG), conferindo classes IFC, materiais e psets. Use quando o usuário pedir IFC, BIM, entrega para Revit/Archicad/Bonsai ou pranchas DXF.
---

# Exportar BIM

1. Rode `verify`; não exporte modelo que falha (a não ser que o usuário peça explicitamente).
2. Revise `ifc_class` de cada `Component` (`info` mostra). Corrija proxies que tenham classe
   adequada (parede → IfcWall, laje → IfcSlab, etc.) no modelo, não no IFC.
3. `mcp__cad__export(format="ifc")`. Confira a saída: lista de elementos com GlobalId.
4. Valide reabrindo:
   `python -c "import ifcopenshell,ifcopenshell.util.element as u;f=ifcopenshell.open('out/<n>/<n>.ifc');[print(e.is_a(),e.Name,u.get_psets(e).get('Pset_CadHarness')) for e in f.by_type('IfcElement')]"`
5. Desenhos: `export(format="dxf", view="frente"|"topo"|"direita")` — camadas VISIVEL e
   OCULTA (tracejada), em mm.
6. Reporte arquivos gerados, GlobalIds e qualquer limitação (geometria tesselada no IFC;
   sem aberturas IfcOpeningElement — o vão é recortado na própria parede).
