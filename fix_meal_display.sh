#!/bin/bash

echo "=== Corrigiendo visualización de comidas en el plan nutricional ==="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "\n${GREEN}1. Verificando cambios...${NC}"
git status

echo -e "\n${GREEN}2. Agregando archivos modificados...${NC}"
git add api/routers/motor1.py
git add api/services/plan_generator.py
git add telegram_bot/utils/formatters.py

echo -e "\n${GREEN}3. Commiteando cambios...${NC}"
git commit -m "fix: corregir visualización de comidas en Telegram

- Agregar logs de depuración en motor1.py
- Implementar parser completo para respuestas de OpenAI
- Mejorar formatters para mostrar mensaje cuando no hay comidas
- Manejar múltiples formatos de respuesta JSON

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

echo -e "\n${GREEN}4. Pusheando a origin...${NC}"
git push origin main

echo -e "\n${YELLOW}5. Para desplegar en el servidor:${NC}"
echo "ssh root@tu-servidor-ip"
echo "cd /root/nutrition-bot"
echo "./redeploy.sh"

echo -e "\n${GREEN}¡Listo! Los cambios están listos para desplegar.${NC}"
echo -e "${YELLOW}NOTA: Revisa los logs del servidor para ver qué formato está devolviendo OpenAI${NC}"