# Bot Nutricional - Sistema de Planificación Nutricional Automatizado

Sistema completo para generar planes nutricionales personalizados utilizando IA, con interfaz de Telegram.

## 🚀 Características

- **Generación de Planes Personalizados**: Crea planes nutricionales adaptados a las necesidades individuales
- **Motor de Reemplazo de Comidas**: Encuentra alternativas equivalentes para cualquier comida
- **Base de Datos de Recetas**: Sistema RAG con ChromaDB para búsqueda semántica
- **Interfaz de Telegram**: Bot interactivo fácil de usar
- **API RESTful**: Backend escalable con FastAPI
- **Sin almacenamiento de datos**: Genera planes bajo demanda sin guardar información personal

## 🏗️ Arquitectura

```
Bot Telegram → API FastAPI → RAG + OpenAI → Usuario
                    ↗
              ChromaDB (Recetas)
```

### Componentes principales:

1. **Bot de Telegram**: Interfaz de usuario conversacional
2. **API FastAPI**: Backend que maneja la lógica de negocio
3. **ChromaDB**: Base de datos vectorial para búsqueda semántica de recetas
4. **OpenAI GPT-4**: Generación inteligente de planes nutricionales

## 📋 Requisitos

- Python 3.11+
- Docker y Docker Compose
- Token de bot de Telegram
- API Key de OpenAI
- Archivos DOCX con recetas en `data/`

## 🛠️ Instalación

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd nutrition-bot
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env` y configurar:
- `TELEGRAM_BOT_TOKEN`: Token del bot de Telegram (obtener de @BotFather)
- `OPENAI_API_KEY`: API key de OpenAI

### 3. Colocar archivos DOCX

Colocar los archivos DOCX con recetas en el directorio `data/`:
- almuerzoscena.docx
- desayunos.docx
- desayunosequivalentes.docx
- recetas.docx

### 4. Cargar recetas en ChromaDB

```bash
# Activar entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Cargar recetas
python data_processor/load_to_chromadb.py
```

### 5. Iniciar servicios con Docker

```bash
docker compose up -d
```

### 6. Ejecutar el bot

```bash
./run_bot.sh
```

## 📱 Uso del Bot

### Comandos disponibles:

- `/start` - Iniciar el bot y ver el menú principal
- `/nuevo_plan` - Crear un nuevo plan nutricional
- `/reemplazar` - Buscar alternativas para una comida
- `/ayuda` - Mostrar ayuda
- `/cancelar` - Cancelar la operación actual

### Flujo de generación de plan:

1. **Información personal**: El bot solicita nombre, edad, género, altura y peso
2. **Actividad física**: Selección del nivel de actividad (sedentario a muy intenso)
3. **Información médica**: Patologías, alergias, preferencias y alimentos no deseados
4. **Configuración del plan**: Número de comidas diarias y días del plan
5. **Nivel económico**: Estándar o económico para las recetas
6. **Generación**: El sistema crea el plan personalizado con GPT-4

### Reemplazo de comidas:

1. Seleccionar tipo de comida a reemplazar
2. Indicar motivo del reemplazo
3. Especificar ingredientes a evitar
4. Elegir nivel económico
5. Seleccionar entre las alternativas sugeridas

## 🔧 Desarrollo

### Estructura del proyecto:

```
nutrition-bot/
├── api/                    # Backend FastAPI
│   ├── main.py            # Aplicación principal
│   ├── routers/           # Endpoints por motor
│   ├── services/          # Servicios (ChromaDB, OpenAI)
│   └── models/            # Modelos de datos
├── data_processor/        # Procesamiento de DOCX
│   ├── docx_processor.py  # Lector de DOCX
│   ├── recipe_extractor.py # Extractor de recetas
│   └── load_to_chromadb.py # Cargador a base de datos
├── telegram_bot/          # Bot de Telegram
│   ├── bot.py            # Aplicación principal
│   ├── handlers/         # Manejadores de conversación
│   ├── utils/            # Utilidades y helpers
│   └── middleware/       # Middleware de errores
├── prompts/              # Templates de prompts para IA
│   ├── motor1_prompt.py  # Prompt para planes nuevos
│   ├── motor2_prompt.py  # Prompt para ajustes
│   └── motor3_prompt.py  # Prompt para reemplazos
└── data/                 # Archivos DOCX con recetas
```

### Ejecutar en modo desarrollo:

```bash
# Terminal 1: API
cd nutrition-bot
source venv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Bot
cd nutrition-bot
source venv/bin/activate
python telegram_bot/bot.py
```

### Tests de la API:

```bash
# Test de salud
curl http://localhost:8000/health

# Test de búsqueda de recetas
./test_search.sh
```

## 📊 Motores del Sistema

### Motor 1: Generación de Planes Nuevos
- Entrada: Información completa del paciente
- Proceso: Análisis de requerimientos nutricionales + búsqueda RAG de recetas
- Salida: Plan nutricional completo para los días solicitados

### Motor 2: Ajustes y Control (Planeado)
- Entrada: Plan existente + progreso del paciente
- Proceso: Análisis de adherencia y resultados
- Salida: Plan ajustado con modificaciones

### Motor 3: Reemplazo de Comidas
- Entrada: Comida a reemplazar + restricciones
- Proceso: Búsqueda semántica de alternativas equivalentes
- Salida: Lista de opciones con valores nutricionales similares

## 🔒 Seguridad y Privacidad

- **Sin almacenamiento**: No se guarda información personal
- **Generación bajo demanda**: Los planes se crean en tiempo real
- **Comunicación segura**: Uso de HTTPS y tokens de Telegram
- **Validación de entrada**: Sanitización de todos los datos del usuario

## 🐛 Solución de Problemas

### El bot no responde:
1. Verificar token en `.env`: `TELEGRAM_BOT_TOKEN`
2. Comprobar que la API esté activa: `curl http://localhost:8000/health`
3. Revisar logs del bot: Ver salida de `./run_bot.sh`

### Error al generar planes:
1. Verificar API key de OpenAI en `.env`
2. Comprobar límites de rate/quota en OpenAI
3. Verificar que ChromaDB tenga recetas: `docker compose logs chromadb`

### Problemas con Docker:
1. Usar `docker compose` (sin guión)
2. Liberar puertos: 8000 (API), 6380 (Redis)
3. Reiniciar: `docker compose down && docker compose up -d`

### Error de dependencias Python:
1. Verificar versión de Python: `python --version` (debe ser 3.11+)
2. Actualizar pip: `pip install --upgrade pip`
3. Reinstalar dependencias: `pip install -r requirements.txt --force-reinstall`

## 📈 Monitoreo

### Logs en tiempo real:
```bash
# Todos los servicios
docker compose logs -f

# Servicio específico
docker compose logs -f api
docker compose logs -f telegram_bot
```

### Métricas de uso:
- Requests a la API: Ver logs de FastAPI
- Uso del bot: Logs del bot de Telegram
- Búsquedas en ChromaDB: Logs del servicio

## 🚀 Deployment

### Producción con Docker:
1. Configurar `.env` con valores de producción
2. Usar `docker compose -f docker-compose.prod.yml up -d`
3. Configurar reverse proxy (nginx) para la API
4. Habilitar HTTPS con Let's Encrypt

### Variables de entorno adicionales para producción:
- `API_BASE_URL`: URL pública de la API
- `LOG_LEVEL`: Cambiar a "WARNING" o "ERROR"
- `REDIS_PASSWORD`: Configurar contraseña para Redis

## 👥 Contribuir

1. Fork el proyecto
2. Crear rama feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -m 'Agregar nueva funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

### Estándares de código:
- Usar type hints en Python
- Documentar funciones con docstrings
- Seguir PEP 8
- Agregar tests para nuevas funcionalidades

## 📝 Licencia

Este proyecto es privado y confidencial.

## 📞 Soporte

Para soporte técnico o preguntas sobre el sistema, contactar al equipo de desarrollo.