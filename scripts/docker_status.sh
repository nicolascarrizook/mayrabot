#!/bin/bash

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Estado del Sistema Docker ===${NC}"

# Estado de contenedores
echo -e "\n${YELLOW}1. Contenedores en ejecución:${NC}"
docker-compose -f docker-compose.prod.yml ps

# Uso de recursos
echo -e "\n${YELLOW}2. Uso de recursos:${NC}"
docker stats --no-stream

# Espacio en disco
echo -e "\n${YELLOW}3. Espacio en disco:${NC}"
df -h / | grep -E '^/|^Filesystem'

# Uso de Docker
echo -e "\n${YELLOW}4. Uso de espacio por Docker:${NC}"
docker system df

# Últimos logs de error
echo -e "\n${YELLOW}5. Últimos errores (si hay):${NC}"
docker-compose -f docker-compose.prod.yml logs --tail=50 | grep -i "error\|exception" | tail -10 || echo "No se encontraron errores recientes"

# Verificar servicios
echo -e "\n${YELLOW}6. Verificación de servicios:${NC}"

# Verificar API
API_STATUS=$(docker-compose -f docker-compose.prod.yml ps api | grep "Up" > /dev/null && echo "✓ RUNNING" || echo "✗ DOWN")
echo -e "API: ${API_STATUS}"

# Verificar Bot
BOT_STATUS=$(docker-compose -f docker-compose.prod.yml ps telegram_bot | grep "Up" > /dev/null && echo "✓ RUNNING" || echo "✗ DOWN")
echo -e "Bot: ${BOT_STATUS}"

# Verificar ChromaDB
if [ -d "./chroma_db" ]; then
    CHROMA_SIZE=$(du -sh ./chroma_db | cut -f1)
    echo -e "ChromaDB: ✓ EXISTS (Size: ${CHROMA_SIZE})"
else
    echo -e "ChromaDB: ✗ NOT FOUND"
fi

echo -e "\n${GREEN}Estado del sistema completado${NC}"