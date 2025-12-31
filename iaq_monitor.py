import Adafruit_DHT
import RPi.GPIO as GPIO
import threading
import csv
import time
import streamlit as st
import pandas as pd
import os
from flask import Flask, jsonify
from collections import deque

# -------------------------------------------------------------

# GPIO setup
GPIO.setmode(GPIO.BCM)

# Pins
DHT_PIN = 4 # DHT22 data pin
MQ135_PIN = 17 # MQ-135 digital output
MQ5_PIN = 27     # Flammable gas (DANGER)
# DIP switch pins (test overrides)
DIP_TEMP = 5
DIP_HUMIDITY = 6
DIP_AIR = 13
DIP_GAS = 19

GPIO.setup(MQ135_PIN, GPIO.IN)
GPIO.setup(MQ5_PIN, GPIO.IN)

GPIO.setup(DIP_TEMP, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(DIP_HUMIDITY, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(DIP_AIR, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(DIP_GAS, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# -------------------------------------------------------------

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

# MQ-5 reading function
def read_mq5():
    value = GPIO.input(MQ5_PIN)  # HIGH = gas leak
    return {'gas_leak_alert': value}

# -------------------------------------------------------------

# Shared Data
sensor_data = {
    'temperature': None,
    'humidity': None,
    'air_quality_alert': 0,
    'gas_leak_alert': 0
}

# Keep last N readings for AI prediction
history = deque(maxlen=25)

ema_temp = None
ema_humidity = None
alpha = 0.3  # smoothing factor

# -------------------------------------------------------------

app = Flask(__name__)

@app.route("/sensors")
def get_sensors():
    return jsonify(sensor_data)
app = Flask(__name__)

@app.route("/sensors")
def get_sensors():
    return jsonify(sensor_data)

# -------------------------------------------------------------

# Reading the sensors, thread 1
def sensor_thread():
    global sensor_data, history
    while True:
        dht = read_dht22()
        mq135 = read_mq135()
        mq5 = read_mq5()

        sensor_data.update(dht)
        sensor_data.update(mq135)
        sensor_data.update(mq5)

        # Add data to history for AI
        history.append(sensor_data.copy())

        time.sleep(2) # reading interval

# -------------------------------------------------------------

# Exponential moving average prediction, thread 2
def ai_thread():
    global ema_temp, ema_humidity, alpha, sensor_data

    while True:
        temp = sensor_data['temperature'] if sensor_data['temperature'] is not None else None
        humidity = sensor_data['humidity'] if sensor_data['humidity'] is not None else None

        if temp is not None:
            if ema_temp is None:
                ema_temp = temp
            else:
                ema_temp = alpha * temp + (1 - alpha) * ema_temp

        if humidity is not None:
            if ema_humidity is None:
                ema_humidity = humidity
            else:
                ema_humidity = alpha * humidity + (1 - alpha) * ema_humidity

        if ema_temp is not None and ema_temp > 30:
            print("ALERT: High temperature predicted!")
        if ema_humidity is not None and ema_humidity > 70:
            print("ALERT: High humidity predicted!")

        time.sleep(5) # reading interval

# -------------------------------------------------------------

# Logging, thread 3
def logging_thread():
    file_exists = os.path.isfile("iaq_log.csv")
    with open("iaq_log.csv", "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "temperature", "humidity", "air_quality_alert", "gas_leak_alert", "ai_alerts"])
            
        while True:
            # Safe defaults for none values
            temp = sensor_data['temperature'] if sensor_data['temperature'] is not None else 0
            humidity = sensor_data['humidity'] if sensor_data['humidity'] is not None else 0
            air = sensor_data['air_quality_alert'] # digital, 0 or 1
            gas = sensor_data['gas_leak_alert'] # digital, 0 or 1
            
            # Build alert message
            alerts = []
            if temp > 30:
                alerts.append("High Temp")
            if humidity > 70:
                alerts.append("High Humidity")
            if air == 1:
                alerts.append("Poor Air Quality")
            if gas == 1:
                alerts.append("Gas Leak")
            
            # Write current data and alerts
            writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), temp, humidity, air, gas, ";".join(alerts)])
            f.flush()
            time.sleep(5)

# -------------------------------------------------------------

if "initialized" not in st.session_state:
        st.session_state.initialized = True

threading.Thread(target=sensor_thread, daemon=True).start()
threading.Thread(target=ai_thread, daemon=True).start()
threading.Thread(target=logging_thread, daemon=True).start()
threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000), daemon=True).start()

st.set_page_config(page_title="Indoor Air Quality Dashboard")
st.title("Indoor Air Quality Monitoring")

# Placeholders
temp_display = st.empty()
humidity_display = st.empty()
air_alert_display = st.empty()
gas_display = st.empty()

# Alarm state
gas_alarm_latched = False
alerts = {
    "temp": False,
    "humidity": False,
    "air": False,
    "gas": False
}

# Streamlit containers
metrics_container = st.container()
chart_container = st.container()
alerts_container = st.container()

# LED pin
LED_PIN = 23
GPIO.setup(LED_PIN, GPIO.OUT)

def alarm_on():
    GPIO.output(LED_PIN, GPIO.HIGH)

def alarm_off():
    GPIO.output(LED_PIN, GPIO.LOW)

# Update loop
try:
    temp = sensor_data['temperature']
    humidity = sensor_data['humidity']
    
    # Update metrics
    with metrics_container:
        st.metric("Temperature", "—" if temp is None else f"{temp:.1f} °C")
        st.metric("Humidity", "—" if humidity is None else f"{humidity:.1f} %")
        st.metric("Air Quality Alert", sensor_data['air_quality_alert'])
        st.metric("Gas Leak Alert", sensor_data['gas_leak_alert'])

    # Update chart
    with chart_container:
        if history:
            df = pd.DataFrame(list(history))
            st.line_chart(df[['temperature', 'humidity', 'gas_leak_alert']])

    # Update alerts
    with alerts_container:
        dip_temp = GPIO.input(DIP_TEMP)
        dip_humidity = GPIO.input(DIP_HUMIDITY)
        dip_air = GPIO.input(DIP_AIR)
        dip_gas = GPIO.input(DIP_GAS)
        
        st.caption(f"DIP switches — Temp:{dip_temp} Hum:{dip_humidity} Air:{dip_air} Gas:{dip_gas}")
        
        temp = sensor_data['temperature']
        humidity = sensor_data['humidity']
        air = sensor_data['air_quality_alert']
        gas = sensor_data['gas_leak_alert']

        # Advisory alerts
        alerts["temp"] = (temp is not None and temp > 40) or dip_temp == 1
        alerts["humidity"] = (humidity is not None and humidity > 70) or dip_humidity == 1
        alerts["air"] = (air == 1) or dip_air == 1

        # Gas alarm latch
        if gas == 1 or dip_gas == 1:
            gas_alarm_latched = True
            alerts["gas"] = True

        # Display advisory messages
        if alerts["temp"]:
            st.warning("Temperature is high! Turn on a fan or improve ventilation.")
        if alerts["humidity"]:
            st.warning(
                "Humidity is high! Consider ventilation or a dehumidifier."
            )
        if alerts["air"]:
            st.warning(
                "Air quality is poor! Open a window and point a fan toward it."
            )
        
        # Gas leak emergency
        if gas_alarm_latched:
            # Flash background red
            st.markdown(
                """
                <style>
                body {
                    background-color: #8B0000;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            st.error("GAS LEAK DETECTED — EVACUATE IMMEDIATELY!")
            alarm_on()

            # Button to stop alarm
            if st.button("I have handled the situation"):
                gas_alarm_latched = False
                alerts["gas"] = False
                alarm_off()
                time.sleep(0.3)
                # Reset background color
                st.markdown(
                    """
                    <style>
                    body {
                        background-color: white;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )
        else:
            alarm_off()

    st_autorefresh(interval=2000)  
finally:
    GPIO.cleanup()
# -------------------------------------------------------------
