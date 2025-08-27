# AI-Powered Renewable Energy Forecasting System

A comprehensive dashboard system for solar and wind energy forecasting, featuring user-specific dashboards based on plant type and customized features for different user roles. Now with **Docker deployment** and **CI/CD pipeline** for Azure VM.

## 🚀 Quick Deploy to Azure

### Option 1: Automated CI/CD (Recommended)
1. **Fork this repository**
2. **Configure GitHub secrets** (see [QUICKSTART.md](QUICKSTART.md))
3. **Push to main branch** - automatic deployment!

### Option 2: Manual Deployment
```bash
# See detailed instructions in DEPLOYMENT.md
./scripts/deploy.sh
```

## 📋 Features

- **Role-based Dashboards**: Solar, Wind, and Admin interfaces
- **AI-powered Forecasting**: Machine learning models for energy prediction
- **Real-time Weather Integration**: Open-Meteo API integration
- **Threshold Alerts**: Automated recommendations for low generation
- **Azure SQL Server**: Cloud database integration
- **Docker Deployment**: Containerized application
- **CI/CD Pipeline**: Automated testing and deployment

## 🛠️ Technology Stack

- **Backend**: Python Flask, SQLAlchemy, scikit-learn
- **Frontend**: HTML5, CSS3, JavaScript, Chart.js
- **Database**: Azure SQL Server
- **Deployment**: Docker, Nginx, Gunicorn
- **Cloud**: Azure VM, GitHub Actions CI/CD
- **APIs**: Open-Meteo Weather API

## 📁 Project Structure

```
├── app.py                      # Main Flask application
├── models/                     # Trained ML models
│   ├── solar_power_rf_model.pkl
│   └── wind_power_rf_model.pkl.gz
├── ml_pipeline/                # ML processing pipeline
│   ├── fetch_weather.py
│   ├── predict_hourly.py
│   └── aggregate_daily.py
├── static/                     # Frontend assets
├── templates/                  # Jinja2 templates
├── scripts/                    # Deployment scripts
├── .github/workflows/          # CI/CD pipeline
├── Dockerfile                  # Container configuration
├── docker-compose.yml          # Production compose
├── nginx/                      # Web server config
└── docs/                      # Documentation
```

## 🔧 Local Development

### Prerequisites
- Python 3.10+
- Docker & Docker Compose
- Azure SQL Server credentials

### Setup

### Setup

```bash
# Clone repository
git clone https://github.com/your-username/AI-Renewable-energy-forcasting.git
cd AI-Renewable-energy-forcasting

# Create .env file
cp .env.example .env
# Edit .env with your Azure SQL credentials

# Option 1: Docker Development
docker-compose -f docker-compose.dev.yml up --build

# Option 2: Local Python
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Access the application at `http://localhost:5000`

## 🚀 Production Deployment

### Azure VM Deployment
See detailed guides:
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide
- **[QUICKSTART.md](QUICKSTART.md)** - Quick commands reference

### Key Steps:
1. **Create Azure VM** (Standard_B2s recommended for student subscription)
2. **Setup Docker & dependencies** using provided scripts
3. **Configure CI/CD** with GitHub Actions
4. **Deploy application** automatically on git push

## 📊 System Architecture

### Database Schema (Azure SQL Server)
- **Plants** → **Users** (1:many)
- **Plants** → **Predictions** (1:many)
- Separate tables for solar/wind hourly and daily predictions

### ML Pipeline Flow
1. **Weather Fetch**: Open-Meteo API (5-day forecast)
2. **Hourly Prediction**: scikit-learn models with domain logic
3. **Daily Aggregation**: Sum hourly data, generate recommendations

### User Roles & Access
- **Solar Users**: Solar plant dashboard only
- **Wind Users**: Wind plant dashboard only  
- **Admins**: Multi-plant overview with tabs

## 🔐 Environment Variables

Required in `.env` file:
```env
AZURE_SQL_SERVER=your-server.database.windows.net
AZURE_SQL_USERNAME=your-username
AZURE_SQL_PASSWORD=your-password
AZURE_SQL_DATABASE=your-database-name
SECRET_KEY=your-secret-key-here
```

## 🧪 API Endpoints

### Web Routes
- `/` - Home page
- `/login` - User authentication
- `/dashboard` - Role-based dashboard routing
- `/solar_dashboard` - Solar plant interface
- `/wind_dashboard` - Wind plant interface
- `/admin_dashboard` - Admin multi-plant view

### API Routes
- `/api/refresh-solar-data` - Trigger solar forecast update
- `/api/refresh-wind-data` - Trigger wind forecast update
- `/api/solar_chart_data` - Get solar prediction data
- `/api/wind_chart_data` - Get wind prediction data
- `/api/weather-data` - Current weather information
- `/health` - Container health check

## 🛡️ Security Features

- **Role-based access control**
- **Session management** with Flask-Login
- **SQL injection prevention** with parameterized queries
- **Environment-based secrets** management
- **Docker security** with non-root user
- **Nginx security headers**

## 📈 Monitoring & Logs

```bash
# Application logs
sudo docker logs renewable-energy-app

# System monitoring
htop
sudo docker stats

# Log files
tail -f /opt/renewable-energy-app/logs/access.log
tail -f /opt/renewable-energy-app/logs/error.log
```

## 🔄 CI/CD Pipeline

Automated workflow on push to main:
1. **Test**: Python linting and tests
2. **Build**: Docker image creation
3. **Deploy**: Push to Docker Hub & deploy to Azure VM

## 💰 Cost Optimization

For Azure Student subscription:
- **VM Size**: Standard_B2s (2 vCPUs, 4GB RAM)
- **Auto-shutdown**: Schedule VM shutdown during off-hours
- **Monitoring**: Set up cost alerts
- **Storage**: Use Standard HDD for logs

## 🚨 Troubleshooting

### Common Issues
1. **Database connection**: Check Azure SQL firewall settings
2. **Docker issues**: Verify ODBC driver installation
3. **Port conflicts**: Ensure ports 80/443 are available
4. **Memory issues**: Monitor container resource usage

### Debug Commands
```bash
# Check container status
sudo docker ps -a

# View application logs
sudo docker logs renewable-energy-app

# Test database connection
sudo docker exec -it renewable-energy-app python -c "from app import db; print('DB OK')"

# Restart services
sudo systemctl restart renewable-energy-app
sudo systemctl restart nginx
```

## 📝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

- **Documentation**: [DEPLOYMENT.md](DEPLOYMENT.md) for deployment help
- **Quick Start**: [QUICKSTART.md](QUICKSTART.md) for fast setup
- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions

---

**Live Demo**: `http://your-azure-vm-ip` (after deployment)
**Status**: [![CI/CD Pipeline](https://github.com/your-username/AI-Renewable-energy-forcasting/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/your-username/AI-Renewable-energy-forcasting/actions) 