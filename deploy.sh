#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="docker-compose.prod.yml"
DOMAIN="sunstein.cloud"
EMAIL="weissvanderpol.ivan@gmail.com"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log()  { echo -e "${GREEN}[deploy]${NC} $1"; }
warn() { echo -e "${YELLOW}[warn]${NC} $1"; }
err()  { echo -e "${RED}[error]${NC} $1" >&2; }

check_env() {
    [ ! -f .env ] && err ".env not found. cp .env.production.example .env && nano .env" && exit 1
    source .env
    for var in POSTGRES_PASSWORD SECRET_KEY; do
        [ -z "${!var:-}" ] && err "$var not set in .env" && exit 1
    done
    log "Environment validated."
}

case "${1:-help}" in
    init)
        check_env
        mkdir -p nginx/conf.d
        docker compose -f "$COMPOSE_FILE" build
        docker compose -f "$COMPOSE_FILE" up -d
        log "Started. Run './deploy.sh ssl' for HTTPS."
        ;;
    ssl)
        docker compose -f "$COMPOSE_FILE" up -d nginx
        docker compose -f "$COMPOSE_FILE" run --rm certbot certonly \
            --webroot -w /var/www/certbot \
            -d "$DOMAIN" -d "www.$DOMAIN" \
            --email "$EMAIL" --agree-tos --no-eff-email
        docker compose -f "$COMPOSE_FILE" exec nginx nginx -s reload
        log "SSL done! https://${DOMAIN}/petShelter"
        ;;
    update)
        check_env
        [ -d .git ] && git pull origin develop
        docker compose -f "$COMPOSE_FILE" build
        docker compose -f "$COMPOSE_FILE" up -d --remove-orphans
        log "Updated: https://${DOMAIN}/petShelter"
        ;;
    status)
        docker compose -f "$COMPOSE_FILE" ps
        echo -n "API: "; curl -sf http://localhost:8000/health && echo || echo "DOWN"
        echo -n "Frontend: "; curl -sf -o /dev/null -w "%{http_code}\n" http://localhost:3000 || echo "DOWN"
        ;;
    logs)   docker compose -f "$COMPOSE_FILE" logs -f "${2:-}" ;;
    down)   docker compose -f "$COMPOSE_FILE" down; log "Stopped." ;;
    backup)
        dir="backups/$(date +%Y%m%d_%H%M%S)"; mkdir -p "$dir"
        docker compose -f "$COMPOSE_FILE" exec -T db pg_dump -U refugio_user refugio_prod | gzip > "$dir/db.sql.gz"
        log "Backup: $dir/db.sql.gz"
        ;;
    *) echo "Usage: ./deploy.sh {init|ssl|update|status|logs|down|backup}" ;;
esac
