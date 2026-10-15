"""Fresh CPU-only six-segment authentication to a new output file."""
import argparse
import register as registration


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=registration.Path, required=True)
    args = parser.parse_args()
    e2 = registration.e2
    e2.require(not args.output.exists(), 'new authentication output required')
    scientific = registration.scientific
    scientific.verify_inputs()
    integrity = e2.campaign.load_json(registration.REVIEW / 'INTEGRITY.json')
    e2.check_hashes({str(registration.REVIEW / name): digest
                   for name, digest in integrity['sha256'].items()})
    sources = scientific.authenticate()
    scientific.joint.check_lineage(sources)
    fresh = [dict(attempt=s['attempt'], plan=s['plan'],
        build_authentication_scope=s['build_authentication_scope'],
        histories=[dict(entry=h['entry'], validation=h['validation']) for h in s['histories']])
        for s in sources]
    provenance = e2.campaign.load_json(registration.REVIEW / 'evidence/provenance.json')
    e2.require(fresh == provenance['source_authentication'], 'approved provenance differs')
    registration.check_pins(provenance, (registration.REVIEW / 'ENDPOINTS.md').read_text())
    e2.exclusive_json(args.output, fresh)
    print('PASS: six segments, parent lineage, outputs, completion and numerical replay')


if __name__ == '__main__':
    main()
