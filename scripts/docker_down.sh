#!/bin/bash

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== Deteniendo servicios de Docker ===${NC}"

# Detener servicios
echo -e "\n${YELLOW}Deteniendo contenedores...${NC}"
docker-compose -f docker-compose.prod.yml down

# Verificar que se detuvieron
echo -e "\n${GREEN}✓ Servicios detenidos${NC}"

# Mostrar contenedores activos (deberían estar vacíos)
echo -e "\n${YELLOW}Contenedores activos:${NC}"
docker ps

echo -e "\n${GREEN}¡Listo! Todos los servicios han sido detenidos.${NC}"