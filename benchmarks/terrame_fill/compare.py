#!/usr/bin/env python3
"""Compare a DisSCube data cube with the cellular space TerraME's Fill produced.

    python compare.py itaituba.compare.toml --workspace data/itaituba --out reports/itaituba

Cells are matched by centre coordinates on the same grid, so the comparison does not
depend on TerraME numbering rows from the south (DisSCube grids are north-up) and also
works for references that keep only a subset of the rectangle (``input = "limit"``).

Exit status is 1 if any comparison marked ``expect = "match"`` fails its criterion: a maximum
absolute error (``max_abs_error``) and/or a share of cells within a tolerance (``tol`` and
``min_share``).

``kind = "categorical"`` compares class values instead of measurements (TerraME's ``mode``): the
reference column is text, one class or, on a tie, every tied class separated by comma; a cell agrees
when DisSCube's class is one of them. Only ``min_share`` (share of agreeing cells) applies.
"""
from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

import numpy as np
import pandas as pd

from disscube import CubeClient


def _load_reference(ds: dict) -> pd.DataFrame:
    """Golden cells from LambdaGeo/luccme-goldens, downloaded and SHA-256 verified (pooch).

    Set LUCCME_GOLDENS_DIR to a local clone of luccme-goldens to work offline; the file is
    then read from <dir>/goldens/fill/<name>_terrame.csv and checked against the same hash.
    """
    import hashlib
    import os

    import pooch

    want = ds["reference_sha256"]
    if not want or want.upper() == "TODO":
        raise SystemExit(f"{ds['name']}: reference_sha256 is not set; generate the golden and put "
                         "`sha256sum goldens/fill/<name>_terrame.csv` in the compare.toml")
    local = os.environ.get("LUCCME_GOLDENS_DIR")
    if local:
        path = Path(local) / "goldens" / "fill" / f"{ds['name']}_terrame.csv"
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        if got != want:
            raise SystemExit(f"{path}: sha256 {got} != expected {want}")
        return pd.read_csv(path)
    path = pooch.retrieve(url=ds["reference_url"], known_hash=f"sha256:{want}",
                          path=pooch.os_cache("disscube") / "goldens", fname=f"{ds['name']}_terrame.csv")
    return pd.read_csv(path)


def _cells(cube: CubeClient, grid_id: str, ref: pd.DataFrame):
    """(row, col) index of every reference cell on the DisSCube grid."""
    grid = cube.catalog.get_grid(grid_id)
    xmin, _, _, ymax = grid.bbox
    res = grid.resolution
    cols = np.floor((ref["cx"].to_numpy() - xmin) / res).astype(int)
    rows = np.floor((ymax - ref["cy"].to_numpy()) / res).astype(int)
    return rows, cols


def _metrics(ours: np.ndarray, theirs: np.ndarray, tol: float | None = None, nan_ref: float | None = None) -> dict:
    """Error metrics over the cells where both values exist.

    ``nan_ref``: DisSCube leaves a cell without any source pixel as NaN while TerraME writes a
    value (0 for coverage). Those cells are left out of the errors, and reported as ``nan_cells``;
    ``nan_ok`` says whether TerraME's value in all of them is ``nan_ref``.
    """
    nan = np.isnan(ours)
    m: dict = {"nan_cells": int(nan.sum() if nan_ref is not None else 0)}
    if nan_ref is not None:
        m["nan_ok"] = bool(np.all(theirs[nan] == nan_ref))
    ok = np.isfinite(ours) & np.isfinite(theirs)
    a, b = ours[ok], theirs[ok]
    err = a - b
    m.update(
        n=int(ok.sum()),
        mean_abs_error=float(np.abs(err).mean()),
        max_abs_error=float(np.abs(err).max()),
        bias=float(err.mean()),
        pearson_r=float(np.corrcoef(a, b)[0, 1]) if a.std() > 0 and b.std() > 0 else float("nan"),
        share=float(np.mean(np.abs(err) <= tol)) if tol is not None else None,
    )
    return m


def _classes(cell) -> set[float]:
    """Classes listed in one cell of a TerraME ``mode`` column: ``7`` -> {7}, ``"7,87"`` -> {7, 87}."""
    return {float(v) for v in str(cell).split(",") if v.strip()}


def _categorical(ours: np.ndarray, theirs, nan_ref: float | None = None) -> dict:
    """Agreement of DisSCube's class with TerraME's ``mode`` (which lists every tied class).

    A cell agrees when DisSCube's value is among the classes TerraME lists. Cells without source
    pixels (NaN in DisSCube) are left out and, with ``nan_ref``, checked against TerraME's ``missing``.
    ``exact_share`` is the agreement over the cells with a single class; ``tie_cells``/``tie_share``
    describe the cells where TerraME lists more than one.
    """
    sets = [_classes(t) for t in theirs]
    nan = np.isnan(ours)
    m: dict = {"nan_cells": int(nan.sum() if nan_ref is not None else 0)}
    if nan_ref is not None:
        m["nan_ok"] = all(sets[i] == {nan_ref} for i in np.flatnonzero(nan))
    ok = np.flatnonzero(~nan) if nan_ref is not None else np.arange(len(ours))
    agree = np.array([ours[i] in sets[i] for i in ok])
    tie = np.array([len(sets[i]) > 1 for i in ok])
    nan_ = float("nan")
    m.update(
        n=int(len(ok)), mean_abs_error=nan_, max_abs_error=nan_, bias=nan_, pearson_r=nan_,
        share=float(agree.mean()),
        exact_share=float(agree[~tie].mean()) if (~tie).any() else None,
        tie_cells=int(tie.sum()),
        tie_share=float(agree[tie].mean()) if tie.any() else None,
    )
    return m


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("spec", type=Path, help="<dataset>.compare.toml")
    p.add_argument("--workspace", type=Path, required=True, help="DisSCube workspace of the run")
    p.add_argument("--out", type=Path, default=None, help="folder for report.json / report.md")
    args = p.parse_args()

    spec = tomllib.loads(args.spec.read_text(encoding="utf-8"))
    ds = spec["dataset"]
    ref = _load_reference(ds)
    cube = CubeClient(str(args.workspace / "catalog.db"), str(args.workspace / "store"))
    rows, cols = _cells(cube, ds["grid"], ref)

    results = []
    for c in spec.get("compare", []):
        da = cube.load(c["variable"], grid_id=ds["grid"])
        if c.get("kind") == "categorical":
            ours = da.to_numpy()[rows, cols]
            m = _categorical(ours, ref[c["reference"]].to_numpy(), c.get("nan_ref"))
            m.update(label=c.get("label", c["variable"]), expect=c["expect"], limit=None, tol=None,
                     min_share=c.get("min_share"), note=c.get("note", ""), kind="categorical")
            m["passed"] = (all([m["share"] >= m["min_share"]] + ([m["nan_ok"]] if "nan_ok" in m else []))
                           if c["expect"] == "match" else None)
            results.append(m)
            continue
        if c.get("purity"):
            da = da * da.coords["coverage_purity"]
        ours = da.to_numpy()[rows, cols] * c.get("scale", 1.0)
        m = _metrics(ours, ref[c["reference"]].to_numpy(), c.get("tol"), c.get("nan_ref"))
        limit, min_share = c.get("max_abs_error"), c.get("min_share")
        m.update(label=c.get("label", c["variable"]), expect=c["expect"], limit=limit, tol=c.get("tol"),
                 min_share=min_share, note=c.get("note", ""))
        if c["expect"] == "match":
            checks = []
            if limit is not None:
                checks.append(m["max_abs_error"] <= limit)
            if min_share is not None:
                checks.append(m["share"] >= min_share)
            if "nan_ok" in m:
                checks.append(m["nan_ok"])
            m["passed"] = all(checks)
        else:
            m["passed"] = None
        results.append(m)
    unsupported = spec.get("unsupported", [])

    report = {"dataset": ds["name"], "grid": ds["grid"], "cells": int(len(ref)),
              "disscube": _version(), "comparisons": results, "unsupported": unsupported}
    _print(report)
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        (args.out / "report.md").write_text(_markdown(report), encoding="utf-8")
        print(f"\nreport: {args.out}/report.md, report.json")

    failed = [r["label"] for r in results if r["passed"] is False]
    if failed:
        print(f"\nFAILED (exceeds threshold): {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


def _version() -> str:
    from importlib.metadata import version
    return version("disscube")


def _rows(report: dict):
    for r in report["comparisons"]:
        status = {True: "match", False: "FAIL", None: "differs"}[r["passed"]]
        crit = []
        cat = r.get("kind") == "categorical"
        if r["limit"] is not None:
            crit.append(f"max <= {r['limit']:g}")
        if r["min_share"] is not None:
            crit.append(f">= {r['min_share']:.1%} agree" if cat else f">= {r['min_share']:.1%} within {r['tol']:g}")
        share = f"{r['share']:.1%}" if r["share"] is not None else "-"
        if cat:
            share += " agree"
        elif r["share"] is not None and r["tol"] is not None:
            share += f" (<= {r['tol']:g})"
        num = lambda v, f: "-" if v != v else format(v, f)  # NaN -> "-" (categorical has no error metrics)
        yield (r["label"], r["n"], num(r["mean_abs_error"], ".3g"), num(r["max_abs_error"], ".3g"),
               num(r["bias"], "+.3g"), num(r["pearson_r"], ".4f"), share, "; ".join(crit) or "-", status)


HEAD = ("variable", "cells", "mean |err|", "max |err|", "bias", "r", "within tol", "criterion", "status")


def _print(report: dict) -> None:
    print(f"{report['dataset']} — {report['cells']} cells, grid {report['grid']}, DisSCube {report['disscube']}\n")
    table = [HEAD, *_rows(report)]
    w = [max(len(str(row[i])) for row in table) for i in range(len(HEAD))]
    for i, row in enumerate(table):
        print("  ".join(str(v).ljust(w[j]) for j, v in enumerate(row)))
        if i == 0:
            print("  ".join("-" * x for x in w))
    for r in report["comparisons"]:
        if r["nan_cells"]:
            print(f"\n{r['label']}: {r['nan_cells']} cells without source pixels are NaN in DisSCube; "
                  f"TerraME's value there is the expected one: {r['nan_ok']}")
    for r in report["comparisons"]:
        if r.get("kind") == "categorical":
            ex = f"{r['exact_share']:.1%}" if r["exact_share"] is not None else "-"
            ti = f"{r['tie_share']:.1%}" if r["tie_share"] is not None else "-"
            print(f"\n{r['label']}: single-class cells agree in {ex}; "
                  f"{r['tie_cells']} tie cells (TerraME lists several classes), DisSCube's is one of them in {ti}")
    for u in report["unsupported"]:
        print(f"\nnot supported: {u['reference']} — {u['note']}")


def _markdown(report: dict) -> str:
    out = [f"# {report['dataset']}: DisSCube vs TerraME Fill\n",
           f"{report['cells']} cells, grid `{report['grid']}`, DisSCube {report['disscube']}.\n",
           "| " + " | ".join(HEAD) + " |", "|" + "---|" * len(HEAD)]
    out += ["| " + " | ".join(str(v) for v in row) + " |" for row in _rows(report)]
    out.append("")
    for r in report["comparisons"]:
        if r["note"]:
            out.append(f"- **{r['label']}**: {r['note']}")
    for u in report["unsupported"]:
        out.append(f"- **{u['reference']}** (not supported): {u['note']}")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    sys.exit(main())
