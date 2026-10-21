"""Private module bindings reuse frozen D1.1 helpers without mutating their imports."""
import importlib.util
from pathlib import Path


def bind(name, specification):
    path=Path(__file__).with_name('e1_d1_pilot_'+name+'.py')
    definition=importlib.util.spec_from_file_location('_d13_frozen_'+name,path)
    module=importlib.util.module_from_spec(definition)
    definition.loader.exec_module(module)
    module.spec=specification
    return module
