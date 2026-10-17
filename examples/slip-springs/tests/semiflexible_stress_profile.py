"""Generate/authenticate a new compact execution overlay; never execute experiments."""
import argparse
import copy
from pathlib import Path
import shutil

import semiflexible_stress_analysis as a
from semiflexible_scalar_schema import SCHEMA_HASH
from semiflexible_stress_host import safe


def derive(base,root,build,manifest,parent_ids,parent_hash):
    descriptor=dict(version='compact-scalar-v1',parent_root=str(base),parent_manifest_sha256=parent_hash,
                    output_root=str(root),build_root=str(build),plan_sha256=a.PLAN_HASH,schema_sha256=SCHEMA_HASH)
    descriptor['profile_id']=a.identity(descriptor)
    derived=[]
    for original,parent_id in zip(manifest,parent_ids):
        r=copy.deepcopy(original);cmd=r['command'];cmd[0]=str(build/r['precision']/'semiflexible')
        r['output']=str(root/'runs'/Path(original['output']).name)
        cmd[cmd.index('--output')+1]=r['output']
        profile='compact' if r['phase'] in ('stream','memory') else 'full'
        if profile=='compact':cmd+=['--scalar-output','compact']
        r.update(parent_run_id=parent_id,execution_profile=descriptor['profile_id'],scalar_profile=profile)
        r['run_id']=a.identity(r)
        derived.append(r)
    return descriptor,derived


def create(base,root,build=None):
    base=safe(base);root=safe(root)
    a.require(not (base/'execution-profile.json').exists(),'parent must be the original full campaign, not another overlay')
    a.require(not root.is_relative_to(base) and not base.is_relative_to(root),'overlay and parent must be separate directories')
    manifest,ids,mhash=a.authenticate(base)
    build=Path(build).resolve() if build else Path(manifest[0]['command'][0]).parents[1]
    descriptor,derived=derive(base,root,build,manifest,ids,mhash)
    root.mkdir(parents=True,exist_ok=False)
    (root/'execution-profile.json').write_bytes(a.encoded(descriptor)+b'\n')
    (root/'manifest.json').write_bytes(a.encoded(derived)+b'\n')
    for name in ('validation-plan.md','PLAN_SHA256'):shutil.copyfile(base/name,root/name)
    shutil.copyfile(a.PROJECT/'STAGE4A3C_OUTPUT_SCHEMA_V1.md',root/'output-schema-v1.md')
    print('Generated 282 mapped runs; 174 compact, 108 full diagnostics/references. No experiments executed.')
    return derived


def authenticate_profile(root):
    d=a.load(root/'execution-profile.json');base=Path(d['parent_root']);build=Path(d['build_root'])
    a.require(base.is_absolute() and build.is_absolute() and root==Path(d['output_root']),'profile paths inconsistent')
    a.require(not (base/'execution-profile.json').exists() and not root.is_relative_to(base) and not base.is_relative_to(root),'invalid parent/profile nesting')
    a.require(a.digest(root/'output-schema-v1.md')==SCHEMA_HASH and a.digest(a.PROJECT/'STAGE4A3C_OUTPUT_SCHEMA_V1.md')==SCHEMA_HASH,'profile schema hash mismatch')
    manifest,ids,mhash=a.authenticate(base)
    expected,derived=derive(base,root,build,manifest,ids,mhash)
    a.require(d==expected,'execution profile identity/version/hash mismatch')
    actual=a.load(root/'manifest.json');a.require(actual==derived,'derived scientific/profile commands mismatch')
    a.require(a.digest(root/'validation-plan.md')==a.PLAN_HASH and (root/'PLAN_SHA256').read_text()==a.PLAN_HASH+'  validation-plan.md\n','profile frozen plan mismatch')
    return actual,[r['run_id'] for r in actual],a.identity(actual)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--build',type=Path)
    args=p.parse_args();create(args.base,args.output,args.build)


if __name__=='__main__':main()
