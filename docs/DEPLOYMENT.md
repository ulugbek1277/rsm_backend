# EduMaster CRM - Production Deployment

Bu hujjat EduMaster CRM tizimini production muhitda deploy qilish bo'yicha qo'llanma.

## Server Talablari

### Minimum talablar:
- **CPU**: 2 core
- **RAM**: 4GB
- **Disk**: 50GB SSD
- **OS**: Ubuntu 20.04+ / CentOS 8+

### Tavsiya etilgan:
- **CPU**: 4+ core
- **RAM**: 8GB+
- **Disk**: 100GB+ SSD
- **OS**: Ubuntu 22.04 LTS

## 1. Server Tayyorlash

### System yangilash
\`\`\`bash
sudo apt update && sudo apt upgrade -y
\`\`\`

### Kerakli paketlar
\`\`\`bash
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib redis-server nginx supervisor git
\`\`\`

### PostgreSQL sozlash
\`\`\`bash
sudo -u postgres psql
CREATE DATABASE edumaster_crm;
CREATE USER edumaster WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE edumaster_crm TO edumaster;
\q
\`\`\`

### Redis sozlash
\`\`\`bash
sudo systemctl enable redis-server
sudo systemctl start redis-server
\`\`\`

## 2. Loyihani Deploy Qilish

### Loyihani klonlash
\`\`\`bash
cd /opt
sudo git clone <repository-url> edumaster-crm
sudo chown -R $USER:$USER /opt/edumaster-crm
cd /opt/edumaster-crm
\`\`\`

### Virtual muhit
\`\`\`bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
\`\`\`

### Environment sozlamalari
\`\`\`bash
cp .env.example .env
nano .env
\`\`\`

**.env fayli:**
\`\`\`bash
DEBUG=False
SECRET_KEY=your-very-secure-secret-key-here
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database
DATABASE_URL=postgresql://edumaster:secure_password@localhost/edumaster_crm

# Redis
REDIS_URL=redis://localhost:6379/0

# SMS
ESKIZ_EMAIL=your-email@example.com
ESKIZ_PASSWORD=your-sms-password

# Security
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')
\`\`\`

### Ma'lumotlar bazasini sozlash
\`\`\`bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
\`\`\`

## 3. Gunicorn Sozlash

### Gunicorn konfiguratsiyasi
\`\`\`bash
nano /opt/edumaster-crm/gunicorn.conf.py
\`\`\`

\`\`\`python
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
\`\`\`

### Systemd service
\`\`\`bash
sudo nano /etc/systemd/system/edumaster-crm.service
\`\`\`

\`\`\`ini
[Unit]
Description=EduMaster CRM Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/edumaster-crm
Environment="PATH=/opt/edumaster-crm/venv/bin"
ExecStart=/opt/edumaster-crm/venv/bin/gunicorn --config gunicorn.conf.py config.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
\`\`\`

\`\`\`bash
sudo systemctl daemon-reload
sudo systemctl enable edumaster-crm
sudo systemctl start edumaster-crm
\`\`\`

## 4. Celery Sozlash

### Celery worker service
\`\`\`bash
sudo nano /etc/systemd/system/edumaster-celery.service
\`\`\`

\`\`\`ini
[Unit]
Description=EduMaster CRM Celery Worker
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
EnvironmentFile=/opt/edumaster-crm/.env
WorkingDirectory=/opt/edumaster-crm
ExecStart=/opt/edumaster-crm/venv/bin/celery -A config worker -l info --detach
ExecStop=/opt/edumaster-crm/venv/bin/celery -A config control shutdown
ExecReload=/opt/edumaster-crm/venv/bin/celery -A config control reload
Restart=always

[Install]
WantedBy=multi-user.target
\`\`\`

### Celery beat service
\`\`\`bash
sudo nano /etc/systemd/system/edumaster-celery-beat.service
\`\`\`

\`\`\`ini
[Unit]
Description=EduMaster CRM Celery Beat
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
EnvironmentFile=/opt/edumaster-crm/.env
WorkingDirectory=/opt/edumaster-crm
ExecStart=/opt/edumaster-crm/venv/bin/celery -A config beat -l info
Restart=always

[Install]
WantedBy=multi-user.target
\`\`\`

\`\`\`bash
sudo systemctl daemon-reload
sudo systemctl enable edumaster-celery
sudo systemctl enable edumaster-celery-beat
sudo systemctl start edumaster-celery
sudo systemctl start edumaster-celery-beat
\`\`\`

## 5. Nginx Sozlash

\`\`\`bash
sudo nano /etc/nginx/sites-available/edumaster-crm
\`\`\`

\`\`\`nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/edumaster-crm/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /opt/edumaster-crm/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
}
\`\`\`

\`\`\`bash
sudo ln -s /etc/nginx/sites-available/edumaster-crm /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
\`\`\`

## 6. SSL Sertifikat (Let's Encrypt)

\`\`\`bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
\`\`\`

## 7. Monitoring va Logging

### Log fayllar
\`\`\`bash
# Application logs
tail -f /opt/edumaster-crm/logs/django.log

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# System logs
journalctl -u edumaster-crm -f
journalctl -u edumaster-celery -f
\`\`\`

### Monitoring script
\`\`\`bash
nano /opt/edumaster-crm/scripts/health_check.sh
\`\`\`

\`\`\`bash
#!/bin/bash
# Health check script

echo "=== EduMaster CRM Health Check ==="
echo "Date: $(date)"

# Check services
services=("edumaster-crm" "edumaster-celery" "edumaster-celery-beat" "postgresql" "redis-server" "nginx")

for service in "${services[@]}"; do
    if systemctl is-active --quiet $service; then
        echo "✅ $service: Running"
    else
        echo "❌ $service: Not running"
    fi
done

# Check disk space
echo ""
echo "=== Disk Usage ==="
df -h /

# Check memory
echo ""
echo "=== Memory Usage ==="
free -h

# Check database connection
echo ""
echo "=== Database Check ==="
cd /opt/edumaster-crm
source venv/bin/activate
python manage.py check --database default
\`\`\`

## 8. Backup va Restore

### Database backup
\`\`\`bash
nano /opt/edumaster-crm/scripts/backup_db.sh
\`\`\`

\`\`\`bash
#!/bin/bash
BACKUP_DIR="/opt/backups/edumaster-crm"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -U edumaster edumaster_crm > $BACKUP_DIR/db_backup_$DATE.sql

# Media files backup
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz /opt/edumaster-crm/media/

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
\`\`\`

### Crontab sozlash
\`\`\`bash
crontab -e
\`\`\`

\`\`\`bash
# Daily backup at 2 AM
0 2 * * * /opt/edumaster-crm/scripts/backup_db.sh

# Health check every 5 minutes
*/5 * * * * /opt/edumaster-crm/scripts/health_check.sh >> /var/log/edumaster-health.log
\`\`\`

## 9. Security

### Firewall
\`\`\`bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw status
\`\`\`

### Fail2ban
\`\`\`bash
sudo apt install fail2ban
sudo nano /etc/fail2ban/jail.local
\`\`\`

\`\`\`ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true

[nginx-http-auth]
enabled = true
\`\`\`

## 10. Yangilash

\`\`\`bash
cd /opt/edumaster-crm
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart edumaster-crm
sudo systemctl restart edumaster-celery
\`\`\`

## Troubleshooting

### Umumiy muammolar:

1. **Service ishlamayapti**:
\`\`\`bash
sudo systemctl status edumaster-crm
journalctl -u edumaster-crm -n 50
\`\`\`

2. **Database ulanish xatosi**:
\`\`\`bash
sudo -u postgres psql -c "SELECT version();"
\`\`\`

3. **Static fayllar yuklanmayapti**:
\`\`\`bash
python manage.py collectstatic --noinput
sudo chown -R www-data:www-data /opt/edumaster-crm/staticfiles/
\`\`\`

4. **Celery ishlamayapti**:
\`\`\`bash
redis-cli ping
sudo systemctl restart edumaster-celery
