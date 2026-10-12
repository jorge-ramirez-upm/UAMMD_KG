#!/usr/bin/env python3
"""Offline campaign navigation. Only new, ignored catalog snapshots are written."""
import argparse
import csv
import hashlib
import html
import json
import os
import uuid
import webbrowser
from pathlib import Path
from urllib.parse import quote

from catalog_model import Catalog, discover, utcnow

STYLE = '''body{font:15px system-ui;margin:2rem;line-height:1.5;color:#17212b}
 table{border-collapse:collapse;width:100%;font-size:13px}td,th{padding:.5rem;border:1px solid #ddd;text-align:left}
 th{background:#e9eef3}pre{white-space:pre-wrap;overflow-wrap:anywhere}input,select{padding:.5rem;margin:.3rem}
 .notice{background:#fff3ce;padding:1rem}details{margin:.7rem 0}a{color:#164d9b}'''


def escaped(value):
    return html.escape(str(value), quote=True)


def dump(value):
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)


def source_link(path, page, label=None):
    if not path:
        return 'Unavailable locally'
    relative = os.path.relpath(path, page.parent)
    return f'<a href="{quote(relative, safe="/.")}">{escaped(label or path)}</a>'


def detail(title, data):
    return f'<details><summary>{escaped(title)}</summary><pre>{escaped(dump(data))}</pre></details>'


def page_document(title, body):
    return ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escaped(title)}</title><style>{STYLE}</style><body>'
            f'<h1>{escaped(title)}</h1>{body}</body></html>')


def context(graph):
    return (f"23 conditions / 69 history slots / {graph['coverage']['unique_selected_e1']} shared E1 references\n"
            f"Commit: {graph['generator_git_sha']}\nDataset: {graph['dataset_root']}\n"
            f"Scope: {graph['scope']}; recorded claims; payload authentication deferred\n"
            f"Observation: {graph['scan_started_at']} to {graph['scan_finished_at']}\n"
            f"Registry view: {graph['selected_registry'] or 'none (missing or ambiguous)'}\n"
            f"Coverage: {graph['coverage']['metadata_records']} metadata records; "
            f"{graph['coverage']['missing_system_records']} system records unavailable; "
            f"{len(graph['diagnostics'])} diagnostics")


def status(graph):
    print(context(graph))
    print('\nSYSTEM                            SMOKE           E2 / SCIENCE / SELECTION')
    for system in graph['systems']:
        print(f"{system['system_id']:33} {system['smoke']:15} "
              f"{system['execution']} / {system['scientific']} / {system['selection']}")
    if len(graph['registry_views']) > 1 and not graph['selected_registry']:
        print('\nMultiple registry views; choose --registry PATH explicitly:')
        print('\n'.join(graph['registry_views']))
    print('\nProduction authorization is separate; no catalog command authorizes MD.')


def system_record(graph, sid):
    system = next((s for s in graph['systems'] if s['system_id'] == sid), None)
    if system is None:
        raise ValueError('Unknown system: ' + sid)
    attempts = [a for a in graph['attempts'] if sid in a['systems']]
    ids = {a['id'] for a in attempts}
    reviews = [r for r in graph['reviews'] if ids.intersection(r['attempts'])]
    sources = {a['source'] for a in attempts} | ids
    return dict(system=system, histories=[h for h in graph['histories'] if h['system_id'] == sid],
                attempts=attempts, reviews=reviews,
                references=[r for r in graph['references'] if r['source'] in sources],
                diagnostics=[d for d in graph['diagnostics'] if d['source'] in sources],
                acceptances=[a for a in graph['acceptances'] if sid in a['data'].get('permitted_systems', [])])


def safe_csv(value):
    if isinstance(value, (list, dict)):
        value = json.dumps(value, sort_keys=True)
    if value is None:
        return 'unknown'
    text = str(value)
    return "'" + text if text.lstrip().startswith(('=', '+', '-', '@')) else text


def write_csv(path, rows, fields):
    with path.open('x', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=['schema_version'] + fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(schema_version=1, **{f: safe_csv(row.get(f)) for f in fields}))


def render_system(graph, sid, page):
    view = system_record(graph, sid)
    records = {r['id']: r for r in graph['records']}
    body = '<a href="../index.html">Campaign</a>'
    body += '<p class="notice">Recorded metadata only. Payload authentication deferred. '
    body += 'Smokes are not equilibrium data. Production authorization is a separate gate.</p>'
    body += detail('Parameters and separate readiness gates', view['system'])
    for decision in view['system'].get('documented_reviews', []):
        body += '<p>' + source_link(records[decision['source']]['path'], page, 'Documented scientific review decision; not registered acceptance') + '</p>'
        for link in graph['references']:
            if link['source'] == decision['source']:
                body += '<p>' + source_link(link['path'], page, link['original']) + '</p>'
    body += '<h2>Three independent histories</h2>'
    for history in view['histories']:
        body += detail(history['id'] + ' — shared E1 reference and lineage', history)
    body += '<h2>Attempts, extensions, tests and production</h2>'
    for attempt in view['attempts']:
        record = records[attempt['source']]
        body += source_link(record['path'], page, attempt['role'] + ' source record')
        body += detail(f"r{attempt['replica']:03d}: {attempt['role']} / {attempt['execution']} / "
                       f"{attempt['numerical']} / {attempt['scientific']}", attempt)
        body += detail('Original provenance record; metadata SHA256 ' + record['sha256'], record['data'])
    body += '<h2>Scientific reviews (never automatic acceptance)</h2>'
    for review in view['reviews']:
        body += source_link(records[review['source']]['path'], page, 'Review receipt')
        body += detail('Review windows and provenance', review)
        for link in review['links']:
            body += '<p>' + source_link(link, page) + '</p>'
    body += detail('Formal acceptance records; payload checks deferred', view['acceptances'])
    sources = {a['source'] for a in view['attempts']} | {a['id'] for a in view['attempts']}
    references = [r for r in graph['references'] if r['source'] in sources]
    body += '<h2>Evidence references</h2>'
    for reference in references:
        body += source_link(reference['path'], page, reference['original'])
        body += detail(reference['integrity'], reference)
    body += detail('Relevant diagnostics', [d for d in graph['diagnostics'] if d['source'] in sources])
    body += '<pre>' + escaped(context(graph)) + '</pre>'
    page.write_text(page_document(sid, body), encoding='utf-8')


def render_index(graph, directory):
    page = directory / 'index.html'
    fields = ['geometry', 'role', 'Ee', 'target_Ea', 'smoke', 'execution', 'numerical', 'scientific', 'selection', 'integrity']
    body = '<p class="notice">Local metadata observation; giant payloads are not read or hashed. '
    body += 'Missing local records do not establish what exists on another host. '
    body += 'No acceptance or production authorization is created.</p>'
    body += '<pre>' + escaped(context(graph)) + '</pre>'
    body += '<label>Search <input id="search" placeholder="System, Ea, Ee, state…"></label>'
    for field in fields:
        options = sorted({s[field] for s in graph['systems']})
        body += f'<label>{escaped(field)}<select data-field="{field}"><option value="">All</option>'
        body += ''.join(f'<option>{escaped(v)}</option>' for v in options) + '</select></label>'
    body += '<table><thead><tr><th>System (Ee / target Ea)</th>'
    body += ''.join(f'<th>{escaped(f)}</th>' for f in fields) + '</tr></thead><tbody>'
    for system in graph['systems']:
        sid = system['system_id']
        attrs = ' '.join(f'data-{field}="{escaped(system[field])}"' for field in fields)
        body += f'<tr {attrs}><td><a href="systems/{sid}.html">{sid}</a></td>'
        body += ''.join(f'<td>{escaped(system[f])}</td>' for f in fields) + '</tr>'
    body += '</tbody></table><p id="count"></p>'
    body += '''<script>
const rows = [...document.querySelectorAll('tbody tr')];
function filter() {
  const query = document.querySelector('#search').value.toLowerCase();
  const filters = [...document.querySelectorAll('select[data-field]')];
  let count = 0;
  rows.forEach(row => {
    const show = row.textContent.toLowerCase().includes(query) &&
      filters.every(f => !f.value || row.getAttribute('data-' + f.dataset.field) === f.value);
    row.hidden = !show; if (show) count++;
  });
  document.querySelector('#count').textContent = count + ' of 23 conditions';
}
document.querySelectorAll('input,select').forEach(e => e.addEventListener('input', filter));
filter();
</script>'''
    body += '<h2>Exports</h2><p><a href="catalog.json">Evidence graph JSON</a> · '
    body += '<a href="systems.csv">Conditions CSV</a> · <a href="histories.csv">Histories CSV</a> · '
    body += '<a href="attempts.csv">Attempts CSV</a></p>'
    body += detail('Registry views — choose explicitly when ambiguous', graph['registry_views'])
    body += detail('Coverage and freshness', graph['coverage'])
    body += detail('Integrity and unresolved-reference diagnostics', graph['diagnostics'])
    body += '<h2>Builds, diagnostic reports and workflow journals</h2>'
    for record in graph['records']:
        if any(p in Path(record['path']).parts for p in ('builds', 'aggregate')):
            body += '<p>' + source_link(record['path'], page, record['id']) + '</p>'
    page.write_text(page_document('Associating-star campaign catalog', body), encoding='utf-8')


def publish(graph, repository, include_html=True):
    """Exclusive staging and UUID destination; never replace a report or runtime file."""
    output = Path(repository) / 'examples/KG_Assoc/catalog_output'
    dataset = Path(graph['dataset_root']).resolve()
    if output.resolve().is_relative_to(dataset) or dataset.is_relative_to(output.resolve()):
        raise ValueError('Catalog output must be separate from runtime data')
    if not output.resolve().is_relative_to(Path(repository).resolve()):
        raise ValueError('Catalog output escapes repository')
    if output.is_symlink():
        raise ValueError('Catalog output must not be a symlink')
    output.mkdir(parents=True, exist_ok=True)
    identifier = 'snapshot_' + utcnow().replace(':', '-').replace('+', '_') + '_' + uuid.uuid4().hex
    staging = output / ('.building_' + identifier)
    final = output / identifier
    staging.mkdir()  # Exclusive. Failures remain here for inspection.
    (staging / 'catalog.json').write_text(dump(graph) + '\n', encoding='utf-8')
    write_csv(staging / 'systems.csv', graph['systems'],
              ['system_id', 'parameters', 'geometry', 'bank', 'execution', 'smoke', 'numerical', 'scientific',
               'selection', 'production_eligibility', 'production_authorization', 'integrity'])
    write_csv(staging / 'histories.csv', graph['histories'],
              ['id', 'system_id', 'replica', 'selected_e1', 'e1_sha256', 'attempts'])
    write_csv(staging / 'attempts.csv', graph['attempts'],
              ['id', 'source', 'role', 'replica', 'systems', 'start_step', 'end_step', 'physics',
               'chemistry_seed', 'md_seed', 'effective_md_seed', 'execution', 'numerical',
               'scientific', 'authorization', 'parent_segment', 'git_sha', 'step_units'])
    if include_html:
        (staging / 'systems').mkdir()
        for system in graph['systems']:
            render_system(graph, system['system_id'], staging / 'systems' / (system['system_id'] + '.html'))
        render_index(graph, staging)
    files = {str(p.relative_to(staging)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(staging.glob('**/*')) if p.is_file()}
    (staging / 'generation_manifest.json').write_text(dump(dict(schema_version=1,
        snapshot_id=identifier, generated_at=utcnow(), generator_git_sha=graph['generator_git_sha'],
        scope=graph['scope'], files_sha256=files)) + '\n', encoding='utf-8')
    # UUID plus exclusive reservation prevents concurrent publishers replacing a destination.
    reservation = output / ('.publish_' + identifier)
    with reservation.open('x', encoding='utf-8') as stream:
        stream.write(identifier)
    if final.exists():
        raise FileExistsError('Immutable snapshot already exists: ' + str(final))
    staging.rename(final)
    reservation.unlink()
    return final


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', help='Explicit dataset-relative registry view; never activates it')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('status')
    commands.add_parser('show').add_argument('system_id')
    report = commands.add_parser('report')
    report.add_argument('--open', action='store_true', help='Open the immutable offline HTML snapshot')
    commands.add_parser('export').add_argument('--format', choices=['json', 'csv', 'all'], default='all',
                                                help='Snapshot always retains all graph and CSV evidence')
    args = parser.parse_args(argv)
    repository, dataset = discover(__file__)
    try:
        graph = Catalog(repository, dataset, args.registry).scan()
        if args.command == 'status':
            status(graph)
        elif args.command == 'show':
            print(context(graph))
            print(dump(system_record(graph, args.system_id)))
        else:
            output = publish(graph, repository, args.command == 'report')
            target = output / ('index.html' if args.command == 'report' else
                               ('systems.csv' if args.format == 'csv' else 'catalog.json'))
            print(context(graph))
            print('\nImmutable snapshot: ' + str(output))
            print('Open: ' + str(target))
            if args.command == 'report' and args.open and not webbrowser.open(target.as_uri()):
                print('Browser launch unavailable; open the printed index.html path.')
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(2, f'Catalog error: {error}\n')


if __name__ == '__main__':
    main()
