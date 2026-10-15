"""Read-only PDF numeric audit and local contact-sheet rendering for R2.

Uses an existing PDF-inspection interpreter (pypdf/PyMuPDF/Pillow), not the
simulation environment. No local PDF is uploaded or copied into Git.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from experiments_ext.reproduce import ROOT, save, sha


def numbers(text):
    # TeX row-span counts are layout metadata, not observations.
    text = re.sub(r"\\multirow\{[^}]+\}\{[^}]+\}", "", text)
    text = text.replace("−", "-").replace("–", "-")
    return [float(n) for n in re.findall(r"[-+]?\d+(?:\.\d+)?", text)]


def contains(sequence, candidate):
    n = len(candidate)
    return any(sequence[i:i+n] == candidate for i in range(len(sequence)-n+1))


def audit(run, paper, name):
    import pypdf
    reader = pypdf.PdfReader(paper)
    specs = {"IV": (8, "table_validation.tex", 1), "V": (8, "table_default.tex", 1),
             "VI": (8, "table_values.tex", 2), "VII": (9, "table_noise.tex", 1),
             "VIII": (10, "table_ablation.tex", 2), "IX": (10, "table_overhead.tex", 1),
             "X": (10, "table_cost.tex", 1), "XI": (12, "table_shared.tex", 1),
             "XII": (12, "table_llm_extended.tex", 2), "XIII": (12, "table_frozen.tex", 1)}
    result = {}
    for table, (page, filename, skip) in specs.items():
        texts = [reader.pages[page-1].extract_text(), reader.pages[page-1].extract_text(extraction_mode="layout")]
        sequences = [numbers(text) for text in texts]
        rows = []
        for line in (run / "upstream_workspace/figures" / filename).read_text(encoding="utf-8").splitlines():
            if "&" not in line or "multicolumn" in line:
                continue
            cells = line.split("&")
            numeric = numbers(" ".join(cells[skip:]))
            if not numeric:
                continue
            matched = any(contains(s, numeric) for s in sequences)
            rows.append(dict(label=" | ".join(cells[:skip]).strip(), values=numeric, matched=matched, generated_row=line))
        result[table] = dict(pdf_page=page, generated_file=filename, rows=rows,
                             matched=sum(r["matched"] for r in rows), checked=len(rows))
    all_matched = all(t["matched"] == t["checked"] and t["checked"] for t in result.values())
    output = dict(status="passed" if all_matched else "needs_review", paper_sha256=sha(paper),
                  python_version=sys.version, pypdf_version=pypdf.__version__, tables=result,
                  method="Numeric row sequences checked against both plain and layout extraction of the cited PDF page. Scenario labels and figure shapes are reviewed separately.",
                  scope="Tables IV-XIII generated data rows; conceptual Figure 1/Tables I-III not generated; no LLM re-evaluation.")
    save(run / name, output)
    print(json.dumps({k: {"matched": t["matched"], "checked": t["checked"]} for k,t in result.items()}, indent=2))
    print("R2 numeric audit", output["status"])


def render(run, paper):
    import fitz
    from PIL import Image, ImageDraw
    output = run / "visual_review"
    output.mkdir(exist_ok=False)
    figures = sorted((run / "upstream_workspace/figures").glob("*.pdf"))
    cells = []
    for p in figures:
        with fitz.open(p) as doc:
            pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            pix.save(output / (p.stem + ".png"))
            im = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        im.thumbnail((590, 290))
        cell = Image.new("RGB", (610, 325), "white")
        cell.paste(im, ((610-im.width)//2, 25+(290-im.height)//2))
        ImageDraw.Draw(cell).text((8, 5), p.name, fill="black")
        cells.append(cell)
    sheet = Image.new("RGB", (1830, 325*((len(cells)+2)//3)), "#dddddd")
    for i, cell in enumerate(cells): sheet.paste(cell, ((i%3)*610,(i//3)*325))
    sheet.save(output / "all_figures.png")
    with fitz.open(paper) as doc:
        for page in (7, 8, 9, 10, 11, 12):
            doc[page-1].get_pixmap(matrix=fitz.Matrix(1.4, 1.4), alpha=False).save(output / f"paper_page_{page}.png")
    print("Rendered",len(figures),"figures and six paper pages locally.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=["audit", "render"])
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--paper", required=True, type=Path)
    ap.add_argument("--audit-name", default="r2_numeric_audit.json")
    args = ap.parse_args()
    if Path(args.run_id).name != args.run_id: ap.error("Invalid run-id")
    run = ROOT / ".local/reproduction" / args.run_id
    if Path(args.audit_name).name != args.audit_name: ap.error("Invalid audit filename")
    if args.action == "audit": audit(run, args.paper, args.audit_name)
    else: render(run, args.paper)


if __name__ == "__main__": main()
