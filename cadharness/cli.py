"""CLI: python -m cadharness <comando> modelo.py [opções]. Saída sempre JSON em stdout."""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

from . import analysis, export, render
from .model import load_model, parse_params


def default_spec(model: Path) -> Path | None:
    p = model.with_suffix(".spec.toml")
    return p if p.exists() else None


def out_path(model: Path, suffix: str, out: str | None) -> Path:
    if out:
        return Path(out)
    d = Path("out") / model.stem
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{model.stem}{suffix}"


def run(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(prog="cadharness")
    ap.add_argument("cmd", choices=["info", "verify", "stability", "interference",
                                    "clearance", "render", "export"])
    ap.add_argument("model")
    ap.add_argument("-p", "--param", action="append", help="sobrescreve parâmetro: nome=valor")
    ap.add_argument("--spec")
    ap.add_argument("--out")
    ap.add_argument("--format", default="step", choices=["step", "stl", "dxf", "svg", "ifc"])
    ap.add_argument("--view", action="append", help="vista (render: iso/frente/topo/direita)")
    ap.add_argument("--a"); ap.add_argument("--b")
    a = ap.parse_args(argv)

    model = Path(a.model)
    comps, params = load_model(model, parse_params(a.param))

    if a.cmd == "info":
        return analysis.summary(comps, params)
    if a.cmd == "interference":
        return {"interferences": analysis.interferences(comps)}
    if a.cmd == "clearance":
        return analysis.clearance(comps, a.a, a.b)
    if a.cmd == "stability":
        spec = Path(a.spec) if a.spec else default_spec(model)
        loads = analysis.load_spec(spec).get("carga", []) if spec else []
        return analysis.stability(comps, loads)
    if a.cmd == "verify":
        spec = Path(a.spec) if a.spec else default_spec(model)
        if not spec:
            return {"ok": False, "error": f"Sem spec: crie {model.with_suffix('.spec.toml')}"}
        res = analysis.check_spec(comps, analysis.load_spec(spec))
        res["spec"] = str(spec)
        res["params"] = params
        return res
    if a.cmd == "render":
        return render.render(comps, out_path(model, ".png", a.out), a.view, title=model.stem)
    if a.cmd == "export":
        fmt = a.format
        if fmt == "step":
            return export.export_step(comps, out_path(model, ".step", a.out))
        if fmt == "stl":
            return export.export_stl(comps, a.out or Path("out") / model.stem / "stl")
        if fmt in ("dxf", "svg"):
            view = (a.view or ["frente"])[0]
            return export.export_drawing(comps, out_path(model, f"_{view}.{fmt}", a.out), view)
        if fmt == "ifc":
            return export.export_ifc(comps, out_path(model, ".ifc", a.out), project=model.stem)
    raise AssertionError(a.cmd)


def main(argv: list[str] | None = None) -> int:
    try:
        res = run(argv)
        code = 0 if res.get("ok", True) else 1
    except SystemExit:
        raise
    except Exception as e:  # erro do modelo vira JSON para o agente corrigir
        res = {"ok": False, "error": f"{type(e).__name__}: {e}",
               "traceback": traceback.format_exc(limit=4)}
        code = 2
    json.dump(res, sys.stdout, ensure_ascii=False, indent=1, default=str)
    sys.stdout.write("\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
