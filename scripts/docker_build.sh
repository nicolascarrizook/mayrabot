#!/bin/bash

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Construyendo imágenes de Docker ===${NC}"

# Verificar espacio en disco
echo -e "\n${YELLOW}Espacio en disco:${NC}"
df -h / | grep -E '^/|^Filesystem'

# Preguntar si continuar
echo -e "\n${YELLOW}¿Deseas continuar con el build? (s/n)${NC}"
read -r response
if [[ ! "$response" =~ ^[Ss]$ ]]; then
    echo -e "${RED}Build cancelado${NC}"
    exit 1
fi

# Pull últimos cambios
echo -e "\n${YELLOW}Actualizando código...${NC}"
git pull origin main

# Construir con no-cache para asegurar build limpio
echo -e "\n${YELLOW}Construyendo imágenes (esto puede tardar varios minutos)...${NC}"
docker-compose -f docker-compose.prod.yml build --no-cache

# Verificar que se construyeron
echo -e "\n${GREEN}✓ Imágenes construidas${NC}"

# Mostrar imágenes
echo -e "\n${YELLOW}Imágenes de Docker:${NC}"
docker images | grep nutrition

echo -e "\n${GREEN}¡Build completado exitosamente!${NC}"
echo -e "${BLUE}Ahora podés ejecutar ./docker_up.sh para iniciar los servicios${NC}"