#!/bin/bash
# Script alternativo para ejecutar el bot de Telegram usando directamente el venv

echo "🤖 Iniciando Bot Nutricional (modo directo)..."

# Verificar que el entorno virtual existe
if [ ! -d "venv" ]; then
    echo "❌ Error: No se encuentra el entorno virtual 'venv'"
    echo "Por favor, crea el entorno virtual con: python -m venv venv"
    exit 1
fi

# Verificar que el archivo .env existe
if [ ! -f .env ]; then
    echo "❌ Error: No se encuentra el archivo .env"
    echo "Por favor, crea un archivo .env con el TELEGRAM_BOT_TOKEN"
    exit 1
fi

# Verificar que el token está configurado
if ! grep -q "TELEGRAM_BOT_TOKEN=" .env; then
    echo "❌ Error: TELEGRAM_BOT_TOKEN no está configurado en .env"
    exit 1
fi

# Verificar que la API está corriendo
echo "🔍 Verificando conexión con la API..."
if curl -s -f http://localhost:8000/health > /dev/null; then
    echo "✅ API está funcionando correctamente"
else
    echo "⚠️  Advertencia: No se puede conectar con la API en http://localhost:8000"
    echo "El bot se iniciará pero necesitará la API para funcionar correctamente"
fi

# Verificar que las dependencias están instaladas
echo "📦 Verificando dependencias..."
if ! venv/bin/python -c "import telegram" 2>/dev/null; then
    echo "⚠️  Instalando dependencias faltantes..."
    venv/bin/pip install -r requirements.txt
fi

# Ejecutar el bot con el Python del venv directamente
echo "🚀 Ejecutando bot..."
venv/bin/python telegram_bot/bot.py