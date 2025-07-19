#!/bin/bash

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Logs de Docker ===${NC}"
echo -e "${YELLOW}Opciones disponibles:${NC}"
echo "1) Ver logs del Bot de Telegram"
echo "2) Ver logs de la API"
echo "3) Ver logs de todos los servicios"
echo "4) Ver logs del Bot (últimas 100 líneas)"
echo "5) Ver logs de la API (últimas 100 líneas)"
echo "6) Seguir logs del Bot en tiempo real"
echo "7) Seguir logs de la API en tiempo real"
echo "8) Buscar errores en los logs"
echo "9) Ver logs con timestamps"

read -p "Selecciona una opción (1-9): " option

case $option in
    1)
        echo -e "\n${YELLOW}Logs del Bot de Telegram:${NC}"
        docker-compose -f docker-compose.prod.yml logs telegram_bot
        ;;
    2)
        echo -e "\n${YELLOW}Logs de la API:${NC}"
        docker-compose -f docker-compose.prod.yml logs api
        ;;
    3)
        echo -e "\n${YELLOW}Logs de todos los servicios:${NC}"
        docker-compose -f docker-compose.prod.yml logs
        ;;
    4)
        echo -e "\n${YELLOW}Últimas 100 líneas del Bot:${NC}"
        docker-compose -f docker-compose.prod.yml logs --tail=100 telegram_bot
        ;;
    5)
        echo -e "\n${YELLOW}Últimas 100 líneas de la API:${NC}"
        docker-compose -f docker-compose.prod.yml logs --tail=100 api
        ;;
    6)
        echo -e "\n${YELLOW}Siguiendo logs del Bot (Ctrl+C para salir):${NC}"
        docker-compose -f docker-compose.prod.yml logs -f telegram_bot
        ;;
    7)
        echo -e "\n${YELLOW}Siguiendo logs de la API (Ctrl+C para salir):${NC}"
        docker-compose -f docker-compose.prod.yml logs -f api
        ;;
    8)
        echo -e "\n${YELLOW}Buscando errores en los logs:${NC}"
        docker-compose -f docker-compose.prod.yml logs | grep -i "error\|exception\|traceback" --color=always
        ;;
    9)
        echo -e "\n${YELLOW}Logs con timestamps:${NC}"
        docker-compose -f docker-compose.prod.yml logs --timestamps
        ;;
    *)
        echo -e "${RED}Opción inválida${NC}"
        exit 1
        ;;
esac