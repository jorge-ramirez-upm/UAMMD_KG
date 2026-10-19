# Ea8 r001 completed MD; required device readback absent

**Validation hold. The completed trajectory cannot be fully validated without a
new trajectory. No GPU work, recovery writes or new attempts were performed in
this investigation. The other five extensions remain unstarted and blocked.**

Starting clean local/remote KremerGrest HEAD:
`dbd79b1ba3fba4c9701e54d09de9a9a5cf6e700f`.
The date of this CPU-only investigation is 2026-10-19 Europe/Madrid.

## Actual trajectory and evidence

Ea8 r001 native execution completed exactly **16,000,000 additional MD steps**,
absolute 24,000,000→40,000,000. Its native executable returned through the PASS
path; the Python launcher subsequently failed during independent validation.
The footer, all 16,001 diagnostic samples, 160,000 consecutive chemistry/oracle
records, final restart timestamp and chemistry sidecar agree. There is no valid
complete.json. The immutable incomplete.json and campaign state retain the
original missing-file error. Native wall_seconds in the footer is 12,345.

The unchanged strict validator independently replayed the events and passed all
checks preceding its mandatory readback gate: exact parent/lineage/counters,
permanent identities/topology, final chemistry partners, endpoint sidecar/mirrors,
finite numerical/conformation records, bond geometry, runtime MD-stream identity
and endpoint consistency. It then reproduced FileNotFoundError at the exact
expected readback path. The oracle records located after that gate in the
validator were checked separately: 160,000 consecutive sweeps and 401,605,094
candidate pairs, consistent with the native counter. The native diagnostic build
requires candidate/all-pairs equality before each recorded sweep. These checks
provide useful forensic evidence but **do not constitute full validation**.

New accepted events: 6,369 creations and 6,381 breaks, 12,750 total.
Inherited→final counters are creations 126,066→132,435 and breaks
124,269→130,650. Active bonds 1,797→1,785; intra 82→104; inter 1,715→1,681.
No equilibration or scientific acceptance conclusion is drawn from this evidence.

All five other histories used zero MD steps. Aggregate extension-campaign usage
is exactly 16,000,000 MD steps, all in the held Ea8 r001 history. Assistant GPU
usage is zero. No retry or restart overhead has been generated.

ENDPOINT_IDENTITIES.log binds exact endpoint paths, SHA256 values, original
24M parent, branch, seeds, executable and approvals. Principal endpoint hashes:

| Original artifact | SHA256 |
|---|---|
| state.restart.lammpsdat | `3936ac0d892951f8e2bb5f3b88fe2bcf731a647ed373cbc059b0f747c82af0d4` |
| state.assoc_restart | `c26e17d1465681bf754858cd488504eb6e760b4448efe614591b1c47d8d749da` |
| state.events | `3a8b7e5cda5d5c394bc8c18f34ec9430da07f780caaa15eaa26e53030886510a` |
| state.candidate_validation.tsv | `e5dba8f264ff44a634707d596ce4e0e8f85d5f6095a2a2f64ce3219ce9514926` |

## Root cause: the call did not execute

The authenticated native source at kg_assoc_stars.cu:1128 guards the entire
initialDeviceReadback call with `if (parameters.reseedChemistry)`. The extension
mode preserves the chemistry seed and sets e2Extension, so reseedChemistry is
false. No initial device readback was executed or written. The source digest is
`07b6eb5f725f46c1f5b04ef45123fd8915a562c62cee916e2eb0b18eda581ae7`.
The candidate executable digest is
`88e8225f9dd4f221ff861f135e68cec927b4a3228d166429ae804a39129b636b`.
Both match the immutable build and plan. NATIVE_CALL_PATH.log preserves the
exact relevant source. State/event headers declare readback required, but that
declaration is not evidence that the call ran.

Writer and validator use the same `.initial_device_validation.tsv` suffix and
absolute output prefix. This is neither a filename nor a working-directory
defect. The previous GPU smoke and 8M→24M preparation used chemistry reseeding,
so they entered this guard. READBACK_SEARCH.log identifies 23 historical files,
including retained failed-attempt evidence; none belongs to either extension
attempt. A parent's readback has a different start step, branch and build and
cannot substitute for this trajectory's missing initial device evidence.

All six original plans select the same affected native build and seed-preserving
extension mode. HOST initialization checks return before device construction;
they could not detect the omitted GPU call. Prior CPU tests proved that the
readback implementation and physical tail were unchanged, but did not prove
that the new extension path called it. The earlier handoff's claim that the
extension would execute readback before MD was incorrect. This review supersedes
that readiness claim while preserving all historical dossier bytes.

## Scoped administrative repair and stopping decision

The launcher and runner now explicitly reject this known defective native-source
identity for extensions. `--check`, `--prepare` and `--execute` fail before
allocation or MD. The common E2 launch entry point also blocks the affected
extension build. Status now says `validation_hold_missing_initial_device_readback`
for the native-PASS history. Existing sticky numerical/provenance failure gates,
exact readback comparisons and independent-completion replay remain intact.
No failed state was cleared and no alternate seed, receipt, plan or output was
created. Existing receipt recovery still requires actual authenticated evidence;
CPU fixtures test both valid-evidence recovery and missing-evidence rejection.

No tolerance, oracle or physics change was made. Native CUDA, headers, physical
restart loader and strict validator were untouched; no new executable was needed
for this administrative hold. The defective historical executable remains intact.
The runner's complete source-map gates also remain enforced: existing plans are
not migrated to modified code by an exception.

**The user-run workflow cannot safely resume with these plans/build.** Missing
initial readback cannot be reconstructed from a final restart or generated by a
new zero-step run after the event. Full validation under the authorized contract
would require a new trajectory after correction; a synthetic readback, copied
parent evidence or a waived assertion would be invalid.

The smallest subsequent corrective milestone is to include extension mode in the
validation-only call guard, add a call-path regression, build in a fresh out-of-tree
directory, authenticate updated immutable plans/approvals and test actual device
readback before user-run MD. A replacement Ea8 r001 would start again from its
same exact 24M parent with fresh MD streams and preserve this failed attempt.
The other five must also use corrected authenticated preparations. None of that
GPU execution or new allocation is performed or authorized by this investigation.
A later explicit authorization is required before replacing the held trajectory.
No scientific acceptance or production action occurred.

## Reproduce and monitor safely

```bash
cd /home/jramirez/UAMMD_KG
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea8_extension_readback_forensics_20261019/INVESTIGATE.txt
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea8_extension_readback_forensics_20261019/VERIFY.txt
python3 examples/KG_Assoc/campaign/run_ea_extensions.py --status
python3 examples/KG_Assoc/campaign/run_ea_extensions.py --check
```

The last command intentionally exits 1 with the explicit validation hold. The
first two are read-only CPU checks; neither publishes a receipt nor changes
campaign state. Do not delete folders, edit JSON, reclaim streams or rerun MD to
try to clear this failure. TESTS.md records CPU regressions and preservation.
