#!/usr/bin/env python3
"""Run database-backed ingestion; obsolete county adapter stubs are not executed.

python3 state_manager.py --status
python3 state_manager.py --list MT
python3 state_manager.py MT --dry-run
python3 state_manager.py GA
python3 state_manager.py --all
"""
import argparse
import subprocess
from pathlib import Path
from backend.national_seed import STATES

def main():
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('state',nargs='?',type=str.upper,choices=sorted(STATES))
    actions=parser.add_mutually_exclusive_group()
    actions.add_argument('--status',action='store_true')
    actions.add_argument('--list',type=str.upper,choices=sorted(STATES),dest='list_state')
    actions.add_argument('--all',action='store_true')
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--county')
    args=parser.parse_args()
    root=Path(__file__).resolve().parent
    cmd=['docker','compose','run','--rm','--no-deps','-T','--volume',f'{root}/backend:/app/backend:ro','api','python','-m']
    if args.status or args.list_state:
        cmd += ['backend.coverage']
        if args.list_state: cmd += ['--state',args.list_state]
    elif args.state or args.all:
        cmd += ['backend.ingest']
        if args.state: cmd += ['--state',args.state]
        if args.county: cmd += ['--county',args.county]
        if args.dry_run: cmd += ['--dry-run']
    else:
        parser.error('Supply a state, --all, --status, or --list STATE')
    raise SystemExit(subprocess.call(cmd,cwd=root))

if __name__=='__main__': main()
