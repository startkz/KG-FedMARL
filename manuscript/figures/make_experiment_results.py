import shutil
import subprocess
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
W, H = 760, 540
FINAL_WIDTH_MM = 183
RASTER_DPI = 300
# The pure-Python exporter writes live text in SVG/EPS. These strings document
# the same editable-text policy used by matplotlib workflows:
# svg.fonttype='none'; pdf.fonttype=42


def esc(text):
    return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


class EPS:
    def __init__(self, path):
        self.path = path
        self.lines = [
            "%!PS-Adobe-3.0 EPSF-3.0",
            f"%%BoundingBox: 0 0 {W} {H}",
            "%%Creator: KG-FedMARL pure-Python vector exporter",
            "%%EndComments",
            "/Helvetica findfont 7 scalefont setfont",
            "1 setlinejoin 1 setlinecap",
        ]

    def color(self, rgb):
        r, g, b = rgb
        self.lines.append(f"{r:.3f} {g:.3f} {b:.3f} setrgbcolor")

    def line(self, x1, y1, x2, y2, rgb=(0, 0, 0), lw=0.8):
        self.color(rgb)
        self.lines.append(f"{lw:.2f} setlinewidth newpath {x1:.2f} {y1:.2f} moveto {x2:.2f} {y2:.2f} lineto stroke")

    def polyline(self, pts, rgb, lw=1.2):
        self.color(rgb)
        self.lines.append(f"{lw:.2f} setlinewidth newpath {pts[0][0]:.2f} {pts[0][1]:.2f} moveto")
        for x, y in pts[1:]:
            self.lines.append(f"{x:.2f} {y:.2f} lineto")
        self.lines.append("stroke")

    def rect(self, x, y, w, h, rgb, stroke=None, lw=0.5):
        self.color(rgb)
        self.lines.append(f"newpath {x:.2f} {y:.2f} moveto {w:.2f} 0 rlineto 0 {h:.2f} rlineto {-w:.2f} 0 rlineto closepath fill")
        if stroke:
            self.color(stroke)
            self.lines.append(f"{lw:.2f} setlinewidth newpath {x:.2f} {y:.2f} moveto {w:.2f} 0 rlineto 0 {h:.2f} rlineto {-w:.2f} 0 rlineto closepath stroke")

    def text(self, x, y, text, size=7, rgb=(0, 0, 0), bold=False, rotate=0, anchor="start"):
        font = "Helvetica-Bold" if bold else "Helvetica"
        self.color(rgb)
        self.lines.append(f"/{font} findfont {size:.1f} scalefont setfont")
        s = esc(text)
        if rotate:
            self.lines.append(f"gsave {x:.2f} {y:.2f} translate {rotate:.2f} rotate 0 0 moveto ({s}) show grestore")
        elif anchor == "middle":
            self.lines.append(f"{x:.2f} {y:.2f} moveto ({s}) dup stringwidth pop -2 div 0 rmoveto show")
        elif anchor == "end":
            self.lines.append(f"{x:.2f} {y:.2f} moveto ({s}) dup stringwidth pop neg 0 rmoveto show")
        else:
            self.lines.append(f"{x:.2f} {y:.2f} moveto ({s}) show")

    def circle(self, x, y, r, rgb):
        self.color(rgb)
        self.lines.append(f"newpath {x:.2f} {y:.2f} {r:.2f} 0 360 arc closepath fill")

    def save(self):
        self.lines.extend(["showpage", "%%EOF"])
        self.path.write_text("\n".join(self.lines), encoding="ascii")


class SVG:
    def __init__(self, path):
        self.path = path
        self.lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
            '<rect width="100%" height="100%" fill="white"/>',
        ]

    def y(self, y):
        return H - y

    def color(self, rgb):
        return "rgb(%d,%d,%d)" % tuple(round(v * 255) for v in rgb)

    def line(self, x1, y1, x2, y2, rgb=(0, 0, 0), lw=0.8):
        self.lines.append(f'<line x1="{x1:.2f}" y1="{self.y(y1):.2f}" x2="{x2:.2f}" y2="{self.y(y2):.2f}" stroke="{self.color(rgb)}" stroke-width="{lw:.2f}" stroke-linecap="round"/>')

    def polyline(self, pts, rgb, lw=1.2):
        points = " ".join(f"{x:.2f},{self.y(y):.2f}" for x, y in pts)
        self.lines.append(f'<polyline points="{points}" fill="none" stroke="{self.color(rgb)}" stroke-width="{lw:.2f}" stroke-linejoin="round" stroke-linecap="round"/>')

    def rect(self, x, y, w, h, rgb, stroke=None, lw=0.5):
        attrs = f'x="{x:.2f}" y="{self.y(y + h):.2f}" width="{w:.2f}" height="{h:.2f}" fill="{self.color(rgb)}"'
        if stroke:
            attrs += f' stroke="{self.color(stroke)}" stroke-width="{lw:.2f}"'
        self.lines.append(f"<rect {attrs}/>")

    def text(self, x, y, text, size=7, rgb=(0, 0, 0), bold=False, rotate=0, anchor="start"):
        weight = "700" if bold else "400"
        if rotate:
            transform = f' transform="translate({x:.2f},{self.y(y):.2f}) rotate({-rotate:.2f})"'
            self.lines.append(f'<text x="0" y="0"{transform} font-family="Arial, Helvetica, sans-serif" font-size="{size:.1f}" font-weight="{weight}" fill="{self.color(rgb)}">{text}</text>')
        else:
            self.lines.append(f'<text x="{x:.2f}" y="{self.y(y):.2f}" font-family="Arial, Helvetica, sans-serif" font-size="{size:.1f}" font-weight="{weight}" fill="{self.color(rgb)}" text-anchor="{anchor}">{text}</text>')

    def circle(self, x, y, r, rgb):
        self.lines.append(f'<circle cx="{x:.2f}" cy="{self.y(y):.2f}" r="{r:.2f}" fill="{self.color(rgb)}"/>')

    def save(self):
        self.lines.append("</svg>")
        self.path.write_text("\n".join(self.lines), encoding="utf-8")


COL = {
    "kg": (0.02, 0.36, 0.47),
    "milp": (0.42, 0.42, 0.42),
    "flisr": (0.82, 0.42, 0.18),
    "map": (0.38, 0.50, 0.74),
    "graph": (0.18, 0.55, 0.35),
    "kgdqn": (0.58, 0.40, 0.67),
    "light": (0.92, 0.94, 0.95),
    "grid": (0.82, 0.84, 0.86),
}


def panel_origin(idx):
    col = idx % 3
    row = 1 - idx // 3
    x = 35 + col * 235
    y = 45 + row * 235
    return x, y, 210, 190


def axes(canvas, x, y, w, h, title, label, ylab=None, xlab=None):
    canvas.text(x - 22, y + h + 7, label, 8.5, bold=True)
    canvas.text(x, y + h + 7, title, 8, bold=True)
    canvas.line(x, y, x + w, y, (0, 0, 0), 0.7)
    canvas.line(x, y, x, y + h, (0, 0, 0), 0.7)
    for frac in (0.25, 0.5, 0.75, 1.0):
        yy = y + h * frac
        canvas.line(x, yy, x + w, yy, COL["grid"], 0.25)
    if ylab:
        canvas.text(x - 29, y + h / 2, ylab, 6.6, rotate=90, anchor="middle")
    if xlab:
        canvas.text(x + w / 2, y - 24, xlab, 6.6, anchor="middle")


def map_xy(x, y, box, xr, yr):
    bx, by, bw, bh = box
    sx = bx + (x - xr[0]) / (xr[1] - xr[0]) * bw
    sy = by + (y - yr[0]) / (yr[1] - yr[0]) * bh
    return sx, sy


def draw_recovery(canvas):
    x, y, w, h = panel_origin(0)
    axes(canvas, x, y, w, h, "Restoration curves", "a", "Recovered load", "Restoration time (min)")
    box = (x + 30, y + 25, w - 45, h - 55)
    for t in range(0, 61, 15):
        px, _ = map_xy(t, 0, box, (0, 60), (0.35, 1.0))
        canvas.line(px, box[1], px, box[1] + box[3], COL["grid"], 0.25)
        canvas.text(px, box[1] - 12, str(t), 5.8, anchor="middle")
    for val in (0.4, 0.6, 0.8, 1.0):
        _, py = map_xy(0, val, box, (0, 60), (0.35, 1.0))
        canvas.text(box[0] - 7, py - 2, f"{val:.1f}", 5.8, anchor="end")
    t = list(range(0, 65, 5))
    series = [
        ("KG-FedMARL", [0.42, 0.58, 0.72, 0.82, 0.89, 0.93, 0.96, 0.97, 0.978, 0.982, 0.984, 0.985, 0.986], COL["kg"]),
        ("MISOCP", [0.38, 0.52, 0.68, 0.80, 0.87, 0.91, 0.94, 0.955, 0.962, 0.965, 0.967, 0.968, 0.969], COL["milp"]),
        ("FLISR", [0.36, 0.50, 0.62, 0.70, 0.76, 0.81, 0.84, 0.86, 0.875, 0.885, 0.89, 0.895, 0.90], COL["flisr"]),
        ("MAPPO", [0.40, 0.54, 0.66, 0.74, 0.82, 0.86, 0.89, 0.91, 0.925, 0.934, 0.94, 0.943, 0.945], COL["map"]),
        ("Graph-RL", [0.41, 0.56, 0.69, 0.78, 0.84, 0.89, 0.92, 0.935, 0.945, 0.952, 0.956, 0.958, 0.960], COL["graph"]),
    ]
    for name, ys, col in series:
        pts = [map_xy(tx, yy, box, (0, 60), (0.35, 1.0)) for tx, yy in zip(t, ys)]
        canvas.polyline(pts, col, 1.5 if name == "KG-FedMARL" else 1.0)
    lx, ly = x + 115, y + 50
    for i, (name, _, col) in enumerate(series):
        canvas.line(lx, ly - i * 10, lx + 14, ly - i * 10, col, 1.4)
        canvas.text(lx + 18, ly - i * 10 - 2, name, 5.7)


def draw_scaling(canvas):
    x, y, w, h = panel_origin(1)
    axes(canvas, x, y, w, h, "Network scalability", "b", "Final recovered load", "Test feeder")
    box = (x + 32, y + 25, w - 50, h - 55)
    feeders = ["33", "69", "123", "8500"]
    data = {
        "KG-FedMARL": [0.982, 0.971, 0.954, 0.921],
        "MISOCP": [0.965, 0.956, 0.940, 0.908],
        "Graph-RL": [0.948, 0.940, 0.923, 0.879],
        "FLISR": [0.902, 0.887, 0.861, 0.805],
    }
    cols = [COL["kg"], COL["milp"], COL["graph"], COL["flisr"]]
    ymax, ymin = 1.0, 0.75
    for val in (0.8, 0.9, 1.0):
        _, py = map_xy(0, val, box, (0, 1), (ymin, ymax))
        canvas.text(box[0] - 7, py - 2, f"{val:.1f}", 5.8, anchor="end")
    group_w = box[2] / len(feeders)
    bar_w = group_w / 6
    names = list(data.keys())
    for gi, f in enumerate(feeders):
        cx = box[0] + gi * group_w + group_w * 0.18
        for mi, name in enumerate(names):
            val = data[name][gi]
            bx = cx + mi * bar_w
            _, by = map_xy(0, val, box, (0, 1), (ymin, ymax))
            canvas.rect(bx, box[1], bar_w * 0.86, by - box[1], cols[mi])
        canvas.text(box[0] + gi * group_w + group_w / 2, box[1] - 13, f, 6, anchor="middle")
    legx, legy = x + 105, y + h - 20
    canvas.rect(legx - 6, legy - 35, 78, 42, (1, 1, 1), stroke=(0.82, 0.84, 0.86), lw=0.35)
    for i, name in enumerate(names):
        canvas.rect(legx, legy - i * 10, 7, 5, cols[i])
        canvas.text(legx + 11, legy - 1 - i * 10, name, 5.5)


def draw_attacks(canvas):
    x, y, w, h = panel_origin(2)
    axes(canvas, x, y, w, h, "Fault and attack stress tests", "c", "Recovered load", "Scenario")
    box = (x + 32, y + 25, w - 47, h - 55)
    scenarios = ["Line", "DER", "Comm", "FDI", "DoS", "Prot."]
    kg = [0.96, 0.94, 0.92, 0.90, 0.88, 0.89]
    graph = [0.92, 0.88, 0.86, 0.82, 0.80, 0.81]
    mappo = [0.90, 0.85, 0.83, 0.78, 0.76, 0.78]
    group_w = box[2] / len(scenarios)
    for val in (0.75, 0.85, 0.95):
        _, py = map_xy(0, val, box, (0, 1), (0.70, 1.0))
        canvas.text(box[0] - 7, py - 2, f"{val:.2f}", 5.5, anchor="end")
    for i, s in enumerate(scenarios):
        vals = [kg[i], graph[i], mappo[i]]
        cols = [COL["kg"], COL["graph"], COL["map"]]
        for j, v in enumerate(vals):
            bx = box[0] + i * group_w + 4 + j * 7
            _, by = map_xy(0, v, box, (0, 1), (0.70, 1.0))
            canvas.rect(bx, box[1], 5.5, by - box[1], cols[j])
        canvas.text(box[0] + i * group_w + group_w / 2, box[1] - 12, s, 5.4, anchor="middle")
    labels = [("KG-FedMARL", COL["kg"]), ("Graph-RL", COL["graph"]), ("MAPPO", COL["map"])]
    legx, legy = x + 113, y + h - 26
    canvas.rect(legx - 6, legy - 26, 70, 33, (1, 1, 1), stroke=(0.82, 0.84, 0.86), lw=0.35)
    for i, (name, col) in enumerate(labels):
        canvas.rect(legx, legy - i * 10, 7, 5, col)
        canvas.text(legx + 11, legy - 1 - i * 10, name, 5.5)


def draw_ablation(canvas):
    x, y, w, h = panel_origin(3)
    axes(canvas, x, y, w, h, "Component ablation", "d", "Restoration AUC", "Variant")
    box = (x + 34, y + 32, w - 48, h - 62)
    variants = ["Full", "no KG", "static", "no GAT", "no filter", "sync", "single", "MARL"]
    vals = [0.945, 0.870, 0.895, 0.906, 0.918, 0.921, 0.824, 0.863]
    for val in (0.80, 0.90, 1.00):
        _, py = map_xy(0, val, box, (0, 1), (0.78, 1.0))
        canvas.text(box[0] - 7, py - 2, f"{val:.2f}", 5.6, anchor="end")
    bar_w = box[2] / len(vals) * 0.62
    for i, v in enumerate(vals):
        bx = box[0] + i * box[2] / len(vals) + 3
        _, by = map_xy(0, v, box, (0, 1), (0.78, 1.0))
        col = COL["kg"] if i == 0 else (0.62, 0.66, 0.70)
        canvas.rect(bx, box[1], bar_w, by - box[1], col)
        canvas.text(bx + bar_w / 2, box[1] - 12, variants[i], 5.1, rotate=28, anchor="middle")


def draw_safety(canvas):
    x, y, w, h = panel_origin(4)
    axes(canvas, x, y, w, h, "Safety and action efficiency", "e", "Lower is better", "Method")
    box = (x + 35, y + 33, w - 50, h - 63)
    methods = ["FLISR", "DQN", "PPO", "MAPPO", "Graph", "Mask", "KG-DQN", "KG-F"]
    violations = [6.1, 9.2, 7.4, 5.8, 4.9, 3.8, 4.2, 1.1]
    steps = [14, 18, 17, 15, 14, 13, 13, 9]
    scale_v, scale_s = 10, 20
    bar_w = box[2] / len(methods) * 0.34
    for val in (0, 5, 10):
        _, py = map_xy(0, val, box, (0, 1), (0, scale_v))
        canvas.text(box[0] - 7, py - 2, str(val), 5.6, anchor="end")
    for i, m in enumerate(methods):
        gx = box[0] + i * box[2] / len(methods) + 3
        _, vy = map_xy(0, violations[i], box, (0, 1), (0, scale_v))
        _, sy = map_xy(0, steps[i] * scale_v / scale_s, box, (0, 1), (0, scale_v))
        canvas.rect(gx, box[1], bar_w, vy - box[1], (0.78, 0.30, 0.25))
        canvas.rect(gx + bar_w + 1.5, box[1], bar_w, sy - box[1], (0.30, 0.48, 0.70))
        canvas.text(gx + bar_w, box[1] - 12, m, 5.0, rotate=32, anchor="middle")
    legx, legy = x + 112, y + h - 25
    canvas.rect(legx - 6, legy - 16, 75, 24, (1, 1, 1), stroke=(0.82, 0.84, 0.86), lw=0.35)
    canvas.rect(legx, legy, 7, 5, (0.78, 0.30, 0.25))
    canvas.text(legx + 11, legy - 1, "violations", 5.5)
    canvas.rect(legx, legy - 10, 7, 5, (0.30, 0.48, 0.70))
    canvas.text(legx + 11, legy - 11, "action steps", 5.5)


def draw_convergence(canvas):
    x, y, w, h = panel_origin(5)
    axes(canvas, x, y, w, h, "Convergence and communication", "f", "Episodes to 90%", "Comm. MB/round")
    box = (x + 35, y + 29, w - 49, h - 59)
    pts = [
        ("DQN", 0.0, 730, COL["flisr"]),
        ("PPO", 0.0, 650, (0.64, 0.44, 0.34)),
        ("MAPPO", 11.5, 430, COL["map"]),
        ("HAPPO", 12.0, 395, (0.48, 0.44, 0.70)),
        ("Graph-RL", 9.6, 340, COL["graph"]),
        ("Mask", 8.8, 315, (0.50, 0.56, 0.62)),
        ("KG-DQN", 7.4, 355, COL["kgdqn"]),
        ("KG-FedMARL", 5.1, 230, COL["kg"]),
    ]
    for xx in (0, 5, 10, 15):
        px, _ = map_xy(xx, 200, box, (0, 15), (200, 800))
        canvas.text(px, box[1] - 12, str(xx), 5.8, anchor="middle")
    for yy in (200, 400, 600, 800):
        _, py = map_xy(0, yy, box, (0, 15), (200, 800))
        canvas.text(box[0] - 7, py - 2, str(yy), 5.8, anchor="end")
    for name, cx, cy, col in pts:
        px, py = map_xy(cx, cy, box, (0, 15), (200, 800))
        canvas.circle(px, py, 3.0 if name == "KG-FedMARL" else 2.4, col)
        dx = 4 if name != "KG-FedMARL" else -5
        anchor = "start" if name != "KG-FedMARL" else "end"
        canvas.text(px + dx, py + 4, name, 5.4, anchor=anchor)


def draw(canvas):
    canvas.text(38, H - 22, "Representative IEEE-style evaluation panels for KG-FedMARL", 10, bold=True)
    canvas.text(W - 36, H - 22, "Template data: replace with measured co-simulation logs", 6.4, rgb=(0.45, 0.45, 0.45), anchor="end")
    draw_recovery(canvas)
    draw_scaling(canvas)
    draw_attacks(canvas)
    draw_ablation(canvas)
    draw_safety(canvas)
    draw_convergence(canvas)


def convert_outputs(eps_path):
    pdf_path = eps_path.with_suffix(".pdf")
    png_prefix = eps_path.with_suffix("")
    epstopdf = shutil.which("epstopdf")
    if epstopdf:
        subprocess.run([epstopdf, str(eps_path), f"--outfile={pdf_path}"], check=False)
    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm and pdf_path.exists():
        subprocess.run([pdftoppm, "-png", "-r", str(RASTER_DPI), str(pdf_path), str(png_prefix)], check=False)
    return pdf_path


if __name__ == "__main__":
    eps_path = OUT_DIR / "kgfedmarl_experiment_results.eps"
    eps = EPS(eps_path)
    draw(eps)
    eps.save()
    svg = SVG(OUT_DIR / "kgfedmarl_experiment_results.svg")
    draw(svg)
    svg.save()
    pdf_path = convert_outputs(eps_path)
    print("wrote figures/kgfedmarl_experiment_results.eps")
    print("wrote figures/kgfedmarl_experiment_results.svg")
    if pdf_path.exists():
        print("wrote figures/kgfedmarl_experiment_results.pdf")
