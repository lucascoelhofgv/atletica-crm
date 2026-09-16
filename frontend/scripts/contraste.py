"""Checa contraste WCAG (AA) dos tokens de globals.css nos dois temas."""
import math
import re
import sys

CSS = open(sys.argv[1], encoding="utf-8").read()


def bloco(seletor):
    m = re.search(re.escape(seletor) + r"\s*\{(.*?)\}", CSS, re.S)
    toks = {}
    for k, v in re.findall(r"--([\w-]+):\s*([^;]+);", m.group(1)):
        toks[k] = v.strip()
    return toks


def oklch_para_srgb(s):
    m = re.match(r"oklch\(([\d.]+)\s+([\d.]+)\s+([\d.]+)(?:\s*/\s*([\d.]+)%)?\)", s)
    if not m:
        return None
    L, C, h = float(m.group(1)), float(m.group(2)), float(m.group(3))
    alpha = float(m.group(4)) / 100 if m.group(4) else 1.0
    a = C * math.cos(math.radians(h))
    b = C * math.sin(math.radians(h))
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l3, m3, s3 = l_ ** 3, m_ ** 3, s_ ** 3
    r = 4.0767416621 * l3 - 3.3077115913 * m3 + 0.2309699292 * s3
    g = -1.2684380046 * l3 + 2.6097574011 * m3 - 0.3413193965 * s3
    bb = -0.0041960863 * l3 - 0.7034186147 * m3 + 1.7076147010 * s3
    def gama(c):  # linear -> sRGB codificado (lum() decodifica de novo)
        c = max(0, min(1, c))
        return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return (gama(r), gama(g), gama(bb), alpha)


def hex_para_srgb(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (1.0,)


def cor(s):
    return oklch_para_srgb(s) if s.startswith("oklch") else hex_para_srgb(s)


def compor(fg, bg):
    a = fg[3]
    return tuple(fg[i] * a + bg[i] * (1 - a) for i in range(3))


def lum(rgb):
    def ch(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(fg, bg):
    l1, l2 = lum(fg), lum(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


PARES = [  # (texto, fundo, mínimo)
    ("foreground", "background", 4.5),
    ("muted-foreground", "background", 4.5),
    ("muted-foreground", "card", 4.5),
    ("card-foreground", "card", 4.5),
    ("primary-foreground", "primary", 4.5),
    ("secondary-foreground", "secondary", 4.5),
    ("accent-foreground", "accent", 4.5),
    ("sidebar-foreground", "sidebar", 4.5),
    ("sidebar-accent-foreground", "sidebar-accent", 4.5),
    ("sidebar-primary-foreground", "sidebar-primary", 4.5),
    ("sidebar-primary", "sidebar", 3.0),
    ("primary", "background", 3.0),
    ("destructive", "background", 4.5),
    ("success", "background", 3.0),
    ("warning", "background", 3.0),
    ("chart-1", "background", 3.0),
    ("chart-2", "background", 3.0),
    ("chart-3", "background", 3.0),
    ("chart-4", "background", 3.0),
    ("chart-5", "background", 3.0),
    ("border", "background", 1.5),
]

for tema, sel in (("claro", ":root"), ("escuro", ".dark")):
    t = bloco(sel)
    print(f"\n== tema {tema}")
    for fg, bg, minimo in PARES:
        if fg not in t or bg not in t:
            continue
        c_bg = compor(cor(t[bg]), (1, 1, 1)) if tema == "claro" else compor(cor(t[bg]), cor(t.get("background", t[bg]))[:3])
        c_fg = compor(cor(t[fg]), c_bg)
        r = contraste(c_fg, c_bg)
        flag = "ok " if r >= minimo else "BAIXO"
        print(f"  {flag} {r:5.2f} (min {minimo})  {fg} / {bg}")
