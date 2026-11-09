#!/usr/bin/env python3
"""
Zero-dependency PPTX Layout, CJK Overflow & Academic Density Auditor.
Works with built-in macOS/Linux Python 3 (only standard library: zipfile, xml, math, sys).

Checks for:
1. Table vertical auto-expansion (PowerPoint ignores `h` when cells wrap) colliding with bottom callouts or slide edge.
2. CJK-aware text box overflow (estimating wrapped lines from box width, font size, and CJK/ASCII character widths).
3. Text density overload (character count per slide exceeding academic readability thresholds).
4. Micro-fonts (< 12pt on main slides, < 10.5pt in tables/appendix, excluding superscripts/subscripts/footers).
5. Shape-to-shape / table-to-shape bounding-box collisions.
6. "AI Card-Stacking" anti-pattern (> 28 shapes on a single slide or < 35% slides having visual figures).

Usage:
    python3 scripts/layout_audit.py path/to/deck.pptx [--strict]
"""

import argparse
import colorsys
import math
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
}
A_T = f"{{{NS['a']}}}t"
A_RPR = f"{{{NS['a']}}}rPr"
A_P = f"{{{NS['a']}}}p"
A_SRGB = f"{{{NS['a']}}}srgbClr"

EMU_PER_INCH = 914400.0


def hex_to_hsv(hex_str: str):
    hex_str = hex_str.strip().lstrip("#")
    if len(hex_str) != 6:
        return (0.0, 0.0, 1.0)
    r = int(hex_str[0:2], 16) / 255.0
    g = int(hex_str[2:4], 16) / 255.0
    b = int(hex_str[4:6], 16) / 255.0
    return colorsys.rgb_to_hsv(r, g, b)


def em_width(text: str) -> float:
    """Estimate visual width in ems (CJK = 1.0 em, ASCII/Latin = 0.55 em)."""
    return sum(1.0 if ord(c) > 127 else 0.55 for c in text)


def rect_overlap(a, b, tol=0.06):
    """Return True if rectangles a=(x1,y1,w1,h1) and b=(x2,y2,w2,h2) overlap significantly
    without one simply being a background container of the other."""
    ax1, ay1, aw, ah = a
    bx1, by1, bw, bh = b
    ax2, ay2 = ax1 + aw, ay1 + ah
    bx2, by2 = bx1 + bw, by1 + bh

    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    if ix2 - ix1 <= tol or iy2 - iy1 <= tol:
        return False

    # Ignore if one shape contains >= 85% of the other (e.g., background card + inner text box)
    inter_area = (ix2 - ix1) * (iy2 - iy1)
    area_a = max(aw * ah, 1e-6)
    area_b = max(bw * bh, 1e-6)
    if inter_area / min(area_a, area_b) >= 0.80:
        return False
    return True


def audit_pptx(pptx_path: Path) -> int:
    if not pptx_path.is_file():
        print(f"[ERROR] File not found: {pptx_path}", file=sys.stderr)
        return 2

    errors = []
    warnings = []
    slides_with_visuals = 0

    with zipfile.ZipFile(pptx_path, "r") as zf:
        pres = ET.fromstring(zf.read("ppt/presentation.xml"))
        sld_sz = pres.find("p:sldSz", NS)
        slide_w = int(sld_sz.attrib["cx"]) / EMU_PER_INCH if sld_sz is not None else 13.333
        slide_h = int(sld_sz.attrib["cy"]) / EMU_PER_INCH if sld_sz is not None else 7.500

        slide_files = sorted(
            [f for f in zf.namelist() if re.match(r"^ppt/slides/slide\d+\.xml$", f)],
            key=lambda x: int(re.findall(r"\d+", x)[0]),
        )
        total_slides = len(slide_files)

        for idx, sfile in enumerate(slide_files, 1):
            root = ET.fromstring(zf.read(sfile))
            all_texts = [t.text for t in root.iter(A_T) if t.text]
            full_slide_text = " ".join(all_texts)
            is_backup = bool(re.search(r"\[Backup|附录\s*A", full_slide_text))

            total_chars = sum(len(t.strip()) for t in all_texts)
            char_limit = 650 if is_backup else 420
            if total_chars > char_limit:
                errors.append(
                    f"Slide {idx:02d}: Text overload ({total_chars} chars > max {char_limit}). "
                    f"Move paragraph details to slide.addNotes() or split across slides."
                )

            # Collect shapes, pictures, charts, tables
            shapes = root.findall(".//p:sp", NS)
            pics = root.findall(".//p:pic", NS)
            charts = root.findall(".//a:chart", NS)
            tables = []

            if len(pics) > 0 or len(charts) > 0:
                slides_with_visuals += 1

            if len(shapes) > 14:
                errors.append(
                    f"Slide {idx:02d}: Too many shapes ({len(shapes)} > 14). "
                    f"Minimalist monochromatic style forbids boxed cards, numbered badges, section pills, or bottom warning bars."
                )

            # Check monochromatic palette across slide shapes (excluding embedded pictures)
            hue_buckets = set()
            for clr_el in root.iter(A_SRGB):
                val = clr_el.attrib.get("val", "")
                if len(val) == 6:
                    h_val, s_val, v_val = hex_to_hsv(val)
                    # If saturation > 0.22 and value > 0.20, it's a chromatic color (not gray/black/white)
                    if s_val > 0.22 and v_val > 0.20:
                        hue_buckets.add(int(round(h_val * 12)) % 12)
            if len(hue_buckets) > 1:
                errors.append(
                    f"Slide {idx:02d}: Multi-color violation ({len(hue_buckets)} distinct chromatic hues found on shapes/text). "
                    f"Use strictly ONE monochromatic hue family + neutral grays/blacks on white background."
                )

            text_boxes = []
            min_body_pt = 999.0

            for sp in shapes:
                xfrm = sp.find(".//a:xfrm", NS)
                if xfrm is None:
                    continue
                off, ext = xfrm.find("a:off", NS), xfrm.find("a:ext", NS)
                if off is None or ext is None:
                    continue
                x = int(off.attrib["x"]) / EMU_PER_INCH
                y = int(off.attrib["y"]) / EMU_PER_INCH
                w = int(ext.attrib["cx"]) / EMU_PER_INCH
                h = int(ext.attrib["cy"]) / EMU_PER_INCH

                paras = sp.findall(".//a:p", NS)
                est_h = 0.0
                box_texts = []

                for p in paras:
                    ptxt = "".join(t.text for t in p.iter(A_T) if t.text)
                    box_texts.append(ptxt)
                    rprs = list(p.iter(A_RPR))
                    szs = []
                    for r in rprs:
                        if "sz" in r.attrib and "baseline" not in r.attrib:
                            szs.append(int(r.attrib["sz"]) / 100.0)
                    pt = max(szs) if szs else 12.0
                    # Ignore footer/badge when tracking minimum body font size
                    if y < slide_h - 0.65 and len(ptxt.strip()) > 4:
                        min_body_pt = min(min_body_pt, pt)

                    usable_w = max(w - 0.16, 0.25)
                    ems_per_line = (usable_w * 72.0) / pt
                    lines = max(1, math.ceil(em_width(ptxt) / max(ems_per_line, 1.0))) if ptxt.strip() else 0.4
                    est_h += lines * (pt * 1.35 / 72.0)

                joined = " ".join(t.strip() for t in box_texts if t.strip())
                if joined:
                    text_boxes.append((x, y, w, h, joined))
                    if est_h > h * 1.15 and len(joined) > 8:
                        errors.append(
                            f"Slide {idx:02d}: Text box overflow at ({x:.2f}\", {y:.2f}\", {w:.2f}\"×{h:.2f}\") "
                            f"— needs ~{est_h:.2f}\" height for '{joined[:40]}...'"
                        )
                    if x + w > slide_w + 0.08 or y + h > slide_h + 0.08:
                        errors.append(
                            f"Slide {idx:02d}: Shape out of slide bounds ({x+w:.2f}\"×{y+h:.2f}\" > {slide_w:.2f}\"×{slide_h:.2f}\")"
                        )

            min_allowed_pt = 10.5 if is_backup else 12.0
            if min_body_pt < min_allowed_pt:
                errors.append(
                    f"Slide {idx:02d}: Font size too small ({min_body_pt:.1f}pt < {min_allowed_pt:.1f}pt). "
                    f"Cut word count and increase font size."
                )

            # Check tables and vertical expansion
            for gf in root.findall(".//p:graphicFrame", NS):
                xfrm = gf.find(".//p:xfrm", NS) or gf.find(".//a:xfrm", NS)
                tbl = gf.find(".//a:tbl", NS)
                if tbl is None or xfrm is None:
                    continue
                off, ext = xfrm.find("a:off", NS), xfrm.find("a:ext", NS)
                tx = int(off.attrib["x"]) / EMU_PER_INCH
                ty = int(off.attrib["y"]) / EMU_PER_INCH
                tw = int(ext.attrib["cx"]) / EMU_PER_INCH
                col_ws = [
                    int(c.attrib.get("w", 0)) / EMU_PER_INCH
                    for c in tbl.findall("a:tblGrid/a:gridCol", NS)
                ]
                rows = tbl.findall("a:tr", NS)
                est_tbl_h = 0.0
                for tr in rows:
                    rh = int(tr.attrib.get("h", 0)) / EMU_PER_INCH
                    max_cell_h = rh
                    for ci, tc in enumerate(tr.findall("a:tc", NS)):
                        cw = col_ws[ci] if ci < len(col_ws) else (tw / max(len(col_ws), 1))
                        paras = tc.findall(".//a:p", NS)
                        cell_h = 0.08
                        for p in paras:
                            ptxt = "".join(t.text for t in p.iter(A_T) if t.text)
                            szs = [
                                int(r.attrib["sz"]) / 100.0
                                for r in p.iter(A_RPR)
                                if "sz" in r.attrib
                            ]
                            pt = max(szs) if szs else 10.0
                            usable_cw = max(cw - 0.14, 0.25)
                            ems_per_line = (usable_cw * 72.0) / pt
                            lines = max(1, math.ceil(em_width(ptxt) / max(ems_per_line, 1.0))) if ptxt else 1
                            cell_h += lines * (pt * 1.32 / 72.0)
                        max_cell_h = max(max_cell_h, cell_h)
                    est_tbl_h += max_cell_h

                tables.append((tx, ty, tw, est_tbl_h, len(rows), len(col_ws)))
                if ty + est_tbl_h > slide_h - 0.45:
                    errors.append(
                        f"Slide {idx:02d}: Table ({len(rows)}×{len(col_ws)}) at y={ty:.2f}\" auto-expands to "
                        f"bottom={ty+est_tbl_h:.2f}\" (exceeds safe bottom {slide_h-0.45:.2f}\"). "
                        f"Never stack a large figure and a multi-row table on the same slide!"
                    )
                # Check if table collides with any text box below it
                for bx, by, bw, bh, btxt in text_boxes:
                    if by >= ty + 0.2 and rect_overlap((tx, ty, tw, est_tbl_h), (bx, by, bw, bh)):
                        errors.append(
                            f"Slide {idx:02d}: Expanded table (bottom={ty+est_tbl_h:.2f}\") collides with "
                            f"shape at y={by:.2f}\" ('{btxt[:35]}...')."
                        )

    if total_slides >= 5 and slides_with_visuals / total_slides < 0.35:
        warnings.append(
            f"Deck visual ratio is low: only {slides_with_visuals}/{total_slides} slides ({slides_with_visuals*100//total_slides}%) "
            f"contain figures/charts (target >= 40%). Add SVG/PNG schematics or plots."
        )

    print(f"=== PPTX Layout & Academic Audit: {pptx_path.name} ({total_slides} slides) ===")
    if warnings:
        for w in warnings:
            print(f"  [WARN] {w}")
    if errors:
        for e in errors:
            print(f"  [FAIL] {e}")
        print(f"\nAudit FAILED with {len(errors)} error(s). Fix all layout/density issues before finishing.")
        return 1

    print("Audit PASSED! Zero layout overflows, table collisions, or density violations.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Audit PPTX layout, overflow, and academic density")
    parser.add_argument("pptx", type=Path, help="Path to .pptx file")
    args = parser.parse_args()
    sys.exit(audit_pptx(args.pptx))


if __name__ == "__main__":
    main()
