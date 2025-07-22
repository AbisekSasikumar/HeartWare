import ttkbootstrap as tb
from ttkbootstrap.constants import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import serial
import threading
import time
import csv
from tkinter import filedialog, messagebox
import numpy as np
from matplotlib.patches import Circle, Rectangle
from mpl_toolkits.mplot3d import Axes3D

SENSOR_KEYS = ['Heart Rate (bpm)', 'SpO₂ (%)', 'Temp (°C)', 'Pressure (hPa)', 'Altitude (m)', 
               'Acc X', 'Acc Y', 'Acc Z', 'Air Quality (ppm)']

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
        self.visualization_mode = tb.StringVar(value="Default")  # For switching views

        self.create_widgets()
        self.update_loop()

    def create_widgets(self):
        tb.Label(self.root, text="SensoHealth", font=("Segoe UI", 24, "bold"), bootstyle="info").pack(pady=10)

        # Top Gauges Frame
        self.meter_frame = tb.Frame(self.root)
        self.meter_frame.pack(fill='x', padx=10, pady=10)

        # Heart Rate Visualization
        self.hr_frame = tb.LabelFrame(self.meter_frame, text="Heart Rate", bootstyle="danger")
        self.hr_frame.pack(side='left', expand=True, fill='both', padx=5)
        self.hr_meter = tb.Meter(self.hr_frame, bootstyle="danger", subtext="(bpm)",
                                 metertype="semi", amounttotal=200, amountused=0, interactive=False)
        self.hr_meter.pack(pady=5)
        self.hr_beat = tb.Label(self.hr_frame, text="💓", font=("Segoe UI", 24))
        self.hr_beat.pack()

        # SpO2 Visualization
        self.spo2_frame = tb.LabelFrame(self.meter_frame, text="SpO₂", bootstyle="success")
        self.spo2_frame.pack(side='left', expand=True, fill='both', padx=5)
        self.spo2_meter = tb.Meter(self.spo2_frame, bootstyle="success", subtext="(%)",
                                   metertype="semi", amounttotal=100, amountused=0, interactive=False)
        self.spo2_meter.pack(pady=5)
        self.spo2_pulse = tb.Label(self.spo2_frame, text="🫀", font=("Segoe UI", 24))
        self.spo2_pulse.pack()

        # Temperature Visualization
        self.temp_frame = tb.LabelFrame(self.meter_frame, text="Temperature", bootstyle="warning")
        self.temp_frame.pack(side='left', expand=True, fill='both', padx=5)
        self.temp_meter = tb.Meter(self.temp_frame, bootstyle="warning", subtext="(°C)",
                                   metertype="semi", amounttotal=45, amountused=0, interactive=False)
        self.temp_meter.pack(pady=5)
        self.temp_icon = tb.Label(self.temp_frame, text="🌡️", font=("Segoe UI", 24))
        self.temp_icon.pack()

        # Environment Data Frame
        self.env_frame = tb.Frame(self.root)
        self.env_frame.pack(pady=10, padx=10, fill='x')

        # Air Quality Visualization
        self.aq_frame = tb.LabelFrame(self.env_frame, text="Air Quality", bootstyle="primary")
        self.aq_frame.pack(side='left', expand=True, fill='both', padx=5)
        self.aq_label = tb.Label(self.aq_frame, text="-- ppm", font=("Segoe UI", 14))
        self.aq_label.pack(pady=5)
        self.aq_status = tb.Label(self.aq_frame, text="😊", font=("Segoe UI", 24))
        self.aq_status.pack()

        # Pressure Visualization
        self.pressure_frame = tb.LabelFrame(self.env_frame, text="Pressure", bootstyle="primary")
        self.pressure_frame.pack(side='left', expand=True, fill='both', padx=5)
        self.pressure_label = tb.Label(self.pressure_frame, text="-- hPa", font=("Segoe UI", 14))
        self.pressure_label.pack(pady=5)
        self.pressure_icon = tb.Label(self.pressure_frame, text="⏱️", font=("Segoe UI", 24))
        self.pressure_icon.pack()

        # Altitude Visualization
        self.altitude_frame = tb.LabelFrame(self.env_frame, text="Altitude", bootstyle="primary")
        self.altitude_frame.pack(side='left', expand=True, fill='both', padx=5)
        self.altitude_label = tb.Label(self.altitude_frame, text="-- m", font=("Segoe UI", 14))
        self.altitude_label.pack(pady=5)
        self.altitude_icon = tb.Label(self.altitude_frame, text="✈️", font=("Segoe UI", 24))
        self.altitude_icon.pack()

        # Accelerometer Visualization
        self.accel_frame = tb.LabelFrame(self.env_frame, text="Accelerometer", bootstyle="primary")
        self.accel_frame.pack(side='left', expand=True, fill='both', padx=5)
        self.accel_label = tb.Label(self.accel_frame, text="X: --\nY: --\nZ: --", font=("Courier", 12))
        self.accel_label.pack(pady=5)

        # Controls Frame
        self.ctrl_frame = tb.Frame(self.root)
        self.ctrl_frame.pack(fill='x', padx=10, pady=5)

        tb.Label(self.ctrl_frame, text="Sensor:").grid(row=0, column=0, padx=5)
        self.sensor_dropdown = tb.Combobox(self.ctrl_frame, values=SENSOR_KEYS, textvariable=self.selected_sensor)
        self.sensor_dropdown.grid(row=0, column=1, padx=5)

        tb.Label(self.ctrl_frame, text="Time Range:").grid(row=0, column=2, padx=5)
        self.range_dropdown = tb.Combobox(self.ctrl_frame, values=["1 min", "5 min", "Full"], textvariable=self.selected_range)
        self.range_dropdown.grid(row=0, column=3, padx=5)

        tb.Label(self.ctrl_frame, text="View:").grid(row=0, column=4, padx=5)
        self.view_dropdown = tb.Combobox(self.ctrl_frame, values=["Default", "3D View", "Radial View"], textvariable=self.visualization_mode)
        self.view_dropdown.grid(row=0, column=5, padx=5)

        self.save_button = tb.Button(self.ctrl_frame, text="💾 Export CSV", command=self.save_csv, bootstyle="primary")
        self.save_button.grid(row=0, column=6, padx=10)

        # Plot Frame
        self.plot_frame = tb.LabelFrame(self.root, text="📈 Live Sensor Plot", bootstyle="info")
        self.plot_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.fig, self.ax = plt.subplots(figsize=(6, 3))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        self.plot_line, = self.ax.plot([], [], label=self.selected_sensor.get())
        self.ax.legend()

        # For 3D visualization
        self.fig_3d = plt.figure(figsize=(6, 3))
        self.ax_3d = self.fig_3d.add_subplot(111, projection='3d')
        self.cube = self.create_3d_cube()
        self.canvas_3d = FigureCanvasTkAgg(self.fig_3d, master=self.plot_frame)

    def create_3d_cube(self):
        # Create a 3D cube for accelerometer visualization
        r = [-1, 1]
        X, Y = np.meshgrid(r, r)
        one = np.ones(4).reshape(2, 2)
        return [
            self.ax_3d.plot_surface(X, Y, one, alpha=0.5),
            self.ax_3d.plot_surface(X, Y, -one, alpha=0.5),
            self.ax_3d.plot_surface(X, -one, Y, alpha=0.5),
            self.ax_3d.plot_surface(X, one, Y, alpha=0.5),
            self.ax_3d.plot_surface(-one, X, Y, alpha=0.5),
            self.ax_3d.plot_surface(one, X, Y, alpha=0.5)
        ]

    def update_loop(self):
        ts, data = self.serial_reader.get_all_data()
        sensor = self.selected_sensor.get()
        if data:
            idx = SENSOR_KEYS.index(sensor)
            now = time.time()
            range_sec = {"1 min": 60, "5 min": 300, "Full": float("inf")}[self.selected_range.get()]
            filtered = [(t, d[idx]) for t, d in zip(ts, data) if now - t <= range_sec]

            latest = data[-1]
            hr = latest[SENSOR_KEYS.index("Heart Rate (bpm)")]
            spo2 = latest[SENSOR_KEYS.index("SpO₂ (%)")]
            temp = latest[SENSOR_KEYS.index("Temp (°C)")]
            pres = latest[SENSOR_KEYS.index("Pressure (hPa)")]
            alt = latest[SENSOR_KEYS.index("Altitude (m)")]
            aq = latest[SENSOR_KEYS.index("Air Quality (ppm)")]
            acc_x = latest[SENSOR_KEYS.index("Acc X")]
            acc_y = latest[SENSOR_KEYS.index("Acc Y")]
            acc_z = latest[SENSOR_KEYS.index("Acc Z")]

            # Update gauges and visualizations
            self.hr_meter.configure(amountused=hr)
            self.spo2_meter.configure(amountused=spo2)
            self.temp_meter.configure(amountused=temp)
            self.pressure_label.configure(text=f"{pres:.1f} hPa")
            self.altitude_label.configure(text=f"{alt:.1f} m")
            self.aq_label.configure(text=f"{aq:.1f} ppm")
            self.accel_label.configure(text=f"X: {acc_x:.2f}\nY: {acc_y:.2f}\nZ: {acc_z:.2f}")

            # Animate heart beat
            self.hr_beat.config(text="💓" if int(time.time()*2) % 2 else "❤️")
            
            # Update air quality emoji
            if aq < 50:
                self.aq_status.config(text="😊", bootstyle="success")
            elif aq < 100:
                self.aq_status.config(text="😐", bootstyle="warning")
            else:
                self.aq_status.config(text="😷", bootstyle="danger")

            # Update altitude icon position (simple animation)
            alt_pos = min(max(int((alt % 1000) / 1000 * 4), 0), 3)
            self.altitude_icon.config(text=["🛩️", "✈️", "🛫", "🛬"][alt_pos])

            # Update plot based on selected view
            if self.visualization_mode.get() == "3D View":
                self.update_3d_view(acc_x, acc_y, acc_z)
            else:
                self.update_2d_plot(filtered, sensor, range_sec)

            self.check_alerts(latest)

        self.root.after(1000, self.update_loop)

    def update_2d_plot(self, filtered, sensor, range_sec):
        if filtered:
            x_vals = [t - filtered[0][0] for t, _ in filtered]
            y_vals = [v for _, v in filtered]

            self.canvas.get_tk_widget().pack_forget()
            self.canvas_3d.get_tk_widget().pack_forget()
            self.canvas.get_tk_widget().pack(fill='both', expand=True)

            self.plot_line.set_data(x_vals, y_vals)
            self.ax.set_xlim(max(0, x_vals[-1] - range_sec), x_vals[-1] + 1)
            self.ax.set_ylim(min(y_vals) - 5, max(y_vals) + 5)
            self.ax.set_title(f"{sensor} over Time ({self.selected_range.get()})")
            self.ax.set_xlabel("Time (s)")
            self.ax.set_ylabel(sensor)
            self.ax.legend([sensor])
            self.canvas.draw()

    def update_3d_view(self, acc_x, acc_y, acc_z):
        self.canvas.get_tk_widget().pack_forget()
        self.canvas_3d.get_tk_widget().pack(fill='both', expand=True)
        
        self.ax_3d.clear()
        self.ax_3d.view_init(elev=acc_y*10, azim=acc_x*10)
        self.create_3d_cube()
        self.ax_3d.set_title(f"3D Orientation (X:{acc_x:.1f}, Y:{acc_y:.1f}, Z:{acc_z:.1f})")
        self.ax_3d.set_xlim(-1.5, 1.5)
        self.ax_3d.set_ylim(-1.5, 1.5)
        self.ax_3d.set_zlim(-1.5, 1.5)
        self.canvas_3d.draw()

    def check_alerts(self, latest_data):
        alerts = []
        hr = latest_data[SENSOR_KEYS.index("Heart Rate (bpm)")]
        spo2 = latest_data[SENSOR_KEYS.index("SpO₂ (%)")]
        temp = latest_data[SENSOR_KEYS.index("Temp (°C)")]
        aq = latest_data[SENSOR_KEYS.index("Air Quality (ppm)")]

        if hr < 50 or hr > 120:
            alerts.append(f"⚠️ Abnormal Heart Rate: {hr:.1f} bpm")
        if spo2 < 90:
            alerts.append(f"⚠️ Low SpO₂: {spo2:.1f}%")
        if temp > 38.0:
            alerts.append(f"🌡️ High Temperature: {temp:.1f}°C")
        if aq > 100:
            alerts.append(f"😷 Poor Air Quality: {aq:.1f} ppm")

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