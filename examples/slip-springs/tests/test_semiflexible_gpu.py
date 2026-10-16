"""Bounded GPU verification, not Stage 4A.2 scientific acceptance."""
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from semiflexible_reference import Chain

BINARY = Path(sys.argv.pop(1)).resolve()


def write_parameters(path, model):
    path.write_text(str(model.n)+'\n'+''.join(f'{b:.17g} {k:.17g}\n' for b, k in zip(model.b0, model.kb))
                    +'\n'.join(f'{k:.17g}' for k in model.kappa)+'\n')


def read_csv(path):
    return np.atleast_1d(np.genfromtxt(path, delimiter=',', names=True))


def rg_prediction(model, kbt=1):
    total = 0
    for i in range(model.n):
        for j in range(i+1, model.n+1):
            k = np.r_[0, model.kappa[i+1:j], 0]
            total += Chain(model.b0[i:j], model.kb[i:j], k).equilibrium_predictions(kbt)['re2']
    return total/(model.n+1)**2


class GPUChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='semiflexible-bounded-')
        self.root = Path(self.temp.name)
        self.serial = 0

    def tearDown(self):
        self.temp.cleanup()

    def run_model(self, model, chains=1, positions=None, force=False, steps=0,
                  dt=1e-4, seed=42021, sample=1, kbt=1, zeta=1, extra=(), expect=True):
        self.serial += 1
        directory = self.root/str(self.serial)
        params = self.root/f'p{self.serial}.txt'
        write_parameters(params, model)
        args = [str(BINARY), '--springs', str(model.n), '--chains', str(chains),
                '--parameters', str(params), '--steps', str(steps), '--dt', str(dt),
                '--seed', str(seed), '--sample', str(sample), '--kbt', str(kbt),
                '--zeta', str(zeta), '--output', str(directory)]
        if positions is not None:
            initial = self.root/f'r{self.serial}.txt'
            np.savetxt(initial, np.asarray(positions).reshape(-1, 3), fmt='%.17g')
            args += ['--force-input' if force else '--initial', str(initial)]
        result = subprocess.run(args+list(extra), text=True, capture_output=True, timeout=90)
        if expect:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return directory, result

    def mean_check(self, values, target, floor=1e-5):
        values = np.asarray(values)
        se = np.std(values, axis=0, ddof=1)/math.sqrt(len(values))
        self.assertTrue(np.all(np.abs(values.mean(axis=0)-target) < 6*se+floor),
                        (values.mean(axis=0), target, se))

    def coords(self, directory, name='final.csv'):
        table = read_csv(directory/name)
        return np.column_stack([table[k] for k in ('x', 'y', 'z')])

    def test_force_cpu_geometry_symmetry_and_boundaries(self):
        r = np.array([[0, 0, 0], [1.1, 0, 0], [1.8, 0.7, -0.2], [2.1, 0.3, 0.9]])
        nearly = np.array([[0, 0, 0], [1, 0, 0], [2, 1e-4, 0], [1, 2e-4, 1e-5]])
        rotation, _ = np.linalg.qr(np.random.default_rng(321).normal(size=(3, 3)))
        models = [Chain.homogeneous(3, kappa=0), Chain.homogeneous(3, kappa=2),
                  Chain([0, 0.8, 1.2], [2, 15, 40], [0, 0, 1000, 0]),
                  Chain.homogeneous(1)]
        for model in models:
            n = model.n+1
            configs = np.array([r[:n], nearly[:n], r[:n] @ rotation + [1, -2, 3],
                                np.column_stack([np.arange(n), np.zeros(n), np.zeros(n)])])
            d, _ = self.run_model(model, chains=4, positions=configs, force=True)
            meta = json.loads((d/'metadata.json').read_text())
            single = meta['precision_bits'] == 32
            stored = self.coords(d, 'initial.csv').reshape(4, n, 3)
            f = read_csv(d/'forces.csv')
            actual = np.column_stack([f[k] for k in ('fx', 'fy', 'fz')]).reshape(4, n, 3)
            energies = f['energy'].reshape(4, n).sum(axis=1)
            for i in range(4):
                e, expected = model.energy_forces(stored[i])
                scale = max(1, np.max(np.abs(expected)))
                tol = (3e-6 if single else 3e-14)*max(1, model.kappa.max(), model.kb.max())
                np.testing.assert_allclose(actual[i], expected, rtol=3e-5 if single else 2e-12, atol=tol)
                self.assertAlmostEqual(energies[i], e, delta=(3e-6 if single else 3e-14)*max(1, abs(e)))
                np.testing.assert_allclose(actual[i].sum(axis=0), 0, atol=(3e-6 if single else 3e-14)*scale)
                torque = np.cross(stored[i]-stored[i].mean(axis=0), actual[i]).sum(axis=0)
                np.testing.assert_allclose(torque, 0, atol=(8e-6 if single else 8e-14)*scale)
            # Rotation/translation covariance, allowing stored-coordinate roundoff.
            np.testing.assert_allclose(actual[2], actual[0] @ rotation,
                                       atol=(1e-5 if single else 1e-12)*max(1, model.kappa.max(), model.kb.max()),
                                       rtol=1e-4 if single else 2e-12)

    def test_zero_path_and_heterogeneous_inactive_collapse(self):
        model = Chain.homogeneous(3, kappa=0)
        d, _ = self.run_model(model, chains=8, steps=3)
        meta = json.loads((d/'metadata.json').read_text())
        self.assertEqual(meta['bending_device_bytes'], 0)
        self.assertEqual(meta['bending_launches'], 0)
        self.assertEqual(meta['active_angles'], 0)
        model = Chain([0, 1, 1], [2, 3, 4], [0, 0, 2, 0])
        r = [[0, 0, 0], [0, 0, 0], [1, 0, 0], [1, 1, 0]]
        d, _ = self.run_model(model, positions=r, force=True)
        self.assertEqual(json.loads((d/'metadata.json').read_text())['active_angles'], 1)

    def test_diagnostics_and_cli_guards(self):
        for model in (Chain.homogeneous(2), Chain.homogeneous(2, b0=0, kappa=2)):
            d, result = self.run_model(model, positions=np.zeros((3, 3)), force=True, expect=False)
            failure = json.loads((d/'failure.json').read_text())
            self.assertEqual(failure['step'], 0)
            self.assertTrue((d/'failure_positions.csv').exists())
            self.assertIn('diagnostic failure', result.stderr)
        for extra in (('--dt', 'nan'), ('--sample', '0'), ('--zeta', '0'),
                      ('--steps', str(2**64//8+1)), ('--kb', '-1'), ('--unknown', '1')):
            self.run_model(Chain.homogeneous(1), extra=extra, expect=False)
        d, _ = self.run_model(Chain.homogeneous(1))
        result = subprocess.run([str(BINARY), '--output', str(d)], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        # An unstable finite force must produce a diagnosed nonfinite proposal,
        # or fail explicit precision validation; it must never silently clamp.
        d, result = self.run_model(Chain.homogeneous(1, b0=0, kb=1e30),
                                  positions=[[0, 0, 0], [1, 0, 0]], steps=2,
                                  extra=('--dt', '1e200'), expect=False)
        self.assertTrue((d/'failure.json').exists() or 'representable' in result.stderr)

    def test_replay_chain_isolation_and_parameter_path(self):
        model = Chain([0.8, 1.2, 1], [20, 40, 30], [0, 0, 3, 0])
        a, _ = self.run_model(model, chains=3, steps=5)
        b, _ = self.run_model(model, chains=3, steps=5)
        for name in ('initial.csv', 'final.csv', 'samples.csv', 'bond_statistics.csv'):
            self.assertEqual((a/name).read_bytes(), (b/name).read_bytes())
        c, _ = self.run_model(model, chains=7, steps=5)
        np.testing.assert_array_equal(self.coords(a), self.coords(c)[:12])
        self.assertEqual(json.loads((c/'metadata.json').read_text())['rng_domain'], 3)

    def test_noise_variance_and_center_of_mass(self):
        model = Chain.homogeneous(1, b0=0, kb=3, kappa=0)
        d, _ = self.run_model(model, chains=4096, positions=np.zeros((8192, 3)),
                              steps=1, dt=0.001, kbt=1, zeta=2)
        noise = self.coords(d)/math.sqrt(0.001)
        self.mean_check(noise, np.zeros(3))
        self.mean_check(noise**2, np.ones(3))
        self.mean_check(noise[:, 0]*noise[:, 1], 0)
        last = read_csv(d/'samples.csv')[-4096:]
        self.mean_check(last['cm_msd'], 6*0.001/(2*2))
        self.mean_check(last['monomer_msd'], 6*0.001/2)
        # Finite-rest-length internal forces also cancel in COM motion.
        d, _ = self.run_model(Chain.homogeneous(4, kappa=3), chains=2048, steps=20, sample=20)
        self.mean_check(read_csv(d/'samples.csv')['cm_msd'][-2048:], 6*0.002/5)

    def test_equilibrium_initialization_short_dynamics_and_observables(self):
        for model in (Chain.homogeneous(4, kappa=0), Chain.homogeneous(4, kappa=2),
                      Chain.homogeneous(2, kappa=1e-9), Chain.homogeneous(2, kappa=1000),
                      Chain([0.8, 1.2, 1], [20, 40, 30], [0, 0, 3, 0])):
            # Resolve the additional angular stiffness in the large-kappa smoke.
            h = 1e-6 if model.kappa.max() >= 1000 else 1e-4
            d, _ = self.run_model(model, chains=2048, steps=32, sample=32, dt=h)
            table = read_csv(d/'samples.csv')
            pred = model.equilibrium_predictions()
            for frame in (table[:2048], table[-2048:]):
                self.mean_check(frame['mean_r'], pred['mean_r'].mean())
                self.mean_check(frame['mean_r2'], pred['mean_r2'].mean())
                self.mean_check(frame['re2'], pred['re2'])
                self.mean_check(frame['rg2'], rg_prediction(model))
                for s in range(1, min(4, model.n-1)+1):
                    from semiflexible_reference import langevin
                    expected = np.mean([math.prod(langevin(k) for k in model.kappa[i+1:i+s+1])
                                        for i in range(model.n-s)])
                    self.mean_check(frame[f'tangent{s}'], expected)
            lengths = read_csv(d/'initial_bonds.csv')['length'].reshape(2048, model.n)
            self.mean_check(lengths, pred['mean_r'])
            self.mean_check(lengths**2, pred['mean_r2'])
            # Independent uniform-grid radial CDF, including the r^2 Jacobian.
            for bond, (b0, kb) in enumerate(zip(model.b0, model.kb)):
                grid = np.linspace(0, b0+14/math.sqrt(kb), 40001)
                w = grid**2*np.exp(-kb*(grid-b0)**2/2)
                cdf = np.r_[0, np.cumsum((w[1:]+w[:-1])*(grid[1]-grid[0])/2)]
                u = np.sort(np.interp(lengths[:, bond], grid, cdf/cdf[-1]))
                empirical = np.arange(1, len(u)+1)/len(u)
                self.assertLess(max(np.max(empirical-u), np.max(u-empirical+1/len(u))), 0.065)
            q = np.diff(self.coords(d, 'initial.csv').reshape(2048, model.n+1, 3), axis=1)
            for bead in range(1, model.n):
                cosine = np.sum(q[:, bead-1]*q[:, bead], axis=1)/(lengths[:, bead-1]*lengths[:, bead])
                x = model.kappa[bead]
                u = (np.sort(cosine)+1)/2 if x == 0 else (np.exp(x*(np.sort(cosine)-1))-np.exp(-2*x))/(-np.expm1(-2*x))
                empirical = np.arange(1, len(u)+1)/len(u)
                self.assertLess(max(np.max(empirical-u), np.max(u-empirical+1/len(u))), 0.065)
            stats = read_csv(d/'bond_statistics.csv')
            for row in stats:
                self.assertEqual(sum(row[f'bin{i}'] for i in range(33)), row['frames'])
            metadata = json.loads((d/'metadata.json').read_text())
            self.assertGreater(metadata['integration_ns_per_bead_step'], 0)
            self.assertEqual(metadata['update_launches'], 32)

    def test_timestep_refinement_controlled_gaussian_limit(self):
        model = Chain.homogeneous(2, b0=0, kb=3, kappa=0)
        biases, measured, errors = [], [], []
        for h in (0.04, 0.02, 0.01):
            steps = round(0.4/h)
            d, _ = self.run_model(model, chains=4096, steps=steps, sample=steps, dt=h)
            lam = 12*np.sin(np.arange(1, 3)*np.pi/6)**2
            a = 1-h*lam
            variance = a**(2*steps)/lam + 2*h*(1-a**(2*steps))/(1-a*a)
            expected = np.sum(lam*variance)/2  # 3 dimensions / (N*kb)
            values = read_csv(d/'samples.csv')['mean_r2'][-4096:]
            self.mean_check(values, expected)
            measured.append(abs(values.mean()-1))
            errors.append(values.std(ddof=1)/math.sqrt(len(values)))
            biases.append(expected-1)
        self.assertGreater(biases[0], biases[1])
        self.assertGreater(biases[1], biases[2])
        self.assertLess(measured[2], measured[0]+6*math.hypot(errors[0], errors[2]))


if __name__ == '__main__':
    unittest.main(verbosity=2)
