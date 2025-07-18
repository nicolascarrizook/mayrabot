#!/bin/bash

echo "=== Verificando y corrigiendo el despliegue ==="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "\n${GREEN}1. Obteniendo últimos cambios...${NC}"
git pull origin main

echo -e "\n${GREEN}2. Verificando que activity_level esté en el código...${NC}"
if grep -q "activity_level" telegram_bot/utils/api_client.py; then
    echo -e "${GREEN}✓ El código contiene activity_level${NC}"
else
    echo -e "${RED}✗ ERROR: El código NO contiene activity_level${NC}"
    exit 1
fi

echo -e "\n${GREEN}3. Deteniendo contenedores...${NC}"
docker-compose -f docker-compose.prod.yml down

echo -e "\n${GREEN}4. Eliminando imágenes en caché del bot...${NC}"
docker rmi mayrabot_telegram_bot -f 2>/dev/null || true

echo -e "\n${GREEN}5. Reconstruyendo con --no-cache...${NC}"
docker-compose -f docker-compose.prod.yml build --no-cache telegram_bot

echo -e "\n${GREEN}6. Iniciando servicios...${NC}"
docker-compose -f docker-compose.prod.yml up -d

echo -e "\n${GREEN}7. Esperando que los servicios inicien...${NC}"
sleep 10

echo -e "\n${GREEN}8. Verificando logs del bot...${NC}"
docker-compose -f docker-compose.prod.yml logs --tail 50 telegram_bot | grep -E "(activity_level|Started successfully|ERROR)"

echo -e "\n${GREEN}9. Verificando que el contenedor esté ejecutándose...${NC}"
docker-compose -f docker-compose.prod.yml ps

echo -e "\n${GREEN}¡Despliegue completado!${NC}"
echo "Ahora prueba el bot nuevamente. Si sigue fallando, ejecuta:"
echo "docker-compose -f docker-compose.prod.yml logs -f telegram_bot"