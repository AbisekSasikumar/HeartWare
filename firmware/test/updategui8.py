import ttkbootstrap as tb
from ttkbootstrap.constants import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import serial
import threading
import time
import csv
from tkinter import filedialog, messagebox

SENSOR_KEYS = ['Heart Rate', 'SpO2', 'Temp (\u00b0C)', 'Pressure (hPa)', 'Altitude (m)', 'Acc X', 'Acc Y', 'Acc Z', 'Air Quality']

class SerialReader:
    def __init__(self, port='COM3', baudrate=115200):
        self.ser = serial.Serial(port, baudrate, timeout=1)
        self.running = True
        self.lock = threading.Lock()
        self.data = []
        self.timestamps = []

    def start(self):
        threading.Thread(target=self.read_loop, daemon=True).start()

    def stop(self):
        self.running = False
        self.ser.close()

    def read_loop(self):
        while self.running:
            try:
                line = self.ser.readline().decode(errors='ignore').strip()
                if line.startswith("PYTHON->"):
                    values = list(map(float, line.split("->")[1].split(",")))
                    if len(values) == len(SENSOR_KEYS):
                        with self.lock:
                            self.data.append(values)
                            self.timestamps.append(time.time())
            except:
                continue

    def get_all_data(self):
        with self.lock:
            return self.timestamps[:], self.data[:]


class SensorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SensoHealth - ESP32 Real-Time Sensor Dashboard")
        self.serial_reader = SerialReader()
        self.serial_reader.start()

        self.selected_sensor = tb.StringVar(value=SENSOR_KEYS[0])
        self.selected_range = tb.StringVar(value="1 min")

        self.create_widgets()
        self.update_loop()

    def create_widgets(self):
        tb.Label(self.root, text="SensoHealth", font=("Segoe UI", 24, "bold"), bootstyle="info").pack(pady=10)

        # Top Gauges
        self.meter_frame = tb.Frame(self.root)
        self.meter_frame.pack(fill='x', padx=10, pady=10)

        self.hr_meter = tb.Meter(self.meter_frame, bootstyle="danger", subtext="Heart Rate (bpm)",
                                 metertype="semi", amounttotal=200, amountused=0, interactive=False)
        self.hr_meter.pack(side='left', padx=20)

        self.spo2_meter = tb.Meter(self.meter_frame, bootstyle="success", subtext="SpO₂ (%)",
                                   metertype="semi", amounttotal=100, amountused=0, interactive=False)
        self.spo2_meter.pack(side='left', padx=20)

        self.temp_meter = tb.Meter(self.meter_frame, bootstyle="warning", subtext="Temp (°C)",
                                   metertype="semi", amounttotal=45, amountused=0, interactive=False)
        self.temp_meter.pack(side='left', padx=20)

        # Altitude and Pressure in a Frame
        self.info_card = tb.LabelFrame(self.root, text="Environment Data", bootstyle="primary")
        self.info_card.pack(pady=10, padx=10, fill='x')

        self.altitude_label = tb.Label(self.info_card, text="Altitude: -- m", font=("Segoe UI", 12))
        self.altitude_label.pack(side='left', padx=20, pady=5)

        self.pressure_label = tb.Label(self.info_card, text="Pressure: -- hPa", font=("Segoe UI", 12))
        self.pressure_label.pack(side='left', padx=20, pady=5)

        # Controls
        self.ctrl_frame = tb.Frame(self.root)
        self.ctrl_frame.pack(fill='x', padx=10, pady=5)

        tb.Label(self.ctrl_frame, text="Sensor:").grid(row=0, column=0, padx=5)
        self.sensor_dropdown = tb.Combobox(self.ctrl_frame, values=SENSOR_KEYS, textvariable=self.selected_sensor)
        self.sensor_dropdown.grid(row=0, column=1, padx=5)

        tb.Label(self.ctrl_frame, text="Time Range:").grid(row=0, column=2, padx=5)
        self.range_dropdown = tb.Combobox(self.ctrl_frame, values=["1 min", "5 min", "Full"], textvariable=self.selected_range)
        self.range_dropdown.grid(row=0, column=3, padx=5)

        self.save_button = tb.Button(self.ctrl_frame, text="💾 Export CSV", command=self.save_csv, bootstyle="primary")
        self.save_button.grid(row=0, column=4, padx=10)

        # Plot Frame
        self.plot_frame = tb.LabelFrame(self.root, text="📈 Live Sensor Plot", bootstyle="info")
        self.plot_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.fig, self.ax = plt.subplots(figsize=(6, 3))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        self.plot_line, = self.ax.plot([], [], label=self.selected_sensor.get())
        self.ax.legend()

    def update_loop(self):
        ts, data = self.serial_reader.get_all_data()
        sensor = self.selected_sensor.get()
        if data:
            idx = SENSOR_KEYS.index(sensor)
            now = time.time()
            range_sec = {"1 min": 60, "5 min": 300, "Full": float("inf")}[self.selected_range.get()]
            filtered = [(t, d[idx]) for t, d in zip(ts, data) if now - t <= range_sec]

            if filtered:
                x_vals = [t - filtered[0][0] for t, _ in filtered]
                y_vals = [v for _, v in filtered]

                self.plot_line.set_data(x_vals, y_vals)
                self.ax.set_xlim(max(0, x_vals[-1] - range_sec), x_vals[-1] + 1)
                self.ax.set_ylim(min(y_vals) - 5, max(y_vals) + 5)
                self.ax.set_title(f"{sensor} over Time ({self.selected_range.get()})")
                self.ax.set_xlabel("Time (s)")
                self.ax.set_ylabel(sensor)
                self.ax.legend([sensor])
                self.canvas.draw()

                latest = data[-1]
                hr = latest[SENSOR_KEYS.index("Heart Rate")]
                spo2 = latest[SENSOR_KEYS.index("SpO2")]
                temp = latest[SENSOR_KEYS.index("Temp (°C)")]
                alt = latest[SENSOR_KEYS.index("Altitude (m)")]
                pres = latest[SENSOR_KEYS.index("Pressure (hPa)")]

                self.hr_meter.configure(amountused=hr)
                self.spo2_meter.configure(amountused=spo2)
                self.temp_meter.configure(amountused=temp)
                self.altitude_label.configure(text=f"Altitude: {alt:.1f} m")
                self.pressure_label.configure(text=f"Pressure: {pres:.1f} hPa")

                self.check_alerts(latest)

        self.root.after(1000, self.update_loop)

    def check_alerts(self, latest_data):
        alerts = []
        hr = latest_data[SENSOR_KEYS.index("Heart Rate")]
        spo2 = latest_data[SENSOR_KEYS.index("SpO2")]
        temp = latest_data[SENSOR_KEYS.index("Temp (°C)")]

        if hr < 50 or hr > 120:
            alerts.append(f"⚠️ Abnormal Heart Rate: {hr:.1f} bpm")
        if spo2 < 90:
            alerts.append(f"⚠️ Low SpO₂: {spo2:.1f}%")
        if temp > 38.0:
            alerts.append(f"🌡️ High Temperature: {temp:.1f}°C")

        for alert in alerts:
            self.show_alert(alert)

    def show_alert(self, message):
        if not hasattr(self, "last_alert_time"):
            self.last_alert_time = 0
        if time.time() - self.last_alert_time > 10:
            self.last_alert_time = time.time()
            messagebox.showwarning("Sensor Alert", message)

    def save_csv(self):
        ts, data = self.serial_reader.get_all_data()
        if not data:
            messagebox.showinfo("No Data", "No sensor data to save.")
            return

        now = time.time()
        range_sec = {"1 min": 60, "5 min": 300, "Full": float("inf")}[self.selected_range.get()]
        filtered_rows = [(t, d) for t, d in zip(ts, data) if now - t <= range_sec]

        if not filtered_rows:
            messagebox.showinfo("No Data", "No data in selected time range.")
            return

        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV File", "*.csv")])
        if not filepath:
            return

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp"] + SENSOR_KEYS)
            for t, row in filtered_rows:
                writer.writerow([time.strftime('%H:%M:%S', time.localtime(t))] + row)

        messagebox.showinfo("Exported", f"CSV saved to:\n{filepath}")

    def on_close(self):
        self.serial_reader.stop()
        self.root.destroy()


if __name__ == '__main__':
    root = tb.Window(themename="flatly")
    app = SensorGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
