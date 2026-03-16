# Deployment Guide - Voice Banking Authentication System

## Pre-Deployment Checklist

- [ ] All tests pass locally
- [ ] No hardcoded secrets in code
- [ ] Environment variables configured
- [ ] Database backups configured
- [ ] Logging enabled
- [ ] Error handling complete
- [ ] HTTPS certificate obtained
- [ ] Email service configured
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Security headers added

## Development to Production

### 1. Environment Setup

```bash
# Production .env
export SECRET_KEY=<generate-random-256-bit-key>
export SENDER_EMAIL=noreply@yourbank.com
export SENDER_PASSWORD=<app-specific-password>
export DEBUG=False
export HOST=0.0.0.0
export PORT=8000
```

### 2. Dependencies

```bash
# Use specific versions
pip install -r requirements.txt --no-deps
pip install -r requirements.txt

# Or freeze versions
pip freeze > requirements.lock.txt
```

### 3. Database

**SQLite** (suitable for small-scale):
```bash
# Already bundled with Python
sqlite3 database/database.db < init.sql
```

**PostgreSQL** (suitable for production):

```sql
-- Create database
CREATE DATABASE voice_auth;

-- Create user
CREATE USER voice_auth_user WITH PASSWORD 'strong-password';

-- Update connection string in .env
DATABASE_URL=postgresql://voice_auth_user:password@localhost/voice_auth
```

Update `database.py`:
```python
from sqlalchemy import create_engine
engine = create_engine(os.getenv('DATABASE_URL'))
```

### 4. Web Server Setup

#### Using Gunicorn (Recommended)

```bash
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

Configuration file (`gunicorn.conf.py`):
```python
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 30
keepalive = 2
```

Run:
```bash
gunicorn -c gunicorn.conf.py main:app
```

#### Using Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t voice-auth .
docker run -p 8000:8000 voice-auth
```

### 5. Reverse Proxy (Nginx)

```nginx
upstream voice_auth {
    server 127.0.0.1:8000;
}

server {
    listen 443 ssl http2;
    server_name auth.yourbank.com;

    ssl_certificate /etc/letsencrypt/live/auth.yourbank.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/auth.yourbank.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://voice_auth;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/frontend;
        expires 1h;
    }
}

server {
    listen 80;
    server_name auth.yourbank.com;
    return 301 https://$server_name$request_uri;
}
```

### 6. SSL/TLS Certificate

```bash
# Using Let's Encrypt
sudo apt-get install certbot python3-certbot-nginx

sudo certbot certonly --nginx -d auth.yourbank.com

# Auto-renewal
sudo certbot renew --dry-run
```

### 7. Systemd Service

Create `/etc/systemd/system/voice-auth.service`:

```ini
[Unit]
Description=Voice Banking Authentication Service
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/voice-auth
ExecStart=/opt/voice-auth/venv/bin/gunicorn -c gunicorn.conf.py main:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
KillSignal=SIGTERM
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable voice-auth.service
sudo systemctl start voice-auth.service
sudo systemctl status voice-auth.service
```

### 8. Monitoring & Logging

#### Logging Setup

```python
# In main.py
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)
handler = RotatingFileHandler('logs/app.log', maxBytes=10000000, backupCount=10)
logger.addHandler(handler)
```

Create log directory:
```bash
mkdir -p logs
chmod 755 logs
```

#### Health Monitoring

```bash
# Check service
curl https://auth.yourbank.com/health

# Setup monitoring with Prometheus
# pip install prometheus-client
```

#### Alerting

```python
# Email alerts on errors
import smtplib
from email.mime.text import MIMEText

def alert_on_error(error):
    msg = MIMEText(f"Error: {error}")
    # Send email to admin
```

### 9. Database Backups

**Automated daily backup** (crontab):

```bash
0 2 * * * /opt/voice-auth/backup.sh
```

Create `backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/opt/voice-auth/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# SQLite backup
cp /opt/voice-auth/database/database.db \
   $BACKUP_DIR/database_$DATE.db

# Or PostgreSQL backup
pg_dump voice_auth | gzip > $BACKUP_DIR/database_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "database_*.db" -mtime +30 -delete
```

### 10. Security Hardening

#### Update Security Headers

```python
# In main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourbank.com"],  # Only your domain
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# Add security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

#### Rate Limiting

```bash
pip install slowapi

# In main.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/register")
@limiter.limit("5/minute")
async def register(request: Request):
    pass
```

#### Input Validation

```python
from pydantic import BaseModel, EmailStr, validator

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 12:
            raise ValueError('Password must be 12+ characters')
        return v
```

### 11. Performance Tuning

#### Database Connection Pooling

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)
```

#### Caching

```bash
pip install redis

# In main.py
from redis import Redis

redis_client = Redis(host='localhost', port=6379, db=0)

@app.get("/user/{user_id}")
async def get_user(user_id: int):
    cached = redis_client.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)
    # Otherwise fetch from DB
```

#### Model Optimization

```python
# Load models on startup (not per request)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load models
    load_models()
    yield
    # Cleanup

app = FastAPI(lifespan=lifespan)
```

## Deployment Checklist

### Pre-Launch
- [ ] Test all endpoints in production environment
- [ ] Verify SSL/TLS certificate
- [ ] Test database backups
- [ ] Configure monitoring and alerts
- [ ] Setup logging and centralized log aggregation
- [ ] Load testing (1000+ concurrent users)
- [ ] Security penetration testing
- [ ] Disaster recovery plan documented

### Launch Day
- [ ] Maintenance window announced
- [ ] Full backup taken
- [ ] Deployment executed
- [ ] All services verified online
- [ ] Health checks passing
- [ ] Users notified of service availability
- [ ] Support team on standby

### Post-Launch
- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] Verify OTP email sending
- [ ] Test voice authentication
- [ ] Monitor database growth
- [ ] Analyze user feedback
- [ ] Plan optimization improvements

## Scaling Considerations

### Horizontal Scaling

```yaml
# Docker Compose for multiple instances
version: '3'
services:
  web:
    image: voice-auth
    deploy:
      replicas: 3
    ports:
      - "8000-8002:8000"
  
  db:
    image: postgres:15
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:
```

### Load Balancing

```nginx
upstream backend {
    server web1:8000;
    server web2:8000;
    server web3:8000;
    least_conn;  # Load balancing strategy
}
```

### Database Optimization

```sql
-- Index frequently queried columns
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_login_attempts_user_id ON login_attempts(user_id);
CREATE INDEX idx_otp_user_id ON otp(user_id);
```

## Troubleshooting Production

### Check Service Status
```bash
systemctl status voice-auth
journalctl -u voice-auth -n 100
```

### View Logs
```bash
tail -f logs/app.log
```

### Database Issues
```bash
# Check DB connection
sqlite3 database/database.db ".tables"

# Or PostgreSQL
psql -U voice_auth_user -d voice_auth -c "\dt"
```

### Performance Issues
```bash
# Check Python memory usage
ps aux | grep gunicorn

# Monitor system
top
# or
htop
```

### SSL Certificate Issues
```bash
# Check expiration
openssl x509 -in cert.pem -noout -dates

# Renew
certbot renew
```

## Rollback Plan

If deployment fails:

```bash
# Stop new version
systemctl stop voice-auth

# Restore from backup
cp backups/database_backup.db database/database.db

# Start old version
git checkout previous-version
systemctl start voice-auth

# Verify
curl https://auth.yourbank.com/health
```

## Cost Estimation

- **Server**: $10-50/month (small instance)
- **Database**: $0-20/month (PostgreSQL hosting)
- **SSL Certificate**: $0/month (Let's Encrypt)
- **Email Service**: $0-5/month (SMTP)
- **Monitoring**: $0-20/month
- **Backup Storage**: $0-10/month

**Total**: ~$10-145/month depending on scale

## References

- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Gunicorn Documentation](https://gunicorn.org/)
- [Nginx](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)

---

**Deployment Status**: Ready for production ✓
