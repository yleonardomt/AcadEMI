#!/bin/bash
# RNF-11: recuperación ante fallos. Restaura la base de datos (y opcionalmente media/) desde una copia.
# Uso:  ./scripts/restore_db.sh backups/db_AAAAMMDD_HHMMSS.dump [backups/media_AAAAMMDD_HHMMSS.tar.gz]
# ATENCIÓN: reemplaza los datos actuales de la base de datos.
set -euo pipefail
cd "$(dirname "$0")/.."
[ $# -ge 1 ] || { echo "Uso: $0 <archivo.dump> [media.tar.gz]"; exit 1; }
set -a; source .env; set +a

read -r -p "Esto reemplazará la base de datos '$DB_NAME'. ¿Continuar? (escribe SI): " ok
[ "$ok" = "SI" ] || { echo "Cancelado."; exit 1; }

PGPASSWORD="$DB_PASSWORD" pg_restore -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "$DB_USER" \
  --clean --if-exists --no-owner -d "$DB_NAME" "$1"
echo "Base de datos restaurada."

if [ $# -ge 2 ]; then
  tar -xzf "$2"
  echo "Archivos de media/ restaurados."
fi
