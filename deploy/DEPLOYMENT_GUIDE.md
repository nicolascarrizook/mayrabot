# Guía de Deployment en DigitalOcean

Esta guía detalla el proceso completo para desplegar el Nutrition Bot en un Droplet de DigitalOcean.

## 📋 Requisitos Previos

1. **Cuenta en DigitalOcean** con créditos o método de pago configurado
2. **Token de Bot de Telegram** (obtener de @BotFather)
3. **API Key de OpenAI** con créditos disponibles
4. **Archivos DOCX** con las recetas (subirlos al servidor)
5. **Dominio** (opcional, para HTTPS)

## 🚀 Paso 1: Crear el Droplet

1. Ingresar a DigitalOcean y crear un nuevo Droplet:
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: 
     - Mínimo: Basic, Regular Intel, 2 GB RAM / 1 CPU ($12/mes)
     - Recomendado: Basic, Regular Intel, 4 GB RAM / 2 CPUs ($24/mes)
   - **Datacenter**: Elegir el más cercano a tus usuarios
   - **Authentication**: SSH keys (más seguro) o Password
   - **Hostname**: `nutrition-bot` o el que prefieras

2. Anotar la IP del servidor una vez creado

## 🔧 Paso 2: Configuración Inicial del Servidor

1. **Conectarse al servidor**:
   ```bash
   ssh root@TU_IP_DEL_SERVIDOR
   ```

2. **Descargar y ejecutar el script de configuración**:
   ```bash
   # Descargar el script
   wget https://raw.githubusercontent.com/tu-usuario/nutrition-bot/main/deploy/setup-droplet.sh
   
   # Dar permisos de ejecución
   chmod +x setup-droplet.sh
   
   # Ejecutar (opcionalmente con dominio si lo tienes)
   ./setup-droplet.sh
   # O con dominio:
   DOMAIN=tudominio.com ./setup-droplet.sh
   ```

   Este script automatiza:
   - Instalación de Docker y Docker Compose
   - Configuración de firewall y seguridad
   - Creación de usuario para la aplicación
   - Configuración de swap y optimizaciones
   - Estructura de directorios

## 📦 Paso 3: Deployment de la Aplicación

1. **Cambiar al usuario de la aplicación**:
   ```bash
   su - nutritionbot
   ```

2. **Clonar el repositorio**:
   ```bash
   cd ~
   git clone https://github.com/tu-usuario/nutrition-bot.git
   cd nutrition-bot
   ```

3. **Configurar variables de entorno**:
   ```bash
   # Copiar el ejemplo
   cp .env.prod.example .env.prod
   
   # Editar con tus credenciales
   nano .env.prod
   ```

   Configurar obligatoriamente:
   - `TELEGRAM_BOT_TOKEN`: Tu token del bot
   - `OPENAI_API_KEY`: Tu API key de OpenAI
   - `REDIS_PASSWORD`: Una contraseña segura para Redis
   - `SECRET_KEY`: Una clave secreta (puedes generarla con `openssl rand -hex 32`)

4. **Subir archivos DOCX**:
   ```bash
   # Desde tu máquina local
   scp data/*.docx nutritionbot@TU_IP_DEL_SERVIDOR:~/nutrition-bot/data/
   ```

5. **Ejecutar el deployment**:
   ```bash
   ./deploy/deploy.sh
   ```

## 🔒 Paso 4: Configurar SSL (Opcional pero Recomendado)

Si tienes un dominio:

1. **Apuntar el dominio a la IP del servidor** en tu proveedor de DNS

2. **Obtener certificado SSL**:
   ```bash
   # Como root
   docker run -it --rm \
     -v /home/nutritionbot/nutrition-bot/certbot/conf:/etc/letsencrypt \
     -v /home/nutritionbot/nutrition-bot/certbot/www:/var/www/certbot \
     certbot/certbot certonly --webroot \
     --webroot-path /var/www/certbot \
     --email tu-email@ejemplo.com \
     --agree-tos \
     --no-eff-email \
     -d tudominio.com
   ```

3. **Reiniciar nginx**:
   ```bash
   cd /home/nutritionbot/nutrition-bot
   docker-compose -f docker-compose.prod.yml restart nginx
   ```

## 📊 Paso 5: Verificación y Monitoreo

1. **Verificar que todos los servicios estén corriendo**:
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

   Deberías ver:
   - nutrition_bot_api (Estado: Up)
   - nutrition_telegram_bot (Estado: Up)
   - nutrition_bot_redis (Estado: Up)
   - nutrition_bot_nginx (Estado: Up)

2. **Ver logs en tiempo real**:
   ```bash
   # Todos los servicios
   docker-compose -f docker-compose.prod.yml logs -f
   
   # Solo el bot
   docker-compose -f docker-compose.prod.yml logs -f telegram_bot
   ```

3. **Probar el bot**:
   - Abrir Telegram
   - Buscar tu bot por su username
   - Enviar `/start`
   - Debería responder con el menú principal

4. **Monitoreo continuo**:
   ```bash
   # Script de monitoreo
   ./monitor.sh
   ```

## 🛠️ Mantenimiento

### Actualizar el código:
```bash
cd /home/nutritionbot/nutrition-bot
git pull origin main
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### Backup manual:
```bash
./backup.sh
```

### Ver uso de recursos:
```bash
docker stats
```

### Reiniciar servicios:
```bash
docker-compose -f docker-compose.prod.yml restart
```

### Logs de errores:
```bash
# Ver últimos errores
docker-compose -f docker-compose.prod.yml logs --tail=100 | grep ERROR
```

## 🚨 Solución de Problemas

### El bot no responde:
1. Verificar token en `.env.prod`
2. Revisar logs: `docker-compose -f docker-compose.prod.yml logs telegram_bot`
3. Verificar que la API esté funcionando: `curl http://localhost:8000/health`

### Error de OpenAI:
1. Verificar API key en `.env.prod`
2. Verificar créditos en tu cuenta de OpenAI
3. Revisar logs de la API

### Problemas de memoria:
1. Verificar swap: `free -h`
2. Ver procesos: `docker stats`
3. Considerar aumentar el tamaño del Droplet

### ChromaDB no tiene recetas:
1. Verificar que los DOCX estén en `data/`
2. Recargar manualmente:
   ```bash
   docker-compose -f docker-compose.prod.yml exec api python data_processor/load_to_chromadb.py
   ```

## 📈 Escalamiento

Si necesitas manejar más usuarios:

1. **Vertical**: Aumentar el tamaño del Droplet
2. **Horizontal**: 
   - Separar la base de datos en otro servidor
   - Usar un balanceador de carga
   - Múltiples instancias del bot

## 🔐 Seguridad Adicional

1. **Configurar backup automático** en DigitalOcean
2. **Habilitar monitoring** en DigitalOcean
3. **Configurar alertas** para uso de recursos
4. **Revisar logs regularmente** por actividad sospechosa
5. **Mantener el sistema actualizado**:
   ```bash
   apt update && apt upgrade -y
   ```

## 💰 Costos Estimados

- **Droplet Basic 2GB**: $12/mes
- **Droplet Basic 4GB**: $24/mes (recomendado)
- **Backup automático**: 20% adicional
- **Bandwidth**: 1-3 TB incluidos (suficiente para miles de usuarios)

Total estimado: $15-30/mes para operación normal

## 📞 Soporte

Si encuentras problemas:
1. Revisar los logs detalladamente
2. Verificar la documentación de Docker Compose
3. Revisar issues en el repositorio
4. Contactar al equipo de desarrollo