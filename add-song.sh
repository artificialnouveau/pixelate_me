#!/bin/bash
# add-song.sh <youtube-url>
# Downloads a YouTube video AND its English subtitles (.srt) into the karaoke
# library next to run.html, and updates karaoke-videos.json. The subtitles are
# used directly as the karaoke lyrics (no lrclib fetch). Re-run per song.
set -e
URL="$1"
if [ -z "$URL" ]; then echo "usage: ./add-song.sh <youtube-url>"; exit 1; fi
DIR="$(cd "$(dirname "$0")" && pwd)"
ID="$(yt-dlp --no-warnings --get-id --no-playlist "$URL")"
TITLE="$(yt-dlp --no-warnings --get-title --skip-download --no-playlist "$URL")"
FILE="karaoke-$ID.mp4"
SRT="karaoke-$ID.srt"

if [ -f "$DIR/$FILE" ]; then
  echo "Already downloaded: $FILE"
else
  yt-dlp -f "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best" \
    --merge-output-format mp4 --no-playlist -o "$DIR/$FILE" "$URL"
fi

# subtitles -> karaoke-<id>.srt (prefer manual en, fall back to auto captions)
rm -f "$DIR/karaoke-$ID".*.srt
yt-dlp --no-warnings --skip-download --write-subs --write-auto-subs \
  --sub-langs "en.*,en" --sub-format srt --convert-subs srt \
  -o "$DIR/karaoke-$ID.%(ext)s" "$URL" >/dev/null 2>&1 || true
# yt-dlp names it karaoke-<id>.en.srt etc; normalise to karaoke-<id>.srt
CAND="$(ls "$DIR/karaoke-$ID".*.srt 2>/dev/null | head -1)"
if [ -n "$CAND" ]; then mv -f "$CAND" "$DIR/$SRT"; rm -f "$DIR/karaoke-$ID".*.srt; HAVE_SRT=1; else HAVE_SRT=0; fi

python3 - "$DIR" "$ID" "$TITLE" "$FILE" "$URL" "$SRT" "$HAVE_SRT" <<'PY'
import json, sys, os
d, idv, title, file, url, srt, have = sys.argv[1:8]
p = os.path.join(d, 'karaoke-videos.json')
lib = json.load(open(p)) if os.path.exists(p) else []
lib = [e for e in lib if e.get('id') != idv]
entry = {'id': idv, 'title': title, 'file': file, 'url': url}
if have == '1': entry['srt'] = srt
lib.append(entry)
json.dump(lib, open(p, 'w'), indent=2)
print(f'Added "{title}" -> {file}' + (f' + {srt}' if have == '1' else ' (no subtitles found)') + f'  ({len(lib)} songs)')
PY
echo "Reload run.html and pick it from the Library dropdown (Karaoke modes)."
