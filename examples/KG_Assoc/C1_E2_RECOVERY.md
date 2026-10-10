# Prepared C1 corrected-chemistry recovery — execution not authorized

Starting HEAD: `34c2874804ed1adfd621d4abd58da480a8593040`, `KremerGrest`.
The periodic cell-assignment fix is present and unchanged. No 2M recovery, other
E2 condition or production was launched by this work.

## Scientific and restart specification

All three runs start from the **original** bank
`DATASET_ROOT/banks/e2/F04_N010_RP080_EE08/r001..r003/state` at step 6,000,000,
not from smoke outputs. They run 2,000,000 additional steps to absolute step
8,000,000. These remain the same three independent E1/E2 histories, not three
new independent replicas. Original states are loadable nonequilibrium recovery
starts, not accepted equilibrium samples of corrected chemistry.

The reader restores the permanent molecular state, velocities, reciprocal
temporary partners, accepted creation/break counters, frozen parameters and
absolute step. Input positions are centered/folded on load by the existing
`kg::createParticleDataFromLammps`; this changes periodic images, not geometry.
It does not preserve unwrapped-image continuity for a transport estimator.
Unit masses and bead identities are unchanged. `initVelocities=false` prevents
velocity resampling. Forces are recomputed for the initial state by the existing
GJF first-step initialization; no force snapshot or thermostat memory is loaded.

Frozen restart parameters are T=1, dt=.01, f=4, Narm=10, Ea=4, Ee=8, nu0=20,
Nevery=100, r_assoc=1.25, damping=2 (NVT friction .5), K=30 and R0=1.5. There
are 1000 stars, 41000 polymer beads and 2563 solvent beads. The original box is
preserved, including the documented small serialized-box density rounding around
rho_poly=.8 and total rho=.85. No DPD preparation setting is used.

Chemistry is stateless, keyed to `(seed, absolute step, ordered IDs, stream)`.
Keep seeds 22001/22002/22003; new reaction keys start at step 6,000,100, with
20,000 sweeps. Accepted-event order and all finite-step/Metropolis probabilities
remain unchanged. Final counters include the inherited 6M counts.

GJF initializes its internal MD step to zero; its Saru noise uses particle/group
index, local step and an effective 32-bit seed. It does not serialize the stream.
New local `--md-seed` reseeds System **immediately before** NVT construction and
does not change chemistry or resample velocities. Basic takes the third next32
value. A copy of the generator records that effective value without consuming
the live stream. ParticleGroup construction does not consume RNG values.

| History | Chemistry seed | Fresh MD System seed | Effective MD kernel seed |
|---|---:|---:|---:|
| r001 | 22001 | 32001 | 3928609932 |
| r002 | 22002 | 32002 | 3937019018 |
| r003 | 22003 | 32003 | 3945428108 |

Original effective kernel seeds were 3924086680, 3949264792 and 3940888472.
All six are distinct in the deterministic regression. Distinct seeds are the
standard independent-stream preparation policy, not proof of mathematical
independence of a PRNG. This is scientifically valid stochastic re-equilibration
with fresh future noise, **not bitwise continuation**. Do not stitch lifetimes,
COM, stress or transport histories across the algorithm/reseed/image boundary.
Default behavior without `--md-seed` is unchanged. The chemical sidecar schema is
unchanged and does not save MD stream state; every future segment must explicitly
record its reseed policy. No shared UAMMD or non-associating code was modified.

## Safety and validation

`campaign/kg_assoc_c1_recovery.py` implements plan/prepare/dry-run launch/status/
verify. The parent snapshot, chemical sidecar and original completion record have
pinned SHA256 references. All original scientific outputs are checked against the
pinned completion record; E1 provenance is checked too. Before prepare and every
actual replica launch, all three original parents are checked by the independent
candidate oracle: 2484/2538/2438 pairs and all eligible active bonds.

Preparation checks a clean committed tree, up-to-date executables, their hashes,
host self-test and retained GPU smoke evidence. It creates a NEW attempt directory
exclusively, with immutable `plan.json`, three empty replica directories and an
unapproved example approval. Launch re-authenticates commands, code, executables,
parents and evidence, and refuses any used replica directory. No overwrite,
`--force`, automatic retry, resumption or smoke-output substitution is supported.
A exclusive attempt lock prevents duplicate launches; a stale lock requires
manual investigation. Exclusive logs and running/incomplete/validated status
retain failure provenance. The runner stops immediately on the first failure.

Execution additionally requires `--execute`, a plan-hash-bound signed-off approval
JSON and validated **fresh-seed** capped GPU smoke from the prepared git SHA.
This gate remains uncleared until scientific execution approval. The example
approval is deliberately `approved=false`; never treat preparation as approval.

The generalized segment validator requires 2001 synchronized scalar/numerical
samples at steps 6M..8M, exactly 20000 chemistry sweeps, absolute event cadence,
time=step*.01, frozen parameters and correct input/seed provenance. It replays
ordered events from inherited partners/counters, verifies valence-one/accounting,
intra/inter counts, components/degree/L1/L2 against every network diagnostic and
final chemical mirrors/counters. It validates finite final positions/velocities,
permanent and temporary FENE geometry, endpoint timestamps and loaded/final kinetic
temperature consistency, plus runtime NVT and fresh effective-seed logs.

The ordinary recovery executable contains no all-pairs calculation. The oracle
is an input preflight, and remains per-chemistry-sweep instrumentation only in the
separate <=10000-step test build. No per-MD-step global bond scan was added.

## Exact commands

Run from repository root on the dedicated host. Retain the final approved SHA
and executables unchanged between preparation, smoke, launch and validation.
Replace version names with NEW immutable attempt/analysis names on any retry.

```bash
make -C examples/KG_Assoc -j2 kg_assoc_stars kg_assoc_candidates_test \
  kg_assoc_stars_candidate_smoke
export DATASET_ROOT="$(pwd)/examples/KG_Assoc/kg_assoc_100m"
export RECOVERY="$DATASET_ROOT/banks/e2_extensions/C1_periodic_recovery_v1"
export PRIOR_SMOKE="$DATASET_ROOT/aggregate/e2/C1_periodic_smoke_v1"
export FRESH_SMOKE="$DATASET_ROOT/aggregate/e2/C1_fresh_md_smoke_v1"

python3 examples/KG_Assoc/campaign/kg_assoc_c1_recovery.py plan \
  --dataset-root "$DATASET_ROOT" --output "$RECOVERY"
python3 examples/KG_Assoc/campaign/kg_assoc_c1_recovery.py prepare \
  --dataset-root "$DATASET_ROOT" --output "$RECOVERY" --smoke-evidence "$PRIOR_SMOKE"
python3 examples/KG_Assoc/campaign/kg_assoc_c1_recovery.py launch \
  --dataset-root "$DATASET_ROOT" --output "$RECOVERY"
```

Those commands launch **no MD**. For the permitted short fresh-stream validation
on the GPU host (only 10000 steps per original parent, never recovery):

```bash
python3 examples/KG_Assoc/campaign/validate_periodic_e2_smoke.py \
  --dataset-root "$DATASET_ROOT" --output "$FRESH_SMOKE" --fresh-md --execute
python3 examples/KG_Assoc/campaign/validate_periodic_e2_smoke.py \
  --dataset-root "$DATASET_ROOT" --output "$FRESH_SMOKE" --verify
```

**Only after explicit recovery execution approval**, create a separate approval
file from `approval.example.json` containing `approved=true`, reviewer/date and
the unchanged plan SHA256. The exact gated sequential launch/validation commands
are provided for later use, not current authorization:

```bash
python3 examples/KG_Assoc/campaign/kg_assoc_c1_recovery.py launch \
  --dataset-root "$DATASET_ROOT" --output "$RECOVERY" \
  --approval "$RECOVERY/approval.json" --fresh-md-smoke "$FRESH_SMOKE" --execute
python3 examples/KG_Assoc/campaign/kg_assoc_c1_recovery.py status \
  --dataset-root "$DATASET_ROOT" --output "$RECOVERY"
python3 examples/KG_Assoc/campaign/kg_assoc_c1_recovery.py verify \
  --dataset-root "$DATASET_ROOT" --output "$RECOVERY"
python3 examples/KG_Assoc/analysis/analyze_c1_recovery.py \
  --dataset-root "$DATASET_ROOT" --attempt "$RECOVERY" \
  --output "$DATASET_ROOT/aggregate/e2/C1_recovery_review_v1"
```

The three underlying commands are `kg_assoc_stars --restart-prefix` each original
`.../r00X/state --steps 2000000 --diagnostic-every 1000 --seed 2200X --md-seed 3200X
--output "$RECOVERY/r00X/state"`. Use the launcher for authenticated execution,
not manual redirects that bypass its safeguards.

## Scientific review protocol

Analyze four corrected windows `(6M,6.5M]`, `(6.5M,7M]`, `(7M,7.5M]`, `(7.5M,8M]`.
Compare against four separately labeled defective windows spanning 4–6M. Each
window duration is **5000 physical time units**. Boundary events belong exactly
once to `(start,end]`; the inherited 6M frame is not an independent new sample.

Outputs include per-replica JSON, windowed observables/events CSV, replica Student-t
comparisons, window comparison plots, reproducible analysis configuration with
hashes and REPORT.md in a new dataset `aggregate/e2/` directory. Old analyses are
never overwritten. Analysis fails on incomplete or changed recovery outputs.

Track bound/free stickers, total/intra/inter bonds, L1/L2, largest component and
distinct degree, accepted creations/ruptures and distinct-neighbor gains/losses,
numerical temperature and permanent-bond extrema. Neighbor gains/losses are
zero-to-one/one-to-zero molecular edge transitions, not individual parallel bonds.
Population-normalized activity uses exact free-sticker-time/active-bond-time
integrals between accepted events, not final populations or diagnostic-frame
averages. Creation events per free-sticker-time are not candidate acceptance
probabilities; rupture events per active-bond-time are not assumed universal
lifetimes. Candidate-attempt/rejection denominators are not recorded.

Use 1000-step (10-time-unit) activity bins and diagnostic sampling. Reuse the
validated first-nonpositive-lag IAT estimator, ten contiguous block means/window,
and 5/10/20-block SEM sensitivity. Flag IAT approaching window scale. IAT-derived
SEMs assume local stationarity and can underestimate slow unresolved drift; do
not use them as automatic pass/fail thresholds. Independent units are three
histories; Student-t comparisons use df=2. Report paired last-minus-previous
window differences across histories and last-corrected-minus-defective-baseline
differences without interpreting the defective baseline as an equilibrium target.

Acceptance requires numerical validity/completeness, no unresolved late trends
at available correlation-aware resolution, compatible independent histories and
joint consistency of chemical/topological observables and activity. No arbitrary
universal percent threshold is imposed. Broad uncertainty, strong block-size
dependence, long correlations, continuing drift or replica disagreement require
scientific review and possibly a separately authorized longer recovery. Neither
2M steps nor stable total bond count alone guarantees corrected equilibrium.
Constant observables in a short window do not establish mixing. Pressure and
candidate-rejection diagnostics are unavailable in the current E2 output; no new
estimator or physical model was introduced to fill these gaps.

## Executed evidence and resources

The prior retained GPU smoke was independently revalidated: 100 oracle sweeps
per replica, accepted events 362/405/385, final bonds 1785/1799/1780,
sampled permanent maxima 1.15755/1.16694/1.17022, final temperatures
.984815/.976707/.978654, wall times 20.140/20.147/20.081 seconds.
These test the corrected candidate search, not the new fresh-seed runtime path.

Both changed E2 executables rebuilt with CUDA12.8/GCC11.2. Host regression tests
verify independent seed parsing/effective seed uniqueness; original C1 endpoint
oracle checks and the 31-test offline campaign suite pass, including inherited
reconstruction, wrong MD seed/timestamp rejection, dry-run/approval/nonoverwrite
gates, tamper rejection, immediate failure retention, exact event/exposure windows
and three-history Student-t statistics. The synthetic full analysis pipeline
also verifies byte-identical repeat outputs and nonoverwrite behavior.
No MD was executed in this task.
Fresh-seed GPU validation is pending: NVIDIA driver unavailable here.

Resource estimates are proxies, not new GPU measurements: the old ordinary 6M
run took 1664.55 s (2M scaling ~9.25 min); the oracle-instrumented 10k smoke scales
to ~67 min per 2M (~3.35 h for three sequential runs), with intentionally large
CPU oracle overhead. Ordinary corrected runtime should be measured on the host;
budget up to ~4 h initially, not a guaranteed limit. Retained short output is
~7.74 MB/replica; fixed final mirrors plus expected ~50–80k event rows and 2001
scalar rows suggest ~10–15 MB/replica. Reserve ~30 MB/replica plus ~100 MB for
analyses/provenance (~0.2–0.25 GB total). No full-bead trajectory is added to E2.

All 24 audited E1 final-state hashes and 93 audited E2/historical file hashes
were checked unchanged. `src/*` and `examples/KG/*` remain untouched. Existing
restart-parser ResourceWarnings are nonfatal and were not silenced by unrelated
code changes. Full recovery execution and equilibrium acceptance remain gated.
