import tkinter as tk
from tkinter import ttk, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import pandas as pd
import random

# Sensor Keys
SENSOR_KEYS = ["Heart Rate", "SpO2", "Temperature", "Altitude", "Pressure"]

class HealthMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SensoHealth - Real-time Health Monitor")
        self.root.geometry("1000x720")
        self.data = []

        self.setup_gui()
        self.update_data()

    def setup_gui(self):
        # Header
        ttk.Label(self.root, text="SensoHealth - Live Health Dashboard", font=("Helvetica", 16, "bold")).pack(pady=10)

        # Plot Area
        self.figure, self.ax = plt.subplots(figsize=(8, 3), dpi=100)
        self.ax.set_title("Live Sensor Data")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Value")
        self.canvas = FigureCanvasTkAgg(self.figure, self.root)
        self.canvas.get_tk_widget().pack()

        # Time Range Dropdown & Export
        controls_frame = ttk.Frame(self.root)
        controls_frame.pack(pady=5)

        ttk.Label(controls_frame, text="Time Range:").pack(side=tk.LEFT, padx=(0, 5))

        self.time_range = ttk.Combobox(controls_frame, values=["1 min", "5 min", "Full"], state="readonly", width=10)
        self.time_range.current(2)
        self.time_range.pack(side=tk.LEFT)

        ttk.Button(controls_frame, text="Export CSV", command=self.export_csv).pack(side=tk.LEFT, padx=10)

        # Readouts (Heart Rate, SpO2, Temp)
        readouts_frame = ttk.Frame(self.root)
        readouts_frame.pack(pady=5, fill="x")

        self.labels = {}
        for key in SENSOR_KEYS:
            if key in ["Altitude", "Pressure"]:
                continue
            frame = ttk.LabelFrame(readouts_frame, text=key)
            frame.pack(side=tk.LEFT, expand=True, fill="both", padx=5)
            self.labels[key] = ttk.Label(frame, text="--", font=("Helvetica", 14))
            self.labels[key].pack(padx=10, pady=10)

        # Separate Altitude and Pressure
        environment_frame = ttk.Frame(self.root)
        environment_frame.pack(pady=5, fill="x")

        for key in ["Altitude", "Pressure"]:
            box = ttk.LabelFrame(environment_frame, text=key)
            box.pack(side=tk.LEFT, expand=True, fill="both", padx=5)
            self.labels[key] = ttk.Label(box, text="--", font=("Helvetica", 14))
            self.labels[key].pack(padx=10, pady=10)

        # Live Alerts / Fall Logs
        log_frame = ttk.LabelFrame(self.root, text="Live Alerts / Fall Logs")
        log_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.log_text = tk.Text(log_frame, height=6, font=("Courier", 10), bg="#f2f2f2")
        self.log_text.pack(fill="both", expand=True)
        self.log_text.config(state=tk.DISABLED)

    def update_data(self):
        now = datetime.now()
        new_entry = {"Time": now}
        for key in SENSOR_KEYS:
            if key == "Heart Rate":
                value = random.randint(60, 100)
            elif key == "SpO2":
                value = random.uniform(95, 100)
            elif key == "Temperature":
                value = random.uniform(36, 37.5)
            elif key == "Altitude":
                value = random.randint(10, 100)
            elif key == "Pressure":
                value = random.randint(950, 1050)
            new_entry[key] = round(value, 2)

        self.data.append(new_entry)
        self.update_gui(new_entry)
        self.root.after(1000, self.update_data)

    def update_gui(self, entry):
        # Update sensor labels
        for key in SENSOR_KEYS:
            self.labels[key].config(text=str(entry[key]))

        # Filter DataFrame
        df = pd.DataFrame(self.data)
        if self.time_range.get() != "Full":
            minutes = int(self.time_range.get().split()[0])
            df = df[df["Time"] >= datetime.now() - timedelta(minutes=minutes)]

        # Plot data
        self.ax.clear()
        self.ax.set_title("Live Sensor Data")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Value")

        for key in ["Heart Rate", "SpO2", "Temperature"]:
            self.ax.plot(df["Time"], df[key], label=key)

        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.ax.legend(loc="upper left")
        self.canvas.draw()

        self.check_alerts(entry)

    def check_alerts(self, entry):
        alerts = []
        if entry["SpO2"] < 94:
            alerts.append("Low SpO2!")
        if entry["Heart Rate"] > 100:
            alerts.append("High Heart Rate!")
        if entry["Temperature"] > 37.5:
            alerts.append("Fever Detected!")
        if entry["Altitude"] > 80:
            alerts.append("Fall Detected!")

        if alerts:
            self.log_text.config(state=tk.NORMAL)
            timestamp = entry["Time"].strftime("%H:%M:%S")
            for alert in alerts:
                self.log_text.insert(tk.END, f"[{timestamp}] {alert}\n")
            self.log_text.config(state=tk.DISABLED)
            self.log_text.see(tk.END)

    def export_csv(self):
        df = pd.DataFrame(self.data)
        if self.time_range.get() != "Full":
            minutes = int(self.time_range.get().split()[0])
            df = df[df["Time"] >= datetime.now() - timedelta(minutes=minutes)]

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save CSV File"
        )
        if file_path:
            df.to_csv(file_path, index=False)

# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = HealthMonitorApp(root)
    root.mainloop()
