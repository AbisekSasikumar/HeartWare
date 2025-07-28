import sys, time, csv
import serial
import numpy as np
import requests
import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QComboBox,
    QGroupBox, QStatusBar, QSplitter, QFrame
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QColor, QPalette

# === CONFIG ===
PORT = "COM3"       # ← Replace with your actual COM port
BAUD = 115200
CSV_FILE = "health_log.csv"
MAX_POINTS = 500
THEME_COLORS = {
    'dark_bg': '#1e1e2e',
    'light_bg': '#2a2a3a',
    'text': '#e0e0f0',
    'accent': '#5e9ae0',
    'critical': '#ff5555',
    'warning': '#ffb86c',
    'normal': '#50fa7b'
}

# Define practical ranges for sensor validation
SENSOR_RANGES = {
    "HR": (30, 250),          # Heart Rate (bpm)
    "SpO2": (70, 100),        # Blood Oxygen (%)
    "Temp": (30, 42),         # Body Temperature (°C)
    "Pressure": (900, 1100),  # Atmospheric Pressure (hPa)
    "Altitude": (-100, 9000), # Altitude (meters)
    "AccX": (-20, 20),        # Acceleration (g)
    "AccY": (-20, 20),
    "AccZ": (-20, 20),
    "MQ": (0, 5000),          # Air Quality (ppm)
    "ECG": (-5, 5)            # ECG (voltage)
}

# === SERIAL INIT ===
try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    print(f"✅ Connected to {PORT} at {BAUD} baud")
except Exception as e:
    print(f"❌ Serial error: {e}")
    sys.exit(1)

# === BUFFER ===
BUFFER = {
    "HR": [], "SpO2": [], "Temp": [], "Pressure": [],
    "Altitude": [], "AccX": [], "AccY": [], "AccZ": [],
    "MQ": [], "ECG": []
}

# Store last valid readings for each sensor
LAST_VALID = {
    "HR": 75, "SpO2": 98, "Temp": 36.6, "Pressure": 1013,
    "Altitude": 0, "AccX": 0, "AccY": 0, "AccZ": 0,
    "MQ": 0, "ECG": 0
}

# === SAFE FORECAST ===
def forecast(values, future=10):
    if len(values) < 5:
        return [0] * future
    try:
        y = np.array(values, dtype=float)
        if np.any(np.isnan(y)) or np.any(np.isinf(y)):
            return [values[-1]] * future
        if np.std(y) == 0:
            return [y[-1]] * future
        x = np.arange(len(y))
        coeffs = np.polyfit(x, y, 1)
        x_future = np.arange(len(y), len(y) + future)
        return coeffs[0] * x_future + coeffs[1]
    except Exception as e:
        print("⚠ Forecast error:", e)
        return [values[-1]] * future if values else [0] * future

# === ANALYTICAL FUNCTIONS ===
def detect_mood(hr, spo2, temp, ax, ay, az):
    acc = np.sqrt(ax*2 + ay2 + az*2)
    hr_var = np.std(BUFFER["HR"][-10:]) if len(BUFFER["HR"]) > 10 else 0
    
    if hr > 100 and acc > 2.5 and hr_var > 8:
        return ("Stressed", THEME_COLORS['critical'])
    if hr < 65 and spo2 > 97 and acc < 0.5 and hr_var < 3:
        return ("Relaxed", THEME_COLORS['normal'])
    if hr > 90 and spo2 < 94 and temp > 37.2:
        return ("Fatigued", THEME_COLORS['warning'])
    if acc > 3.0 and hr > 85:
        return ("Active", '#a0a0ff')
    return ("Neutral", THEME_COLORS['accent'])

def risk_index(temp, mq, pressure, hr, spo2):
    score = 0
    if temp > 37.5: score += 25
    if mq > 3000: score += 30
    if pressure < 980: score += 15
    if hr > 120 or hr < 50: score += 20
    if spo2 < 92: score += 25
    return min(max(score, 0), 100)

def detect_fall(ax, ay, az, hr):
    acc_mag = np.sqrt(ax*2 + ay2 + az*2)
    return acc_mag < 0.3 and (hr < 50 or hr > 140)

def calculate_trend(data):
    if len(data) < 2:
        return "stable"
    trend = data[-1] - data[-2]
    if abs(trend) < 0.1:
        return "stable"
    return "rising" if trend > 0 else "falling"

# === SENSOR VALIDATION ===
def validate_sensor_value(sensor, value):
    """Validate sensor reading against practical range"""
    min_val, max_val = SENSOR_RANGES[sensor]
    
    if min_val <= value <= max_val:
        LAST_VALID[sensor] = value
        return value
    else:
        print(f"⚠ Invalid {sensor} reading: {value:.1f} (using last valid: {LAST_VALID[sensor]:.1f})")
        return LAST_VALID[sensor]

# === VITAL INDICATOR WIDGET ===
class VitalIndicator(QLabel):
    def _init_(self, title, unit, normal_range, parent=None):
        super()._init_(parent)
        self.title = title
        self.unit = unit
        self.normal_range = normal_range
        self.value = 0
        self.setMinimumWidth(120)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            border-radius: 8px;
            padding: 8px;
            background: """ + THEME_COLORS['light_bg'] + """;
            font-weight: bold;
        """)
        self.update_display()
        
    def update_value(self, value):
        self.value = value
        self.update_display()
        
    def update_display(self):
        # Handle invalid values
        if self.value is None or np.isnan(self.value) or np.isinf(self.value):
            self.setText(
                f"<b><font size='5' color='{THEME_COLORS['warning']}'>N/A</font></b>"
                f"<br><font size='4'>-</font>"
                f"<br><font size='3' color='#a0a0a0'>{self.title}</font>"
            )
            return
            
        color = THEME_COLORS['normal']
        if self.normal_range:
            low, high = self.normal_range
            if not (low <= self.value <= high):
                color = THEME_COLORS['critical']
            elif not (low * 1.1 <= self.value <= high * 0.9):
                color = THEME_COLORS['warning']
                
        trend = calculate_trend(BUFFER.get(self.title, []))
        trend_symbol = "→" if trend == "stable" else "↑" if trend == "rising" else "↓"
        
        self.setText(
            f"<b><font size='5' color='{color}'>{self.value:.1f}</font></b>"
            f"<br><font size='4'>{trend_symbol} {self.unit}</font>"
            f"<br><font size='3' color='#a0a0a0'>{self.title}</font>"
        )

# === MAIN DASHBOARD ===
class HealthDashboard(QMainWindow):
    def _init_(self):
        super()._init_()
        self.setWindowTitle("Senso Health Analytics")
        self.setGeometry(100, 100, 1400, 800)
        
        # Apply dark theme
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {THEME_COLORS['dark_bg']};
                color: {THEME_COLORS['text']};
                font-family: 'Segoe UI', Arial;
            }}
            QGroupBox {{
                border: 1px solid {THEME_COLORS['accent']};
                border-radius: 8px;
                margin-top: 1ex;
                font-size: 10pt;
                font-weight: bold;
                color: {THEME_COLORS['accent']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QComboBox {{
                background: {THEME_COLORS['light_bg']};
                padding: 5px;
                border-radius: 4px;
            }}
            QPushButton {{
                background: {THEME_COLORS['accent']};
                color: white;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: #6ea6f0;
            }}
        """)
        
        # Central layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setFont(QFont("Segoe UI", 9))
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("System ready. Waiting for data...")
        
        # Create header
        header_layout = QHBoxLayout()
        
        title = QLabel("SensoHealth - Monitoring System")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet(f"color: {THEME_COLORS['accent']}; padding: 10px;")
        
        # Export button
        self.export_btn = QPushButton("Export Data to CSV")
        self.export_btn.setFont(QFont("Segoe UI", 8))
        self.export_btn.clicked.connect(self.export_data)
        self.export_btn.setFixedWidth(150)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.export_btn)
        
        main_layout.addLayout(header_layout)
        
        # Create horizontal splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Metrics and alerts
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(15)
        
        # Vital metrics group
        metrics_group = QGroupBox("Vital Metrics")
        metrics_layout = QGridLayout()
        metrics_group.setLayout(metrics_layout)
        
        # Create vital indicators
        self.indicators = {
            "HR": VitalIndicator("HR", "bpm", (60, 100)),
            "SpO2": VitalIndicator("SpO2", "%", (95, 100)),
            "Temp": VitalIndicator("Temp", "°C", (36.0, 37.5)),
            "Pressure": VitalIndicator("Pressure", "hPa", (980, 1030)),
            "Altitude": VitalIndicator("Altitude", "m", None),
            "MQ": VitalIndicator("MQ", "ppm", (0, 2000))
        }
        
        # Position indicators
        metrics_layout.addWidget(self.indicators["HR"], 0, 0)
        metrics_layout.addWidget(self.indicators["SpO2"], 0, 1)
        metrics_layout.addWidget(self.indicators["Temp"], 1, 0)
        metrics_layout.addWidget(self.indicators["Pressure"], 1, 1)
        metrics_layout.addWidget(self.indicators["Altitude"], 2, 0)
        metrics_layout.addWidget(self.indicators["MQ"], 2, 1)
        
        left_layout.addWidget(metrics_group)
        
        # Mood and risk group
        status_group = QGroupBox("Status Analysis")
        status_layout = QVBoxLayout()
        status_group.setLayout(status_layout)
        
        # Mood display
        self.mood_display = QLabel("<b>Emotional Status:</b> Analyzing...")
        self.mood_display.setFont(QFont("Segoe UI", 12))
        self.mood_display.setAlignment(Qt.AlignCenter)
        self.mood_display.setStyleSheet("""
            background: """ + THEME_COLORS['light_bg'] + """;
            border-radius: 8px;
            padding: 15px;
        """)
        status_layout.addWidget(self.mood_display)
        
        # Risk display
        self.risk_display = QLabel("<b>Risk Index:</b> Calculating...")
        self.risk_display.setFont(QFont("Segoe UI", 12))
        self.risk_display.setAlignment(Qt.AlignCenter)
        self.risk_display.setStyleSheet("""
            background: """ + THEME_COLORS['light_bg'] + """;
            border-radius: 8px;
            padding: 15px;
        """)
        status_layout.addWidget(self.risk_display)
        
        left_layout.addWidget(status_group)
        
        # Alerts group
        alerts_group = QGroupBox("Alerts & Forecast")
        alerts_layout = QVBoxLayout()
        alerts_group.setLayout(alerts_layout)
        
        self.alert_display = QLabel("No critical alerts")
        self.alert_display.setFont(QFont("Segoe UI", 10))
        self.alert_display.setWordWrap(True)
        self.alert_display.setStyleSheet("""
            background: """ + THEME_COLORS['light_bg'] + """;
            border-radius: 8px;
            padding: 15px;
            min-height: 80px;
        """)
        alerts_layout.addWidget(self.alert_display)
        
        # Forecast display
        self.forecast_display = QLabel("Forecast data will appear here")
        self.forecast_display.setFont(QFont("Segoe UI", 10))
        self.forecast_display.setWordWrap(True)
        self.forecast_display.setStyleSheet("""
            background: """ + THEME_COLORS['light_bg'] + """;
            border-radius: 8px;
            padding: 15px;
            min-height: 80px;
        """)
        alerts_layout.addWidget(self.forecast_display)
        
        left_layout.addWidget(alerts_group)
        
        # Right panel - Visualization
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(15)
        
        # Plot selection
        plot_select_layout = QHBoxLayout()
        self.plot_select = QComboBox()
        self.plot_select.addItems(BUFFER.keys())
        self.plot_select.setCurrentIndex(0)
        plot_select_layout.addWidget(QLabel("Select Visualization:"))
        plot_select_layout.addWidget(self.plot_select)
        plot_select_layout.addStretch()
        right_layout.addLayout(plot_select_layout)
        
        # Main plot
        self.plot = pg.PlotWidget()
        self.plot.setBackground(THEME_COLORS['light_bg'])
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.setTitle("Vital Signs Visualization", color='w', size='14pt')
        
        # Create a color gradient for the plot
        gradient = pg.ColorMap(
            [0, 0.5, 1], 
            [
                QColor(94, 154, 224), 
                QColor(161, 129, 224), 
                QColor(224, 86, 138)
            ]
        ).getLookupTable()
        
        self.curve = self.plot.plot(pen=pg.mkPen('#5e9ae0', width=3))
        self.fill = pg.FillBetweenItem(
            self.curve, 
            pg.PlotDataItem(),
            brush=pg.mkBrush(QColor(94, 154, 224, 80))
        )
        self.plot.addItem(self.fill)
        
        right_layout.addWidget(self.plot)
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([500, 900])
        
        # Setup timers
        self.serial_timer = QTimer()
        self.serial_timer.timeout.connect(self.read_serial)
        self.serial_timer.start(100)
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_dashboard)
        self.update_timer.start(500)
        
        self.last_alert = ""
        self.fall_detected = False
        self.sensor_error_count = 0
        
    def read_serial(self):
        try:
            if ser.in_waiting:
                line = ser.readline().decode().strip()
                if not line.startswith("PYTHON->"): 
                    return
                    
                raw_values = line.replace("PYTHON->", "").split(",")
                if len(raw_values) != 10: 
                    return
                
                # Validate and process sensor values
                validated_values = []
                keys = list(BUFFER.keys())
                
                for i, raw_val in enumerate(raw_values):
                    try:
                        value = float(raw_val)
                        sensor = keys[i]
                        
                        # Validate against practical range
                        min_val, max_val = SENSOR_RANGES[sensor]
                        if min_val <= value <= max_val:
                            validated_values.append(value)
                            LAST_VALID[sensor] = value
                        else:
                            # Use last valid value if current is out of range
                            validated_values.append(LAST_VALID[sensor])
                            self.sensor_error_count += 1
                            self.status_bar.showMessage(
                                f"Sensor error: {sensor} value {value} out of range. Using {LAST_VALID[sensor]}"
                            )
                    except ValueError:
                        # Handle conversion errors
                        validated_values.append(LAST_VALID[keys[i]])
                        self.sensor_error_count += 1
                        self.status_bar.showMessage(
                            f"Conversion error for {keys[i]}. Using last valid value"
                        )
                
                # Update buffers with validated values
                for i in range(10):
                    BUFFER[keys[i]].append(validated_values[i])
                    if len(BUFFER[keys[i]]) > MAX_POINTS:
                        BUFFER[keys[i]].pop(0)
                
                # Save to CSV with both raw and validated values
                with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S")] + 
                                   raw_values + 
                                   [str(v) for v in validated_values])
                    
                self.status_bar.showMessage(
                    f"Last update: {time.strftime('%H:%M:%S')} | "
                    f"Points: {len(BUFFER['HR'])} | "
                    f"Errors: {self.sensor_error_count}"
                )
                
        except Exception as e:
            self.status_bar.showMessage(f"Serial error: {str(e)}")
    
    def update_dashboard(self):
        if not BUFFER["HR"]:
            return
            
        try:
            # Get latest validated values
            hr = BUFFER["HR"][-1]
            spo2 = BUFFER["SpO2"][-1]
            temp = BUFFER["Temp"][-1]
            pres = BUFFER["Pressure"][-1]
            alt = BUFFER["Altitude"][-1]
            mq = BUFFER["MQ"][-1]
            ax = BUFFER["AccX"][-1]
            ay = BUFFER["AccY"][-1]
            az = BUFFER["AccZ"][-1]
            ecg = BUFFER["ECG"][-1]
            
            # Update indicators
            self.indicators["HR"].update_value(hr)
            self.indicators["SpO2"].update_value(spo2)
            self.indicators["Temp"].update_value(temp)
            self.indicators["Pressure"].update_value(pres)
            self.indicators["Altitude"].update_value(alt)
            self.indicators["MQ"].update_value(mq)
            
            # Update mood
            mood, mood_color = detect_mood(hr, spo2, temp, ax, ay, az)
            self.mood_display.setText(
                f"<b>Emotional Status:</b>"
                f"<br><font size='5' color='{mood_color}'>{mood}</font>"
            )
            
            # Update risk
            risk = risk_index(temp, mq, pres, hr, spo2)
            risk_color = THEME_COLORS['normal']
            if risk > 60:
                risk_color = THEME_COLORS['critical']
            elif risk > 30:
                risk_color = THEME_COLORS['warning']
                
            self.risk_display.setText(
                f"<b>Risk Index:</b>"
                f"<br><font size='5' color='{risk_color}'>{risk:.0f}/100</font>"
            )
            
            # Check for alerts
            alert_text = "No critical alerts"
            alert_style = f"color: {THEME_COLORS['normal']};"
            
            if detect_fall(ax, ay, az, hr) and not self.fall_detected:
                self.fall_detected = True
                self.last_alert = f"🚨 FALL DETECTED! At {time.strftime('%H:%M:%S')}"
                # Send emergency notification (simulated)
                try:
                    requests.post("https://api.emergency.com/alert", 
                                 json={"message": "Fall detected!", "priority": "critical"})
                except:
                    pass
                
            if self.fall_detected:
                alert_text = self.last_alert
                alert_style = f"background-color: #ff5555; color: white; font-weight: bold;"
                
            elif temp > 38.0:
                alert_text = f"⚠ HIGH TEMPERATURE: {temp:.1f}°C"
                alert_style = f"color: {THEME_COLORS['warning']};"
                
            elif spo2 < 92:
                alert_text = f"⚠ LOW OXYGEN: SpO2 at {spo2:.1f}%"
                alert_style = f"color: {THEME_COLORS['critical']};"
                
            elif hr > 120:
                alert_text = f"⚠ HIGH HEART RATE: {hr:.0f} bpm"
                alert_style = f"color: {THEME_COLORS['critical']};"
                
            self.alert_display.setText(alert_text)
            self.alert_display.setStyleSheet(f"""
                background: {THEME_COLORS['light_bg']};
                border-radius: 8px;
                padding: 15px;
                {alert_style}
            """)
            
            # Update forecast
            f_temp = forecast(BUFFER["Temp"])[-1]
            f_pres = forecast(BUFFER["Pressure"])[-1]
            f_mq = forecast(BUFFER["MQ"])[-1]
            
            self.forecast_display.setText(
                "<b>10-min Forecast:</b><br>"
                f"Temperature: {f_temp:.1f}°C<br>"
                f"Pressure: {f_pres:.1f} hPa<br>"
                f"Air Quality: {f_mq:.0f} ppm"
            )
            
            # Update plots
            current_vital = self.plot_select.currentText()
            data = BUFFER[current_vital]
            self.curve.setData(data)
            self.plot.setTitle(f"{current_vital} Signal", color='w')
            
        except Exception as e:
            print("Dashboard update error:", e)
            
    def export_data(self):
        """Export current buffer data to CSV"""
        try:
            filename = f"health_export_{time.strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                # Write header
                writer.writerow(['Timestamp'] + list(BUFFER.keys()))
                
                # Determine number of data points (all buffers should be same length)
                n = len(BUFFER["HR"])
                
                # Create timestamps (relative to now)
                timestamps = [f"{-i}s" for i in range(n, 0, -1)]
                
                # Write data
                for i in range(n):
                    row = [timestamps[i]]
                    for key in BUFFER:
                        if i < len(BUFFER[key]):
                            row.append(BUFFER[key][i])
                        else:
                            row.append('')
                    writer.writerow(row)
                    
            self.status_bar.showMessage(f"Exported {n} data points to {filename}", 5000)
        except Exception as e:
            self.status_bar.showMessage(f"Export failed: {str(e)}", 5000)

# === MAIN ===
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(THEME_COLORS['dark_bg']))
    palette.setColor(QPalette.WindowText, QColor(THEME_COLORS['text']))
    app.setPalette(palette)
    
    # Create and show dashboard
    dashboard = HealthDashboard()
    dashboard.show()
    
    sys.exit(app.exec_())