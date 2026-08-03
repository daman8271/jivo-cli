#!/usr/bin/env bash
# Fold a freshly-generated printing-press tree into the published ecom-cli,
# preserving every hand-authored file and re-applying every patch.
#
# `regen-merge --apply` is not used for a from-scratch reprint: it leaves
# value-drift and body-drift files at the PUBLISHED version for human review,
# which for a full regeneration means root.go never learns about the new
# commands and the build ships half-unwired. The workable sequence is: install
# the fresh tree wholesale, restore the NOVEL files, re-apply each hand-edit.
#
# What regen-merge IS good for is classification - run it with --json first and
# read `lost_registrations`. It correctly names every AddCommand call the fresh
# tree dropped. Note that root.go and auth.go classify as TEMPLATED-CLEAN even
# though both carry hand-edits, because the decl-set comparison cannot see
# AddCommand *calls* - "CLEAN" here does not mean "no hand-edit".
#
# usage: refold.sh <fresh-tree-dir> <emitted-spec.yaml>
set -euo pipefail
FRESH="${1:?usage: refold.sh <fresh-tree> <spec.yaml>}"
SPEC="${2:?usage: refold.sh <fresh-tree> <spec.yaml>}"
CLI="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$CLI"

[ -d "$FRESH/internal" ] || { echo "no internal/ in $FRESH"; exit 2; }
[ -f "$SPEC" ] || { echo "no spec at $SPEC"; exit 2; }

STAMP=$(date +%Y%m%d-%H%M%S)
BACKUP="/tmp/ecom-cli-prefold-$STAMP.tar.gz"
tar czf "$BACKUP" --exclude='jivo-ecom-pp-*' . && echo "backup -> $BACKUP"

# hand-authored files the press does not know about; a clean regen drops them
NOVEL=(jivo_login.go api_discovery.go api_discovery_test.go readonly_guard_test.go)
PRESERVE=$(mktemp -d)
for f in "${NOVEL[@]}"; do
  [ -f "internal/cli/$f" ]  && cp "internal/cli/$f"  "$PRESERVE/$f"
  [ -f "internal/mcp/$f" ]  && cp "internal/mcp/$f"  "$PRESERVE/$f"
done

rm -rf internal cmd
cp -R "$FRESH/internal" internal
cp -R "$FRESH/cmd" cmd
for f in go.mod go.sum README.md SKILL.md AGENTS.md manifest.json \
         tools-manifest.json .printing-press.json Makefile .golangci.yml .goreleaser.yaml; do
  [ -f "$FRESH/$f" ] && cp "$FRESH/$f" "$f"
done
# the press does NOT copy the spec into its output dir - install it explicitly,
# or the tree ships new code beside the previous spec and every consumer that
# reads spec.yaml (including the api-discovery test) sees the old surface.
cp "$SPEC" spec.yaml

for f in jivo_login.go api_discovery.go api_discovery_test.go; do
  [ -f "$PRESERVE/$f" ] && cp "$PRESERVE/$f" "internal/cli/$f"
done
[ -f "$PRESERVE/readonly_guard_test.go" ] && cp "$PRESERVE/readonly_guard_test.go" internal/mcp/

# Go stdlib CVE gate: the press pins the toolchain it generated with. Bumping
# the directive is the fix - Go downloads the patched toolchain itself and the
# host's own Go version does not need changing.
sed -i '' 's/^toolchain go1\.26\.4$/toolchain go1.26.5/' go.mod 2>/dev/null || \
  sed -i 's/^toolchain go1\.26\.4$/toolchain go1.26.5/' go.mod

python3 "$CLI/research/scripts/apply_patches.py"

gofmt -w internal cmd
go build -o jivo-ecom-pp-cli ./cmd/jivo-ecom-pp-cli
go build -o jivo-ecom-pp-mcp ./cmd/jivo-ecom-pp-mcp
go vet ./...
go test ./...
bash "$CLI/research/scripts/verify-patches.sh" ./jivo-ecom-pp-cli
echo "refold complete"
