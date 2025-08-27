# Quick Start Guide - Azure VM Deployment

## 🚀 Quick Commands Summary

### 1. Azure VM Creation (Azure CLI)
```bash
# Login and create resources
az login
az group create --name renewable-energy-rg --location eastus
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

### 2. VM Setup
```bash
# Get VM IP
VM_IP=$(az vm show --resource-group renewable-energy-rg --name renewable-energy-vm --show-details --query publicIps --output tsv)

# Connect to VM
ssh azureuser@$VM_IP

# Run setup
git clone https://github.com/your-username/AI-Renewable-energy-forcasting.git
cd AI-Renewable-energy-forcasting
chmod +x scripts/setup-azure-vm.sh
./scripts/setup-azure-vm.sh
sudo reboot
```

### 3. Application Deployment
```bash
# After reboot, connect again
ssh azureuser@$VM_IP

# Setup application
sudo mkdir -p /opt/renewable-energy-app
sudo chown azureuser:azureuser /opt/renewable-energy-app
cd /opt/renewable-energy-app
git clone https://github.com/your-username/AI-Renewable-energy-forcasting.git .

# Create environment file
cat > .env << EOF
AZURE_SQL_SERVER=your-server.database.windows.net
AZURE_SQL_USERNAME=your-username
AZURE_SQL_PASSWORD=your-password
AZURE_SQL_DATABASE=your-database-name
SECRET_KEY=your-secret-key-here
EOF

# Deploy
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### 4. GitHub Secrets Configuration
Add these secrets in GitHub repository settings:

```
DOCKER_USERNAME=your-dockerhub-username
DOCKER_PASSWORD=your-dockerhub-password
AZURE_VM_HOST=your-vm-ip-address
AZURE_VM_USERNAME=azureuser
AZURE_VM_SSH_KEY=your-private-ssh-key-content
AZURE_SQL_SERVER=your-server.database.windows.net
AZURE_SQL_USERNAME=your-username
AZURE_SQL_PASSWORD=your-password
AZURE_SQL_DATABASE=your-database-name
SECRET_KEY=your-secret-key
```

### 5. Verify Deployment
```bash
# Check container status
sudo docker ps

# View logs
sudo docker logs renewable-energy-app

# Test application
curl http://localhost/health
```

## 🔧 Useful Commands

### Application Management
```bash
# Restart application
sudo systemctl restart renewable-energy-app

# View logs
sudo docker logs -f renewable-energy-app

# Update application
cd /opt/renewable-energy-app
git pull
./scripts/deploy.sh
```

### System Monitoring
```bash
# System resources
htop
df -h
free -h

# Docker resources
sudo docker stats
sudo docker system df
```

### Troubleshooting
```bash
# Check services
sudo systemctl status nginx
sudo systemctl status docker

# Check ports
sudo netstat -tlnp | grep :80
sudo ufw status

# Clean Docker
sudo docker system prune -f
sudo docker volume prune -f
```

## 💰 Cost Optimization Tips

1. **Enable auto-shutdown**: Set VM to shutdown at night
2. **Use Spot instances**: For development (not production)
3. **Monitor usage**: Set up cost alerts
4. **Right-size**: Start with smaller VM, scale up if needed

## 🔒 Security Checklist

- [ ] SSH key-based authentication enabled
- [ ] Password authentication disabled
- [ ] Firewall configured (only ports 22, 80, 443)
- [ ] Regular security updates scheduled
- [ ] Secrets not committed to Git
- [ ] SSL certificate configured (optional)

## 📞 Support

If you encounter issues:
1. Check logs: `sudo docker logs renewable-energy-app`
2. Verify environment variables in `.env` file
3. Ensure Azure SQL Server allows connections
4. Check GitHub Actions logs for CI/CD issues

Your application should be available at: `http://YOUR_VM_IP`
