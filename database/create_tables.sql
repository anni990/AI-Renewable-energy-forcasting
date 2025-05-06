-- Plants table (must be created first because users table references it)
CREATE TABLE IF NOT EXISTS plants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    type ENUM('solar', 'wind', 'both') NOT NULL,
    threshold_value DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    plant_id INT,
    plant_type ENUM('solar', 'wind', 'both'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plant_id) REFERENCES plants (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Hourly solar predictions table
CREATE TABLE IF NOT EXISTS hourly_solar_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plant_id INT NOT NULL,
    timestamp DATETIME NOT NULL,
    weather_data JSON NOT NULL,
    predicted_generation DECIMAL(10,2),
    actual_generation DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plant_id) REFERENCES plants (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Hourly wind predictions table
CREATE TABLE IF NOT EXISTS hourly_wind_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plant_id INT NOT NULL,
    timestamp DATETIME NOT NULL,
    weather_data JSON NOT NULL,
    predicted_generation DECIMAL(10,2),
    actual_generation DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plant_id) REFERENCES plants (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Daily solar predictions table
CREATE TABLE IF NOT EXISTS daily_solar_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plant_id INT NOT NULL,
    date DATE NOT NULL,
    total_predicted_generation DECIMAL(10,2),
    total_actual_generation DECIMAL(10,2),
    recommendation_status TINYINT(1) DEFAULT 0,
    recommendation_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plant_id) REFERENCES plants (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Daily wind predictions table
CREATE TABLE IF NOT EXISTS daily_wind_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plant_id INT NOT NULL,
    date DATE NOT NULL,
    total_predicted_generation DECIMAL(10,2),
    total_actual_generation DECIMAL(10,2),
    recommendation_status TINYINT(1) DEFAULT 0,
    recommendation_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plant_id) REFERENCES plants (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create indexes for performance
CREATE INDEX idx_hourly_solar_plant_timestamp ON hourly_solar_predictions (plant_id, timestamp);
CREATE INDEX idx_hourly_wind_plant_timestamp ON hourly_wind_predictions (plant_id, timestamp);
CREATE INDEX idx_daily_solar_plant_date ON daily_solar_predictions (plant_id, date);
CREATE INDEX idx_daily_wind_plant_date ON daily_wind_predictions (plant_id, date);
CREATE INDEX idx_users_plant_id ON users (plant_id); 