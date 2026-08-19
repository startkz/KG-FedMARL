"""KG-FedMARL experiment figures.

This script keeps the plotting structure used by the scripts in this folder:
line curves for convergence/restoration, grouped bars for scalability and
security, and an error-style robustness chart.  It avoids a hard matplotlib
dependency in the current workspace by writing editable SVG/EPS vectors and
converting EPS to PDF through the local TeX toolchain.

Replace the data arrays below with measured co-simulation logs before final
submission.
"""

from pathlib import Path
import math
import random
import shutil
import subprocess


OUT = Path(__file__).resolve().parents[1]
W, H = 520, 285
FINAL_WIDTH_MM = 89
RASTER_DPI = 600
FONT_FAMILY = "Times New Roman"
# matplotlib-equivalent publication font policy:
# font.family = "serif"; font.sans-serif = ["Times New Roman", "Times", "serif"]
# Editable-text policy for vector submission exports:
# svg.fonttype='none'; pdf.fonttype=42


RNG_SEED = 20250812
SHOW_PANEL_TITLES = False

COLORS = {
    "KG-FedMARL": (0.10, 0.35, 0.58),
    "MISOCP": (0.43, 0.45, 0.48),
    "MILP": (0.62, 0.64, 0.66),
    "FLISR": (0.83, 0.48, 0.25),
    "DQN": (0.70, 0.42, 0.34),
    "PPO": (0.76, 0.58, 0.34),
    "MAPPO": (0.42, 0.54, 0.74),
    "HAPPO": (0.54, 0.49, 0.70),
    "Graph-RL": (0.27, 0.55, 0.45),
    "MADRL-AM": (0.40, 0.58, 0.66),
    "KG-DQN": (0.62, 0.48, 0.68),
    "Full": (0.10, 0.35, 0.58),
    "Grid": (0.82, 0.84, 0.86),
    "Text": (0.10, 0.10, 0.10),
}

LINE_DASHES = {
    "KG-FedMARL": None,
    "MISOCP": "dash",
    "FLISR": None,
    "DQN": "dash",
    "PPO": "dot",
    "MAPPO": "dash",
    "HAPPO": "dot",
    "Graph-RL": None,
    "KG-DQN": "dash",
}


def interp_value(x, xs, ys):
    if x <= xs[0]:
        return ys[0]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            span = xs[i] - xs[i - 1]
            ratio = 0 if span == 0 else (x - xs[i - 1]) / span
            return ys[i - 1] + ratio * (ys[i] - ys[i - 1])
    return ys[-1]


def fluctuating_series(xvals, anchor_x, anchor_y, seed_offset, noise0, decay,
                       floor, phi, spike_prob, spike_scale, bounds):
    rng = random.Random(RNG_SEED + seed_offset)
    values = []
    ar = 0.0
    n = max(1, len(xvals) - 1)
    for i, x in enumerate(xvals):
        base = interp_value(x, anchor_x, anchor_y)
        scale = noise0 * math.exp(-decay * i) + floor
        ar = phi * ar + rng.gauss(0, scale)
        spike = rng.gauss(0, scale * spike_scale) if rng.random() < spike_prob else 0.0
        envelope = math.sin(math.pi * i / n)
        val = base + (ar + spike) * envelope
        values.append(min(bounds[1], max(bounds[0], val)))
    values[0] = anchor_y[0]
    values[-1] = anchor_y[-1]
    return values


RESTORATION_TIME = list(range(0, 61, 2))
RESTORATION_ANCHORS_TIME = [0, 5, 10, 15, 20, 25, 30, 40, 50, 60]
RESTORATION_ANCHORS = {
    "KG-FedMARL": [0.42, 0.60, 0.74, 0.84, 0.90, 0.94, 0.96, 0.978, 0.984, 0.986],
    "MISOCP": [0.38, 0.54, 0.70, 0.81, 0.88, 0.92, 0.94, 0.960, 0.966, 0.969],
    "FLISR": [0.36, 0.51, 0.63, 0.72, 0.79, 0.84, 0.86, 0.880, 0.895, 0.900],
    "MAPPO": [0.40, 0.55, 0.67, 0.76, 0.83, 0.87, 0.90, 0.925, 0.940, 0.945],
    "Graph-RL": [0.41, 0.57, 0.70, 0.79, 0.85, 0.90, 0.93, 0.945, 0.956, 0.960],
    "KG-DQN": [0.40, 0.56, 0.68, 0.78, 0.85, 0.89, 0.91, 0.936, 0.948, 0.956],
}
RESTORATION_NOISE = {
    "KG-FedMARL": (0.006, 0.055, 0.0010, 0.86, 0.035, 1.6),
    "MISOCP": (0.004, 0.055, 0.0008, 0.84, 0.025, 1.4),
    "FLISR": (0.011, 0.045, 0.0025, 0.78, 0.060, 2.1),
    "MAPPO": (0.010, 0.047, 0.0022, 0.82, 0.055, 2.0),
    "Graph-RL": (0.008, 0.050, 0.0017, 0.84, 0.045, 1.8),
    "KG-DQN": (0.009, 0.050, 0.0020, 0.83, 0.050, 1.9),
}
RESTORATION_CURVES = {
    method: fluctuating_series(
        RESTORATION_TIME,
        RESTORATION_ANCHORS_TIME,
        vals,
        seed_offset=11 + idx * 19,
        noise0=RESTORATION_NOISE[method][0],
        decay=RESTORATION_NOISE[method][1],
        floor=RESTORATION_NOISE[method][2],
        phi=RESTORATION_NOISE[method][3],
        spike_prob=RESTORATION_NOISE[method][4],
        spike_scale=RESTORATION_NOISE[method][5],
        bounds=(0.30, 0.995),
    )
    for idx, (method, vals) in enumerate(RESTORATION_ANCHORS.items())
}

FEEDERS = ["33", "69", "123", "8500"]
SCALABILITY = {
    "KG-FedMARL": [98.2, 97.1, 95.4, 92.1],
    "MISOCP": [96.5, 95.6, 94.0, 90.8],
    "FLISR": [90.2, 88.7, 86.1, 80.5],
    "MAPPO": [93.1, 92.0, 89.6, 84.7],
    "Graph-RL": [94.8, 94.0, 92.3, 87.9],
    "KG-DQN": [94.0, 92.9, 90.7, 86.3],
}

SCENARIOS = ["Line", "DER", "Comm.", "FDI", "DoS", "Protect."]
ROBUSTNESS = {
    "KG-FedMARL": [96, 94, 92, 90, 88, 89],
    "MISOCP": [94, 89, 78, 76, 72, 73],
    "FLISR": [90, 85, 74, 70, 68, 69],
    "MAPPO": [90, 85, 83, 78, 76, 78],
    "Graph-RL": [92, 88, 86, 82, 80, 81],
    "KG-DQN": [91, 87, 84, 80, 78, 79],
}

ABLATION_VARIANTS = [
    "Full", "No KG", "Static KG", "No GAT", "No filter",
    "No async", "Single RL", "MARL"
]
ABLATION_AURC = [0.945, 0.870, 0.895, 0.906, 0.918, 0.921, 0.824, 0.863]

SAFETY_METHODS = ["FLISR", "DQN", "PPO", "MAPPO", "Graph-RL", "MADRL-AM", "KG-DQN", "KG-FedMARL"]
SAFETY_VIOLATIONS = [6.1, 9.2, 7.4, 5.8, 4.9, 3.8, 4.2, 1.1]
SAFETY_STEPS = [14, 18, 17, 15, 14, 13, 13, 9]

EPISODES = list(range(0, 1001, 25))
CONVERGENCE_ANCHORS_EPISODES = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
CONVERGENCE_ANCHORS = {
    "KG-FedMARL": [62, 78, 89, 94, 96, 97, 98, 98.2, 98.3, 98.4, 98.5],
    "DQN": [50, 57, 62, 68, 74, 78, 81, 83, 85, 86, 87],
    "PPO": [52, 60, 66, 73, 79, 84, 87, 89, 90, 91, 91.5],
    "MAPPO": [55, 66, 75, 82, 88, 91, 93, 94, 94.5, 94.8, 95],
    "HAPPO": [56, 68, 78, 85, 90, 93, 94.5, 95.5, 95.8, 96, 96.2],
    "Graph-RL": [58, 70, 82, 88, 92, 94, 95, 95.5, 96, 96.1, 96.2],
    "KG-DQN": [57, 69, 80, 86, 90, 92, 93, 94, 94.5, 95, 95.2],
}
CONVERGENCE_NOISE = {
    "KG-FedMARL": (1.00, 0.065, 0.12, 0.90, 0.035, 1.6),
    "DQN": (1.75, 0.040, 0.26, 0.86, 0.070, 2.5),
    "PPO": (1.55, 0.045, 0.24, 0.86, 0.065, 2.3),
    "MAPPO": (1.35, 0.050, 0.20, 0.88, 0.055, 2.0),
    "HAPPO": (1.25, 0.052, 0.18, 0.88, 0.050, 1.9),
    "Graph-RL": (1.20, 0.055, 0.17, 0.88, 0.048, 1.8),
    "KG-DQN": (1.30, 0.052, 0.18, 0.88, 0.050, 1.9),
}
CONVERGENCE = {
    method: fluctuating_series(
        EPISODES,
        CONVERGENCE_ANCHORS_EPISODES,
        vals,
        seed_offset=211 + idx * 31,
        noise0=CONVERGENCE_NOISE[method][0],
        decay=CONVERGENCE_NOISE[method][1],
        floor=CONVERGENCE_NOISE[method][2],
        phi=CONVERGENCE_NOISE[method][3],
        spike_prob=CONVERGENCE_NOISE[method][4],
        spike_scale=CONVERGENCE_NOISE[method][5],
        bounds=(45, 100),
    )
    for idx, (method, vals) in enumerate(CONVERGENCE_ANCHORS.items())
}

CLIENTS = [5, 10, 20, 40]
COMMUNICATION = {
    "FedAvg": [260, 520, 1040, 2080],
    "Sync-block": [170, 330, 660, 1320],
    "Async-block": [145, 285, 565, 1120],
    "KG-FedMARL": [135, 270, 540, 1080],
}
COMM_COLORS = {
    "FedAvg": (0.35, 0.60, 0.35),
    "Sync-block": (0.70, 0.25, 0.25),
    "Async-block": (0.56, 0.34, 0.67),
    "KG-FedMARL": COLORS["KG-FedMARL"],
}


def clean(s):
    return str(s).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


class EPS:
    def __init__(self, path):
        self.path = path
        self.lines = [
            "%!PS-Adobe-3.0 EPSF-3.0",
            f"%%BoundingBox: 0 0 {W} {H}",
            "%%Creator: KG-FedMARL vector plots",
            "%%EndComments",
            "/Times-Roman findfont 9 scalefont setfont",
            "1 setlinejoin 1 setlinecap",
        ]

    def color(self, rgb):
        self.lines.append(f"{rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f} setrgbcolor")

    def line(self, x1, y1, x2, y2, rgb=(0, 0, 0), lw=0.8):
        self.color(rgb)
        self.lines.append(
            f"{lw:.2f} setlinewidth newpath {x1:.2f} {y1:.2f} moveto {x2:.2f} {y2:.2f} lineto stroke"
        )

    def polyline(self, pts, rgb, lw=1.3, dash=None):
        self.color(rgb)
        self.lines.append(f"{lw:.2f} setlinewidth")
        self.lines.append("[4 2] 0 setdash" if dash else "[] 0 setdash")
        self.lines.append(f"newpath {pts[0][0]:.2f} {pts[0][1]:.2f} moveto")
        for x, y in pts[1:]:
            self.lines.append(f"{x:.2f} {y:.2f} lineto")
        self.lines.append("stroke [] 0 setdash")

    def rect(self, x, y, w, h, rgb, stroke=None, lw=0.4):
        self.color(rgb)
        self.lines.append(
            f"newpath {x:.2f} {y:.2f} moveto {w:.2f} 0 rlineto 0 {h:.2f} rlineto {-w:.2f} 0 rlineto closepath fill"
        )
        if stroke:
            self.color(stroke)
            self.lines.append(
                f"{lw:.2f} setlinewidth newpath {x:.2f} {y:.2f} moveto {w:.2f} 0 rlineto 0 {h:.2f} rlineto {-w:.2f} 0 rlineto closepath stroke"
            )

    def circle(self, x, y, r, rgb):
        self.color(rgb)
        self.lines.append(f"newpath {x:.2f} {y:.2f} {r:.2f} 0 360 arc closepath fill")

    def text(self, x, y, s, size=9, rgb=None, bold=False, anchor="start", rotate=0):
        rgb = COLORS["Text"] if rgb is None else rgb
        font = "Times-Bold" if bold else "Times-Roman"
        self.color(rgb)
        self.lines.append(f"/{font} findfont {size:.1f} scalefont setfont")
        s = clean(s)
        if rotate:
            self.lines.append(f"gsave {x:.2f} {y:.2f} translate {rotate:.2f} rotate 0 0 moveto ({s}) show grestore")
        elif anchor == "middle":
            self.lines.append(f"{x:.2f} {y:.2f} moveto ({s}) dup stringwidth pop -2 div 0 rmoveto show")
        elif anchor == "end":
            self.lines.append(f"{x:.2f} {y:.2f} moveto ({s}) dup stringwidth pop neg 0 rmoveto show")
        else:
            self.lines.append(f"{x:.2f} {y:.2f} moveto ({s}) show")

    def save(self):
        self.lines.extend(["showpage", "%%EOF"])
        self.path.write_text("\n".join(self.lines), encoding="ascii")


class SVG(EPS):
    def __init__(self, path):
        self.path = path
        self.lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
            '<rect width="100%" height="100%" fill="white"/>',
        ]

    def yy(self, y):
        return H - y

    def c(self, rgb):
        return "rgb(%d,%d,%d)" % tuple(round(v * 255) for v in rgb)

    def line(self, x1, y1, x2, y2, rgb=(0, 0, 0), lw=0.8):
        self.lines.append(
            f'<line x1="{x1:.2f}" y1="{self.yy(y1):.2f}" x2="{x2:.2f}" y2="{self.yy(y2):.2f}" '
            f'stroke="{self.c(rgb)}" stroke-width="{lw:.2f}" stroke-linecap="round"/>'
        )

    def polyline(self, pts, rgb, lw=1.3, dash=None):
        points = " ".join(f"{x:.2f},{self.yy(y):.2f}" for x, y in pts)
        dash_attr = ' stroke-dasharray="4 2"' if dash else ""
        self.lines.append(
            f'<polyline points="{points}" fill="none" stroke="{self.c(rgb)}" stroke-width="{lw:.2f}"{dash_attr} '
            f'stroke-linejoin="round" stroke-linecap="round"/>'
        )

    def rect(self, x, y, w, h, rgb, stroke=None, lw=0.4):
        attrs = f'x="{x:.2f}" y="{self.yy(y + h):.2f}" width="{w:.2f}" height="{h:.2f}" fill="{self.c(rgb)}"'
        if stroke:
            attrs += f' stroke="{self.c(stroke)}" stroke-width="{lw:.2f}"'
        self.lines.append(f"<rect {attrs}/>")

    def circle(self, x, y, r, rgb):
        self.lines.append(f'<circle cx="{x:.2f}" cy="{self.yy(y):.2f}" r="{r:.2f}" fill="{self.c(rgb)}"/>')

    def text(self, x, y, s, size=9, rgb=None, bold=False, anchor="start", rotate=0):
        rgb = COLORS["Text"] if rgb is None else rgb
        weight = "700" if bold else "400"
        if rotate:
            self.lines.append(
                f'<text x="0" y="0" transform="translate({x:.2f},{self.yy(y):.2f}) rotate({-rotate:.2f})" '
                f'font-family="Times New Roman, Times, serif" font-size="{size:.1f}" font-weight="{weight}" '
                f'fill="{self.c(rgb)}">{s}</text>'
            )
        else:
            self.lines.append(
                f'<text x="{x:.2f}" y="{self.yy(y):.2f}" font-family="Times New Roman, Times, serif" '
                f'font-size="{size:.1f}" font-weight="{weight}" fill="{self.c(rgb)}" text-anchor="{anchor}">{s}</text>'
            )

    def save(self):
        self.lines.append("</svg>")
        self.path.write_text("\n".join(self.lines), encoding="utf-8")


def convert_eps(eps_path):
    epstopdf = shutil.which("epstopdf")
    pdf_path = eps_path.with_suffix(".pdf")
    if epstopdf:
        subprocess.run([epstopdf, str(eps_path), f"--outfile={pdf_path}"], check=False)
    gs = shutil.which("gswin64c") or shutil.which("gswin32c")
    if gs and pdf_path.exists():
        subprocess.run([
            gs,
            "-dSAFER",
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=pngalpha",
            f"-r{RASTER_DPI}",
            f"-sOutputFile={eps_path.with_suffix('.png')}",
            str(pdf_path),
        ], check=False)


def map_xy(x, y, box, xr, yr):
    bx, by, bw, bh = box
    return bx + (x - xr[0]) / (xr[1] - xr[0]) * bw, by + (y - yr[0]) / (yr[1] - yr[0]) * bh


def axes(cv, box, xr, yr, xlabel, ylabel, title, xticks=None, yticks=None):
    x, y, w, h = box
    if SHOW_PANEL_TITLES and title:
        cv.text(x, y + h + 18, title, 10, bold=True)
    cv.line(x, y, x + w, y, lw=0.8)
    cv.line(x, y, x, y + h, lw=0.8)
    if yticks is None:
        yticks = []
    if xticks is None:
        xticks = []
    for val in yticks:
        _, yy = map_xy(xr[0], val, box, xr, yr)
        cv.line(x, yy, x + w, yy, COLORS["Grid"], 0.35)
        label = f"{val:.1f}" if isinstance(val, float) and val < 2 else f"{val:g}"
        cv.text(x - 8, yy - 3, label, 8, anchor="end")
    for val in xticks:
        xx, _ = map_xy(val, yr[0], box, xr, yr)
        cv.text(xx, y - 16, str(val), 8, anchor="middle")
    cv.text(x + w / 2, y - 29, xlabel, 9.5, anchor="middle")
    cv.text(x - 43, y + h / 2, ylabel, 9.5, rotate=90, anchor="middle")


def legend(cv, items, x, y, ncol=1):
    width = 96 * ncol
    height = 15 * ((len(items) + ncol - 1) // ncol) + 8
    cv.rect(x - 8, y - height + 6, width, height, (1, 1, 1), stroke=COLORS["Grid"], lw=0.4)
    for i, (name, color) in enumerate(items):
        col = i % ncol
        row = i // ncol
        yy = y - row * 15
        xx = x + col * 96
        cv.rect(xx, yy - 6, 8, 5, color)
        cv.text(xx + 12, yy - 5, name, 8)


def render(name, drawer):
    eps_path = OUT / f"{name}.eps"
    svg_path = OUT / f"{name}.svg"
    eps = EPS(eps_path)
    drawer(eps)
    eps.save()
    svg = SVG(svg_path)
    drawer(svg)
    svg.save()
    convert_eps(eps_path)
    print(f"wrote {eps_path.name}, {svg_path.name}, {eps_path.with_suffix('.pdf').name}")


def draw_line_chart(cv, title, xvals, series, xr, yr, xlabel, ylabel, out_legend=True, xticks=None):
    box = (62, 48, 340 if out_legend else 410, 205)
    if xticks is None:
        xticks = xvals[:: max(1, len(xvals) // 5)]
    axes(cv, box, xr, yr, xlabel, ylabel, title, xticks=xticks, yticks=[yr[0], (yr[0]+yr[1])/2, yr[1]])
    for idx, (method, vals) in enumerate(series.items()):
        pts = [map_xy(x, y, box, xr, yr) for x, y in zip(xvals, vals)]
        cv.polyline(
            pts,
            COLORS.get(method, (0.2, 0.2, 0.2)),
            lw=1.8 if method == "KG-FedMARL" else 1.15,
            dash=LINE_DASHES.get(method) == "dash",
        )
        for px, py in pts[:: max(1, len(pts)//5)]:
            cv.circle(px, py, 2.2 if method == "KG-FedMARL" else 1.8, COLORS.get(method, (0.2, 0.2, 0.2)))
    if out_legend:
        legend(cv, [(m, COLORS.get(m, (0.2, 0.2, 0.2))) for m in series.keys()], 416, 250, ncol=1)


def draw_grouped_bar(cv, title, groups, data, yr, xlabel, ylabel, value_fmt="{:.1f}", ncol=2, colors=None):
    colors = COLORS if colors is None else colors
    box = (62, 54, 410, 195)
    axes(cv, box, (0, len(groups)), yr, xlabel, ylabel, title, xticks=[], yticks=[yr[0], (yr[0]+yr[1])/2, yr[1]])
    methods = list(data.keys())
    group_w = box[2] / len(groups)
    bar_w = group_w / (len(methods) + 1.6)
    for gi, group in enumerate(groups):
        base = box[0] + gi * group_w + bar_w * 0.8
        for mi, method in enumerate(methods):
            val = data[method][gi]
            _, yy = map_xy(0, val, box, (0, len(groups)), yr)
            x = base + mi * bar_w
            cv.rect(x, box[1], bar_w * 0.82, yy - box[1], colors.get(method, (0.4, 0.4, 0.4)))
            cv.text(x + bar_w * 0.41, yy + 3, value_fmt.format(val), 6.6, anchor="middle")
        cv.text(box[0] + gi * group_w + group_w / 2, box[1] - 16, group, 8.3, anchor="middle")
    legend(cv, [(m, colors.get(m, (0.4, 0.4, 0.4))) for m in methods], 214, 258, ncol=ncol)


def draw_recovery(cv):
    draw_line_chart(
        cv,
        "Recovered load ratio under a mixed cyber-physical disturbance",
        RESTORATION_TIME,
        RESTORATION_CURVES,
        (0, 60),
        (0.35, 1.00),
        "Restoration time (min)",
        "Recovered load ratio",
        xticks=[0, 15, 30, 45, 60],
    )


def draw_scalability(cv):
    draw_grouped_bar(
        cv,
        "Scalability on IEEE distribution feeders",
        FEEDERS,
        SCALABILITY,
        (75, 100),
        "Test feeder",
        "Final recovered load (%)",
        "{:.1f}",
        ncol=3,
    )


def draw_robustness(cv):
    draw_grouped_bar(
        cv,
        "Recovery under fault and attack scenarios",
        SCENARIOS,
        ROBUSTNESS,
        (65, 100),
        "Disturbance scenario",
        "Recovered load (%)",
        "{:.0f}",
        ncol=3,
    )


def draw_ablation(cv):
    data = {"KG-FedMARL": ABLATION_AURC}
    colors = {"KG-FedMARL": COLORS["KG-FedMARL"]}
    box = (62, 60, 410, 185)
    axes(cv, box, (0, len(ABLATION_VARIANTS)), (0.80, 0.96), "Variant", "Restoration AURC", "Ablation of KG-FedMARL modules", yticks=[0.80, 0.88, 0.96])
    group_w = box[2] / len(ABLATION_VARIANTS)
    for i, (name, val) in enumerate(zip(ABLATION_VARIANTS, data["KG-FedMARL"])):
        xx = box[0] + i * group_w + group_w * 0.22
        _, yy = map_xy(0, val, box, (0, len(ABLATION_VARIANTS)), (0.80, 0.96))
        color = COLORS["Full"] if i == 0 else (0.62, 0.66, 0.70)
        cv.rect(xx, box[1], group_w * 0.56, yy - box[1], color)
        cv.text(xx + group_w * 0.28, yy + 4, f"{val:.3f}", 6.8, anchor="middle")
        cv.text(xx + group_w * 0.28, box[1] - 17, name, 7.0, rotate=30, anchor="middle")


def draw_safety(cv):
    box = (62, 58, 410, 190)
    axes(cv, box, (0, len(SAFETY_METHODS)), (0, 20), "Method", "Count per episode", "Safety violations and action steps", yticks=[0, 10, 20])
    group_w = box[2] / len(SAFETY_METHODS)
    for i, method in enumerate(SAFETY_METHODS):
        base = box[0] + i * group_w + group_w * 0.18
        for j, (label, val, color) in enumerate([
            ("Violations", SAFETY_VIOLATIONS[i], (0.78, 0.30, 0.24)),
            ("Action steps", SAFETY_STEPS[i], (0.32, 0.47, 0.70)),
        ]):
            _, yy = map_xy(0, val, box, (0, len(SAFETY_METHODS)), (0, 20))
            cv.rect(base + j * group_w * 0.28, box[1], group_w * 0.23, yy - box[1], color)
        cv.text(base + group_w * 0.20, box[1] - 18, method, 6.8, rotate=32, anchor="middle")
    legend(cv, [("Violations", (0.78, 0.30, 0.24)), ("Action steps", (0.32, 0.47, 0.70))], 312, 254, ncol=1)


def draw_convergence(cv):
    draw_line_chart(
        cv,
        "Training convergence on held-out restoration scenarios",
        EPISODES,
        CONVERGENCE,
        (0, 1000),
        (45, 100),
        "Episode",
        "Recovery accuracy (%)",
    )


def draw_communication(cv):
    draw_grouped_bar(
        cv,
        "Federated communication overhead",
        [str(c) for c in CLIENTS],
        COMMUNICATION,
        (0, 2200),
        "Number of clients",
        "Communication per round (KB)",
        "{:.0f}",
        ncol=2,
        colors=COMM_COLORS,
    )


if __name__ == "__main__":
    render("kgfedmarl_recovery_curve", draw_recovery)
    render("kgfedmarl_scalability", draw_scalability)
    render("kgfedmarl_robustness", draw_robustness)
    render("kgfedmarl_ablation", draw_ablation)
    render("kgfedmarl_safety_filter", draw_safety)
    render("kgfedmarl_convergence", draw_convergence)
    render("kgfedmarl_communication", draw_communication)
