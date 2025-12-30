# Indoor Air Quality Monitoring System

## Description

A multithreaded IoT project for Nile University of Egypt’s CSCI410: Introduction to IoT course, by Mazen Ahmed Sayed El-Mallah (ID no. 231000137).
The project monitors indoor air quality in real time using multiple sensors.

The system uses three sensors:

* DHT22 -> Temperature & Humidity
* MQ-135 -> Air Quality / CO₂
* PMS7003 -> PM2.5

It provides a live web dashboard via Streamlit, AI-based trend alerts, and logs data to `iaq_log.csv`.

## Setup

1. Connect the sensors to the Raspberry Pi:

   * DHT22 -> GPIO 4
   * MQ-135 -> GPIO 17
   * PMS7003 -> GPIO 27

2. Install dependencies:

```bash
pip install Adafruit_DHT RPi.GPIO streamlit
```

3. Save the Python file as `iaq_monitor.py`.

## Running

```bash
streamlit run iaq_monitor.py
```

* Open the URL printed by Streamlit (usually `http://localhost:8501`) to view the dashboard.
* The system automatically runs three threads:

  1. Sensor readings
  2. AI predictions & alerts
  3. Data logging

## Dashboard

Displays live values for: Temperature, Humidity, Air Quality Alert, PM2.5 Alert.

## Block Diagram

<img width="521" height="321" alt="IoT drawio" src="https://github.com/user-attachments/assets/207c1beb-f2c4-4291-a6c2-91182a77d0ba" />

## Sources

The following sources were used to code the project. I included all research material here so anyone with no knowledge of the functionings of GPIO, Python multithreading, Streamlit, or how to use a RaspberryPi for projects, could self-learn by using these as a starting point.

Raspberry Pi Projects: Physical Computing with Python - https://projects.raspberrypi.org/en/projects/physical-computing/

Official Python Documentation: Threading - https://docs.python.org/3/library/threading.html#module-threading/

Instructables: Raspberry Pi GPIO Python - https://www.instructables.com/Raspberry-Pi-Python-scripting-the-GPIO/

Learn Streamlit Tutorials - https://streamlitpython.com/

Random Nerd Tutorials: Raspberry Pi Projects - https://randomnerdtutorials.com/projects-raspberry-pi/

SparkFun Python GPIO Tutorial - https://learn.sparkfun.com/tutorials/python-programming-tutorial-getting-started-with-the-raspberry-pi/

Jeremy Morgan Adafruit IoT with Raspberry Pi - https://www.jeremymorgan.com/tutorials/raspberry-pi/how-to-iot-adafruit-raspberrypi/
