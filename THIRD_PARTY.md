# Third-party material

This repository stores **no third-party data and no third-party code**. Everything below is
fetched at run time from the upstream project, from a **fixed commit** (not a branch), and every file is
checked against the SHA-256 recorded in the corresponding `benchmarks/terrame_fill/<dataset>.toml` before it is used.
A file that changed upstream, or was replaced, fails before any metric is computed.

| Material | Upstream | Fixed at | Licence declared by upstream | Used by |
|---|---|---|---|---|
| `packages/gis/data/` (amazonia-*, emas-*, itaituba-*) | [TerraME/terrame](https://github.com/TerraME/terrame) | commit `84faddc4e5149a89d7486444b61b8c50474e199c` | LGPL (TerraME, INPE and TerraLAB/UFOP) | `amazonia`, `emas`, `itaituba`, `majority` |
| `data/br_roads_5880`, `br_ports_5880`, `br_cs_5880_25x25km` | [TerraME/gpm](https://github.com/TerraME/gpm) | commit `3aa0e91498f37d1b55adbe54d5d0fda3137f251f` (6 Dec 2019, last commit) | `description.lua`: LGPL-3; `license.txt`: GPL-3 text (the upstream is inconsistent; we redistribute nothing) | `connectivity` |
| Reference outputs (goldens) and TerraME timing | [LambdaGeo/luccme-goldens](https://github.com/LambdaGeo/luccme-goldens) | tag `v1.1.0` (`benchmark_pins.json`) | see that repository | all |

The SHA-256 of each file is in the `.toml` of the dataset. The binary that produced the goldens (TerraME 2.0.1,
LuccME 3.1, gpm 0.6) is described in [`terrame-docker`](https://github.com/profsergiocosta/terrame-docker).

`benchmarks/terrame_fill/node_cost/case_247km/` contains two diffs against `lua/Network.lua` of TerraME/gpm
(`Network_trace.diff`, `Network_fix_experiment.diff`). They are changes to a file of that project, offered under its licence.

The code in this repository is MIT (see `LICENSE`).
