"""Servidor MCP 'cad': expõe o harness como ferramentas para o Claude Code / Agent SDK.

Cada chamada roda o modelo num subprocesso (isolamento + timeout), então um erro de
geometria do OpenCascade nunca derruba o servidor.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

try:  # mcp >= 2.0
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server

ROOT = Path(__file__).resolve().parent.parent
mcp = _Server("cad", instructions=(
    "Ferramentas CAD paramétricas (build123d). Unidades mm/kg. Rode verify após toda "
    "alteração e leia o PNG de render com Read para ver o modelo."))


def _call(*args: str, timeout: int = 180) -> dict:
    try:
        p = subprocess.run([sys.executable, "-m", "cadharness", *args], cwd=ROOT,
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"timeout ({timeout}s) — simplifique a geometria"}
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "error": (p.stderr or p.stdout)[-3000:]}


def _params(params: dict | None) -> list[str]:
    out = []
    for k, v in (params or {}).items():
        out += ["-p", f"{k}={v}"]
    return out


@mcp.tool()
def info(model: str, params: dict | None = None) -> dict:
    """Resumo do modelo: parâmetros efetivos, bbox, volume/massa/CM por componente."""
    return _call("info", model, *_params(params))


@mcp.tool()
def verify(model: str, params: dict | None = None, spec: str | None = None) -> dict:
    """Verifica o modelo contra o .spec.toml (cotas, massa, folgas, interferência, estabilidade).
    Rode após TODA alteração. Só declare a tarefa concluída com ok=true."""
    extra = ["--spec", spec] if spec else []
    return _call("verify", model, *_params(params), *extra)


@mcp.tool()
def stability(model: str, params: dict | None = None) -> dict:
    """Estabilidade estática (gravidade -Z): CM vs polígono de apoio, margem e ângulo de tombamento.
    Inclui as cargas [[carga]] do spec, se houver."""
    return _call("stability", model, *_params(params))


@mcp.tool()
def interference(model: str, params: dict | None = None) -> dict:
    """Lista pares de peças que se interpenetram, com o volume de interseção."""
    return _call("interference", model, *_params(params))


@mcp.tool()
def clearance(model: str, a: str, b: str, params: dict | None = None) -> dict:
    """Distância mínima (mm) entre dois componentes."""
    return _call("clearance", model, "--a", a, "--b", b, *_params(params))


@mcp.tool()
def render(model: str, views: list[str] | None = None, params: dict | None = None) -> dict:
    """Renderiza PNG (vistas iso/frente/topo/direita). Depois use Read no caminho 'png' para VER."""
    v = [x for view in (views or []) for x in ("--view", view)]
    return _call("render", model, *v, *_params(params))


@mcp.tool()
def export(model: str, format: str = "step", view: str | None = None,
           params: dict | None = None) -> dict:
    """Exporta: step | stl | dxf | svg (desenho 2D ortográfico; view=frente/topo/direita) | ifc."""
    v = ["--view", view] if view else []
    return _call("export", model, "--format", format, *v, *_params(params))


if __name__ == "__main__":
    mcp.run()
