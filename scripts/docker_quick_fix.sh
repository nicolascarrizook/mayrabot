#!/bin/bash

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Quick Fix - Solución Rápida ===${NC}"

# Pull últimos cambios
echo -e "\n${YELLOW}1. Actualizando código...${NC}"
git pull origin main

# Reiniciar solo el bot (más rápido que rebuild)
echo -e "\n${YELLOW}2. Reiniciando el bot...${NC}"
docker-compose -f docker-compose.prod.yml restart telegram_bot

# Esperar
echo -e "\n${YELLOW}3. Esperando que reinicie...${NC}"
sleep 5

# Ver logs
echo -e "\n${YELLOW}4. Últimos logs del bot:${NC}"
docker-compose -f docker-compose.prod.yml logs --tail=30 telegram_bot

# Verificar estado
echo -e "\n${YELLOW}5. Estado actual:${NC}"
docker-compose -f docker-compose.prod.yml ps telegram_bot

echo -e "\n${GREEN}✓ Quick fix completado${NC}"
echo -e "${BLUE}Si sigue el error, usa ./docker_build.sh para rebuild completo${NC}"