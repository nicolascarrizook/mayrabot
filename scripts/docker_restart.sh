#!/bin/bash

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Reiniciando servicios de Docker ===${NC}"

# Mostrar servicios actuales
echo -e "\n${YELLOW}Estado actual:${NC}"
docker-compose -f docker-compose.prod.yml ps

# Reiniciar servicios
echo -e "\n${YELLOW}Reiniciando servicios...${NC}"
docker-compose -f docker-compose.prod.yml restart

# Esperar un momento
echo -e "\n${YELLOW}Esperando que los servicios reinicien...${NC}"
sleep 5

# Verificar nuevo estado
echo -e "\n${YELLOW}Nuevo estado:${NC}"
docker-compose -f docker-compose.prod.yml ps

# Mostrar logs recientes
echo -e "\n${YELLOW}Logs después del reinicio:${NC}"
docker-compose -f docker-compose.prod.yml logs --tail=20

echo -e "\n${GREEN}✓ Servicios reiniciados${NC}"