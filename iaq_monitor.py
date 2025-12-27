import Adafruit_DHT
import RPi.GPIO as GPIO
import threading
import csv
import time
import streamlit as st
import pandas as pd
from collections import deque

# ---------------- GPIO SETUP ----------------
GPIO.setmode(GPIO.BCM)

DHT_PIN = 4
MQ135_PIN = 17
MQ5_PIN = 27
BUZZER_PIN = 22
LED_PIN = 23

GPIO.setup(MQ135_PIN, GPIO.IN)
GPIO.setup(MQ5_PIN, GPIO.IN)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.setup(LED_PIN, GPIO.OUT)

# ---------------- SHARED DATA ----------------
sensor_data = {
    'temperature': None,
    'humidity': None,
    'air_quality_alert': 0,
    'gas_leak_alert': 0
}

history = deque(maxlen=25)
data_lock = threading.Lock()  # for thread-safe access

gas_alarm_latched = False

# ---------------- SENSOR FUNCTIONS ----------------
def read_dht22():
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, DHT_PIN)
    return {'temperature': temperature, 'humidity': humidity}

def read_mq135():
    return {'air_quality_alert': GPIO.input(MQ135_PIN)}

def read_mq5():
    return {'gas_leak_alert': GPIO.input(MQ5_PIN)}

# ---------------- THREADS ----------------
def sensor_thread():
    while True:
        dht = read_dht22()
        mq135 = read_mq135()
        mq5 = read_mq5()
        with data_lock:
            sensor_data.update(dht)
            sensor_data.update(mq135)
            sensor_data.update(mq5)
            history.append(sensor_data.copy())
        time.sleep(2)

def logging_thread():
    with open("iaq_log.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "temperature", "humidity", "air_quality_alert", "gas_leak_alert"])
        while True:
            with data_lock:
                temp = sensor_data['temperature'] or 0
                humidity = sensor_data['humidity'] or 0
                air = sensor_data['air_quality_alert']
                gas = sensor_data['gas_leak_alert']
            writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), temp, humidity, air, gas])
            f.flush()
            time.sleep(5)

# ---------------- ALARM FUNCTIONS ----------------
def alarm_on():
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    GPIO.output(LED_PIN, GPIO.HIGH)

def alarm_off():
    GPIO.output(BUZZER_PIN, GPIO.LOW)
    GPIO.output(LED_PIN, GPIO.LOW)

# ---------------- START THREADS ----------------
threading.Thread(target=sensor_thread, daemon=True).start()
threading.Thread(target=logging_thread, daemon=True).start()

# ---------------- STREAMLIT DASHBOARD ----------------
st.set_page_config(page_title="Indoor Air Quality Dashboard")
st.title("Indoor Air Quality Monitoring")

# Placeholders for metrics
temp_display = st.empty()
humidity_display = st.empty()
air_alert_display = st.empty()
gas_display = st.empty()
chart_container = st.container()
alerts_container = st.container()

# Auto-refresh every 2 seconds
st_autorefresh = st.experimental_rerun
st_autorefresh(interval=2000)

# ---------------- DISPLAY ----------------
with data_lock:
    temp = sensor_data['temperature']
    humidity = sensor_data['humidity']
    air = sensor_data['air_quality_alert']
    gas = sensor_data['gas_leak_alert']
    df = pd.DataFrame(list(history))

# Display metrics
temp_display.metric("Temperature", f"{temp} °C" if temp is not None else "N/A")
humidity_display.metric("Humidity", f"{humidity} %" if humidity is not None else "N/A")
air_alert_display.metric("Air Quality Alert", air)
gas_display.metric("Gas Leak Alert", gas)

# Display chart
if not df.empty:
    chart_container.line_chart(df[['temperature', 'humidity', 'gas_leak_alert']])

# Display alerts
with alerts_container:
    if temp is not None and temp > 30:
        st.warning("Temperature is high! Turn on a fan or improve ventilation.")
    if humidity is not None and humidity > 70:
        st.warning("Humidity is high! Consider ventilation or a dehumidifier.")
    if air == 1:
        st.warning("Air quality is poor! Open a window and point a fan toward it.")

    # Gas leak handling
    if gas == 1:
        gas_alarm_latched = True

    if gas_alarm_latched:
        st.markdown("<style>body {background-color: #8B0000;}</style>", unsafe_allow_html=True)
        st.error("GAS LEAK DETECTED — EVACUATE IMMEDIATELY!")
        alarm_on()
        if st.button("I have handled the situation"):
            gas_alarm_latched = False
            alarm_off()
            st.markdown("<style>body {background-color: white;}</style>", unsafe_allow_html=True)
    else:
        alarm_off()
