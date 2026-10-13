# N=20 6M assessment: validation and integrity

Starting verified local/remote `KremerGrest`:
`05d6ea06323df2b0059fa1da9c1fb21d56f75e0e`.
Source plan SHA256:
`085a6a56f004ef6c5d21d2d0fa0a9277e51e8c97c96312eaf34e2067de5e5b90`.

Existing `analyze_joint_e2.authenticate()` and the unchanged numerical/event/network/
conformation validators independently authenticate all three 0–6M histories.
The E1 snapshots/completion/diagnostic/inventory hashes, initial particle and sticker
identities, plans/approvals, physical parameters, seeds, build/source/log/executable
hashes, completion receipts and output payloads are checked. Current executable
bytes authenticate for this attempt; no unavailable-historical-binary qualification
is needed for the N=20 histories. The N=10 corrected C1 reference retains its own
historical provenance limitations and is used only as qualitative context.

Original histories are continuous, initially unbound, absolute 0–6M, with no E2
extensions or intermediate MD reseeding. Analysis cuts are not restart boundaries.
Chemistry seeds: 420901/420902/420903; MD seeds: 520070/520071/520072. Exact effective
MD seeds, endpoint bindings and fresh validation results are in provenance.json.

Graph capture uses the unchanged validated replay callback, returns each original
graph untouched and stores compact derived counts. Satellites are non-singleton
components outside one largest component; isolation/degree are defined on distinct
inter-star neighbors. Non-overlapping 1M and 2M windows use existing correlation
and 5/10/20-block helpers. Half-million windows carry exact means only unless a
separate conformational estimate is explicitly recorded. Shifted/overlapping
windows remain exploratory; they are not additional independent observations.
Only three histories enter paired Student-t df=2 intervals. No universal threshold
or automatic equilibrium acceptance is introduced. Constant observables are not
mixing evidence. The 0–1M unbound-association transient remains contextual.

Reproduction command (CPU-only, requires a new output path):

```sh
python3 examples/KG_Assoc/analysis/analyze_e2_continuous_review.py --dataset-root examples/KG_Assoc/kg_assoc_100m --attempt examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N020_RP080_EE08/equilibrate_bdfe5dc30d87435899f6d2d21dc99fac --plan-sha256 085a6a56f004ef6c5d21d2d0fa0a9277e51e8c97c96312eaf34e2067de5e5b90 --output NEW_IMMUTABLE_REVIEW_DIRECTORY
```

CPU regression suite: **121 tests passed**, including four new continuous-review
tests for exact frame/event means, input immutability, three-history fractional
window pairing, overlap labeling, scope/source-hash/no-overwrite guards and
restoration of temporary metric selection after failure. Existing acceptance,
joint review, satellite, catalog, recovery and wrapper tests passed. Python byte
compilation and diff whitespace checks passed. Existing legacy restart-reader
ResourceWarnings remain unchanged. No native code/header changed; no rebuild or
GPU smoke is required.

The conformation figure shows correlated diagnostics and uniform start-exclusive,
end-inclusive 500k means, with no pseudo-replica error bars. Its source hashes,
rendering version and recipe are frozen separately. Corrected C1 summary bytes
match the frozen inventory and its accepted restart payloads authenticate. Only
corrected C1 6–8M windows are used; PBC-defective windows are excluded.

Original MD trajectories/restarts, checkpoint reports, historical reviews and five
formal acceptance records remain unchanged. No GPU calculation, further E2,
formal registration, registry publication/selection/activation, production
preparation or authorization occurs. This dossier documents a recommendation only.
