"""Optimized CPU call-path tests; the device callback is a spy, never a GPU readback."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

import kg_assoc_e2 as e2
import kg_assoc_e2_extension as extension
import run_ea_extensions as runner


class ReadbackCallPathTests(unittest.TestCase):
    def test_optimized_exact_production_block_invokes_readback_and_stops_before_MD(self):
        source = (e2.HERE.parent/'kg_assoc_stars.cu').read_text()
        begin = source.index('    kg_assoc_test::dispatchInitialReadback(')
        end = source.index('\n#endif', begin)
        block = source[begin:end]
        self.assertLess(end, source.index('      integrator->forwardTime();'))
        self.assertEqual(block.count('initialDeviceReadback('), 1)
        before = r'''
#include "kg_assoc_readback_dispatch.cuh"
struct Parameters { bool reseedChemistry; bool e2Extension; };
int calls = 0;
bool fail = false;
void initialDeviceReadback(const Parameters&, int, int, int, int, int, int) {
  ++calls;
  if (fail) { throw std::runtime_error("CPU spy missing required readback"); }
}
int main() {
  for (bool reseed : {false, true}) {
    for (bool extension : {false, true}) {
      for (bool missing : {false, true}) {
        Parameters parameters{reseed, extension};
        int data=0, simulationBox=0, particles=0, state=0, lengths=0, diagnosticContext=0;
        calls=0;
        fail=missing;
        bool integrated=false;
        try {
'''
        after = r'''
          integrated=true;
        } catch (const std::runtime_error&) {}
        if (calls != int(reseed || extension) ||
            integrated != (!missing || !(reseed || extension))) { return 1; }
      }
    }
  }
}
'''
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            for mutation in (False, True):
                body = block.replace('parameters.e2Extension', 'false') if mutation else block
                path = root/'probe.cu'
                path.write_text(before+body+after)
                executable = root/'probe'
                subprocess.run(['/usr/local/cuda-12.8/bin/nvcc',
                    '-ccbin=/usr/local/gcc-11.2.0/bin/g++','-O3','-std=c++14',
                    '-I'+str(e2.HERE.parent),str(path),'-o',str(executable)],
                    check=True,capture_output=True,text=True,timeout=60)
                result = subprocess.run([str(executable)],timeout=60)
                self.assertEqual(result.returncode, int(mutation))

    def test_ordinary_and_reseeded_physical_source_is_unchanged_except_validation_dispatch(self):
        old = subprocess.check_output(['git','show',
            '32adf91b3dda2ef94b535597744234685d422e87:examples/KG_Assoc/kg_assoc_stars.cu'],text=True)
        current = (e2.HERE.parent/'kg_assoc_stars.cu').read_text()
        begin = current.index('    kg_assoc_test::dispatchInitialReadback(')
        end = current.index('\n#endif',begin)
        old_begin = old.index('    if (parameters.reseedChemistry) {\n      initialDeviceReadback(')
        old_end = old.index('\n#endif',old_begin)
        current = current[:begin]+old[old_begin:old_end]+current[end:]
        marker = '      const double requestedEa = targetEa;'
        self.assertEqual(old.split(marker,1)[1], current.split(marker,1)[1])
        marker = 'void initialDeviceReadback('
        self.assertEqual(old[old.index(marker):old.index('int main(')],
                         current[current.index(marker):current.index('int main(')])

    def test_unknown_or_old_native_build_is_rejected(self):
        for build in ({},dict(source_sha256={'kg_assoc_stars.cu':'unknown'})):
            with self.assertRaisesRegex(ValueError,'not authenticated'):
                e2.require_extension_readback_build(build)

    def test_new_state_is_separate_and_original_failed_campaign_is_unchanged(self):
        self.assertEqual(runner.STATE_DIRECTORY,'manual_ea_extensions_readback_v2')
        old = e2.HERE.parent/'kg_assoc_100m/aggregate/e2/manual_ea_extensions_v1/state.json'
        before = old.read_bytes()
        self.assertEqual(json.loads(before)['jobs'][0]['status'],'failed')
        frozen = e2.campaign.load_json(e2.HERE.parent/
            'reviews/e2_ea8_extension_readback_forensics_20261019/ORIGINAL_FILES.sha256')
        e2.check_hashes(frozen)
        self.assertEqual(old.read_bytes(),before)

    def test_corrected_optimized_binary_probe_and_tampering(self):
        build = e2.HERE.parent/'kg_assoc_100m/builds'/extension.BUILD/'manifest.json'
        if not build.exists():
            self.skipTest('fresh optimized build not compiled yet')
        record = e2.campaign.load_json(build)
        e2.require_extension_readback_build(record)
        with mock.patch.object(e2.subprocess,'check_output',return_value='bad CPU probe'):
            with self.assertRaisesRegex(ValueError,'probe failed'):
                e2.require_extension_readback_build(record)


if __name__ == '__main__':
    unittest.main()
