#!/bin/bash

# Script de configuración automática para DigitalOcean Droplet
# Compatible con Ubuntu 22.04 LTS

set -e  # Exit on error

echo "🚀 Iniciando configuración del servidor para Nutrition Bot..."

# Variables de configuración
DOMAIN=${DOMAIN:-""}  # Dominio opcional para SSL
USER="nutritionbot"
APP_DIR="/home/$USER/nutrition-bot"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_message() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 1. Actualizar sistema
print_message "Actualizando sistema..."
apt-get update
apt-get upgrade -y

# 2. Instalar dependencias básicas
print_message "Instalando dependencias básicas..."
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    ufw \
    fail2ban \
    htop \
    tmux

# 3. Instalar Docker
print_message "Instalando Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io
fi

# 4. Instalar Docker Compose
print_message "Instalando Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
fi

# 5. Crear usuario para la aplicación
print_message "Creando usuario de aplicación..."
if ! id "$USER" &>/dev/null; then
    useradd -m -s /bin/bash $USER
    usermod -aG docker $USER
fi

# 6. Configurar firewall
print_message "Configurando firewall..."
ufw --force disable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# 7. Configurar fail2ban
print_message "Configurando fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

# 8. Configurar swap (importante para servidores con poca RAM)
print_message "Configurando swap..."
if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
fi

# 9. Optimizaciones del kernel
print_message "Aplicando optimizaciones del kernel..."
cat > /etc/sysctl.d/99-nutrition-bot.conf << EOF
# Optimizaciones de red
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq

# Optimizaciones de memoria
vm.swappiness = 10
vm.vfs_cache_pressure = 50
EOF
sysctl -p /etc/sysctl.d/99-nutrition-bot.conf

# 10. Crear estructura de directorios
print_message "Creando estructura de directorios..."
sudo -u $USER mkdir -p $APP_DIR
sudo -u $USER mkdir -p $APP_DIR/nginx/sites-enabled
sudo -u $USER mkdir -p $APP_DIR/certbot/conf
sudo -u $USER mkdir -p $APP_DIR/certbot/www
sudo -u $USER mkdir -p $APP_DIR/backups

# 11. Configurar logrotate
print_message "Configurando rotación de logs..."
cat > /etc/logrotate.d/nutrition-bot << EOF
$APP_DIR/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 $USER $USER
    sharedscripts
    postrotate
        docker-compose -f $APP_DIR/docker-compose.prod.yml kill -s USR1 nginx
    endscript
}
EOF

# 12. Crear script de backup
print_message "Creando script de backup..."
cat > $APP_DIR/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/nutritionbot/nutrition-bot/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup de ChromaDB
docker run --rm -v nutrition-bot_chroma_data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/chromadb_$DATE.tar.gz -C /data .

# Limpiar backups antiguos (mantener últimos 7 días)
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF
chmod +x $APP_DIR/backup.sh
chown $USER:$USER $APP_DIR/backup.sh

# 13. Configurar cron para backups
print_message "Configurando cron para backups..."
echo "0 3 * * * $USER $APP_DIR/backup.sh" > /etc/cron.d/nutrition-bot-backup

# 14. Crear archivo de configuración de nginx
print_message "Creando configuración de nginx..."
if [ -n "$DOMAIN" ]; then
    cat > $APP_DIR/nginx/sites-enabled/nutrition-bot.conf << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name $DOMAIN;
    
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    location / {
        proxy_pass http://api:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
else
    cat > $APP_DIR/nginx/sites-enabled/nutrition-bot.conf << EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://api:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
fi

# 15. Script de monitoreo
print_message "Creando script de monitoreo..."
cat > $APP_DIR/monitor.sh << 'EOF'
#!/bin/bash
# Script de monitoreo básico

check_service() {
    if docker ps | grep -q $1; then
        echo "✅ $1 está funcionando"
    else
        echo "❌ $1 está detenido"
        # Intentar reiniciar
        cd /home/nutritionbot/nutrition-bot
        docker-compose -f docker-compose.prod.yml up -d $1
    fi
}

echo "=== Estado de servicios ==="
check_service "nutrition_bot_api"
check_service "nutrition_telegram_bot"
check_service "nutrition_bot_redis"
check_service "nutrition_bot_nginx"

echo -e "\n=== Uso de recursos ==="
docker stats --no-stream
EOF
chmod +x $APP_DIR/monitor.sh
chown $USER:$USER $APP_DIR/monitor.sh

# 16. Crear systemd service para auto-start
print_message "Configurando auto-start con systemd..."
cat > /etc/systemd/system/nutrition-bot.service << EOF
[Unit]
Description=Nutrition Bot Docker Compose Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=$USER
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable nutrition-bot

print_message "✅ Configuración del servidor completada!"
print_message ""
print_message "📋 Próximos pasos:"
print_message "1. Clonar el repositorio en $APP_DIR"
print_message "2. Crear archivo .env.prod con las variables de entorno"
print_message "3. Ejecutar: docker-compose -f docker-compose.prod.yml up -d"
print_message "4. Si tienes dominio, ejecutar certbot para SSL"
print_message ""
print_message "📊 Comandos útiles:"
print_message "- Monitorear servicios: $APP_DIR/monitor.sh"
print_message "- Ver logs: docker-compose -f docker-compose.prod.yml logs -f"
print_message "- Backup manual: $APP_DIR/backup.sh"