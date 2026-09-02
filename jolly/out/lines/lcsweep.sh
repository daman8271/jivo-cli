#!/bin/bash
cd /Users/damanpreetsingh/jivo-cli/factory-cli
OUT=/Users/damanpreetsingh/jivo-cli/jolly/out/lines/lcdetail
mkdir -p $OUT
ids=$(python3 -c "import json;print(' '.join(str(r['id']) for r in json.load(open('/Users/damanpreetsingh/jivo-cli/jolly/out/lines/lc-aug.json'))['results']))")
n=0
for id in $ids; do
  [ -s "$OUT/$id.json" ] && continue
  timeout 90 ./jivo-factory-pp-cli production-execution line-clearance-detail --id $id --json --no-input --no-color --yes --company JIVO_OIL --data-source live > "$OUT/$id.json" 2>/dev/null &
  n=$((n+1)); [ $((n % 6)) -eq 0 ] && wait
done
wait; ls $OUT | wc -l
