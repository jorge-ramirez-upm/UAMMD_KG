"""CPU audit of actual COM writer, permanent-bond reconstruction and MSD consumers.

Run with Python 3.11 (the installed correlator extension's ABI). The host harness
compiles the actual StarComWriter text with a minimal ParticleData/vector shim;
it does not compile or execute CUDA. The corrected observer and fail-closed transport metadata are tested directly.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest
import warnings
import com_transport

import numpy as np
import analyze_campaign_structure as structure
import analyze_p44_com_diffusion as diffusion
import analyze_p47_walking_hopping as walking
import analyze_p48_percolation as percolation
import kg_assoc_campaign as campaign


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
  std::vector<double> mass;
  auto getMass(access::Mode, access::Mode) { return mass; }
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
  std::vector<std::pair<int, int>> bonds;
  double xlo, xhi, ylo, yhi, zlo, zhi;
};
}
namespace kg_assoc { struct BoxLengths { double x, y, z; };
'''
MAIN = r'''
int main(int argc, char** argv) {
  if (argc == 4 && std::string(argv[2]) == "preflight") {
    kg_assoc::requireOrthorhombicComInput(argv[1]);
    kg_assoc::requireIndependentComOrigin(argv[1], std::string(argv[3]) == "continuation");
    return 0;
  }
  int count, frames, resetAt, bondCount, header, continuous;
  kg_assoc::BoxLengths box;
  std::cin >> count >> frames >> resetAt >> bondCount >> header >> continuous;
  std::cin >> box.x >> box.y >> box.z;
  kg::LammpsData data;
  data.natoms = count;
  data.xlo = -box.x / 2;
  data.xhi = box.x / 2;
  data.ylo = -box.y / 2;
  data.yhi = box.y / 2;
  data.zlo = -box.z / 2;
  data.zhi = box.z / 2;
  data.mol.resize(count);
  data.type.resize(count);
  auto particles = std::make_shared<uammd::ParticleData>();
  particles->positions.resize(count);
  particles->mapping.resize(count);
  particles->mass.assign(count, 1.0);
  for (int id = 0; id < count; ++id) {
    std::cin >> data.mol[id] >> data.type[id] >> particles->mapping[id];
  }
  for (int bond = 0; bond < bondCount; ++bond) {
    int first, second;
    std::cin >> first >> second;
    data.bonds.emplace_back(first, second);
  }
  std::unique_ptr<StarComWriter> writer;
  for (int frame = 0; frame < frames; ++frame) {
    if (frame == resetAt) {
      kg_assoc::requireIndependentComOrigin(argv[1]);
    }
    for (auto& index : particles->mapping) {
      std::cin >> index;
    }
    for (auto& position : particles->positions) {
      std::cin >> position.x >> position.y >> position.z;
      position.w = 0;
    }
    if (!writer) {
      writer = std::make_unique<StarComWriter>(data, box, particles, 1.5,
          continuous ? kg_assoc::NativeComConvention::continuous_gronbech_jensen_v1 :
                       kg_assoc::NativeComConvention::unknown);
      if (header) {
        kg_assoc::writeComTransportHeader(std::cout,
            {{data.xlo, data.xhi, data.ylo, data.yhi, data.zlo, data.zhi}},
            writer->moleculeIds(), 0, 1, 1.0, "synthetic-independent-origin");
      }
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
        cpp.write_text('#include "' + str(repo / 'examples/KG_Assoc/kg_assoc_com_transport.cuh') +
                       '"\n' + SHIM + minimum + '}\n' + writer + MAIN)
        cls.executable = Path(cls.temp.name) / 'actual_writer'
        subprocess.run(['g++', '-std=c++14', '-O2', str(cpp), '-o', str(cls.executable)],
                       check=True, capture_output=True, text=True)

    def writer(self, frames, molecules=None, lengths=(10., 10., 10.), reset_at=-1, order=None, bonds=None, header=False, continuous=True, types=None):
        frames = np.asarray(frames, dtype=float)
        count = frames.shape[1]
        molecules = [1] * count if molecules is None else molecules
        types = [1] * count if types is None else types
        order = list(range(count)) if order is None else order
        orders = order if order and isinstance(order[0], (list, tuple)) else [order] * len(frames)
        self.assertEqual(len(orders), len(frames))
        for frame_order in orders:
            self.assertEqual(sorted(frame_order), list(range(count)))
        mapping = [orders[0].index(i) for i in range(count)]
        bonds = ([(i - 1, i) for i in range(1, count) if molecules[i - 1] == molecules[i]]
                 if bonds is None else bonds)
        lines = [' '.join(map(str, (count, len(frames), reset_at, len(bonds),
                                   int(header), int(continuous), *lengths)))]
        lines += [f'{molecule} {types[i]} {mapping[i]}' for i, molecule in enumerate(molecules)]
        lines += [f'{a + 1} {b + 1}' for a, b in bonds]
        for frame, frame_order in zip(frames, orders):
            lines.append(' '.join(str(frame_order.index(i)) for i in range(count)))
            lines += [' '.join(map(str, point)) for point in frame[frame_order]]
        prefix = str(Path(self.temp.name) / 'restart-test')
        if reset_at >= 0:
            Path(prefix + '.com_trajectory').write_text('existing production trajectory')
        output = subprocess.check_output([str(self.executable), prefix],
                                         input='\n'.join(lines), text=True, stderr=subprocess.PIPE)
        if header:
            return output
        rows = np.asarray([[float(v) for v in line.split()] for line in output.splitlines()])
        stars = {m for m, kind in zip(molecules, types) if kind in (1, 2)}
        return rows[:, 3:].reshape(len(frames), len(stars), 3)

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
        frames = folded(base)[None, :, :] + times[:, None, None] * velocity
        com = self.writer(frames)
        np.testing.assert_allclose(com[:, 0] - com[0, 0], times[:, None] * velocity)
        lags, msd, counts = diffusion.multi_tau_msd(com)
        np.testing.assert_allclose(msd, np.dot(velocity, velocity) * lags ** 2)
        exact = diffusion.brute_force_msd(com)
        np.testing.assert_allclose(exact, np.dot(velocity, velocity) * times ** 2)
        self.assertTrue(np.all(counts > 0))

    def test_back_and_forth_crossings_and_walking_consumer(self):
        shifts = np.array([0., .8, 1.6, .8, 0., -.8, 0.])
        frames = (folded(np.array([[4.8, 0, 0], [5.2, 0, 0]]))[None] +
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
        reconstructed = self.writer(path[:, None, :])
        np.testing.assert_allclose(reconstructed[:, 0] - reconstructed[0, 0], path - path[0])
        output = Path(self.temp.name) / 'synthetic.com_trajectory'
        output.write_text(self.writer(path[:, None, :], header=True))
        _, _, loaded = diffusion.read_com_trajectory(output)
        np.testing.assert_allclose(loaded, reconstructed)
        lags, observed, _ = diffusion.multi_tau_msd(loaded)
        expected = diffusion.brute_force_msd(path[:, None, :])
        # The fine level averages every origin; coarse multi-tau levels subsample origins.
        np.testing.assert_allclose(observed[:16], expected[lags[:16]])

    def test_multiple_crossings_between_samples_are_not_aliased(self):
        base = np.array([[4.8, 0, 0], [-4.8, 0, 0], [4.8, .4, 0],
                         [4.8, -.4, 0], [4.8, 0, .4]])
        bonds = [(0, i) for i in range(1, 5)]
        frames = base[None] + np.arange(3.)[:, None, None] * [21., 0., 0.]
        observed = self.writer(frames, bonds=bonds)
        expected = np.array([[[0., 0, 0]], [[21., 0, 0]], [[42., 0, 0]]])
        np.testing.assert_allclose(observed - observed[0], expected, atol=1e-12)
        self.assertAlmostEqual(diffusion.brute_force_msd(observed)[1], 441.)
        with self.assertRaises(subprocess.CalledProcessError):
            self.writer(frames, bonds=bonds, continuous=False)

    def test_permanent_backbone_reconstructs_extended_star(self):
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
        actual = self.writer([folded(points, (60.,) * 3)], lengths=(60.,) * 3,
                             bonds=bonds)[0, 0]
        np.testing.assert_allclose(actual, expected, atol=1e-12)

    def test_restart_before_and_after_crossing_requires_origin_checkpoint(self):
        frames = np.array([[[4., 0, 0]], [[6., 0, 0]], [[8., 0, 0]], [[10., 0, 0]]])
        np.testing.assert_allclose(self.writer(frames)[:, 0, 0], [4, 6, 8, 10])
        for restart in (1, 2):
            with self.subTest(restart=restart), self.assertRaises(subprocess.CalledProcessError):
                self.writer(frames, reset_at=restart)
        first = self.writer(frames[:2], header=True)
        second = self.writer(frames[2:], header=True)
        output = Path(self.temp.name) / 'concatenated.com_trajectory'
        output.write_text(first + second)
        with self.assertRaises(ValueError):
            diffusion.read_com_trajectory(output)

    def test_temporary_bonds_do_not_merge_permanent_membership_or_storage_order(self):
        points = [[4.8, 0, 0], [-4.8, 0, 0], [1., 0, 0], [1.4, 0, 0], [20., 0, 0]]
        permanent = [(0, 1), (2, 3)]
        with_temporary = permanent + [(1, 2)]
        first = bond_com(points, permanent, members=[0, 1])
        second = bond_com(points, permanent, members=[2, 3])
        np.testing.assert_allclose(bond_com(points, with_temporary, members=[0, 1]), first)
        np.testing.assert_allclose(bond_com(points, with_temporary, members=[2, 3]), second)
        frames = np.array([points, np.asarray(points) + [21., 0., 0.]])
        output = self.writer(frames, molecules=[1, 1, 2, 2, 0], types=[1, 2, 1, 2, 3],
                             bonds=permanent, order=[[4, 3, 1, 0, 2], [0, 2, 4, 1, 3]])
        np.testing.assert_allclose(output[0], [first, second])
        np.testing.assert_allclose(output[1] - output[0], [[21., 0., 0.]] * 2)

    def test_metadata_is_required_legacy_is_explicitly_unverified(self):
        frames = np.array([[[0., 0, 0]], [[21., 0, 0]]])
        corrected = self.writer(frames, header=True)
        output = Path(self.temp.name) / 'metadata.com_trajectory'
        output.write_text(corrected)
        _, _, loaded = diffusion.read_com_trajectory(output)
        np.testing.assert_allclose(loaded, frames)
        for old, new in (('KG_COM_TRANSPORT 2', 'KG_COM_TRANSPORT 3'),
                         ('native_continuous_plus_initial_backbone_offsets', 'wrapped'),
                         ('independent_segment_no_concatenation', 'unverified_continuation'),
                         ('# cadence_steps 1', '# cadence_steps 2'),
                         ('# unit_mass 1', '# unit_mass 2'),
                         ('# molecule_ids 1', '# molecule_ids 2')):
            output.write_text(corrected.replace(old, new))
            with self.subTest(field=old), self.assertRaises(ValueError):
                diffusion.read_com_trajectory(output, allow_legacy=True)
        output.write_text(com_transport.COLUMNS + '\n0 0 1 0 0 0\n1 1 1 1 0 0\n')
        with self.assertRaisesRegex(ValueError, 'legacy COM'):
            diffusion.read_com_trajectory(output)
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter('always')
            diffusion.read_com_trajectory(output, allow_legacy=True)
            metadata = com_transport.metadata_for(output, allow_legacy=True)
        self.assertTrue(metadata['legacy_unverified'])
        self.assertTrue(captured)

    def test_all_com_consumers_enforce_the_coordinate_contract(self):
        frames = np.array([[[0., 0, 0]], [[21., 0, 0]]])
        corrected = self.writer(frames, header=True)
        output = Path(self.temp.name) / 'consumers.com_trajectory'
        readers = (lambda: campaign.read_com_frames(output, 1),
                   lambda: walking.read_com(output),
                   lambda: list(percolation.read_com_frames(output, {1})))
        output.write_text(corrected)
        for reader in readers:
            reader()
        for invalid in (corrected.replace(com_transport.CONVENTION, 'wrapped'),
                        corrected.replace('1 1 1 21', '1 1 1 nan')):
            output.write_text(invalid)
            for reader in readers:
                with self.assertRaises(ValueError):
                    reader()

    def test_stable_noncontiguous_molecule_ids_and_independent_origins(self):
        frames = np.array([[[0., 0, 0]], [[21., 0, 0]]])
        output = Path(self.temp.name) / 'ids.com_trajectory'
        output.write_text(self.writer(frames, molecules=[42], header=True))
        steps, times, positions = diffusion.read_com_trajectory(output)
        metadata = com_transport.metadata_for(output)
        self.assertEqual(metadata['molecule_ids'], [42])
        first = dict(path='first', steps=steps, times=times, positions=positions,
                     transport_metadata=metadata)
        second = dict(first, path='second')
        with self.assertRaisesRegex(ValueError, 'share an origin'):
            diffusion.validate_replica_ensemble([first, second])
        second['transport_metadata'] = dict(metadata, origin_id='second-independent-origin')
        diffusion.validate_replica_ensemble([first, second])
        second['transport_metadata'] = dict(second['transport_metadata'], box_bounds=[-6, 6] * 3)
        with self.assertRaisesRegex(ValueError, 'incompatible'):
            diffusion.validate_replica_ensemble([first, second])

    def test_unsupported_cell_and_continuation_preflight(self):
        path = Path(self.temp.name) / 'geometry.lammpsdat'
        orthorhombic = 'LAMMPS data\n-5 5 xlo xhi\n-5 5 ylo yhi\n-5 5 zlo zhi\nAtoms\n'
        path.write_text(orthorhombic)
        subprocess.check_call([str(self.executable), str(path), 'preflight', 'independent'])
        for text, request in ((orthorhombic, 'continuation'),
                              (orthorhombic.replace('Atoms', '0 0 0 xy   xz\t yz\nAtoms'),
                               'independent'),
                              ('LAMMPS archival data from kg_assoc_campaign_production\nAtoms\n',
                               'independent')):
            path.write_text(text)
            with self.subTest(request=request), self.assertRaises(subprocess.CalledProcessError):
                subprocess.check_output([str(self.executable), str(path), 'preflight', request],
                                        stderr=subprocess.PIPE)

    def test_internal_coordinate_folding_invalidates_the_native_contract(self):
        base = np.array([[4.8, 0, 0], [-4.8, 0, 0]])
        native = base[None] + np.array([0., .4])[:, None, None] * [1., 0., 0.]
        np.testing.assert_allclose(self.writer(native)[:, 0, 0], [5., 5.4])
        with self.assertRaises(subprocess.CalledProcessError):
            self.writer(folded(native))

    def test_unit_mass_com_and_velocity_mean(self):
        points = np.array([[1., 2, 3], [1.2, 2.3, 3.4]])
        velocities = np.array([[2., 0, 0], [0., 2, 0]])
        np.testing.assert_allclose(self.writer([points])[0, 0],
                                   np.average(points, axis=0, weights=[1., 1.]))
        np.testing.assert_allclose(np.mean(velocities, axis=0),
                                   np.average(velocities, axis=0, weights=[1., 1.]))
        self.assertFalse(np.allclose(self.writer([points])[0, 0],
                                     np.average(points, axis=0, weights=[1., 3.])))


if __name__ == '__main__':
    unittest.main()
