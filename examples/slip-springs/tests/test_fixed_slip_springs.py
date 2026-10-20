"""Bounded development-only E1 GPU regression. Requires the semiflexible executable.

No hopping, renewal, production trajectories or rheological stress assumptions.
"""
import csv
import math
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def rows(path):
    with open(path, newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


class FixedSpringGPU(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if len(sys.argv) != 2:
            raise RuntimeError("usage: test_fixed_slip_springs.py /path/to/semiflexible")
        cls.binary = pathlib.Path(sys.argv.pop()).resolve()

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
            # Two nondegenerate semiflexible chains, with six independent coordinates each.
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
            anchors = rows(enriched / "fixed_slip_springs.csv")
            self.assertEqual(len(anchors), 3)
            sites = [(int(r["chain"]), int(r["bead"])) for r in anchors]
            self.assertEqual(len(set(sites)), len(sites))
            amap = {site: r for site, r in zip(sites, anchors)}
            k = 3.0 / 2.4
            for old, new in zip(before, after):
                site = (int(old["chain"]), int(old["bead"]))
                self.assertEqual(site, (int(new["chain"]), int(new["bead"])))
                if site not in amap:
                    for label in ("fx", "fy", "fz", "energy"):
                        self.assertAlmostEqual(float(old[label]), float(new[label]), delta=5e-5)
                    continue
                r = xyz[site[0] * 4 + site[1]]
                a = tuple(float(amap[site][label]) for label in ("ax", "ay", "az"))
                delta = [r[d]-a[d] for d in range(3)]
                for label, d in zip(("fx", "fy", "fz"), range(3)):
                    self.assertAlmostEqual(float(new[label])-float(old[label]),
                                           -k*delta[d], delta=5e-5)
                self.assertAlmostEqual(float(new["energy"])-float(old["energy"]),
                                       0.5*k*sum(x*x for x in delta), delta=5e-5)
            again = self.run_case(path, "enriched_replay", config,
                                  ["--slip-count", "3", "--slip-ms2", "2.4"])
            self.assertEqual((enriched / "fixed_slip_springs.csv").read_bytes(),
                             (again / "fixed_slip_springs.csv").read_bytes())
            self.assertEqual((enriched / "forces.csv").read_bytes(),
                             (again / "forces.csv").read_bytes())


if __name__ == "__main__":
    unittest.main()
