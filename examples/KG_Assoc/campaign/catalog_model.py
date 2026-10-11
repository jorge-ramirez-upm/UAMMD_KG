"""Read-only metadata adapters. No simulation runner or payload validator is called."""
import hashlib
import json
import re
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from kg_assoc_campaign import campaign_systems, e2_bank_id, geometry_id

SCHEMA_VERSION = 1
MAX_METADATA_BYTES = 4 * 1024 * 1024
METADATA_NAMES = {
    'manifest.json', 'system.json', 'command.json', 'numerical_validation.json',
    'validation.json', 'active_states.json', 'plan.json', 'approval.json',
    'started.json', 'environment.json', 'complete.json', 'incomplete.json',
    'status.json', 'request.json', 'report.json', 'failed.json', 'run.json',
    'run.complete.json', 'analysis.json', 'analysis_config.json', 'summary.json',
    'review_complete.json', 'initial.lammpsdat.validation.json',
    'requirements.example.json', 'integrity_manifest.json', 'results.json',
    'runtime_checks.json', 'inventory.json', 'FINAL_MANIFEST.json', 'integrity.json',
    'pbc_candidates.json', 'e1_integrity.json', 'launch_plan.json',
}
C1_BANK = 'F04_N010_RP080_EE08'


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def discover(script=None):
    repository = Path(script or __file__).resolve().parents[3]
    return repository, repository / 'examples/KG_Assoc/kg_assoc_100m'


def git_sha(repository):
    try:
        return subprocess.check_output(
            ['git', '-C', str(repository), 'rev-parse', 'HEAD'],
            stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


class Reader:
    """Bounded stable JSON reads, exact declared-root relocation, stat-only payloads."""
    def __init__(self, repository, dataset):
        self.repository = Path(repository).resolve()
        self.dataset = Path(dataset).resolve()
        self.aliases = {}
        self.records = {}
        self.issues = []
        self.references = []

    def issue(self, code, source, detail):
        self.issues.append(dict(code=code, source=str(source), detail=str(detail)))

    def key(self, path):
        path = Path(path)
        if path.is_relative_to(self.dataset):
            return 'dataset:' + path.relative_to(self.dataset).as_posix()
        return 'repository:' + path.relative_to(self.repository).as_posix()

    def resolve(self, value):
        if not isinstance(value, str) or not value:
            return None
        path = Path(value)
        if '..' in path.parts:
            return None
        if path.is_absolute():
            for old, new in sorted(self.aliases.items(), key=lambda x: -len(str(x[0]))):
                if path.is_relative_to(old):
                    path = new / path.relative_to(old)
                    break
        elif value.startswith('examples/'):
            path = self.repository / path
        else:
            path = self.dataset / path
        resolved = path.resolve()
        if resolved.is_relative_to(self.dataset) or resolved.is_relative_to(self.repository):
            return resolved
        return None

    def read(self, path, adapter='metadata-v1'):
        path = Path(path)
        safe = self.resolve(str(path))
        if safe is None:
            self.issue('unsafe_reference', path, 'Outside trusted roots or traversal/symlink escape')
            return None
        key = self.key(safe)
        if key in self.records:
            return self.records[key]
        if not safe.exists():
            return None
        try:
            for _ in range(2):
                before = safe.stat()
                if before.st_size > MAX_METADATA_BYTES or not safe.is_file():
                    raise ValueError('Oversize or non-file metadata')
                with safe.open('rb') as stream:
                    payload = stream.read(MAX_METADATA_BYTES + 1)
                after = safe.stat()
                token = lambda s: (s.st_size, s.st_mtime_ns, s.st_ino)
                if token(before) == token(after) and len(payload) <= MAX_METADATA_BYTES:
                    break
            else:
                raise ValueError('Metadata changed during both bounded reads')
            value = json.loads(payload, parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError('Non-finite JSON number: ' + value)))
            original_array = None
            if isinstance(value, list) and safe.name in ('runtime_checks.json', 'pbc_candidates.json'):
                original_array = value
                value = {'legacy_array_rows': value}
                adapter = 'legacy-diagnostic-array-v1'
            if not isinstance(value, dict):
                raise ValueError('Metadata root must be an object or supported legacy diagnostic array')
            record = dict(id=key, path=str(safe), adapter=adapter, data=value,
                          sha256=hashlib.sha256(payload).hexdigest(),
                          stat=dict(size=after.st_size, mtime_ns=after.st_mtime_ns),
                          supported=value.get('schema_version', 1) == 1)
            if original_array is not None:
                record['original_data'] = original_array
            self.records[key] = record
            if not record['supported']:
                self.issue('unsupported_schema', key, value.get('schema_version'))
            return record
        except (OSError, ValueError, RecursionError) as error:
            self.issue('unreadable_metadata', key, error)
            return None

    def reference(self, value, digest=None, source=None):
        path = self.resolve(value)
        item = dict(original=value, source=source, declared_sha256=digest,
                    path=str(path) if path else None, verification='payload_deferred')
        if path is None:
            item['integrity'] = 'outside_available_scope'
        else:
            try:
                stat = path.stat()
                item.update(exists=True, size=stat.st_size, mtime_ns=stat.st_mtime_ns,
                            integrity='present_payload_deferred')
                metadata = self.records.get(self.key(path))
                if metadata and digest:
                    item['verification'] = 'metadata_hash_checked'
                    item['integrity'] = ('metadata_consistent' if metadata['sha256'] == digest
                                         else 'changed_metadata')
            except OSError:
                item.update(exists=False, integrity='missing')
        if item['integrity'] in ('missing', 'outside_available_scope', 'changed_metadata'):
            self.issue(item['integrity'], source, value)
        self.references.append(item)
        return item

    def hash_map(self, values, source, relative_to=None):
        if isinstance(values, dict):
            for path, digest in values.items():
                if isinstance(digest, str) and len(digest) == 64:
                    target = str(relative_to / path) if relative_to and not Path(path).is_absolute() and not path.startswith('examples/') and not path.startswith('banks/') else path
                    item = self.reference(target, digest, source)
                    item['original'] = path


def numerical(record):
    if not record:
        return 'absent'
    validation = record.get('validation', record.get('numerical_validation', record))
    value = validation.get('numerical_status', validation.get('status'))
    if value in ('valid', 'validated', 'accepted'):
        return 'recorded_pass'
    if value in ('invalid', 'failed'):
        return 'recorded_failure'
    # Legacy corrected-C1 receipt stores numerical metrics without a status field.
    if record.get('status') == 'validated' and record.get('numerical_validation'):
        return 'recorded_pass'
    return 'absent'


def execution(complete, failed, started, command=None):
    if complete and failed:
        return 'conflicting_evidence'
    if failed:
        return 'failed_receipt'
    if complete:
        return 'completed_receipt'
    if started or (command or {}).get('status') == 'running':
        return 'started_liveness_unknown'
    if (command or {}).get('status') in ('finished', 'complete'):
        return 'completed_receipt'
    if (command or {}).get('status') in ('incomplete', 'invalid', 'failed'):
        return 'failed_receipt'
    return 'planned'


class Catalog:
    """Version-one adapters retain original records beside their normalized projection."""
    def __init__(self, repository, dataset, registry=None):
        self.reader = Reader(repository, dataset)
        self.registry_request = registry
        self.graph = dict(schema_version=SCHEMA_VERSION, reader_version='metadata-adapters-v1',
                          scan_started_at=utcnow(), generator_git_sha=git_sha(repository),
                          observation_host=socket.gethostname(), dataset_root=str(dataset),
                          expected_campaign_branch='KremerGrest',
                          scope='local_metadata_only; remote liveness not inspected',
                          payload_authentication='deferred', attempts=[], reviews=[],
                          acceptances=[], histories=[], systems=[], selections=[])

    def adapt(self, method, *args):
        try:
            method(*args)
        except (KeyError, TypeError, ValueError, AttributeError, IndexError) as error:
            self.reader.issue('invalid_adapter_record', str(args[0].get('id', method.__name__))
                              if args and isinstance(args[0], dict) else method.__name__, error)

    def get(self, path):
        record = self.reader.read(self.reader.dataset / path)
        return record['data'] if record and record['supported'] else {}

    def scan(self):
        r = self.reader
        inventory_path = r.repository / 'examples/KG_Assoc/campaign/e2_remaining_inventory_20261011.json'
        inventory_record = r.read(inventory_path, 'frozen-inventory-v1')
        inventory = inventory_record['data'] if inventory_record else {}
        # Plans explicitly declare their original dataset root; no basename guessing.
        plan_paths = sorted(r.dataset.glob('banks/e2_attempts/*/*/plan.json'))
        plan_paths += sorted(r.dataset.glob('banks/e2_extensions/*/plan.json'))
        for path in plan_paths:
            record = r.read(path, 'e2-plan-v1')
            if record:
                original = record['data'].get('dataset_root')
                if original and Path(original).is_absolute():
                    r.aliases[Path(original)] = r.dataset
                    suffix = Path('examples/KG_Assoc/kg_assoc_100m')
                    old = Path(original)
                    if old.parts[-len(suffix.parts):] == suffix.parts:
                        r.aliases[old.parents[2]] = r.repository
        # Legacy records use this campaign's repository-qualified dataset path.
        for path in sorted(r.dataset.glob('banks/e2_extensions/*/plan.json')):
            record = r.read(path)
            for command in (record or {}).get('data', {}).get('commands', []):
                if '--output' in command:
                    output = Path(command[command.index('--output') + 1])
                    marker = 'examples/KG_Assoc/kg_assoc_100m'
                    if marker in str(output):
                        root = str(output).split(marker, 1)[0] + marker
                        r.aliases[Path(root)] = r.dataset
        for base in ('inputs', 'banks', 'builds', 'aggregate', 'systems'):
            # JSON discovery only; never open simulation logs, frames, states or events.
            for path in sorted((r.dataset / base).glob('**/*.json')):
                if (path.name in METADATA_NAMES or
                    base == 'aggregate' and re.fullmatch(r'(?:F[0-9]{2}_N[0-9]{3}_RP[0-9]{3}_)?r[0-9]{3}(?:_summary)?\.json|failure_[a-f0-9]+\.json', path.name) or
                    base == 'banks' and path.parent.name in ('e2_registry', 'e2_acceptance')):
                    r.read(path)
        r.read(r.dataset / 'manifest.json', 'campaign-manifest-v1')
        systems = campaign_systems()
        known = {s['system_id'] for s in systems}
        manifest = self.get('manifest.json')
        if manifest and set(manifest.get('systems', [])) != known:
            r.issue('campaign_coverage_mismatch', 'manifest.json', 'Expected all 23 protocol conditions')
        for path in (r.dataset / 'systems').glob('*/system.json'):
            if path.parent.name not in known:
                r.issue('unexpected_condition', path, path.parent.name)
        for system in systems:
            sid = system['system_id']
            geometry = geometry_id(system)
            bank = e2_bank_id(system)
            record = self.get(f'systems/{sid}/system.json')
            if record:
                for field in ('f', 'N', 'rho_p', 'Ee', 'Ea', 'associating', 'dt', 'temperature'):
                    if field in record and record[field] != system[field]:
                        r.issue('condition_mismatch', f'systems/{sid}/system.json', field)
            self.graph['systems'].append(dict(
                system_id=sid, parameters=system, geometry=geometry, bank=bank,
                role='associating' if bank else 'control',
                Ee=str(system['Ee']) if bank else 'not_applicable',
                target_Ea=str(system['Ea']) if bank else 'not_applicable',
                numerical='absent', scientific='absent' if bank else 'E1_acceptance_unknown',
                selection='missing' if bank else 'E2_not_applicable',
                production_authorization='absent', production_eligibility='unknown_payload_deferred',
                documented_decision=None, execution='not_available_here', smoke='absent',
                integrity='payload_deferred'))
        active = self.get('banks/e1/active_states.json')
        pins = {(p['geometry'], p['replica']): p for p in inventory.get('e1_states', [])}
        for system in self.graph['systems']:
            for replica in (1, 2, 3):
                geometry = system['geometry']
                selected = active.get(f'{geometry}/r{replica:03d}',
                                      f'banks/e1/{geometry}/r{replica:03d}')
                pin = pins.get((geometry, replica), {})
                snapshot = selected + '/state.e1.lammpsdat'
                if pin and pin.get('path') != snapshot:
                    r.issue('E1_selection_inventory_mismatch', selected, pin.get('path'))
                self.graph['histories'].append(dict(
                    id=f"{system['system_id']}/r{replica:03d}", system_id=system['system_id'],
                    replica=replica, selected_e1=selected, e1_snapshot=snapshot,
                    e1_sha256=pin.get('sha256'), e1_scientific='review_required',
                    e1_selection_source='active_states.json' if f'{geometry}/r{replica:03d}' in active
                    else 'original_fallback', attempts=[]))
        selected_e1_refs = {}
        for history in self.graph['histories']:
            snapshot = history['e1_snapshot']
            if snapshot not in selected_e1_refs:
                selected_e1_refs[snapshot] = r.reference(snapshot, history['e1_sha256'], 'E1_selection_inventory')
        self.adapt(self.e1_attempts)
        for path in plan_paths:
            record = r.read(path)
            if record and record['supported']:
                if record['data'].get('stage') == 'E2-G1':
                    self.adapt(self.generalized, record)
                elif 'absolute_start_step' in record['data']:
                    self.adapt(self.recovery, record, inventory)
                else:
                    r.issue('unsupported_adapter', record['id'], 'Unrecognized E2 plan')
        self.adapt(self.historical, inventory)
        self.adapt(self.production)
        self.adapt(self.reviews)
        self.lineage()
        self.registry_views = []
        self.selected_registry = None
        self.registries()
        # Authenticate only previously recognized, bounded metadata; payloads stay deferred.
        for record in list(r.records.values()):
            data = record['data']
            for field in ('input_sha256', 'output_sha256', 'evidence_sha256', 'source_sha256',
                          'sha256', 'report_sha256', 'fresh_smoke_sha256', 'parent_sha256', 'files_sha256'):
                r.hash_map(data.get(field), record['id'],
                           Path(record['path']).parent if field in ('input_sha256', 'output_sha256', 'files_sha256') else None)
        for attempt in self.graph['attempts']:
            sources = {attempt['source'], attempt['id'], attempt.get('completion')}
            issues = [i for i in r.issues if i['source'] in sources]
            attempt['integrity'] = 'metadata_issues_payload_deferred' if issues else 'metadata_consistent_payload_deferred'
            attempt['selection'] = 'unselected_or_unregistered'
            if attempt['role'] == 'E1':
                if any(r.resolve(h['e1_snapshot']) == r.resolve(attempt['output_prefix'])
                       for h in self.graph['histories']):
                    attempt['selection'] = 'selected_E1_not_scientific_acceptance'
            attempt['step_units'] = 'production_stage_MD_steps' if attempt['role'] == 'production' else 'absolute_MD_steps'
        for replacement in self.graph['attempts']:
            supersedes = replacement.get('supersedes')
            for older in self.graph['attempts']:
                if supersedes in (older['id'], older['source']) and supersedes is not None:
                    older['selection'] = 'superseded_by_explicit_relationship'
                    older['superseded_by'] = replacement['id']
        for system in self.graph['systems']:
            attempts = [a for a in self.graph['attempts'] if system['system_id'] in a['systems']]
            ordinary = [a for a in attempts if a['role'] in ('E2', 'corrected_C1_8M')]
            system['smoke'] = ('recorded_pass' if any(a['role'] == 'smoke' and
                a['numerical'] == 'recorded_pass' for a in attempts) else 'absent')
            if any(a['integrity'] == 'metadata_issues_payload_deferred' for a in attempts):
                system['integrity'] = 'metadata_issues_payload_deferred'
            if system['bank'] and system['selection'] != 'selected_metadata_payload_deferred':
                system['production_eligibility'] = 'blocked_missing_or_invalid_registered_selection'
            if not system['bank']:
                system.update(smoke='not_applicable', execution='E2_not_applicable')
            elif ordinary:
                counts = {state: sum(a['execution'] == state for a in ordinary)
                          for state in sorted({a['execution'] for a in ordinary})}
                system['execution'] = ', '.join(f'{v} {k}' for k, v in counts.items())
                system['numerical'] = ('recorded_pass' if all(a['numerical'] == 'recorded_pass'
                                       for a in ordinary) else 'mixed_or_absent')
                if system['scientific'] == 'absent':
                    system['scientific'] = 'review_required'
            if system['bank'] == C1_BANK and inventory.get('C1_recovery'):
                system['documented_decision'] = dict(
                    status='documented_qualified_decision', source=inventory_record['id'],
                    qualification=[p.get('user_review_status') for p in inventory['C1_recovery']])
            for history in self.graph['histories']:
                if history['system_id'] == system['system_id']:
                    history['attempts'] = [a['id'] for a in attempts if a['replica'] == history['replica']]
        self.graph.update(records=list(r.records.values()), references=r.references, diagnostics=r.issues,
                          scan_finished_at=utcnow(), registry_views=self.registry_views,
                          selected_registry=self.selected_registry,
                          coverage=dict(expected_conditions=23, history_slots=69,
                              unique_selected_e1=len({h['selected_e1'] for h in self.graph['histories']}),
                              available_selected_e1=sum(ref.get('exists', False) for ref in selected_e1_refs.values()),
                              dataset_available=r.dataset.is_dir(), metadata_records=len(r.records),
                              newest_metadata_mtime_ns=max((p['stat']['mtime_ns'] for p in r.records.values()), default=None),
                              freshness='non_atomic_local_observation; remote scope unknown',
                              missing_system_records=sum(not self.get(f"systems/{s['system_id']}/system.json")
                                                         for s in self.graph['systems'])))
        return self.graph

    def add_attempt(self, record, role, replica, systems, **fields):
        data = record['data']
        attempt = dict(id=f"{role}:{record['id']}:{record['sha256'][:12]}:r{replica:03d}",
                       source=record['id'], role=role, replica=replica, systems=systems,
                       execution='planned', numerical='absent', scientific='review_required',
                       authorization='absent', integrity='payload_deferred', parent=None,
                       supersedes=data.get('supersedes'),
                       output_prefix=None, start_step=None, end_step=None, chemistry_seed=None,
                       md_seed=None, effective_md_seed=None, physics={},
                       git_sha=data.get('git_sha'), executable_sha256=data.get('executable_sha256'),
                       timestamps={k: data[k] for k in ('prepared_at', 'started_at', 'finished_at') if k in data})
        attempt.update(fields)
        if role == 'smoke':
            attempt['scientific'] = 'not_applicable_for_equilibrium'
        if role == 'historical_pbc_defective_6M':
            attempt['scientific'] = 'historically_defective_not_eligible'
        self.graph['attempts'].append(attempt)
        return attempt

    def matching(self, bank=None, geometry=None):
        return [s['system_id'] for s in self.graph['systems']
                if (bank is not None and s['bank'] == bank) or
                   (geometry is not None and s['geometry'] == geometry)]

    def e1_attempts(self):
        for record in list(self.reader.records.values()):
            path = Path(record['path'])
            if path.name != 'command.json' or not any(
                    part in path.parts for part in ('e1', 'e1_retries')):
                continue
            data = record['data']
            if not record['supported']:
                continue
            relative = path.relative_to(self.reader.dataset)
            geometry = relative.parts[2]
            replica = data.get('replica', next((int(p[1:]) for p in relative.parts if
                                              p.startswith('r') and p[1:].isdigit()), 0))
            validation = self.get(str(relative.parent / 'numerical_validation.json'))
            self.add_attempt(record, 'E1', replica, self.matching(geometry=geometry),
                execution=execution(None, None, None, data), numerical=numerical(validation),
                md_seed=data.get('seed'), output_prefix=str(path.parent / 'state.e1.lammpsdat'),
                authorization='legacy_execution_evidence')

    def generalized(self, record):
        r = self.reader
        plan = record['data']
        directory = Path(record['path']).parent
        sid = plan.get('system', {}).get('system_id')
        expected_system = next((s['parameters'] for s in self.graph['systems'] if s['system_id'] == sid), None)
        if not expected_system:
            r.issue('unknown_plan_condition', record['id'], sid)
        else:
            for field in ('f', 'N', 'rho_p', 'Ee', 'dt', 'temperature'):
                if plan.get('system', {}).get(field) != expected_system[field]:
                    r.issue('plan_condition_mismatch', record['id'], field)
        approval = r.read(directory / 'approval.json')
        approved = bool(approval and approval['supported'] and approval['data'].get('approved') is True
                        and approval['data'].get('plan_sha256') == record['sha256']
                        and approval['data'].get('purpose') == ('e2_smoke' if plan.get('smoke') else 'e2_segment'))
        if approval and not approved:
            r.issue('authorization_mismatch', approval['id'], 'Approval not bound to this plan')
        histories = plan.get('histories', [])
        if [h.get('replica') for h in histories] != [1, 2, 3]:
            r.issue('replica_coverage', record['id'], 'Expected exactly replicas 1,2,3')
        for history in histories:
            replica = history.get('replica', 0)
            base = directory / f'r{replica:03d}'
            complete_record = r.read(base / 'complete.json')
            complete = complete_record['data'] if complete_record and complete_record['supported'] else {}
            failed = self.get(str(base.relative_to(r.dataset) / 'incomplete.json'))
            started = self.get(str(base.relative_to(r.dataset) / 'started.json'))
            valid_binding = complete.get('plan_sha256') == record['sha256']
            if complete and (not valid_binding or complete.get('end_step') != history.get('end_step')):
                r.issue('completion_plan_mismatch', record['id'], replica)
            num = numerical(complete)
            if complete and (not valid_binding or complete.get('end_step') != history.get('end_step')):
                num = 'stale_mismatched'
            if started and started.get('plan_sha256') != record['sha256']:
                r.issue('start_plan_mismatch', record['id'], replica)
            physics = history.get('physics', {})
            system = plan.get('system', {})
            for pfield, sfield in [('arms', 'f'), ('narm', 'N'), ('Ee', 'Ee'), ('dt', 'dt'),
                                   ('temperature', 'temperature')]:
                if physics.get(pfield) != system.get(sfield):
                    r.issue('physics_mismatch', record['id'], pfield)
            self.add_attempt(record, 'smoke' if plan.get('smoke') is True else 'E2', replica,
                [sid] if sid else [], execution=execution(complete, failed, started), numerical=num,
                authorization='plan_bound_recorded' if approved else 'absent_or_mismatched',
                parent=history.get('parent'), output_prefix=history.get('output_prefix'),
                start_step=history.get('start_step'), end_step=history.get('end_step'),
                chemistry_seed=history.get('chemistry_seed'), md_seed=history.get('md_seed'),
                effective_md_seed=history.get('effective_md_seed'), physics=physics,
                preparation_Ea=physics.get('Ea'), parent_Ea=history.get('parent_Ea'),
                source_sha256=plan.get('source_sha256'), build=plan.get('build'),
                completion=complete_record['id'] if complete_record else None,
                completion_data=complete, started=started, failure=failed,
                parent_attempt=plan.get('parent_attempt'), segment_index=plan.get('segment_index'))
            switch_from = history.get('parent_Ea')
            if switch_from != physics.get('Ea'):
                command = history.get('command', [])
                options = {command[i]: command[i + 1] for i in range(len(command) - 1)
                           if command[i].startswith('--')}
                if (options.get('--switch-ea-from') != str(switch_from) or
                    options.get('--Ea') != str(physics.get('Ea'))):
                    r.issue('Ea_switch_not_explicit', record['id'], replica)
            if history.get('end_step', 0) - history.get('start_step', 0) != plan.get('steps'):
                r.issue('segment_length_mismatch', record['id'], replica)
            parent = history.get('parent', {})
            if parent.get('snapshot'):
                r.reference(parent['snapshot'], source=record['id'])
                selected_history = next((h for h in self.graph['histories'] if
                    h['system_id'] == sid and h['replica'] == replica), None)
                if parent.get('kind') == 'e1' and selected_history and r.resolve(parent['snapshot']) != r.resolve(selected_history['e1_snapshot']):
                    r.issue('E1_parent_not_selected', record['id'], replica)
            if parent.get('prefix'):
                r.reference(parent['prefix'] + '.assoc_restart', source=record['id'])
            r.hash_map(history.get('parent', {}).get('sha256'), record['id'])

    def recovery(self, record, inventory):
        plan = record['data']
        directory = Path(record['path']).parent
        pinned = {p['prefix'] for p in inventory.get('C1_recovery', [])}
        for replica, command in enumerate(plan.get('commands', []), 1):
            options = {command[i]: command[i + 1] for i in range(len(command) - 1)
                       if command[i].startswith('--')}
            prefix = options.get('--output')
            resolved = self.reader.resolve(prefix)
            canonical = str(resolved.relative_to(self.reader.dataset)) if resolved else None
            corrected = canonical in pinned
            complete = self.get(str(directory.relative_to(self.reader.dataset) / f'r{replica:03d}/status.json'))
            self.add_attempt(record, 'corrected_C1_8M' if corrected else 'recovery_check', replica,
                self.matching(bank=C1_BANK), execution=execution(
                    complete if complete.get('status') == 'validated' else None,
                    complete if complete.get('status') in ('failed', 'incomplete') else None,
                    complete if complete.get('status') == 'running' else None),
                numerical=numerical(complete), parent=dict(kind='e2', prefix=options.get('--restart-prefix')),
                output_prefix=prefix, start_step=plan.get('absolute_start_step'),
                end_step=plan.get('absolute_end_step'),
                chemistry_seed=int(options['--seed']) if '--seed' in options else None,
                md_seed=int(options['--md-seed']) if '--md-seed' in options else None,
                completion_data=complete, authorization='legacy_execution_evidence',
                scientific='documented_qualified_decision' if corrected else 'review_required')

    def historical(self, inventory):
        pins = inventory.get('preserved_files', {})
        for record in list(self.reader.records.values()):
            path = Path(record['path'])
            if path.name != 'command.json' or 'e2' not in path.parts or not record['supported']:
                continue
            data = record['data']
            bank = path.parent.parent.name
            replica = data.get('replica', 0)
            relative = path.relative_to(self.reader.dataset).as_posix()
            pinned = any(relative.removesuffix('command.json') in p for p in pins)
            defective = bank == C1_BANK and data.get('completed_e2_steps') == 6000000 and pinned
            self.add_attempt(record, 'historical_pbc_defective_6M' if defective else 'legacy_E2',
                replica, self.matching(bank=bank), execution=execution(None, None, None, data),
                numerical=numerical(self.get(str(path.parent.relative_to(self.reader.dataset) /
                                                     'numerical_validation.json'))),
                parent=dict(kind='e1', snapshot=data.get('parent_e1')),
                output_prefix=str(path.parent / 'state'), start_step=data.get('e2_start_step'),
                end_step=data.get('completed_e2_steps'), chemistry_seed=data.get('chemistry_seed'),
                md_seed=data.get('md_seed'), authorization='legacy_execution_evidence')

    def production(self):
        for record in list(self.reader.records.values()):
            path = Path(record['path'])
            if path.name != 'run.json' or 'production' not in path.parts or not record['supported']:
                continue
            data = record['data']
            self.add_attempt(record, 'production', data.get('replica', 0), [data.get('system_id')],
                execution=execution(data if data.get('status') == 'complete' else None,
                    data if data.get('status') in ('invalid', 'incomplete') else None,
                    data if data.get('status') == 'running' else None),
                numerical=numerical(data), scientific='initialization_acceptance_separate',
                parent=dict(e1=data.get('parent_e1'), e2=data.get('parent_e2')),
                md_seed=data.get('md_seed'), chemistry_seed=data.get('chemistry_seed'),
                end_step=data.get('completed_production_steps'), active_e2=data.get('active_e2'),
                authorization='legacy_execution_evidence_no_launch_receipt')

    def reviews(self):
        for record in list(self.reader.records.values()):
            path = Path(record['path'])
            if path.name not in ('review_complete.json', 'analysis.json', 'manifest.json', 'results.json',
                                 'FINAL_MANIFEST.json', 'summary.json') and not re.fullmatch(
                                 r'(?:F[0-9]{2}_N[0-9]{3}_RP[0-9]{3}_)?r[0-9]{3}(?:_summary)?\.json', path.name):
                continue
            if 'aggregate' not in path.parts and 'analysis' not in path.parts:
                continue
            if (record['data'].get('status') == 'short_numerical_validation_passed_not_equilibrated'
                and record['data'].get('md_steps_per_replica', 10001) <= 10000):
                for replica in (1, 2, 3):
                    validation = self.get(str(path.parent.relative_to(self.reader.dataset) / f'r{replica:03d}/validation.json'))
                    self.add_attempt(record, 'smoke', replica, self.matching(bank=C1_BANK),
                        execution='completed_receipt', numerical='recorded_pass',
                        end_step=record['data'].get('md_steps_per_replica'),
                        authorization='legacy_execution_evidence', completion_data=validation,
                        output_prefix=str(path.parent / f'r{replica:03d}/state'))
            config = self.get(str(path.parent.relative_to(self.reader.dataset) / 'analysis_config.json'))
            if config.get('attempt'):
                target = self.reader.resolve(config['attempt'])
                attempts = [a['id'] for a in self.graph['attempts'] if target and
                            Path(self.reader.records[a['source']]['path']).parent == target]
                self.graph['reviews'].append(dict(source=record['id'], attempts=attempts,
                    scientific='review_required', automatic_acceptance=False,
                    window_steps=config.get('window_steps'), data=record['data'],
                    links=[str(p) for p in sorted(path.parent.glob('*.md'))] +
                          [str(p) for p in sorted(path.parent.glob('*.json')) if p.name in METADATA_NAMES] +
                          [str(p) for p in sorted(path.parent.glob('figures/*')) if p.is_file()]))
                self.reader.hash_map(config.get('source_sha256'), record['id'])
                target_plan = self.reader.records.get(self.reader.key(target / 'plan.json')) if target else None
                if (not target_plan or target_plan['sha256'] != config.get('plan_sha256') or
                    'plan_sha256' in record['data'] and record['data']['plan_sha256'] != config.get('plan_sha256')):
                    self.reader.issue('review_binding_mismatch', record['id'], 'Plan hash differs')
            else:
                data = record['data']
                snapshot = data.get('snapshot', {})
                snapshot_path = self.reader.resolve(snapshot.get('path')) if isinstance(snapshot, dict) else None
                command_bank = data.get('command', {}).get('bank') if isinstance(data.get('command'), dict) else None
                command_path = self.reader.resolve(command_bank) if command_bank else None
                matches = []
                for attempt in self.graph['attempts']:
                    output = self.reader.resolve(attempt.get('output_prefix'))
                    if (snapshot_path and output == snapshot_path or
                        command_path and output and output.parent == command_path or
                        'corrected' in data and 'defective' in data and
                        attempt['role'] in ('corrected_C1_8M', 'historical_pbc_defective_6M') and
                        attempt['replica'] == data.get('replica')):
                        matches.append(attempt['id'])
                self.graph['reviews'].append(dict(source=record['id'], attempts=matches,
                    scientific='diagnostic_not_acceptance', data=data,
                    association_scope='legacy_structural_match; not authenticated lineage',
                    links=[str(path)] + [str(p) for p in sorted(path.parent.glob('*.md'))] +
                          [str(p) for p in sorted(path.parent.glob('*.png'))]))

    def lineage(self):
        r = self.reader
        outputs = {}
        for attempt in self.graph['attempts']:
            prefix = r.resolve(attempt.get('output_prefix'))
            if prefix:
                outputs[str(prefix)] = attempt
        children = {}
        seed_roots = {}
        for attempt in self.graph['attempts']:
            parent = attempt.get('parent') or {}
            parent_path = r.resolve(parent.get('prefix') or parent.get('snapshot'))
            predecessor = outputs.get(str(parent_path)) if parent_path else None
            attempt['parent_segment'] = predecessor['id'] if predecessor else None
            if predecessor:
                children.setdefault(predecessor['id'], []).append(attempt['id'])
                if attempt['role'] == 'E2' and parent.get('kind') == 'e2':
                    if attempt['start_step'] != predecessor['end_step']:
                        r.issue('step_discontinuity', attempt['id'], predecessor['id'])
                    if attempt['chemistry_seed'] != predecessor['chemistry_seed']:
                        r.issue('chemical_rng_changed', attempt['id'], predecessor['id'])
                    if attempt['md_seed'] == predecessor['md_seed']:
                        r.issue('MD_seed_not_reseeded', attempt['id'], predecessor['id'])
                    if attempt['replica'] != predecessor['replica']:
                        r.issue('replica_lineage_mismatch', attempt['id'], predecessor['id'])
                    for field in ('arms', 'narm', 'Ee', 'dt', 'temperature'):
                        if predecessor['physics'] and attempt['physics'].get(field) != predecessor['physics'].get(field):
                            r.issue('restart_physics_mismatch', attempt['id'], field)
            elif parent.get('kind') == 'e2':
                r.issue('unresolved_parent_segment', attempt['id'], parent)
            if attempt['role'] == 'E2' and parent.get('kind') != 'e2':
                key = attempt['chemistry_seed']
                if key is None:
                    r.issue('missing_chemical_seed', attempt['id'], 'No seed recorded')
                elif key in seed_roots:
                    r.issue('chemical_seed_collision', attempt['id'], seed_roots[key])
                seed_roots[key] = attempt['id']
            if attempt['role'] == 'E2' and parent.get('kind') == 'e1' and attempt['start_step'] != 0:
                r.issue('E1_start_not_zero', attempt['id'], attempt['start_step'])
            if attempt['role'] in ('E2', 'smoke') and attempt.get('parent_Ea') != attempt.get('preparation_Ea'):
                attempt['parameter_switch'] = dict(parent_Ea=attempt.get('parent_Ea'),
                    preparation_Ea=attempt.get('preparation_Ea'), authentication='payload_deferred')
            visited = set()
            cursor = attempt
            while cursor and cursor['id'] not in visited:
                visited.add(cursor['id'])
                p = r.resolve((cursor.get('parent') or {}).get('prefix'))
                cursor = outputs.get(str(p)) if p else None
            if cursor:
                r.issue('lineage_cycle', attempt['id'], cursor['id'])
        for attempt in self.graph['attempts']:
            started_at = attempt.get('started', {}).get('started_at')
            if attempt['execution'] == 'started_liveness_unknown' and started_at:
                try:
                    age = (datetime.now(timezone.utc) - datetime.fromisoformat(started_at)).total_seconds()
                    if age > 86400:
                        r.issue('stale_candidate_liveness_unknown', attempt['id'],
                                'Start receipt over 24h old; remote liveness is unknown, not failed')
                except (ValueError, TypeError):
                    r.issue('invalid_timestamp', attempt['id'], started_at)
        for parent, branches in children.items():
            if len(branches) > 1:
                r.issue('lineage_fork', parent, ', '.join(branches))

    def registries(self):
        r = self.reader
        records = list(r.records.values())
        registries = [p for p in records if p['data'].get('stage') == 'E2_active_registry']
        acceptances = [p for p in records if p['data'].get('stage') == 'E2_acceptance']
        self.registry_views = [p['id'] for p in registries]
        self.selected_registry = None
        if self.registry_request:
            path = r.resolve(self.registry_request)
            self.selected_registry = next((p['id'] for p in registries if str(path) == p['path']), None)
            if not self.selected_registry:
                raise ValueError('Registry view not found: ' + self.registry_request)
        elif len(registries) == 1:
            self.selected_registry = registries[0]['id']
        elif len(registries) > 1:
            r.issue('ambiguous_registry', 'banks/e2_registry', 'Select a view with --registry PATH')
        for record in acceptances:
            data = record['data']
            problems = []
            required = {'schema_version', 'stage', 'bank_id', 'provenance_kind', 'status', 'reviewer',
                        'reviewed_at', 'evidence', 'evidence_sha256', 'source_plan', 'source_plan_sha256',
                        'histories', 'permitted_use', 'permitted_systems', 'qualification',
                        'numerical_qualification', 'publisher_git_sha'}
            if not record['supported'] or not required <= data.keys():
                problems.append('incomplete_or_unsupported_schema')
            histories = data.get('histories', [])
            if not isinstance(histories, list) or not all(isinstance(h, dict) for h in histories):
                r.issue('invalid_acceptance_histories', record['id'], 'Histories must be objects')
                continue
            if not all(isinstance(data.get(field), str) and data[field].strip()
                       for field in ('reviewer', 'reviewed_at', 'numerical_qualification')):
                problems.append('reviewer_or_qualification_absent')
            if [h.get('replica') for h in histories] != [1, 2, 3]:
                problems.append('missing_three_histories')
            if data.get('status') not in ('accepted', 'accepted_with_qualification'):
                problems.append('not_accepted')
            if data.get('permitted_use') != 'production_initial_state':
                problems.append('invalid_permitted_use')
            plan_path = r.resolve(data.get('source_plan'))
            source_plan = r.records.get(r.key(plan_path)) if plan_path else None
            if not source_plan or source_plan['sha256'] != data.get('source_plan_sha256'):
                problems.append('source_plan_mismatch')
            if source_plan and source_plan['data'].get('smoke') is True:
                problems.append('smoke_cannot_be_accepted')
            evidence = r.reference(data.get('evidence'), data.get('evidence_sha256'), record['id'])
            if evidence['integrity'] in ('missing', 'outside_available_scope', 'changed_metadata'):
                problems.append('missing_or_changed_review_evidence')
            for history in histories:
                prefix = history.get('prefix', '')
                if '/banks/e2/' + C1_BANK + '/' in '/' + prefix:
                    problems.append('historical_defective_parent')
                match = [a for a in self.graph['attempts'] if
                         r.resolve(a['output_prefix']) == r.resolve(prefix) and
                         a['replica'] == history.get('replica') and
                         a['end_step'] == history.get('end_step') and
                         a['chemistry_seed'] == history.get('chemistry_seed') and
                         a['role'] == ('corrected_C1_8M' if data.get('provenance_kind') == 'corrected_C1_8M' else 'E2') and
                         source_plan and a['source'] == source_plan['id'] and
                         a['numerical'] == 'recorded_pass']
                if not match:
                    problems.append('accepted_endpoint_mismatch')
                receipt_name = 'status.json' if data.get('provenance_kind') == 'corrected_C1_8M' else 'complete.json'
                receipt_path = str(Path(prefix).parent / receipt_name)
                if receipt_path not in history.get('sha256', {}):
                    problems.append('accepted_completion_hash_absent')
                if match and match[0]['physics'] and match[0]['physics'] != history.get('physics'):
                    problems.append('accepted_physics_mismatch')
                for value, digest in history.get('sha256', {}).items():
                    reference = r.reference(value, digest, record['id'])
                    if reference['integrity'] in ('missing', 'outside_available_scope', 'changed_metadata'):
                        problems.append('accepted_evidence_unavailable_or_changed')
                hashes = history.get('sha256', {})
                if not all(prefix + suffix in hashes for suffix in ('.restart.lammpsdat', '.assoc_restart')):
                    problems.append('endpoint_hashes_absent')
                if data.get('provenance_kind') == 'corrected_C1_8M':
                    inventory_record = r.records.get('repository:examples/KG_Assoc/campaign/e2_remaining_inventory_20261011.json')
                    pins = (inventory_record or {}).get('data', {}).get('preserved_files', {})
                    for suffix in ('.restart.lammpsdat', '.assoc_restart'):
                        endpoint = r.resolve(prefix + suffix)
                        relative = ('examples/KG_Assoc/kg_assoc_100m/' +
                                    endpoint.relative_to(r.dataset).as_posix()) if endpoint and endpoint.is_relative_to(r.dataset) else None
                        if not relative or hashes.get(prefix + suffix) != pins.get(relative, {}).get('sha256'):
                            problems.append('corrected_C1_endpoint_not_frozen')
            if len({h.get('prefix') for h in histories}) != 3 or len({h.get('chemistry_seed') for h in histories}) != 3:
                problems.append('duplicate_histories_or_chemical_seeds')
            if data.get('provenance_kind') not in ('E2_G1_segment', 'corrected_C1_8M'):
                problems.append('unknown_provenance_kind')
            if data.get('provenance_kind') == 'corrected_C1_8M' and (
                data.get('bank_id') != C1_BANK or any(h.get('end_step') != 8000000 for h in histories)
                or not data.get('qualification', '').strip()):
                problems.append('invalid_corrected_C1_endpoint')
            if data.get('status') == 'accepted_with_qualification' and not data.get('qualification', '').strip():
                problems.append('qualification_absent')
            acceptance = dict(source=record['id'], data=data, metadata_eligible=not problems,
                              issues=sorted(set(problems)), payload_authentication='deferred')
            self.graph['acceptances'].append(acceptance)
            for problem in acceptance['issues']:
                r.issue('acceptance_' + problem, record['id'], 'Not eligible in this metadata view')
        for system in self.graph['systems']:
            if not system['bank']:
                continue
            if len(registries) > 1 and not self.selected_registry:
                system['selection'] = 'ambiguous'
            formal = [a for a in self.graph['acceptances'] if a['metadata_eligible'] and
                      system['system_id'] in a['data'].get('permitted_systems', []) and
                      system['bank'] == a['data'].get('bank_id')]
            if formal:
                system['scientific'] = 'formal_acceptance_recorded_payload_deferred'
            registry = next((p for p in registries if p['id'] == self.selected_registry), None)
            entry = registry['data'].get('systems', {}).get(system['system_id']) if registry else None
            if entry:
                path = r.resolve(entry.get('acceptance'))
                chosen = next((a for a in formal if path and a['source'] == r.key(path) and
                               r.records[a['source']]['sha256'] == entry.get('sha256')), None)
                if chosen and registry['supported']:
                    system['selection'] = 'selected_metadata_payload_deferred'
                else:
                    system['selection'] = 'invalid_selection'
                    r.issue('registry_acceptance_mismatch', registry['id'], system['system_id'])
                self.graph['selections'].append(dict(system_id=system['system_id'],
                    registry=registry['id'], entry=entry, status=system['selection']))
