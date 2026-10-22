"""Reusable CLI: compile an exercise phase into explicit animation inputs."""
import argparse
import json
from pathlib import Path
from . import contract, registry

ROOT=Path(__file__).resolve().parents[2]
LIBRARY=Path(__file__).with_name('exercise_contracts.json')


def load_inputs():
    seed=json.loads(registry.SEED.read_text())
    muscles=registry.expand(seed)
    library=json.loads(LIBRARY.read_text())
    errors=contract.validate_library(library,muscles)
    if errors: raise ValueError(errors)
    return library,muscles


def compile_request(exercise_id,phase_id,progress,activation_scale):
    library,_=load_inputs()
    try: exercise=next(e for e in library['exercises'] if e['id']==exercise_id)
    except StopIteration: raise ValueError('unknown exercise')
    output=contract.sample_phase(exercise,phase_id,progress,activation_scale)
    output['contract_version']=library['contract_version']
    output['PT_MODEL_VERSION']=library['PT_MODEL_VERSION']
    output['source_ids']=exercise['source_ids']
    output['instruction']=exercise['instruction']
    return output


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--exercise',required=True)
    p.add_argument('--phase',required=True)
    p.add_argument('--progress',type=float,required=True)
    p.add_argument('--activation-scale',type=float,default=1)
    p.add_argument('--out',type=Path)
    a=p.parse_args()
    result=compile_request(a.exercise,a.phase,a.progress,a.activation_scale)
    text=json.dumps(result,indent=2)+'\n'
    if a.out:
        with a.out.open('x') as f: f.write(text)
    else: print(text,end='')

if __name__=='__main__': main()
