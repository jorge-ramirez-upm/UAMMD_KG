"""Deterministic CPU-only next-extension authorization and isolation regressions."""
import contextlib
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import kg_assoc_e2 as e2
import kg_assoc_e2_next_extension as extension
import kg_assoc_e2_readback as readback
import run_ea_next_extensions as runner
import test_e2_single_history as fixtures


class ScopeTests(unittest.TestCase):
    setUp = fixtures.SingleHistoryTests.setUp
    write_approval = fixtures.SingleHistoryTests.write_approval

    def configure(self, ea=8, execution=True):
        sid = f'F04_N010_RP080_EE08_EA{ea:02d}'
        start, end = extension.RANGES[sid]
        self.plan.update(lineage_mode=extension.MODE, reference_control=False, smoke=False,
                         steps=end-start, system=dict(system_id=sid), build={}, attempt=str(self.attempt))
        for h in self.plan['histories']:
            h.update(start_step=start,end_step=end)
        (self.attempt/'plan.json').write_text(json.dumps(self.plan))
        self.record.update(purpose='e2_derived_extension', selector_scope=extension.SCOPE,
            plan_sha256=e2.campaign.sha256(self.attempt/'plan.json'), authorized_system=sid,
            authorized_replicas=[1],maximum_additional_MD_steps_per_history=end-start,
            maximum_additional_MD_steps=end-start,absolute_start_step=start,absolute_end_step=end,
            diagnostic_window_steps=500000,GPU_execution_authorized=execution)
        self.write_approval(self.record)
        self.source = self.attempt/'sources.json'
        e2.exclusive_json(self.source,dict(schema_version=1,approved=True,
            purpose='e2_extension_source_authorization',plan_sha256=self.record['plan_sha256'],
            execution_approval_sha256=e2.campaign.sha256(self.approval),reviewer='CPU fixture',
            approved_at='fixture',source_sha256_overrides={'administrative.py':'exact-reviewed-hash'}))

    @contextlib.contextmanager
    def native(self, tamper=False, validation_error=None):
        def start(command,stdout,stderr,**kwargs):
            stdout.write('STAR_ASSOCIATION_SMOKE PASS\n')
            process = mock.Mock(pid=12345)
            def finished():
                if tamper:
                    self.source.write_text('changed authorization')
                return 0
            process.wait.side_effect = finished
            return process
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(e2,'check_plan',return_value=self.plan))
            stack.enter_context(mock.patch.object(e2,'require_extension_readback_build'))
            live = stack.enter_context(mock.patch.object(e2,'live_code'))
            stack.enter_context(mock.patch.object(e2,'matching_smoke',return_value={}))
            stack.enter_context(mock.patch.object(e2.socket,'gethostname',return_value='titan'))
            stack.enter_context(mock.patch.object(extension,'revalidate_parent'))
            stack.enter_context(mock.patch.object(extension,'process_identity',return_value={'pid':12345}))
            stack.enter_context(mock.patch.object(e2.subprocess,'check_output',return_value='CPU fixture'))
            validate = stack.enter_context(mock.patch.object(e2.validation,'validate',
                side_effect=validation_error,return_value=([],[],{'strict':'validated'})))
            popen = stack.enter_context(mock.patch.object(e2.subprocess,'Popen',side_effect=start))
            yield popen,live,validate

    def launch(self):
        e2.launch(self.root,self.attempt,True,self.approval,replicas=[1],source_authorization=self.source)

    def test_exact_ranges_and_explicit_selections(self):
        for ea in (8,10):
            self.configure(ea)
            self.assertEqual(e2.launch_scope(self.plan,None,[1,3]),
                             [self.plan['histories'][0],self.plan['histories'][2]])
            for selected in (None,[],[True],[4],[2,1],[1,1]):
                with self.assertRaises(ValueError):
                    e2.launch_scope(self.plan,None,selected)
            for key,value in [('steps',8000001),('smoke',True),('reference_control',True)]:
                plan = dict(self.plan,**{key:value})
                with self.assertRaises(ValueError): e2.launch_scope(plan,None,[1])
            self.source.unlink()

    def test_preparation_approval_rejects_gpu_before_popen(self):
        self.configure(execution=False)
        with self.native() as (popen,_,_), self.assertRaisesRegex(ValueError,'preparation only'):
            self.launch()
        popen.assert_not_called()
        self.assertEqual(list((self.attempt/'r001').iterdir()),[])

    def test_pre_and_post_run_use_identical_authorized_source_map(self):
        self.configure()
        with self.native() as (popen,live,validate):
            self.launch()
        self.assertEqual(popen.call_count,1)
        self.assertGreaterEqual(live.call_count,3)
        self.assertTrue(all(call.args == (self.plan,{'administrative.py':'exact-reviewed-hash'})
                            for call in live.call_args_list))
        validate.assert_called_once_with(self.plan['histories'][0],oracle=False)
        self.assertTrue((self.attempt/'r001/complete.json').exists())

    def test_source_authorization_tamper_after_native_pass_is_held(self):
        self.configure()
        with self.native(tamper=True), self.assertRaisesRegex(ValueError,'authenticated file changed'):
            self.launch()
        self.assertTrue((self.attempt/'r001/incomplete.json').exists())
        self.assertFalse((self.attempt/'r001/complete.json').exists())

    def test_missing_readback_fails_completion_and_never_retries(self):
        self.configure()
        with self.native(validation_error=FileNotFoundError('initial_device_validation.tsv')), \
                self.assertRaises(FileNotFoundError): self.launch()
        self.assertFalse((self.attempt/'r001/complete.json').exists())
        with self.native() as (popen,_,_), self.assertRaisesRegex(ValueError,'attempt already used'):
            self.launch()
        popen.assert_not_called()
        with self.assertRaises(FileNotFoundError):
            readback.check(self.attempt/'missing_readback.tsv',{}, {},[])

    def test_reused_outputs_preserve_unselected_directories(self):
        self.configure()
        sentinel = self.attempt/'r002/sentinel'
        sentinel.write_text('preserved')
        with self.native(): self.launch()
        self.assertEqual(sentinel.read_text(),'preserved')
        self.assertEqual(list((self.attempt/'r003').iterdir()),[])
        with self.native() as (popen,_,_), self.assertRaises(ValueError): self.launch()
        popen.assert_not_called()

    def test_tampered_scope_or_approval_hash_never_launches(self):
        self.configure()
        for change in ({'authorized_replicas':[True]}, {'maximum_additional_MD_steps':32000000},
                       {'absolute_start_step':24000000}, {'authorized_system':'wrong'}):
            self.write_approval(dict(self.record,**change))
            with self.native() as (popen,_,_), self.assertRaises(ValueError): self.launch()
            popen.assert_not_called()

    def test_command_preserves_chemistry_and_selects_reviewed_native_guard(self):
        entry = dict(parent=dict(kind='e2',prefix='/exact40M'),parent_Ea=8,physics=dict(Ea=8),
            start_step=40000000,end_step=48000000,lineage=dict(mode=extension.MODE,branch_id='family'),
            chemistry_seed=1220801,md_seed=1331016,output_prefix='/new/state')
        command = e2.command(entry,False)
        self.assertIn('--e2-reviewed-extension',command)
        self.assertNotIn('--reseed-chemistry-from',command)
        self.assertNotIn('--switch-ea-from',command)
        self.assertEqual(command[command.index('--steps')+1],'8000000')

    def test_duplicate_output_paths_are_rejected_by_plan_reconstruction(self):
        self.configure()
        plan = copy.deepcopy(self.plan)
        for h in plan['histories']: h['executable_directory'] = '/fixture_build'
        plan['reservation_sha256'] = {'fixture_policy':'hash'}
        expected = copy.deepcopy(plan)
        plan['histories'][1]['output_prefix'] = plan['histories'][0]['output_prefix']
        with mock.patch.object(e2,'check_hashes'), \
                mock.patch.object(extension,'inspect',return_value=expected), \
                self.assertRaisesRegex(ValueError,'plan differs'):
            extension.check_plan(self.root,self.attempt,plan)


class ParentAndStateTests(unittest.TestCase):
    def test_frozen_device_readback_body_and_dispatch_are_unchanged(self):
        native = e2.HERE.parent/'kg_assoc_stars.cu'
        previous = e2.subprocess.check_output(['git','show',extension.PARENT_SOURCE_COMMIT+':'+
            str(native.relative_to(e2.campaign.REPOSITORY_ROOT))],text=True)
        current = native.read_text()
        marker = 'void initialDeviceReadback('
        self.assertEqual(previous[previous.index(marker):previous.index('int main(')],
                         current[current.index(marker):current.index('int main(')])
        self.assertIn('parameters.reseedChemistry, parameters.e2Extension, [&]() {',current)
        self.assertIn('parameters.reviewedExtension = true;',current)
        self.assertEqual(e2.campaign.sha256(e2.HERE.parent/'kg_assoc_readback_dispatch.cuh'),
                         '27b78580c23a285c5a1375ad953583ea6f841c75104f2bb6af69c35b1d582812')

    def test_historical_source_map_matches_starting_commit(self):
        sources = extension.historical_sources()
        self.assertEqual(sources[str(e2.HERE.parent/'kg_assoc_stars.cu')],
                         '9c0e9269b761ff38c07c8d5d2bc0da54d80dab42374030cb2cc39892b18f2c85')

    def test_all_six_real_parents_and_recovered_identity(self):
        root = e2.HERE.parent/'kg_assoc_100m'
        for sid in extension.RANGES:
            plan,rows = extension.predecessor(root,sid)
            self.assertEqual(len(rows),3)
            self.assertEqual(plan['system']['system_id'],sid)
            for row in rows:
                self.assertEqual(int(row['end_step']),extension.RANGES[sid][0])
            if sid.endswith('EA08'):
                self.assertTrue(rows[0]['receipt'].endswith('validation_recovery.json'))

    def test_old_build_rejected_for_new_scope(self):
        build = e2.HERE.parent/'kg_assoc_100m/builds'/extension.legacy.BUILD
        record = e2.campaign.load_json(build/'manifest.json')
        with mock.patch.object(e2,'check_build',return_value=(record,build/'manifest.json')), \
                self.assertRaisesRegex(ValueError,'reviewed extension guard'):
            extension.check_build(build)

    def test_mismatched_executable_rejected_before_native_probe(self):
        with tempfile.TemporaryDirectory() as folder:
            build = Path(folder)
            executable = build/'kg_assoc_stars_candidate_smoke'
            executable.write_text('wrong bytes')
            record = dict(out_of_tree=True,source_sha256={str(e2.HERE.parent/'kg_assoc_stars.cu'):
                extension.NATIVE_HASH,str(e2.HERE.parent/'kg_assoc_readback_dispatch.cuh'):
                '27b78580c23a285c5a1375ad953583ea6f841c75104f2bb6af69c35b1d582812'},
                executable_sha256={str(executable):'does-not-match'})
            with mock.patch.object(e2,'check_build',return_value=(record,build/'manifest.json')), \
                    mock.patch.object(e2.subprocess,'check_output') as probe, \
                    self.assertRaisesRegex(ValueError,'authenticated file changed'):
                extension.check_build(build)
            probe.assert_not_called()

    def test_tampered_parent_hash_rejected_without_touching_real_outputs(self):
        original = e2.campaign.sha256
        def altered(path):
            return 'corrupt' if str(path).endswith('.restart.lammpsdat') else original(path)
        with mock.patch.object(e2.campaign,'sha256',side_effect=altered), \
                self.assertRaisesRegex(ValueError,'authenticated file changed'):
            extension.predecessor(e2.HERE.parent/'kg_assoc_100m',list(extension.RANGES)[0])

    def test_forged_recovered_parent_is_rejected(self):
        original = e2.campaign.load_json
        def altered(path):
            record = original(path)
            if Path(path).name == 'validation_recovery.json':
                record['status'] = 'validated'
            return record
        with mock.patch.object(e2.campaign,'load_json',side_effect=altered), \
                self.assertRaisesRegex(ValueError,'recovery record'):
            extension.predecessor(e2.HERE.parent/'kg_assoc_100m',list(extension.RANGES)[0])

    def test_duplicate_reserved_md_stream_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            policy = root/'banks/e2_md_reservations/policy.json'
            attempt = root/'attempt'
            sid = list(extension.RANGES)[0]
            e2.exclusive_json(policy,dict(schema_version=1,purpose=extension.SCOPE,
                system=sid,attempt=str(attempt),streams=[dict(replica=r,md_seed=1234,
                effective_md_seed=e2.validation.effective_md_seed(1234)) for r in (1,2,3)]))
            with self.assertRaisesRegex(ValueError,'reservation collision'):
                extension.legacy.reservation(root,policy,attempt,sid,scope=extension.SCOPE)

    def test_next_mode_exact_source_matching_and_ancestry(self):
        plan = dict(lineage_mode=extension.MODE,git_sha='prepared',
            source_sha256={'administrative.py':'old','physics.cuh':'frozen'},
            executable_sha256={},build=dict(out_of_tree=True,build_log_sha256={},executable_sha256={}))
        for current,ancestor in [({'administrative.py':'new','physics.cuh':'corrupt'},True),
                ({'administrative.py':'new'},True),
                ({'administrative.py':'new','physics.cuh':'frozen','extra.py':'extra'},True),
                ({'administrative.py':'new','physics.cuh':'frozen'},False)]:
            with mock.patch.object(e2,'clean_tree'),mock.patch.object(e2,'sources',return_value=current), \
                    mock.patch.object(e2.campaign,'git_sha',return_value='live'), \
                    mock.patch.object(e2.subprocess,'run',return_value=mock.Mock(returncode=0 if ancestor else 1)), \
                    self.assertRaisesRegex(ValueError,'prepared extension sources/history changed'):
                e2.live_code(plan,{'administrative.py':'new'})

    def test_partial_bounds_use_correct_absolute_origin(self):
        with tempfile.TemporaryDirectory() as folder:
            prefix = Path(folder)/'state'
            Path(str(prefix)+'.candidate_validation.tsv').write_text('# sweep\n56000100 2 1\n56000200 2 1\n')
            bounds = extension.partial_step_bounds(prefix,56000000,32000000)
            self.assertEqual(bounds['completed_MD_steps_lower_bound'],200)
            self.assertFalse(bounds['exact_partial_MD_steps_known'])
            with self.assertRaises(ValueError): extension.partial_step_bounds(prefix,40000000,8000000)

    def test_completed_native_without_receipt_is_never_reclassified_as_partial(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            (p/'stdout.log').write_text('STAR_ASSOCIATION_SMOKE PASS\n')
            job = dict(plan_sha256='plan')
            entry = dict(output_prefix=str(p/'state'),command=['CPU fixture'])
            before = e2.hash_files(p.iterdir())
            self.assertEqual(runner.classify(job,entry),'native_PASS_validation_hold; never retry MD')
            self.assertEqual(e2.hash_files(p.iterdir()),before)


if __name__ == '__main__':
    unittest.main()
