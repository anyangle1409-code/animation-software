#!/usr/bin/env python3
"""Recompute evidence and print one explicit next action; never launches modelling."""
import argparse
import json
import sys
from original_v1_production_control import ROOT,build

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--json',action='store_true');args=ap.parse_args()
    try:
        status,_=build(ROOT); action=status['next_action']
        print(json.dumps(action,indent=2) if args.json else action['action']+'\n'+action['reason']+'\n'+(action.get('command') or action.get('work_package','')))
        return 2 if action['action']=='STOP' else 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print('STOP — '+str(exc),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
