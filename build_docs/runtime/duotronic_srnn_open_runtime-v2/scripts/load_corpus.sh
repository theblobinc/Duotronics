#!/usr/bin/env sh
set -eu
SRC=${1:-}
DST=${2:-./corpus}
if [ -z "$SRC" ]; then
  echo "usage: $0 path/to/corpus.zip-or-directory [./corpus]" >&2
  exit 2
fi
mkdir -p "$DST"
if [ -d "$SRC" ]; then
  rsync -a --delete "$SRC"/ "$DST"/
elif [ -f "$SRC" ]; then
  rm -rf "$DST"/*
  unzip -q "$SRC" -d "$DST"
else
  echo "source not found: $SRC" >&2
  exit 1
fi
echo "corpus staged at $DST"
