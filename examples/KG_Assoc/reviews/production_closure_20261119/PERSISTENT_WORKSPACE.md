# Review evidence preservation

The review began on 18 November and completed on 19 November 2026 (Europe/Madrid).
Initial /tmp files were scratch staging, never simulation data or immutable
campaign records. Following the user’s storage concern, 47 files were checkpointed
under `kg_assoc_100m/aggregate/cpu_closure_review_20261119_v1/checkpoint_001`.
46 stable copies were independently compared with original bytes; the active
audit log was mirrored separately through an open file descriptor. The checkpoint
manifest is `CHECKPOINT_001.sha256`. No file in the original simulation dataset,
bank, acceptance, registry or execution journal was overwritten.

Subsequent publication preparation used the persistent workspace. Final dossiers,
inventories, test/audit evidence, scripts and their seal are committed to Git and
pushed, so they do not depend on /tmp retention. Reproduction writes to a new
`work/kg_closure_inventory_NEW` directory outside the dataset; `work/` is already
ignored by Git. The script refuses dataset destinations and existing output paths.

Git contains the compact review evidence, not the large ignored simulation data.
Persistent storage alone is not an independent backup. A separate-disk or
institutional backup of the dataset, banks, build records and journals is still
needed for disk-failure protection; no large copy or deletion was launched here.
