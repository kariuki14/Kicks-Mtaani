# 🐳 Docker Deployment Guide for Kicks Mtaani

This guide explains how to deploy the Kicks Mtaani e-commerce application using Docker and Docker Compose.

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- OpenSSL (for generating secure keys)

## Quick Start

### 1. Generate Secure Keys

Before running the containers, generate secure secret keys:

```bash
# Generate JWT_SECRET_KEY (64 characters)
JWT_SECRET=$(openssl rand -hex 32)

# Generate ADMIN_API_KEY (64 characters)
ADMIN_API_KEY=$(openssl rand -hex 32)

echo "JWT_SECRET_KEY=$JWT_SECRET"
echo "ADMIN_API_KEY=$ADMIN_API_KEY"
```

### 2. Configure Environment Variables

Copy the example environment file and update it with your generated keys:

```bash
cp .env.docker .env
```

Edit `.env` and replace the placeholder values:

```env
DB_USER=kicks_user
DB_PASSWORD=your_secure_database_password
DB_NAME=kicks_mtaani
JWT_SECRET_KEY=<paste_generated_jwt_secret>
ADMIN_API_KEY=<paste_generated_admin_key>
ALLOWED_ORIGINS=http://localhost,http://yourdomain.com
ENVIRONMENT=production
```

### 3. Build and Run

Build and start all services:

```bash
docker-compose up --build -d
```

The `-d` flag runs containers in detached mode (background).

### 4. Verify Deployment

Check if all services are running:

```bash
docker-compose ps
```

View logs:

```bash
docker-compose logs -f
```

## Services

| Service     | Port | Description                          |
|-------------|------|--------------------------------------|
| frontend    | 80   | Nginx serving static files + reverse proxy |
| backend     | 8000 | FastAPI application (internal only)  |
| db          | 5432 | PostgreSQL database (internal only)  |

## Accessing the Application

- **Frontend**: http://localhost
- **Backend API**: http://localhost/api/health
- **Admin Panel**: http://localhost/admin.html

## Common Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Stop Services

```bash
# Stop without removing volumes
docker-compose down

# Stop and remove volumes (DELETES DATA!)
docker-compose down -v
```

### Rebuild After Changes

```bash
docker-compose up --build -d
```

### Database Management

```bash
# Access PostgreSQL shell
docker-compose exec db psql -U kicks_user -d kicks_mtaani

# Backup database
docker-compose exec db pg_dump -U kicks_user kicks_mtaani > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T db psql -U kicks_user -d kicks_mtaani
```

## Health Checks

All services include health checks:

- **Frontend**: `GET http://localhost/health`
- **Backend**: `GET http://localhost/api/health`
- **Database**: Automatic PostgreSQL readiness check

Check health status:

```bash
docker inspect --format='{{.State.Health.Status}}' kicks-mtaani-frontend
docker inspect --format='{{.State.Health.Status}}' kicks-mtaani-backend
docker inspect --format='{{.State.Health.Status}}' kicks-mtaani-db
```

## Security Considerations

1. **Never commit `.env`** - Contains sensitive credentials
2. **Generate unique keys** - Use `openssl rand -hex 32` for production
3. **Update ALLOWED_ORIGINS** - Set to your actual domain in production
4. **Use strong passwords** - For database and admin access
5. **Enable SSL/TLS** - Use a reverse proxy like Traefik or Nginx Proxy Manager for HTTPS

## Production Deployment

For production deployment:

1. **Set up HTTPS** using a reverse proxy or load balancer
2. **Configure domain names** in ALLOWED_ORIGINS
3. **Use external database** instead of containerized PostgreSQL for critical data
4. **Set up monitoring** for container health and resource usage
5. **Configure backups** for the PostgreSQL volume
6. **Use secrets management** (Docker Swarm secrets, Kubernetes secrets, or HashiCorp Vault)

Example production nginx reverse proxy for HTTPS:

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Troubleshooting

### Backend won't start

Check if database is ready:
```bash
docker-compose logs db
```

Ensure environment variables are set correctly:
```bash
docker-compose exec backend env | grep JWT
```

### Frontend can't connect to backend

Verify network connectivity:
```bash
docker-compose exec frontend wget -qO- http://backend:8000/api/health
```

Check nginx configuration:
```bash
docker-compose exec frontend nginx -t
```

### Database connection issues

Test database connection:
```bash
docker-compose exec db pg_isready -U kicks_user -d kicks_mtaani
```

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Client    │────▶│   Frontend   │────▶│   Backend   │
│  (Browser)  │     │   (Nginx)    │     │  (FastAPI)  │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                │
                                                ▼
                                         ┌─────────────┐
                                         │  Database   │
                                         │ (PostgreSQL)│
                                         └─────────────┘
```

## File Structure

```
/workspace
├── docker-compose.yml      # Main Docker Compose configuration
├── .env.docker            # Example environment variables
├── backend/
│   ├── Dockerfile         # Backend container definition
│   ├── .dockerignore      # Files to exclude from backend build
│   ├── app/               # Application code
│   └── requirements.txt   # Python dependencies
└── docs/
    ├── Dockerfile         # Frontend container definition
    ├── .dockerignore      # Files to exclude from frontend build
    ├── nginx.conf         # Nginx configuration
    ├── index.html         # Main HTML file
    ├── style.css          # Stylesheet
    ├── admin.html         # Admin panel
    └── images/            # Static images
```

## Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- Review health checks
- Verify environment variables
- Ensure ports 80 and 5432 are available
