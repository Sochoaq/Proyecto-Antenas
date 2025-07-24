#include <LoRa.h>
#include <DHT.h>
#include <Adafruit_BMP280.h>

// Pines LoRa
#define SS 5
#define RST 14
#define DIO0 2

// Pines sensores
#define DHTPIN 4
#define ledpin 27

#define BAND 433E6  // Frecuencia LoRa

DHT dht(DHTPIN, DHT11);
Adafruit_BMP280 bmp;  // Usamos interfaz I2C (SDA=21, SCL=22 en ESP32)

void setup() {
  Serial.begin(115200);
  pinMode(ledpin, OUTPUT);
  digitalWrite(ledpin, LOW);

  // Iniciar sensores
  dht.begin();

  if (!bmp.begin()) {
    Serial.println("No se detecta el BMP280, revisa el cableado.");
    while (1);
  }

  // Configurar LoRa
  LoRa.setPins(SS, RST, DIO0);

  if (!LoRa.begin(BAND)) {
    Serial.println("Error al iniciar LoRa");
    while (1) {
      digitalWrite(ledpin, HIGH);
      delay(300);
      digitalWrite(ledpin, LOW);
      delay(300);
    }
  }

  digitalWrite(ledpin, HIGH);
  Serial.println("LoRa Iniciado correctamente");

  // Configuración avanzada LoRa
  LoRa.setTxPower(0.0001, PA_OUTPUT_PA_BOOST_PIN); // 20 dBm = 100 mW
  LoRa.setSpreadingFactor(12);
  LoRa.setSignalBandwidth(125E3);
  LoRa.setCodingRate4(8);
}

void loop() {
  float temperatura = dht.readTemperature();
  float humedad = dht.readHumidity();
  float presion = bmp.readPressure() / 100.0;  // Conversión a hPa

  if (isnan(temperatura) || isnan(humedad) || isnan(presion)) {
    Serial.println("Error al leer algún sensor");
    return;
  }

  // Mostrar en consola
  Serial.print("T: ");
  Serial.print(temperatura);
  Serial.print(" °C | H: ");
  Serial.print(humedad);
  Serial.print(" % | P: ");
  Serial.print(presion);
  Serial.println(" hPa");

  // Enviar por LoRa
  LoRa.beginPacket();
  LoRa.print("T:");
  LoRa.print(temperatura);
  LoRa.print(" H:");
  LoRa.print(humedad);
  LoRa.print(" P:");
  LoRa.print(presion);
  LoRa.endPacket();

  delay(2000);
}

