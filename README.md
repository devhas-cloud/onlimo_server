# Onlimo DLH

Water Quality Monitoring System — aplikasi backend untuk menerima data kualitas air dari alat pengukur melalui FTP, menyimpannya ke database MySQL, dan mengirimkan data ke DLH (Dinas Lingkungan Hidup) serta HAS Portal melalui API.

## Fitur

- **FTP Data Ingestion** — Membaca file CSV dari folder FTP alat pengukur secara berkala (setiap 30 detik)
- **CSV Parser** — Parsing file CSV dengan delimiter semicolon, mapping kolom dinamis ke parameter standar
- **DLH API Integration** — Pengiriman data ke DLH setiap jam (HH:00:10) dengan retry otomatis setiap 10 menit
- **HAS Portal Integration** — Pengiriman data real-time ke HAS Portal setelah CSV diproses, dengan parameter yang dapat dikonfigurasi
- **Device Management** — CRUD akun alat pengukur kualitas air, termasuk pembuatan akun FTP otomatis
- **Dashboard** — Ringkasan data dan status pengiriman DLH/HAS
- **Authentication** — Login administrator dengan Flask-Login

## Arsitektur

```
Alat Pengukur ──FTP (CSV)──> /home/onlimo/<device_id>/*.csv
                                       │
                                       ▼
                               FTP Watcher (30s)
                                       │
                                       ▼
                              Parse CSV ─> DB (wide table)
                                       │
                          ┌────────────┴────────────┐
                          ▼                          ▼
                   HAS Sender                DLH Primary (HH:00:10)
                   (real-time)              DLH Retry (10 menit)
                          │                          │
                          ▼                          ▼
                    HAS Portal API            DLH API
```

## Persyaratan

- Python 3.10+
- MySQL 5.7+ / MariaDB 10.3+
- vsftpd (untuk FTP server)
- sudo (untuk eksekusi script FTP)
- Systemd (untuk service management)

## Instalasi

### 1. Clone Repository

```bash
cd /var/www/html
git clone <repository-url> onlimo_server
cd onlimo_server
```

### 2. Buat Virtual Environment & Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

### 3. Konfigurasi Environment

Salin file `.env.example` ke `.env` dan sesuaikan:

```bash
cp .env.example .env
nano .env
```

Konfigurasi yang perlu disesuaikan:

| Variable | Default | Keterangan |
|---|---|---|
| `SECRET_KEY` | - | Kunci rahasia Flask (ganti dengan string acak) |
| `DB_HOST` | localhost | Host MySQL |
| `DB_PORT` | 3306 | Port MySQL |
| `DB_USER` | onlimo | User MySQL |
| `DB_PASSWORD` | onlimo | Password MySQL |
| `DB_NAME` | onlimo | Nama database MySQL |
| `ADMIN_USERNAME` | admin | Username admin default |
| `ADMIN_PASSWORD` | admin123 | Password admin default |
| `FTP_ROOT` | /home/onlimo | Root folder FTP |
| `APP_HOST` | 0.0.0.0 | Host bind aplikasi |
| `APP_PORT` | 9000 | Port aplikasi |

### 4. Buat Database MySQL

```bash
mysql -u root -p
```

```sql
CREATE DATABASE onlimo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'onlimo'@'localhost' IDENTIFIED BY 'onlimo';
GRANT ALL PRIVILEGES ON onlimo.* TO 'onlimo'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Tabel akan dibuat otomatis saat aplikasi pertama kali dijalankan.

### 5. Buat Folder FTP Root

```bash
mkdir -p /home/onlimo
chmod 755 /home/onlimo
```

### 6. Setup Permissions

```bash
# Set executable permission untuk FTP scripts
chmod +x addftp.sh delftp.sh
```

### 7. Setup Sudoers untuk FTP Scripts

```bash
sudo visudo -f /etc/sudoers.d/onlimo_ftp
```

Tambahkan baris berikut (sesuaikan user yang menjalankan service):

```
root ALL=(root) NOPASSWD: /var/www/html/onlimo_server/addftp.sh, /var/www/html/onlimo_server/delftp.sh
```

### 8. Buat Log Directory

```bash
mkdir -p /var/log/onlimo
touch /var/log/onlimo/onlimo.log
```

### 9. Setup Systemd Service

```bash
sudo cp onlimo.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable onlimo
sudo systemctl start onlimo
```

Verifikasi service berjalan:

```bash
sudo systemctl status onlimo
```

Lihat log:

```bash
tail -f /var/log/onlimo/onlimo.log
```

### 10. Setup Logrotate

```bash
sudo tee /etc/logrotate.d/onlimo << 'EOF'
/var/log/onlimo/onlimo.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
    create 644 root root
    dateext
    dateformat -%Y%m%d
}
EOF
```

Juga setup logrotate untuk log aplikasi:

```bash
sudo tee /etc/logrotate.d/onlimo_app << 'EOF'
/var/www/html/onlimo_server/onlimo_dlh.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
    create 644 root root
    dateext
    dateformat -%Y%m%d
}
EOF
```

## Penggunaan

### Akses Aplikasi

Buka browser dan akses:

```
http://<server-ip>:9000
```

Login dengan kredensial admin yang dikonfigurasi di `.env` (default: `admin` / `admin123`).

### Menu Aplikasi

| Menu | Fungsi |
|---|---|
| **Dashboard** | Ringkasan data dan status pengiriman DLH/HAS |
| **Devices** | Kelola akun alat pengukur (tambah, edit, hapus, FTP management) |
| **Data** | Lihat data measurement dengan filter |
| **DLH Config** | Konfigurasi API DLH per device |
| **HAS Config** | Konfigurasi HAS Portal (global) dan pilih parameter yang dikirim |
| **Logs** | Log pengiriman data ke DLH dan HAS Portal |

### Menambah Device Baru

1. Buka menu **Devices** → klik **Tambah Device**
2. Isi **Device ID** (ID unik, misal: `SP-001`) dan **Device Name** (nama deskriptif, misal: `Stasiun Kali Brantas`)
3. Username dan password FTP akan dibuat otomatis
4. Aktifkan **CSV Reader Status** untuk mulai membaca data dari FTP
5. Konfigurasi DLH API di menu **DLH Config**

### Format CSV yang Didukung

File CSV yang diunggah ke folder FTP harus berformat:

- **Delimiter:** semicolon (`;`)
- **Baris 1:** Header identifier (diabaikan)
- **Baris 2:** Header parameter (di-parse untuk mapping)
- **Baris 3+:** Data (timestamp + values)

Contoh:

```csv
Timestamp;spec 23260208;spec 23260208;spec 23260208
Measurement interval=120[sec];ph - Measured value;tds - Measured value;do - Measured value
2026-06-15 02:36:00;7.1;120.5;6.8
```

### Mapping Parameter CSV

| CSV Header Pattern | Parameter Standar |
|---|---|
| `ph - Measured value` | `ph` |
| `tds - Measured value` | `tds` |
| `do - Measured value` | `do` |
| `dissolved oxygen - Measured value` | `do` |
| `conductivity - Measured value` | `conduct` |
| `salinity - Measured value` | `salinity` |
| `nh3n - Measured value` / `ammonium - Measured value` | `nh3n` |
| `battery - Measured value` | `battery` |
| `depth - Measured value` | `depth` |
| `flow - Measured value` / `debit - Measured value` | `flow` |
| `total flow` | `tflow` |
| `turbidity - Measured value` | `turb` |
| `tss - Measured value` / `tsseq - Measured value` | `tss` |
| `cod - Measured value` / `codeq - Measured value` | `cod` |
| `bod - Measured value` / `bodeq - Measured value` | `bod` |
| `no3 - Measured value` / `no3eq - Measured value` | `no3` |
| `temperature - Measured value` | `wtemp` |
| `wpress - Measured value` | `wpress` |

### Pengiriman Data ke DLH

- **Jadwal Primary:** Setiap jam tepat di menit ke-0 detik ke-10 (`HH:00:10`)
- **Retry:** Setiap 10 menit untuk data yang gagal atau pending
- **Format:** JSON POST ke API DLH dengan `apikey` dan `apisecret`
- **Status:** `pending` → `sent` / `failed`

### Pengiriman Data ke HAS Portal

- **Real-time:** Data dikirim segera setelah CSV diproses
- **Parameter:** Dapat dikonfigurasi di menu **HAS Config** (checkbox per parameter)
- **Format:** JSON POST ke HAS API dengan `X-API-Key` header

## Skema Database

### Tabel `config_device`

| Kolom | Tipe | Keterangan |
|---|---|---|
| `id` | INT, PK, AUTO_INCREMENT | |
| `device_id` | VARCHAR(255), UNIQUE | ID unik device |
| `device_name` | VARCHAR(255), NOT NULL | Nama deskriptif device |
| `userftp` | VARCHAR(255), DEFAULT 'onlimo' | Username FTP |
| `passwordftp` | VARCHAR(255), DEFAULT 'onlimo_pass_2026' | Password FTP |
| `dlh_status` | VARCHAR(50), DEFAULT 'inactive' | Status pengiriman DLH |
| `dlh_api_url` | TEXT | URL API DLH |
| `dlh_api_key` | TEXT | API Key DLH |
| `dlh_api_secret` | TEXT | API Secret DLH |
| `dlh_uid` | VARCHAR(255) | IDStasiun DLH |
| `read_csv_status` | VARCHAR(50), DEFAULT 'inactive' | Status pembacaan CSV |

### Tabel `data_measurements`

| Kolom | Tipe | Keterangan |
|---|---|---|
| `id` | INT, PK, AUTO_INCREMENT | |
| `device_id` | VARCHAR(255), FK | ID device |
| `timestamp` | DATETIME | Waktu pengukuran |
| `ph` | FLOAT, NULLABLE | pH |
| `orp` | FLOAT, NULLABLE | ORP |
| `tds` | FLOAT, NULLABLE | TDS |
| `conduct` | FLOAT, NULLABLE | Conductivity |
| `do` | FLOAT, NULLABLE | Dissolved Oxygen |
| `salinity` | FLOAT, NULLABLE | Salinity |
| `nh3n` | FLOAT, NULLABLE | NH3-N |
| `battery` | FLOAT, NULLABLE | Battery |
| `depth` | FLOAT, NULLABLE | Depth |
| `flow` | FLOAT, NULLABLE | Flow |
| `tflow` | FLOAT, NULLABLE | Total Flow |
| `turb` | FLOAT, NULLABLE | Turbidity |
| `tss` | FLOAT, NULLABLE | TSS |
| `cod` | FLOAT, NULLABLE | COD |
| `bod` | FLOAT, NULLABLE | BOD |
| `no3` | FLOAT, NULLABLE | NO3 |
| `wtemp` | FLOAT, NULLABLE | Water Temperature |
| `wpress` | FLOAT, NULLABLE | Water Pressure |
| `dlh_send_status` | VARCHAR(50), DEFAULT 'pending' | Status pengiriman DLH |
| `dlh_response` | TEXT, NULLABLE | Response dari DLH |
| `has_send_status` | VARCHAR(50), DEFAULT 'pending' | Status pengiriman HAS |
| `has_response` | TEXT, NULLABLE | Response dari HAS |

### Tabel `has_config`

| Kolom | Tipe | Keterangan |
|---|---|---|
| `id` | INT, PK, AUTO_INCREMENT | |
| `has_status` | VARCHAR(50), DEFAULT 'inactive' | Status HAS Portal |
| `has_api_url` | TEXT | URL API HAS Portal |
| `has_api_key` | VARCHAR(255) | API Key HAS Portal |
| `has_params` | TEXT, NULLABLE | Parameter yang dikirim (comma-separated) |

### Tabel `admin`

| Kolom | Tipe | Keterangan |
|---|---|---|
| `id` | INT, PK, AUTO_INCREMENT | |
| `username` | VARCHAR(255), UNIQUE | Username admin |
| `password_hash` | VARCHAR(255) | Password hash |

## Struktur Proyek

```
onlimo_server/
├── app.py                    # Flask app factory + APScheduler
├── config.py                 # Konfigurasi dari .env
├── run.py                    # Entry point gunicorn
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables
├── addftp.sh                 # Script tambah akun FTP
├── delftp.sh                 # Script hapus akun FTP
├── onlimo.service            # Systemd service file
├── models/
│   ├── __init__.py           # SQLAlchemy db instance
│   ├── admin.py              # Model admin
│   ├── config_device.py      # Model config_device
│   ├── data_measurement.py    # Model data_measurements (wide table)
│   └── has_config.py          # Model has_config (global)
├── routes/
│   ├── __init__.py           # Blueprint registration
│   ├── auth.py               # Login/logout
│   ├── dashboard.py          # Dashboard ringkasan
│   ├── devices.py            # CRUD devices + FTP management
│   ├── data.py               # Data measurements (filter + pagination)
│   ├── dlh_config.py          # Konfigurasi DLH per device
│   ├── has_config.py          # Konfigurasi HAS Portal (global)
│   └── logs.py                # Log pengiriman DLH/HAS
├── services/
│   ├── __init__.py
│   ├── csv_parser.py          # Parse CSV semicolon, 2 header rows
│   ├── ftp_watcher.py         # Scan FTP folder untuk CSV baru
│   ├── dlh_sender.py           # Kirim data ke DLH (primary + retry)
│   ├── has_sender.py           # Kirim data ke HAS Portal (real-time)
│   └── ftp_manager.py          # Eksekusi addftp.sh/delftp.sh
├── templates/
│   ├── base.html              # Layout + navbar Bootstrap 5
│   ├── login.html
│   ├── dashboard.html
│   ├── devices.html
│   ├── device_form.html
│   ├── data.html
│   ├── dlh_config.html
│   ├── has_config.html
│   └── logs.html
└── static/
    ├── css/style.css          # Modern light theme CSS
    └── js/app.js
```

## Manajemen Service

```bash
# Start service
sudo systemctl start onlimo

# Stop service
sudo systemctl stop onlimo

# Restart service
sudo systemctl restart onlimo

# Cek status
sudo systemctl status onlimo

# Lihat log real-time
tail -f /var/log/onlimo/onlimo.log

# Lihat log aplikasi
tail -f /var/www/html/onlimo_server/onlimo.log
```

## Troubleshooting

### Service gagal start

```bash
# Lihat detail error
sudo journalctl -u onlimo -n 50 --no-pager

# Cek konfigurasi
cat /var/www/html/onlimo_server/.env

# Cek koneksi MySQL
mysql -u onlimo -p -h localhost onlimo
```

### FTP user gagal dibuat

Pastikan:
1. `addftp.sh` dan `delftp.sh` executable (`chmod +x`)
2. Sudoers dikonfigurasi dengan benar (`/etc/sudoers.d/onlimo_ftp`)
3. vsftpd terinstal dan berjalan

### Data CSV tidak terbaca

1. Pastikan `read_csv_status` device di-set ke `active` di dashboard
2. Pastikan file CSV berada di `/home/onlimo/<device_id>/`
3. Setelah berhasil dibaca, file CSV akan dihapus otomatis
4. Cek log: `tail -f onlimo_dlh.log | grep ftp_watcher`

### Data tidak terkirim ke DLH

1. Pastikan `dlh_status` device di-set ke `active`
2. Pastikan konfigurasi DLH API (URL, Key, Secret, UID) lengkap
3. Cek status pengiriman di menu **Logs**
4. Cek log: `tail -f onlimo_dlh.log | grep dlh_sender`

## Teknologi

| Komponen | Teknologi |
|---|---|
| Backend | Flask 3.1, SQLAlchemy, Flask-Login |
| Database | MySQL (PyMySQL) |
| Scheduler | APScheduler 3.11 |
| WSGI Server | Gunicorn |
| Frontend | Bootstrap 5, Jinja2 |
| FTP Server | vsftpd |
| Service Manager | systemd |

## Lisensi

Hak Cipta Dilindungi. Penggunaan terbatas sesuai ketentuan yang berlaku.