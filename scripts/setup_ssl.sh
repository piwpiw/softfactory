#!/bin/bash
# =============================================================
# SoftFactory — Let's Encrypt SSL Setup Script
# Usage: ./scripts/setup_ssl.sh <domain> <email>
# Example: ./scripts/setup_ssl.sh softfactory.kr admin@softfactory.kr
# =============================================================

set -e  # Exit on any error

DOMAIN="${1}"
EMAIL="${2}"

# ---- Input validation ----
if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo "Usage: $0 <domain> <email>"
    echo "Example: $0 softfactory.kr admin@softfactory.kr"
    exit 1
fi

# Validate domain format (basic check)
if ! echo "$DOMAIN" | grep -qE '^[a-zA-Z0-9][a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}$'; then
    echo "ERROR: Invalid domain format: $DOMAIN"
    exit 1
fi

# Validate email format (basic check)
if ! echo "$EMAIL" | grep -qE '^[^@]+@[^@]+\.[^@]+$'; then
    echo "ERROR: Invalid email format: $EMAIL"
    exit 1
fi

echo "===================================================="
echo " SoftFactory SSL Setup"
echo " Domain: $DOMAIN (and www.$DOMAIN)"
echo " Email:  $EMAIL"
echo "===================================================="

# ---- Step 1: Check root privileges ----
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root (sudo)."
    exit 1
fi

# ---- Step 2: Install certbot and nginx plugin ----
echo ""
echo "[1/5] Installing certbot..."
if command -v apt-get &>/dev/null; then
    apt-get update -qq
    apt-get install -y certbot python3-certbot-nginx
elif command -v yum &>/dev/null; then
    yum install -y certbot python3-certbot-nginx
elif command -v dnf &>/dev/null; then
    dnf install -y certbot python3-certbot-nginx
else
    echo "ERROR: Unsupported package manager. Install certbot manually."
    exit 1
fi
echo "Certbot installed."

# ---- Step 3: Create certbot webroot directory ----
echo ""
echo "[2/5] Creating ACME challenge directory..."
mkdir -p /var/www/certbot
echo "Directory created: /var/www/certbot"

# ---- Step 4: Obtain SSL certificate ----
echo ""
echo "[3/5] Obtaining SSL certificate from Let's Encrypt..."
certbot --nginx \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    --redirect \
    --hsts \
    --staple-ocsp

echo "Certificate obtained successfully."

# ---- Step 5: Verify certificate ----
echo ""
echo "[4/5] Verifying certificate..."
if certbot certificates | grep -q "$DOMAIN"; then
    echo "Certificate verified for $DOMAIN"
    certbot certificates | grep -A 5 "$DOMAIN"
else
    echo "WARNING: Could not verify certificate. Check certbot output above."
fi

# ---- Step 6: Set up auto-renewal cron job ----
echo ""
echo "[5/5] Setting up automatic certificate renewal..."

# Check if cron job already exists
CRON_JOB="0 3 * * * /usr/bin/certbot renew --quiet --post-hook 'systemctl reload nginx'"
if crontab -l 2>/dev/null | grep -q "certbot renew"; then
    echo "Auto-renewal cron job already exists. Skipping."
else
    # Add cron job (runs daily at 3 AM)
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "Auto-renewal cron job added: runs daily at 3 AM."
fi

# Also enable systemd timer if available (preferred on modern systems)
if systemctl is-active --quiet certbot.timer 2>/dev/null; then
    echo "systemd certbot.timer already active."
elif systemctl list-unit-files certbot.timer &>/dev/null; then
    systemctl enable --now certbot.timer
    echo "systemd certbot.timer enabled."
fi

# ---- Done ----
echo ""
echo "===================================================="
echo " SSL setup complete!"
echo ""
echo " Certificate files:"
echo "   Cert:    /etc/letsencrypt/live/$DOMAIN/fullchain.pem"
echo "   Key:     /etc/letsencrypt/live/$DOMAIN/privkey.pem"
echo "   Chain:   /etc/letsencrypt/live/$DOMAIN/chain.pem"
echo ""
echo " Next steps:"
echo "   1. Update nginx.production.conf with domain: $DOMAIN"
echo "   2. Copy nginx.production.conf to /etc/nginx/conf.d/"
echo "   3. Test nginx config: nginx -t"
echo "   4. Reload nginx: systemctl reload nginx"
echo "   5. Test HTTPS: curl -I https://$DOMAIN"
echo ""
echo " Auto-renewal: cron job set (daily 3 AM)"
echo " Test renewal:  certbot renew --dry-run"
echo "===================================================="
