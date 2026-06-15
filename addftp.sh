#!/bin/bash

USERNAME=$1
PASSWORD=$2

if [ -z "$USERNAME" ] || [ -z "$PASSWORD" ]; then
    echo "Usage:"
    echo "ftp-create-user username password"
    exit
fi

useradd -d /home/onlimo/$USERNAME -s /usr/sbin/nologin -m $USERNAME

echo "$USERNAME:$PASSWORD" | chpasswd

mkdir -p /home/onlimo/$USERNAME

chown $USERNAME:$USERNAME /home/onlimo/$USERNAME

cat <<EOF >/etc/vsftpd/users/$USERNAME
local_root=/home/onlimo/$USERNAME
EOF

echo "User created"