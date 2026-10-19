# Resume the remaining Ea extensions on titan

From a clean checkout on `titan`:

```bash
cd /home/jramirez/UAMMD_KG
git status --short --branch
python3 examples/KG_Assoc/campaign/run_ea_extensions.py --check
python3 examples/KG_Assoc/campaign/run_ea_extensions.py --status
python3 examples/KG_Assoc/campaign/run_ea_extensions.py --execute
```

The launcher replays and skips recovered Ea8 r001. It can execute only Ea8 r002/r003 and Ea10
r001/r002/r003 under their existing immutable approvals. To interrupt safely, send `SIGINT` to the
foreground launcher, keep all outputs, inspect `--status`, and reissue `--execute` only after that
inspection. Completed validated histories are skipped; a genuine partial history is preserved and
uses the workflow's new immutable replacement path rather than an overwrite or bitwise-resume claim.
