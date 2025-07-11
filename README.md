# SensoHealth
Comprehensive Health Monitoring System with environmental alerts, emergency ECG access, fall detection , pressure contextualization

## Table of Contents

1. [Introduction](#1-introduction)  
2. [Repo Structure](#2-RepoStructure)  
3. [Components Required with Bill of Materials](#3-components-required-with-bill-of-materials)  
4. [Table for Pin Connections](#4-table-for-pin-connections)  
5. [Pinout Diagram](#5-pinout-diagram)  
6. [Working Code](#6-working-code)  
7. [Demo Images and Videos](#7-demo-images-and-videos)  
 
## 1. Introduction


## 2. RepoStructure

```  
SensoHealth
├── README.md
├── hardware/
│   ├── circuit_diagram.png
│   ├── pin_mapping.txt
│   └── components.list.md
├── firmware/
│   ├── src/
│   ├── main.py
├── test_logs/
│   ├── csv_files
│   └── screenshots/
└── demo/
    └── demo_video.mp4
```
## 3. Components with BOM


## 4. Pinout Table


| **ESP32 Pin** | **MAX30105**       | **DS18B20**     | **MQ-135**        | **ADXL345**          | **AD8232**              | **BMP280**         |
|---------------|--------------------|------------------|--------------------|------------------------|--------------------------|----------------------|
| GPIO 4        | –                  | **Data**         | –                  | –                      | –                        | –                    |
| GPIO 16       | –                  | –                | –                  | **INT (optional)**     | –                        | –                    |
| GPIO 17       | **INT (optional)** | –                | –                  | –                      | –                        | –                    |
| GPIO 21       | **SDA**            | –                | –                  | **SDA**                | –                        | **SDA**              |
| GPIO 22       | **SCL**            | –                | –                  | **SCL**                | –                        | **SCL**              |
| GPIO 32       | –                  | –                | –                  | –                      | **LO+**                 | –                    |
| GPIO 33       | –                  | –                | –                  | –                      | **LO−**                 | –                    |
| GPIO 34       | –                  | –                | **Analog Output**  | –                      | –                        | –                    |
| GPIO 35       | –                  | –                | –                  | –                      | **ECG Analog Output**   | –                    |
| 3.3V          | **VCC**            | **VCC**          | –                  | **VCC**                | **VCC**                 | **VCC**              |
| 5V            | –                  | –                | **VCC**            | –                      | –                        | –                    |
| GND           | **GND**            | **GND**          | **GND**            | **GND**                | **GND**                 | **GND**              |


## 5. Pinout diagram
![Circuit Diagram](hardware/circuit_diagram.png)
