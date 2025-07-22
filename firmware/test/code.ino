#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>
#include <Adafruit_BMP280.h>
#include <LiquidCrystal_I2C.h>
#include "MAX30105.h"
#include <OneWire.h>
#include <DallasTemperature.h>

// ===== WiFi and ThingSpeak =====
const char* ssid = "POCO X2";
const char* password = "1234567a";
const char* THINGSPEAK_API_KEY = "67DEWBO770UKV585";
const char* THINGSPEAK_URL = "https://api.thingspeak.com/update";

// ===== Telegram Bot (Optional) =====
String TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"; // Replace
String TELEGRAM_CHAT_ID = "YOUR_CHAT_ID";     // Replace

// ===== Pins =====
#define ECG_PIN 35
#define MQ135_PIN 34
#define DSB_PIN 27
#define BUZZER_PIN 4
#define BUTTON_PIN 5

// ===== LCD & I2C =====
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ===== Sensor Objects =====
MAX30105 max30102;
Adafruit_BMP280 bmp;
Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(12345);
OneWire oneWire(DSB_PIN);
DallasTemperature dsbSensor(&oneWire);
WiFiClient client;

// ===== State Variables =====
int screenIndex = 0;
bool alertActive = false;
unsigned long alertStart = 0;
const unsigned long alertDuration = 5000;
unsigned long lastThingSpeakTime = 0;
const unsigned long THINGSPEAK_INTERVAL = 15000;
bool lastButtonState = HIGH;

// ===== Telegram Sender =====
void sendTelegram(String msg) {
  if (TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN") return;
  String url = "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN +
               "/sendMessage?chat_id=" + TELEGRAM_CHAT_ID + "&text=" + msg;
  HTTPClient http;
  http.begin(url);
  int code = http.GET();
  Serial.println(code > 0 ? "✅ Telegram Sent!" : "❌ Telegram Failed!");
  http.end();
}

// ===== ThingSpeak Uploader =====
void uploadThingSpeak(float temp, float spo2, float hr, float pressure, float alt, float ax, float ay, float az) {
  if (WiFi.status() != WL_CONNECTED) return;
  String url = String(THINGSPEAK_URL) + "?api_key=" + THINGSPEAK_API_KEY +
               "&field1=" + String(hr) +
               "&field2=" + String(spo2) +
               "&field3=" + String(temp) +
               "&field4=" + String(pressure) +
               "&field5=" + String(alt) +
               "&field6=" + String(ax) +
               "&field7=" + String(ay) +
               "&field8=" + String(az);
  HTTPClient http;
  http.begin(url);
  int code = http.GET();
  Serial.println(code > 0 ? "✅ Sent to ThingSpeak" : "❌ ThingSpeak Error");
  http.end();
}

// ===== LCD Updater =====
void updateLCD(float hr, float spo2, float temp, float pressure, float alt, int mq, float ax, float ay, float az, String alertText = "") {
  if (alertText != "") {
    lcd.clear();
    lcd.setCursor(0, 0); lcd.print("⚠ ALERT:");
    lcd.setCursor(0, 1); lcd.print(alertText.substring(0, 16));
    digitalWrite(BUZZER_PIN, HIGH);
    alertStart = millis();
    alertActive = true;
    return;
  }

  if (alertActive && millis() - alertStart > alertDuration) {
    alertActive = false;
    digitalWrite(BUZZER_PIN, LOW);
    lcd.clear();
  }

  if (alertActive) return;

  lcd.clear();
  switch (screenIndex) {
    case 0:
      lcd.setCursor(0, 0); lcd.print("HR:"); lcd.print(hr, 0); lcd.print(" SpO2:"); lcd.print(spo2, 0);
      lcd.setCursor(0, 1); lcd.print("Temp:"); lcd.print(temp, 1); lcd.print("C");
      break;
    case 1:
      lcd.setCursor(0, 0); lcd.print("Pres:"); lcd.print(pressure, 0); lcd.print("hPa");
      lcd.setCursor(0, 1); lcd.print("Alt:"); lcd.print(alt, 0); lcd.print(" MQ:"); lcd.print(mq);
      break;
    case 2:
      lcd.setCursor(0, 0); lcd.print("AccX:"); lcd.print(ax, 1); lcd.print(" Y:"); lcd.print(ay, 1);
      lcd.setCursor(0, 1); lcd.print("Z:"); lcd.print(az, 1);
      break;
  }
}

// ===== Setup =====
void setup() {
  Serial.begin(115200);
  lcd.init(); lcd.backlight();
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(BUZZER_PIN, OUTPUT); digitalWrite(BUZZER_PIN, LOW);

  WiFi.begin(ssid, password);
  unsigned long wifiStart = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - wifiStart < 10000) {
    delay(500); Serial.print(".");
  }
  Serial.println(WiFi.status() == WL_CONNECTED ? "\n✅ WiFi Connected" : "\n❌ WiFi Failed");

  Wire.begin(21, 22);
  if (!max30102.begin()) Serial.println("❌ MAX30102 Not Found");
  if (!bmp.begin(0x76)) Serial.println("❌ BMP280 Not Found");
  if (!accel.begin()) Serial.println("❌ ADXL345 Not Found");
  dsbSensor.begin();
}

// ===== Main Loop =====
void loop() {
  // Instant Button Handling
  bool currentButton = digitalRead(BUTTON_PIN);
  if (lastButtonState == HIGH && currentButton == LOW) {
    screenIndex = (screenIndex + 1) % 3;
    lcd.clear();
  }
  lastButtonState = currentButton;

  // === Sensor Readings ===
  int ecg = analogRead(ECG_PIN);
  dsbSensor.requestTemperatures();
  float dsbTemp = dsbSensor.getTempCByIndex(0);

  long ir = max30102.getIR();
  long red = max30102.getRed();
  float spo2 = (ir > 1000) ? red * 100.0 / ir : 98.0;
  float hr = (ir > 1000) ? 60.0 / (ir / 1000.0) : 75.0;

  float pressure = bmp.readPressure() / 100.0;
  float alt = bmp.readAltitude(1013.25);

  sensors_event_t event;
  accel.getEvent(&event);
  float accX = event.acceleration.x;
  float accY = event.acceleration.y;
  float accZ = event.acceleration.z;

  int mq = analogRead(MQ135_PIN);

  // === Serial Output to Python (Fast) ===
  Serial.print("ECG: "); Serial.println(ecg);
  Serial.print("PYTHON-> ");
  Serial.print(hr); Serial.print(",");
  Serial.print(spo2); Serial.print(",");
  Serial.print(dsbTemp); Serial.print(",");
  Serial.print(pressure); Serial.print(",");
  Serial.print(alt); Serial.print(",");
  Serial.print(accX); Serial.print(",");
  Serial.print(accY); Serial.print(",");
  Serial.print(accZ); Serial.print(",");
  Serial.println(mq);

  // === Alert Detection ===
  String alertMsg = "";
  if (spo2 < 90) alertMsg = "Low SpO2";
  else if (hr > 120) alertMsg = "High HR";
  else if (mq > 3000) alertMsg = "Air Bad";
  else if (abs(accX) > 10 || abs(accY) > 10 || abs(accZ) < 2) alertMsg = "Fall Detected";

  if (alertMsg != "") sendTelegram("⚠ " + alertMsg);

  // === LCD Update ===
  updateLCD(hr, spo2, dsbTemp, pressure, alt, mq, accX, accY, accZ, alertMsg);

  // === ThingSpeak Upload (every 15s) ===
  if (millis() - lastThingSpeakTime > THINGSPEAK_INTERVAL) {
    uploadThingSpeak(dsbTemp, spo2, hr, pressure, alt, accX, accY, accZ);
    lastThingSpeakTime = millis();
  }

  // No delay to keep loop fast
}