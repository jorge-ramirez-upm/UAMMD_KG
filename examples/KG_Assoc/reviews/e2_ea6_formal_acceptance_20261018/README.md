# Ea6 exact-24M formal qualified acceptance

User approval: 2026-10-18. Starting `KremerGrest` SHA:
`ceb4048a00897b8c335d718d885f9e14ac2c37e7` (clean; local/remote agreed).

Only `F04_N010_RP080_EE08_EA06` r001/r002/r003 at absolute 24,000,000 are now
formally `accepted_with_qualification` for `production_initial_state`.

Dataset record:
`examples/KG_Assoc/kg_assoc_100m/banks/e2_acceptance/F04_N010_RP080_EE08_EA06_24M_qualified_20261018_v1.json`

SHA256: `042b8a8dffa15ceba46cd4989bae4fb91cf9331dffeedf67d04c675adbe7ebd6`.
`ACCEPTANCE_RECORD.log` is the byte-identical committed copy, following the
repository's separation between dataset records and review evidence.

The exact three restart/chemistry pairs and hashes are in ACCEPTED_ENDPOINTS.csv.
They descend from the qualified corrected-C1 Ea4/Ee8 r001/r002/r003 at 8M via the
manually completed reseeded Ea6 16M segments, never through a smoke output.
REVALIDATE.txt independently replayed each complete history under a separate
600-second CPU cap. REGISTER.txt then invoked the established
`kg_assoc_e2_registry.accept` mechanism, including its full-triplet independent
validation and immutable exclusive publication. That job also had a 600-second
cap. No GPU execution, registry publication, selection or activation occurred.

The registration binds the existing joint scientific assessment, immutable source
plan and completion receipts, exact restart/sidecars and all standard numerical
outputs. Source/build identities and MD streams remain bound through the source
plan, manifest and receipts. New accepted-event counts are 92200/92177/91378;
160,000 oracle comparisons and 43,563-particle initial device readbacks/history
were revalidated. The inherited original source/build limitations remain stated.

The qualification explicitly retains inherited Ea4/preparation-route and legacy
provenance limitations; unproven finite-step coupled-process equilibrium
invariance; limited ESS in some slow observables; replica-specific excursions,
especially r002 intra associations; and unproven complete decorrelation or
initialization-bias removal. This is qualified initialization, not proof of full
equilibrium. Ea8/Ea10 remain on scientific hold.

REGISTRATION_TESTS.log records six CPU checks of exact publication, immutable
nonoverwrite behavior, endpoint/family identity, use restrictions, qualifications,
wrong-system rejection, and the twelve previous records/payload sets. Registration
was performed before any new executable front-end source changes. Later read-only
verification authenticates historical executable bytes/manifests and the exact
allowlisted continuation front-end transition rather than claiming that an old
build equals the new source tree.

For read-only rechecking on the authenticated raw-data host:

```bash
cd /home/jramirez/UAMMD_KG
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea6_formal_acceptance_20261018/TEST_REGISTRATION.txt
```

REGISTER.txt is the retained one-time registration procedure. Re-execution refuses
to replace the immutable record. Do not delete or recreate an existing record.
The acceptance is archived in Git; the operative dataset record remains in the
managed dataset, as with the previous twelve acceptances. The final preservation
and handoff results are in the sibling Ea8/Ea10 extension dossier.
