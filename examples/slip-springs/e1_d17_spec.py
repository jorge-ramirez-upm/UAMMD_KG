"""D1.7 pilot contract; import performs no validation, sampling or execution."""
from pathlib import Path
import csv
import itertools
import math
import re

from e1_d1_pilot import (require, load, file_record, digest, exact_step,
                         schedule_text, command as old_command, row_counts as old_counts)
from e1_d2a3_analyze import snapshot
from e1_d2a5_n64_analyze import regular_path, stamp

PROJECT = Path(__file__).resolve().parent
MANIFEST = PROJECT/'e1_d17_manifest.json'
BASE = Path('/home/jramirez/UAMMD_KG-evidence/d17')
EVIDENCE = BASE.parent


def output_path(path):
    path = regular_path(Path(path).absolute())
    value = path.resolve()
    require(value != BASE and value.is_relative_to(BASE), 'new evidence must be beneath d17')
    return value


def candidate():
    require(digest(MANIFEST) == (PROJECT/'e1_d17_manifest.sha256').read_text().split()[0], 'candidate changed')
    value = load(MANIFEST)
    require(value['execution_authorized'] is False and value['stage_b_authorized'] is False,
            'candidate cannot grant execution')
    require(len(value['cells']) == 6 and all(len(c['seeds']) == 4 for c in value['cells']), 'six R4 cells')
    require(len({s for c in value['cells'] for s in c['seeds']}) == 24, 'independent seeds required')
    return value


def runs(manifest):
    return [dict(id=f"{c['id']}-r{i}", cell=c['id'], replica=i, seed=seed,
        N=32, M=256, kappa=10, Z=c['Z'], nu_hop=100, dt=c['dt'],
        steps=exact_step(manifest['T'], c['dt']), sample=exact_step(manifest['scalar_spacing'], c['dt']),
        schedule=f"dt{c['dt']}.full.steps", snapshots=f"dt{c['dt']}.snapshots.steps")
        for c in manifest['cells'] for i, seed in enumerate(c['seeds'], 1)]


def schedules(manifest):
    result = {}
    for dt in sorted({c['dt'] for c in manifest['cells']}):
        end = exact_step(manifest['T'], dt)
        result[f'dt{dt}.full.steps'] = list(range(0, end+1, exact_step(manifest['full_spacing'], dt)))
        result[f'dt{dt}.snapshots.steps'] = [0, end]
    return result


def command(run, root):
    argv = old_command(run, root/'provenance/semiflexible', root/'runs'/run['id']/'output', root/'config')
    # Bare controls use the accepted disabled path; no zero-Z renewal request.
    argv[argv.index('--end-renewal')+1] = '1' if run['Z'] else '0'
    return argv


def tool_records():
    names = sorted(PROJECT.glob('*.py')) + [PROJECT/'tests/d17_regression.py',
        PROJECT/'E1_STAGE_D17_PROTOCOL.md', PROJECT/'E1_STAGE_D17_HANDOFF.md',
        MANIFEST, PROJECT/'e1_d17_manifest.sha256']
    return {str(p.relative_to(PROJECT)): file_record(p) for p in names}


def input_stamps(root):
    return {str(p.relative_to(root)): stamp(regular_path(p)) for p in sorted(root.rglob('*')) if p.is_file()}


def frames(path, columns, count, steps, dt):
    """One-frame streaming reader with exact integer schedule and finite records."""
    with Path(path).open(newline='') as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == columns, 'schema mismatch: '+str(path))
        for step in steps:
            batch = list(itertools.islice(reader, count))
            require(len(batch) == count, 'truncated frame: '+str(path))
            for i, row in enumerate(batch):
                require(set(row) == set(columns) and all(v is not None and math.isfinite(float(v))
                        for v in row.values()), 'malformed/nonfinite frame')
                require(row['step'] == str(step) and float(row['time']) == step*float(dt), 'frame clock')
                if 'chain' in row and Path(path).name not in ('equilibrium_sites.csv', 'equilibrium_connectors.csv'):
                    require(row['chain'] == str(i), 'frame chain order')
            yield step*float(dt), batch
        require(next(reader, None) is None, 'extra frame: '+str(path))


def seed_audit(manifest, roots, excluded):
    """Scan metadata/text only; no CSVs, binaries, compressed payloads or source copies."""
    import os
    planned = {s for c in manifest['cells'] for s in c['seeds']}
    pattern = re.compile(rb'(?<![0-9])(?:'+b'|'.join(str(s).encode() for s in sorted(planned))+rb')(?![0-9])')
    records, matches = {}, []
    for root in roots:
        root = regular_path(Path(root))
        require(root.is_dir(), 'missing seed audit root')
        for directory, children, names in os.walk(root, followlinks=False):
            children[:] = sorted(c for c in children if c not in ('.git', 'build', 'source', 'preparation', '__pycache__')
                and not c.startswith('regression') and not Path(directory, c).is_relative_to(excluded))
            for name in sorted(names):
                path = Path(directory, name)
                if path.suffix not in ('.json', '.jsonl', '.py', '.md', '.txt') or \
                        path.is_relative_to(excluded) or (path.parent == PROJECT and path.name in
                        ('e1_d17_manifest.json', 'E1_STAGE_D17_PROTOCOL.md')):
                    continue
                regular_path(path)
                # Planned seeds fit on one text line in supported metadata formats.
                with path.open('rb') as stream:
                    for line in stream:
                        if pattern.search(line):
                            matches.append(str(path))
                            break
                records[str(path)] = file_record(path)
    require(not matches, 'planned seed collision: '+str(matches))
    return dict(status='NO_MATCHES_IN_DECLARED_SCOPE', planned=sorted(planned), files=records,
        excluded_directories=['.git', 'build', 'source', 'preparation', 'regression*', str(excluded)],
        scope='Available JSON/JSONL/Python/Markdown/text metadata only; no guarantee about inaccessible or compressed external use.')
