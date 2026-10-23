# CPU-only design audit

No production commands, seed reservations, plans or approvals are issued here.
BUDGET.csv and CONDITIONS.csv are descriptive review tables; every execution flag
is false. Fifteen immutable acceptance records and 45 exact initial-state pairs are
hash-bound in BUDGET_INPUTS.sha256. BUDGET_SUMMARY.log excludes text/COM/events,
analysis duplication and I/O cost; its historical-linear timing is not a benchmark.

From repository root, reproduce only resource arithmetic into a new scratch directory:

```bash
out=$(mktemp -d /tmp/kg_rheology_design.XXXXXXXX)
timeout 600 python3 examples/KG_Assoc/reviews/rheology_production_design_20261023/BUDGET.txt --output "$out/budget"
```

Verify original input and dossier hashes without writing any campaign state:

```bash
python3 - <<'PY'
import hashlib,json
from pathlib import Path
folder=Path('examples/KG_Assoc/reviews/rheology_production_design_20261023')
for name in ('INTEGRITY.sha256','BUDGET_INPUTS.sha256'):
    for path,digest in json.loads((folder/name).read_text()).items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
print('PASS design/initial-state bindings; no execution')
PY
```

DESIGN.md distinguishes the existing online six-channel estimator from proposed
synchronized stress output, and the existing 100M-only campaign gate from proposed
staged 32M observation. Neither capability is silently claimed implemented. A later
milestone must test those administrative/observability changes before a user can
approve any simulation. Existing post-run endpoint/lineage gates remain mandatory.
