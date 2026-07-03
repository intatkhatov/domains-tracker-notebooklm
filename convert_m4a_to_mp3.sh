#!/bin/bash

INPUT_DIR="$HOME/projects/domains-tracker/audio/m4a"
OUTPUT_DIR="$HOME/projects/domains-tracker/audio/mp3"

mkdir -p "$INPUT_DIR"
mkdir -p "$OUTPUT_DIR"

files=("$INPUT_DIR"/*.m4a)
if [ ! -f "${files[0]}" ]; then
  echo "Нет m4a-файлов в $INPUT_DIR"
  exit 0
fi

count=0
for f in "$INPUT_DIR"/*.m4a; do
  filename=$(basename "$f" .m4a)
  out="$OUTPUT_DIR/${filename}.mp3"

  echo "Конвертирую: $filename.m4a → $filename.mp3"

  ffmpeg -i "$f" \
    -codec:a libmp3lame \
    -qscale:a 0 \
    -id3v2_version 3 \
    -write_id3v1 1 \
    -y "$out" \
    -hide_banner -loglevel error

  if [ $? -eq 0 ]; then
    echo "  ✓ Готово: $filename.mp3"
    ((count++))
  else
    echo "  ✗ Ошибка: $filename.m4a"
  fi
done

echo ""
echo "Конвертировано файлов: $count"
echo "MP3-файлы в: $OUTPUT_DIR"
