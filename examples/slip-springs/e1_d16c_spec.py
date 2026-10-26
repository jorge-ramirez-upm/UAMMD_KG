"""D1.6C frozen read-only evidence and secondary-audit contract. No jobs on import."""
from pathlib import Path
import os

from e1_d1_pilot import require, load, encoded, digest, file_record, identity
from e1_d15_local import write, git, clean, local_env

PROJECT=Path(__file__).resolve().parent
CONFIG=PROJECT/'e1_d16c_config'
START='0f46ad6781cf48d6945b055b864b67f63b17e325'
FILES=('e1_d16c_spec.py','e1_d16c_json.py','e1_d16c_evidence.py','e1_d16c_audit.py',
       'e1_d16c_local.py','tests/test_e1_d16c.py','E1_STAGE_D16C_PROTOCOL_V1.md',
       'E1_STAGE_D16C_OPERATOR_GUIDE.md','E1_STAGE_D16C_IMPLEMENTATION_REPORT.md',
       'e1_d16c_config/original-lock.json','e1_d16c_config/protocol.json','e1_d16c_config/resources.json')


def durable(path):
    path=Path(path).expanduser().resolve()
    require(not any(path.is_relative_to(Path(p)) for p in ('/tmp','/var/tmp','/dev/shm')),'durable storage required')
    return path


def original():return load(CONFIG/'original-lock.json')


def tools():
    prior=load(Path(original()['root'])/'session.json')['sources']
    names=set(prior)|set(FILES)|{'e1_d1_pilot_runner.py','e1_d15_local.py','e1_observer_check.py',
        'e1_d16b_config/manifest.json','e1_d16b_config/manifest.sha256'}
    return {name:digest(PROJECT/name) for name in sorted(names)}


def resources(stage):
    value=load(CONFIG/'resources.json')[stage]
    require(stage in ('existing','audit','return','tests') and all(type(v) is int and v>0 for v in value.values()),
            'invalid frozen stage resources')
    return value


def fresh_output(parent):
    parent=durable(parent);old=Path(original()['root']).resolve()
    require(not parent.is_relative_to(old) and not old.is_relative_to(parent), 'new output must be separate from original evidence')
    require(not any((p/'.git').exists() for p in (parent,*parent.parents)),'returns must be outside Git')
    require(not any((p/'session.json').exists() for p in (parent,*parent.parents)), 'never nest new outputs inside existing evidence')
    parent.mkdir(parents=True,exist_ok=True)
    return parent


def checked(root):
    root=durable(root);session=load(root/'session.json');project=root/'preparation/examples/slip-springs'
    require(session['schema']=='e1-d16c-session-v1' and session['root']==str(root)
            and session['project']==str(project),'wrong D1.6C session')
    require(git(project,'rev-parse','HEAD')==session['commit'],'source commit changed')
    clean(project)
    require(session['tools']==tools()=={name:digest(project/name) for name in session['tools']},'source closure changed')
    require(str(Path(os.sys.executable).resolve())==session['python'],'use original Stage A Python')
    return session,project
