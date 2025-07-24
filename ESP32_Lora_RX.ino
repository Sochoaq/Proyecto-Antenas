#include <LoRa.h>

#define SS 5
#define RST 14
#define DIO0 2
#define ledpin 27

String received_message = "";
float temperatura = 0.0;
float humedad = 0.0;

void setup() {
  Serial.begin(115200);
  pinMode(ledpin, OUTPUT);
  digitalWrite(ledpin, LOW);

  LoRa.setPins(SS, RST, DIO0);

  if (!LoRa.begin(433E6)) {
    Serial.println("Error al iniciar LoRa");
    while (1) {
      digitalWrite(ledpin, HIGH);
      delay(300);
      digitalWrite(ledpin, LOW);
      delay(300);
    }
  }

  digitalWrite(ledpin, HIGH);
  Serial.println("LoRa RX iniciado correctamente");

  LoRa.setTxPower(20, PA_OUTPUT_PA_BOOST_PIN);
  LoRa.setSpreadingFactor(12);
  LoRa.setSignalBandwidth(125E3);
  LoRa.setCodingRate4(8);
}

void loop() {
  int packetSize = LoRa.parsePacket();

  if (packetSize) {
    received_message = "";

    while (LoRa.available()) {
      received_message += (char)LoRa.read();
      delay(5);  // Asegura que no se pierdan caracteres
    }

    Serial.println("Mensaje recibido:");
    Serial.println(received_message);

    int rssi = LoRa.packetRssi();
    float snr = LoRa.packetSnr();

    Serial.print("Potencia recibida (RSSI): ");
    Serial.print(rssi);
    Serial.println(" dBm");

    Serial.print("SNR: ");
    Serial.println(snr);

    digitalWrite(ledpin, HIGH);
    delay(200);
    digitalWrite(ledpin, LOW);
  }
}