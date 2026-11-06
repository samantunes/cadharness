"""Mesa de trabalho: tampo em MDF sobre 4 pernas de pinus e travessas (saias).

Origem: centro do tampo em XY, piso em Z=0. Unidades: mm.
"""
from build123d import Box, Align, Location

from cadharness import Component


def build(comprimento=1200.0, profundidade=600.0, altura=750.0, esp_tampo=25.0,
          secao_perna=50.0, recuo_perna=40.0, altura_saia=80.0, esp_saia=20.0):
    zt = altura - esp_tampo  # face inferior do tampo
    tampo = Box(comprimento, profundidade, esp_tampo,
                align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((0, 0, zt)))
    comps = [Component("tampo", tampo, "mdf", "IfcFurniture", {"Acabamento": "laminado"})]

    px = comprimento / 2 - recuo_perna - secao_perna / 2
    py = profundidade / 2 - recuo_perna - secao_perna / 2
    for i, (sx, sy) in enumerate([(-1, -1), (1, -1), (1, 1), (-1, 1)], start=1):
        perna = Box(secao_perna, secao_perna, zt,
                    align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((sx * px, sy * py, 0)))
        comps.append(Component(f"perna_{i}", perna, "madeira_pinus", "IfcFurniture"))

    # Saias entre as pernas (encostadas, sem interpenetração), rentes à face externa das pernas
    vao_x = 2 * px - secao_perna
    vao_y = 2 * py - secao_perna
    zs = zt - altura_saia
    yo = py + secao_perna / 2 - esp_saia / 2
    xo = px + secao_perna / 2 - esp_saia / 2
    for nome, dims, pos in [
        ("saia_frente", (vao_x, esp_saia, altura_saia), (0, -yo, zs)),
        ("saia_fundo", (vao_x, esp_saia, altura_saia), (0, yo, zs)),
        ("saia_esq", (esp_saia, vao_y, altura_saia), (-xo, 0, zs)),
        ("saia_dir", (esp_saia, vao_y, altura_saia), (xo, 0, zs)),
    ]:
        s = Box(*dims, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location(pos))
        comps.append(Component(nome, s, "madeira_pinus", "IfcFurniture"))
    return comps
