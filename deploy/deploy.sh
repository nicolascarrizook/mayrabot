#!/bin/bash

# Script de deployment para Nutrition Bot
# Ejecutar este script después de setup-droplet.sh

set -e

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Variables
REPO_URL="https://github.com/tu-usuario/nutrition-bot.git"  # CAMBIAR POR TU REPO
APP_DIR="/home/nutritionbot/nutrition-bot"
USER="nutritionbot"

echo -e "${GREEN}🚀 Iniciando deployment de Nutrition Bot...${NC}"

# 1. Verificar que estamos en el servidor correcto
if [ ! -d "/home/nutritionbot" ]; then
    echo -e "${RED}Error: Este script debe ejecutarse en el servidor configurado con setup-droplet.sh${NC}"
    exit 1
fi

# 2. Cambiar al usuario de la aplicación
if [ "$USER" != "nutritionbot" ]; then
    echo "Cambiando a usuario nutritionbot..."
    sudo -u nutritionbot -i bash -c "cd $APP_DIR && bash deploy/deploy.sh"
    exit 0
fi

# 3. Clonar o actualizar repositorio
if [ ! -d "$APP_DIR/.git" ]; then
    echo -e "${GREEN}Clonando repositorio...${NC}"
    git clone $REPO_URL $APP_DIR
    cd $APP_DIR
else
    echo -e "${GREEN}Actualizando repositorio...${NC}"
    cd $APP_DIR
    git pull origin main
fi

# 4. Crear archivo .env.prod si no existe
if [ ! -f ".env.prod" ]; then
    echo -e "${YELLOW}⚠️  Creando archivo .env.prod de ejemplo...${NC}"
    cat > .env.prod << 'EOF'
# Configuración de Producción
# IMPORTANTE: Editar estos valores antes de ejecutar

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=4000

# ChromaDB
CHROMA_PERSIST_DIRECTORY=./chroma_db
CHROMA_COLLECTION_NAME=nutrition_recipes

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Redis
REDIS_URL=redis://:your_redis_password@redis:6379
REDIS_PASSWORD=your_redis_password
REDIS_TTL=3600

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Security
SECRET_KEY=your_secret_key_here_change_in_production

# Environment
ENVIRONMENT=production
EOF
    echo -e "${RED}⚠️  IMPORTANTE: Editar .env.prod con las credenciales correctas antes de continuar${NC}"
    echo "Presiona Enter cuando hayas editado el archivo..."
    read
fi

# 5. Crear directorios necesarios
echo -e "${GREEN}Creando directorios...${NC}"
mkdir -p data
mkdir -p chroma_db
mkdir -p generated_pdfs
mkdir -p logs
mkdir -p nginx/sites-enabled

# 6. Copiar archivos DOCX si existen
if [ -d "data_backup" ]; then
    echo -e "${GREEN}Copiando archivos DOCX...${NC}"
    cp data_backup/*.docx data/ 2>/dev/null || true
fi

# 7. Construir imágenes de Docker
echo -e "${GREEN}Construyendo imágenes de Docker...${NC}"
docker-compose -f docker-compose.prod.yml build

# 8. Detener servicios anteriores si existen
echo -e "${GREEN}Deteniendo servicios anteriores...${NC}"
docker-compose -f docker-compose.prod.yml down

# 9. Iniciar servicios
echo -e "${GREEN}Iniciando servicios...${NC}"
docker-compose -f docker-compose.prod.yml up -d

# 10. Esperar a que los servicios estén listos
echo -e "${GREEN}Esperando a que los servicios estén listos...${NC}"
sleep 10

# 11. Cargar recetas en ChromaDB
echo -e "${GREEN}Cargando recetas en ChromaDB...${NC}"
docker-compose -f docker-compose.prod.yml exec -T api python data_processor/load_to_chromadb.py || {
    echo -e "${YELLOW}Advertencia: No se pudieron cargar las recetas. Verifica que los archivos DOCX estén en data/${NC}"
}

# 12. Verificar estado de servicios
echo -e "${GREEN}Verificando servicios...${NC}"
docker-compose -f docker-compose.prod.yml ps

# 13. Mostrar logs
echo -e "${GREEN}Últimas líneas de logs:${NC}"
docker-compose -f docker-compose.prod.yml logs --tail=20

# 14. Información final
echo -e "${GREEN}✅ Deployment completado!${NC}"
echo ""
echo "📊 Comandos útiles:"
echo "- Ver logs en tiempo real: docker-compose -f docker-compose.prod.yml logs -f"
echo "- Ver logs de un servicio: docker-compose -f docker-compose.prod.yml logs -f telegram_bot"
echo "- Reiniciar servicios: docker-compose -f docker-compose.prod.yml restart"
echo "- Detener servicios: docker-compose -f docker-compose.prod.yml down"
echo "- Ver estado: docker-compose -f docker-compose.prod.yml ps"
echo ""
echo "🔍 Para monitorear:"
echo "- ./monitor.sh"
echo ""

# Verificar si el bot está respondiendo
if [ -n "$(docker-compose -f docker-compose.prod.yml ps -q telegram_bot)" ]; then
    echo -e "${GREEN}✅ El bot de Telegram está ejecutándose${NC}"
    echo "Puedes probarlo enviando /start a tu bot"
else
    echo -e "${RED}❌ El bot de Telegram no está ejecutándose${NC}"
    echo "Revisa los logs con: docker-compose -f docker-compose.prod.yml logs telegram_bot"
fi