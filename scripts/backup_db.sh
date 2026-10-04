#!/bin/bash
# RNF-10: copia de seguridad de la base de datos PostgreSQL y de los archivos subidos (media/).
# Uso:  ./scripts/backup_db.sh            (guarda en ./backups)
# Programarla cada noche a las 2:00 con cron:
#   0 2 * * * cd /ruta/a/Academi && ./scripts/backup_db.sh >> backups/backup.log 2>&1
set -euo pipefail
cd "$(dirname "$0")/.."

# Lee DB_NAME, DB_USER, DB_PASSWORD, DB_HOST y DB_PORT del archivo .env
set -a; source .env; set +a

STAMP=$(date +%Y%m%d_%H%M%S)
DEST=backups
KEEP_DAYS=${KEEP_DAYS:-14}
mkdir -p "$DEST"

echo "[$(date)] Respaldando base de datos $DB_NAME ..."
PGPASSWORD="$DB_PASSWORD" pg_dump -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "$DB_USER" \
  --format=custom --file="$DEST/db_$STAMP.dump" "$DB_NAME"

if [ -d media ]; then
  echo "[$(date)] Respaldando archivos subidos (media/) ..."
  tar -czf "$DEST/media_$STAMP.tar.gz" media
fi

# Elimina copias más viejas que KEEP_DAYS días
find "$DEST" -type f \( -name 'db_*.dump' -o -name 'media_*.tar.gz' \) -mtime +"$KEEP_DAYS" -delete
echo "[$(date)] Listo: $DEST/db_$STAMP.dump"
