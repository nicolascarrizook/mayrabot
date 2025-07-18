#!/bin/bash

echo "=== Desplegando sistema de entrega de PDFs ==="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "\n${GREEN}1. Verificando cambios...${NC}"
git status

echo -e "\n${GREEN}2. Agregando cambios...${NC}"
git add api/services/pdf_generator.py
git add api/routers/motor1.py
git add telegram_bot/utils/api_client.py
git add telegram_bot/handlers/new_plan_handler.py

echo -e "\n${GREEN}3. Commiteando cambios...${NC}"
git commit -m "feat: implementar sistema de entrega de PDFs por Telegram

- PDF generator ahora crea PDFs reales con ReportLab
- Endpoint API para descargar PDFs implementado
- Bot de Telegram ahora envía el PDF al usuario
- Incluye reintentos si el PDF no está listo

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

echo -e "\n${GREEN}4. Pusheando a origin...${NC}"
git push origin main

echo -e "\n${YELLOW}5. IMPORTANTE: Ahora necesitas conectarte al servidor y ejecutar:${NC}"
echo "ssh root@tu-servidor-ip"
echo "cd /root/nutrition-bot"
echo "./redeploy.sh"

echo -e "\n${GREEN}¡Cambios listos para desplegar!${NC}"
echo -e "${YELLOW}Recuerda: El directorio 'generated_pdfs' debe existir en el servidor${NC}"