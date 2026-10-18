# User authorization: Ea8/Ea10 extensions from exact 24M parents

Authorized milestone begun 2026-10-18, prepared across 2026-10-18/19. Starting
Git SHA `ceb4048a00897b8c335d718d885f9e14ac2c37e7` on `KremerGrest`.

Only `F04_N010_RP080_EE08_EA08` r001/r002/r003 may run +16,000,000 steps,
24M→40M. Only `F04_N010_RP080_EE08_EA10` r001/r002/r003 may run +32,000,000
steps, 24M→56M. All start from the corresponding authenticated manual 24M
endpoint named in the joint scientific review's ENDPOINTS.csv. Exactly six
completed extensions total 144,000,000 additional steps; no further extensions
or replicas are authorized.

The user explicitly clarified interruption accounting:

> Allow recorded restart overhead; cap each completed extension as specified

Thus abandoned partial execution is recorded separately, with a trustworthy
completed-step lower bound and the attempt's authorized maximum as an upper
bound when a hard interruption prevents an exact count. The completion budget
remains 144M. A safely interrupted partial may be retried automatically, only
from its original exact 24M parent in a fresh immutable attempt with fresh MD
streams. Its outputs and all consumed/reserved streams remain preserved.
Numerical, candidate, provenance and chemistry failures stop the campaign and
are never retried automatically. Scientific incompleteness never triggers an
extension or retry.

Chemistry retains the exact inherited seed and absolute-step keys and offsets.
MD uses new GJ noise; this is not bitwise MD continuation. Retried partials reuse
the parent's counter-based chemical key schedule by the continuation policy;
they are not independent chemical preparations and must not be merged with the
successful attempt. No segment-crossing IAT, SEM or full lifetime origin is
stitched through the fresh-MD boundary.

Codex is authorized only to implement, prepare, compile and CPU-test this handoff.
Codex must not execute GPU equilibration or extension calculations. The user
runs `--execute` on titan. Preparation and read-only checks are separate commands.
No Ea8/Ea10 formal acceptance, registry selection/activation or production action
is authorized. Their existing scientific holds remain in effect after numerical
completion until separate scientific review and user approval.
