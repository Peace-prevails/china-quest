"""Run all offline acceptance checks and persist a versioned, secret-free report."""
import argparse
from datetime import datetime
import json
import platform
import subprocess
import sys
from zoneinfo import ZoneInfo
from common import ROOT, write


def checkpoint(label):
    commands = [
        [sys.executable, 'scripts/validate_story.py'],
        [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
        [sys.executable, 'scripts/generate_assets.py', '--dry-run', '--max-images', '12'],
    ]
    results = []
    for cmd in commands:
        result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        # Tests use fake credentials only; dry-run never prints environment secrets.
        results.append({'command': ['python3', *cmd[1:]], 'exit_code': result.returncode,
                        'stdout': result.stdout, 'stderr': result.stderr})
        print(('PASS' if result.returncode == 0 else 'FAIL'), ' '.join(cmd[1:]))
    report = {'label': label, 'time': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
              'python': platform.python_version(), 'paid_api_calls': 0,
              'passed': all(r['exit_code'] == 0 for r in results), 'checks': results}
    if not label.replace('-', '').replace('_', '').isalnum():
        raise ValueError('Use an alphanumeric checkpoint label')
    path = ROOT / 'docs/checkpoints' / (label + '.json')
    if path.exists():
        raise ValueError('Checkpoint already exists; choose a new label')
    write(path, report)
    print(path)
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('label')
    raise SystemExit(0 if checkpoint(parser.parse_args().label) else 1)
