#include <Adafruit_NeoPixel.h>

// ----- User config -----
#define LED_PIN     15          // GPIO driving the LED strip
#define NUM_LEDS    1          // how many pixels you have
#define BRIGHTNESS  100        // 0..255
// UART pins (ESP32 is pin-matrix; 16/17 are common defaults)
#define UART_RX_PIN 16         // from Raspberry Pi TXD (pin 8)
#define UART_TX_PIN 17         // to Raspberry Pi RXD (pin 10)
#define UART_BAUD   115200
// -----------------------

Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

HardwareSerial RPI(2);

static uint8_t rgb[3];
static uint8_t idx = 0;

void setAll(uint8_t r, uint8_t g, uint8_t b) {
  strip.setPixelColor(0, strip.Color(r, g, b));
  strip.show();
}

void applyRGB() {
  setAll(rgb[0], rgb[1], rgb[2]);
}

void setup() {
  strip.begin();
  strip.setBrightness(BRIGHTNESS);
  strip.show();              // initialize all OFF

  // Debug over USB serial (optional)
  Serial.begin(115200);
  delay(100);

  // UART to Raspberry Pi
  RPI.begin(UART_BAUD, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);
  Serial.println("UART RGB controller ready");
}

void loop() {
  while (RPI.available() > 0) {
    Serial.println("Data received");
    uint8_t b = RPI.read();
    rgb[idx++] = b;
    if (idx == 3) {
      applyRGB();
      idx = 0;
    }
  }
}
