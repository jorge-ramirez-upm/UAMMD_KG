"""Bounded development-only E1 GPU regression. Requires the semiflexible executable.

No hopping, renewal, production trajectories or rheological stress assumptions.
"""
import csv
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


def rows(path):
    with open(path, newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


class FixedSpringGPU(unittest.TestCase):
    binary = None

    def run_case(self, directory, name, input_path, additional):
        dest = directory / name
        command = [str(self.binary), "--output", str(dest), "--springs", "3",
                   "--chains", "2", "--seed", "4317", "--kappa", "1",
                   "--steps", "0", "--force-input", str(input_path)] + additional
        p = subprocess.run(command, capture_output=True, text=True, check=False, timeout=40)
        if p.returncode:
            self.fail(f"{command!r}: {p.stdout}\n{p.stderr}")
        return dest

    def test_exact_force_energy_and_zero_recovery(self):
        with tempfile.TemporaryDirectory(prefix="e1-fixed-") as tmp:
            path = pathlib.Path(tmp)
            # Two nondegenerate semiflexible chains, four beads each.
            config = path / "positions.txt"
            xyz = [
                (0., 0., 0.), (1., 0., 0.), (1.8, .5, 0.), (2.1, 1.2, .4),
                (.2, .2, .1), (1.2, -.1, .3), (1.9, .2, .8), (2.3, .9, 1.),
            ]
            config.write_text("".join(f"{x} {y} {z}\n" for x, y, z in xyz), encoding="utf-8")
            bare = self.run_case(path, "bare", config, [])
            zero = self.run_case(path, "zero", config, ["--slip-count", "0"])
            enriched = self.run_case(path, "enriched", config,
                                     ["--slip-count", "3", "--slip-ms2", "2.4"])
            self.assertEqual((bare / "forces.csv").read_bytes(),
                             (zero / "forces.csv").read_bytes())
            before = rows(bare / "forces.csv")
            after = rows(enriched / "forces.csv")
            self.assertEqual(len(before), 8)
            self.assertEqual(len(after), 8)
            anchors = rows(enriched / "fixed_slip_springs.csv")
            self.assertEqual(len(anchors), 3)
            sites = [(int(r["chain"]), int(r["bead"])) for r in anchors]
            self.assertEqual(len(set(sites)), len(sites))
            amap = {site: r for site, r in zip(sites, anchors)}
            metadata = json.loads((enriched / "metadata.json").read_text())
            tolerance = 5e-5 if metadata["precision_bits"] == 32 else 2e-12
            k = metadata["slip_effective_stiffness"]
            stored = rows(enriched / "initial.csv")
            for old, new in zip(before, after):
                site = (int(old["chain"]), int(old["bead"]))
                self.assertEqual(site, (int(new["chain"]), int(new["bead"])))
                if site not in amap:
                    for label in ("fx", "fy", "fz", "energy"):
                        self.assertAlmostEqual(float(old[label]), float(new[label]), delta=tolerance)
                    continue
                r = tuple(float(stored[site[0] * 4 + site[1]][label]) for label in ("x", "y", "z"))
                a = tuple(float(amap[site][label]) for label in ("ax", "ay", "az"))
                delta = [r[d]-a[d] for d in range(3)]
                for label, d in zip(("fx", "fy", "fz"), range(3)):
                    self.assertAlmostEqual(float(new[label])-float(old[label]),
                                           -k*delta[d], delta=tolerance)
                self.assertAlmostEqual(float(new["energy"])-float(old["energy"]),
                                       0.5*k*sum(x*x for x in delta), delta=tolerance)
            again = self.run_case(path, "enriched_replay", config,
                                  ["--slip-count", "3", "--slip-ms2", "2.4"])
            self.assertEqual((enriched / "fixed_slip_springs.csv").read_bytes(),
                             (again / "fixed_slip_springs.csv").read_bytes())
            self.assertEqual((enriched / "forces.csv").read_bytes(),
                             (again / "forces.csv").read_bytes())

    def test_input_validation_before_cuda(self):
        # Each rejection must be an input error, never a missing-device error.
        with tempfile.TemporaryDirectory(prefix="e1-cli-") as tmp:
            for i, extra in enumerate((
                ["--slip-count", "9"], ["--slip-count", "-1"],
                ["--slip-count", "1"],
                ["--slip-count", "1", "--slip-ms2", "0"],
                ["--slip-count", "1", "--slip-ms2", "nan"],
                ["--slip-count", "1", "--slip-ms2", "1e-320"],
                *(["--slip-count", "1", "--slip-ms2", "3", "--stress-mode", mode]
                  for mode in ("diagnostic", "stream", "every-step")),
            )):
                dest = pathlib.Path(tmp) / str(i)
                p = subprocess.run([str(self.binary), "--springs", "3", "--chains", "2",
                                    "--output", str(dest)] + extra,
                                   capture_output=True, text=True, timeout=40)
                self.assertNotEqual(p.returncode, 0)
                self.assertNotIn("cuda", p.stderr.lower())
                self.assertFalse(dest.exists(), p.stderr)

    def test_active_force_diagnostic(self):
        with tempfile.TemporaryDirectory(prefix="e1-failure-") as tmp:
            root = pathlib.Path(tmp)
            config = root / "r.txt"
            config.write_text("0 0 0\n1 0 0\n2 0 0\n3 0 0\n" * 2)
            probe = self.run_case(root, "probe", config, [])
            bits = json.loads((probe / "metadata.json").read_text())["precision_bits"]
            initial = root / "collapsed.txt"
            initial.write_text("0 0 0\n0 0 0\n")
            dest = root / "failure"
            ms2 = "1e-30" if bits == 32 else "1e-300"
            p = subprocess.run([str(self.binary), "--output", str(dest),
                                "--springs", "1", "--chains", "1", "--kappa", "0",
                                "--b0", "0", "--kb", "3", "--dt", "1", "--steps", "1",
                                "--initial", str(initial), "--slip-count", "2", "--slip-ms2", ms2],
                               capture_output=True, text=True, timeout=40)
            self.assertNotEqual(p.returncode, 0)
            failure = json.loads((dest / "failure.json").read_text())
            self.assertEqual(failure["step"], 1)
            self.assertEqual(failure["reason"], 4)
            self.assertEqual(failure["slip_count"], 2)
            self.assertEqual(failure["slip_ms2"], float(ms2))
            self.assertGreater(failure["slip_effective_stiffness"], 0)
            self.assertTrue((dest / "failure_positions.csv").exists())
            self.assertTrue((dest / "fixed_slip_springs.csv").exists())

    def test_dynamics_rng_isolation_and_disabled_compatibility(self):
        with tempfile.TemporaryDirectory(prefix="e1-dynamics-") as tmp:
            root = pathlib.Path(tmp)
            def run(name, extra):
                dest = root / name
                args = [str(self.binary), "--springs", "3", "--chains", "2",
                        "--seed", "4317", "--kbt", "1.7", "--zeta", "2",
                        "--kappa", "1", "--dt", "0.0001", "--steps", "1",
                        "--sample", "1", "--output", str(dest)] + extra
                p = subprocess.run(args, capture_output=True, text=True, timeout=40)
                self.assertEqual(p.returncode, 0, p.stderr)
                return dest
            bare = run("bare", [])
            zero = run("zero", ["--slip-count", "0", "--slip-ms2", "-1"])
            active = run("active", ["--slip-count", "8", "--slip-ms2", "2.4"])
            replay = run("replay", ["--slip-count", "8", "--slip-ms2", "2.4"])
            for name in ("initial.csv", "final.csv", "samples.csv", "bond_statistics.csv"):
                self.assertEqual((bare/name).read_bytes(), (zero/name).read_bytes())
                self.assertEqual((active/name).read_bytes(), (replay/name).read_bytes())
            self.assertEqual((bare/"initial.csv").read_bytes(), (active/"initial.csv").read_bytes())
            self.assertEqual((active/"fixed_slip_springs.csv").read_bytes(),
                             (replay/"fixed_slip_springs.csv").read_bytes())
            self.assertFalse((zero/"fixed_slip_springs.csv").exists())
            zmeta = json.loads((zero/"metadata.json").read_text())
            meta = json.loads((active/"metadata.json").read_text())
            self.assertEqual(zmeta["slip_launches"], 0)
            self.assertEqual(zmeta["slip_device_bytes"], 0)
            self.assertIsNone(zmeta["slip_effective_stiffness"])
            self.assertEqual(meta["slip_launches"], meta["stretch_launches"])
            self.assertGreater(meta["slip_device_bytes"], 0)
            single = meta["precision_bits"] == 32
            tolerance = 3e-7 if single else 3e-15
            self.assertAlmostEqual(meta["slip_effective_stiffness"], 3*1.7/2.4, delta=tolerance)
            initial = rows(active/"initial.csv")
            anchors = rows(active/"fixed_slip_springs.csv")
            final_bare, final_active = rows(bare/"final.csv"), rows(active/"final.csv")
            for table in (initial, anchors, final_bare, final_active):
                self.assertEqual(len(table), 8)
            # Same Philox increments: the one-step difference is precisely the
            # added deterministic spring drift, with stretch and bend present.
            for r, a, b, f in zip(initial, anchors, final_bare, final_active):
                for coord, anchor in zip(("x", "y", "z"), ("ax", "ay", "az")):
                    force = -meta["slip_effective_stiffness"]*(float(r[coord])-float(a[anchor]))
                    self.assertAlmostEqual(float(f[coord])-float(b[coord]),
                                           meta["effective_mobility_step"]*force,
                                           delta=tolerance)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: test_fixed_slip_springs.py /path/to/semiflexible")
    FixedSpringGPU.binary = pathlib.Path(sys.argv.pop()).resolve()
    unittest.main(verbosity=2)
