import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, Polygon
from matplotlib.path import Path
from matplotlib.patches import PathPatch

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "Liberation Sans"]
plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42

BLUE = "#0F4D92"
BLUE2 = "#3775BA"
TEAL = "#42949E"
GREEN = "#8BCF8B"
GREEN_L = "#DDF3DE"
RED = "#B64342"
RED_L = "#F6CFCB"
GOLD = "#D99A21"
GREY = "#767676"
DARK = "#272727"
LIGHT = "#EEF2F5"
VIOLET = "#9A4D8E"


def box(ax, xy, w, h, text, fc="white", ec=DARK, lw=1.2, fs=7.4, bold=False):
    x, y = xy
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.018,rounding_size=0.035",
        linewidth=lw, edgecolor=ec, facecolor=fc
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color=DARK, fontweight="bold" if bold else "normal",
            linespacing=1.15)
    return patch


def arrow(ax, start, end, color=DARK, lw=1.2, style="-|>", rad=0.0, ms=9):
    ax.annotate(
        "", xy=end, xytext=start,
        arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                        shrinkA=2, shrinkB=2, mutation_scale=ms,
                        connectionstyle=f"arc3,rad={rad}")
    )


def label(ax, x, y, text, fs=7, color=DARK, ha="center", va="center", weight="normal"):
    ax.text(x, y, text, fontsize=fs, color=color, ha=ha, va=va,
            fontweight=weight, linespacing=1.15)


def draw_power_icon(ax, x, y, s=0.06, color=BLUE):
    pts = [(x - s, y - s * 0.9), (x, y + s), (x + s, y - s * 0.9)]
    ax.add_patch(Polygon(pts, closed=True, fill=False, edgecolor=color, linewidth=1.2))
    ax.plot([x, x], [y + s * 0.8, y - s * 0.9], color=color, lw=1.2)
    ax.plot([x - s * 0.45, x + s * 0.45], [y - s * 0.15, y - s * 0.15], color=color, lw=1.2)
    ax.plot([x - s * 0.7, x + s * 0.7], [y - s * 0.5, y - s * 0.5], color=color, lw=1.2)


def save(fig, name):
    for ext in ("svg", "pdf", "eps", "png"):
        fig.savefig(f"figures/{name}.{ext}", bbox_inches="tight", dpi=600)
    plt.close(fig)


def scenario_figure():
    fig, ax = plt.subplots(figsize=(7.15, 3.45))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    label(ax, 0.02, 0.98, "a", fs=9, ha="left", va="top", weight="bold")

    ax.add_patch(Rectangle((0.03, 0.58), 0.94, 0.34, facecolor="#F4F7FA", edgecolor="none"))
    ax.add_patch(Rectangle((0.03, 0.10), 0.94, 0.36, facecolor="#F9F7F1", edgecolor="none"))
    label(ax, 0.055, 0.89, "Cyber/control layer", fs=7.6, ha="left", weight="bold", color=BLUE)
    label(ax, 0.055, 0.42, "Physical distribution layer", fs=7.6, ha="left", weight="bold", color=GOLD)

    center = box(ax, (0.08, 0.72), 0.15, 0.10, "Control\ncenter", fc="#EAF1FA", ec=BLUE, fs=7.2, bold=True)
    edge1 = box(ax, (0.34, 0.75), 0.13, 0.08, "Substation\nedge", fc="#EAF1FA", ec=BLUE2, fs=6.8)
    edge2 = box(ax, (0.58, 0.75), 0.13, 0.08, "Feeder\nagent", fc="#EAF1FA", ec=BLUE2, fs=6.8)
    micro = box(ax, (0.77, 0.69), 0.13, 0.08, "Microgrid\nagent", fc="#E9F7F0", ec=TEAL, fs=6.8)
    for x, y in [(0.28, 0.68), (0.51, 0.67), (0.74, 0.64)]:
        ax.add_patch(Circle((x, y), 0.014, facecolor="white", edgecolor=GREY, lw=1.0))
    arrow(ax, (0.23, 0.77), (0.34, 0.79), BLUE2)
    arrow(ax, (0.47, 0.79), (0.58, 0.79), BLUE2)
    arrow(ax, (0.71, 0.78), (0.77, 0.73), TEAL)
    arrow(ax, (0.58, 0.75), (0.42, 0.45), GREY, rad=-0.08)
    arrow(ax, (0.77, 0.69), (0.70, 0.37), TEAL, rad=-0.08)

    ax.plot([0.10, 0.22, 0.34, 0.47, 0.60, 0.73, 0.88],
            [0.28, 0.30, 0.30, 0.31, 0.29, 0.29, 0.31],
            color=DARK, lw=1.6)
    for x in [0.22, 0.34, 0.47, 0.60, 0.73, 0.88]:
        ax.add_patch(Circle((x, 0.30 if x != 0.47 else 0.31), 0.015, facecolor="white", edgecolor=DARK, lw=1.1))
    draw_power_icon(ax, 0.105, 0.28, s=0.045, color=GOLD)
    for x, txt in [(0.34, "IED/\nrelay"), (0.60, "switch"), (0.73, "DG"), (0.88, "critical\nload")]:
        label(ax, x, 0.20, txt, fs=6.6)
    ax.plot([0.34, 0.34], [0.315, 0.50], color=GREY, lw=1.0, ls="--")
    ax.plot([0.60, 0.60], [0.305, 0.52], color=GREY, lw=1.0, ls="--")
    ax.plot([0.73, 0.73], [0.305, 0.52], color=GREY, lw=1.0, ls="--")

    ax.plot([0.49, 0.57], [0.32, 0.32], color=RED, lw=3.0)
    label(ax, 0.53, 0.38, "line fault", fs=6.6, color=RED, weight="bold")
    ax.plot([0.50, 0.56], [0.66, 0.68], color=RED, lw=2.2, ls="--")
    label(ax, 0.535, 0.60, "lost / delayed\ncommands", fs=6.5, color=RED)
    ax.add_patch(FancyBboxPatch((0.18, 0.12), 0.17, 0.09, boxstyle="round,pad=0.012",
                                facecolor=RED_L, edgecolor=RED, lw=1.0))
    label(ax, 0.265, 0.165, "partial\nobservability", fs=6.5, color=DARK)
    ax.add_patch(FancyBboxPatch((0.46, 0.12), 0.16, 0.09, boxstyle="round,pad=0.012",
                                facecolor="#FFF2CC", edgecolor=GOLD, lw=1.0))
    label(ax, 0.54, 0.165, "hard power-flow\nconstraints", fs=6.5, color=DARK)
    ax.add_patch(FancyBboxPatch((0.70, 0.12), 0.17, 0.09, boxstyle="round,pad=0.012",
                                facecolor=GREEN_L, edgecolor=TEAL, lw=1.0))
    label(ax, 0.785, 0.165, "distributed\nrestoration agents", fs=6.5, color=DARK)

    box(ax, (0.36, 0.49), 0.29, 0.105,
        "Restoration need:\nquery cross-layer evidence, learn coordinated actions,\nexecute only rule- and physics-feasible controls",
        fc="white", ec=DARK, fs=6.4, bold=False)
    arrow(ax, (0.51, 0.49), (0.54, 0.40), DARK, rad=0.05)
    save(fig, "power_cps_scenario")


def architecture_figure():
    fig, ax = plt.subplots(figsize=(7.2, 4.05))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    label(ax, 0.02, 0.98, "a", fs=9, ha="left", va="top", weight="bold")

    box(ax, (0.04, 0.72), 0.16, 0.12, "Evidence stream\nfaults, alarms,\ncyber status", fc="#F7ECEB", ec=RED, fs=6.7, bold=True)
    box(ax, (0.26, 0.68), 0.22, 0.20, "Dynamic power-CPS KG\nentities: device/state/action/rule\nrelations: controls, depends-on,\nviolates, relieves, precedes\nmemory: outcome and provenance", fc="#EEF5EE", ec=TEAL, fs=6.25, bold=True)
    box(ax, (0.55, 0.74), 0.16, 0.10, "Task subgraph\nfault k-hop region\ncandidate actions", fc="#F4F7FA", ec=BLUE2, fs=6.5)
    box(ax, (0.78, 0.74), 0.17, 0.10, "Relation-aware\nGAT encoder\nsemantic state st", fc="#EAF1FA", ec=BLUE, fs=6.5)
    arrow(ax, (0.20, 0.78), (0.26, 0.78), RED)
    arrow(ax, (0.48, 0.78), (0.55, 0.79), TEAL)
    arrow(ax, (0.71, 0.79), (0.78, 0.79), BLUE2)

    ax.add_patch(Rectangle((0.03, 0.39), 0.94, 0.20, facecolor="#F8F8FB", edgecolor="#D8D8D8", lw=0.8))
    label(ax, 0.055, 0.565, "Federated CTDE multi-agent learning", fs=7.3, ha="left", weight="bold", color=VIOLET)
    for i, (x, name) in enumerate([(0.10, "substation\nactor"), (0.27, "feeder\nactor"),
                                   (0.44, "microgrid\nactor"), (0.61, "comm.\nrepair actor")]):
        box(ax, (x, 0.43), 0.115, 0.085, name, fc="white", ec=VIOLET, fs=6.3)
        arrow(ax, (0.865, 0.74), (x + 0.058, 0.515), BLUE, rad=0.08 - i * 0.035, ms=7)
    box(ax, (0.77, 0.43), 0.15, 0.085, "centralized\nsemantic critic", fc="#F1EAF4", ec=VIOLET, fs=6.4, bold=True)
    for x in [0.157, 0.327, 0.497, 0.667]:
        arrow(ax, (x, 0.43), (0.77, 0.47), VIOLET, rad=0.04, ms=7)
    arrow(ax, (0.845, 0.43), (0.845, 0.34), VIOLET)

    box(ax, (0.58, 0.20), 0.22, 0.105, "Semantic safety filter\nKG rule query + power-flow,\nradiality and cyber prerequisite checks", fc="#FFF7E6", ec=GOLD, fs=6.25, bold=True)
    box(ax, (0.30, 0.20), 0.18, 0.105, "Feasible restoration\nswitching, load transfer,\nDG/storage, cyber reroute", fc="#EAF1FA", ec=BLUE2, fs=6.25)
    box(ax, (0.06, 0.20), 0.16, 0.105, "Execution\nand field response", fc="white", ec=DARK, fs=6.5)
    arrow(ax, (0.77, 0.43), (0.71, 0.305), VIOLET, rad=-0.05)
    arrow(ax, (0.58, 0.255), (0.48, 0.255), GOLD)
    arrow(ax, (0.30, 0.255), (0.22, 0.255), BLUE2)
    arrow(ax, (0.14, 0.20), (0.26, 0.68), TEAL, rad=-0.35)
    label(ax, 0.17, 0.50, "outcome write-back:\nrecovered load, violations,\ntime, success paths", fs=6.1, color=TEAL, ha="center")

    box(ax, (0.06, 0.045), 0.86, 0.085,
        "Cross-layer design principle: the KG is simultaneously semantic state, constraint carrier, and restoration memory; learning proposes actions, but execution is gated by encoded rules and physical checks.",
        fc=LIGHT, ec="#BFC7CF", fs=6.2)
    save(fig, "kgfedmarl_architecture")


if __name__ == "__main__":
    scenario_figure()
    architecture_figure()
