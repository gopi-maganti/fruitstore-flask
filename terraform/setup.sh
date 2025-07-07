#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

echo "[INFO] Updating system packages..."
sudo apt-get update -y

echo "[INFO] Installing dependencies..."
sudo apt-get install -y python3-pip git

echo "[INFO] Cloning FruitStore repo..."
git clone https://github.com/gopi-maganti/fruitstore-flask.git

cd fruitstore-flask || exit 1

echo "[INFO] Installing Python requirements..."
pip3 install --user -r requirements.txt

echo "[INFO] Creating .env configuration..."
cat <<EOF > .env
USE_AWS_SECRET=true
AWS_SECRET_NAME=fruitstore-db-secret
AWS_REGION=us-east-1
S3_BUCKET_NAME=fruitstore-image-uploads
EOF

echo "[INFO] Running Flask app..."
nohup python3 run.py > app.log 2>&1 &

echo "[INFO] Deployment complete."
