#!/bin/bash

echo "=== Desplegando Nutrition Bot Professional v2.0 ==="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "\n${BLUE}=== MEJORAS IMPLEMENTADAS ===${NC}"
echo -e "${GREEN}✅ PDF Generator corregido - Muestra comidas correctamente${NC}"
echo -e "${GREEN}✅ Barra de progreso profesional con 6 pasos detallados${NC}"
echo -e "${GREEN}✅ Feedback instantáneo al ingresar datos (IMC, calorías)${NC}"
echo -e "${GREEN}✅ Búsqueda inteligente de recetas con scoring${NC}"
echo -e "${GREEN}✅ Mejor integración con ChromaDB${NC}"

echo -e "\n${YELLOW}1. Verificando cambios...${NC}"
git status --short

echo -e "\n${YELLOW}2. Agregando todos los archivos modificados...${NC}"
git add api/services/pdf_generator.py
git add api/services/plan_generator.py
git add api/services/recipe_searcher.py
git add telegram_bot/handlers/new_plan_handler.py
git add telegram_bot/utils/progress.py
git add telegram_bot/utils/formatters.py
git add api/routers/motor1.py

echo -e "\n${YELLOW}3. Commiteando mejoras profesionales...${NC}"
git commit -m "feat: versión profesional del bot de nutrición v2.0

✨ Nuevas características:
- PDF generator completamente reescrito con diseño profesional
- Barra de progreso animada con tiempo estimado
- Feedback instantáneo durante ingreso de datos
- Búsqueda inteligente de recetas con scoring
- Mejor manejo de errores y logs detallados

🎨 Mejoras UX:
- Progreso visual durante generación (6 pasos)
- Cálculo instantáneo de IMC
- Mensajes contextuales según patologías
- Tips durante el proceso de generación

🔧 Mejoras técnicas:
- RecipeSearcher con filtrado inteligente
- Mejor integración ChromaDB
- Estructura de datos correcta en PDF
- Logs extensivos para debugging

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

echo -e "\n${YELLOW}4. Pusheando a GitHub...${NC}"
git push origin main

echo -e "\n${BLUE}=== INSTRUCCIONES DE DEPLOYMENT ===${NC}"
echo -e "${YELLOW}En el servidor DigitalOcean:${NC}"
echo ""
echo "ssh root@tu-servidor-ip"
echo "cd /root/nutrition-bot"
echo ""
echo "# Pull últimos cambios"
echo "git pull origin main"
echo ""
echo "# Detener servicios"
echo "docker-compose -f docker-compose.prod.yml down"
echo ""
echo "# Rebuild con cache limpio"
echo "docker-compose -f docker-compose.prod.yml build --no-cache"
echo ""
echo "# Iniciar servicios"
echo "docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "# Verificar logs"
echo "docker-compose -f docker-compose.prod.yml logs -f"

echo -e "\n${GREEN}=== TESTING RECOMENDADO ===${NC}"
echo "1. Crear un plan nuevo y verificar:"
echo "   - Barra de progreso funciona correctamente"
echo "   - Feedback de IMC al ingresar peso"
echo "   - PDF muestra las comidas con ingredientes"
echo ""
echo "2. Revisar logs para confirmar:"
echo "   - Búsqueda de recetas encuentra resultados"
echo "   - Parser de OpenAI funciona"
echo "   - PDF se genera sin errores"

echo -e "\n${GREEN}¡Deployment script listo!${NC}"
echo -e "${BLUE}Esta es una actualización mayor - versión profesional del bot${NC}"