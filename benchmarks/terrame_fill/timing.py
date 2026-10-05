#!/usr/bin/env python3
"""timing.py — time and peak memory of a DisSCube pipeline, next to the TerraME reference.

  python benchmarks/terrame_fill/timing.py <dataset> [--reps 5]
  make timing DATASET=connectivity REPS=5

Inputs are fetched first (not timed). Each repetition starts from an empty workspace; rep 0 is a
warm-up and is excluded. Writes reports/<dataset>/timing.json.

If <dataset>.compare.toml has `timing_url` and `timing_sha256` (set by `make pins` in
luccme-goldens), the frozen TerraME measurement is fetched, SHA-256 verified, and printed next to
this run. It is informational only and never fails: the two times are comparable only if they
were measured on equivalent machines/limits (see environment.json in luccme-goldens). Set
LUCCME_GOLDENS_DIR to read goldens/timing/ from a local clone.
"""
import argparse, json, os, platform, resource, shutil, statistics, subprocess, sys, tempfile, time
from importlib.metadata import version
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib

HERE = Path(__file__).resolve().parent


def _cpu_model():
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or None


def _ram_mb():
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal"):
                return round(int(line.split()[1]) / 1024)
    except OSError:
        pass
    return None


def _terrame_reference(ds):
    url, want = ds.get("timing_url"), ds.get("timing_sha256")
    if not want:
        return None
    import hashlib
    local = os.environ.get("LUCCME_GOLDENS_DIR")
    if not local:
        cand = HERE.parents[2] / "luccme-goldens"
        local = str(cand) if cand.is_dir() else None
    path = Path(local) / "goldens" / "timing" / "timing_terrame.json" if local else None
    if path and path.exists():
        if hashlib.sha256(path.read_bytes()).hexdigest() != want:
            raise SystemExit(f"{path}: sha256 differs from timing_sha256 in the compare.toml")
    elif url:
        import pooch
        path = Path(pooch.retrieve(url=url, known_hash=f"sha256:{want}",
                                   path=pooch.os_cache("disscube") / "goldens", fname="timing_terrame.json"))
    else:
        return None
    return json.loads(path.read_text())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset")
    ap.add_argument("--reps", type=int, default=5)
    a = ap.parse_args()

    pipeline = HERE / f"{a.dataset}.toml"
    compare = tomllib.loads((HERE / f"{a.dataset}.compare.toml").read_text())["dataset"]
    out_dir = HERE / "reports" / a.dataset
    out_dir.mkdir(parents=True, exist_ok=True)

    subprocess.run(["disscube", "fetch", str(pipeline)], check=True, capture_output=True)  # not timed

    rows = []
    for rep in range(a.reps + 1):
        ws = tempfile.mkdtemp(prefix=f"timing_{a.dataset}_")
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        t0 = time.perf_counter()
        r = subprocess.run(["disscube", "run", str(pipeline), "--workspace", ws], capture_output=True, text=True)
        wall = time.perf_counter() - t0
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        shutil.rmtree(ws, ignore_errors=True)
        if r.returncode:
            sys.exit(r.stderr[-800:])
        rows.append({"rep": rep, "wall_s": round(wall, 3),
                     "user_s": round(after.ru_utime - before.ru_utime, 3),
                     "sys_s": round(after.ru_stime - before.ru_stime, 3),
                     # ru_maxrss is the max over all children so far (KB on Linux)
                     "max_rss_mb": round(after.ru_maxrss / 1024, 1)})
    kept = rows[1:]
    wall = [r["wall_s"] for r in kept]
    result = {
        "dataset": a.dataset,
        "engine": f"DisSCube {version('disscube')}",
        "reps": len(kept),
        "wall_s": {"median": statistics.median(wall), "min": min(wall), "max": max(wall)},
        "max_rss_mb": max(r["max_rss_mb"] for r in kept),
        "runs": rows,
        "environment": {"python": platform.python_version(), "cpu_model": _cpu_model(),
                        "cores": os.cpu_count(), "ram_mb": _ram_mb(), "os": platform.platform()},
    }
    ref = _terrame_reference(compare)
    if ref and a.dataset in ref.get("datasets", {}):
        t = ref["datasets"][a.dataset]
        result["terrame_reference"] = {"wall_s": t["wall_s"], "max_rss_mb": t["max_rss_mb"], "reps": t["reps"]}
    (out_dir / "timing.json").write_text(json.dumps(result, indent=2) + "\n")

    print(f"{a.dataset}: DisSCube wall median {result['wall_s']['median']:.2f} s "
          f"(min {result['wall_s']['min']:.2f}, max {result['wall_s']['max']:.2f}), "
          f"peak memory {result['max_rss_mb']} MB, {len(kept)} reps")
    if "terrame_reference" in result:
        t = result["terrame_reference"]
        print(f"{'':>{len(a.dataset)}}  TerraME wall median {t['wall_s']['median']:.2f} s, peak memory "
              f"{t['max_rss_mb']} MB (frozen measurement; comparable only on equivalent machines)")
    else:
        print("  no TerraME timing reference pinned in the compare.toml (timing_url / timing_sha256)")


if __name__ == "__main__":
    main()
