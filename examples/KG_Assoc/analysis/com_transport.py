"""Fail-closed metadata contract for corrected, independent COM transport segments."""
from contextlib import contextmanager
import bisect
import json
import math
import warnings

COLUMNS = '# step time molecule_id com_x com_y com_z'
CONVENTION = 'native_continuous_plus_initial_backbone_offsets'
FIELDS = {'convention', 'origin_kind', 'origin_id', 'origin_step', 'cadence_steps',
          'dt', 'unit_mass', 'box_bounds', 'molecule_ids'}


def read_metadata(stream, path, allow_legacy=False):
    if stream.readline().strip() != COLUMNS:
        raise ValueError(f'{path}: unexpected COM header')
    boundary = stream.tell()
    marker = stream.readline().strip()
    if not marker.startswith('# KG_COM_TRANSPORT'):
        stream.seek(boundary)
        if not allow_legacy:
            raise ValueError(f'{path}: legacy COM lacks authenticated continuous-coordinate metadata; '
                             'use --allow-legacy-com only for explicitly unverified historical analysis')
        warnings.warn(f'{path}: legacy COM explicitly accepted as unverified; winding may be aliased')
        return {'version': 1, 'legacy_unverified': True}
    if marker != '# KG_COM_TRANSPORT 2':
        raise ValueError(f'{path}: unsupported COM transport version')
    fields = {}
    while True:
        line = stream.readline().strip()
        if line == '# END_KG_COM_TRANSPORT':
            break
        if not line.startswith('# ') or len(line.split(maxsplit=2)) != 3:
            raise ValueError(f'{path}: incomplete COM transport metadata')
        _, key, value = line.split(maxsplit=2)
        if key not in FIELDS or key in fields:
            raise ValueError(f'{path}: duplicate or unknown COM metadata field {key}')
        fields[key] = value
    if set(fields) != FIELDS or fields['convention'] != CONVENTION or \
            fields['origin_kind'] != 'independent_segment_no_concatenation':
        raise ValueError(f'{path}: incompatible COM coordinate or restart-origin convention')
    fields['origin_id'] = json.loads(fields['origin_id'])
    for key in ('origin_step', 'cadence_steps', 'unit_mass'):
        fields[key] = int(fields[key])
    fields['dt'] = float(fields['dt'])
    fields['box_bounds'] = [float(v) for v in fields['box_bounds'].split()]
    fields['molecule_ids'] = [int(v) for v in fields['molecule_ids'].split()]
    ids = fields['molecule_ids']
    bounds = fields['box_bounds']
    if not isinstance(fields['origin_id'], str) or not fields['origin_id'].strip() or \
            fields['origin_step'] < 0 or fields['cadence_steps'] <= 0 or fields['unit_mass'] != 1 or \
            not math.isfinite(fields['dt']) or fields['dt'] <= 0 or len(bounds) != 6 or \
            not all(math.isfinite(v) for v in bounds) or \
            not all(bounds[i + 1] > bounds[i] for i in (0, 2, 4)) or \
            not ids or ids != sorted(set(ids)) or min(ids) <= 0:
        raise ValueError(f'{path}: invalid COM identity, box, mass or cadence metadata')
    return dict(fields, version=2, legacy_unverified=False)


@contextmanager
def open_com(path, allow_legacy=False):
    with open(path, encoding='utf-8') as stream:
        metadata = read_metadata(stream, path, allow_legacy)
        yield stream, metadata


def metadata_for(path, allow_legacy=False):
    with open_com(path, allow_legacy) as (_, metadata):
        return metadata


def _validate_step_time(metadata, path, step, time):
    if metadata['version'] == 2 and (step < metadata['origin_step'] or
            (step - metadata['origin_step']) % metadata['cadence_steps'] or
            not math.isclose(time, step * metadata['dt'], rel_tol=1e-12, abs_tol=1e-9)):
        raise ValueError(f'{path}: COM sample disagrees with origin/cadence/time metadata')


def validate_frame(metadata, path, step, time, ids):
    if metadata['version'] == 2 and list(ids) != metadata['molecule_ids']:
        raise ValueError(f'{path}: COM frame disagrees with molecule metadata')
    _validate_step_time(metadata, path, step, time)


def validate_sample(metadata, path, step, time, molecule, position):
    if molecule <= 0 or not all(math.isfinite(v) for v in (time, *position)):
        raise ValueError(f'{path}: nonfinite COM sample or invalid molecule ID')
    if metadata['version'] == 2:
        ids = metadata['molecule_ids']
        index = bisect.bisect_left(ids, molecule)
        if index == len(ids) or ids[index] != molecule:
            raise ValueError(f'{path}: COM molecule is absent from metadata')
    _validate_step_time(metadata, path, step, time)


def validate_step_spacing(metadata, path, steps):
    if metadata['version'] == 2 and any(b - a != metadata['cadence_steps']
                                        for a, b in zip(steps, steps[1:])):
        raise ValueError(f'{path}: missing or reordered COM sampling frames')
