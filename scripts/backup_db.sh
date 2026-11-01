#!/bin/bash
# RNF-10: copia de seguridad de la base de datos PostgreSQL y de los archivos subidos (media/).
# Uso:  ./scripts/backup_db.sh            (guarda en ./backups)
# Programarla cada noche a las 2:00 con cron:
#   0 2 * * * cd /ruta/a/Academi && ./scripts/backup_db.sh >> backups/backup.log 2>&1
set -euo pipefail
umask 077
cd "$(dirname "$0")/.."

# Lee DB_NAME, DB_USER, DB_PASSWORD, DB_HOST y DB_PORT del archivo .env
set -a; source .env; set +a

STAMP=$(date +%Y%m%d_%H%M%S)
DEST=backups
KEEP_DAYS=${KEEP_DAYS:-14}
mkdir -p "$DEST"
chmod 700 "$DEST"
TMP_DUMP=$(mktemp "$DEST/.db_$STAMP.XXXXXX")
trap 'rm -f "$TMP_DUMP"' EXIT

echo "[$(date)] Respaldando base de datos $DB_NAME ..."
PGPASSWORD="$DB_PASSWORD" pg_dump -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "$DB_USER" \
  --format=custom --file="$TMP_DUMP" "$DB_NAME"
pg_restore --list "$TMP_DUMP" > /dev/null
mv "$TMP_DUMP" "$DEST/db_$STAMP.dump"

if [ -d media ]; then
  echo "[$(date)] Respaldando archivos subidos (media/) ..."
  TMP_MEDIA=$(mktemp "$DEST/.media_$STAMP.XXXXXX")
  trap 'rm -f "$TMP_DUMP" "$TMP_MEDIA"' EXIT
  tar -czf "$TMP_MEDIA" media
  tar -tzf "$TMP_MEDIA" > /dev/null
  mv "$TMP_MEDIA" "$DEST/media_$STAMP.tar.gz"
fi

# Elimina copias más viejas que KEEP_DAYS días
find "$DEST" -type f \( -name 'db_*.dump' -o -name 'media_*.tar.gz' \) -mtime +"$KEEP_DAYS" -delete
echo "[$(date)] Listo: $DEST/db_$STAMP.dump"
