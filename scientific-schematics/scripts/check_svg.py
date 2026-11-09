#!/usr/bin/env python3
"""Check a hand-written SVG schematic for the usual layout failures, then render it to PNG.

Standard library only for the checks. PNG rendering uses the first of rsvg-convert,
inkscape or cairosvg that is installed; if none is, the checks still run.

Checks (all geometric estimates, so treat a pass as "no obvious fault", not proof):
  1. Root has a viewBox.
  2. Every <text> lies inside the viewBox.
  3. No two <text> labels overlap.
  4. A label that sits inside a <rect> fits inside that rect (the common "text overflows its box").
  5. Font size >= --min-font (in viewBox units, default 11) and only approved font families.
  6. Chromatic hues used <= 2 (one primary + one accent) on a white page.

Only translate(...) transforms are followed; text under rotate/scale/matrix is skipped with a warning.

Usage:
    python3 scripts/check_svg.py figure.svg [--png figure.png] [--min-font 11]
Exit code 0 = no failures, 1 = failures, 2 = bad input.
"""

import argparse
import colorsys
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SVG = "{http://www.w3.org/2000/svg}"
LATIN_OK = {"arial", "calibri", "helvetica", "helvetica neue", "times new roman", "cambria", "consolas", "courier new"}
CJK_OK = {"microsoft yahei", "微软雅黑", "pingfang sc", "苹方-简", "simsun", "宋体", "simhei", "黑体", "songti sc"}
GENERIC = {"sans-serif", "serif", "monospace"}
MAX_HUES = 2
LATIN_EM = 0.58


def em_width(text):
    return sum(1.0 if ord(c) > 0x2E7F else (LATIN_EM if ord(c) > 32 else 0.3) for c in text)


def num(v, default=0.0):
    if v is None:
        return default
    m = re.match(r"\s*(-?\d+(?:\.\d+)?)", v)
    return float(m.group(1)) if m else default


def translate_of(el):
    t = el.attrib.get("transform", "")
    if not t:
        return 0.0, 0.0, True
    parts = re.findall(r"(\w+)\s*\(([^)]*)\)", t)
    dx = dy = 0.0
    ok = True
    for name, args in parts:
        vals = [float(x) for x in re.split(r"[ ,]+", args.strip()) if x]
        if name == "translate":
            dx += vals[0]
            dy += vals[1] if len(vals) > 1 else 0.0
        else:
            ok = False
    return dx, dy, ok


def walk(el, dx=0.0, dy=0.0, ok=True):
    """Yield (element, abs_dx, abs_dy, transform_ok) for every element."""
    tdx, tdy, tok = translate_of(el)
    dx, dy, ok = dx + tdx, dy + tdy, ok and tok
    yield el, dx, dy, ok
    for ch in el:
        yield from walk(ch, dx, dy, ok)


def font_size(el, parents_style):
    s = el.attrib.get("font-size")
    if s is None:
        m = re.search(r"font-size\s*:\s*([\d.]+)", el.attrib.get("style", ""))
        s = m.group(1) if m else None
    return num(s, parents_style)


def font_family(el):
    f = el.attrib.get("font-family")
    if f is None:
        m = re.search(r"font-family\s*:\s*([^;]+)", el.attrib.get("style", ""))
        f = m.group(1) if m else ""
    return [x.strip().strip("'\"") for x in f.split(",") if x.strip()]


def fill_hex(el):
    for attr in ("fill", "stroke"):
        v = el.attrib.get(attr, "")
        if re.fullmatch(r"#[0-9a-fA-F]{6}", v):
            yield v[1:]
        elif re.fullmatch(r"#[0-9a-fA-F]{3}", v):
            yield "".join(c * 2 for c in v[1:])


def hue_bucket(hexv):
    r, g, b = (int(hexv[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if s > 0.22 and v > 0.20:
        return int(round(h * 12)) % 12
    return None


def check(path, min_font):
    errors, warnings = [], []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        print(f"[ERROR] Not well-formed XML: {e}", file=sys.stderr)
        return None, None

    vb = root.attrib.get("viewBox")
    if not vb:
        errors.append("Root <svg> has no viewBox; the figure will not scale reliably.")
        vbx = vby = 0.0
        vbw, vbh = num(root.attrib.get("width"), 1000), num(root.attrib.get("height"), 600)
    else:
        vbx, vby, vbw, vbh = (float(x) for x in re.split(r"[ ,]+", vb.strip()))

    rects, texts = [], []
    hues = set()
    skipped = 0
    for el, dx, dy, tok in walk(root):
        tag = el.tag.replace(SVG, "")
        for hx in fill_hex(el):
            b = hue_bucket(hx)
            if b is not None:
                hues.add(b)
        if tag == "rect" and tok:
            w, h = num(el.attrib.get("width")), num(el.attrib.get("height"))
            if w > 0 and h > 0:
                rects.append((num(el.attrib.get("x")) + dx, num(el.attrib.get("y")) + dy, w, h))
        elif tag == "text":
            if not tok:
                skipped += 1
                continue
            txt = "".join(el.itertext()).strip()
            if not txt:
                continue
            size = font_size(el, 16.0)
            x, y = num(el.attrib.get("x")) + dx, num(el.attrib.get("y")) + dy
            w = em_width(txt) * size
            anchor = el.attrib.get("text-anchor", "start")
            left = x - (w / 2 if anchor == "middle" else w if anchor == "end" else 0)
            texts.append({"txt": txt, "x": left, "y": y - size * 0.9, "w": w, "h": size * 1.2,
                          "cx": x, "cy": y - size * 0.35, "size": size, "fam": font_family(el)})

    if skipped:
        warnings.append(f"{skipped} <text> element(s) under rotate/scale/matrix were skipped.")

    for t in texts:
        label = t["txt"][:30]
        if t["x"] < vbx - 1 or t["y"] < vby - 1 or t["x"] + t["w"] > vbx + vbw + 1 or t["y"] + t["h"] > vby + vbh + 1:
            errors.append(f"Text outside viewBox: '{label}'")
        if t["size"] < min_font:
            errors.append(f"Font too small ({t['size']:g} < {min_font:g}): '{label}'")
        for f in t["fam"]:
            fl = f.lower()
            if fl not in LATIN_OK | CJK_OK | GENERIC:
                errors.append(f"Font '{f}' is not on both Windows and macOS: '{label}'")
        containing = [r for r in rects if r[0] <= t["cx"] <= r[0] + r[2] and r[1] <= t["cy"] <= r[1] + r[3]]
        if containing:
            r = min(containing, key=lambda r: r[2] * r[3])
            if t["x"] < r[0] + 2 or t["x"] + t["w"] > r[0] + r[2] - 2:
                errors.append(f"Label wider than its box ({t['w']:.0f} vs {r[2]:.0f}): '{label}'")

    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            a, b = texts[i], texts[j]
            ix = min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"])
            iy = min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"])
            if ix > 1 and iy > 1 and ix * iy > 0.15 * min(a["w"] * a["h"], b["w"] * b["h"]):
                errors.append(f"Overlapping labels: '{a['txt'][:25]}' and '{b['txt'][:25]}'")

    if len(hues) > MAX_HUES:
        errors.append(f"Too many colors: {len(hues)} chromatic hues (max {MAX_HUES}: one primary + one accent).")
    return errors, warnings


def render(svg, png):
    exe = shutil.which("rsvg-convert")
    if exe:
        subprocess.run([exe, "-w", "2400", "-o", str(png), str(svg)], check=True)
        return "rsvg-convert"
    exe = shutil.which("inkscape")
    if exe:
        subprocess.run([exe, str(svg), "--export-type=png", f"--export-filename={png}", "--export-width=2400"], check=True)
        return "inkscape"
    try:
        import cairosvg  # type: ignore
        cairosvg.svg2png(url=str(svg), write_to=str(png), output_width=2400)
        return "cairosvg"
    except ImportError:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("svg", type=Path)
    ap.add_argument("--png", type=Path, help="also render to this PNG path")
    ap.add_argument("--min-font", type=float, default=11.0)
    args = ap.parse_args()
    if not args.svg.is_file():
        print(f"[ERROR] File not found: {args.svg}", file=sys.stderr)
        sys.exit(2)

    errors, warnings = check(args.svg, args.min_font)
    if errors is None:
        sys.exit(2)
    print(f"=== SVG check: {args.svg.name} ===")
    for w in warnings:
        print(f"  [WARN] {w}")
    for e in errors:
        print(f"  [FAIL] {e}")

    if args.png:
        try:
            used = render(args.svg, args.png)
        except subprocess.CalledProcessError as e:
            used = None
            print(f"  [WARN] Renderer failed: {e}")
        if used:
            print(f"  Rendered {args.png} with {used}. Open it and look at it before delivering.")
        else:
            print("  [WARN] No renderer found (install librsvg2-bin, inkscape, or `pip install cairosvg`); could not make a PNG.")

    if errors:
        print(f"\nCheck FAILED with {len(errors)} error(s).")
        sys.exit(1)
    print("\nNo geometric faults found (estimate only; still inspect the rendered image).")


if __name__ == "__main__":
    main()
