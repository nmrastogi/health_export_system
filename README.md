# iPhone Health Data Export System

A comprehensive system to automatically export sleep and exercise data from iPhone Health app to Amazon RDS database.

## Features

- 🛏️ **Sleep Data Export**: Every 6 hours
- 🏃 **Exercise Data Export**: Every 15 minutes  
- 🗄️ **Amazon RDS Integration**: Automatic database storage
- 📊 **Data Analytics**: Built-in data processing
- 🔄 **Automated Scheduling**: Background data collection
- 📱 **iPhone Integration**: Health app data access

## Prerequisites

- Python 3.8 or higher
- Amazon RDS MySQL database
- iPhone with Health app data
- Health data export method (Shortcuts app or third-party service)

## Installation

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd health_export_system
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp config_template.txt .env
   ```
   
   Edit `.env` file with your credentials:
   ```env
   # Amazon RDS Database Configuration
   RDS_HOST=your-rds-endpoint.amazonaws.com
   RDS_USER=your-database-username
   RDS_PASSWORD=your-database-password
   RDS_DATABASE=health_data
   RDS_PORT=3306
   
   # iPhone Health App API Configuration
   HEALTH_SLEEP_ENDPOINT=https://your-health-api.com/api/sleep
   HEALTH_EXERCISE_ENDPOINT=https://your-health-api.com/api/exercise
   HEALTH_API_KEY=your-health-api-key
   ```

## iPhone Health App Setup

### Method 1: Using Shortcuts App (Recommended)

1. **Open Shortcuts app** on your iPhone
2. **Create a new shortcut** called "Export Health Data"
3. **Add actions:**
   - "Get Health Sample" → Select Sleep Analysis
   - "Get Health Sample" → Select Workout
   - "Get Contents of URL" → POST to your API endpoint
4. **Set up automation** to run every 6 hours for sleep, 15 minutes for exercise

### Method 2: Using Third-Party Apps

- **Health Export**: Export health data to CSV/JSON
- **Health Auto Export**: Automated health data export
- **QSAccess**: Query and export health data

### Method 3: Custom API Integration

If you have access to Health app APIs or use a service like:
- Apple HealthKit (for developers)
- Health data export services
- Custom iOS apps with HealthKit integration

## Amazon RDS Setup

1. **Create RDS MySQL instance**
   ```sql
   CREATE DATABASE health_data;
   ```

2. **Configure security groups** to allow connections from your server

3. **Test connection**
   ```bash
   python test_connection.py
   ```

## Usage

### Start the Health Data Exporter

```bash
python main.py
```

The system will:
- ✅ Connect to Amazon RDS
- ✅ Create necessary database tables
- ✅ Start automated data collection
- ✅ Export sleep data every 6 hours
- ✅ Export exercise data every 15 minutes

### Manual Data Export

```bash
# Export sleep data only
python export_sleep.py

# Export exercise data only  
python export_exercise.py

# Export all data
python export_all.py
```

## Database Schema

### Sleep Data Table
```sql
CREATE TABLE sleep_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    bedtime DATETIME,
    wake_time DATETIME,
    sleep_duration_minutes INT,
    deep_sleep_minutes INT,
    light_sleep_minutes INT,
    rem_sleep_minutes INT,
    sleep_efficiency DECIMAL(5,2),
    heart_rate_avg INT,
    heart_rate_min INT,
    heart_rate_max INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_date (date)
);
```

### Exercise Data Table
```sql
CREATE TABLE exercise_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    activity_type VARCHAR(100),
    duration_minutes INT,
    calories_burned INT,
    distance_km DECIMAL(8,3),
    steps INT,
    heart_rate_avg INT,
    heart_rate_max INT,
    active_energy_kcal INT,
    resting_energy_kcal INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_timestamp (timestamp)
);
```

## Scheduling Options

### Option 1: Built-in Scheduler (Default)
The application runs continuously with built-in scheduling.

### Option 2: Cron Jobs (Linux/Mac)
```bash
# Sleep data every 6 hours
0 */6 * * * /usr/bin/python3 /path/to/health_export_system/main.py --sleep-only

# Exercise data every 15 minutes
*/15 * * * * /usr/bin/python3 /path/to/health_export_system/main.py --exercise-only
```

### Option 3: Windows Task Scheduler
Set up scheduled tasks for:
- Sleep export: Every 6 hours
- Exercise export: Every 15 minutes

## Monitoring and Logs

- **Log file**: `health_export.log`
- **Database logs**: Check RDS CloudWatch logs
- **Health app logs**: Monitor iPhone Shortcuts execution

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check RDS security groups
   - Verify credentials in `.env`
   - Test network connectivity

2. **Health Data Not Available**
   - Ensure Health app has data
   - Check Shortcuts automation
   - Verify API endpoints

3. **Scheduling Issues**
   - Check system time
   - Verify cron jobs (if using)
   - Monitor application logs

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py
```

## Data Analysis

### Basic Queries

```sql
-- Average sleep duration by week
SELECT 
    WEEK(date) as week,
    AVG(sleep_duration_minutes) as avg_sleep_minutes
FROM sleep_data 
GROUP BY WEEK(date)
ORDER BY week;

-- Daily exercise summary
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as exercise_sessions,
    SUM(duration_minutes) as total_minutes,
    SUM(calories_burned) as total_calories
FROM exercise_data 
GROUP BY DATE(timestamp)
ORDER BY date;
```

## Security Considerations

- 🔐 **Encrypt sensitive data** in database
- 🔑 **Use IAM roles** for RDS access
- 🛡️ **Enable SSL** for database connections
- 🔒 **Secure API keys** and credentials
- 📱 **Limit Health app permissions**

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review logs for error messages
3. Open an issue in the repository
