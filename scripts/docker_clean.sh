#!/bin/bash

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${RED}=== Limpieza de Docker (CUIDADO: Esto borrará datos) ===${NC}"

# Mostrar espacio actual
echo -e "\n${YELLOW}Espacio en disco actual:${NC}"
df -h / | grep -E '^/|^Filesystem'

# Confirmar acción
echo -e "\n${RED}ADVERTENCIA: Esto va a:${NC}"
echo "- Detener todos los contenedores"
echo "- Borrar imágenes no utilizadas"
echo "- Borrar volúmenes no utilizados"
echo "- Borrar redes no utilizadas"
echo "- Borrar build cache"

echo -e "\n${YELLOW}¿Estás seguro? (escribe 'SI' en mayúsculas para continuar)${NC}"
read -r response
if [[ "$response" != "SI" ]]; then
    echo -e "${GREEN}Limpieza cancelada${NC}"
    exit 0
fi

# Detener servicios
echo -e "\n${YELLOW}1. Deteniendo servicios...${NC}"
docker-compose -f docker-compose.prod.yml down

# Limpiar contenedores detenidos
echo -e "\n${YELLOW}2. Limpiando contenedores detenidos...${NC}"
docker container prune -f

# Limpiar imágenes no utilizadas
echo -e "\n${YELLOW}3. Limpiando imágenes no utilizadas...${NC}"
docker image prune -a -f

# Limpiar volúmenes no utilizados
echo -e "\n${YELLOW}4. Limpiando volúmenes no utilizados...${NC}"
docker volume prune -f

# Limpiar redes no utilizadas
echo -e "\n${YELLOW}5. Limpiando redes no utilizadas...${NC}"
docker network prune -f

# Limpiar build cache
echo -e "\n${YELLOW}6. Limpiando build cache...${NC}"
docker builder prune -a -f

# Limpiar logs del sistema si es necesario
echo -e "\n${YELLOW}7. ¿Limpiar logs del sistema? (s/n)${NC}"
read -r clean_logs
if [[ "$clean_logs" =~ ^[Ss]$ ]]; then
    sudo journalctl --vacuum-time=3d
    sudo apt-get clean
    sudo apt-get autoremove -y
fi

# Mostrar nuevo espacio
echo -e "\n${GREEN}Espacio después de la limpieza:${NC}"
df -h / | grep -E '^/|^Filesystem'

echo -e "\n${GREEN}✓ Limpieza completada${NC}"
echo -e "${BLUE}Ahora podés ejecutar ./docker_build.sh para reconstruir${NC}"