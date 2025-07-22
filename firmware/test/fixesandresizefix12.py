import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import ttkbootstrap as tb

# Simulated sensor data
sensor_data = {
    "Temperature (°C)": "25.3",
    "Humidity (%)": "45.6",
    "Pressure (hPa)": "1013.25",
    "Altitude (m)": "150.5"
}
SENSOR_KEYS = list(sensor_data.keys())

class SensorDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("SensoHealth Dashboard")
        self.root.geometry("600x400")
        self.root.resizable(False, False)

        self.selected_sensor = tk.StringVar()
        self.selected_sensor.set(SENSOR_KEYS[0])

        self.create_widgets()

    def create_widgets(self):
        # Title
        title = tb.Label(self.root, text="SensoHealth", font=("Helvetica", 20, "bold"), bootstyle="info")
        title.pack(pady=10)

        # Logo image
        try:
            logo_img = Image.open(r"C:\Users\USER\Desktop\Keyboard_Fixer\Sense2Scale Hackathon\logo.jpg")  # Use raw string
            logo_img = logo_img.resize((60, 60), Image.ANTIALIAS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = tb.Label(self.root, image=logo_photo)
            logo_label.image = logo_photo
            logo_label.place(x=20, y=15)
        except Exception as e:
            print("Error loading logo:", e)

        # Dropdown
        dropdown = tb.Combobox(self.root, textvariable=self.selected_sensor, values=SENSOR_KEYS, width=25)
        dropdown.pack(pady=5)
        dropdown.bind("<<ComboboxSelected>>", self.update_sensor_display)

        # Sensor display frame
        self.sensor_frame = tb.Frame(self.root, borderwidth=2, relief="ridge", padding=10)
        self.sensor_frame.pack(pady=15)

        self.sensor_label = tb.Label(self.sensor_frame, text="", font=("Arial", 18), bootstyle="success")
        self.sensor_label.pack()

        # Initial display
        self.update_sensor_display()

        # Altitude & Pressure frame
        self.alt_pres_frame = tb.Frame(self.root, borderwidth=2, relief="solid", padding=10)
        self.alt_pres_frame.pack(pady=10)

        self.altitude_label = tb.Label(self.alt_pres_frame, text=f"Altitude: {sensor_data['Altitude (m)']} m", font=("Arial", 12), bootstyle="primary")
        self.altitude_label.pack()

        self.pressure_label = tb.Label(self.alt_pres_frame, text=f"Pressure: {sensor_data['Pressure (hPa)']} hPa", font=("Arial", 12), bootstyle="primary")
        self.pressure_label.pack()

    def update_sensor_display(self, event=None):
        key = self.selected_sensor.get()
        value = sensor_data.get(key, "N/A")
        self.sensor_label.config(text=f"{key}: {value}")

if __name__ == "__main__":
    root = tb.Window(themename="flatly")
    app = SensorDashboard(root)
    root.mainloop()
