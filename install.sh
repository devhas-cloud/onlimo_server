#!/bin/bash
# ============================================================================
# Onlimo DLH Server - Installation Script
# ============================================================================
# This script automates the deployment of Onlimo DLH Server including:
#   - System dependencies installation
#   - Python virtual environment setup
#   - Database creation (optional)
#   - FTP directory setup
#   - Systemd service configuration
#   - Logrotate configuration
#   - Sudoers configuration for FTP scripts
#
# Usage:
#   sudo bash install.sh [OPTIONS]
#
# Options:
#   --skip-db         Skip database creation
#     --skip-service     Skip systemd service setup
#   --skip-sudoers     Skip sudoers configuration
#   --non-interactive  Run without prompts (use defaults)
#   -h, --help         Show this help message
#
# See README.md for detailed documentation.
# ============================================================================

set -e

# ============================================================================
# Configuration
# ============================================================================

APP_DIR="/var/www/html/onlimo_server"
APP_USER="root"
APP_GROUP="root"
APP_PORT=9000
VENV_DIR="${APP_DIR}/venv"
LOG_DIR="/var/log/onlimo"
LOG_FILE="${LOG_DIR}/onlimo.log"
APP_LOG_FILE="${APP_DIR}/onlimo.log"
FTP_ROOT="/home/onlimo"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script flags
SKIP_DB=false
SKIP_SERVICE=false
SKIP_SUDOERS=false
NON_INTERACTIVE=false

# ============================================================================
# Helper Functions
# ============================================================================

print_banner() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}   Onlimo DLH Server - Installer${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

ask_continue() {
    local prompt="$1"
    local default="${2:-Y}"

    if [ "$NON_INTERACTIVE" = true ]; then
        return 0
    fi

    if [ "$default" = "Y" ]; then
        echo -e "${YELLOW}${prompt} ${NC}[Y/n] "
    else
        echo -e "${YELLOW}${prompt} ${NC}[y/N] "
    fi

    read -r answer
    answer=${answer:-$default}

    case "$answer" in
        [Yy]*) return 0 ;;
        *) return 1 ;;
    esac
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "Script ini harus dijalankan sebagai root."
        echo "Gunakan: sudo bash install.sh"
        exit 1
    fi
}

check_os() {
    if [ ! -f /etc/os-release ]; then
        print_warn "Tidak dapat mendeteksi OS. Mengasumsikan Debian/Ubuntu."
        PKG_MANAGER="apt"
    else
        . /etc/os-release
        case "$ID" in
            debian|ubuntu|linuxmint)
                PKG_MANAGER="apt"
                ;;
            centos|rhel|fedora|rocky|almalinux)
                PKG_MANAGER="yum"
                ;;
            *)
                print_warn "OS $ID tidak dikenali. Menggunakan apt."
                PKG_MANAGER="apt"
                ;;
        esac
    fi
    print_info "Package manager: $PKG_MANAGER"
}

# ============================================================================
# Step Functions
# ============================================================================

step_check_app_dir() {
    print_step "Memeriksa direktori aplikasi..."

    if [ ! -d "$APP_DIR" ]; then
        print_error "Direktori aplikasi tidak ditemukan: $APP_DIR"
        print_error "Pastikan kode aplikasi sudah berada di $APP_DIR"
        exit 1
    fi

    if [ ! -f "${APP_DIR}/app.py" ]; then
        print_error "File app.py tidak ditemukan di $APP_DIR"
        print_error "Pastikan kode aplikasi sudah terdeploy dengan benar."
        exit 1
    fi

    print_success "Direktori aplikasi ditemukan: $APP_DIR"
}

step_install_dependencies() {
    print_step "Menginstall dependencies sistem..."

    if [ "$PKG_MANAGER" = "apt" ]; then
        apt-get update -qq
        apt-get install -y -qq python3 python3-venv python3-pip mysql-client grep curl > /dev/null 2>&1
    elif [ "$PKG_MANAGER" = "yum" ]; then
        yum install -y python3 python3-pip mysql grep curl > /dev/null 2>&1
    fi

    print_success "Dependencies sistem terinstall."
}

step_setup_venv() {
    print_step "Membuat virtual environment..."

    if [ -d "${VENV_DIR}" ]; then
        print_warn "Virtual environment sudah ada. Mereinstall dependencies..."
        rm -rf "${VENV_DIR}"
    fi

    python3 -m venv "${VENV_DIR}"
    print_success "Virtual environment dibuat: ${VENV_DIR}"

    print_step "Menginstall Python dependencies..."
    "${VENV_DIR}/bin/pip" install --upgrade pip > /dev/null 2>&1
    "${VENV_DIR}/bin/pip" install -r "${APP_DIR}/requirements.txt" 2>&1 | tail -5

    print_success "Python dependencies terinstall."
}

step_setup_env() {
    print_step "Mengkonfigurasi environment..."

    ENV_FILE="${APP_DIR}/env"

    if [ -f "${APP_DIR}/.env" ]; then
        print_success "File .env sudah ada."

        if ask_continue "Apakah ingin mengupdate .env?"; then
            echo ""
            echo -e "${YELLOW}Konfigurasi Database MySQL:${NC}"

            if [ "$NON_INTERACTIVE" = false ]; then
                read -p "DB Host [localhost]: " db_host
                db_host=${db_host:-localhost}

                read -p "DB Port [3306]: " db_port
                db_port=${db_port:-3306}

                read -p "DB User [onlimo]: " db_user
                db_user=${db_user:-onlimo}

                read -sp "DB Password: " db_password
                echo ""

                read -p "DB Name [onlimo]: " db_name
                db_name=${db_name:-onlimo}

                read -p "Admin Username [admin]: " admin_user
                admin_user=${admin_user:-admin}

                read -sp "Admin Password: " admin_password
                echo ""
            else
                db_host="localhost"
                db_port="3306"
                db_user="onlimo"
                db_password="onlimo"
                db_name="onlimo"
                admin_user="admin"
                admin_password="admin123"
            fi

            # Generate random secret key
            secret_key=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "change-this-to-a-secure-random-string")

            cat > "${APP_DIR}/.env" << ENVEOF
# Flask
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=${secret_key}

# MySQL Database
DB_HOST=${db_host}
DB_PORT=${db_port}
DB_USER=${db_user}
DB_PASSWORD=${db_password}
DB_NAME=${db_name}

# Admin Credentials
ADMIN_USERNAME=${admin_user}
ADMIN_PASSWORD=${admin_password}

# FTP Root Path
FTP_ROOT=${FTP_ROOT}

# Application
APP_HOST=0.0.0.0
APP_PORT=${APP_PORT}
ENVEOF

            chmod 600 "${APP_DIR}/.env"
            print_success "File .env diperbarui."
        fi
    else
        print_warn "File .env tidak ditemukan. Membuat dari template..."

        echo ""
        echo -e "${YELLOW}Konfigurasi Database MySQL:${NC}"

        if [ "$NON_INTERACTIVE" = false ]; then
            read -p "DB Host [localhost]: " db_host
            db_host=${db_host:-localhost}

            read -p "DB Port [3306]: " db_port
            db_port=${db_port:-3306}

            read -p "DB User [onlimo]: " db_user
            db_user=${db_user:-onlimo}

            read -sp "DB Password: " db_password
            echo ""

            read -p "DB Name [onlimo]: " db_name
            db_name=${db_name:-onlimo}

            read -p "Admin Username [admin]: " admin_user
            admin_user=${admin_user:-admin}

            read -sp "Admin Password: " admin_password
            echo ""
        else
            db_host="localhost"
            db_port="3306"
            db_user="onlimo"
            db_password="onlimo"
            db_name="onlimo"
            admin_user="admin"
            admin_password="admin123"
        fi

        # Generate random secret key
        secret_key=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "change-this-to-a-secure-random-string")

        cat > "${APP_DIR}/.env" << ENVEOF
# Flask
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=${secret_key}

# MySQL Database
DB_HOST=${db_host}
DB_PORT=${db_port}
DB_USER=${db_user}
DB_PASSWORD=${db_password}
DB_NAME=${db_name}

# Admin Credentials
ADMIN_USERNAME=${admin_user}
ADMIN_PASSWORD=${admin_password}

# FTP Root Path
FTP_ROOT=${FTP_ROOT}

# Application
APP_HOST=0.0.0.0
APP_PORT=${APP_PORT}
ENVEOF

        chmod 600 "${APP_DIR}/.env"
        print_success "File .env dibuat."
    fi
}

step_setup_database() {
    if [ "$SKIP_DB" = true ]; then
        print_info "Pembuatan database dilewati (--skip-db)."
        return 0
    fi

    print_step "Setup database MySQL..."

    if [ "$NON_INTERACTIVE" = true ]; then
        print_info "Mode non-interactive: skip pembuatan database."
        print_info "Pastikan database sudah dibuat manual."
        return 0
    fi

    if ! command -v mysql &> /dev/null; then
        print_warn "mysql client tidak ditemukan. Skip pembuatan database."
        return 0
    fi

    # Read .env for database config
    if [ -f "${APP_DIR}/.env" ]; then
        source <(grep -E '^(DB_|ADMIN_)' "${APP_DIR}/.env" | sed 's/^/export /')
    fi

    echo ""
    echo -e "${YELLOW}Pembuatan Database MySQL${NC}"
    echo -e "${YELLOW}=========================${NC}"
    echo ""
    echo "Script ini akan membuat database dan user MySQL."
    echo "MySQL root password diperlukan untuk proses ini."
    echo ""

    if ask_continue "Buat database dan user MySQL?" "Y"; then
        read -sp "MySQL root password: " mysql_root_pass
        echo ""

        # Create database and user
        mysql -u root -p"${mysql_root_pass}" << SQLEOF 2>/dev/null || {
            print_error "Gagal koneksi ke MySQL. Pastikan password benar."
            print_info "Anda bisa membuat database manual dengan:"
            echo ""
            echo "  mysql -u root -p"
            echo "  CREATE DATABASE ${DB_NAME:-onlimo} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            echo "  CREATE USER '${DB_USER:-onlimo}'@'localhost' IDENTIFIED BY '${DB_PASSWORD:-onlimo}';"
            echo "  GRANT ALL PRIVILEGES ON ${DB_NAME:-onlimo}.* TO '${DB_USER:-onlimo}'@'localhost';"
            echo "  FLUSH PRIVILEGES;"
            echo ""
            return 1
        }
CREATE DATABASE IF NOT EXISTS ${DB_NAME:-onlimo} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER:-onlimo}'@'localhost' IDENTIFIED BY '${DB_PASSWORD:-onlimo}';
GRANT ALL PRIVILEGES ON ${DB_NAME:-onlimo}.* TO '${DB_USER:-onlimo}'@'localhost';
FLUSH PRIVILEGES;
SQLEOF

        print_success "Database dan user MySQL berhasil dibuat/diperbarui."
    else
        print_info "Pembuatan database dilewati."
        print_info "Pastikan database sudah dibuat manual sebelum menjalankan aplikasi."
    fi
}

step_setup_ftp_dir() {
    print_step "Membuat direktori FTP..."

    mkdir -p "${FTP_ROOT}"
    chmod 755 "${FTP_ROOT}"

    print_success "Direktori FTP: ${FTP_ROOT}"
}

step_setup_permissions() {
    print_step "Mengatur permissions..."

    # Set executable for FTP scripts
    if [ -f "${APP_DIR}/addftp.sh" ]; then
        chmod +x "${APP_DIR}/addftp.sh"
        print_success "addftp.sh: executable"
    else
        print_warn "addftp.sh tidak ditemukan"
    fi

    if [ -f "${APP_DIR}/delftp.sh" ]; then
        chmod +x "${APP_DIR}/delftp.sh"
        print_success "delftp.sh: executable"
    else
        print_warn "delftp.sh tidak ditemukan"
    fi
}

step_setup_sudoers() {
    if [ "$SKIP_SUDOERS" = true ]; then
        print_info "Sudoers configuration dilewati (--skip-sudoers)."
        return 0
    fi

    print_step "Mengkonfigurasi sudoers untuk FTP scripts..."

    SUDOERS_FILE="/etc/sudoers.d/onlimo_ftp"

    cat > "${SUDOERS_FILE}" << SUDOEOF
# Onlimo DLH - FTP user management scripts
# Allow the application user to execute FTP scripts without password
${APP_USER} ALL=(root) NOPASSWD: ${APP_DIR}/addftp.sh, ${APP_DIR}/delftp.sh
SUDOEOF

    chmod 440 "${SUDOERS_FILE}"

    # Validate sudoers file
    if visudo -c -f "${SUDOERS_FILE}" > /dev/null 2>&1; then
        print_success "Sudoers file valid: ${SUDOERS_FILE}"
    else
        print_error "Sudoers file tidak valid! Memeriksa manual..."
        visudo -c -f "${SUDOERS_FILE}"
    fi
}

step_setup_log_dir() {
    print_step "Membuat direktori log..."

    mkdir -p "${LOG_DIR}"

    if [ -f "${LOG_FILE}" ]; then
        print_info "File log sudah ada: ${LOG_FILE}"
    else
        touch "${LOG_FILE}"
    fi

    # Set ownership based on APP_USER
    if [ "${APP_USER}" = "root" ]; then
        chown root:root "${LOG_DIR}" "${LOG_FILE}"
        chmod 755 "${LOG_DIR}"
        chmod 644 "${LOG_FILE}"
    else
        chown "${APP_USER}:${APP_GROUP}" "${LOG_DIR}" "${LOG_FILE}"
        chmod 755 "${LOG_DIR}"
        chmod 644 "${LOG_FILE}"
    fi

    print_success "Direktori log: ${LOG_DIR}"
}

step_setup_systemd() {
    if [ "$SKIP_SERVICE" = true ]; then
        print_info "Systemd service setup dilewati (--skip-service)."
        return 0
    fi

    print_step "Mengkonfigurasi systemd service..."

    SERVICE_FILE="${APP_DIR}/onlimo.service"

    if [ ! -f "${SERVICE_FILE}" ]; then
        print_warn "onlimo.service tidak ditemukan di ${APP_DIR}. Membuat default..."

        cat > "${SERVICE_FILE}" << SVCEOF
[Unit]
Description=Onlimo DLH Application
After=network.target
Wants=mysql.service
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=simple
User=${APP_USER}
Group=${APP_GROUP}
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
Environment=PYTHONUNBUFFERED=1

ExecStart=${VENV_DIR}/bin/gunicorn \\
    --workers 1 \\
    --bind 0.0.0.0:${APP_PORT} \\
    --timeout 120 \\
    run:app

Restart=on-failure
RestartSec=5
TimeoutStopSec=20
KillMode=control-group

StandardOutput=append:${LOG_FILE}
StandardError=append:${LOG_FILE}

[Install]
WantedBy=multi-user.target
SVCEOF

        print_success "onlimo.service dibuat di ${SERVICE_FILE}"
    fi

    # Copy to systemd directory
    cp "${SERVICE_FILE}" /etc/systemd/system/onlimo.service
    print_success "Service file copied to /etc/systemd/system/onlimo.service"

    # Reload systemd
    systemctl daemon-reload
    print_success "Systemd daemon reloaded."

    # Enable service
    systemctl enable onlimo.service
    print_success "Service enabled: onlimo.service"
}

step_setup_logrotate() {
    print_step "Mengkonfigurasi logrotate..."

    # Application log rotate
    cat > /etc/logrotate.d/onlimo << LOGEOF
${LOG_FILE} {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 ${APP_USER} ${APP_GROUP}
    dateext
    dateformat -%Y%m%d
    sharedscripts
    postrotate
        systemctl reload onlimo.service > /dev/null 2>&1 || true
    endscript
}

${APP_LOG_FILE} {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 ${APP_USER} ${APP_GROUP}
    dateext
    dateformat -%Y%m%d
}
LOGEOF

    chmod 644 /etc/logrotate.d/onlimo
    print_success "Logrotate configured: /etc/logrotate.d/onlimo"
}

step_start_service() {
    if [ "$SKIP_SERVICE" = true ]; then
        print_info "Service start dilewati (--skip-service)."
        return 0
    fi

    print_step "Memulai service..."

    systemctl start onlimo.service
    sleep 3

    if systemctl is-active --quiet onlimo.service; then
        print_success "Service onlimo berjalan (active)."
    else
        print_error "Service onlimo gagal start!"
        echo ""
        echo "Lihat detail error:"
        echo "  systemctl status onlimo.service"
        echo "  journalctl -u onlimo -n 50 --no-pager"
        echo "  tail -f ${LOG_FILE}"
        echo ""
        echo "Periksa konfigurasi .env dan pastikan MySQL sudah berjalan."
        return 1
    fi
}

print_summary() {
    echo ""
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}           Onlimo DLH Server - Instalasi Selesai!${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo ""
    echo -e "  Aplikasi    : ${APP_DIR}"
    echo -e "  Virtual Env : ${VENV_DIR}"
    echo -e "  Config      : ${APP_DIR}/.env"
    echo -e "  Log Dir     : ${LOG_DIR}"
    echo -e "  Log File    : ${LOG_FILE}"
    echo -e "  App Log     : ${APP_LOG_FILE}"
    echo -e "  FTP Root    : ${FTP_ROOT}"
    echo -e "  Port        : ${APP_PORT}"
    echo -e "  Service     : onlimo.service"
    echo ""
    echo -e "${YELLOW}Perintah berguna:${NC}"
    echo ""
    echo "  Cek status service  : systemctl status onlimo"
    echo "  Restart service     : systemctl restart onlimo"
    echo "  Stop service        : systemctl stop onlimo"
    echo "  Lihat log           : tail -f ${LOG_FILE}"
    echo "  Lihat log aplikasi  : tail -f ${APP_LOG_FILE}"
    echo ""
    echo -e "${YELLOW}Akses aplikasi:${NC}"
    echo ""
    echo "  URL      : http://<server-ip>:${APP_PORT}"
    echo "  Username : (lihat file .env: ADMIN_USERNAME)"
    echo "  Password : (lihat file .env: ADMIN_PASSWORD)"
    echo ""
    echo -e "${YELLOW}Langkah selanjutnya:${NC}"
    echo ""
    echo "  1. Buka browser dan akses URL di atas"
    echo "  2. Login dengan kredensial admin"
    echo "  3. Tambah device di menu Devices"
    echo "  4. Konfigurasi DLH API di menu DLH Config"
    echo "  5. Konfigurasi HAS Portal di menu HAS Config"
    echo ""
    echo -e "${GREEN}============================================================${NC}"
    echo ""
}

# ============================================================================
# Parse Arguments
# ============================================================================

show_help() {
    echo "Usage: sudo bash install.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --skip-db           Skip database creation"
    echo "  --skip-service      Skip systemd service setup"
    echo "  --skip-sudoers      Skip sudoers configuration"
    echo "  --non-interactive   Run without prompts (use defaults)"
    echo "  -h, --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  sudo bash install.sh                    # Full interactive install"
    echo "  sudo bash install.sh --skip-db          # Skip database creation"
    echo "  sudo bash install.sh --non-interactive  # Use all defaults"
    echo "  sudo bash install.sh --skip-db --skip-service  # Partial install"
}

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --skip-db)        SKIP_DB=true ;;
        --skip-service)   SKIP_SERVICE=true ;;
        --skip-sudoers)   SKIP_SUDOERS=true ;;
        --non-interactive) NON_INTERACTIVE=true ;;
        -h|--help)        show_help; exit 0 ;;
        *) print_error "Unknown option: $1"; show_help; exit 1 ;;
    esac
    shift
done

# ============================================================================
# Main
# ============================================================================

print_banner
check_root
check_os

echo -e "${YELLOW}Konfigurasi instalasi:${NC}"
echo "  App Directory : ${APP_DIR}"
echo "  App User      : ${APP_USER}"
echo "  App Port      : ${APP_PORT}"
echo "  FTP Root      : ${FTP_ROOT}"
echo "  Skip DB       : ${SKIP_DB}"
echo "  Skip Service  : ${SKIP_SERVICE}"
echo "  Skip Sudoers  : ${SKIP_SUDOERS}"
echo "  Non-Interactive: ${NON_INTERACTIVE}"
echo ""

if ! ask_continue "Lanjutkan instalasi?" "Y"; then
    print_info "Instalasi dibatalkan."
    exit 0
fi

echo ""

step_check_app_dir
step_install_dependencies
step_setup_venv
step_setup_env
step_setup_database
step_setup_ftp_dir
step_setup_permissions
step_setup_sudoers
step_setup_log_dir
step_setup_systemd
step_setup_logrotate
step_start_service

print_summary