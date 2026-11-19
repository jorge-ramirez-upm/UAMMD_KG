# Campaign-mode chemistry validation repair

The native run `F03_N010_RP080_NONASSOC_r001` completed all 100,000 approved
steps on titan. Its authenticated native-finished journal records exit code
0, the original launch identity, and hashes of stdout, stderr, and the
atomic completion file. The completion file reports status `complete`
and steps 0–100,000. The stdout summary reports 17.527 seconds and zero
chemistry sweeps, mean candidates, creations, breaks, and final reversible
bond counts. All other eight histories remained prepared when this
reconciliation was made.

| Evidence | SHA256 |
|---|---|
| Original history | `c3852468e6805f4b048c644b70dd9a98e77fb281b152fddb10acc4a67f780e53` |
| Original started journal | `403949d9efcd8ad1b6e91ef66eddf49a1481f2cf99f41c5d25f2ad209b582f8e` |
| Original native-finished journal | `c90f3f27835c90206ee0bb76a7a86d193e39ac476992ad806989e37701d38036` |
| Original failure journal | `af361ac3c99e5972869cfbb100f6fb648e8e3ea824c49ae7609fd42debd1a5fe` |
| Native atomic completion | `41ffae4eabc2234a4ffb9c50a7e58d634e3e3b8506a32ce1473ee6ae74813e9f` |
| Native stdout | `f9e2a83f6e6b8cb97f0c5a05ae36caaba191580f8785fa9dc25d40878e54adb8` |
| Independent reconciliation | `7523ca02d6b47649c97de92bb60d2891ad7b51d89d7eaecc8d6f61426d2009f9` |

## Cause and repair

The native campaign thermo file contains per-sample temporary energy,
bond and event counters and the input provenance (`nu0=0`). It omits the
end-of-run chemistry summary fields because those fields are written under
`#ifndef KG_ASSOC_CAMPAIGN_PRODUCTION`. The frozen historical validator
mistook the omission for activity. It reproduced the exact exception
`control ran chemistry or candidate searches` on this output.

The repaired validator requires exactly one native stdout summary for the
approved step count, and requires each chemistry, mean candidate, event
and final reversible bond measurement there to be present once and zero.
It checks any optional thermo summary fields if present. The existing
per-row temporary energy and counter, empty event/final association,
zero topology, provenance, final particle geometry/velocity, COM, bead,
and six-channel stress checks still apply. The total candidate count
has no separate campaign output field. Zero sweeps and zero reported
mean candidates confirm the disabled search path together with the
authenticated native implementation. Reversible stress remains unreported
as a separate channel.

The corrected CPU validation passed on the original bytes. It checked
100 thermo rows, ten synchronized COM/topology frames, one bead frame and
100,000 stress samples with 116 lag bins and exact pair counts. The
[immutable reconciliation](RECONCILIATION.log) binds the original failure
hash, native journals, original authority and all output hashes.
[RELEASE.log](RELEASE.log) pins this record and the repaired driver to a
Git publication. There is no new launch approval or general recovery
exception. The original failure still has its original classification and
remains in the original directory. This separate CPU reconciliation is
specific to the one inspected defect. The old driver continues to hold
this history, and ordinary recovery continues to reject numerical failures.

## Continue on titan

From the existing repository on `KremerGrest`, pull the published repair
and use its driver:

```bash
git pull --ff-only origin KremerGrest
timeout 600 python3 examples/KG_Assoc/reviews/nonassoc_compatibility_repair_20261119/CONTINUE.txt --check
python3 -u examples/KG_Assoc/reviews/nonassoc_compatibility_repair_20261119/CONTINUE.txt --execute
```

Preflight must report the first test as `reconciled_complete` and the other
eight as `prepared` if none have run. The continuation authenticates and
skips the first test. It uses the original approvals, seeds, inputs, native
argv and 100k executable for the remaining tests. Use `--status` to
monitor. The original lock, fail-stop policy and restricted administrative
recovery apply. A fixture replaces the launch function with a non-executing
stub and verifies that only the remaining eight histories reach it.

To independently reproduce the CPU reconciliation from the repository
root, with a clean worktree:

```bash
timeout 600 python3 - <<'PY'
from pathlib import Path
import json, runpy
d = Path('examples/KG_Assoc/reviews/nonassoc_compatibility_repair_20261119')
result = runpy.run_path(str(d / 'CONTINUE.txt'))['make_reconciliation']()
assert result == json.loads((d / 'RECONCILIATION.log').read_text())
print('PASS exact reconciliation reproduced')
PY
```

All evidence is CPU-only. The completed associating campaign, accepted
E1 states, dormant control plan and existing compatibility output/journal
files are preserved. The remaining eight compatibility completions and
review of the resulting numerical and resource evidence precede any
separate production activation. Starting Git SHA
`22b8429ae469f4ed162752c257cc720940f6e82a`.
