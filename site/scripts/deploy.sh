#!/usr/bin/env bash
#
# Despliegue canónico del sitio (blueskytravelmx.com + yoga-verde).
#
# Esta es la ÚNICA ruta de despliegue soportada. No uses rsync ni scp -r.
# El tarball se valida en un staging dentro de /docker y se publica moviendo
# el release completo al mismo volumen. Este reemplazo elimina del release
# cualquier archivo que no esté en el tarball, incluido el `site/` huérfano
# histórico. Nunca guardes secretos, volúmenes ni archivos operativos dentro de
# REMOTE_DIR: el script aborta si detecta esos patrones antes del intercambio.
# El release anterior queda disponible hasta que pasan build, arranque, checks
# en vivo y la verificación del manifest de build.
#
# Uso:
#   ./scripts/deploy.sh            # build local + despliegue
#   ./scripts/deploy.sh --no-check # omite npm run check (más rápido)
#
set -euo pipefail

VPS_HOST="${VPS_HOST:-vps-n8n}"
VPS_PORT="${VPS_PORT:-2222}"
REMOTE_DIR="${REMOTE_DIR:-/docker/blueskytravel-site}"

SITE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)-$$"
TARBALL="/tmp/site-${STAMP}.tar.gz"
REMOTE_TAR="/tmp/site-${STAMP}.tar.gz"
REMOTE_PARENT="$(dirname "$REMOTE_DIR")"
REMOTE_NAME="$(basename "$REMOTE_DIR")"
REMOTE_STAGE="${REMOTE_PARENT}/.${REMOTE_NAME}.stage-${STAMP}"
REMOTE_OLD="${REMOTE_PARENT}/.${REMOTE_NAME}.old-${STAMP}"
REMOTE_FAILED="${REMOTE_PARENT}/.${REMOTE_NAME}.failed-${STAMP}"

MANIFEST_FILE="$SITE_DIR/public/yoga-verde/deploy-manifest.json"
SOURCE_REVISION=""
DEPLOY_ID=""
MANIFEST_CREATED=0
REMOTE_TRANSFER_STARTED=0
REMOTE_PHASE="none" # none | swapping | swapped | running | done | rolledback
ROLLBACK_RUNNING=0

say() { printf '\n\033[1m▸ %s\033[0m\n' "$1"; }
ssh_do() { ssh -p "$VPS_PORT" -o ConnectTimeout=15 "$VPS_HOST" "$@"; }

cleanup_remote_artifacts() {
  if [[ "$REMOTE_TRANSFER_STARTED" == 1 ]]; then
    ssh_do "sudo rm -rf '$REMOTE_STAGE' '$REMOTE_TAR'" || true
  fi
}

# Rollback by movement. The failed release is moved aside before the previous
# release is restored; it is never deleted before that restore succeeds.
# A failed build leaves the old container running, so it only restores the
# directory. If up -d may have started the new container, it rebuilds the old
# release before bringing it back.
rollback_remote() {
  if [[ "$ROLLBACK_RUNNING" == 1 ]]; then
    return 0
  fi
  ROLLBACK_RUNNING=1

  local rebuild_old=0
  if [[ "$REMOTE_PHASE" == "running" ]]; then
    rebuild_old=1
  fi

  if ! ssh_do "set -euo pipefail
    if sudo test -e '$REMOTE_DIR'; then
      sudo rm -rf '$REMOTE_FAILED'
      sudo mv '$REMOTE_DIR' '$REMOTE_FAILED'
    fi

    if sudo test -d '$REMOTE_OLD'; then
      if ! sudo mv '$REMOTE_OLD' '$REMOTE_DIR'; then
        if sudo test -e '$REMOTE_FAILED'; then
          sudo mv '$REMOTE_FAILED' '$REMOTE_DIR' || true
        fi
        exit 1
      fi
      sudo chown -R deploy:deploy '$REMOTE_DIR/scripts' '$REMOTE_DIR/src' '$REMOTE_DIR/public' '$REMOTE_DIR/deploy'
      if [[ $rebuild_old == 1 ]]; then
        sudo docker compose -f '$REMOTE_DIR/docker-compose.yml' build --no-cache
        sudo docker compose -f '$REMOTE_DIR/docker-compose.yml' up -d
      fi
      sudo rm -rf '$REMOTE_FAILED'
    elif sudo test -e '$REMOTE_FAILED'; then
      sudo mv '$REMOTE_FAILED' '$REMOTE_DIR'
    fi

    sudo rm -rf '$REMOTE_STAGE' '$REMOTE_TAR'"; then
    echo "ADVERTENCIA: el rollback remoto no terminó; conservar los releases para recuperación manual." >&2
    return 1
  fi

  REMOTE_PHASE="rolledback"
  ROLLBACK_RUNNING=0
}

on_exit() {
  local status=$?
  trap - EXIT INT TERM

  case "$REMOTE_PHASE" in
    swapping|swapped|running)
      rollback_remote || true
      ;;
    none|rolledback)
      cleanup_remote_artifacts
      ;;
    done)
      # La limpieza remota ya se intentó después de validar el sitio. No abras
      # otra conexión desde EXIT: el VPS limita conexiones SSH consecutivas.
      ;;
  esac

  if [[ "$MANIFEST_CREATED" == 1 ]]; then
    rm -f "$MANIFEST_FILE"
  fi
  rm -f "$TARBALL"
  exit "$status"
}

trap on_exit EXIT INT TERM

cd "$SITE_DIR"

# ---------------------------------------------------------------------------
# 0. Manifest efímero. Se sirve con el build y permite verificar exactamente
#    qué ejecución llegó a producción, sin depender de markup incidental.
# ---------------------------------------------------------------------------
SOURCE_REVISION="$(git rev-parse --short=12 HEAD 2>/dev/null || printf 'working-tree')"
DEPLOY_ID="${SOURCE_REVISION}-${STAMP}"
if [[ -e "$MANIFEST_FILE" ]]; then
  echo "ABORTADO: ya existe $MANIFEST_FILE; no se sobrescribe un archivo ajeno." >&2
  exit 1
fi
printf '{"build_id":"%s","source_revision":"%s"}\n' "$DEPLOY_ID" "$SOURCE_REVISION" > "$MANIFEST_FILE"
MANIFEST_CREATED=1

# ---------------------------------------------------------------------------
# 1. Calidad. Nunca se despliega algo que no compila.
# ---------------------------------------------------------------------------
if [[ "${1:-}" != "--no-check" ]]; then
  say "npm run check"
  npm run check
fi
say "npm run build"
npm run build

# ---------------------------------------------------------------------------
# 2. Empaquetado. Se excluye todo lo que no debe salir del equipo: build local,
#    dependencias, git y cualquier credencial.
# ---------------------------------------------------------------------------
say "Empaquetando $SITE_DIR"
COPYFILE_DISABLE=1 tar --exclude='node_modules' \
    --exclude='.git' \
    --exclude='.astro' \
    --exclude='dist' \
    --exclude='.env' \
    --exclude='.env.*' \
    --exclude='*.pem' \
    --exclude='*.key' \
    --exclude='*credentials*' \
    --exclude='*service-account*' \
    --exclude='*token*' \
    --exclude='public/yoga-verde/assets/real-labels-pdf' \
    --exclude='public/yoga-verde/assets/brand/*.pdf' \
    -czf "$TARBALL" .

# Red de seguridad: si algo sensible se coló, se aborta antes de transferir.
if tar -tzf "$TARBALL" | grep -qiE '(^|/)(\.env($|\.)|.*\.(pem|key)$|.*credentials.*|.*service-account.*|.*token.*)'; then
  echo "ABORTADO: el tarball contiene archivos sensibles." >&2
  tar -tzf "$TARBALL" | grep -iE '(^|/)(\.env($|\.)|.*\.(pem|key)$|.*credentials.*|.*service-account.*|.*token.*)' >&2
  exit 1
fi
echo "  $(du -h "$TARBALL" | cut -f1)  $(tar -tzf "$TARBALL" | wc -l | tr -d ' ') entradas"

# ---------------------------------------------------------------------------
# 3. Transferencia del tarball por un stream SSH, verificada con SHA-256.
# ---------------------------------------------------------------------------
say "Transfiriendo"
REMOTE_TRANSFER_STARTED=1
LOCAL_SUM="$(shasum -a 256 "$TARBALL" | awk '{print $1}')"
REMOTE_SUM="$(ssh_do "set -euo pipefail
  rm -f '$REMOTE_TAR'
  umask 077
  dd of='$REMOTE_TAR' bs=1M status=none
  sha256sum '$REMOTE_TAR' | awk '{print \$1}'" < "$TARBALL")"
if [[ "$LOCAL_SUM" != "$REMOTE_SUM" ]]; then
  echo "ABORTADO: SHA-256 distinto (local=$LOCAL_SUM remoto=$REMOTE_SUM)" >&2
  exit 1
fi
echo "  SHA-256 OK ($LOCAL_SUM)"

# ---------------------------------------------------------------------------
# 4. Extraer a staging, validar el paquete y proteger el root activo, antes de
#    tocar producción. Todo ocurre en una sola sesión SSH para respetar el
#    rate-limit del puerto 2222.
# ---------------------------------------------------------------------------
say "Verificando el paquete en el servidor"
if ! ssh_do "set -euo pipefail
    sudo rm -rf '$REMOTE_STAGE'
    sudo mkdir -p '$REMOTE_STAGE'
    sudo tar -xzf '$REMOTE_TAR' -C '$REMOTE_STAGE'
    for f in scripts/run-astro.mjs package.json Dockerfile docker-compose.yml src/pages/yoga-verde/index.astro src/data/yoga-verde-store.js src/assets/fonts/yoga-verde-real/Gelasio/static/Gelasio-Regular.ttf public/yoga-verde/deploy-manifest.json; do
      sudo test -f \"$REMOTE_STAGE/\$f\" || { echo \"ABORTADO: falta \$f en el paquete\"; exit 1; }
    done
    sudo test -d '$REMOTE_STAGE/public/yoga-verde/assets/products'
    sudo test -d '$REMOTE_STAGE/public/yoga-verde/fonts'
    if sudo test -d '$REMOTE_DIR'; then
      protected=\$(sudo find '$REMOTE_DIR' -type f \( -name '.env' -o -name '.env.*' -o -name '*.pem' -o -name '*.key' -o -iname '*credentials*' -o -iname '*service-account*' -o -iname '*token*' -o -name 'docker-compose.override.yml' -o -name '*.sqlite' -o -name '*.db' \) -print -quit)
      if [ -n \"\$protected\" ]; then
        echo \"ABORTADO: archivo protegido dentro de REMOTE_DIR: \$protected\" >&2
        exit 1
      fi
    fi
    echo '  paquete completo y root protegido'"; then
  exit 1
fi

# No se permite destruir secretos ni estado operativo que alguien haya dejado
# dentro del root activo. El site/ histórico sí es deliberadamente huérfano y
# será eliminado al publicar el release completo.

# ---------------------------------------------------------------------------
# 5. Publicar y reconstruir. El contexto de build es la RAÍZ del repo remoto.
#    El viejo release se mueve, no se borra, hasta que el nuevo está verificado.
# ---------------------------------------------------------------------------
say "Publicando en $REMOTE_DIR"
REMOTE_PHASE="swapping"
if ! ssh_do "set -euo pipefail
    sudo rm -rf '$REMOTE_OLD'
    sudo test -d '$REMOTE_DIR' && sudo mv '$REMOTE_DIR' '$REMOTE_OLD'
    sudo mv '$REMOTE_STAGE' '$REMOTE_DIR'
    sudo chown -R deploy:deploy '$REMOTE_DIR/scripts' '$REMOTE_DIR/src' '$REMOTE_DIR/public' '$REMOTE_DIR/deploy'"; then
  exit 1
fi
REMOTE_PHASE="swapped"

say "docker compose build --no-cache"
if ! ssh_do "cd '$REMOTE_DIR' && sudo docker compose build --no-cache &&
    sudo docker run --rm blueskytravel-site-bluesky-site:latest sh -c 'set -eu; test -f /usr/share/nginx/html/yoga-verde/deploy-manifest.json; test -f /usr/share/nginx/html/yoga-verde/assets/products/display/contorno-de-ojos-lavanda.webp; test -f /usr/share/nginx/html/yoga-verde/assets/products/display/crema-corporal-leche-de-coco.webp' &&
    command -v trivy >/dev/null 2>&1 &&
    sudo trivy image --quiet --scanners vuln --ignore-unfixed --severity HIGH,CRITICAL --exit-code 1 blueskytravel-site-bluesky-site:latest"; then
  echo "ABORTADO: el build, los assets o la compuerta Trivy fallaron." >&2
  exit 1
fi

say "docker compose up -d"
REMOTE_PHASE="running"
if ! ssh_do "cd '$REMOTE_DIR' && sudo docker compose up -d"; then
  exit 1
fi

# ---------------------------------------------------------------------------
# 6. Verificar contra el sitio en vivo, no contra el log del build.
# ---------------------------------------------------------------------------
say "Verificando en vivo"
for url in "https://yoga-verde.srv1175749.hstgr.cloud/" "https://blueskytravelmx.com/"; do
  code=""
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    code="$(curl -s -o /dev/null -w '%{http_code}' "$url" || true)"
    [[ "$code" == "200" ]] && break
    sleep 3
  done
  printf '  %-48s %s\n' "$url" "$code"
  [[ "$code" == "200" ]] || { echo "ABORTADO: $url respondió $code" >&2; exit 1; }
done

say "Confirmando manifest de build"
MANIFEST_URL="https://yoga-verde.srv1175749.hstgr.cloud/yoga-verde/deploy-manifest.json"
LIVE_MANIFEST="$(curl -fsS --compressed "$MANIFEST_URL" || true)"
if [[ "$LIVE_MANIFEST" == *"\"build_id\":\"$DEPLOY_ID\""* ]]; then
  echo "  build $DEPLOY_ID confirmado ✓"
else
  echo "ABORTADO: el manifest servido no corresponde a este build ($DEPLOY_ID)." >&2
  exit 1
fi

# Desde aquí el nuevo release está sano. No debe ejecutarse rollback por un
# fallo de limpieza: conservar un respaldo es seguro; servir el build sano es
# más importante. El recolector solo toca directorios temporales con el prefijo
# exacto y de más de dos horas, nunca archivos del release activo.
REMOTE_PHASE="done"
say "Limpiando releases temporales"
if ! ssh_do "set -euo pipefail
    sudo rm -rf '$REMOTE_OLD' '$REMOTE_STAGE' '$REMOTE_TAR'
    sudo find '$REMOTE_PARENT' -mindepth 1 -maxdepth 1 -type d \\
      \( -name '.${REMOTE_NAME}.stage-*' -o -name '.${REMOTE_NAME}.old-*' -o -name '.${REMOTE_NAME}.failed-*' \) \\
      -mmin +120 -exec rm -rf {} +"; then
  echo "ADVERTENCIA: el sitio está verificado, pero quedó basura temporal para limpieza posterior." >&2
fi

say "Despliegue completo"
