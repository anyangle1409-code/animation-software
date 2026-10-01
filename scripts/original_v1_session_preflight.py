#!/usr/bin/env python3
"""Read-only laptop session checks. Never fetch/reset, kill a process or edit files."""
from __future__ import annotations
import argparse
import ctypes
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from original_v1_production_control import ROOT,CAND,RC,build,read,digest


def run(args,root=ROOT):
    return subprocess.check_output(args,cwd=root,text=True,stderr=subprocess.PIPE,timeout=20).strip()


def repository_issues(branch,expected,head,live,tree):
    issues=[]
    if branch!=expected: issues.append('wrong branch: '+str(branch)+'; expected '+expected)
    if not live: issues.append('live branch HEAD unavailable; cannot establish current state')
    elif head!=live: issues.append('local HEAD differs from live HEAD; read/preserve newer work before starting')
    if tree: issues.append('working tree has uncommitted/unknown files; inspect and commit known work first')
    return issues


def collision_issues(root,rev,solution):
    files=[f'{CAND}/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{rev}.blend',
           f'{CAND}/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{rev}.json',
           f'{CAND}/weight_solutions/{solution}',f'{CAND}/weight_solutions/{Path(solution).stem}.json',
           f'{CAND}/review/visual_{rev}']
    files += [f'{RC}/{group}_{rev}' for group in ('neutral','shoulder','hand','hip','pushup','row')]
    files += [p.relative_to(root).as_posix() for p in (root/RC).glob(f'full_{rev}_*')]
    return ['output collision: '+p for p in sorted(set(files)) if (root/p).exists()]


def blender_path():
    configured=os.environ.get('BLENDER_EXE')
    if configured: return Path(configured) if Path(configured).is_file() else None
    found=shutil.which('blender.exe') or shutil.which('blender')
    if found:return Path(found)
    if os.name=='nt':
        files=sorted(Path(os.environ.get('ProgramFiles','C:/Program Files')).glob('Blender Foundation/Blender */blender.exe'))
        if files:return files[-1]
    return None


def power_info():
    if os.name!='nt': return {'available':False,'reason':'Windows power API unavailable on this platform'}
    class Power(ctypes.Structure):
        _fields_=[('ac',ctypes.c_ubyte),('flag',ctypes.c_ubyte),('percent',ctypes.c_ubyte),
                  ('reserved',ctypes.c_ubyte),('seconds',ctypes.c_ulong),('full_seconds',ctypes.c_ulong)]
    p=Power()
    try:
        if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(p)):
            return {'available':False,'reason':'GetSystemPowerStatus failed'}
        return {'available':True,'ac':'connected' if p.ac==1 else 'disconnected' if p.ac==0 else 'unknown',
                'battery_percent':None if p.percent==255 or p.flag & 128 else p.percent,
                'runtime_seconds':None if p.seconds==0xffffffff else p.seconds,
                'note':'OS-reported information only; no solve-duration guarantee.'}
    except (AttributeError,OSError) as exc:return {'available':False,'reason':str(exc)}


def process_info():
    if os.name!='nt':return {'available':False,'reason':'Windows process inventory unavailable'}
    try:
        command="Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(blender|python|pythonw|py).*\\.exe$' } | Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress"
        raw=run(['powershell','-NoProfile','-NonInteractive','-Command',command])
        rows=json.loads(raw) if raw else [];rows=[rows] if isinstance(rows,dict) else rows
        conflicts=[{'pid':r['ProcessId'],'name':r['Name']} for r in rows if r['ProcessId']!=os.getpid() and
                   ('blender' in r['Name'].lower() or 'optimize_original_v1' in (r.get('CommandLine') or ''))]
        return {'available':True,'conflicts':conflicts,'note':'No process is terminated by preflight.'}
    except (OSError,ValueError,subprocess.SubprocessError) as exc:return {'available':False,'reason':str(exc)}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--minimum-free-gib',type=float,default=2.0)
    ap.add_argument('--evidence-only',action='store_true',help='Check read-only evidence environment/source without optimiser inputs or next-task outputs')
    ap.add_argument('--json',action='store_true');args=ap.parse_args()
    issues=[];info={'python':sys.executable,'python_version':sys.version.split()[0]}
    try:
        control=read(ROOT,'ORIGINAL_V1_PRODUCTION_CONTROL.json')
        branch=run(['git','branch','--show-current']);head=run(['git','rev-parse','HEAD'])
        tree=run(['git','status','--porcelain','--untracked-files=all'])
        try:
            raw=run(['git','ls-remote','--exit-code','origin','refs/heads/'+control['branch']])
            live=raw.split()[0] if raw else None
        except (OSError,subprocess.SubprocessError):live=None
        issues+=repository_issues(branch,control['branch'],head,live,tree)
        info.update(branch=branch,local_head=head,live_head=live,working_tree=tree or 'clean')
        state,_=build(ROOT);info['next_action']=state['next_action']
        if state['next_action']['action']=='STOP' and not args.evidence_only: issues.append(state['next_action']['reason'])
        bp=blender_path();info['blender']=str(bp) if bp else None
        if not bp: issues.append('Blender executable unavailable; set BLENDER_EXE to its exact path')
        free=shutil.disk_usage(ROOT).free;info['disk_free_bytes']=free
        if args.minimum_free_gib<=0:issues.append('minimum-free-gib must be positive')
        elif free<args.minimum_free_gib*1024**3:issues.append('insufficient disk space for evidence; minimum '+str(args.minimum_free_gib)+' GiB')
        source=state['current_candidate'] if args.evidence_only else state['next_action'].get('execution_parent') or state['current_candidate']
        mp=f'{CAND}/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{source}.json';man=read(ROOT,mp)
        candidate=ROOT/CAND/man['candidate'];info['local_candidate']=str(candidate)
        if not candidate.is_file(): issues.append('required local candidate missing: '+str(candidate))
        elif digest(candidate)!=man['candidate_sha256']:issues.append('local candidate hash differs from committed manifest')
        if state['next_action']['action']=='RUN r30' and not args.evidence_only:
            init=ROOT/CAND/'weight_solutions/o21.npz'
            if not init.is_file() or digest(init)!=man.get('solution_sha256'):issues.append('o21 warm-start missing or hash mismatch')
            issues+=collision_issues(ROOT,'r30','o22.npz')
            # Only dependencies the r30 pipeline actually imports: the optimiser/dump/apply/pose-test
            # scripts are numpy-only (L-BFGS is project-owned); no repository script imports scipy.
            for pkg in ('numpy',):
                if importlib.util.find_spec(pkg) is None:issues.append('Python authoring dependency unavailable: '+pkg)
            info['dump']='r29_for_o22_dump.npz is disposable; existing runner regenerates it from verified r29'
        else:
            diagnostic=ROOT/RC/f'remaining_diagnostics_{source}'
            if not args.evidence_only and state['next_action']['action']=='RUN remaining diagnostics' and diagnostic.exists():
                issues.append('diagnostic output collision: '+str(diagnostic))
        info['power']=power_info();info['processes']=process_info()
        if info['processes'].get('conflicts'):issues.append('conflicting Blender/optimiser processes exist; inspect PIDs before starting')
        if not info['processes']['available']:info['process_note']='Process conflict check unavailable; inspect manually on laptop.'
        # Unknown battery is reported, never invented or treated as proof of AC.
        if info['power'].get('ac')=='disconnected':
            info['power_note']=('Battery is discharging. Connect AC for the approximately 70-minute r30 solve/evidence run.'
                if state['next_action']['action']=='RUN r30' and not args.evidence_only else
                'Battery is discharging. Connect AC for Blender evidence where practical; no duration guarantee.')
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as exc:issues.append(str(exc))
    result={'status':'STOP' if issues else 'SAFE TO START','issues':issues,'information':info,
            'scope':'Read-only checks; pending routine owner review does not block a session.'}
    if args.json:print(json.dumps(result,indent=2))
    else:
        print('STOP — '+('; '.join(issues)) if issues else 'SAFE TO START')
        print(json.dumps(info,indent=2))
    return 2 if issues else 0
if __name__=='__main__':raise SystemExit(main())
