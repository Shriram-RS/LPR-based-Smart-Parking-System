#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

const char* ssid = "iQOO 9";         // Replace with your WiFi SSID
const char* password = "yellove01";  // Replace with your WiFi password

const char* serverName = "http://192.168.20.44:8000"; // Replace with your local machine IP and port

#define PIR_SENSOR_1 D1
#define PIR_SENSOR_2 D2

int stateSensor1 = 0;
int stateSensor2 = 0;

WiFiClient client;

void sendToServer(String status) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    String serverPath = String(serverName) + "/update?vehicle=" + status;

    Serial.print("Requesting URL: ");
    Serial.println(serverPath);

    http.begin(client, serverPath.c_str());
    
    int httpResponseCode = http.GET();

    if (httpResponseCode > 0) {
      Serial.print("HTTP Response code: ");
      Serial.println(httpResponseCode);
    } 
    else {
      Serial.print("Error code: ");
      Serial.println(httpResponseCode);
    }
    http.end();
  } 
  else {
    Serial.println("WiFi Disconnected");
  }
}


void setup() {
  Serial.begin(115200);

  pinMode(PIR_SENSOR_1, INPUT);
  pinMode(PIR_SENSOR_2, INPUT);

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
}

void loop() {
  stateSensor1 = digitalRead(PIR_SENSOR_1);
  stateSensor2 = digitalRead(PIR_SENSOR_2);

  if (stateSensor1 == HIGH && stateSensor2 == LOW) {
    sendToServer("enter");
    Serial.println("Vehicle Entered");
    delay(500); // Debounce delay
  } 
  else if (stateSensor1 == LOW && stateSensor2 == HIGH) {
    sendToServer("exit");
    Serial.println("Vehicle Exited");
    delay(500); // Debounce delay
  }
}
