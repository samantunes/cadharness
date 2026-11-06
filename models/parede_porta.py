"""Módulo BIM simples: laje + parede de blocos com vão de porta + porta.

Demonstra classes IFC (IfcSlab, IfcWall, IfcDoor) a partir de geometria paramétrica.
Origem: canto inferior esquerdo da parede, piso acabado em Z=0.
"""
from build123d import Box, Align, Location

from cadharness import Component

A = (Align.MIN, Align.MIN, Align.MIN)


def build(comprimento=4000.0, altura=2800.0, espessura=140.0, esp_laje=120.0,
          porta_largura=800.0, porta_altura=2100.0, porta_x=600.0, porta_esp=35.0):
    laje = Box(comprimento + 400, 2000, esp_laje, align=A).moved(Location((-200, -930, -esp_laje)))
    parede = Box(comprimento, espessura, altura, align=A)
    vao = Box(porta_largura, espessura, porta_altura, align=A).moved(Location((porta_x, 0, 0)))
    parede = parede - vao
    porta = Box(porta_largura - 10, porta_esp, porta_altura - 5, align=A).moved(
        Location((porta_x + 5, (espessura - porta_esp) / 2, 0)))
    return [
        Component("laje_piso", laje, "concreto_armado", "IfcSlab", {"Pavimento": "Térreo"}),
        Component("parede_eixo_A", parede, "bloco_ceramico", "IfcWall", {"Revestimento": "reboco"}),
        Component("porta_P1", porta, "madeira_eucalipto", "IfcDoor", {"Codigo": "P1"}),
    ]
