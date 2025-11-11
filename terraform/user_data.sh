#!/bin/bash
set -e

# install updates and tools
apt-get update -y
apt-get install -y python3-pip python3-venv git awscli

# create app dir
mkdir -p /opt/wms_app
cd /opt/wms_app

# pull app from user-provided S3/Git? We'll create files via Terraform provisioner copy if needed.
# For simplicity: assume Terraform will upload app files to /opt/wms_app (or you can git clone repo)

# create venv and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install flask psycopg2-binary boto3 cryptography aws-encryption-sdk awscli aws-xray-sdk

# configure cloudwatch logs (simple agent)
apt-get install -y collectd
# simple logger: start app with redirect to stdout and rely on CloudWatch agent if configured separately

# create directory for logs
mkdir -p /var/log/wms
chown -R ubuntu:ubuntu /var/log/wms

# create systemd service to run the Flask app
cat <<'EOF' > /etc/systemd/system/wms.service
[Unit]
Description=WMS Flask App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/wms_app
Environment="PATH=/opt/wms_app/venv/bin"
ExecStart=/opt/wms_app/venv/bin/python /opt/wms_app/app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable wms
systemctl start wms
