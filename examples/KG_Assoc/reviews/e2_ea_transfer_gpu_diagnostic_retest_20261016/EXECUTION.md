# Execution identities and cap accounting

The user authorized only this capped GPU diagnostic retest. AUTHORIZATION.json
records that authority; each approval is bound to its immutable plan SHA256 and
purpose `e2_derived_smoke`. Reviewer text records the user's instruction, not an
independently supplied external signature. The existing `kg_assoc_e2.launch`
performs all source/parent/build/approval and output-reuse checks. Its first
nonzero executable exit aborts the orchestration, without resume or retry.

Dataset: `examples/KG_Assoc/kg_assoc_100m`.
Work: `aggregate/e2/ea_transfer_diagnostic_retest_20261016_v1`.
The four bank attempt names are
`derived_F04_N010_RP080_EE08_EA{04,06,08,10}_gpu_diagnostic_retest_20261016_v1`,
under `banks/e2_attempts/F04_N010_RP080_EE08/`; each has r001–r003 and prefix `state`.
All twelve host checks succeed before launch. All start steps are 8,000,000,
branch origin 8M, age zero, planned additional steps 10,000 and end caps 8,010,000.
No smoke output is a parent.

The reference acceptance record is
`banks/e2_acceptance/F04_N010_RP080_EE08_EA04_8M_qualified_20261013_v1.json`, SHA256
`525a1834494d88c8f5eae919d87bdcaa6d372e875acd340d1be66b124165ef22`.
Its restricted `production_initial_state` qualification is preserved verbatim in
PREFLIGHT.json and every history lineage. Original defective historical C1 states
are excluded. Chemistry seed 22000+replica, partners, absolute step, physical time
80,000 and cumulative counters are inherited; new chemical seeds are explicit
branch seeds, with no synthetic events. At the failed readback the new Kinetics
object has not yet been constructed and no chemical sweep is executed.

Physics: Ee=8, T=1, nu0=20, Nevery=100, dt=.01, damping=2, K=30, R0=1.5,
r_assoc=1.25, original box/density/topology; only target Ea and explicitly selected
random streams differ. Complete physics dictionaries, canonical commands and
source/executable maps are in EXECUTION_METADATA.json. The strict candidate
predicate remains real-first subtraction, double nearest-image reduction and
`rsq < 1.5625`; the independent all-pairs algorithm remains separate. Neither
algorithm executes a chemistry sweep in this retest.

## Source and build

Plan source HEAD: `ecce23aad26884d0ec270a25d769ca0abf341a5b`.
Ancestor build source SHA: `74933f7c4e12f8812e44707c89662af1aec273f7`.
The official build checker authenticated source equality (620 captured bindings),
ancestor lineage, compile logs and all executable hashes. No rebuild was needed.
Build directory: `builds/ea_cutoff_contract_cpu_20261016_v1`.
Manifest SHA256:
`3739b7611ecd5b4e78d0739f882677a8c163eb107526515fcce7cff74fbc890a`.
Actual GPU executable `kg_assoc_stars_candidate_smoke` SHA256:
`45a8f85e8a421a6730e8ba96f543635bbad0a7c56bf23bfd8d7e865604e7089c`.
Ordinary frontend SHA256:
`f0b1494fc25859485c94466866dde5bf6683d1c6dc63efa290b888f8799108ac`.
Candidate-test SHA256:
`c58bdb3573d97e6b34b219dc2503e192995e6b9662facd2115d3541d36768d85`.
No historical executable is overwritten. Build manifest copies are in PREFLIGHT.json
and the plans. New review files are added only after GPU execution has stopped;
this dossier does not claim the old build captures those later-added review files.

Actual GPU: TITAN Xp, UUID `GPU-8170bfc5-0914-1b23-e2b6-fdb85300a2b6`,
driver 580.178.04, host `titan`; environment and stderr are bound in the output map.
The failed executable logs requested MD seed 730401, effective seed 2405369836 and
GJ internal_start_step=0. Velocities are preserved; GJ internal memory/noise is reset.
This is explicitly **non-bitwise continuation**. No first MD noise step executes.

## New reservation and evidence

New immutable policy:
`banks/e2_seed_reservations/ea_transfer_diagnostic_retest_20261016_v2.json`.
An exact tracked copy is SEED_RESERVATIONS.json. Its twelve rows were selected
as the prior policy's chemical/requested-MD seeds plus 100,000, then authenticated
against all existing plans/records, legacy seed evidence, other reservations and
effective 32-bit MD streams. All 24 requested IDs and twelve effective MD streams
are distinct. The old reservation is unchanged. All new rows are claimed by these
plans, including eleven unexecuted histories; none may be reclaimed.

Raw plans, approvals, receipts, logs, readback and partial outputs remain in their
immutable dataset locations, following campaign conventions. EXECUTION_METADATA.json
preserves parsed metadata copies; NEW_OUTPUTS_SHA256.json binds all 28 new raw
campaign/authorization artifacts. Large particle output is not checked into Git.
The readback's embedded full build manifest and branch/step/precision/rounding
metadata are authenticated by reproduce.py. There is no complete receipt; only
started/environment/incomplete receipts for Ea4 r001. Other replica directories
are empty.

The failure is before Kinetics construction and the first `integrator->forwardTime`.
No state/event/numerical/conformation row exists. Thus actual aggregate MD usage
is zero, not a last-output-step estimate. One GPU context/readback ran; zero
histories completed, zero oracle sweeps ran, eleven histories were never started.
The step authorization is a maximum, not permission to proceed after failure.

## Exact original parents

Each prefix is `banks/e2_extensions/C1_periodic_recovery_v1/rNNN/state`.

| Replica | Restart SHA256 | Chemistry-sidecar SHA256 | Inherited creations / breaks |
|---|---|---|---|
| r001 | 09e1a9f5329a2be06e28112c5bc53e399f54c7aba74369684f12968f68d6b21b | 9eb4e566d96f0080d9a03677e5d23d231ce389193c71a57f68c58f22035e9ecc | 119665 / 117882 |
| r002 | ae1599f3d2ffcfd333058b2867bbc7ba897b7dccd84e8b2e7a2996aaa6df3c5b | 7fd18a27d4d989881397b33b94ffe92de21a05c1e318f8236586b737ee697674 | 120242 / 118455 |
| r003 | 10a7885b6e704258dee322e4c310f26bfe921b586e769a477600d515ef888e2a | 8a260fd5a6e5b3408ba71e10ccb2e47437cf61691036e5c82fcf1c9ac058427c | 119059 / 117256 |

## Exact plans and approvals

| Ea | Plan SHA256 | Approval SHA256 |
|---|---|---|
| 4 | df0094f54990d7c8feac1e4a7a8dec4d998769cfd81531b3d58fd2a93d65f3e1 | cbffd34a76814e9b04ebb23e99c7747a891f45ec8058b826055c87adbafc8055 |
| 6 | 5923cfa3e05ee47725e22974b9b04a3d369c9b36957a4414b1290f8139007f83 | d8784529195b65d34ffad92e883ac8188c2ee954365ae53cd342e306054efb5a |
| 8 | 585fdc58a6e219a4a13957a0d69ab00fb0d1ad57cfdccabe035152ac12e57024 | 2cad903f6d52ce1814ebc7b5ce6657f973a300195f10d898197ab0fb08ed8a5f |
| 10 | 6d74b58bca134c7a4989c7232ec889e4cde10da977cf26439ea3cd64a91c71d5 | bf9c4b35ae756aad3ab1fcb3702db288502aed559447d4a21cdc4b7bb050d831 |

## Key raw artifact SHA256

| Artifact | SHA256 |
|---|---|
| environment.json | 5f4ab29ef78faffa1b36d8cea93ffb93870d3d38852d8964e3b26fd797d6571d |
| incomplete.json | 25009b4a9d78255d6c9d19df086dc10a60825ddfcf0256eacdd7ce6fd85a3626 |
| started.json | 9f40e3f09aec0236fa72758ae5e7fbb55510b514a3f5fea98962298afb69a915 |
| state.candidate_validation.tsv | 105a151bd66e03c24f503a36277fd800db1e462d493d299e9c5963c450a1b06a |
| state.initial_device_validation.tsv | 16eba43065f812930363c9259cc0ff633a001f622d027c4fdea47a2d3f30582f |
| stderr.log | 517f77ac5360ccf1bdd2351b42f683d7a7e05d8688b994552f0c2b38908f1942 |
| ea_transfer_diagnostic_retest_20261016_v2.json | c23daa056cd33963ecdf0bed2ba4d1b45a4fbcbcd8fce55cb3d21276019fb7ac |
