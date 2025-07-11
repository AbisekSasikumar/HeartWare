# SensoHealth
Comprehensive Health Monitoring System with environmental alerts, emergency ECG access, fall detection , pressure contextualization


Summary 4 lines
sensors used TRL-8 goals, setup steps

```  
SensoHealth
├── README.md
├── hardware/
│   ├── circuit_diagram.png
│   ├── pin_mapping.txt
│   └── components.list.md
├── firmware/
│   ├── src/
│   ├── firmware.ino / main.py
├── test_logs/
│   ├── csv_files
│   └── screenshots/
└── demo/
    └── demo_video.mp4
```
## 🔌 Circuit Connection & Pinout Table

| Sensor/Module | Function              | ESP32 Pin   | Notes                              |
|---------------|-----------------------|-------------|------------------------------------|
| **MAX30105**  | SDA (I2C Data)        | GPIO 21     | Shared I2C                         |
|               | SCL (I2C Clock)       | GPIO 22     | Shared I2C                         |
|               | VCC                   | 3.3V        | Use 3.3V only                      |
|               | GND                   | GND         | Common ground                      |
|               | INT (optional)        | GPIO 17     | Optional interrupt pin             |
| **DS18B20**   | Data                  | GPIO 4      | Add 4.7KΩ pull-up to 3.3V          |
|               | VCC                   | 3.3V        |                                    |
|               | GND                   | GND         |                                    |
| **MQ-135**    | Analog Output         | GPIO 34     | Read as voltage                    |
|               | VCC                   | 5V          | Needs 5V for heater                |
|               | GND                   | GND         |                                    |
| **ADXL345**   | SDA (I2C Data)        | GPIO 21     | Shared I2C with MAX30105           |
|               | SCL (I2C Clock)       | GPIO 22     | Shared I2C with MAX30105           |
|               | VCC                   | 3.3V        | Confirm 3.3V support               |
|               | GND                   | GND         |                                    |
|               | INT (optional)        | GPIO 16     | Fall detection trigger             |
| **AD8232**    | Analog ECG Output     | GPIO 35     | Use ADC1 pin only                  |
|               | LO+ / LO− (optional)  | GPIO 32/33  | For lead-off detection             |
|               | VCC                   | 3.3V        | Clean supply reduces noise         |
|               | GND                   | GND         |                                    |
| **BMP280**    | SDA (I2C Data)        | GPIO 21     | Same I2C bus, no conflict          |
|               | SCL (I2C Clock)       | GPIO 22     |                                    |
|               | VCC                   | 3.3V        | Confirm sensor variant             |
|               | GND                   | GND         |                                    |
| **Button**    | ECG Activation Input  | GPIO 18     | Use internal pull-up               |
| **Buzzer**    | Alert Sounder (PWM)   | GPIO 19     | Optional feedback                  |
| **LED**       | Status Indicator      | GPIO 2/25   | GPIO 2 has onboard LED (optional)  |

💰 **Total Cost:** *INR 1547*

# need to edit 
