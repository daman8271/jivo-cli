#!/usr/bin/env bash
# Which desktop backends exist on THIS machine? Run before designing a harness —
# the backend you can actually invoke decides the design, not the one the docs
# describe. Prints one line per candidate; absent is normal, not a failure.
printf '%-14s %-8s %s\n' BACKEND STATE HOW
# macOS keeps app binaries inside bundles, off PATH. A backend that is "absent"
# on PATH but present in /Applications is present — that distinction is the whole
# reason a GUI app looks unreachable when it is not.
BUNDLES="/Applications/LibreOffice.app/Contents/MacOS/soffice
/Applications/Google Chrome.app/Contents/MacOS/Google Chrome
/Applications/draw.io.app/Contents/MacOS/draw.io"

bundle_for() {
  while IFS= read -r b; do
    case "$b" in *"$1"*) [ -x "$b" ] && { printf '%s' "$b"; return 0; };; esac
  done <<EOF
$BUNDLES
EOF
  return 1
}

probe() { # name, command to test, how-to-drive-it
  if command -v "$2" >/dev/null 2>&1; then
    printf '%-14s %-8s %s\n' "$1" present "$3"
  elif b=$(bundle_for "$2"); then
    printf '%-14s %-8s %s\n' "$1" bundle "$b"
  else
    printf '%-14s %-8s %s\n' "$1" absent  "$3"
  fi
}
probe libreoffice soffice      'soffice --headless --convert-to csv:"Text - txt - csv (StarCalc)" f.xlsx'
probe libreoffice libreoffice  'same as soffice; on macOS it is /Applications/LibreOffice.app/Contents/MacOS/soffice'
probe chrome       google-chrome '--headless --print-to-pdf / --dump-dom'
probe chrome-mac   'Google Chrome' '--headless=new --print-to-pdf=out.pdf file.html'
probe soffice-mac  soffice '--headless --convert-to csv'
probe python-xlsx  python3      'python3 -c "import openpyxl" — reads .xlsx with no app at all'
probe pdftotext    pdftotext    'pdftotext -layout bill.pdf -   (poppler)'
probe pdftoppm     pdftoppm     'pdftoppm -r 200 -png bill.pdf page  — for reading a scan in tiles'
probe imagemagick  magick       'magick in.png -crop ... out.png'
probe ffmpeg       ffmpeg       'ffmpeg -i in.mp4 ...'
probe qpdf         qpdf         'qpdf --pages ... — split/merge without re-rendering'
probe drawio       drawio       'drawio -x -f png -o out.png in.drawio'
echo
echo 'macOS note: an app in /Applications is not on PATH. Check the real binary, e.g.'
echo '  /Applications/LibreOffice.app/Contents/MacOS/soffice --version'
