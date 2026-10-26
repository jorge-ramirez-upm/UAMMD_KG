"""Frozen D1.6B candidate and resource amendment. Import performs no jobs."""
from fractions import Fraction
import math
from pathlib import Path

import e1_d1_pilot as old
from e1_d1_pilot import (require, Invalid, encoded, load, digest, identity, file_record,
                         atomic, utc, capture, exact_step, schedule_text, source_identity)

PROJECT = Path(__file__).resolve().parent
CONFIG = PROJECT/'e1_d16b_config'
ACCEPTED_SHA = old.ACCEPTED_SHA
REPOSITORY_ID = old.REPOSITORY_ID
GPU_UUID = 'GPU-83d1eede-bd03-c365-6f3a-b6d6e2be6274'
START = 'e533e0412476c3e98875d9518afae42d75273928'
NEW_FILES = ('e1_d16b_spec.py', 'e1_d16b_references.py', 'e1_d16b_auth.py',
    'e1_d16b_host.py', 'e1_d16b_local.py', 'e1_d16b_analysis.py',
    'tests/test_e1_d16b.py', 'E1_STAGE_D16B_PROTOCOL_V1.md',
    'E1_STAGE_D16B_RESOURCE_AMENDMENT_V1.md', 'E1_STAGE_D16B_OPERATOR_GUIDE.md',
    'E1_STAGE_D16B_IMPLEMENTATION_REPORT.md', 'e1_d16b_config/reference-lock.json',
    'e1_d16b_config/performance-lock.json', 'e1_d16b_config/resources.json')


def durable(path):
    path = Path(path).expanduser().resolve()
    require(not any(path.is_relative_to(Path(p)) for p in ('/tmp', '/var/tmp', '/dev/shm')),
            'persistent D1.6B paths must use durable storage')
    return path


def output_path(path, protected_source=None):
    return old.output_path(durable(path), protected_source)


def tool_hashes():
    prior = load(PROJECT/'e1_d15_config/exploratory/manifest.json')['preparation_sources']
    closure = set(prior) | set(NEW_FILES) | {
        'e1_d15_local.py', 'e1_d16a2_local.py', 'e1_d16a2_reference.py',
        'e1_d16a2_sampling.py', 'e1_d16a_reference.py', 'e1_d16a2_config.json',
        'e1_d16a2_preserved_sources.json', 'tests/test_e1_d14_phase_b_technical.py',
        'E1_STAGE_D16_SCIENTIFIC_DESIGN_V1.md', 'E1_STAGE_D16_REFERENCE_MOMENTS_V1.md',
        'E1_STAGE_D16_RESOURCE_PLAN_V1.md'}
    return {name: digest(PROJECT/name) for name in sorted(closure)}


def schedule(dt):
    end = exact_step('100', dt)
    scalar = list(range(0, end+1, exact_step('0.5', dt)))
    regular_full = list(range(0, end+1, exact_step('2', dt)))
    early = [1]+[exact_step(t, dt) for t in ('0.0005','0.0025','0.01','0.05')]
    full = sorted(set(regular_full+early))
    audits = [exact_step(t, dt) for t in ('0','0.01','50','100')]
    require(set(audits) <= set(full), 'audit requires an actual full frame')
    return {'scalar': scalar, 'full': full, 'snapshots': audits, 'regular_full': regular_full,
            'extra_early': early, 'union': sorted(set(scalar+full))}


def runs():
    # Preserve the old, never executed D1.5 exploratory seed identities exactly.
    prior = load(PROJECT/'e1_d15_config/exploratory/manifest.json')['runs']
    return [dict(r, id=r['id'].replace('D15-exploratory', 'D16B')) for r in prior]


def row_counts(run, observations=None, snapshots=None):
    s = schedule(run['dt'])
    return old.row_counts(run, s['full'] if observations is None else observations,
                          s['snapshots'] if snapshots is None else snapshots)


command = old.command
state_estimate = old.state_estimate


def validate_limits(value):
    expected = load(CONFIG/'resources.json')['limits']
    require(value == expected and all(type(v) in (int,float) and math.isfinite(v) and v>0
            for v in value.values()), 'D1.6B resource amendment differs; new review/version required')
    require(all(type(v) is int for k,v in value.items() if k.endswith('bytes')), 'integer byte limits required')
    return value


def validate_manifest(path, sha):
    require(digest(path) == sha and sha == (CONFIG/'manifest.sha256').read_text().split()[0],
            'frozen D1.6B manifest SHA256 mismatch')
    value = load(path)
    require(value == load(CONFIG/'manifest.json'), 'not the frozen D1.6B candidate')
    require(value['schema'] == 'e1-d16b-candidate-v1' and value['execution_authorized'] is False
            and value['candidate_only'] is True, 'manifest cannot grant execution')
    require(value['preparation_sources'] == tool_hashes(), 'preparation source changed')
    require(value['accepted_sources'] == old.source_hashes(), 'accepted model source identity changed')
    require(value['runs'] == runs() and len(value['runs']) == 16
            and len({r['seed'] for r in value['runs']}) == 16, 'frozen 16-run seed/matrix mismatch')
    prior = load(PROJECT/'e1_d15_config/exploratory/manifest.json')
    require(value['common'] == prior['common'], 'physical parameters changed')
    require(digest(PROJECT/'e1_d15_config/exploratory/manifest.json') == value['parent_manifest_sha256'],
            'immutable D1.5 T100 proposal changed')
    require(value['resource_amendment'] == file_record(CONFIG/'resources.json'), 'resource amendment changed')
    for dt in old.TIMESTEPS:
        s = schedule(dt)
        require((len(s['scalar']),len(s['regular_full']),len(s['full']),len(s['union'])) == (201,51,56,206),
                'observation counts changed')
        for kind in ('scalar','full','snapshots'):
            name = f'dt{dt}.{kind}.steps'
            require(value['schedules'][name]['steps'] == s[kind]
                    and (Path(path).parent/name).read_bytes() == schedule_text(s[kind])
                    and digest(Path(path).parent/name) == value['schedules'][name]['sha256'],
                    'schedule content changed: '+name)
    require(value['expected_row_counts'] == {r['id']: row_counts(r) for r in value['runs']},
            'expected row counts changed')
    return value


def estimates(manifest):
    # Format-derived envelope from the retained observer and all legacy tables.
    per = 948+256*(67550+292*5+342*201+5574*56)+323*56
    limits = validate_limits(load(CONFIG/'resources.json')['limits'])
    require(per+2*1024**2 < limits['per_run_output_bytes'], 'per-run schema envelope exceeds proposal')
    require(16*(per+2*1024**2)+64*1024**2 < limits['aggregate_output_bytes'], 'cohort envelope exceeds proposal')
    return {'runs': len(manifest['runs']), 'csv_width_envelope_per_run': per,
            'csv_width_envelope_cohort': 16*per, 'shared_allowance_bytes':64*1024**2,
            'metadata_allowance_bytes_per_run':2*1024**2,
            'planning_only':True, 'gross_production_proxy_seconds':2056,
            'initial_disk_required_bytes': limits['min_free_disk_bytes']+2*limits['aggregate_output_bytes']}
