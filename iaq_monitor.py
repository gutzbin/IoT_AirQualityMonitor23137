import Adafruit_DHT
import RPi.GPIO as GPIO
import threading
import csv
import time
import streamlit as st
from collections import deque

# GPIO setup
GPIO.setmode(GPIO.BCM)

# Pins
DHT_PIN = 4 # DHT22 data pin
MQ135_PIN = 17 # MQ-135 digital output
PMS7003_PIN = 27 # PMS7003 alert digital output

GPIO.setup(MQ135_PIN, GPIO.IN)
GPIO.setup(PMS7003_PIN, GPIO.IN)

# DHT22 reading function
def read_dht22():
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, DHT_PIN)
    if humidity is not None and temperature is not None:
        return {'temperature': temperature, 'humidity': humidity}
    else:
        return {'temperature': None, 'humidity': None}

# MQ-135 reading function
def read_mq135():
    value = GPIO.input(MQ135_PIN) # HIGH if gas exceeds threshold
    return {'air_quality_alert': value}

# PMS7003 reading function
def read_pm25():
    value = GPIO.input(PMS7003_PIN) # HIGH if PM2.5 exceeds threshold
    return {'pm25_alert': value}

# -------------------------------------------------------------

# Shared Data
sensor_data = {
    'temperature': None,
    'humidity': None,
    'air_quality_alert': 0,
    'pm25_alert': 0
}

# Keep last N readings for AI prediction
history = deque(maxlen=10)

# Reading the sensors, thread 1
def sensor_thread():
    global sensor_data, history
    while True:
        dht = read_dht22()
        mq = read_mq135()
        pm = read_pm25()

        sensor_data.update(dht)
        sensor_data.update(mq)
        sensor_data.update(pm)

        # Add data to history for AI
        history.append(sensor_data.copy())

        time.sleep(2) # reading interval

# Moving average prediction, thread 2
def ai_thread():
    global history, sensor_data
    while True:
        if len(history) > 1:
            # Safe defaults for none values
            temp = sensor_data['temperature'] if sensor_data['temperature'] is not None else 0
            humidity = sensor_data['humidity'] if sensor_data['humidity'] is not None else 0
            pm25 = sensor_data['pm25_alert']
            
            # Simple moving average prediction
            avg_temp = sum([h['temperature'] for h in history if h['temperature'] is not None]) / len(history)
            avg_humidity = sum([h['humidity'] for h in history if h['humidity'] is not None]) / len(history)
            avg_pm25 = sum([h['pm25_alert'] for h in history]) / len(history)
            # Trigger alert if predicted temp/humidity exceeds thresholds
            if avg_temp > 30:
                print("ALERT: High temperature predicted!")
            if avg_humidity > 70:
                print("ALERT: High humidity predicted!")
            if avg_pm25 > 1:  # 1 = HIGH digital reading from sensor
                print("ALERT: PM2.5 predicted to be high!")

        time.sleep(5)  # prediction interval

# Logging, thread 3
def logging_thread():
    with open("iaq_log.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "temperature", "humidity", "pm25_alert", "ai_alerts"])
        
        while True:
            # Safe defaults for none values
            temp = sensor_data['temperature'] if sensor_data['temperature'] is not None else 0
            humidity = sensor_data['humidity'] if sensor_data['humidity'] is not None else 0
            pm25 = sensor_data['pm25_alert']  # digital, usually 0 or 1
            
            # Build alert message
            alerts = []
            if temp > 30:
                alerts.append("High Temp")
            if humidity > 70:
                alerts.append("High Humidity")
            if pm25 > 1:
                alerts.append("High PM2.5")
            
            # Write current data and alerts
            writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"),
                             sensor_data['temperature'],
                             sensor_data['humidity'],
                             sensor_data['pm25_alert'],
                             ";".join(alerts)])
            f.flush()
            time.sleep(5)

st.set_page_config(page_title="Indoor Air Quality Dashboard")
st.title("Indoor Air Quality Monitoring")

# Placeholders
temp_display = st.empty()
humidity_display = st.empty()
air_alert_display = st.empty()
pm_display = st.empty()

# Start threads
t1 = threading.Thread(target=sensor_thread, daemon=True)
t2 = threading.Thread(target=ai_thread, daemon=True)
t3 = threading.Thread(target=logging_thread, daemon=True)

t1.start()
t2.start()
t3.start()

# Streamlit update loop
while True:
    temp_display.metric("Temperature", sensor_data['temperature'])
    humidity_display.metric("Humidity", sensor_data['humidity'])
    air_alert_display.metric("Air Quality Alert", sensor_data['air_quality_alert'])
    pm_display.metric("PM2.5 Alert", sensor_data['pm25_alert'])
    time.sleep(2)
