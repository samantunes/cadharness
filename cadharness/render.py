"""Renderização para o agente *ver* o modelo (PNG legível pela ferramenta Read)."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .model import Component

PALETTE = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2", "#EECA3B",
           "#B279A2", "#FF9DA6", "#9D755D", "#BAB0AC"]

VIEWS = {
    "iso": (30, -60),
    "frente": (0, -90),   # olhando +Y (plano XZ)
    "topo": (90, -90),    # olhando -Z (plano XY)
    "direita": (0, 0),    # olhando -X (plano YZ)
}


def _mesh(shape, tol: float):
    verts, tris = shape.tessellate(tol, 0.3)
    v = np.array([tuple(p) for p in verts])
    t = np.array(tris, dtype=int)
    return v, t


def render(comps: list[Component], out: str | Path, views: list[str] | None = None,
           tol: float = 0.5, title: str | None = None) -> dict:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    views = views or ["iso", "frente", "topo", "direita"]
    bad = [v for v in views if v not in VIEWS]
    if bad:
        raise ValueError(f"Vistas inválidas {bad}; use {list(VIEWS)}")

    meshes = []
    for i, c in enumerate(comps):
        v, t = _mesh(c.shape, tol)
        meshes.append((c, v, t, PALETTE[i % len(PALETTE)]))
    allv = np.vstack([m[1] for m in meshes])
    lo, hi = allv.min(0), allv.max(0)
    span = np.maximum(hi - lo, 1e-6)
    light = np.array([0.4, -0.5, 0.75])
    light /= np.linalg.norm(light)

    n = len(views)
    cols = 2 if n > 1 else 1
    rows = (n + 1) // 2
    fig = plt.figure(figsize=(6 * cols, 5 * rows), dpi=110)
    for k, view in enumerate(views):
        ax = fig.add_subplot(rows, cols, k + 1, projection="3d")
        ax.set_proj_type("ortho")
        for c, v, t, color in meshes:
            tri = v[t]
            nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
            nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
            shade = 0.45 + 0.55 * np.clip(nrm @ light, 0, 1)
            base = np.array(matplotlib.colors.to_rgb(color))
            fc = np.clip(base[None, :] * shade[:, None], 0, 1)
            pc = Poly3DCollection(tri, facecolors=fc, edgecolors=fc, linewidths=0.3)
            ax.add_collection3d(pc)
        ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
        ax.set_box_aspect(tuple(span))
        ax.view_init(*VIEWS[view])
        ax.set_xlabel("X [mm]"); ax.set_ylabel("Y [mm]"); ax.set_zlabel("Z [mm]")
        ax.set_title(view)
        hide = {"frente": "y", "topo": "z", "direita": "x"}.get(view)
        if hide:  # eixo de profundidade não carrega informação na vista ortográfica
            getattr(ax, f"set_{hide}ticks")([])
            getattr(ax, f"set_{hide}label")("")
        ax.tick_params(labelsize=7)
    handles = [Patch(color=col, label=f"{c.name} ({c.material})") for c, _, _, col in meshes]
    fig.legend(handles=handles, loc="lower center", ncol=min(4, len(handles)), fontsize=8)
    if title:
        fig.suptitle(title)
    fig.tight_layout(rect=(0, 0.06, 1, 0.97))
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    return {"png": str(out), "views": views,
            "bbox_mm": {"min": lo.round(2).tolist(), "max": hi.round(2).tolist()}}
