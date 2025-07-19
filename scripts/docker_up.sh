#!/bin/bash

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Iniciando servicios de Docker ===${NC}"

# Verificar que el archivo .env existe
if [ ! -f .env ]; then
    echo -e "${RED}ERROR: No se encontró el archivo .env${NC}"
    echo -e "${YELLOW}Copiá .env.example a .env y configurá las variables${NC}"
    exit 1
fi

# Verificar variables críticas
echo -e "\n${YELLOW}Verificando configuración...${NC}"
if ! grep -q "TELEGRAM_BOT_TOKEN=.*[a-zA-Z0-9]" .env; then
    echo -e "${RED}ERROR: TELEGRAM_BOT_TOKEN no está configurado en .env${NC}"
    exit 1
fi

if ! grep -q "OPENAI_API_KEY=.*[a-zA-Z0-9]" .env; then
    echo -e "${RED}ERROR: OPENAI_API_KEY no está configurado en .env${NC}"
    exit 1
fi

# Iniciar servicios en modo detached
echo -e "\n${YELLOW}Iniciando servicios...${NC}"
docker-compose -f docker-compose.prod.yml up -d

# Esperar un momento para que inicien
echo -e "\n${YELLOW}Esperando que los servicios inicien...${NC}"
sleep 5

# Verificar estado
echo -e "\n${YELLOW}Estado de los contenedores:${NC}"
docker-compose -f docker-compose.prod.yml ps

# Mostrar logs iniciales
echo -e "\n${YELLOW}Logs iniciales del bot:${NC}"
docker-compose -f docker-compose.prod.yml logs --tail=20 telegram_bot

echo -e "\n${GREEN}✓ Servicios iniciados${NC}"
echo -e "${BLUE}Para ver logs en tiempo real: ./docker_logs.sh${NC}"
echo -e "${BLUE}Para detener: ./docker_down.sh${NC}"