# --- PARTE A: VARIABLES (ajusta si hace falta) ---
PROJECT_ID="promising-node-469902-m2"
REGION="us-central1"
PROD_SERVICE="telegram-bot-agency"   # nombre de tu servicio prod (ajusta si es otro)
DEV_SERVICE="telegram-bot-dev"
SECRET_NAME="telegram-bot-token-dev"
IMAGE="gcr.io/${PROJECT_ID}/telegram-bot-agency:dev-$(date +%Y%m%d%H%M)"
SERVICE_ACCOUNT="900061908290-compute@developer.gserviceaccount.com"   # pega aquí la service account que copiaste desde la UI

# Verificación mínima
echo "PROJECT: $PROJECT_ID   REGION: $REGION   SERVICE_ACCOUNT: $SERVICE_ACCOUNT"

# --- PARTE B: Crear/añadir secreto dev (usa /tmp/dev_token.txt) ---
if [ ! -f /tmp/dev_token.txt ]; then
  echo "ERROR: /tmp/dev_token.txt no existe. Crea el fichero con tu token y vuelve a ejecutar."
  exit 1
fi

if gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" >/dev/null 2>&1; then
  echo "Añadiendo nueva versión a secreto $SECRET_NAME ..."
  gcloud secrets versions add "$SECRET_NAME" --data-file=/tmp/dev_token.txt --project="$PROJECT_ID"
else
  echo "Creando secreto $SECRET_NAME ..."
  gcloud secrets create "$SECRET_NAME" --data-file=/tmp/dev_token.txt --replication-policy="automatic" --project="$PROJECT_ID"
fi

# (opcional) borrar el temporal de manera segura
shred -u /tmp/dev_token.txt 2>/dev/null || rm -f /tmp/dev_token.txt

# --- PARTE C: Dar permiso a la service account para acceder al secreto ---
echo "Asignando role secretAccessor a $SERVICE_ACCOUNT para el secreto $SECRET_NAME ..."
gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
  --project="$PROJECT_ID" \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"

# --- PARTE D: Build + push de la imagen (Cloud Build) ---
echo "Iniciando build..."
gcloud builds submit --tag "$IMAGE" .

# --- PARTE E: Deploy Cloud Run (dev) exponiendo el secreto como env var TELEGRAM_BOT_TOKEN ---
echo "Desplegando $DEV_SERVICE en Cloud Run..."
gcloud run deploy "$DEV_SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform managed \
  --memory 512Mi \
  --concurrency 1 \
  --allow-unauthenticated \
  --service-account="$SERVICE_ACCOUNT" \
  --set-env-vars SPREADSHEET_ID=1wUi1v53PeV9HUdtwHsbeIweM4VOTjueh6_KJMtHBjeE,LOGS_SHEET_ID=1m7TRBqjkM5BgFtEdkWqD40LJpJg3pNMOje4VEIKpsko,INDEX_TTL_SECONDS=600,ROW_CACHE_SIZE=200,MIN_CLIENT_NUMBER_LENGTH=3,DEDUP_WINDOW_SECONDS=30 \
  --set-secrets TELEGRAM_BOT_TOKEN=projects/"$PROJECT_ID"/secrets/"$SECRET_NAME":latest

# --- PARTE F: Obtener URL del servicio dev y hacer health-check ---
SERVICE_URL=$(gcloud run services describe "$DEV_SERVICE" --project="$PROJECT_ID" --region="$REGION" --format="value(status.url)")
echo "Dev service URL: $SERVICE_URL"
echo "Health check:"
curl -s "$SERVICE_URL/health" || echo "No response from health endpoint"