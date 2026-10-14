"""CPU audit of actual COM writer, permanent-bond reconstruction and MSD consumers.

Run with Python 3.11 (the installed correlator extension's ABI). The host harness
compiles the unchanged StarComWriter text with a minimal ParticleData/vector shim;
it does not compile or execute CUDA. Known defects are asserted as counterexamples.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

import numpy as np
import analyze_campaign_structure as structure
import analyze_p44_com_diffusion as diffusion
import analyze_p47_walking_hopping as walking


SHIM = r'''
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <memory>
#include <vector>
namespace uammd {
using real = double;
struct real3 {
  double x, y, z;
  real3& operator+=(real3 b) {
    x += b.x;
    y += b.y;
    z += b.z;
    return *this;
  }
  real3& operator/=(double b) {
    x /= b;
    y /= b;
    z /= b;
    return *this;
  }
};
struct real4 { double x, y, z, w; };
real3 make_real3(double x, double y, double z) {
  return {x, y, z};
}
real3 make_real3(double x) {
  return {x, x, x};
}
real3 make_real3(real4 p) {
  return {p.x, p.y, p.z};
}
real3 operator+(real3 a, real3 b) {
  return {a.x + b.x, a.y + b.y, a.z + b.z};
}
namespace access { enum Mode { cpu, read }; }
struct ParticleData {
  std::vector<real4> positions;
  std::vector<int> mapping;
  auto getPos(access::Mode, access::Mode) {
    return positions;
  }
  auto getIdOrderedIndices(access::Mode) {
    return mapping;
  }
};
}
namespace kg {
struct LammpsData {
  int natoms;
  std::vector<int> type, mol;
};
}
namespace kg_assoc { struct BoxLengths { double x, y, z; };
'''
MAIN = r'''
int main() {
  int count, frames, resetAt;
  kg_assoc::BoxLengths box;
  std::cin >> count >> frames >> resetAt >> box.x >> box.y >> box.z;
  kg::LammpsData data;
  data.natoms = count;
  data.mol.resize(count);
  data.type.resize(count);
  auto particles = std::make_shared<uammd::ParticleData>();
  particles->positions.resize(count);
  particles->mapping.resize(count);
  for (int id = 0; id < count; ++id) {
    std::cin >> data.mol[id] >> data.type[id] >> particles->mapping[id];
  }
  auto writer = std::make_unique<StarComWriter>(data, box);
  for (int frame = 0; frame < frames; ++frame) {
    if (frame == resetAt) {
      writer = std::make_unique<StarComWriter>(data, box);
    }
    for (auto& position : particles->positions) {
      std::cin >> position.x >> position.y >> position.z;
      position.w = 0;
    }
    writer->write(frame, frame, particles, std::cout);
  }
}
'''


def bond_com(points, bonds, lengths=(10., 10., 10.), members=None):
    members = list(range(len(points))) if members is None else members
    adjacency = [set() for _ in points]
    for first, second in bonds:
        adjacency[first].add(second)
        adjacency[second].add(first)
    whole = structure.unwrap_star(np.asarray(points).ravel(), members, adjacency, lengths)
    return np.mean(whole, axis=0)


def folded(points, lengths=(10., 10., 10.)):
    points = np.asarray(points)
    return points - np.asarray(lengths) * np.floor(points / lengths + .5)


class ComPbcAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        repo = Path(__file__).resolve().parents[3]
        source = (repo / 'examples/KG_Assoc/kg_assoc_production.cu').read_text()
        writer = 'class StarComWriter {' + source.split('class StarComWriter {', 1)[1]
        writer = writer.split('\n};', 1)[0] + '\n};\n'
        runtime = (repo / 'examples/KG_Assoc/kg_assoc_star_runtime.cuh').read_text()
        minimum = 'inline double minimumImage' + runtime.split('inline double minimumImage', 1)[1]
        minimum = minimum.split('\n}', 1)[0] + '\n}\n'
        cls.temp = tempfile.TemporaryDirectory(prefix='com_pbc_cpu_')
        cls.addClassCleanup(cls.temp.cleanup)
        cpp = Path(cls.temp.name) / 'actual_writer.cpp'
        cpp.write_text(SHIM + minimum + '}\n' + writer + MAIN)
        cls.executable = Path(cls.temp.name) / 'actual_writer'
        subprocess.run(['g++', '-std=c++14', '-O2', str(cpp), '-o', str(cls.executable)],
                       check=True, capture_output=True, text=True)

    def writer(self, frames, molecules=None, lengths=(10., 10., 10.), reset_at=-1, order=None):
        frames = np.asarray(frames, dtype=float)
        count = frames.shape[1]
        molecules = [1] * count if molecules is None else molecules
        order = list(range(count)) if order is None else order
        mapping = [order.index(i) for i in range(count)]
        lines = [' '.join(map(str, (count, len(frames), reset_at, *lengths)))]
        lines += [f'{molecule} 1 {mapping[i]}' for i, molecule in enumerate(molecules)]
        lines += [' '.join(map(str, point)) for frame in frames for point in frame[order]]
        output = subprocess.check_output([str(self.executable)], input='\n'.join(lines), text=True)
        rows = np.asarray([[float(v) for v in line.split()] for line in output.splitlines()])
        return rows[:, 3:].reshape(len(frames), len(set(molecules)), 3)

    def test_star_straddles_boundary_naive_mean_is_wrong(self):
        points = [[4.8, 0, 0], [-4.8, 0, 0], [4.8, .4, 0], [4.8, -.4, 0], [4.8, 0, .4]]
        bonds = [(0, i) for i in range(1, 5)]
        expected = np.array([4.88, 0, .08])
        np.testing.assert_allclose(bond_com(points, bonds), expected)
        np.testing.assert_allclose(self.writer([points])[0, 0], expected)
        self.assertGreater(np.linalg.norm(np.mean(points, axis=0) - expected), 1.)

    def test_opposite_box_sides_and_equivalent_images(self):
        points = np.array([[4.9, 0, 0], [-4.9, 0, 0]])
        images = points + [[20, -10, 30], [-30, 20, -10]]
        first = bond_com(points, [(0, 1)])
        second = bond_com(images, [(0, 1)])
        np.testing.assert_allclose(folded(first), folded(second))
        np.testing.assert_allclose(folded(self.writer([points])[0]),
                                   folded(self.writer([images])[0]))

    def test_rigid_translation_multiple_box_lengths_and_time_origins(self):
        base = np.array([[4.7, 0, 0], [5.1, 0, 0], [4.7, .4, 0]])
        velocity = np.array([.75, -.25, .125])
        times = np.arange(80.)
        frames = folded(base[None, :, :] + times[:, None, None] * velocity)
        com = self.writer(frames)
        np.testing.assert_allclose(com[:, 0] - com[0, 0], times[:, None] * velocity)
        lags, msd, counts = diffusion.multi_tau_msd(com)
        np.testing.assert_allclose(msd, np.dot(velocity, velocity) * lags ** 2)
        exact = diffusion.brute_force_msd(com)
        np.testing.assert_allclose(exact, np.dot(velocity, velocity) * times ** 2)
        self.assertTrue(np.all(counts > 0))

    def test_back_and_forth_crossings_and_walking_consumer(self):
        shifts = np.array([0., .8, 1.6, .8, 0., -.8, 0.])
        frames = folded(np.array([[4.8, 0, 0], [5.2, 0, 0]])[None] +
                        shifts[:, None, None] * [1., 0., 0.])
        com = self.writer(frames)
        np.testing.assert_allclose(com[:, 0, 0] - com[0, 0, 0], shifts, atol=1e-12)
        positions = {i: {1: (float(i), *point[0])} for i, point in enumerate(com)}
        observed = walking.lag_statistics(list(positions), positions, 1, (1,), 1)['msd']
        self.assertAlmostEqual(observed, float(np.mean(np.diff(shifts) ** 2)))

    def test_deterministic_walk_across_boxes_and_com_file_reader(self):
        # A fixed synthetic walk tests reconstruction, not statistical diffusion convergence.
        increments = np.random.default_rng(27).integers(-4, 5, size=(256, 3)) * .5
        path = np.cumsum(increments, axis=0)
        self.assertGreater(float(np.max(np.ptp(path, axis=0))), 20.)
        self.assertLess(float(np.max(np.abs(increments))), 5.)
        reconstructed = self.writer(folded(path[:, None, :]))
        np.testing.assert_allclose(reconstructed[:, 0] - reconstructed[0, 0], path - path[0])
        output = Path(self.temp.name) / 'synthetic.com_trajectory'
        with output.open('w') as stream:
            stream.write('# step time molecule_id com_x com_y com_z\n')
            for step, point in enumerate(reconstructed[:, 0]):
                stream.write(f'{step} {step} 1 {point[0]} {point[1]} {point[2]}\n')
        _, _, loaded = diffusion.read_com_trajectory(output)
        np.testing.assert_allclose(loaded, reconstructed)
        lags, observed, _ = diffusion.multi_tau_msd(loaded)
        expected = diffusion.brute_force_msd(path[:, None, :])
        # The fine level averages every origin; coarse multi-tau levels subsample origins.
        np.testing.assert_allclose(observed[:16], expected[lags[:16]])

    def test_multiple_crossings_between_samples_are_silently_aliased(self):
        frames = np.array([[[0., 0, 0]], [[21., 0, 0]], [[42., 0, 0]]])
        observed = self.writer(frames)
        np.testing.assert_allclose(observed[:, 0, 0], [0., 1., 2.])
        self.assertEqual(diffusion.brute_force_msd(observed)[1], 1.)
        self.assertEqual(diffusion.brute_force_msd(frames)[1], 441.)
        np.testing.assert_allclose(self.writer(folded(frames)), observed)

    def test_single_anchor_fails_for_extended_permanent_backbone(self):
        # Four valid 40-bead arms, edge length 1.1 < R0, L=60: the +x arm exceeds L/2.
        points = [[0., 0, 0]]
        bonds = []
        for direction in ((1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1)):
            parent = 0
            for bead in range(1, 41):
                points.append([1.1 * bead * value for value in direction])
                bonds.append((parent, len(points) - 1))
                parent = len(points) - 1
        expected = np.mean(points, axis=0)
        np.testing.assert_allclose(bond_com(folded(points, (60.,) * 3), bonds, (60.,) * 3), expected)
        actual = self.writer([points], lengths=(60.,) * 3)[0, 0]
        self.assertGreater(np.linalg.norm(actual - expected), 1.)

    def test_restart_before_and_after_crossing_resets_com_origin(self):
        frames = folded([[[4., 0, 0]], [[6., 0, 0]], [[8., 0, 0]], [[10., 0, 0]]])
        continuous = self.writer(frames)
        np.testing.assert_allclose(continuous[:, 0, 0], [4, 6, 8, 10])
        for restart in (1, 2):
            with self.subTest(restart=restart):
                reset = self.writer(frames, reset_at=restart)
                self.assertNotAlmostEqual(reset[restart, 0, 0], continuous[restart, 0, 0])
                aligned = reset.copy()
                aligned[restart:] += continuous[restart] - reset[restart]
                np.testing.assert_allclose(aligned, continuous)
                np.testing.assert_allclose(diffusion.brute_force_msd(aligned),
                                           4 * np.arange(len(frames)) ** 2)

    def test_temporary_bonds_do_not_merge_permanent_membership_or_storage_order(self):
        points = [[4.8, 0, 0], [-4.8, 0, 0], [1., 0, 0], [1.4, 0, 0]]
        permanent = [(0, 1), (2, 3)]
        with_temporary = permanent + [(1, 2)]
        first = bond_com(points, permanent, members=[0, 1])
        second = bond_com(points, permanent, members=[2, 3])
        np.testing.assert_allclose(bond_com(points, with_temporary, members=[0, 1]), first)
        np.testing.assert_allclose(bond_com(points, with_temporary, members=[2, 3]), second)
        output = self.writer([points], molecules=[1, 1, 2, 2], order=[3, 1, 0, 2])[0]
        np.testing.assert_allclose(output, [first, second])

    def test_unit_mass_com_and_velocity_mean(self):
        points = np.array([[1., 2, 3], [2., 3, 4]])
        velocities = np.array([[2., 0, 0], [0., 2, 0]])
        np.testing.assert_allclose(self.writer([points])[0, 0],
                                   np.average(points, axis=0, weights=[1., 1.]))
        np.testing.assert_allclose(np.mean(velocities, axis=0),
                                   np.average(velocities, axis=0, weights=[1., 1.]))
        self.assertFalse(np.allclose(self.writer([points])[0, 0],
                                     np.average(points, axis=0, weights=[1., 3.])))


if __name__ == '__main__':
    unittest.main()
