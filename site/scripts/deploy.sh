#!/usr/bin/env bash
#
# Despliegue canónico del sitio (blueskytravelmx.com + yoga-verde).
#
# Esta es la ÚNICA ruta de despliegue soportada. Un solo tarball con checksum
# verificado se extrae a staging y se publica con tar, de forma comprobable.
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
STAMP="$(date +%Y%m%d-%H%M%S)"
TARBALL="/tmp/site-${STAMP}.tar.gz"
REMOTE_TAR="/tmp/site-${STAMP}.tar.gz"
REMOTE_STAGE="/tmp/site-stage-${STAMP}"

say() { printf '\n\033[1m▸ %s\033[0m\n' "$1"; }
ssh_do() { ssh -p "$VPS_PORT" -o ConnectTimeout=15 "$VPS_HOST" "$@"; }

cd "$SITE_DIR"

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
tar --exclude='node_modules' \
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
    --exclude='src/assets/fonts' \
    -czf "$TARBALL" .

# Red de seguridad: si algo sensible se coló, se aborta antes de transferir.
if tar -tzf "$TARBALL" | grep -qiE '(^|/)(\.env|.*\.pem|.*\.key)$|credentials|service-account'; then
  echo "ABORTADO: el tarball contiene archivos sensibles." >&2
  tar -tzf "$TARBALL" | grep -iE '(^|/)(\.env|.*\.pem|.*\.key)$|credentials|service-account' >&2
  rm -f "$TARBALL"; exit 1
fi
echo "  $(du -h "$TARBALL" | cut -f1)  $(tar -tzf "$TARBALL" | wc -l | tr -d ' ') entradas"

# ---------------------------------------------------------------------------
# 3. Transferencia de UN archivo, verificada por checksum.
# ---------------------------------------------------------------------------
say "Transfiriendo"
scp -P "$VPS_PORT" "$TARBALL" "$VPS_HOST:$REMOTE_TAR"

LOCAL_SUM="$(md5 -q "$TARBALL" 2>/dev/null || md5sum "$TARBALL" | cut -d' ' -f1)"
REMOTE_SUM="$(ssh_do "md5sum $REMOTE_TAR | cut -d' ' -f1")"
if [[ "$LOCAL_SUM" != "$REMOTE_SUM" ]]; then
  echo "ABORTADO: checksum distinto (local=$LOCAL_SUM remoto=$REMOTE_SUM)" >&2
  exit 1
fi
echo "  checksum OK ($LOCAL_SUM)"

# ---------------------------------------------------------------------------
# 4. Extraer a staging y COMPROBAR que llegó completo, antes de tocar producción.
#    El paso que faltaba las veces que el despliegue quedó a medias.
# ---------------------------------------------------------------------------
say "Verificando el paquete en el servidor"
ssh_do "rm -rf $REMOTE_STAGE && mkdir -p $REMOTE_STAGE && tar -xzf $REMOTE_TAR -C $REMOTE_STAGE 2>/dev/null
  cd $REMOTE_STAGE
  for f in scripts/run-astro.mjs package.json Dockerfile docker-compose.yml src/pages/yoga-verde/index.astro src/data/yoga-verde-store.js; do
    [ -f \"\$f\" ] || { echo \"ABORTADO: falta \$f en el paquete\"; exit 1; }
  done
  echo \"  productos: \$(ls public/yoga-verde/assets/products | wc -l | tr -d ' ')  fuentes: \$(ls public/yoga-verde/fonts | wc -l | tr -d ' ')\""

# ---------------------------------------------------------------------------
# 5. Publicar y reconstruir. El contexto de build es la RAÍZ del repo remoto:
#    existe un subdirectorio `site/` huérfano que NO es el que sirve Docker.
# ---------------------------------------------------------------------------
say "Publicando en $REMOTE_DIR"
ssh_do "set -euo pipefail
  sudo tar -C $REMOTE_STAGE -cf - . | sudo tar -C $REMOTE_DIR -xf -
  sudo chown -R deploy:deploy $REMOTE_DIR/scripts $REMOTE_DIR/src $REMOTE_DIR/public $REMOTE_DIR/deploy
  rm -rf $REMOTE_STAGE $REMOTE_TAR"

say "docker compose build --no-cache"
ssh_do "cd $REMOTE_DIR && sudo docker compose build --no-cache" 2>&1 | tail -3
ssh_do "cd $REMOTE_DIR && sudo docker compose up -d" 2>&1 | tail -2

# ---------------------------------------------------------------------------
# 6. Verificar contra el sitio en vivo, no contra el log del build.
# ---------------------------------------------------------------------------
say "Verificando en vivo"
rm -f "$TARBALL"
# El contenedor acaba de recrearse: nginx tarda un momento en aceptar tráfico.
# Sin esta espera la verificación da un 404 engañoso con el sitio ya sano.
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

# Que responda 200 no basta: hay que confirmar que sirve ESTE build.
# Nota: no encadenar `curl | grep -q` aquí. Con `set -o pipefail`, grep -q corta
# la tubería en la primera coincidencia, curl muere con SIGPIPE y el pipeline se
# reporta como fallido justo cuando la verificación fue exitosa.
say "Confirmando contenido"
LIVE_HTML="$(curl -s --compressed "https://yoga-verde.srv1175749.hstgr.cloud/")"
if [[ "$LIVE_HTML" == *"data-hero-slide"* ]]; then
  echo "  homepage de Yoga Verde actualizada ✓"
else
  echo "ABORTADO: el HTML servido no corresponde a este build." >&2; exit 1
fi

say "Despliegue completo"
