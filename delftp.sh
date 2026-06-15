#!/bin/bash

USERNAME=$1

if [ -z "$USERNAME" ]; then
    echo "Usage:"
    echo "ftp-delete-user username"
    exit 1
fi

# Pastikan user ada
if ! id "$USERNAME" >/dev/null 2>&1; then
    echo "User '$USERNAME' tidak ditemukan."
    exit 1
fi

echo "Menghapus konfigurasi FTP user: $USERNAME"

# Hapus file konfigurasi vsftpd
if [ -f "/etc/vsftpd/users/$USERNAME" ]; then
    rm -f "/etc/vsftpd/users/$USERNAME"
    echo "✓ File /etc/vsftpd/users/$USERNAME dihapus"
fi

# Hapus user beserta home directory
userdel -r "$USERNAME" 2>/dev/null

# Jika folder masih tersisa, hapus secara manual
if [ -d "/home/onlimo/$USERNAME" ]; then
    rm -rf "/home/onlimo/$USERNAME"
    echo "✓ Folder /home/onlimo/$USERNAME dihapus"
fi

echo "User '$USERNAME' berhasil dihapus."