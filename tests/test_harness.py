"""Testes com respostas conhecidas (calculadas à mão) — rode a cada mudança no harness."""
import json
import subprocess
import sys
from pathlib import Path

import pytest
from build123d import Align, Box, Location

from cadharness import Component, load_model
from cadharness import analysis, export

ROOT = Path(__file__).resolve().parent.parent
A = (Align.CENTER, Align.CENTER, Align.MIN)


def cubo(nome, lado, pos=(0, 0, 0), mat="aco"):
    return Component(nome, Box(lado, lado, lado, align=A).moved(Location(pos)), mat)


def test_massa_cubo_aco():
    # 100 mm de aço: 1e6 mm³ = 1e-3 m³ × 7850 = 7.85 kg ; CM em z = 50
    mp = analysis.mass_properties([cubo("c", 100)])
    assert mp["mass_kg"] == pytest.approx(7.85)
    assert mp["center_of_mass_mm"] == pytest.approx([0, 0, 50])
    # Inércia de cubo: m·a²/6 = 7.85 × 0.1² / 6
    assert mp["inertia_kg_m2"][0][0] == pytest.approx(7.85 * 0.01 / 6, rel=1e-3)


def test_interferencia_e_folga():
    a, b = cubo("a", 100), cubo("b", 100, (50, 0, 0))
    inter = analysis.interferences([a, b])
    assert inter[0]["volume_mm3"] == pytest.approx(50 * 100 * 100)
    c = cubo("c", 100, (130, 0, 0))
    assert analysis.interferences([a, c]) == []
    assert analysis.clearance([a, c], "a", "c")["distance_mm"] == pytest.approx(30)


def test_contato_nao_e_interferencia():
    a, b = cubo("a", 100), cubo("b", 100, (100, 0, 0))
    assert analysis.interferences([a, b]) == []


def test_estabilidade_com_carga():
    base = cubo("base", 100)
    st = analysis.stability([base])
    assert st["stable"] and st["margin_mm"] == pytest.approx(50, abs=0.5)
    # 7.85 kg de carga a x=200 → CM em x≈100 → fora do apoio (borda em 50)
    st2 = analysis.stability([base], [{"massa_kg": 7.85, "posicao": [200, 0, 50]}])
    assert not st2["stable"]


def test_mesa_exemplo_passa_e_varredura_falha():
    comps, _ = load_model(ROOT / "models/mesa.py")
    spec = analysis.load_spec(ROOT / "models/mesa.spec.toml")
    assert analysis.check_spec(comps, spec)["ok"]
    comps2, _ = load_model(ROOT / "models/mesa.py", {"recuo_perna": 120})
    res = analysis.check_spec(comps2, spec)
    assert res["failed"] == ["estavel"]


def test_parametro_desconhecido():
    with pytest.raises(ValueError, match="desconhecidos"):
        load_model(ROOT / "models/mesa.py", {"cor": "azul"})


def test_ifc_roundtrip(tmp_path):
    import ifcopenshell
    comps, _ = load_model(ROOT / "models/parede_porta.py")
    out = tmp_path / "m.ifc"
    export.export_ifc(comps, out)
    f = ifcopenshell.open(str(out))
    assert {e.is_a() for e in f.by_type("IfcElement")} == {"IfcWall", "IfcSlab", "IfcDoor"}
    assert f.by_type("IfcBuildingStorey")[0].Name == "Térreo"


def test_cli_json():
    p = subprocess.run([sys.executable, "-m", "cadharness", "clearance", "models/parede_porta.py",
                        "--a", "porta_P1", "--b", "parede_eixo_A"],
                       cwd=ROOT, capture_output=True, text=True)
    assert json.loads(p.stdout)["distance_mm"] == pytest.approx(5)
