#!/usr/bin/env python3
"""One-command authenticated E2 workflow. Smoke commands authorize only capped tests."""

import argparse
from contextlib import contextmanager
import fcntl
import getpass
import os
from pathlib import Path
import socket
import subprocess
import sys
import uuid

import kg_assoc_e2 as e2

campaign = e2.campaign
require = e2.require
SMOKE_SYSTEMS = (
    'F04_N010_RP080_EE04_EA04', 'F04_N010_RP020_EE08_EA04',
    'F03_N010_RP080_EE08_EA04', 'F06_N010_RP080_EE08_EA04',
    'F04_N020_RP080_EE08_EA04', 'F04_N040_RP080_EE08_EA04',
    'F04_N010_RP080_EE08_EA08',
)
C1_BANK = 'F04_N010_RP080_EE08'


def discover(script=Path(__file__)):
    repository = script.resolve().parents[3]
    branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=repository,
                                     text=True).strip()
    require(branch == 'KremerGrest', 'switch to the KremerGrest branch before using E2')
    root = repository / 'examples/KG_Assoc/kg_assoc_100m'
    require(root.is_dir(), 'campaign dataset missing: ' + str(root))
    require(campaign.load_json(root / 'campaign_protocol.json') ==
            campaign.load_json(campaign.PROTOCOL_PATH), 'dataset protocol mismatch')
    require(set(campaign.load_json(root / 'manifest.json')['systems']) ==
            {s['system_id'] for s in campaign.campaign_systems()}, 'dataset matrix mismatch')
    inventory = campaign.load_json(e2.INVENTORY)
    require(inventory['e1_states'] and inventory['C1_recovery'] and inventory['preserved_files'],
            'frozen inventory is incomplete')
    return root


def new_path(parent, label):
    parent.mkdir(parents=True, exist_ok=True)
    while True:
        path = parent / (label + '_' + uuid.uuid4().hex)
        if not path.exists():
            return path


@contextmanager
def workflow_lock(root):
    path = root / 'banks/.run_e2.lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    # OS releases this advisory lock even after interruption; no stale-lock editing needed.
    with path.open('a') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('another run_e2 workflow is active; use status') from None
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def ensure_build(root):
    e2.clean_tree()
    for manifest in sorted((root / 'builds').glob('*/manifest.json'),
                           key=lambda p: p.stat().st_mtime_ns, reverse=True):
        try:
            e2.check_build(manifest.parent)
            e2.live_code()
            print('BUILD reused authenticated ' + manifest.parent.name, flush=True)
            return manifest.parent
        except (ValueError, KeyError, OSError, subprocess.CalledProcessError):
            continue
    path = new_path(root / 'builds', 'run_e2_build')
    print('BUILD rebuilding six targets; logs: ' + str(path), flush=True)
    e2.build(root, path)
    e2.check_build(path)
    return path


def attempts(root, system):
    return sorted((root / 'banks/e2_attempts' / campaign.e2_bank_id(system)).glob('*/plan.json'))


def desired_parents(root, system, parent_attempt=None):
    if parent_attempt:
        previous = e2.verify(root, parent_attempt)
        result = []
        for entry in previous['histories']:
            prefix = entry['output_prefix']
            result.append(dict(kind='e2', prefix=prefix, snapshot=prefix + '.restart.lammpsdat',
                          sha256=e2.hash_files([Path(prefix + suffix) for suffix in e2.validation.OUTPUTS] +
                                  [Path(prefix).parent / 'complete.json', parent_attempt / 'plan.json'])))
        return result
    if campaign.e2_bank_id(system) == C1_BANK:
        return [e2.corrected_c1(root, r, replay=False) for r in (1, 2, 3)]
    return [e2.original_e1(root, system, r) for r in (1, 2, 3)]


def find_smoke(root, system, parent_attempt=None):
    parents = desired_parents(root, system, parent_attempt)
    current = dict(source_sha256=e2.sources(), executable_sha256=e2.hash_files(
        [e2.HERE.parent / name for name in e2.EXECUTABLES]))
    expected_seeds = ([int(e2.validation.analysis.restart.read_metadata(
        p['prefix'] + '.assoc_restart')[0]['seed']) for p in parents]
        if parents[0]['kind'] == 'e2' else e2.seed_map()[campaign.e2_bank_id(system)])
    for path in reversed(attempts(root, system)):
        try:
            raw = campaign.load_json(path)
            if not raw['smoke'] or raw['preparation_Ea'] != system['Ea']:
                continue
            plan = e2.verify(root, path.parent)
            if not e2.smoke_code_compatible(plan, current):
                continue
            if all(entry['parent'] == parent and entry['physics'] ==
                   e2.validation.physics(system, system['Ea']) and
                   entry['chemistry_seed'] == seed
                   for entry, parent, seed in zip(plan['histories'], parents, expected_seeds)):
                return path.parent
        except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
            print('NOT REUSABLE ' + path.parent.name + ': ' + str(error), flush=True)
    return None


def authorize(attempt, invocation, smoke, journal):
    plan_path = attempt / 'plan.json'
    path = attempt / 'approval.json'
    e2.exclusive_json(path, dict(
        schema_version=1, approved=True, purpose='e2_smoke' if smoke else 'e2_segment',
        plan_sha256=campaign.sha256(plan_path), reviewer=getpass.getuser(),
        approved_at=e2.timestamp(), authorization='explicit_user_cli_request',
        invocation=invocation, host=socket.gethostname(), pid=os.getpid(),
        command_record=str(journal / 'request.json'),
        command_record_sha256=campaign.sha256(journal / 'request.json'),
        scope='capped_numerical_test' if smoke else 'requested_system_and_step_count',
        scientific_equilibrium_acceptance=False))
    return path


def execute_segment(root, system, steps, build, invocation, journal, smoke,
                    parent_attempt=None):
    bank = campaign.e2_bank_id(system)
    path = new_path(root / 'banks/e2_attempts' / bank, 'smoke' if smoke else 'equilibrate')
    evidence = campaign.REPOSITORY_ROOT / 'examples/KG_Assoc/E2_G1.md'
    c1 = bank == C1_BANK
    print(('SMOKE ' if smoke else 'E2 ') + system['system_id'] + ': ' + str(path), flush=True)
    try:
        e2.prepare(root, path, system['system_id'], steps, evidence, parent_attempt,
                   smoke, c1, system['Ea'], build)
        approval = authorize(path, invocation, smoke, journal)
        matching = None if smoke else find_smoke(root, system, parent_attempt)
        require(smoke or matching is not None, 'matching smoke was not verified')
        e2.launch(root, path, execute=True, approval=approval, smoke_attempt=matching)
        e2.verify(root, path)
    except BaseException as error:
        # Preparation can fail before its plan is written; retain a wrapper-level record too.
        e2.exclusive_json(journal / ('failure_' + uuid.uuid4().hex + '.json'),
                          dict(attempt=str(path), error=str(error), recorded_at=e2.timestamp()))
        raise
    return path


def smoke_one(root, system, build, invocation, journal, parent_attempt=None):
    existing = find_smoke(root, system, parent_attempt)
    if existing:
        print('SKIP verified compatible ' + system['system_id'] + ': ' + existing.name, flush=True)
        return dict(system=system['system_id'], status='skipped_verified', attempt=str(existing))
    path = execute_segment(root, system, 10000, build, invocation, journal, True, parent_attempt)
    print('PASS ' + system['system_id'] + ' (three replicas; numerical validation)', flush=True)
    return dict(system=system['system_id'], status='passed', attempt=str(path))


def completed_segments(root, system):
    segments = []
    for path in attempts(root, system):
        raw = campaign.load_json(path)
        if raw['smoke'] or raw['system'] != system:
            continue
        if not all((path.parent / f'r{r:03d}/complete.json').is_file() for r in (1, 2, 3)):
            continue
        segments.append((path.parent, e2.verify(root, path.parent)))
    return sorted(segments, key=lambda item: item[1]['histories'][0]['end_step'])


def unfinished_state(attempt):
    if any((attempt / f'r{r:03d}/incomplete.json').exists() for r in (1, 2, 3)):
        return 'failed'
    if not any((attempt / f'r{r:03d}/started.json').exists() for r in (1, 2, 3)):
        return 'pending'
    approval_path = attempt / 'approval.json'
    approval = campaign.load_json(approval_path) if approval_path.exists() else {}
    if approval.get('host') == socket.gethostname() and approval.get('pid'):
        try:
            os.kill(int(approval['pid']), 0)
        except ProcessLookupError:
            return 'failed/interrupted'
        except PermissionError:
            pass
        return 'running'
    return 'running/unresolved (external host or legacy process)'


def status(root):
    current = dict(source_sha256=e2.sources(), executable_sha256={})
    try:
        current['executable_sha256'] = e2.hash_files([e2.HERE.parent / n for n in e2.EXECUTABLES])
    except OSError:
        pass
    for identifier in SMOKE_SYSTEMS:
        system = e2.system_by_id(identifier)
        states = []
        for path in attempts(root, system):
            try:
                plan = campaign.load_json(path)
                if not plan['smoke'] or plan['preparation_Ea'] != system['Ea']:
                    continue
                if all((path.parent / f'r{r:03d}/complete.json').exists() for r in (1, 2, 3)):
                    verified = e2.verify(root, path.parent)
                    state = 'completed' if e2.smoke_code_compatible(verified, current) else 'incompatible'
                else:
                    state = unfinished_state(path.parent)
                states.append(state + ':' + path.parent.name)
            except (ValueError, KeyError, OSError) as error:
                states.append('failed:' + path.parent.name + ' (' + str(error) + ')')
        print(identifier + '  ' + (', '.join(states) if states else 'pending'))
    for path in sorted((root / 'banks/e2_attempts').glob('*/*/plan.json')):
        plan = campaign.load_json(path)
        if not plan['smoke']:
            try:
                if all((path.parent / f'r{r:03d}/complete.json').exists() for r in (1, 2, 3)):
                    e2.verify(root, path.parent)
                    state = 'completed; scientific review required'
                else:
                    state = unfinished_state(path.parent)
            except (ValueError, KeyError, OSError) as error:
                state = 'failed: ' + str(error)
            print('E2 ' + plan['system']['system_id'] + '  ' + state + '  ' + path.parent.name)
    for failure in sorted((root / 'aggregate/e2/workflow').glob('*/failed.json')):
        print('FAILED WORKFLOW ' + failure.parent.name + ': ' + campaign.load_json(failure)['error'])


def review_window(steps, requested=None):
    window = requested if requested is not None else (
        500000 if steps >= 500000 and steps % 500000 == 0 else
        steps // 2 if steps >= 8000 and steps % 2000 == 0 else steps)
    require(window >= 4000 and window % 1000 == 0 and steps % window == 0,
            'review windows must be at least 4000, align to 1000 and partition the segment')
    return window


def scientific_report(output, attempt, window_steps):
    """Render the validated analyzer's numbers; no new acceptance or statistical rules."""
    summary = campaign.load_json(output / 'summary.json')
    config = campaign.load_json(output / 'analysis_config.json')
    plan = campaign.load_json(attempt / 'plan.json')
    require(config['plan_sha256'] == campaign.sha256(attempt / 'plan.json') and
            config['window_steps'] == window_steps, 'review plan/window provenance mismatch')
    require(summary['scientific_status'] == 'review_required' and
            summary['automatic_acceptance'] is False and len(summary['records']) == 3,
            'analysis is not a three-history scientific review')
    def number(value):
        return 'unresolved' if value is None else format(value, '.7g')

    lines = ['# E2 scientific checkpoint', '',
             'System: `' + plan['system']['system_id'] + '`.',
             'Numerical, accepted-event, network and conformation validation passed.',
             '**Scientific review required. This checkpoint does not accept equilibrium.**', '',
             f"Segment: {plan['histories'][0]['start_step']}–{plan['histories'][0]['end_step']} MD steps; "
             f'{window_steps}-step windows; three original independent histories.',
             'Physics: `' + str(plan['histories'][0]['physics']) + '`.',
             'Attempt: `' + str(attempt) + '`.',
             'Plan SHA256: `' + config['plan_sha256'] + '`.', '',
             'All transients are retained. No extensions or production are launched.',
             'Rates use physical time; neighbor gains/losses count distinct inter-star edges, not bonds.',
             'L1 counts parallel inter-star bond pairs; L2 counts distinct-star triangles.',
             'Rg² and center-terminal R² use permanent-bond minimum-image unwrapping.', '',
             '## Replica-level comparisons', '',
             'Window means and paired last-minus-previous differences use Student-t 95% intervals (df=2).',
             'A wide interval or a difference compatible with zero does not establish stationarity.', '',
             '| Category | Observable | Window | Mean | 95% half-width |',
             '|---|---|---|---:|---:|']
    for item in summary['comparisons']:
        lines.append(f"| {item['category']} | {item['observable']} | {item['window']} | "
                     f"{number(item['mean'])} | {number(item['ci95_half_width'])} |")
    warnings = 0
    for record in summary['records']:
        lines += ['', f"## History r{record['replica']:03d}", '']
        for index, window in enumerate(record['windows'], 1):
            lines += [f"### Window {index}: ({window['start_step_exclusive']}, "
                      f"{window['end_step_inclusive']}]", '',
                      '| Category | Observable | Mean | IAT SEM | τ time | Effective samples | Slope/time | Review flag |',
                      '|---|---|---:|---:|---:|---:|---:|---|']
            for category in ('metrics', 'activity'):
                for name, item in window[category].items():
                    flags = []
                    if item.get('constant_not_mixing_evidence'):
                        flags.append('constant: no mixing evidence')
                    if item.get('resolution_warning'):
                        flags.append('correlation/resolution')
                    warnings += bool(flags)
                    lines.append(f"| {category} | {name} | {number(item['mean'])} | "
                                 f"{number(item['sem_estimate'])} | {number(item['tau_time'])} | "
                                 f"{number(item['effective_samples_estimate'])} | {number(item['slope'])} | "
                                 + '; '.join(flags) + ' |')
            lines += ['', '| Accepted activity | Count | Rate/time | Rate/star/time |',
                      '|---|---:|---:|---:|']
            for name, count in window['event_counts'].items():
                lines.append(f"| {name} | {count} | {number(window['event_rates_per_time'][name])} | "
                             f"{number(window['event_rates_per_star_time'][name])} |")
            lines += ['', 'Exact event-integrated exposures: `' + str(window['exposure']) + '`.',
                      'Population-normalized rates: `' + str(window['population_normalized_rates']) + '`.',
                      '5/10/20-block SEM sensitivity is retained in [summary.json](summary.json).']
    lines += ['', '## Review decision remains open', '',
              f'{warnings} observable/window entries carry mixing or correlation-resolution flags.',
              'Inspect population and intra/inter drift, reaction/neighbor exchange, connectivity,',
              'L1/L2, shape relaxation, autocorrelation resolution and agreement between histories together.',
              'Compare the windows and paired late-window changes; retain the initial unbound transient.',
              'No automatic stop/extend/accept decision is made.', '',
              '[Full statistics](summary.json) · [Replica comparisons](replica_comparisons.csv) · '
              '[Authenticated analysis configuration](analysis_config.json)', '']
    report = output / 'SCIENTIFIC_REVIEW.md'
    with report.open('x') as stream:
        stream.write('\n'.join(lines))
    e2.exclusive_json(output / 'review_complete.json', dict(
        scientific_status='review_required', automatic_acceptance=False,
        plan_sha256=campaign.sha256(attempt / 'plan.json'),
        report_sha256=e2.hash_files([report, output / 'summary.json', output / 'analysis_config.json',
                                   output / 'replica_comparisons.csv']),
        renderer_git_sha=campaign.git_sha(), window_steps=window_steps, warning_entries=warnings))
    return report


def review_segment(root, attempt, window_steps):
    import analyze_e2_segment
    output = new_path(root / 'aggregate/e2', 'review')
    print('REVIEW reconstructing events and statistics; ' + str(window_steps) + '-step windows', flush=True)
    analyze_e2_segment.analyze(root, attempt, output, window_steps)
    return scientific_report(output, attempt, window_steps)


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest='action', required=True)
    commands.add_parser('smoke-all', help='authorize remaining compatible 10k numerical tests only')
    commands.add_parser('status', help='verify completed tests and show campaign state; runs no MD')
    child = commands.add_parser('smoke', help='authorize one three-replica 10k numerical test')
    child.add_argument('--system', required=True)
    child = commands.add_parser('equilibrate', help='authorize ONLY the named E2 segment')
    child.add_argument('--system', required=True)
    child.add_argument('--steps', required=True, type=int)
    child.add_argument('--window-steps', type=int, help='automatic review partition; 500k for 2M')
    child.add_argument('--extend', action='store_true', help='explicitly extend latest verified E2 segment')
    child = commands.add_parser('review', help='validate/analyze completed E2; does not accept equilibrium')
    child.add_argument('--system', required=True)
    child.add_argument('--window-steps', type=int)
    return result


def run(args, root, invocation):
    if args.action == 'status':
        status(root)
        return 0
    system = None if args.action == 'smoke-all' else e2.system_by_id(args.system)
    if args.action == 'equilibrate':
        require(system['Ea'] == 4 and campaign.e2_bank_id(system) != C1_BANK,
                'fresh E2 requires an Ea04 system; accepted C1 needs no further equilibration')
        require(args.steps >= 4000 and args.steps % 1000 == 0,
                'E2 steps must be at least 4000 and a multiple of 1000 for review')
        review_window(args.steps, args.window_steps)
    with workflow_lock(root):
        journal = new_path(root / 'aggregate/e2/workflow', args.action)
        e2.exclusive_json(journal / 'request.json', dict(invocation=invocation, action=args.action,
                          system=system, steps=getattr(args, 'steps', None),
                          extend=getattr(args, 'extend', False),
                          review_window_steps=review_window(args.steps, args.window_steps)
                          if args.action == 'equilibrate' else getattr(args, 'window_steps', None),
                          requested_at=e2.timestamp(),
                          git_sha=campaign.git_sha(), user=getpass.getuser(),
                          host=socket.gethostname(), pid=os.getpid()))
        results = []
        try:
            if args.action == 'review':
                segments = completed_segments(root, system)
                require(segments, 'no completed ordinary E2 segments to review')
                for attempt, plan in segments:
                    steps = plan['steps']
                    window = review_window(steps, args.window_steps)
                    report = review_segment(root, attempt, window)
                    results.append(dict(system=system['system_id'], status='scientific_review_required',
                                        attempt=str(attempt), report=str(report)))
            else:
                subprocess.check_output(['nvidia-smi', '--query-gpu=name,uuid,driver_version',
                                         '--format=csv,noheader'], text=True)
                build = ensure_build(root)
                if args.action in ('smoke', 'smoke-all'):
                    systems = [system] if system else [e2.system_by_id(i) for i in SMOKE_SYSTEMS]
                    for condition in systems:
                        try:
                            results.append(smoke_one(root, condition, build, invocation, journal))
                        except Exception as error:
                            results.append(dict(system=condition['system_id'], status='failed', error=str(error)))
                            print('FAIL ' + condition['system_id'] + ': ' + str(error), flush=True)
                else:
                    segments = completed_segments(root, system)
                    require(bool(segments) == args.extend,
                            'existing completed E2 requires --extend; --extend requires a completed segment')
                    parent = segments[-1][0] if segments else None
                    if parent:
                        require(sum(p['histories'][0]['end_step'] == segments[-1][1]['histories'][0]['end_step']
                                    for _, p in segments) == 1, 'ambiguous latest E2 history; investigate forks')
                    # This exact-parent capped prerequisite is covered by the explicit equilibration command.
                    smoke_one(root, system, build, invocation, journal, parent)
                    path = execute_segment(root, system, args.steps, build, invocation, journal, False, parent)
                    window = review_window(args.steps, args.window_steps)
                    result = dict(system=system['system_id'], status='numerically_valid_review_pending',
                                  attempt=str(path), steps_per_history=args.steps,
                                  validated_histories=3, review_window_steps=window)
                    results.append(result)
                    report = review_segment(root, path, window)
                    result.update(status='scientific_review_required', report=str(report))
                    print(f'CHECKPOINT: 3/3 histories validated; {args.steps} steps/history; '
                          f'{args.steps // window} review windows of {window} steps.', flush=True)
        except BaseException as error:
            e2.exclusive_json(journal / 'failed.json', dict(error=str(error), results=results, at=e2.timestamp()))
            raise
        failed = any(r['status'] == 'failed' for r in results)
        e2.exclusive_json(journal / 'report.json', dict(results=results, scientific_acceptance=False,
                          finished_at=e2.timestamp(), status='failed' if failed else 'completed'))
        print('\n' + '\n'.join(r['status'].upper() + ' ' + r['system'] +
              (' — ' + r['report'] if 'report' in r else '') for r in results))
        print('Evidence: ' + str(journal / 'report.json'))
        print('No equilibrium acceptance or production launch is implied.')
        return 1 if failed else 0


def main(argv=None):
    arguments = sys.argv[1:] if argv is None else argv
    args = parser().parse_args(arguments)
    try:
        return run(args, discover(), [sys.executable, str(Path(__file__).resolve()), *arguments])
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        print('E2 stopped: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
