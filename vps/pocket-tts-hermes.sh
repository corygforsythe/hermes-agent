#!/usr/bin/env bash
# Kyutai Pocket TTS wrapper for Hermes command-type TTS providers.
#   usage: pocket-tts-hermes.sh <input_text_file> <output_audio_file> [voice]
# Reads UTF-8 text from the input file, synthesizes with pocket-tts (CPU),
# then transcodes to whatever container the output extension names.
set -euo pipefail

IN="$1"
OUT="$2"
VOICE="${3:-alba}"
[ -n "$VOICE" ] || VOICE="alba"

BIN="${POCKET_TTS_BIN:-/opt/pocket-tts/bin/pocket-tts}"

TEXT="$(cat "$IN")"
if [ -z "${TEXT// }" ]; then
  echo "pocket-tts-hermes: empty input text" >&2
  exit 1
fi

TMPWAV="$(mktemp --suffix=.wav)"
trap 'rm -f "$TMPWAV"' EXIT

# Threads: the model only benefits from ~2 cores.
OMP_NUM_THREADS=2 "$BIN" generate \
  --quiet \
  --text "$TEXT" \
  --voice "$VOICE" \
  --output-path "$TMPWAV" >&2

EXT="${OUT##*.}"
case "$EXT" in
  wav)
    mv "$TMPWAV" "$OUT"
    ;;
  m4a|aac)
    ffmpeg -y -loglevel error -i "$TMPWAV" -c:a aac -b:a 64k "$OUT"
    ;;
  opus|ogg)
    ffmpeg -y -loglevel error -i "$TMPWAV" -c:a libopus -b:a 32k "$OUT"
    ;;
  *)
    ffmpeg -y -loglevel error -i "$TMPWAV" -b:a 64k "$OUT"
    ;;
esac

[ -s "$OUT" ] || { echo "pocket-tts-hermes: no audio produced" >&2; exit 1; }
