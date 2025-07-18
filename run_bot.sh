#!/bin/bash
# Script para ejecutar el bot de Telegram

echo "🤖 Iniciando Bot Nutricional..."

# Verificar que el entorno virtual existe
if [ ! -d "venv" ]; then
    echo "❌ Error: No se encuentra el entorno virtual 'venv'"
    echo "Por favor, crea el entorno virtual con: python -m venv venv"
    exit 1
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

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
if ! python -c "import telegram" 2>/dev/null; then
    echo "⚠️  Instalando dependencias faltantes..."
    pip install -r requirements.txt
fi

# Ejecutar el bot
echo "🚀 Ejecutando bot..."
python telegram_bot/bot.py