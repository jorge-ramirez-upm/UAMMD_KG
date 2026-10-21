# E1 Stage C — end escape and canonical renewal

## Revision and scope

Starting local HEAD and independently queried remote `refs/heads/slip-springs`
both equaled **921b9c238f8dd266774566241b0ae79e41cfbd04**. The working tree was
clean. Development stayed on `slip-springs`, under `examples/slip-springs/`.
The final commit SHA and push result are supplied in the handoff: a commit
cannot contain its own SHA. Recover the report revision with:

```sh
git log -1 --format=%H -- examples/slip-springs/E1_STAGE_C_REPORT.md
```

The current Stage C authorization supersedes historical Stage B restrictions.
Stages A/B, the E1 specification, backbone validation report, project status,
local rules, production source, CPU references and tests were inspected first.
This implements end renewal only. The complete fixed-coordinate jump process
passed the bounded detailed-balance and equilibrium gates below in both
precisions. Brownian timestep accuracy, terminal relaxation, diffusion,
rheology and general dynamical ergodicity are **not** validated.

## Representation and transition

`slip_renewal.cuh` extends the existing serial event processor. Stage B's Spring
slots remain stable identities with current chain/site, previous/next contour
IDs and an anchor. The bead occupancy map and dense anchor buffer remain the
force lookup. Ordinary hopping calls the unchanged Stage B implementation.

An outward proposal picks a chain uniformly among all M chains, then one of its
two ends fairly. Occupancy is checked before unlinking the source; the occupied
source end therefore rejects, without changing or refreshing its anchor. A
vacant destination permits a fresh independent Gaussian anchor centered on its
stored bead position, component variance A2/3. There is **no** energy criterion
or extra Metropolis factor. A representable candidate is generated before any
source mutation. Numeric failure terminates the run, preserving the old spring
rather than resampling or silently rejecting a difficult Gaussian draw.

A permitted transfer validates source links, finds the destination extreme by
scanning its occupancy, unlinks the old slot, and relinks that same ID at the
new end. It clears the old dense entry and writes the new entry and occupancy.
Same-chain opposite-end transfers exclude the source when finding the new
neighbor. Empty chains, singletons, reversed ID order and ordered multi-spring
chains need no alternate representation. No per-chain constant-population
assumption remains in the active Stage C path. Links encode current contour
order; interior hops cannot overtake a spring. Global Z is fixed.

Production checks the full occupancy/slot/link/anchor invariants after every
batch. Scripted fixtures also check after every individual event, including
injected nonfinite candidates and occupied-end rejections. No spring or anchor
array is resized; there are no orphan slots, per-event host transfers, or
independent constraint-release events.

## Scheduling, coupling and RNG

`--end-renewal 0|1` defaults to 0. It becomes active only when Z>0 and NU>0.
Z=0 is the bare backbone, NU=0 is Stage A, and renewal off is Stage B. Existing
stress modes remain prohibited for any active slip-springs.

Every Brownian step computes forces from the current springs, performs the
unchanged Euler–Maruyama update, swaps coordinate buffers, then performs one
sequential batch at those new coordinates. K is Poisson(Z*NU*dt); IDs are
selected uniformly **with replacement** and directions fairly. Coordinates are
fixed within a batch; all later attempts see accepted changes immediately.
A renewed ID can be chosen again. The next Brownian force evaluation uses its
new bead and new anchor. This is Lie splitting, not an exact finite-dt sampler
of the coupled Brownian/jump process.

The existing Poisson, uniform selection, direction and interior Metropolis RNG
sequence is retained at subsequence `(1ULL<<61)|step`. Renewal destinations and
Gaussians use a separate Philox subsequence `(3ULL<<61)|step`, base
6917529027641081856. With the existing step bound 2^61-1, this is the upper half
of domain 1 and is disjoint from bounded Rouse bead/chain IDs in its lower half,
Stage B draws, domains 2 and 3, backbone initialization and Brownian noise.
Each step has its own variable-length stream, not a fixed draw reservation.
Float uses curand_normal4; double uses two curand_normal2_double calls. Gaussian
scaling/addition uses double before storage in the selected coordinate type.

The accepted Stage B guards are reused: finite nonnegative rates,
representable means, mean<=10000, drawn K<=100000, step and counter limits,
unbiased bounded-index draws, and deterministic finite/invariant diagnostics.
Nothing clips attempts or changes rates to meet a budget. Existing failure
snapshots now include active renewal context. A failed batch is fatal, rather
than rolling back earlier successfully completed events or continuing at a
modified rate.

## Independent balance and equilibrium evidence

`slip_renewal_reference.py` is independent of the CUDA mutation algorithm. It
uses immutable site tuples, NumPy RNGs and freshly sorted contour links. The
joint density at fixed bead positions is proportional to the product of
normalized g(a_j|r_sj), with uniform distinct occupied sites after integrating
anchors. Stable labels contribute a constant Z! multiplicity, which cancels
in all balance relations and unordered marginals.

For a vacant end y and occupied end x, the reference checks pointwise:

```text
log pi(X) + log[NU/(4M)] + log g(b|r_y)
  = log pi(Y) + log[NU/(4M)] + log g(a|r_x).
```

The reverse proposal restores the same identity and original anchor. Tests
cover same-chain/cross-chain proposals, both directions and occupied-end null
events. Scripted GPU transfers agree with the independent reference for every
end transfer from all occupancy states of (M,m,Z)=(1,2,1), (1,2,2), (2,2,2),
(3,3,3), where m=N+1. Each case checks anchors, chain/site assignment, full
links, occupancy invariants and actual production force/energy values. An
artificially very high-energy replacement is still accepted at a vacant end,
preventing an erroneous second Metropolis factor. Interior detailed balance
and nonuniform **conditional** occupancy remain covered by the unchanged Stage
B reference/GPU suites; uniform annealed occupancy is not imposed at fixed
anchors.

### Exactly enumerable complete generator

For coincident fixed bead coordinates, all interior energy differences vanish
for every anchor and g is site independent. Only in this explicitly restricted
case is occupancy a closed Markov quotient of the full process. The CPU builds
its generator independently by enumerating unordered occupancy subsets:
interior rates NU/2, renewal channels NU/(4M), with occupied targets omitted
and null events included through the diagonal convention. One-bond chains
correctly have distinct ends and can have both interior and renewal channels
between the same occupancy states; these rates are added.

The 20-state (M=3,m=2,Z=3) and 84-state (M=3,m=3,Z=3) generators have zero row
sums, reversible off-diagonal connections, symmetric rates, uniform stationary
occupancy and the exact hypergeometric chain-population marginal. Multiplying
NU by four multiplies the entire generator by four. GPU complete batches,
started with all three springs on one chain and correct Gaussian anchors,
match `exp(t Q)` over all 84 states at NU=0.5 and 4, t=2, using 8192 independent
replicas per rate. Deterministic replay is byte identical. This is an exact
reduced test, **not** an anchor-averaged Markov approximation for separated
coordinates; the reference rejects such misuse.

### Continuous anchors and separated bead positions

Independent CPU and production GPU complete hopping/renewal processes were
also tested at separated, fixed bead coordinates, M=3,m=3,Z=3,A2=2.4. Each
replica starts from the exact fully annealed distribution (uniform distinct
sites, conditional independent Gaussian anchors). This tests preservation of
the target measure, not convergence from arbitrary initial anchors.

The GPU uses 8192 independent replicas, eight batches of dt=0.25, at each of
NU=0.5 and 4. The CPU independently uses 4096 replicas over t=2 per rate.
Preset bounds are six standard errors: binomial site/population probabilities,
and independent-replica cluster errors for connector means and renewal counts.
Springs within one replica are not treated as independent uncertainty samples.
The exact population targets for z=0,1,2,3 are (20,45,18,1)/84, from
C(m,z) C((M-1)m,Z-z)/C(Mm,Z); every site has probability 1/3.

| GPU precision | NU | Observed P(Z_c=0,1,2,3) | Mean connector squared | Mean accepted renewals |
|---|---:|---|---:|---:|
| double | 0.5 | .238770, .531006, .217163, .013062 | 2.395824 | .620728 |
| double | 4 | .234497, .536621, .218018, .010864 | 2.413467 | 5.002686 |
| single | 0.5 | .237671, .533691, .215820, .012817 | 2.393507 | .619141 |
| single | 4 | .237061, .538208, .212646, .012085 | 2.402672 | 5.003418 |

All population, all-site occupancy and connector gates passed. Chain
populations actually change, while each replica conserves exactly three
springs. CPU connector means were 2.42769 and 2.43579; its corresponding
population/occupancy/connector gates also passed. The accepted-renewal target is

```text
E[K] * (1/m) * ((2M-1)/(2M)) * ((Mm-Z)/(Mm-1)),
```

namely .625 and 5 in these cases. This includes rejection of the occupied
source. Measured Poisson attempt means and all event-counter identities passed.
Kinetic changes agree with both this event-count prediction and the independent
finite-generator transient test; both rates preserve the equilibrium target.
This says nothing about terminal polymer timescale independence from NU.

A separate 16384-proposal production RNG test samples destination chains/ends
and new anchors without subsequent hopping. Of these, 13665 selected vacant
ends; occupied choices left the old state unchanged. Each component mean,
variance and cross moment passed the preset Gaussian bounds. Mean squared new
connector was 2.386296 (double), 2.439312 (single), target 2.4.

## Regression and environment results

Tested on 21 October 2026, NVIDIA GeForce RTX 3060 Ti sm_86, driver 580.178.04,
CUDA 13.0.88, g++ 11.4. GPU execution and host leak sanitizers required running
outside this environment's sandbox; those checks actually executed.

| Check | Actual result |
|---|---|
| Stage C CPU suite | 4/4 passed |
| Stage C GPU/simulator suite | 6/6 passed per precision |
| Stage A initialization and force fixtures; simulator suite | Passed both precisions; 4/4 Python tests each |
| Stage B limits, CPU reference and GPU/simulator suite | Passed; CPU 4/4, GPU 8/8 each precision |
| Bare semiflexible force/energy/initializer suite | 7/7 each precision; includes finite-difference checks |
| Backbone independent CPU reference and host tools | 12/12 and 2/2 |
| Semiflexible stress/correlator regression | 7/7 each precision |
| Original Rouse `make check` | Passed both precisions, including smoke, force/RNG, pipeline, CLI, stress and theory checks |
| Host workers/lifetime ASan, UBSan and leak checks | Passed, leak detection enabled |
| Stage C fixture CUDA memcheck/racecheck/initcheck/synccheck | Passed both precisions; zero errors/hazards |
| Short active Stage C simulator CUDA memcheck/racecheck | Passed both precisions; zero errors/hazards |
| Rebuilt accepted Stage B comparison | 44 comparisons passed; see below |
| Historical frozen campaign suite | 12/13 passed; one source-identity authentication error |
| Historical scalar-profile suite | 6/7 passed; one source-identity authentication error |
| Default CUDA 11.5 compilation attempt | Failed in libstdc++11 `std_function.h`: parameter packs not expanded; preserved known limitation |

The historical suites reject `accepted source identity changed:
semiflexible.cu`. These are provenance failures against their frozen source
allowlist, **not** failed equilibrium gates. No allowlist, frozen plan,
scientific threshold, historical binary or analyzer was changed. Full/compact
functional tests passed independently of that authentication error.

Starting Stage B source was reconstructed with `git show` and rebuilt with
CUDA 13 against unchanged Stage B headers, separately for both precisions.
For N3,C4,kBT1.7,dt0.0001,5 steps,stride1,seed4317,kappa0/2,Z0/3 and NU0/10000,
default/explicit renewal-off outputs, plus renewal-on inactive limits, matched
all coordinate, scalar, parameter, bond, anchor/spring CSVs, hopping sidecars
and non-timing metadata byte for byte. Timing fields were excluded explicitly.
44 comparisons passed. This is additional to new-binary disabled-path tests.
Programmatic Stage 0 base comparison, untracked and ignored-path checks found
all changed/generated repository paths under `examples/slip-springs/`. The
protected backbone, force, RNG, Stage B kernel/reference, stress and frozen
source-authentication files were byte-identical to the starting revision.

Successful-replay, same-chain/opposite-end, cross-chain, empty insertion,
last-spring removal, either contour extreme, repeated-ID sequential events,
one-bond occupancy, high-energy acceptance, rejection without reanchoring and
transactional nonfinite-candidate tests passed. Force relocation was checked
both directly and through paired two-step Brownian simulator runs: the first
coordinate update is identical before the jump; the second coordinate
difference equals mobility*dt times the spring-force difference from the two
updated snapshots, within precision tolerance. Backbone noise stays isolated.

Logs and examples are in ignored `build/e1-stage-c/`: `check-{single,double}.log`,
`regression-{single,double}.log`, `rouse-{single,double}.log`, `backbone-*.log`,
`sanitizers.log`, `stage-b-compatibility.log`, `campaign.log`, `scalar.log`,
`cuda115.log` and `short-{single,double}/`. These are local execution evidence,
not a committed scientific trajectory archive. All tests and fixtures needed
to reproduce the acceptance are committed.

## Metadata, cost and numerical limits

Disabled Stage C preserves Stage B version 1 sidecars. Active Stage C writes
`hopping_metadata.json` version 2 and main `slip_mode=canonical-renewal-development`.
In version 2, `accepted`, `occupied_rejected`, `metropolis_rejected` refer to
interior hops; `outward_proposals` replaces `boundary_rejected` and includes
all attempted renewals. The additional counters satisfy:

```text
attempts = accepted + occupied_rejected + metropolis_rejected + outward_proposals
outward_proposals = renewal_proposed = renewal_accepted + renewal_occupied_rejected
renewal_accepted = renewal_same_chain + renewal_cross_chain
```

The sidecar records the renewal RNG base, component variance and
`renewal_device_bytes`. Existing `device_bytes` there continues to count Stage
B hopping arrays/statistics; add `renewal_device_bytes` for the combined jump
state. The main metadata's device total and workspace estimate include both.
Initial/final spring CSVs retain stable IDs with current chain/bead and anchor;
`fixed_slip_springs.csv` is still only the initial snapshot.

Stage C adds five uint64 counters (40 explicitly allocated device bytes) when
active, no additional per-bead or per-spring array, and a per-thread temporary
Philox state. Compiler local/register storage is not measured by that 40-byte
figure. Memory remains O(total beads + Z), independent of steps. A vacant-end
transfer scans at most m beads to find the destination contour extreme; global
serial event processing remains the dominant scaling constraint. Diagnostic
readback remains the Stage B one-integer check per batch, not per event.

The N8,C64,Z32,A2=5,NU100,dt0.0001,100-step short example ran in both precisions:
36 attempts, 8 accepted cross-chain renewals each. Explicit total device bytes
were 40384 single and 77860 double. Single measured integration/overall costs
were 79.827/127.798 ns/bead/step; double 164.658/214.289. These tiny concurrent
verification runs are functional timer evidence, **not** a performance benchmark
or comparison of precisions. No scaling campaign or optimization was performed.

Floating-point storage and rounded stiffness inherit Stage A/B precision
limits; Gaussian sampling and ideal detailed balance are not claims of exact
finite-bit equality of continuous densities. Very large coordinates can lose
small connector displacements; overflow aborts rather than biasing renewal.
Finite-dt Brownian integration/splitting still needs separate accuracy work.
Frozen-coordinate preservation and reduced-generator transients do not prove
arbitrary-initial-state mixing of the coupled polymer model. In particular,
Z=all sites has no vacant destination and cannot refresh anchors by this kernel;
a general ergodicity claim would be false. No new timestep, physical hopping
rate, terminal diffusion or rheology result has been accepted.

## Reproducible bounded commands

Run from the repository root with Python/NumPy, g++ and CUDA 13; choose the
appropriate architecture and a new output root. No campaign command is run.

```sh
C_BUILD="$PWD/examples/slip-springs/build/e1-stage-c"
make -C examples/slip-springs check-slip-renewal-cpu
make -C examples/slip-springs check-slip-renewal PRECISION=single CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 GPU_BUILD="$C_BUILD/single"
make -C examples/slip-springs check-slip-renewal PRECISION=double CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 GPU_BUILD="$C_BUILD/double"
make -C examples/slip-springs check-fixed-slip-springs check-slip-hopping check-semiflexible-stress PRECISION=double CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 GPU_BUILD="$C_BUILD/double"
make -C examples/slip-springs check check-lifetime PRECISION=double CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 GPU_BUILD="$C_BUILD/double"
SAN_OUT=$(mktemp /tmp/e1-c-sanitizer.XXXXXX)
/usr/local/cuda/bin/compute-sanitizer --tool memcheck --error-exitcode 99 "$C_BUILD/double/slip_renewal_gpu" examples/slip-springs/tests/slip_renewal_sanitizer.txt "$SAN_OUT"
```

Repeat regression commands with PRECISION=single and its GPU_BUILD. The
sanitizer fixture also supports `--tool racecheck`, `initcheck`, `synccheck`,
and both fixture binaries. Existing stress, source authentication and
CPU-reference tests retain their original commands and strict checks.

Short example, executed in both precisions (use the single binary for float):

```sh
C_RUNS=$(mktemp -d /tmp/e1-stage-c.XXXXXX)
"$C_BUILD/double/semiflexible" --springs 8 --chains 64 --kappa 2 --dt .0001 --steps 100 --sample 10 --seed 4317 --slip-count 32 --slip-ms2 5 --hop-rate 100 --end-renewal 1 --stress-mode off --output "$C_RUNS/short"
```

A moderately long, **unexecuted host-only** development example, not a scientific
campaign or timestep acceptance:

```sh
"$C_BUILD/double/semiflexible" --springs 8 --chains 64 --kappa 2 --dt .0001 --steps 10000 --sample 100 --seed 4317 --slip-count 32 --slip-ms2 5 --hop-rate 100 --end-renewal 1 --stress-mode off --output "$C_RUNS/moderate"
```
