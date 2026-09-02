#!/usr/bin/env bash
# publish-skills.sh — push new or edited skills to main automatically, so every
# operator box receives them at its next session start without anyone having to
# remember `git add`. Runs from a LaunchAgent on the authoring Mac every 10 min.
#
# Scope is exactly: .claude/skills/  and  harness/desks.json (per-desk exclusions).
# Nothing else in the (usually dirty) working tree is ever staged.
#
# The repo is PUBLIC. Anything that looks like a credential blocks the publish,
# writes a flag, and raises a macOS notification instead of pushing.
set -u
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO" || exit 0
LOG="${HOME}/Library/Logs/jivo-skills-autopublish.log"
FLAG="$REPO/harness/.skills-publish-blocked"
SCOPE=(.claude/skills harness/desks.json)
log(){ printf '%s %s\n' "$(date '+%F %T')" "$*" >> "$LOG"; }
notify(){ command -v osascript >/dev/null && osascript -e "display notification \"$1\" with title \"JIVO skills publish\"" 2>/dev/null; }

[ -d .git ] || exit 0
git rev-parse --abbrev-ref HEAD 2>/dev/null | grep -qx main || { log "not on main — skip"; exit 0; }
[ -f .git/index.lock ] && { log "index.lock present — skip"; exit 0; }

changed="$(git status --porcelain --untracked-files=all -- "${SCOPE[@]}" 2>/dev/null | grep -vE '(__pycache__|\.pyc$|/\._)' )"
git fetch -q origin main >>"$LOG" 2>&1
pending="$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)"
# Nothing new on disk and nothing waiting to go out: the common case, silent.
[ -z "$changed" ] && [ "${pending:-0}" = "0" ] && exit 0
ident=(); [ -z "$(git config user.email)" ] && ident=(-c user.name="Damanpreet Singh" -c user.email="daman@alise.in")

if [ -n "$changed" ]; then

# ── secret scan over what would go out ───────────────────────────────────────
files="$(printf '%s\n' "$changed" | awk '{print $NF}')"
hits=""
while IFS= read -r f; do
  [ -f "$f" ] || continue
  case "$f" in *.env|*/.env|*.pem|*.key|*credentials*) hits+="$f (filename)"$'\n'; continue;; esac
  h="$(grep -nEi -e '-----BEGIN [A-Z ]*PRIVATE KEY' \
       -e '(password|passwd|secret|api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret)[[:space:]]*[:=][[:space:]]*["'"'"']?[A-Za-z0-9@#\$%^&*()_+/=.,-]{6,}' \
       -e 'SAPB1_PASSWORD[[:space:]]*=[[:space:]]*[^[:space:]<$]' \
       -e 'Bearer [A-Za-z0-9._-]{20,}' \
       -e 'sk-[A-Za-z0-9]{20,}' "$f" 2>/dev/null | grep -viE '<[a-z_ -]+>|\$\{?[A-Z_]+|your[_ -]?password|password (is|differs|for|wrong)|example|placeholder|xxxx|…|'"'"'\.\.\.'"'"'' | head -3)"
  [ -n "$h" ] && hits+="$f:"$'\n'"$h"$'\n'
done <<< "$files"

if [ -n "$hits" ]; then
  printf '%s\n' "$hits" > "$FLAG"
  log "BLOCKED — possible credential in skills, not pushed:"; printf '%s\n' "$hits" >> "$LOG"
  notify "Blocked: a skill file looks like it holds a credential. See harness/.skills-publish-blocked"
  exit 1
fi
rm -f "$FLAG"

# ── commit exactly the scope ─────────────────────────────────────────────────
names="$(printf '%s\n' "$files" | sed -nE 's#^\.claude/skills/([^/]+)/.*#\1#p; s#^harness/desks\.json$#desks#p' | sort -u | tr '\n' ' ')"
git add -A -- "${SCOPE[@]}" 2>>"$LOG" || { log "git add failed"; exit 1; }
if ! git diff --cached --quiet; then
  git "${ident[@]}" commit -q -m "skills: auto-publish ${names}" -- "${SCOPE[@]}" >>"$LOG" 2>&1 || { log "commit failed"; git reset -q -- "${SCOPE[@]}"; exit 1; }
fi
fi  # changed

# ── push whatever is ahead of origin (this run's commit, or one that failed to push earlier)
[ "$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)" = "0" ] && exit 0
sha="$(git rev-parse --short HEAD)"
names="${names:-$(git log --format=%s origin/main..HEAD | sed 's/^skills: auto-publish //' | tr '\n' ' ')}"

push(){ git push -q origin main >>"$LOG" 2>&1; }
if ! push; then
  # main moved (operators auto-push corrections all day) — replay on top, keep going.
  if git "${ident[@]}" pull -q --rebase --autostash origin main >>"$LOG" 2>&1 && push; then :; else
    log "push failed for $sha — commit kept locally, will retry next run"
    git rebase --abort >/dev/null 2>&1
    notify "Skills commit $sha could not be pushed — will retry"
    exit 1
  fi
fi
log "published $(git rev-parse --short HEAD): ${names}"
notify "Published to every box: ${names}"
exit 0
