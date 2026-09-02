#!/usr/bin/env bash
# Build and install jwa on the JIVO VPS. Run it ON the VPS, as the user that
# will own the session — not as root, because ~/.jwa holds the linked-device
# keys and they should belong to a person, not to root.
#
#   scp -r whatsapp-cli vps:~/           # from the Mac
#   ssh vps 'bash ~/whatsapp-cli/deploy/install-vps.sh'
#
# Then link the number ONCE, interactively, because a QR needs a human:
#   ssh -t vps '~/go/bin/jwa login'
#   systemctl --user start jwa && systemctl --user status jwa
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$here"

if ! command -v go >/dev/null 2>&1; then
    echo "Go is not installed on this box."
    echo "  Debian/Ubuntu:  sudo apt-get install -y golang-go   (needs 1.24+)"
    echo "  or from source: https://go.dev/dl/"
    exit 1
fi
echo "==> $(go version)"

echo "==> resolving dependencies (this pins whatsmeow to today's release)"
go mod tidy

echo "==> running the guard test — jwa must not contain a single send verb"
go test ./internal/wa/ -run TestNothingSends -v

echo "==> building"
mkdir -p "$HOME/go/bin"
# -buildvcs=false: this tree is normally an rsync'd copy sitting outside any
# checkout. If a stray .git exists anywhere above it (there is one in /root on
# the JIVO VPS) Go tries to stamp the binary from it and the build dies with
# "error obtaining VCS status: exit status 128". The stamp buys us nothing here.
go build -trimpath -buildvcs=false -o "$HOME/go/bin/jwa" ./cmd/jwa
echo "    installed: $HOME/go/bin/jwa"

echo "==> installing the health watch (cron, every 10 min, alerts Telegram on a change)"
mkdir -p "$HOME/bin" "$HOME/.jwa"
install -m 0755 deploy/jwa-health.sh "$HOME/bin/jwa-health.sh"
line="*/10 * * * * $HOME/bin/jwa-health.sh >> $HOME/.jwa/health.log 2>&1   # jwa: WhatsApp link/connect watch -> Telegram"
( crontab -l 2>/dev/null | grep -v 'jwa-health.sh'; echo "$line" ) | crontab -

echo "==> installing the live loop (jolly-wa: WhatsApp → Jolly agent → reply)"
install -m 0755 agent/jolly_wa.py "$HOME/bin/jolly_wa.py"
sed "s|__HOME__|$HOME|g" deploy/jolly-wa.service > "$HOME/.config/systemd/user/jolly-wa.service" 2>/dev/null || {
    mkdir -p "$HOME/.config/systemd/user"
    sed "s|__HOME__|$HOME|g" deploy/jolly-wa.service > "$HOME/.config/systemd/user/jolly-wa.service"
}

echo "==> installing the user service"
mkdir -p "$HOME/.config/systemd/user"
sed "s|__HOME__|$HOME|g" deploy/jwa.service > "$HOME/.config/systemd/user/jwa.service"
systemctl --user daemon-reload
systemctl --user enable jwa.service

# Without lingering, a user service dies when the SSH session ends — which is
# exactly the failure that looks like "WhatsApp keeps unlinking itself".
if ! loginctl show-user "$USER" 2>/dev/null | grep -q 'Linger=yes'; then
    echo
    echo "!! One thing needs root, once:"
    echo "   sudo loginctl enable-linger $USER"
    echo "   Without it the service stops the moment you log out."
fi

echo
echo "Built, not yet linked. Next, with a phone in hand:"
echo "   ssh -t <this-box> '~/go/bin/jwa login'      # scan the QR"
echo "   systemctl --user start jwa"
echo "   ~/go/bin/jwa doctor"
