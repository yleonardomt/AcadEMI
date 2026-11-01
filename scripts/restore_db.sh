#!/bin/bash
# RNF-11: recuperación ante fallos. Restaura la base de datos (y opcionalmente media/) desde una copia.
# Uso:  ./scripts/restore_db.sh backups/db_AAAAMMDD_HHMMSS.dump [backups/media_AAAAMMDD_HHMMSS.tar.gz]
# ATENCIÓN: reemplaza los datos actuales de la base de datos.
set -euo pipefail
umask 077
cd "$(dirname "$0")/.."
[ $# -ge 1 ] || { echo "Uso: $0 <archivo.dump> [media.tar.gz]"; exit 1; }
set -a; source .env; set +a

[ -r "$1" ] || { echo "No se puede leer el respaldo: $1" >&2; exit 1; }
pg_restore --list "$1" > /dev/null
if [ $# -ge 2 ]; then
  [ -r "$2" ] || { echo "No se puede leer el archivo media: $2" >&2; exit 1; }
  python3 - "$2" <<'PY' || { echo "Archivo media con rutas inseguras" >&2; exit 1; }
import sys
import tarfile
from pathlib import PurePosixPath

with tarfile.open(sys.argv[1], 'r:gz') as archive:
    for item in archive:
        path = PurePosixPath(item.name)
        if (path.is_absolute() or '..' in path.parts or
                not path.parts or path.parts[0] != 'media' or
                not (item.isfile() or item.isdir())):
            raise SystemExit(1)
PY
fi

read -r -p "Esto reemplazará la base de datos '$DB_NAME'. ¿Continuar? (escribe SI): " ok
[ "$ok" = "SI" ] || { echo "Cancelado."; exit 1; }

PGPASSWORD="$DB_PASSWORD" pg_restore -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "$DB_USER" \
  --clean --if-exists --no-owner --exit-on-error -d "$DB_NAME" "$1"
echo "Base de datos restaurada."

if [ $# -ge 2 ]; then
  tar -xzf "$2"
  echo "Archivos de media/ restaurados."
fi
