#!/usr/bin/env python3
"""Additional paired consecutive contrasts from the immutable 500k means."""
from pathlib import Path
import argparse
import reproduce as review


def main(directory):
    directory = Path(directory)
    source = directory / 'summary.json'
    data = review.joint.campaign.load_json(source)
    review.joint.require(data['system']['system_id'] == 'F04_N010_RP040_EE08_EA04' and
                         data['automatic_acceptance'] is False, 'wrong scientific review')
    for record in data['records']:
        review.joint.require([(w['start_step_exclusive'], w['end_step_inclusive'])
                              for w in record['windows']] ==
                             [(a, a + 500000) for a in range(0, 6000000, 500000)],
                             'incomplete 0–6M context')
    pairs = tuple(((start, start + width), (start + width, start + 2 * width))
                  for width in (500000, 1000000, 2000000)
                  for start in range(width, 6000000 - 2 * width + 1, width)
                  if start >= 1000000)
    result = review.graph.sensitivity.summarize(data, pairs)
    result['source_sha256'] = review.joint.runner.hash_files([source, Path(__file__)])
    review.joint.runner.exclusive_json(directory / 'consecutive_comparisons.json', result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    main(parser.parse_args().directory)
