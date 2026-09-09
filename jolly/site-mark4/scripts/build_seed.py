#!/usr/bin/env python3
"""Generate public seed from a private snapshot. Never give the seed a fresh clock."""
import argparse
import json
from pathlib import Path
from serve_inputs import sanitize

def main():
    p=argparse.ArgumentParser();p.add_argument('--inputs',required=True);p.add_argument('--state',required=True);p.add_argument('--output',required=True);p.add_argument('--supplements',default=str(Path(__file__).with_name('supplements.json')));a=p.parse_args()
    supplements=json.loads(Path(a.supplements).read_text()) if Path(a.supplements).exists() else {}
    result=sanitize(json.loads(Path(a.inputs).read_text()),json.loads(Path(a.state).read_text()),supplements)
    result['meta']['fallback_snapshot']=True
    Path(a.output).write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n')
    print(f'Sanitized seed: {len(result["plan"])} plan rows, {len(result["items"])} relevant master records; as of {result["meta"]["as_of"]}')
if __name__=='__main__':main()
