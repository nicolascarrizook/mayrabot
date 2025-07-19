#!/bin/bash

echo "=== Debug Script para Nutrition Bot ==="
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}1. Verificando sintaxis de Python...${NC}"
echo "Checking secretary_mode.py..."
python3 -m py_compile telegram_bot/handlers/secretary_mode.py 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ secretary_mode.py OK${NC}"
else
    echo -e "${RED}✗ Error en secretary_mode.py${NC}"
fi

echo "Checking progress.py..."
python3 -m py_compile telegram_bot/utils/progress.py 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ progress.py OK${NC}"
else
    echo -e "${RED}✗ Error en progress.py${NC}"
fi

echo "Checking new_plan_handler.py..."
python3 -m py_compile telegram_bot/handlers/new_plan_handler.py 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ new_plan_handler.py OK${NC}"
else
    echo -e "${RED}✗ Error en new_plan_handler.py${NC}"
fi

echo ""
echo -e "${YELLOW}2. Verificando importaciones...${NC}"
python3 -c "
try:
    import telegram_bot.handlers.secretary_mode
    print('✓ Secretary mode imports OK')
except Exception as e:
    print(f'✗ Error importing secretary_mode: {e}')

try:
    import telegram_bot.utils.progress
    print('✓ Progress utils imports OK')
except Exception as e:
    print(f'✗ Error importing progress: {e}')
" 2>&1

echo ""
echo -e "${YELLOW}3. Si estás usando Docker, ejecutá:${NC}"
echo "docker-compose logs telegram_bot --tail=100"
echo ""
echo "docker-compose logs api --tail=100"

echo ""
echo -e "${YELLOW}4. Para ver logs en tiempo real:${NC}"
echo "docker-compose logs -f telegram_bot"

echo ""
echo -e "${YELLOW}5. Para reiniciar servicios:${NC}"
echo "docker-compose restart telegram_bot"
echo "docker-compose restart api"

echo ""
echo -e "${YELLOW}6. Archivos modificados recientemente:${NC}"
find . -name "*.py" -type f -mmin -60 ! -path "./venv/*" ! -path "./__pycache__/*" | head -10

echo ""
echo -e "${GREEN}Debug script completado!${NC}"