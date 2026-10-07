# KG_Assoc operational tools

Run commands from the repository root. These tools preserve provenance but do
not make a restart time or a time origin into an independent replica: use a
different stochastic seed for each independent realization.

`C1_e2_s*_t40000` denotes 40,000 **physical time units**, not 40,000 MD
steps. COM coordinates are unwrapped only within one executable segment. Do
not stitch COM trajectories across a restart without reconstructing image
history. Raw correlator `n_pairs` and multi-tau origin counts are support
metadata, not independent statistical samples.

## Preparation and restart bank

### `scripts/prepare_p42_c1_replicas.sh`

Purpose: build independent C1 E1 states, create C1 E2 restart-bank entries,
validate them, and run a short continuation smoke test.

Example: `examples/KG_Assoc/scripts/prepare_p42_c1_replicas.sh 12003 12004`

Inputs: the generated C1 LAMMPS data and requested unique seeds. Outputs: E1
data/provenance and restart pairs under `systems/restart_bank/C1`. It refuses
to overwrite existing artifacts. This is a dedicated-host equilibration tool.

### `run_p33_c1_restart_bank.sh`

Purpose: create `t40000`, `t50000`, and `t60000` C1 E2 restart pairs from E1
states and invoke restart-bank validation.

Example: `P33_C1_SEEDS="12001 12002" examples/KG_Assoc/run_p33_c1_restart_bank.sh`

Inputs: `systems/e1_equilibrated/C1_long_s*.e1.lammpsdat`. Outputs: paired
`.restart.lammpsdat` and `.assoc_restart` files. Do not use different bank
times from the same seed as independent replicas.

### `analysis/validate_c1_restart_bank.py`

Purpose: audit C1 restart-bank pairs and their associating topology.

Example: `python3 examples/KG_Assoc/analysis/validate_c1_restart_bank.py \
  --bank-dir examples/KG_Assoc/systems/restart_bank/C1 --seeds 12001,12002`

Inputs: a bank directory and comma-separated seed list. Outputs: validation
report to standard output. Run it before accepting new seed states.

## Production, validation, and profiling

### `scripts/run_p41_validation.sh` and `scripts/benchmark_p41_short.sh`

Purpose: dedicated-host P4.1 validation and controlled baseline/production
throughput comparison. Inputs: documented C1 restart. Outputs: validation and
benchmark logs. Use before changing production instrumentation; these are not
rheology-production runners.

### `scripts/profile_p42_short.sh`

Purpose: short Nsight Systems baseline/production structural profile.

Example: `INPUT=examples/KG_Assoc/systems/restart_bank/C1/C1_e2_s12001_t40000 \
  examples/KG_Assoc/scripts/profile_p42_short.sh`

Outputs: one fresh profile subdirectory containing reports, stats, and target
logs. It rejects failed applications and CUDA-trace-free reports. It is not an
Nsight Compute runner.

### `scripts/run_p42_rheology_pilot.sh`

Purpose: run one or more production restart segments with every-step stress,
fresh output paths, provenance, duplicate-seed rejection, and completion
checks.

Example continuation command:

```bash
P42_PILOT_RUN_KIND=64M_continuation \
P42_PILOT_STEPS=64000000 \
P42_PILOT_COM_EVERY=10000 \
P42_PILOT_DIR=p42_diffusion_continuation \
  examples/KG_Assoc/scripts/run_p42_rheology_pilot.sh \
  p42_rheology_pilot/run.MBA5fA/C1_e2_s12001_t40000 \
  p42_rheology_pilot/run.MBA5fA/C1_e2_s12002_t40000 \
  p42_rheology_pilot/run.RqADk7/C1_e2_s12003_t40000
```

Inputs: restart prefixes, each with both restart files. Outputs: a unique
`run.*` directory with simulation files, logs, and `provenance.txt`; it records
the parent restart paths/SHA256, run kind, stress sampling, COM cadence, and
frame cadence. The production executable samples stress every MD step; the
example writes COM and frame/topology output every 10,000 MD steps. A restarted
COM trajectory remains a separate unwrapped segment.

### `analysis/analyze_p42_rheology_pilot.py`

Purpose: analyze six-channel stress correlators, tail support sensitivity, and
replica-level tail classification.

Example: `python3 examples/KG_Assoc/analysis/analyze_p42_rheology_pilot.py \
  --output-prefix "$RUN_DIR/rheology" "$RUN_DIR"/*.stress_correlator`

Outputs: mean, replica, window, support-sensitivity CSVs and JSON summary.
`n_pairs` is raw correlation support, not an effective sample count. P4.2/P4.3
conclusions are C1-specific; 32M is not a universal sufficient duration.

## COM transport observables

### `analysis/analyze_p44_com_diffusion.py`

Purpose: selected-lag multi-tau star-COM MSD and terminal-diffusion diagnosis.

Example: `python3.11 examples/KG_Assoc/analysis/analyze_p44_com_diffusion.py \
  --output-prefix "$RUN_DIR/diffusion" "$RUN_DIR"/*.com_trajectory`

Outputs: `<prefix>.diffusion.replicas.csv`, `<prefix>.diffusion.mean.csv`, fit
CSV, and JSON summary. It validates ordered IDs and a uniform segment-local COM grid. Origin
counts are support only; independent segment replicas define uncertainty. The
present 32M C1 segments are not terminally diffusive.

### `analysis/analyze_p44_com_fsqt.py`

Purpose: isotropically averaged self intermediate scattering function of star
COMs at the fixed nine-value q grid from 0.1 to 10, including `q=1`.

Example: `python3.11 examples/KG_Assoc/analysis/analyze_p44_com_fsqt.py \
  --output-prefix "$RUN_DIR/fsqt" "$RUN_DIR"/*.com_trajectory`

Outputs: `<prefix>.fsqt.replicas.csv`, `<prefix>.fsqt.mean.csv`, and JSON
diagnostics/crossing times. It uses `correlator.SqtCorrelatorIsotropicManyQ`, evaluating
`mean[sinc(q |Delta R|)]` over stars at selected multi-tau lags. It is a self,
not collective, correlator. High-q relaxation may occur before the first
100-time-unit COM lag in the current 32M data.

## Network topology

### `analysis/analyze_p46_bond_dynamics.py`

Purpose: reconstruct temporary sticker-bond episodes and partner exchange from
production event streams. It uses the parent restart named by each event file
to identify opening left-censored bonds, and can validate reconstruction against
the synchronized topology stream.

Example:

```bash
python3 examples/KG_Assoc/analysis/analyze_p46_bond_dynamics.py \
  --system examples/KG_Assoc/systems/restart_bank/C1/C1_e2_s12001_t40000.restart.lammpsdat \
  --output-prefix p46_c1_bonds \
  --topology p42_rheology_pilot/run.MBA5fA/C1_e2_s12001_t40000.topology \
  p42_rheology_pilot/run.MBA5fA/C1_e2_s12001_t40000.events
```

Outputs: episode, all/intra/inter Kaplan-Meier survival, rebinding, partner
exchange, and summary files. A bond is the unordered pair of sticker atom IDs.
Opening bonds are left-censored and excluded from the Kaplan-Meier risk set;
known-origin bonds active at segment end are right-censored. Rebinding categories
are same sticker, different sticker on the same prior-partner star, different
star, and unbound at segment end. Star-neighbor changes are only inter-star
multiplicity transitions between zero and one; a parallel-bond event can change
`k_bond` without changing `k_neighbor`.

### `analysis/analyze_p45_topology.py`

Purpose: reconstruct the static transient sticker network from synchronized
`.topology` frames. Supply the LAMMPS restart/system file explicitly so all
stars, sticker atoms, and isolated nodes are known.

Example:

```bash
python3 examples/KG_Assoc/analysis/analyze_p45_topology.py \
  --system examples/KG_Assoc/systems/restart_bank/C1/C1_e2_s12001_t40000.restart.lammpsdat \
  --output-prefix p45_c1_topology \
  p42_rheology_pilot/run.MBA5fA/C1_e2_s12001_t40000.topology \
  p42_rheology_pilot/run.MBA5fA/C1_e2_s12002_t40000.topology
```

Outputs: `<prefix>.frames.csv`, degree-bond, degree-neighbor, edge-multiplicity,
and cluster-size histograms, plus a JSON summary with per-replica means and
replica-level uncertainty. Nodes are stars; each inter-star sticker bond is a
multigraph edge, while the component calculation uses its corresponding simple
graph. An intra-star bond is not an edge, counts once in `n_intra`, and consumes
two stickers on that star; an inter-star bond consumes one sticker at each end.

Production topology files list each physical temporary bond once in ascending
atom-ID order and include both molecule IDs. The analyzer rejects duplicate,
reciprocal, nonreciprocal, malformed, or non-sticker endpoints. Largest
connected component is not proof of PBC wrapping/percolation; winding analysis
is deliberately deferred. This tool is static topology only: it does not infer
lifetimes, partner exchange, walking, or hopping.

## Visualization

### `analysis/plot_analysis.py`

Purpose: make quick interactive or saved Matplotlib inspection plots from the
mean CSV files. It uses only the standard library and Matplotlib.

Basic forms:

```bash
python3 examples/KG_Assoc/analysis/plot_analysis.py fsqt p44_c1.fsqt.mean.csv
python3 examples/KG_Assoc/analysis/plot_analysis.py rheology rheology.mean.csv
python3 examples/KG_Assoc/analysis/plot_analysis.py diffusion \
  p44_c1_diffusion.diffusion.mean.csv
```

Use `--output FILE.png` to save, `--no-show` for headless use, `--title TEXT`
to override the title, and `--dpi N` to change the default 150 DPI. If an
output is supplied without `--no-show`, the figure is saved and then shown.

`fsqt` discovers all q values from long-format `q,lag_time,fsqt_mean` data and
plots every curve by default. Use `--q 0.1 0.316227766 1.0` to select q values.
`rheology` uses a log-x/symlog-y total `G(t)` plot; add `--components` for the
six channels or `--positive-log` for a positive-only log-log view. `diffusion`
uses log-log MSD axes; add `--alpha` for a separate local-slope figure and
`--show-diffusive-guide` or `--show-subdiffusive-guide` for late-time `t^1` or
`t^{1/2}` visual references. Add `--replicas FILE` to show low-emphasis
replica curves, `--no-sem` to hide the SEM band, and `--xmin`, `--xmax`,
`--ymin`, or `--ymax` for manual primary-axis limits. The alpha image is named
`<output-stem>.alpha.png` when `--output` is used.

`topology` detects the P4.5 frame, degree-bond, degree-neighbor,
edge-multiplicity, and component-weighted cluster-size CSV schemas from their
headers. For frame files it creates separate figures for inter-star bonds,
mean neighbor degree, isolated-star fraction, and largest-component fraction
by default; use `--metric NAME [NAME ...]` to choose other frame columns. With
`--output topology.png`, these become files such as
`topology.inter_bonds.png`. Distribution plots use normalized probabilities by
default; add `--counts` for raw histogram counts. Cluster-size histograms remain
explicitly component-weighted and default to a logarithmic y axis.

```bash
python3 examples/KG_Assoc/analysis/plot_analysis.py topology \
  p45_c1_topology.frames.csv
python3 examples/KG_Assoc/analysis/plot_analysis.py topology \
  p45_c1_topology.degree_neighbor.csv
python3 examples/KG_Assoc/analysis/plot_analysis.py topology \
  p45_c1_topology.edge_multiplicity.csv \
  --output multiplicity.png --no-show
```

For example, save an F_s(q,t) plot without a display:

```bash
python3 examples/KG_Assoc/analysis/plot_analysis.py fsqt \
  p44_c1.fsqt.mean.csv --output fsqt.png --no-show

python3 examples/KG_Assoc/analysis/plot_analysis.py diffusion \
  p44_c1_diffusion.diffusion.mean.csv \
  --alpha --show-diffusive-guide --show-subdiffusive-guide
```
