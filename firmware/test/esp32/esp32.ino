#include <Wire.h>
#include "MAX30105.h"
#include "spo2_algorithm.h"

MAX30105 particleSensor;

#define MAX_BRIGHTNESS 255

uint32_t irBuffer[100]; // Infrared LED sensor readings
uint32_t redBuffer[100]; // Red LED sensor readings

void setup() {
    Serial.begin(115200);
    Serial.println("Initializing...");

    // Initialize I2C communication
    if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
        Serial.println("MAX30102 not found. Check wiring!");
        while (1);
    }

    Serial.println("MAX30102 detected!");

    // Set sensor mode
    particleSensor.setup();
    particleSensor.setPulseAmplitudeRed(0x0A); // Lower power for better readings
    particleSensor.setPulseAmplitudeIR(0x0A);
}

void loop() {
    int samples = 100; // Number of samples for calculating SpO2 and heart rate

    // Read data from sensor
    for (int i = 0; i < samples; i++) {
        while (particleSensor.check() == false); // Wait for new data
        redBuffer[i] = particleSensor.getRed();
        irBuffer[i] = particleSensor.getIR();
    }

    int spo2;
    int32_t heartRate;  // Keep this as int32_t as per function requirement
    int8_t validSPO2;   // Change to int8_t
    int8_t validHeartRate;  // Change to int8_t

    // Calculate SpO2 and heart rate
    maxim_heart_rate_and_oxygen_saturation(irBuffer, samples, redBuffer, 
                                           &spo2, &validSPO2, 
                                           &heartRate, &validHeartRate);

    // Print results
    Serial.print("Heart Rate: ");
    if (validHeartRate) {
        Serial.print(heartRate);
    } else {
        Serial.print("Invalid");
    }

    Serial.print(" bpm | SpO2: ");
    if (validSPO2) {
        Serial.print(spo2);
        Serial.println(" %");
    } else {
        Serial.println("Invalid");
    }

    delay(1000); // Wait before next measurement
}
