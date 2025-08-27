# Azure Deployment Guide for Renewable Energy Forecasting App

This guide will help you deploy your Flask application on Azure VM with Docker and CI/CD.

## Prerequisites

- Azure Student subscription
- GitHub account
- Docker Hub account (free)
- SSH key pair for Azure VM access

## Step 1: Create Azure VM

### 1.1 Using Azure Portal

1. **Go to Azure Portal** (portal.azure.com)
2. **Create a Resource Group**:
   - Name: `renewable-energy-rg`
   - Region: Choose closest to your users (e.g., East US)

3. **Create Virtual Machine**:
   - **Basics**:
     - VM name: `renewable-energy-vm`
     - Region: Same as resource group
     - Image: `Ubuntu 22.04 LTS`
     - Size: `Standard_B2s` (2 vCPUs, 4 GB RAM) - Good for student subscription
     - Authentication: SSH public key
     - Username: `azureuser`
     - SSH public key: Upload your public key or generate new one

   - **Networking**:
     - Create new virtual network
     - Allow SSH (22), HTTP (80), HTTPS (443)

   - **Management**:
     - Enable auto-shutdown (optional, saves costs)

### 1.2 Using Azure CLI (Alternative)

```bash
# Login to Azure
az login

# Create resource group
az group create --name renewable-energy-rg --location eastus

# Create VM
az vm create \
  --resource-group renewable-energy-rg \
  --name renewable-energy-vm \
  --image Ubuntu2204 \
  --size Standard_B2s \
  --admin-username azureuser \
  --generate-ssh-keys \
  --public-ip-sku Standard

# Open ports
az vm open-port --port 80 --resource-group renewable-energy-rg --name renewable-energy-vm
az vm open-port --port 443 --resource-group renewable-energy-rg --name renewable-energy-vm
```

## Step 2: Setup Azure VM

### 2.1 Connect to VM

```bash
# Get VM public IP
az vm show --resource-group renewable-energy-rg --name renewable-energy-vm --show-details --query publicIps --output tsv

# SSH to VM
ssh azureuser@YOUR_VM_PUBLIC_IP
```

### 2.2 Run Setup Script

```bash
# Clone your repository
git clone https://github.com/your-username/AI-Renewable-energy-forcasting.git
cd AI-Renewable-energy-forcasting

# Make setup script executable
chmod +x scripts/setup-azure-vm.sh

# Run setup script
./scripts/setup-azure-vm.sh

# Reboot VM
sudo reboot
```

## Step 3: Configure Environment

### 3.1 Create .env file on VM

```bash
# SSH back to VM after reboot
ssh azureuser@YOUR_VM_PUBLIC_IP

# Navigate to app directory
cd /opt/renewable-energy-app

# Clone your repository here
git clone https://github.com/your-username/AI-Renewable-energy-forcasting.git .

# Create .env file
nano .env
```

Add your Azure SQL credentials:
```env
AZURE_SQL_SERVER=your-server.database.windows.net
AZURE_SQL_USERNAME=your-username
AZURE_SQL_PASSWORD=your-password
AZURE_SQL_DATABASE=your-database-name
SECRET_KEY=your-secret-key-here
```

## Step 4: Setup CI/CD with GitHub Actions

### 4.1 Create Docker Hub Repository

1. Go to hub.docker.com
2. Create repository: `your-username/renewable-energy-app`
3. Note your Docker Hub username and password

### 4.2 Configure GitHub Secrets

In your GitHub repository, go to **Settings > Secrets and variables > Actions** and add:

```
DOCKER_USERNAME=your-dockerhub-username
DOCKER_PASSWORD=your-dockerhub-password
AZURE_VM_HOST=your-vm-public-ip
AZURE_VM_USERNAME=azureuser
AZURE_VM_SSH_KEY=your-private-ssh-key-content
AZURE_SQL_SERVER=your-server.database.windows.net
AZURE_SQL_USERNAME=your-username
AZURE_SQL_PASSWORD=your-password
AZURE_SQL_DATABASE=your-database-name
SECRET_KEY=your-secret-key
```

### 4.3 Update CI/CD Configuration

Edit `.github/workflows/ci-cd.yml` and update:
```yaml
env:
  DOCKER_IMAGE_NAME: renewable-energy-app
  AZURE_VM_RESOURCE_GROUP: renewable-energy-rg  # Your resource group
  AZURE_VM_NAME: renewable-energy-vm            # Your VM name
```

## Step 5: Deploy Application

### 5.1 Manual Deployment (First Time)

```bash
# On your VM
cd /opt/renewable-energy-app

# Make deploy script executable
chmod +x scripts/deploy.sh

# Deploy
./scripts/deploy.sh
```

### 5.2 Automatic Deployment

Push to main branch:
```bash
git add .
git commit -m "Add Docker deployment configuration"
git push origin main
```

This will trigger the CI/CD pipeline automatically.

## Step 6: Verify Deployment

### 6.1 Check Application

1. Open browser and go to `http://YOUR_VM_PUBLIC_IP`
2. You should see your Flask application

### 6.2 Monitor Logs

```bash
# Check container status
sudo docker ps

# View application logs
sudo docker logs renewable-energy-app

# Follow logs in real-time
sudo docker logs -f renewable-energy-app
```

## Step 7: Domain Setup (Optional)

### 7.1 Configure Custom Domain

1. **Buy domain** (or use free subdomain services)
2. **Point domain to VM IP** using A record
3. **Setup SSL certificate**:

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Setup auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Troubleshooting

### Common Issues

1. **Container won't start**:
   ```bash
   sudo docker logs renewable-energy-app
   ```

2. **Database connection issues**:
   - Check .env file format
   - Verify Azure SQL Server firewall allows Azure services

3. **Port access issues**:
   ```bash
   sudo ufw status
   sudo netstat -tlnp | grep :80
   ```

4. **Memory issues**:
   ```bash
   free -h
   sudo docker system prune -f
   ```

### Useful Commands

```bash
# Restart application
sudo systemctl restart renewable-energy-app

# Check system resources
htop

# View nginx logs
sudo tail -f /var/log/nginx/access.log

# Update application
cd /opt/renewable-energy-app
git pull
./scripts/deploy.sh
```

## Cost Optimization

1. **Auto-shutdown**: Enable VM auto-shutdown in Azure portal
2. **Scale down**: Use smaller VM size if sufficient
3. **Monitoring**: Set up cost alerts in Azure
4. **Storage**: Use Standard HDD instead of Premium SSD for non-critical data

## Security Best Practices

1. **Firewall**: Only open necessary ports
2. **SSH**: Use key-based authentication, disable password auth
3. **Updates**: Keep system updated
4. **Secrets**: Never commit secrets to Git
5. **Monitoring**: Set up Azure Monitor for alerts

Your application should now be live and automatically deploy when you push to the main branch!
