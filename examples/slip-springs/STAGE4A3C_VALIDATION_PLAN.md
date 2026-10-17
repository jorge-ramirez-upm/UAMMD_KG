# Stage 4A.3c frozen scientific host-validation plan (not execution authorization)

Frozen 17 October 2026 before any long stress experiment. Stage 4A.3b must first
receive independent review; scientific host execution requires separate user
authorization. Do not revise gates after viewing campaign results. Archive a
new plan/version for any extension. No slip-springs or new interactions.

## Campaign and provenance

Generate with `tests/semiflexible_stress_host.py --output NEW_DIR`. It only
writes inputs/manifests/commands; it has no simulation execution option. Commands
are split into diagnostics and streaming phases and require an explicit reviewed
host-execution environment flag. Record Git SHA, hashes of BOTH executables,
compiler build transcript (a no-op build does not prove the toolkit), GPU/driver,
NumPy, physical parameters, metadata, and this plan's SHA-256. Use independent
seeds **433201,433202,433203** in both single and double precision.

Uniform kBT=1,zeta=1 unless specified. N bonds imply N+1 beads. Configurations:

| Label | N | b0 | kb | kappa | Chains | Physical duration |
| --- | ---: | --- | --- | --- | ---: | ---: |
| single-bond | 1 | 1 | 30 | 0 | 2048 | 20 |
| finite-N8-k0/k2/k10 | 8 | 1 | 30 | 0/2/10 | 2048 | 200 |
| finite-N32-k0/k2/k10 | 32 | 1 | 30 | 0/2/10 | 2048 | 4000 |
| heterogeneous | 8 | alternating 0.8/1.2 | alternating 20/40 | [0,0,2,0,10,0,2,0,0] | 2048 | 200 |
| gaussian-control | 8 | 0 | 3 | 0 | 2048 | 100 |

For finite-rest-length cases use dt=0.0001,0.00005,0.000025 and physical stress
sample spacing **0.01** (stride100,200,400). For the Gaussian control use
dt=0.001,0.0005,0.00025 and spacing **0.002** (stride2,4,8). Never lower the
sampling frequency for a performance comparison. Stream raw complete virials,
workers=4,batch32,levels20,slots32,coarsening2,correlator budget512 MiB. Density
is unspecified. Automatic initialization is the exact radial/conditional
orientation ensemble; no artificial burn-in. Each stream starts with step0.
There are **162 main stream experiments**, **54 direct-reference stream runs**,
**12 timed memory runs**, plus **54 zero-step tensor diagnostics**
(one per model/seed/precision at the finest dt). Preserve originals.

Durations are coverage choices, not asserted nonlinear relaxation times. Stage
2B supplies a controlled discrete Gaussian reference; Stage 4A.2 supplies
stability/static evidence for these finite-rest-length parameters, not a stress
spectrum. Gaussian N8 has continuous stress tau=1/[24*sin(pi/18)^2]~1.382,
so duration100 covers >70 such times. A rigid straight M-bead chain with length
spacing l has rank-two rotational estimate tau_rot=zeta*l^2*M*(M^2-1)/(72*kBT).
With M=33,l~1.065 this is ~565, making duration4000 a plausible initial coverage
choice; a flexible nonlinear chain is NOT assigned this spectrum or guaranteed
that terminal support. N8 duration200 exceeds the analogous rod estimate by
more than an order of magnitude. Failure to meet the terminal gates requires
reviewed extra coverage; it must not be relabeled acceptance. This campaign is
expensive (up to 160 million integration steps per long run, potentially hours per run).
It must not run in Codex. Check disk capacity for legacy scalar observations.

## Gates established before execution

1. **Diagnostic tensors:** compare stretching,bending,total independently with
   `semiflexible_stress_reference.py` on precision-rounded initial coordinates
   and saved parameters. Float absolute tolerance 2e-7*S and relative3e-6;
   double absolute5e-13*S and relative3e-12; S=max(1,max kb,max kappa).
   Raw tensor symmetry absolute1e-11*S and bending trace3e-11*S. No symmetry or
   trace repair before comparison. Include the bounded prescribed-geometry
   suite with N1/N2, rotations/translations, near-collinearity, zero-rest-length,
   inactive/active collapse and kBT=1.7 before campaign execution.
2. **No numerical/structural failure:** all exit statuses zero, finite tensors
   and channels, no stress/force failure records, zero missing sample frames.
   Expected frames=floor(steps/stride)+1. For zero active bending require force
   and stress angular capacity/launches all zero; active cases must execute
   bending. No RNG or coordinate/force mutation. Repeat bounded replay and
   chain-isolation tests. Both precision stress implementations must pass.
3. **Static stress moments:** initial independent tensor diagnostics require
   <W_s>=N*kBT*I,<W_b>=0 and zero shear/raw normal-difference means. Finest-dt
   streaming requires zero mean total shear/raw normal differences: six independent-chain
   SE plus absolute1e-6*max(1,N*kBT). For time averages use the final half of
   observations and per-chain clusters; no overlapping origins count as chains.
   stress_moments.csv retains final-half per-chain means/raw products with
   explicit frame counts; require at least two selected frames. Correlations
   themselves use ALL frames. Do not relabel these as independent origins. Validate all six-channel
   equal-time raw products/covariances against an independent CPU equilibrium
   ensemble of 65536 chains per model,T. Compare initial diagnostic stress
   channels (three independent seeds) within six combined chain SE +1% of the
   geometric-mean diagonal product scale (absolute1e-6 floor). CPU reference
   sampling and tensor calculation occur on the user host only at this size.
   Hydrostatic stress is not zero. Stretch/bend cross-products are retained.
4. **Direct/multi-tau correctness:** run all bounded synthetic/direct tests.
   For separate reference runs of the same models, C=64,8193 frames, retain
   six-channel samples with --stress-dump1, fixed stride and identical dt. This
   gives incomplete terminal batches/coarse blocks. Independently form complete
   nonoverlapping block means at every exported block width and direct products.
   All six means and paired H/SE must agree with streaming within absolute3e-11
   plus relative3e-11. Match pair counts exactly and lags within1e-12*max(1,lag).
   Repeat workers1/2/4 and batch1/7/32: correlation files must be byte-identical.
   Test a unit-temperature and nonunit-temperature subset (kBT=1.7), and explicit
   n_chain=0.25. Require g=H/(kBT)^2 and G=n_chain*H/kBT within relative2e-14.
   This is an estimator check, not approximate agreement with a nonlinear theory.
5. **Controlled Gaussian dynamics:** raw shear covariance for b0=0,kb3,kappa0
   must match the discrete EM mode covariance including transient variance from
   continuous equilibrium initialization and the two-time covariance at EACH
   origin. Use effective_mobility_step and effective_noise from metadata:
   a_p=1-effective_mobility_step*lambda_p, v_p(0)=kBT/lambda_p, and
   v_p(n+1)=a_p^2*v_p(n)+effective_noise^2. The two-time mode covariance is
   a_p^|n-m|*v_p(min(n,m)); raw shear covariance sums lambda_p^2 times its
   square. This includes precision rounding of BOTH drift and noise scales. Square each origin covariance BEFORE averaging; coarse bins use
   products of block-averaged stress, not a point-sampled curve. kBT arbitrary
   enters twice in raw covariance. Each resolved bin requires six chain SE +1%
   of its predicted value (absolute floor0.002*N*(kBT)^2). Do not apply this
   reference to finite-rest-length chains. Preserve the Stage 2B block/finite-step
   definitions and distinguish continuous theory from finite-step prediction.
6. **Finite-step/static bias and replicas:** finest vs middle means, zero-lag
   stress covariances and resolved correlation bins agree within six combined
   SE +1% of the corresponding zero-lag diagonal scale. If coarse error against
   an independent reference exceeds6SE, require a >=25% reduction by the finest
   step allowing6 combined SE. Unresolved bias is reported as unresolved; no
   convergence order is inferred. Compare independent seeds before combining.
   In nonlinear cases, refinement is a consistency gate, not an analytical
   Gaussian-spectrum comparison. Keep all existing acceptance gates unchanged.
7. **Terminal support (nonlinear cases):** define operational tau_e from the
   first crossing of H(0)/e, with crossing bounds from pointwise mean +/-6SE;
   do not claim a fitted mode lifetime. Require resolved positive H at a lag
   near2*tau_e (>3 chain SE), and a supported bin beyond4*tau_e where
   |H|/H(0)<=0.1+6*SE/H(0). At those lags require >=16 origins per chain and
   block width<=tau_e/4. Frame means are not independent origins. Report
   crossings/support individually for every model/replica/precision; unresolved
   crossings or insufficient duration fail terminal coverage and require a
   separately reviewed extension. This does not justify assigning a nonlinear
   chain the Rouse spectrum. No tail fit or viscosity extrapolation is authorized.
8. **Memory/performance:** compare N8,C2048,kappa10,dt0.00005,stride200,seed433201
   for steps20000 and400000, with fixed worker/batch/correlator configuration.
   Archive /usr/bin/time -v, nvidia-smi whole-device monitoring and metadata.
   After warm-up, no sustained monotone resident/device growth beyond max(16MiB,
   5% of plateau) is allowed. RSS noise is not interpreted as physical growth.
   GPU device-capacity and correlator/buffer estimates must match run settings
   and be independent of step count; scalar output growth is explicitly allowed.
   Record initialization,integration,stress GPU,D2H,diagnostic wait,CPU pool wall,
   barrier,worker-time sum,finalization/output and overall production separately.
   Overlapping/subset timers must not be added as independent elapsed times.
   Repeat memory/timing measurements three times in each precision; report mean/spread without
   claiming a production-server optimum or speed superiority over UAMMD.

## Statistical estimator and acceptance boundary

Independent chains are clusters. Compute six-channel products within each
chain, assemble H with 1/5 and1/30, THEN estimate mean/SE across chains. Means
are raw ensemble products; no finite-trajectory mean subtraction is introduced.
Finite-sample trajectory means may differ from zero and do not justify a new
connected estimator. The validated KG sentinel boundary, nonoverlapping block
means, truncated incomplete coarse blocks and deepest-level export omission
remain unchanged and must be disclosed. Full input frames are still consumed.

The generator's diagnostics can be checked by --check-diagnostics. It does not
implement all scientific acceptance analysis above; an independently reviewed
host report must cover static ensembles, exact Gaussian finite-step predictions,
terminal support, memory, replication and provenance. Do not declare acceptance
from exit status, bounded tests or diagnostic comparisons alone. Archive compact
manifest, metadata, direct/statistical reports and hashes; retain large scalar
files outside Git. Stage 4A.3c simulation and Stage 4B are not authorized here.
