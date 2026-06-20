#!/bin/bash
BACKUP_DIR=~/projects/domains-tracker/backups
DB=~/projects/domains-tracker/backend/data/tracker.db
mkdir -p "$BACKUP_DIR"

# Ротация: максимум 5 файлов
for i in 4 3 2 1; do
  if [ -f "$BACKUP_DIR/tracker_$i.db" ]; then
    mv "$BACKUP_DIR/tracker_$i.db" "$BACKUP_DIR/tracker_$((i+1)).db"
  fi
done

cp "$DB" "$BACKUP_DIR/tracker_1.db"
echo "Backup done: tracker_1.db ($(date '+%Y-%m-%d %H:%M:%S'))"
