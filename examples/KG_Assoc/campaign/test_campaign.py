#!/usr/bin/env python3

import importlib.util
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).with_name("kg_assoc_campaign.py")
SPEC = importlib.util.spec_from_file_location("kg_assoc_campaign", MODULE_PATH)
CAMPAIGN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CAMPAIGN)


class CampaignTest(unittest.TestCase):
    def test_matrix_has_fifteen_associating_and_eight_controls(self):
        systems = CAMPAIGN.campaign_systems()
        self.assertEqual(15, sum(item["associating"] for item in systems))
        self.assertEqual(8, sum(not item["associating"] for item in systems))
        self.assertEqual(23, len({item["system_id"] for item in systems}))

    def test_reference_is_deduplicated_and_in_five_groups(self):
        reference = next(item for item in CAMPAIGN.campaign_systems()
                         if item["system_id"] == "F04_N010_RP080_EE08_EA04")
        self.assertEqual({"association", "kinetics", "density", "arm_length", "functionality"},
                         set(reference["groups"]))

    def test_initialization_writes_eight_geometry_requirements(self):
        with tempfile.TemporaryDirectory() as temporary:
            class Arguments:
                dataset_root = temporary
            CAMPAIGN.command_init(Arguments())
            requirements = list((Path(temporary) / "inputs").glob("*/requirements.example.json"))
            self.assertEqual(8, len(requirements))


if __name__ == "__main__":
    unittest.main()
