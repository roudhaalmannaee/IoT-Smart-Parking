#include <WiFi.h>
#include <PubSubClient.h>
#include <SPI.h>
#include <MFRC522.h>
#include <ESP32Servo.h>

const char* ssid = "KHALID";
const char* password = "0506444030";
const char* mqtt_server = "192.168.200.109";

WiFiClient espClient;
PubSubClient client(espClient);

#define TRIG1 5
#define ECHO1 18
#define RED1 14
#define GREEN1 12

#define SERVO_PIN 26

#define SS_PIN 21
#define RST_PIN 4
#define SCK_PIN 19
#define MISO_PIN 22
#define MOSI_PIN 23

#define CO2_PIN 34

MFRC522 rfid(SS_PIN, RST_PIN);
Servo gateServo;

bool spot1Occupied = false;
float distance1;

float readDistance() {
  digitalWrite(TRIG1, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG1, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG1, LOW);
  long duration = pulseIn(ECHO1, HIGH, 30000);
  if (duration == 0) return 100;
  float dist = duration * 0.034 / 2;
  if (dist < 2 || dist > 400) return 100;
  return dist;
}

void setup_wifi() {
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) delay(500);
}

void reconnect() {
  while (!client.connected()) {
    if (client.connect("ESP32Client")) {
      client.publish("parking/system/status", "ESP32 Connected");
    } else {
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(TRIG1, OUTPUT);
  pinMode(ECHO1, INPUT);
  pinMode(RED1, OUTPUT);
  pinMode(GREEN1, OUTPUT);

  digitalWrite(GREEN1, HIGH);

  SPI.begin(SCK_PIN, MISO_PIN, MOSI_PIN, SS_PIN);
  rfid.PCD_Init();

  gateServo.attach(SERVO_PIN);
  gateServo.write(0);

  setup_wifi();
  client.setServer(mqtt_server, 1883);
}

void loop() {

  if (!client.connected()) reconnect();
  client.loop();

  distance1 = readDistance();

  String vehicleType = "NONE";

  if (distance1 < 25) {
    spot1Occupied = true;

    if (distance1 < 10)
      vehicleType = "SUV";
    else if (distance1 < 18)
      vehicleType = "SEDAN";
    else
      vehicleType = "COMPACT";

    digitalWrite(RED1, HIGH);
    digitalWrite(GREEN1, LOW);
    client.publish("parking/spot1/status", "OCCUPIED");
    client.publish("parking/spot1/type", vehicleType.c_str());

  } else {
    spot1Occupied = false;
    digitalWrite(RED1, LOW);
    digitalWrite(GREEN1, HIGH);
    client.publish("parking/spot1/status", "FREE");
    client.publish("parking/spot1/type", "NONE");
  }

  int co2 = analogRead(CO2_PIN);
  String co2Str = String(co2);
  client.publish("parking/co2", co2Str.c_str());

  if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {

  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++)
    uid += String(rfid.uid.uidByte[i], HEX);

  client.publish("parking/gate/rfid", uid.c_str());

  // ===== AUTHORIZED CARDS =====
  String authorizedCards[] = {
    "73fc7f1a",    // Your main card
    "a1b2c3d4"     // Add second card if needed
  };

  bool accessGranted = false;

  for (int i = 0; i < 2; i++) {
    if (uid == authorizedCards[i]) {
      accessGranted = true;
      break;
    }
  }

  if (accessGranted && !spot1Occupied) {

    client.publish("parking/gate/status", "AUTHORIZED");

    gateServo.write(90);
    delay(3000);
    gateServo.write(0);

    client.publish("parking/gate/status", "CLOSED");

  } else {
    client.publish("parking/gate/status", "DENIED");
  }

  rfid.PICC_HaltA();
}


  delay(1000);
}
