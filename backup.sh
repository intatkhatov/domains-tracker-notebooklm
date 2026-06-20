#!/bin/bash
BACKUP_DIR=~/projects/domains-tracker/backups
DB=~/projects/domains-tracker/backend/data/tracker.db
PROJECT_DIR=~/projects/domains-tracker
mkdir -p "$BACKUP_DIR"

# Локальная ротация: максимум 5 файлов
for i in 4 3 2 1; do
  if [ -f "$BACKUP_DIR/tracker_$i.db" ]; then
    mv "$BACKUP_DIR/tracker_$i.db" "$BACKUP_DIR/tracker_$((i+1)).db"
  fi
done

cp "$DB" "$BACKUP_DIR/tracker_1.db"
echo "Local backup done: tracker_1.db ($(date '+%Y-%m-%d %H:%M:%S'))"

# Git-бэкап в GitHub
cd "$PROJECT_DIR" || exit 1

if [ -d ".git" ]; then
  git add -A
  if ! git diff --cached --quiet; then
    git commit -m "Auto-backup: $(date '+%Y-%m-%d %H:%M:%S')" --quiet
    if git push origin main --quiet 2>/tmp/git_push_error.log; then
      echo "Git backup pushed to GitHub."
    else
      echo "WARNING: Git push failed. See /tmp/git_push_error.log for details."
    fi
  else
    echo "Git backup: no changes to commit."
  fi
else
  echo "Git backup skipped: not a git repository."
fi
