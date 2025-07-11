import serial
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as signal
from collections import deque

# ==== CONFIGURE SERIAL PORT ====
SERIAL_PORT = "COM4"  # Change to match ESP32 port (e.g., "/dev/ttyUSB0" for Linux)
BAUD_RATE = 115200

# ==== PLOT CONFIG ====
plt.ion()
fig, ax = plt.subplots()
window_size = 300  # Increase window size for smoother ECG
ecg_buffer = deque([0] * window_size, maxlen=window_size)


# ==== BANDPASS FILTER (0.5Hz - 50Hz for ECG) ====
def bandpass_filter(data, lowcut=0.5, highcut=50.0, fs=200, order=2):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = signal.butter(order, [low, high], btype='band')
    return signal.filtfilt(b, a, data) if len(data) > 10 else data

# ==== MOVING AVERAGE FILTER ====
def moving_average(data, window_size=5):
    return np.convolve(data, np.ones(window_size)/window_size, mode='same')

# ==== R-PEAK DETECTION ====
def detect_r_peaks(ecg_data, threshold=0.6):
    peaks, _ = signal.find_peaks(ecg_data, height=threshold * max(ecg_data))
    return peaks

# ==== HEART HEALTH PREDICTION ====
def analyze_heart_health(spo2, heart_rate, systolicBP, diastolicBP):
    if spo2 < 90:
        return "⚠ Low Oxygen (Hypoxia)"
    elif heart_rate < 50:
        return "⚠ Bradycardia (Slow HR)"
    elif heart_rate > 100:
        return "⚠ Tachycardia (Fast HR)"
    elif systolicBP > 140 or diastolicBP > 90:
        return "⚠ High Blood Pressure (Hypertension)"
    elif systolicBP < 90 or diastolicBP < 60:
        return "⚠ Low Blood Pressure (Hypotension)"
    else:
        return "✅ Normal Heart Function"

# ==== MAIN LOOP ====
try:
    with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1) as ser:
        print(f"✅ Connected to {SERIAL_PORT}. Reading ECG data...")

        while True:
            try:
                # Read Serial Data
                line = ser.readline().decode('utf-8', errors='ignore').strip()

                if line:
                    parts = line.split(',')
                    if len(parts) == 5:
                        ecg_value = int(parts[0])
                        spo2 = float(parts[1])
                        heart_rate = int(parts[2])
                        systolicBP = int(parts[3])
                        diastolicBP = int(parts[4])

                        # Update ECG Buffer
                        ecg_buffer.append(ecg_value)
                        filtered_ecg = bandpass_filter(list(ecg_buffer))
                        smooth_ecg = moving_average(filtered_ecg)

                        # Detect R-Peaks
                        r_peaks = detect_r_peaks(smooth_ecg)

                        # Analyze Heart Health
                        health_status = analyze_heart_health(spo2, heart_rate, systolicBP, diastolicBP)

                        # === PLOTTING ECG ===
                        ax.clear()
                        ax.plot(smooth_ecg, label="Filtered ECG", color='blue')
                        ax.scatter(r_peaks, [smooth_ecg[p] for p in r_peaks], color='red', label="R-Peaks")
                        ax.set_ylim(min(smooth_ecg) - 50, max(smooth_ecg) + 50)
                        ax.set_title(f"ECG Live (HR: {heart_rate} bpm, SpO2: {spo2}%, BP: {systolicBP}/{diastolicBP})")
                        ax.set_xlabel("Time")
                        ax.set_ylabel("ECG Amplitude")
                        ax.legend()

                        # Refresh Plot
                        plt.draw()
                        plt.pause(0.001)
                        fig.canvas.flush_events()

                        # Print Data
                        print(f"ECG: {ecg_value} | SpO2: {spo2}% | HR: {heart_rate} bpm | BP: {systolicBP}/{diastolicBP} | {health_status}")

            except Exception as e:
                print("⚠ Error reading data:", e)

except serial.SerialException:
    print(f"❌ Cannot open serial port {SERIAL_PORT}. Check your connection.")