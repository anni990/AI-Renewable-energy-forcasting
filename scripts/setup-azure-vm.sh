#!/bin/bash

# Azure VM Setup Script for Renewable Energy Forecasting App
# Run this script on your Azure VM after creation

set -e

echo "🚀 Setting up Azure VM for Renewable Energy Forecasting App..."

# Update system
echo "📦 Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
echo "🐳 Installing Docker..."
sudo apt-get install -y ca-certificates curl gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
echo "🔧 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install other useful tools
echo "🛠️ Installing additional tools..."
sudo apt-get install -y git curl wget htop unzip

# Configure firewall
echo "🔒 Configuring firewall..."
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /opt/renewable-energy-app
sudo chown $USER:$USER /opt/renewable-energy-app

# Install nginx for reverse proxy (optional)
echo "🌐 Installing Nginx..."
sudo apt-get install -y nginx

# Create nginx configuration
sudo tee /etc/nginx/sites-available/renewable-energy-app > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable nginx site
sudo ln -sf /etc/nginx/sites-available/renewable-energy-app /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

# Setup log rotation
echo "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/renewable-energy-app > /dev/null <<EOF
/opt/renewable-energy-app/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
}
EOF

# Create systemd service for Docker container
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/renewable-energy-app.service > /dev/null <<EOF
[Unit]
Description=Renewable Energy Forecasting App
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/renewable-energy-app
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable renewable-energy-app.service

echo "✅ Azure VM setup completed!"
echo ""
echo "Next steps:"
echo "1. Reboot the VM: sudo reboot"
echo "2. Clone your repository to /opt/renewable-energy-app"
echo "3. Create .env file with your Azure SQL credentials"
echo "4. Run: sudo systemctl start renewable-energy-app"
echo ""
echo "Your app will be available at http://your-vm-ip"
