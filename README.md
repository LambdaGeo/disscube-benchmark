# disscube-benchmark

[![CI](https://github.com/LambdaGeo/disscube-benchmark/actions/workflows/ci.yml/badge.svg)](https://github.com/LambdaGeo/disscube-benchmark/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Goldens: Zenodo DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23107748.svg)](https://doi.org/10.5281/zenodo.23107748)
[![Upstream: DisSCube](https://img.shields.io/badge/Engine-DisSCube-green.svg)](https://pypi.org/project/disscube/)

**Quantitative Numerical and Spatial Parity Benchmark for DisSCube against Canonical TerraME Goldens.**

This repository forms the **Level 2 (Parity Benchmark & Quantitative Validation)** foundation of the reproducible replication framework presented in:

> Costa, S. S. (2026). *Declarative Spatial Data Cubes and Verifiable Provenance for Reproducible Land-Use Change Modelling: A Three-Level Replication of LuccME*. Big Earth Data (Taylor & Francis).

---

## 1. Scientific Motivation

When porting environmental simulation models from legacy imperative platforms (such as `TerraME 2.0.1` and `LuccME 3.1`) to declarative spatial data cubes (`DisSCube`), demonstration code alone cannot guarantee scientific fidelity. 

**`disscube-benchmark`** provides a rigorous, automated testing suite that executes modern declarative data cube derivations and measures cell-by-cell numerical parity against the immutable canonical reference goldens published in [`LambdaGeo/luccme-goldens`](https://github.com/LambdaGeo/luccme-goldens) (Zenodo DOI: [10.5281/zenodo.23107748](https://doi.org/10.5281/zenodo.23107748)). No reference data or TerraME code is stored in this repository: goldens are fetched at run time, pinned to release `v1.0.0` and verified by SHA-256.

Every benchmark execution checks:
1. **Mean Absolute Error (MAE)** and **Max Absolute Error ($\max |y - \hat{y}|$)** across all cells.
2. **Mean Bias Error (MBE)** and **Pearson Correlation ($r$)**.
3. **Share of cells within strict physical tolerances** (`min_share` at tolerance `tol`).
4. **Automated pass/fail criteria**: Continuous Integration (CI) fails if numerical parity regresses beyond defined physical limits.

---

## 2. Benchmark Suite: `terrame_fill`

Evaluates the spatial aggregation and feature extraction operations of TerraME's `gis` package (`cells:fill{}`) across three canonical study areas. DisSCube derives each variable **on the same grid** as TerraME, and the cells are compared with the cellular space TerraME produced, the `goldens/fill/<dataset>_terrame.csv` files of `luccme-goldens` (referenced by URL and SHA-256 in each `<dataset>.compare.toml`).

| Case | Domain & Dimensions | Grid Resolution & CRS | TerraME `fill` operation | DisSCube operator |
| :--- | :--- | :--- | :--- | :--- |
| **`itaituba`** | Itaituba / PA (620 cells, 31 × 20) | 5,000 m (EPSG:29191) | `average` (elevation), `coverage` (deforestation), `distance` (roads, localities), `sum` + `area` (population) | `mean`, `percentage`, `distance`, `sum` (`area = true`) |
| **`amazonia`** | Amazônia Legal (2,229 cells) | 50,000 m (EPSG:29191) | `coverage` (PRODES), `distance` (ports, roads), `area` (protected areas) | `percentage`, `distance`, `area` |
| **`majority`** | Itaituba / PA (620 cells, 31 × 20) | 5,000 m (EPSG:29191) | `mode` (predominant deforestation class) | `majority` |
| **`emas`** | P. N. das Emas (5,514 cells) | 500 m (EPSG:29192) | `presence` (firebreaks, rivers), `maximum`, `minimum` (vegetation cover) | `presence`, `max`, `min` |

Each comparison in `benchmarks/terrame_fill/<dataset>.compare.toml` is declared as one of:

* `expect = "match"` — has an explicit criterion (`max_abs_error` and/or `min_share` at `tol`); **the run exits with status 1 if it is not met**.
* `expect = "differs"` — reported only, never fails the run; available for operators that differ by construction (none at the moment).
* `kind = "categorical"` — compares class values (TerraME `mode`): the golden column is text, one class or every tied class (`"7,87"`); a cell agrees when DisSCube's class is one of them, and the criterion is `min_share`.
* `[[unsupported]]` — TerraME operation with no DisSCube operator yet (none at the moment).

---

## 3. Quantitative Parity Results

Obtained with **DisSCube** (`main`, commit `cef6ee2`; only `population` needs it, everything else also runs on PyPI 0.4.0) against the **`luccme-goldens` v1.0.0** fill goldens (TerraME 2.0.1). The tables are produced by `compare.py` (`make benchmark-all`); CI publishes them in each job summary. Coverage values are fractions (0–1), as in the goldens.

### Itaituba (31 × 20 cells, 5 km, EPSG:29191)

| Variable | Cells | Mean \|Err\| | Max \|Err\| | Bias | Pearson $r$ | Criterion | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `elevation` | 620 | 0.889 m | 10.1 m | -0.0746 m | 0.9995 | max ≤ 11 m | **match** |
| `defor_7` | 620 | 0.00054 | 0.00638 | -3.4e-05 | 1.0000 | max ≤ 0.01 | **match** |
| `defor_87` | 620 | 0.00054 | 0.00638 | +1.4e-05 | 1.0000 | max ≤ 0.01 | **match** |
| `defor_167` | 620 | 6.5e-05 | 0.00395 | +2.0e-05 | 1.0000 | max ≤ 0.01 | **match** |
| `defor_255` | 620 | 5.2e-08 | 2.2e-05 | -1.8e-08 | 1.0000 | max ≤ 0.01 | **match** |
| `distroad` | 620 | 24 m | 1,885 m | -24 m | 0.9999 | ≥ 94% within 100 m (94.5%) | **match** |
| `distlocal` | 620 | 1.2e-06 m | 5.0e-06 m | +3.3e-08 m | 1.0000 | 100% within 1 m | **match (exact)** |
| `population` | 620 | 9.1e-09 | 3.8e-07 | -6.1e-11 | 1.0000 | max ≤ 1e-5 | **match** |

### Amazônia Legal (2,229 cells, 50 km, EPSG:29191)

| Variable | Cells | Mean \|Err\| | Max \|Err\| | Bias | Pearson $r$ | Criterion | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `prodes_10` | 2,174 | 6.7e-13 | 4.8e-11 | +1.6e-13 | 1.0000 | max ≤ 1e-4 | **match (identical)** |
| `prodes_208` | 2,174 | 1.1e-12 | 4.9e-11 | -1.4e-13 | 1.0000 | max ≤ 1e-4 | **match (identical)** |
| `protected` | 2,229 | 1.75e-05 | 0.00433 | -1.75e-05 | 1.0000 | ≥ 99% within 0.01 (100.0%) | **match** |
| `distroads` | 2,229 | 300 m | 18.1 km | -300 m | 0.9999 | ≥ 78% within 100 m (79.2%) | **match** |
| `distports` | 2,229 | 3.7e-05 m | 5.0e-04 m | -2.1e-06 m | 1.0000 | 100% within 1 m | **match (exact)** |

The 55 cells without PRODES pixels are `NaN` in DisSCube and `0` in TerraME; the benchmark checks that TerraME's value there is exactly that expected value (`nan_ref = 0.0`).

### Itaituba, predominant class (`majority`, 620 cells, 5 km)

| Variable | Cells | Agreement | Criterion | Status |
| :--- | :--- | :--- | :--- | :--- |
| `defor_mode` | 620 | **100.0%** | ≥ 100% agree | **match** |

TerraME's `mode` lists every tied class (`"7,87"`) and DisSCube's `majority` keeps the smallest; a cell agrees when DisSCube's class is among the listed ones. In this raster (classes 7, 87 and 167) no cell has a tie, so the comparison is exact. The reference is pinned to a `luccme-goldens` commit (SHA-256 verified), not to a release.

### Parque Nacional das Emas (5,514 cells, 500 m, EPSG:29192)

| Variable | Cells | Same-value share | Criterion | Status |
| :--- | :--- | :--- | :--- | :--- |
| `firebreak` | 5,514 | **98.4%** | ≥ 98.0% | **match** |
| `river` | 5,514 | **99.7%** | ≥ 98.0% | **match** |
| `maxcover` | 5,514 | **98.7%** | ≥ 98.5% | **match** |
| `mincover` | 5,514 | **99.0%** | ≥ 98.5% | **match** |

---

## 4. Understanding Documented Divergences

* **Line distances (`distance`: `distroad`, `distroads`):** TerraME 2.0.1 measures from the cell centre to the nearest *vertex* of a polyline; DisSCube (GEOS/Shapely) measures to the nearest point on the *segment*. DisSCube's distance is therefore never larger, and the gap concentrates where road vertices are sparse (94.5% of cells within 100 m at 5 km, 79.2% at 50 km).
* **Point distances (`distlocal`, `distports`):** points are vertices by definition, so both tools agree to numerical precision (< 1e-5 m).
* **Coverage (`percentage`):** both tools divide by the valid pixels of the cell, so no correction is needed (identical for PRODES, below 0.0064 for deforestation in Itaituba).
* **Elevation (`mean`):** area-weighted resampling of a 923 m raster in DisSCube versus TerraME's `average`.
* **Lines and border pixels (Emas):** lines are rasterized through cell centres, whereas TerraME marks every cell a line touches; border pixels count for two cells in DisSCube. Both cause the 0.3–1.6% of cells with a different value.
* **Population (`sum` with `area = true`):** the census attribute is shared among cells in proportion to the intersected area; the total is conserved and all 620 cells match.

> The older `min_distance` operator (a raster approximation between rasterized cell centres) is deliberately **not** used here: it is biased against TerraME by -552 m and -273 m on Itaituba.

---

## 5. Quick Start

### 1. Installation
```bash
git clone https://github.com/LambdaGeo/disscube-benchmark.git
cd disscube-benchmark

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Validate Declarative Pipelines
```bash
make validate
```

### 3. Run Benchmarks
You can execute a specific benchmark or the full suite:

```bash
# Run Itaituba benchmark (derivation + comparison)
make benchmark DATASET=itaituba

# Run Amazônia benchmark
make benchmark DATASET=amazonia

# Run Emas benchmark
make benchmark DATASET=emas

# Run all benchmarks in batch
make benchmark-all
```

Outputs and comparison reports are generated in `benchmarks/terrame_fill/reports/<dataset>/`:
* `report.md`: Markdown summary table ready for copy-pasting.
* `report.json`: Machine-readable metrics payload.

Goldens are downloaded once to `~/.cache/disscube/goldens` and verified by SHA-256. To work offline, point `LUCCME_GOLDENS_DIR` to a local clone of `luccme-goldens` (the same hash is checked):

```bash
LUCCME_GOLDENS_DIR=~/src/luccme-goldens make benchmark DATASET=emas
```

---

## 6. Repository Structure

```text
disscube-benchmark/
├── .github/
│   └── workflows/
│       └── ci.yml                   # GitHub Actions CI: validate + benchmark matrix
├── benchmarks/
│   └── terrame_fill/
│       ├── README.md                # Detailed documentation of the suite
│       ├── amazonia.compare.toml    # Comparison spec (Amazônia): goldens URL + SHA-256, criteria
│       ├── amazonia.toml            # Declarative pipeline (Amazônia)
│       ├── compare.py               # Metrics engine (MAE, max error, bias, r, tolerance share)
│       ├── emas.compare.toml
│       ├── emas.toml
│       ├── majority.compare.toml
│       ├── majority.toml
│       ├── itaituba.compare.toml
│       ├── itaituba.toml
│       └── run.sh                   # Suite runner: run | compare | all
├── .gitignore
├── CITATION.cff                     # Citation metadata
├── LICENSE                          # MIT License
├── Makefile                         # validate, run, compare, benchmark, benchmark-all, clean
├── README.md                        # General documentation with parity tables
└── requirements.txt                 # Python dependencies
```

---

## 7. Citation and Attribution

If you use this benchmark suite in scientific research, please cite:

**BibTeX:**
```bibtex
@software{costa2026disscube_benchmark,
  author       = {Costa, S{\'e}rgio Souza},
  title        = {disscube-benchmark: Quantitative Numerical and Spatial Parity Benchmark for DisSCube against Canonical TerraME Goldens},
  year         = {2026},
  publisher    = {GitHub},
  journal      = {GitHub repository},
  howpublished = {\url{https://github.com/LambdaGeo/disscube-benchmark}}
}
```

Reference golden datasets used by this benchmark are archived on Zenodo:
> Costa, S. S. (2026). *luccme-goldens: Canonical Reference Execution Outputs for TerraME 2.0.1 and LuccME 3.1* (Version v1.0.0). Zenodo. https://doi.org/10.5281/zenodo.23107748
