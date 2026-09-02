#!/bin/bash
cd /Users/damanpreetsingh/jivo-cli/factory-cli
OUT=/Users/damanpreetsingh/jivo-cli/jolly/out/lines/detail
mkdir -p $OUT
ids=$(python3 -c "import json;print(' '.join(str(r['id']) for r in json.load(open('/Users/damanpreetsingh/jivo-cli/jolly/out/lines/aug-runs-oil.json'))['results']))")
n=0
for id in $ids; do
  if [ -s "$OUT/$id.json" ]; then continue; fi
  timeout 90 ./jivo-factory-pp-cli production-execution run-detail --id $id --json --no-input --no-color --yes --company JIVO_OIL --data-source live > "$OUT/$id.json" 2>/dev/null &
  n=$((n+1))
  if [ $((n % 6)) -eq 0 ]; then wait; fi
done
wait
ls $OUT | wc -l
