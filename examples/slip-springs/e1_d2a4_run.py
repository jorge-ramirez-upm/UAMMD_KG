#!/usr/bin/env python3
"""D2A.4 dynamics only: explicit local launch after independent review; never on import."""
from pathlib import Path
from e1_d2a3_run import campaign_main

CONFIG = Path(__file__).resolve().parent / 'e1_d2a4_config'
MANIFEST_SHA = '697f0f3be4841221d5b109e0376f4de9da63f239db6f088e5b128da0d4d438fc'

if __name__ == '__main__':
    campaign_main(CONFIG, MANIFEST_SHA, '--execute-reviewed-twelve', 'twelve', __file__)
