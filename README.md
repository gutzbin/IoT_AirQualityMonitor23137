# Indoor Air Quality Monitoring System

## Project Description
This project is an IoT-based indoor air quality monitoring system that continuously tracks environmental parameters using multiple sensors.

**Sensors Used:**
- DHT22 -> Temperature & Humidity
- MQ-135 -> Air Quality / CO₂
- PMS7003 -> PM2.5 Particulate Matter

The system is multithreaded, reading sensors, updating a web dashboard, and running a simple AI module to predict short-term air quality trends. Alerts are triggered if values exceed safe thresholds. The program is designed to auto-run on system startup, ensuring continuous monitoring.

**Key Features:**
- Real-time monitoring of multiple air quality parameters
- Multithreaded implementation for sensors, dashboard, and AI
- AI-based trend prediction and alert system
- Web-based dashboard using Streamlit
- Fully compatible with GPIO-based sensors in the project kit
