# Indoor Air Quality Monitoring System

## Description

A multithreaded IoT system that monitors indoor air quality using three sensors:

* DHT22 → Temperature & Humidity
* MQ-135 → Air Quality / CO₂
* PMS7003 → PM2.5

It provides a live web dashboard via Streamlit, AI-based trend alerts, and logs data to `iaq_log.csv`.

---

## Setup

1. Connect the sensors to the Raspberry Pi:

   * DHT22 → GPIO 4
   * MQ-135 → GPIO 17
   * PMS7003 → GPIO 27

2. Install dependencies:

```bash
pip install Adafruit_DHT RPi.GPIO streamlit
```

3. Save the Python file as `iaq_monitor.py`.

---

## Running

```bash
streamlit run iaq_monitor.py
```

* Open the URL printed by Streamlit (usually `http://localhost:8501`) to view the dashboard.
* The system automatically runs three threads:

  1. Sensor readings
  2. AI predictions & alerts
  3. Data logging

---

## Dashboard

Displays live values for: Temperature, Humidity, Air Quality Alert, PM2.5 Alert.
