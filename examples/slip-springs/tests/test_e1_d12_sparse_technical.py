"""13-step noncampaign fixtures: independent scalar/spring schedules, either precision."""
import csv
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import e1_d1_pilot as old
from e1_observer_check import verify
BINARY=Path(sys.argv.pop(1)).resolve()


def steps(path):
    with path.open() as f:return {int(r['step']) for r in csv.DictReader(f)}


class SparseTechnicalTests(unittest.TestCase):
    def test_sparse_replay_and_schema(self):
        with tempfile.TemporaryDirectory(prefix='d12-sparse-') as tmp:
            root=Path(tmp);schedule=root/'full.steps';schedule.write_text('0 1 5 13\n')
            snapshots=root/'snapshots.steps';snapshots.write_text('0 5 13\n')
            cross_total=0
            for n,kappa,dt in ((8,0,'0.0001'),(32,10,'0.00025')):
                base=[str(BINARY),'--springs',str(n),'--chains','4','--kappa',str(kappa),
                      '--dt',dt,'--steps','13','--sample','2','--seed','914203',
                      '--slip-count','6','--slip-ms2','5','--hop-rate','20000',
                      '--end-renewal','1','--stress-mode','off','--scalar-output','full']
                outputs=[]
                for enabled in (False,True):
                    out=root/f'N{n}-{enabled}';outputs.append(out)
                    argv=base+['--output',str(out)]
                    if enabled:argv+=['--equilibrium-steps',str(schedule),'--equilibrium-snapshots',str(snapshots)]
                    p=subprocess.run(argv,capture_output=True,text=True,timeout=30)
                    self.assertEqual(p.returncode,0,p.stderr)
                off,on=outputs;verify(on)
                self.assertEqual(steps(on/'samples.csv'),set(range(0,14,2)))
                self.assertEqual(steps(on/'equilibrium_sites.csv'),{0,1,5,13})
                self.assertEqual(steps(on/'equilibrium_backbone.csv'),{1,5,13})
                self.assertEqual(steps(on/'equilibrium_positions.csv'),{0,5,13})
                for path in off.iterdir():
                    a,b=path.read_bytes(),(on/path.name).read_bytes()
                    if path.name=='metadata.json':
                        keys=[k for k in old.load(path) if 'seconds' in k or 'ns_per_bead_step' in k or k=='bead_updates_per_second']
                        pattern=rb'("(?:'+b'|'.join(k.encode() for k in keys)+rb')":)[^,}]*'
                        a,b=(re.sub(pattern,rb'\1TIMING',x) for x in (a,b))
                    self.assertEqual(a,b,path.name)
                hop=old.load(on/'hopping_metadata.json')
                self.assertGreater(hop['accepted'],0)
                cross_total+=hop['renewal_cross_chain']
            self.assertGreater(cross_total,0)


if __name__=='__main__':unittest.main()
