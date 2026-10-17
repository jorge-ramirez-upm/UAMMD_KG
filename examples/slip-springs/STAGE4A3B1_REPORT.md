# Stage 4A.3b.1 — host-validation readiness

Starting SHA, verified clean and equal to fetched origin/slip-springs:
`b47d2876d2380b9f4caace05f6fe193a6f49e3cb`.
Stage 4A.3b is accepted by the user. This readiness work adds host analysis,
execution management, bounded fixtures and documentation only. **No frozen
campaign member, production experiment, large CPU ensemble or slip-spring work
was executed.** Stress-relaxation scientific acceptance remains outstanding.

The original generator, its 282 scientific commands, accepted references,
simulator/forces/RNG, correlators, build behavior, old tests and evidence remain
unchanged. The original Stage4A.3c plan SHA-256 remains:
`efd040ceba8cd903dee7a145296dce08435e3df3efa940c65170f4bcf98acb36`.

## Files and scientific gates

New `tests/semiflexible_stress_analysis.py` supplies independent scientific
checks and bounded parsers. New `tests/semiflexible_stress_campaign.py` manages
authentication, analysis checkpoints, host execution receipts and monitoring.
New `tests/test_semiflexible_stress_campaign.py` exercises them. Documentation
changes are this report, README.md, ROADMAP.md, AGENTS.md and the separately
versioned clarification proposal linked below. No Makefile change is needed.

Authentication reconstructs the unchanged generator in a temporary directory
and compares all 282 ordered commands, parameter inputs and scripts exactly,
allowing only the generator's campaign/build paths. Plan copies and PLAN_SHA256
must match the pinned original hash. Accepted generator/reference/simulator
source hashes are pinned independently: changing the generator together with a
manifest cannot silently redefine the campaign. Run IDs are SHA-256 of canonical
scientific commands with campaign/build path placeholders; manifest authentication
also retains the exact path-bound manifest hash. No relocation is silently accepted.

Checks implemented:

* Raw nine-entry stretching, bending and total GPU tensors versus the independent
  CPU virial, separately; exact chain/term IDs, saved coefficient indexing,
  symmetry, bending trace, finite values and total assembly. Frozen float
  absolute2e-7*S/relative3e-6 and double absolute5e-13*S/relative3e-12 remain;
  symmetry1e-11*S and trace3e-11*S, S=max(1,kb,kappa).
* Initial independent-chain stretching mean N*kBT*I, bending mean zero, total
  deviatoric means zero; final-half means with independent-chain SE. Raw
  equal-time products and static covariances are compared to independently
  sampled CPU ensembles of exactly65536 chains/model/temperature. References
  are generated only by an explicit user-host command, in coordinate chunks128,
  with recorded deterministic analysis seeds starting433301. Static covariance
  is unbiased sample covariance; its SE is the exact leave-one-chain-out
  jackknife, checked against explicit delete-one calculations. Raw correlator
  products remain uncentered. Final-half products are retained as chain-level
  means and used for timestep/replica comparisons, not trajectory-mean subtraction.
* Exact Gaussian finite-acquisition EM theory, including recorded precision-rounded
  mobility/noise, continuous-equilibrium initial variances, each origin's two-time
  covariance squared, and products of nonoverlapping block means. Stable geometric
  sums reuse only the accepted numerical helper. Independent explicit mode/time
  loops validate the new formula. All exported Gaussian bins are checked against
  raw six-channel/H predictions and dimensionless g, using the unchanged six-SE,
  1% and0.002*N*(kBT)^2 raw-scale gates. No Gaussian spectrum is assigned to
  finite-rest-length nonlinear models.
* Every saved direct-reference bin is compared to independent block means and
  direct products, all six channel means/SE and paired H/SE. Exact lag grids,
  origin counts and truncation preserve the omitted deepest populated level.
  Direct tolerances remain absolute3e-11+relative3e-11; thermal/density factors
  relative2e-14. Worker1/2/4,batch1/7/32 files must be byte-identical. Total stress
  retains stretch/bend cross terms. Main long streams do not save raw stress
  histories; their bins/counts/normalizations are authenticated, while independent
  direct recalculation applies to the frozen 54 reference runs, as gate4 specifies.
* Finest/middle means, products and resolved correlations, three-seed comparisons
  before pooling, and coarse-error reduction against available independent
  static/Gaussian references. Six combined chain SE and frozen 1% scales apply.
  Unresolved coarse bias has its own `statistically_unresolved_bias` status,
  never a measured convergence order. No independent nonlinear dynamical reference
  is fabricated. All Gaussian exported bins are tested; nonlinear comparison bins
  are called resolved when either estimate exceeds six of its chain SE in magnitude.
* First H(0)/e crossing and pointwise +/-6SE crossing bounds. Terminal checks
  report the nearest supported exported bin to2*tau_e, its offset, positive
  signal >3SE, a supported bin beyond4*tau_e, the0.1+6SE/H(0) tail criterion,
  >=16 origins and block time<=tau_e/4. Missing crossing/band/origin/time support
  is `insufficient_support`, never pass. No fitted lifetime, tail or viscosity.
* Frozen short/long repeated memory comparisons, production-scoped RSS/GPU
  monitoring, capacities/estimates and separate timing scopes. The frozen
  max(16MiB,5%) allowance is unchanged. Three or more observed monotone points
  provide growth evidence; large oscillations without a resolved monotone trend
  remain insufficient rather than being mislabeled a plateau. GPU records are
  whole-device measurements, not process allocations. Initialization is excluded
  by the production-observed flag, without discarding physical observations.

The plan leaves a few operational words unspecified. The separately versioned
[STAGE4A3C_CLARIFICATION_PROPOSAL_V1.md](STAGE4A3C_CLARIFICATION_PROPOSAL_V1.md)
records these interpretations and proposes clarifications for review. It is
**not applied as an amendment** and does not replace the frozen criteria.

## Fail-closed inputs, uncertainty and outputs

CSV schemas, frame/chain/bead/angle/term identities, metadata dimensions, seed,
precision, temperature, timestep/stride, rounded update coefficients, parameter
arrays, launch/capacity counters, final snapshots, initial bonds, histograms,
final-half counts and complete correlation grids are checked. Failure records,
nonfinite values, malformed rows, missing/duplicate IDs, missing bins/origins,
wrong normalization and inconsistent timing/memory estimates cannot pass.
Exact Linux64 bank-size accounting is checked (296-byte owning object plus the
accepted allocation formula); unsupported ABI changes require reviewed tooling.

Independent chains, not time origins, are the uncertainty clusters. The full
report records observed/reference values, SE, allowances and excesses, as well
as per-run metadata, terminal support and timing. `scientific-analysis.json`
contains the machine-readable result; `readiness-refusal.json` records the
latest refused command without replacing prior scientific analysis; `scientific-summary.txt` is concise and
points to full details. `failed` may mean invalid/corrupted evidence rather than
a physical model being disproved. Missing files and missing provenance are
separate statuses. Scientific-gate status and overall/provenance readiness are
reported separately. Overall exit0 requires complete passing evidence; exit1
means failure/refusal and exit2 means incomplete/support/provenance outstanding.

Compiler identity is never inferred from system nvcc or a no-op build. A supplied
original build transcript is archived and hashed but still requires provenance
review. Without one, missing compiler provenance remains explicit. Execution
receipts identify exact commands, exit codes, repository SHA, both executable
hashes, UTC timestamps, wall time and relevant environment. Current binaries,
when available, must agree with recorded identities. Original unavailable
evidence is not invented. Bounded prerequisite logs link prescribed geometry,
replay/isolation and unit/nonunit-temperature tests to both executable hashes.

Long scalar CSVs and monitoring records are parsed row-by-row with bounded
memory. Direct-reference samples have a32MiB cap (the frozen8193x64x6 sequence
uses~24MiB); only these explicitly short sequences are held. CPU ensemble
coordinates are chunked, retaining six channels per reference chain. Reports
scale with the fixed282 experiments and exported bins, not MD duration.
First analysis additionally streams SHA-256 over completed files; it can take
substantial time on large CSVs and belongs on the host, not Codex.

## Checkpointing and execution management

Checkpoints/references/receipts use canonical JSON with SHA-256 envelopes and
fsync+atomic rename. Their manifest, plan and analysis/reference source-version
identities are strict. Per-run checkpoints commit after each completed analysis.
An unchanged authenticated result skips expensive CSV parsing; size, inode,
mtime/ctime and file inventory are checked. `--verify-hashes` requests full
content rechecking. Version changes force science reanalysis; corrupt checkpoints
are refused. This is integrity verification, not a cryptographic signature or
protection against a malicious actor rewriting every proof.

Execution is serial (at most one requested GPU process). A separate execution
lock prevents overlapping runners; the analysis lock permits completed runs to
be analyzed while execution continues. Running/absent outputs are marked pending
and their large files are not scanned. Completed runs skip only after verifying
the original receipt and file identities; optional deep hashes are available.
Partial outputs, orphan monitoring files, failed receipts and identity changes
are preserved and refused, never overwritten or automatically retried. An
execution/numerical failure stops the phase. Interrupted process groups are
terminated and recorded failed. This resumes between complete experiments;
it does not restart an interrupted trajectory.

The runner passes the original argv unchanged through /usr/bin/time, records
process-tree RSS, nvidia-smi whole-device observations, scalar/output disk growth,
stdout and execution receipts. Relevant environment and system-tool versions
are recorded separately from original compiler provenance. All monitoring uses
actual timestamps; subset/overlapping timers are never added as wall time.
Three-repeat memory timing means/spreads are included in the campaign report.
No stress sampling rate changes. Monitoring itself has a measurable host cost.

## Bounded verification actually run

13 unittest groups passed in under2s; final verification is recorded in the
completion handoff. The unchanged CPU force/equilibrium and stress suites
also passed (12+11 tests). Four GPU fixtures use
N8,C32,kappa10,kBT1.7 in both precisions: zero-step diagnostics and39-step
streams,stride2,batch7. These are not frozen campaign members. No long reference
ensemble or memory benchmark ran. Original binaries were used without rebuild.

Coverage includes constructed passing/failing equilibrium, timestep, replica,
terminal and memory gates; explicit Gaussian mode/time sums; jackknife covariance
SE; corruption of frames, IDs, timestep, parameters, plan hash, normal-channel
factors, g normalization, bending trace, bins/origins, final-half support and
performance fields; missing final output; incomplete execution; provenance
mismatch; corrupted checkpoint; no-execution guard; cached reuse/invalidation;
and running-output avoidance. Fake execution-failure fixtures mock subprocesses,
not scientific runs. Fresh generation/listing and analysis of an unexecuted pilot
were also tested: the analyzer correctly returned INCOMPLETE/exit2.

No inherited regression was changed or threshold weakened. Static checks verify
all old simulator/reference/test/build/plan/archive bytes remain unchanged.
The source change boundary is exclusively examples/slip-springs/.

## Reproducible commands and pilot selection

Run bounded readiness tests using the existing built binaries:

```sh
timeout 180s python3 examples/slip-springs/tests/test_semiflexible_stress_campaign.py examples/slip-springs/build/single/semiflexible examples/slip-springs/build/double/semiflexible
```

Preparation only (tested; no experiment is launched):

```sh
HOST_ROOT=$(mktemp -d /tmp/semiflexible-readiness.XXXXXX)
python3 examples/slip-springs/tests/semiflexible_stress_host.py --output "$HOST_ROOT/campaign"
python3 examples/slip-springs/tests/semiflexible_stress_campaign.py "$HOST_ROOT/campaign" list --pilot
```

The unchanged main pilot is single-N8,kappa10,seed433201,dt0.000025,
8,000,000 steps,stride400,C2048,kBT1:20,001 frames and40,962,048 scalar rows.
Its run ID is `231844aeb5842990bdde4e3be65ccdbe5e8701a1c6314464824777895cc62427`.
Matching zero-step diagnostic ID:
`41ef4bc05565a5f90b66996738796494a14cb5af3ea9c8322f3953929fb8dd96`.
No runtime or disk number is inferred from tiny tests. After the actual full
pilot, pilot-report measures elapsed time, disk growth, memory allocations and
separate costs; it estimates same-N8/kappa10/single production time using measured
integration/step and remaining production/frame costs. Scalar disk estimates
apply measured pilot bytes/row to manifest row counts, with explicit format/
model uncertainty and extra reserve. These are planning estimates, not benchmarks.

ONLY after separate user authorization, on the dedicated Linux host:

```sh
# Preserve the original compilation transcript if available; no-op output is not proof.
python3 examples/slip-springs/tests/semiflexible_stress_campaign.py "$HOST_ROOT/campaign" prerequisites --authorize-host-execution STAGE4A3C
python3 examples/slip-springs/tests/semiflexible_stress_campaign.py "$HOST_ROOT/campaign" run --pilot --phase diagnostic --authorize-host-execution STAGE4A3C
python3 examples/slip-springs/tests/semiflexible_stress_campaign.py "$HOST_ROOT/campaign" run --pilot --authorize-host-execution STAGE4A3C
python3 examples/slip-springs/tests/semiflexible_stress_campaign.py "$HOST_ROOT/campaign" pilot-report
python3 examples/slip-springs/tests/semiflexible_stress_campaign.py "$HOST_ROOT/campaign" analyze --pilot
```

For the eventual separately authorized campaign, `run --phase diagnostic`,
`run --phase reference`, `run --phase stream`, `run --phase memory` use the
same explicit execution flag and skip verified completions. `references` with
that flag prepares the fixed65536-chain CPU ensembles resumably. `analyze`
without selection processes the full manifest incrementally; rerun to resume,
optionally `--verify-hashes`. The execution flag is an acknowledgement, not
permission supplied by this task. No Stage4A.3c execution or Stage4B is authorized.
