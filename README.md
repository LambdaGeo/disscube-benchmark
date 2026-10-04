# disscube-benchmark

[![CI](https://github.com/LambdaGeo/disscube-benchmark/actions/workflows/ci.yml/badge.svg)](https://github.com/LambdaGeo/disscube-benchmark/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX) <!-- TODO: DOI of this repository's own release -->
[![Goldens: Zenodo DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23107748.svg)](https://doi.org/10.5281/zenodo.23107748) <!-- TODO: replace with the DOI of the goldens release that includes majority, connectivity and per-year goldens -->
[![Upstream: DisSCube](https://img.shields.io/badge/Engine-DisSCube-green.svg)](https://pypi.org/project/disscube/)

**Quantitative numerical and spatial parity benchmark of DisSCube against TerraME reference outputs (goldens).**

This repository is **Level 2 (parity benchmark and quantitative validation)** of the replication framework presented in:

> Costa, S. S. (2026). *Declarative Spatial Data Cubes and Verifiable Provenance for Reproducible Land-Use Change Modelling: A Three-Level Replication of LuccME*. Big Earth Data (Taylor & Francis).

Reviewers and readers can verify every number in the paper by running this repository (see [Quick start](#4-quick-start)). No TerraME installation is needed: the references are pre-computed, hashed and archived.

---

## 1. Scientific motivation

Porting a model or a data-preparation step from an imperative platform (TerraME 2.0.1, LuccME 3.1) to a declarative one (DisSCube) is not validated by running demonstration code. It is validated by comparing results, cell by cell, against reference outputs produced by the original platform.

This benchmark derives each variable with DisSCube **on the same grid** that TerraME used, and compares it with the cellular space TerraME produced (`goldens/fill/<dataset>_terrame.csv` in [`luccme-goldens`](https://github.com/LambdaGeo/luccme-goldens)). It reports, per variable:

1. Mean absolute error (MAE) and maximum absolute error over all cells.
2. Mean bias error (MBE) and Pearson correlation (r).
3. The share of cells within a stated tolerance (`min_share` at `tol`).
4. For categorical variables, the share of cells whose class agrees.

Where the two platforms differ **by construction**, the difference is documented and explained (section 5), not hidden by loosening a threshold.

No reference data and no TerraME code is stored here. Goldens are fetched at run time and verified by SHA-256.

---

## 2. Reproducibility chain

Every artifact in the chain is versioned, hashed and, where applicable, archived with a DOI.

| Level | Artifact | What it provides | Pinned version | Identifier |
| --- | --- | --- | --- | --- |
| Engine | [`disscube`](https://github.com/DisSModel/disscube) | The software under test | `X.Y.Z` <!-- TODO: release containing network_cost and sum with area=true --> | PyPI + DOI <!-- TODO --> |
| Reference outputs | [`luccme-goldens`](https://github.com/LambdaGeo/luccme-goldens) | TerraME/LuccME results (fill, labs, per-year) | `vX.Y.Z` <!-- TODO --> | DOI <!-- TODO --> |
| Reference generator | [`terrame-docker`](https://github.com/LambdaGeo/terrame-docker) | TerraME 2.0.1 + LuccME 3.1 image used to produce the goldens | `X.Y.Z` <!-- TODO --> | image digest `sha256:...` <!-- TODO --> + DOI |
| Benchmark | this repository | Pipelines, comparison specs, metrics engine | `vX.Y.Z` <!-- TODO --> | DOI <!-- TODO --> |

Each `<dataset>.compare.toml` records the URL and SHA-256 of its golden, so a wrong or modified reference file fails before any metric is computed.

---

## 3. Benchmark suite: `terrame_fill`

The suite evaluates the spatial aggregation and feature-extraction operations of TerraME's `gis` package (`cs:fill{}`) across five cases.

| Case | Domain and size | Grid and CRS | TerraME `fill` operation | DisSCube operator |
| --- | --- | --- | --- | --- |
| `itaituba` | Itaituba / PA, 620 cells (31 × 20) | 5,000 m, EPSG:29191 | `average` (elevation), `coverage` (deforestation), `distance` (roads, localities), `sum` + `area` (population) | `mean`, `percentage`, `distance`, `sum` (`area = true`) |
| `amazonia` | Amazônia Legal, 2,229 cells | 50,000 m, EPSG:29191 | `coverage` (PRODES), `distance` (ports, roads), `area` (protected areas) | `percentage`, `distance`, `area` |
| `majority` | Itaituba / PA, 620 cells (31 × 20) | 5,000 m, EPSG:29191 | `mode` (predominant deforestation class) | `majority` |
| `emas` | P. N. das Emas, 5,514 cells | 500 m, EPSG:29192 | `presence` (firebreaks, rivers), `maximum`, `minimum` (vegetation cover) | `presence`, `max`, `min` |
| `connectivity` | Brazil, 14,255 cells | 25,000 m, EPSG:5880 | GPM `Network` (generalized transport cost, GTC, to 14 ports) | `network_cost` (exact multi-source Dijkstra) |

Each `benchmarks/terrame_fill/<dataset>.compare.toml` declares every comparison as one of:

- `expect = "match"`: has an explicit criterion (`max_abs_error` and/or `min_share` at `tol`). **The run exits with status 1 if the criterion is not met.**
- `expect = "differs"`: reported only, never fails the run. Used for `connectivity`, where the two methods are not expected to agree cell by cell (section 4).
- `kind = "categorical"`: compares class values (TerraME `mode`). The golden column is text, holding one class or every tied class (`"7,87"`). A cell agrees when DisSCube's class is one of them, and the criterion is `min_share`.
- `[[unsupported]]`: a TerraME operation with no DisSCube operator yet (none at the moment).

### How the criteria were set

The thresholds are **regression guards**: they fail CI if parity gets worse than what was observed and explained. They are not claims of equivalence beyond that. <!-- TODO: confirm this statement is accurate; if thresholds were derived from a physical argument (e.g. half the source pixel size), state that argument here per variable instead. -->

For every variable with a non-exact result, the cause of the difference is documented in section 5, and the table in section 4 shows the observed value next to the threshold so that the margin is visible.

---

## 4. Quantitative parity results

Obtained with DisSCube `X.Y.Z` against the `luccme-goldens` `vX.Y.Z` goldens (TerraME 2.0.1, LuccME 3.1). <!-- TODO: fill versions -->
The tables are produced by `compare.py` (`make benchmark-all`), and CI publishes them in each job summary. Coverage values are fractions (0–1), as in the goldens.

### Itaituba (31 × 20 cells, 5 km, EPSG:29191)

| Variable | Cells | Mean \|Err\| | Max \|Err\| | Bias | Pearson r | Criterion | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `elevation` | 620 | 0.889 m | 10.1 m | -0.0746 m | 0.9995 | max ≤ 11 m | match |
| `defor_7` | 620 | 0.00054 | 0.00638 | -3.4e-05 | 1.0000 | max ≤ 0.01 | match |
| `defor_87` | 620 | 0.00054 | 0.00638 | +1.4e-05 | 1.0000 | max ≤ 0.01 | match |
| `defor_167` | 620 | 6.5e-05 | 0.00395 | +2.0e-05 | 1.0000 | max ≤ 0.01 | match |
| `defor_255` | 620 | 5.2e-08 | 2.2e-05 | -1.8e-08 | 1.0000 | max ≤ 0.01 | match |
| `distroad` | 620 | 24 m | 1,885 m | -24 m | 0.9999 | ≥ 94% within 100 m (94.5%) | match |
| `distlocal` | 620 | 1.2e-06 m | 5.0e-06 m | +3.3e-08 m | 1.0000 | 100% within 1 m | match (exact) |
| `population` | 620 | 9.1e-09 | 3.8e-07 | -6.1e-11 | 1.0000 | max ≤ 1e-5 | match |

### Amazônia Legal (2,229 cells, 50 km, EPSG:29191)

| Variable | Cells | Mean \|Err\| | Max \|Err\| | Bias | Pearson r | Criterion | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `prodes_10` | 2,174 | 6.7e-13 | 4.8e-11 | +1.6e-13 | 1.0000 | max ≤ 1e-4 | match (identical) |
| `prodes_208` | 2,174 | 1.1e-12 | 4.9e-11 | -1.4e-13 | 1.0000 | max ≤ 1e-4 | match (identical) |
| `protected` | 2,229 | 1.75e-05 | 0.00433 | -1.75e-05 | 1.0000 | ≥ 99% within 0.01 (100.0%) | match |
| `distroads` | 2,229 | 300 m | 18.1 km | -300 m | 0.9999 | ≥ 78% within 100 m (79.2%) | match |
| `distports` | 2,229 | 3.7e-05 m | 5.0e-04 m | -2.1e-06 m | 1.0000 | 100% within 1 m | match (exact) |

The 55 cells without PRODES pixels are `NaN` in DisSCube and `0` in TerraME. The benchmark checks that TerraME's value there is exactly the expected one (`nan_ref = 0.0`).

### Itaituba, predominant class (`majority`, 620 cells, 5 km)

| Variable | Cells | Agreement | Criterion | Status |
| --- | --- | --- | --- | --- |
| `defor_mode` | 620 | 100.0% | ≥ 100% agree | match |

TerraME's `mode` lists every tied class (`"7,87"`), and DisSCube's `majority` keeps the smallest. A cell agrees when DisSCube's class is among the listed ones. In this raster (classes 7, 87 and 167) no cell has a tie, so the comparison is exact.

### Parque Nacional das Emas (5,514 cells, 500 m, EPSG:29192)

| Variable | Cells | Same-value share | Criterion | Status |
| --- | --- | --- | --- | --- |
| `firebreak` | 5,514 | 98.4% | ≥ 98.0% | match |
| `river` | 5,514 | 99.7% | ≥ 98.0% | match |
| `maxcover` | 5,514 | 98.7% | ≥ 98.5% | match |
| `mincover` | 5,514 | 99.0% | ≥ 98.5% | match |

### Connectivity: generalized transport cost to ports (`connectivity`, 14,255 cells, 25 km, EPSG:5880)

| Variable | Cells | Mean \|Err\| | Max \|Err\| | Bias | Pearson r | Within 25 km | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `cost` | 14,255 | 27.1 km | 370 km | -25.3 km | 0.9960 | 51.9% | differs (reported only) |

This comparison is **reported, not pass/fail**. The two tools use different methods: TerraME's `Network` (GPM) propagates costs over the road lines to build a route tree, whereas DisSCube computes the exact least cost with a multi-source Dijkstra over the road graph (`scipy.sparse.csgraph.dijkstra`), with the same ports, the same road layer and the same cost factors (`custo_ajus`, `outside = 2.0`). The correlation is high (r = 0.9960), so both preserve the regional pattern of accessibility, but they do **not** agree cell by cell, and **the cause of the difference is not yet established**.

#### What the difference looks like

Computed from the golden and the road layer used here:

- It is mostly one-sided: by the sign of the difference, DisSCube's cost is lower than TerraME's in 84.7% of cells and higher in 15.3%.
- It is **not smooth**. A few exact values recur: -26.80 km in about 2,900 cells (≈ 20% of the grid), -25.42 km in about 340, and -210.73 km in 227. Cells whose routes go through the same point of the network inherit the same offset.
- The bias grows with the distance of the cell centre to the nearest road (about -14 km within 5 km, about -38 km beyond 50 km).

#### What was tested and does not explain it

These checks rebuild TerraME's documented rules (read from the GPM source) in Python. They are approximations of TerraME, not TerraME runs.

| Hypothesis | Result |
| --- | --- |
| Different network topology (TerraME joins lines only at end points) | Not the cause: the shapefile has no T-junctions, and both graphs are identical (116,824 nodes) |
| One joint kept per pair of adjacent lines (14 short rings share both end points) | Not the cause: the recurring offsets are unchanged |
| Exact coordinate equality (`error = 0`) versus 1 mm rounding | Not the cause: the graphs differ by 1 node out of 116,825 |
| Straight-line distance between line ends instead of length along the polyline | Not the cause: it makes the difference larger (bias -38.3 km) |
| Two ports attached to the same road (TerraME keeps one target per line) | Not the cause: the 14 ports are on 14 different roads |
| How a cell and a port enter the network | Explains part of it: entering as TerraME does (closest line, foot of the perpendicular, nearest end) reduces the cells where TerraME is lower from 15.3% to about 2%, but it does not change the recurring offsets |

#### Open

The recurring negative offsets are still unexplained. The leading candidate is a suboptimal route chosen by TerraME at specific points of its propagation, but this is **not verified**: it requires TerraME's own per-node costs, which the golden does not contain. Until then, read the `connectivity` row as a documented difference between two methods, **not** as evidence that either tool is correct or incorrect.

<!-- TODO: after exporting per-node costs from TerraME (network.netpoints) and comparing them node by node with the exact Dijkstra, replace this subsection with the result and, if confirmed, name the mechanism. -->

#### Note on the input layer

In `br_roads_5880.shp`, `custo_ajus` is between 0.18 and 1.19 for almost every feature, but one 29 km segment has the value 1,194,000. It looks like a unit error (1.194 × 10⁶). Both tools read the same value, so it is not a source of disagreement between them, but it is worth correcting upstream.

---

## 5. Documented divergences

Differences below come from how each platform defines the operation, not from errors in either, with one exception: the cause of the `cost` difference is still open (section 4).

| Variable(s) | Operator | Observed difference | Cause |
| --- | --- | --- | --- |
| `distroad`, `distroads` | `distance` (lines) | DisSCube distance is never larger. 94.5% of cells within 100 m at 5 km, 79.2% at 50 km | TerraME 2.0.1 measures from the cell centre to the nearest *vertex* of a polyline. DisSCube (GEOS/Shapely) measures to the nearest point on the *segment*. The gap concentrates where road vertices are sparse |
| `distlocal`, `distports` | `distance` (points) | Agreement to numerical precision (< 1e-5 m) | Points are vertices by definition, so both definitions coincide |
| `defor_*`, `prodes_*` | `percentage` | Identical for PRODES. Below 0.0064 for deforestation in Itaituba | Both tools divide by the valid pixels of the cell, so no correction is needed |
| `elevation` | `mean` | Max error 10.1 m | DisSCube uses area-weighted resampling of a 923 m raster, whereas TerraME uses `average` |
| `firebreak`, `river` (Emas) | `presence` | 0.3–1.6% of cells with a different value | Lines are rasterized through cell centres in DisSCube, whereas TerraME marks every cell a line touches. Border pixels count for two cells in DisSCube |
| `population` | `sum` (`area = true`) | All 620 cells match | The census attribute is shared among cells in proportion to the intersected area, and the total is conserved |
| `cost` | `network_cost` | Mean error 27.1 km, bias -25.3 km, r = 0.9960 | Open. Different methods (route propagation in TerraME, exact Dijkstra in DisSCube), same layers and factors. The difference is concentrated in a few recurring offsets, and several candidate causes were ruled out. See section 4 |

> The older `min_distance` operator (a raster approximation between rasterized cell centres) is deliberately **not** used here. It is biased against TerraME by -552 m and -273 m on Itaituba.

---

## 6. Environment and pinning

Numerical results of spatial operations can depend on library versions (GEOS, GDAL, rasterio, shapely). To keep the comparison stable:

- DisSCube and the goldens are pinned to the versions in section 2.
- Python dependencies are in `requirements.txt`. DisSCube is pinned to a commit there. **The `connectivity` case needs `network_cost`, which is not in the pin `cef6ee2` and not in PyPI 0.4.0**: pin DisSCube to a release that contains it (`>=0.5.0`). <!-- TODO: after the DisSCube release, replace the git pin with the release and fill the version in sections 2 and 4. Also confirm exact pins or add a lock file, and consider a Dockerfile for the benchmark itself -->
- Goldens are downloaded once to `~/.cache/disscube/goldens` and verified by SHA-256 on every run.

<!-- TODO: if report.json does not yet record library versions (disscube, numpy, scipy, rasterio, shapely, GDAL, GEOS), add them, so any difference between machines can be traced. -->

---

## 7. Quick start

### Install

```bash
git clone https://github.com/LambdaGeo/disscube-benchmark.git
cd disscube-benchmark

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Validate the declarative pipelines

```bash
make validate
```

### Run the benchmarks

```bash
make benchmark DATASET=itaituba      # one case: derivation + comparison
make benchmark DATASET=amazonia
make benchmark DATASET=majority
make benchmark DATASET=emas
make benchmark DATASET=connectivity
make benchmark-all                   # the whole suite
```

Reports are written to `benchmarks/terrame_fill/reports/<dataset>/`:

- `report.md`: summary tables, ready to paste.
- `report.json`: machine-readable metrics.

The command exits with status 1 if any `expect = "match"` criterion is not met.

### Work offline

Point `LUCCME_GOLDENS_DIR` to a local clone of `luccme-goldens` (the same SHA-256 is still checked):

```bash
LUCCME_GOLDENS_DIR=~/src/luccme-goldens make benchmark DATASET=emas
```

### Verify from a clean machine

To confirm that the paper's numbers are reproducible without prior state:

```bash
rm -rf ~/.cache/disscube/goldens
make benchmark-all
```

The tables in `report.md` should match section 4.

---

## 8. Reproducing the references themselves (optional)

Reviewers who want to verify the goldens, and not only use them, can regenerate them with the TerraME image. No TerraME installation is required, only Docker.

```bash
git clone https://github.com/LambdaGeo/luccme-goldens.git
cd luccme-goldens
docker pull profsergiocosta/terrame-luccme@sha256:...   # TODO: digest used for the paper
make run-fill                                           # all fill cases
```

Regenerated CSV files should have the same SHA-256 as those listed in `checksums.sha256` of the pinned `luccme-goldens` release. (Zipped shapefiles are for visual inspection and are not part of the hash check.) <!-- TODO: confirm that the hashes of regenerated CSVs match on a second machine, and that connectivity (gpm) is covered by the published image -->

---

## 9. Repository structure

```
disscube-benchmark/
├── .github/workflows/ci.yml         # CI: validate + benchmark matrix
├── benchmarks/terrame_fill/
│   ├── README.md                    # Detailed documentation of the suite
│   ├── compare.py                   # Metrics engine (MAE, max error, bias, r, tolerance share)
│   ├── run.sh                       # Suite runner: run | compare | all
│   ├── <dataset>.toml               # Declarative pipeline (itaituba, amazonia, majority, emas, connectivity)
│   └── <dataset>.compare.toml       # Comparison spec: golden URL + SHA-256, criteria
├── CITATION.cff
├── LICENSE
├── Makefile                         # validate, run, compare, benchmark, benchmark-all, clean
├── README.md
└── requirements.txt
```

---

## 10. Citation

If you use this benchmark in scientific work, please cite the paper above and this repository:

```bibtex
@software{costa2026disscube_benchmark,
  author    = {Costa, S{\'e}rgio Souza},
  title     = {disscube-benchmark: Quantitative Parity Benchmark for DisSCube against TerraME Reference Outputs},
  year      = {2026},
  version   = {X.Y.Z},
  doi       = {10.5281/zenodo.XXXXXXX},
  url       = {https://github.com/LambdaGeo/disscube-benchmark}
}
```

The reference outputs are archived separately:

> Costa, S. S. (2026). *luccme-goldens: Canonical Reference Execution Outputs for TerraME 2.0.1 and LuccME 3.1* (Version vX.Y.Z). Zenodo. <https://doi.org/10.5281/zenodo.23107748>

Upstream TerraME and LuccME are Copyright (C) 2001–2017 INPE and TerraLAB/UFOP (LGPL-3.0).

## License

MIT. See [LICENSE](LICENSE).
