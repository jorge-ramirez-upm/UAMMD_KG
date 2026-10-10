"""Offline synthetic accounting fixtures; these are not GPU/physics validation."""

from pathlib import Path
import tempfile
import unittest

from test_c1_e2_pilot import fixture, snapshot, write
import validate_periodic_e2_smoke as smoke


class PeriodicSmokeTests(unittest.TestCase):
    def test_seeded_segment_and_missing_oracle_sweep(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prefix = fixture(root, 1, snapshot())
            parent = root / "parent/state"
            text = Path(str(prefix) + ".assoc_restart").read_text()
            write(Path(str(parent) + ".assoc_restart"), text.replace(
                "completed_steps 12000", "completed_steps 6000000").replace(
                "creations 2", "creations 1").replace("breaks 1", "breaks 0"))
            write(Path(str(parent) + ".restart.lammpsdat"),
                  "Offline parent step 6000000\n" + snapshot())
            for suffix in (".restart.lammpsdat", ".final_permanent.lammpsdat"):
                path = Path(str(prefix) + suffix)
                path.write_text(path.read_text().replace("step 12000", "step 6010000"))
            path = Path(str(prefix) + ".assoc_restart")
            path.write_text(text.replace("completed_steps 12000", "completed_steps 6010000"))
            path = Path(str(prefix) + ".state")
            lines = path.read_text().splitlines()
            header = lines[0].replace("start_step=0", "start_step=6000000").replace(
                "total_requested_steps=12000", "total_requested_steps=6010000").replace(
                "chemistry_sweeps=120", "chemistry_sweeps=100").replace(
                "input_file=independent_e1_r1", "input_file=" + str(parent) + ".restart.lammpsdat")
            header += " candidate_sticker_pairs=200"
            rows = []
            for line in lines[3:14]:  # Old steps 1000..11000 become 6M..6M+10000.
                fields = line.split()
                step = int(fields[0]) + 5999000
                fields[:2] = [str(step), str(step * .01)]
                rows.append(" ".join(fields))
            path.write_text(header + "\n" + lines[1] + "\n" + "\n".join(rows) + "\n")
            write(Path(str(prefix) + ".events"), header + "\n" +
                  "6000100 B 11 52 1 2\n6001100 C 11 52 1 2\n")
            write(Path(str(prefix) + ".numerics.tsv"),
                  "# step time kinetic_energy temperature min_permanent_bond max_permanent_bond\n" +
                  "\n".join(f"{step} {step * .01} 65344.5 1 .8 .8"
                            for step in range(6000000, 6010001, 1000)) + "\n")
            oracle = Path(str(prefix) + ".candidate_validation.tsv")
            write(oracle, "# step candidates oracle_verified_active_candidates\n" +
                  "\n".join(f"{step} 2 1" for step in range(6000100, 6010001, 100)) + "\n")
            write(prefix.parent / "stderr.log", "\n".join(
                f"[VerletNVT::GronbechJensen] {field}: {value}" for field, value in
                (("Temperature", "1.000000"), ("Time step", "0.010000"),
                 ("Friction", "0.500000"))))
            result = smoke.validate(prefix, parent, 1)
            self.assertEqual(result["oracle_sweeps"], 100)
            self.assertEqual(result["accepted_events"], 2)
            self.assertEqual(result["final_bonds"], 1)
            for suffix in (".state", ".events"):
                path = Path(str(prefix) + suffix)
                path.write_text(path.read_text().replace("seed=22001", "seed=22001 md_seed=32001"))
            log = prefix.parent / "stderr.log"
            log.write_text(log.read_text() +
                           "\n[E2 MD stream] requested_seed=32001 effective_seed=3928609932 internal_start_step=0\n")
            result = smoke.validate(prefix, parent, 1, steps=10000, oracle=False, md_seed=32001)
            self.assertEqual(result["accepted_events"], 2)
            with self.assertRaisesRegex(ValueError, "fresh MD stream"):
                smoke.validate(prefix, parent, 1, steps=10000, oracle=False, md_seed=32002)
            with self.assertRaisesRegex(ValueError, "sweep count"):
                smoke.validate(prefix, parent, 1, steps=2000000, oracle=False, md_seed=32001)
            oracle.write_text(oracle.read_text().replace("6000200 2 1\n", ""))
            with self.assertRaisesRegex(ValueError, "incomplete per-sweep"):
                smoke.validate(prefix, parent, 1)


if __name__ == "__main__":
    unittest.main()
