# N=40 continuous 8M assessment: authentication and method

Starting local and remote `KremerGrest` both authenticated as
`0d947d7c17e8e9e7b48e726a50206d5b041e2287`.
Source plan SHA256:
`c8d624d6205f3b5eeb926b66fa9f992a446e9d53b4840cc88c8240406b99044c`.

The unchanged `analyze_joint_e2.authenticate()` and numerical/event/network/
conformation validators independently replay all three histories. Plan/approval,
frozen E1 inventory, active E1 selections, E1 snapshots/completion/diagnostics,
particle/sticker identities, physics, chemistry/MD/effective MD seeds, build source
and log hashes, current executable bytes, completion receipts and all eight output
payloads authenticate. Accepted event journals reconstruct reciprocal partners,
neighbor exchange, graph motifs and connectivity; final associations match restart
sidecars. Numerical and conformation endpoint checks pass. The original E1
completion records preserve historical code/executable identifiers; this assessment
authenticates their frozen states and records, not a rerun of E1 or reauthentication
of historical E1 executable bytes. Current E2 executable bytes are available and
hash-identical to the plan-bound build; the historical unavailable-binary limitation
of some other systems does not apply to this E2 attempt.

These are three initially unbound, continuous absolute 0–8M histories. There are
8001 scalar diagnostic samples per history, at steps 0,1000,...,8000000. There is
no E2 extension, intermediate restart or MD reseed at 2M, 4M or 6M. These are
analysis cuts only. Absolute MD time ends at 80000 with dt=0.01. Physical settings
are frozen: f=4, N=40, 1000 stars, rho_p=0.8, total bead density 0.85, T=1,
Ea=4, Ee=8, nu0=20, Nevery=100, r_assoc=1.25, K=30, R0=1.5, damping=2.

A separate 8M driver reuses the previous continuous-review helpers, unchanged
joint analyzer, and validated graph callback. Its callback returns each original
graph untouched and retains compact derived metrics. Satellites are non-singleton
components outside one largest component; isolated stars and degree distributions
use distinct inter-star neighbors. 1M and 2M windows use the existing IAT heuristic
and 5/10/20-block sensitivity. Extra intra/inter, degree and shape estimates are
computed directly over their own shifted intervals, never by averaging IATs or
errors. 500k frame/event means tile exactly. The first 0–1M association transient
is retained for context, and 0–2M is excluded from long-window stationarity
comparisons. Early exclusions are contextual choices, not retrospective evidence
that all subsequent windows are stationary.

Only the three original histories enter paired Student-t df=2 intervals. The
intervals are exploratory and unadjusted; overlapping sensitivity comparisons and
coupled network observables are not independent confirmations. Stationary-mean
errors are conditional on approximately stationary windows. First-nonpositive-lag
IATs may miss slow tails; decreasing block errors do not demonstrate an error
plateau or complete mixing. No numerical acceptance threshold is introduced.

Reproduction (CPU only; output must be a new path):

```sh
python3 examples/KG_Assoc/analysis/analyze_e2_continuous8m_review.py --dataset-root examples/KG_Assoc/kg_assoc_100m --attempt examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N040_RP080_EE08/equilibrate_0a6a37a1e8264ceabbeead5362d8423d --plan-sha256 c8d624d6205f3b5eeb926b66fa9f992a446e9d53b4840cc88c8240406b99044c --output NEW_IMMUTABLE_REVIEW_DIRECTORY
```

Fresh 500k means are compared against every shared original checkpoint metric
and activity rate. Original attempt, checkpoint, workflow and six acceptance files
are checked byte-identical before/after analysis; precise hashes and comparison
bounds are in checkpoint_authentication.json. No native simulation code, protected
`examples/KG/` or `src/` files change. No GPU, extra E2, acceptance API, registry
activation/publication, production preparation or production authorization is used.
Reference acceptance validation calls are read-only. Catalog visibility comes from
new documented decision metadata, separately from formal acceptance and active
endpoint selection.
