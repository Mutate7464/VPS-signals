"""Stdlib helpers for the fib overnight chain (ops tooling, not application source).

  manifest <wi.md>                  -> print write_files paths (suffix ':...' stripped), one per line
  snapshot <out.json>               -> record git-dirty files + their sha1 (pre-builder state)
  audit <pre.json> <wi.md> <wi_path_now>  -> exit 1 + print offenders if anything outside the manifest changed
  lock <add|release> <WI-0XX> [<wi.md>]   -> edit .hermes/locks.json
"""
import hashlib
import json
import os
import subprocess
import sys

LOCKS = '.hermes/locks.json'
ALLOWED_PREFIXES = ('logs/', '.hermes/', 'reports/fib_swings/')  # run outputs + lock file + chain logs


def manifest(wi_md):
    out, on = [], False
    for line in open(wi_md):
        if line.startswith('write_files:'):
            on = True
            continue
        if on:
            if line.startswith('  - '):
                out.append(line[4:].strip().split(':')[0])
            else:
                break
    return out


def dirty():
    r = subprocess.run(['git', 'status', '--porcelain', '-uall'], capture_output=True, text=True).stdout
    files = {}
    for ln in r.splitlines():
        p = ln[3:].strip().strip('"')
        if ' -> ' in p:
            p = p.split(' -> ')[1]
        h = hashlib.sha1(open(p, 'rb').read()).hexdigest() if os.path.isfile(p) else 'missing'
        files[p] = h
    return files


def main():
    cmd = sys.argv[1]
    if cmd == 'manifest':
        print('\n'.join(manifest(sys.argv[2])))
    elif cmd == 'snapshot':
        json.dump(dirty(), open(sys.argv[2], 'w'))
    elif cmd == 'audit':
        pre = json.load(open(sys.argv[2]))
        allowed = set(manifest(sys.argv[3])) | {sys.argv[4]}
        bad = [p for p, h in dirty().items()
               if pre.get(p) != h and p not in allowed and not p.startswith(ALLOWED_PREFIXES)
               and '__pycache__' not in p]
        if bad:
            print('UNAUTHORIZED: ' + ' '.join(sorted(bad)))
            sys.exit(1)
        print('AUDIT_OK')
    elif cmd == 'lock':
        d = json.load(open(LOCKS)) if os.path.exists(LOCKS) else {'active_locks': {}, 'queue': []}
        wi = sys.argv[3]
        if sys.argv[2] == 'add':
            files = manifest(sys.argv[4])
            held = {f: o for o, fs in d['active_locks'].items() for f in fs if o != wi}
            clash = [f for f in files if f in held]
            if clash:
                print('LOCKED_BY_OTHER: ' + ' '.join(clash))
                sys.exit(1)
            d['active_locks'][wi] = files
        else:
            d['active_locks'].pop(wi, None)
        json.dump(d, open(LOCKS, 'w'), indent=2)
        print('LOCK_' + sys.argv[2].upper() + '_OK')


if __name__ == '__main__':
    main()
