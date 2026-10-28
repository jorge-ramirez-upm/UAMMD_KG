#!/usr/bin/env python3
"""Reviewed local D2A.5 campaign entry point; preparation is not execution permission."""
from pathlib import Path
from e1_d2a5_campaign import campaign_main

CONFIG = Path(__file__).resolve().parent/'e1_d2a5_production_config'
MANIFEST_SHA = '297ad861edb98232ca91c9fbd11b7eef2443bc685d7c89ec592a7ab86777c365'

if __name__ == '__main__':
    campaign_main(CONFIG,MANIFEST_SHA,__file__)
