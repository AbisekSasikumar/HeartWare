import ttkbootstrap as tb
from ttkbootstrap.constants import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import csv
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

SENSOR_KEYS = ['Heart Rate', 'SpO2', 'Temp (C)', 'Pressure', 'Altitude']

class SensorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SensoHealth - Live Sensor Dashboard")

        self.data = []
        self.timestamps = []

        self.selected_sensor = tb.StringVar(value=SENSOR_KEYS[3])
        self.selected_range = tb.StringVar(value="1 min")

        self.create_widgets()
        self.simulate_data()  # Replace with real serial logic as needed

    def create_widgets(self):
        # Header and Logo
        header_frame = tb.Frame(self.root)
        header_frame.pack(fill='x', pady=5)

        # Optional: Add image/logo
        try:
            logo_img = Image.open(r"C:\Users\USER\Desktop\Keyboard_Fixer\Sense2Scale Hackathon\logo.jpg")  # replace with your image path
            logo_img = logo_img.resize((40, 40))
            self.logo = ImageTk.PhotoImage(logo_img)
            tb.Label(header_frame, image=self.logo).pack(side='left', padx=10)
        except:
            pass

        tb.Label(header_frame, text="SensoHealth - Real-time Monitor", font=("Helvetica", 18, "bold")).pack(side='left')

        # Meters
        self.meter_frame = tb.Frame(self.root)
        self.meter_frame.pack(fill='x', padx=10, pady=10)

        self.hr_meter = tb.Meter(self.meter_frame, bootstyle="danger", subtext="Heart Rate (bpm)", metertype="semi", amounttotal=200, amountused=0)
        self.hr_meter.pack(side='left', padx=10)

        self.spo2_meter = tb.Meter(self.meter_frame, bootstyle="success", subtext="SpO2 (%)", metertype="semi", amounttotal=100, amountused=0)
        self.spo2_meter.pack(side='left', padx=10)

        self.temp_meter = tb.Meter(self.meter_frame, bootstyle="warning", subtext="Temperature (C)", metertype="semi", amounttotal=50, amountused=0)
        self.temp_meter.pack(side='left', padx=10)

        # Sensor Info
        info_frame = tb.Frame(self.root)
        info_frame.pack(fill='x', pady=5)

        self.altitude_label = tb.Label(info_frame, text="Altitude: -- m", font=("Segoe UI", 12))
        self.altitude_label.pack(side='left', padx=10)

        self.pressure_label = tb.Label(info_frame, text="Pressure: -- hPa", font=("Segoe UI", 12))
        self.pressure_label.pack(side='left', padx=10)

        # Controls
        ctrl_frame = tb.Frame(self.root)
        ctrl_frame.pack(pady=5)

        tb.Label(ctrl_frame, text="Sensor:").pack(side='left')
        self.sensor_dropdown = tb.Combobox(ctrl_frame, values=SENSOR_KEYS, textvariable=self.selected_sensor)
        self.sensor_dropdown.pack(side='left', padx=5)

        tb.Label(ctrl_frame, text="Time Range:").pack(side='left')
        self.range_dropdown = tb.Combobox(ctrl_frame, values=["1 min", "5 min", "Full"], textvariable=self.selected_range)
        self.range_dropdown.pack(side='left', padx=5)

        self.save_button = tb.Button(ctrl_frame, text="💾 Export CSV", command=self.save_csv, bootstyle="primary")
        self.save_button.pack(side='left', padx=10)

        # Plot Frame
        plot_frame = tb.LabelFrame(self.root, text="📈 Sensor Data Plot")
        plot_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.fig, self.ax = plt.subplots(figsize=(6, 3))
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        self.plot_line, = self.ax.plot([], [], label=self.selected_sensor.get())

        self.root.after(1000, self.update_loop)

    def simulate_data(self):
        from random import randint, uniform
        ts = time.time()
        entry = [randint(60, 100), uniform(95, 100), uniform(36.5, 38), randint(950, 1050), randint(10, 100)]
        self.timestamps.append(ts)
        self.data.append(entry)
        self.root.after(1000, self.simulate_data)

    def update_loop(self):
        if not self.data:
            return self.root.after(1000, self.update_loop)

        idx = SENSOR_KEYS.index(self.selected_sensor.get())
        now = time.time()
        time_range = {"1 min": 60, "5 min": 300, "Full": float('inf')}[self.selected_range.get()]
        filtered = [(t, d[idx]) for t, d in zip(self.timestamps, self.data) if now - t <= time_range]

        if filtered:
            x = [t - filtered[0][0] for t, _ in filtered]
            y = [v for _, v in filtered]
            self.plot_line.set_data(x, y)
            self.ax.set_xlim(max(0, x[-1] - time_range), x[-1] + 1)
            self.ax.set_ylim(min(y) - 5, max(y) + 5)
            self.ax.set_title(f"{SENSOR_KEYS[idx]} Over Time")
            self.ax.set_xlabel("Time (s)")
            self.ax.set_ylabel(SENSOR_KEYS[idx])
            self.ax.legend([SENSOR_KEYS[idx]])
            self.canvas.draw()

        # Update meters
        latest = self.data[-1]
        self.hr_meter.configure(amountused=latest[0])
        self.spo2_meter.configure(amountused=latest[1])
        self.temp_meter.configure(amountused=latest[2])
        self.pressure_label.configure(text=f"Pressure: {latest[3]:.1f} hPa")
        self.altitude_label.configure(text=f"Altitude: {latest[4]:.1f} m")

        self.root.after(1000, self.update_loop)

    def save_csv(self):
        if not self.data:
            messagebox.showinfo("No Data", "Nothing to save.")
            return

        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not filepath:
            return

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp"] + SENSOR_KEYS)
            for t, row in zip(self.timestamps, self.data):
                writer.writerow([time.strftime('%H:%M:%S', time.localtime(t))] + row)

        messagebox.showinfo("Exported", f"CSV saved to {filepath}")


if __name__ == '__main__':
    root = tb.Window(themename="flatly")
    app = SensorGUI(root)
    root.mainloop()
