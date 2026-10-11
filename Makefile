# ==============================================================================
# Makefile — disscube-benchmark
# Quantitative Numerical and Spatial Parity Benchmark for DisSCube vs TerraME Goldens
# ==============================================================================

SHELL := /bin/bash

DATASET ?= itaituba
DATASETS := itaituba amazonia emas majority connectivity
REPS ?= 5

.PHONY: help validate run compare benchmark benchmark-all timing figure figure-operators clean

help:
	@echo "disscube-benchmark — Command Reference"
	@echo "------------------------------------------------------------------"
	@echo "  make validate               Validate all declarative pipeline TOMLs"
	@echo "  make benchmark              Run & compare default dataset (itaituba)"
	@echo "  make benchmark DATASET=emas Run & compare a specific dataset"
	@echo "  make benchmark-all          Run & compare all datasets (itaituba, amazonia, emas, majority, connectivity)"
	@echo "  make run DATASET=...        Run data cube derivation without comparing"
	@echo "  make compare DATASET=...    Run comparison against goldens (requires cube run)"
	@echo "  make timing DATASET=... REPS=5  Time/peak memory of the DisSCube run (+ pinned TerraME reference)"
	@echo "  make figure                 Figure of the connectivity case (needs: make run DATASET=connectivity)"
	@echo "  make figure-operators       Figure of four operators, DisSCube vs TerraME (needs: make run DATASET=itaituba and DATASET=majority)"
	@echo "  make clean                  Remove generated workspaces and test reports"

validate:
	@echo "==> Validating declarative pipelines in benchmarks/terrame_fill/..."
	@shopt -s nullglob; \
	for f in benchmarks/terrame_fill/*.toml; do \
		case "$$f" in *.compare.toml) continue ;; esac; \
		echo "Validating $$f..."; \
		disscube validate "$$f"; \
	done
	@echo "All pipelines validated successfully!"

run:
	@echo "==> Running DisSCube pipeline for $(DATASET)..."
	bash benchmarks/terrame_fill/run.sh run $(DATASET)

compare:
	@echo "==> Comparing DisSCube outputs against TerraME goldens for $(DATASET)..."
	bash benchmarks/terrame_fill/run.sh compare $(DATASET)

benchmark:
	@echo "==> Executing benchmark for $(DATASET)..."
	bash benchmarks/terrame_fill/run.sh all $(DATASET)

benchmark-all:
	@for d in $(DATASETS); do \
		echo ""; \
		echo "========================================================================"; \
		echo " BENCHMARK SUITE: $$d"; \
		echo "========================================================================"; \
		bash benchmarks/terrame_fill/run.sh all "$$d" || exit 1; \
	done
	@echo ""
	@echo "========================================================================";
	@echo " All benchmarks passed within expected numerical parity tolerances!";
	@echo "========================================================================";

timing:
	@echo "==> Timing DisSCube for $(DATASET)..."
	python benchmarks/terrame_fill/timing.py $(DATASET) --reps $(REPS)

figure:
	@echo "==> Figure: transport cost to ports, DisSCube vs TerraME..."
	python benchmarks/terrame_fill/figure_connectivity.py --workspace benchmarks/terrame_fill/data/connectivity --out benchmarks/terrame_fill/reports/connectivity/fig_connectivity_cost.png

figure-operators:
	@echo "==> Figure: four operators, DisSCube vs TerraME..."
	python benchmarks/terrame_fill/figure_operators.py --out benchmarks/terrame_fill/reports/operators/fig_operators.png

clean:
	rm -rf benchmarks/terrame_fill/data benchmarks/terrame_fill/reports benchmarks/terrame_fill/__pycache__
