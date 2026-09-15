#include <Arduino.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <SPI.h>
#include <Adafruit_AS7341.h>
#include <Adafruit_GFX.h>
#include <Adafruit_PCD8544.h>
#if defined(__AVR__)
#include <avr/wdt.h>
#endif

namespace {

// Queue output without blocking reception on the Mega's small hardware UART buffer.
class SerialOutput : public Print {
 public:
  size_t write(uint8_t value) override {
    if (length_ >= sizeof(buffer_)) return 0;
    buffer_[length_++] = value;
    return 1;
  }
  size_t freeSpace() const { return sizeof(buffer_) - length_; }
  void pump() {
    size_t count = Serial.availableForWrite();
    if (count > length_) count = length_;
    if (!count) return;
    Serial.write(buffer_, count);
    length_ -= count;
    memmove(buffer_, buffer_ + count, length_);
  }
 private:
  uint8_t buffer_[1024]{};
  size_t length_{0};
};
SerialOutput tx;

constexpr uint8_t kDisplayDcPin{5};
constexpr uint8_t kDisplayCePin{4};
constexpr uint8_t kDisplayResetPin{3};
constexpr unsigned long kPageIntervalMs{3000UL};
constexpr uint16_t kOverflowCount{65535U};
constexpr uint8_t kChannelCount{10};
constexpr uint8_t kPageSize{5};
constexpr uint8_t kSerialLineCapacity{128};
constexpr uint8_t kLedPwmPin{11};
constexpr uint8_t kDefaultLedPwmPercent{25};

Adafruit_PCD8544 display{kDisplayDcPin, kDisplayCePin, kDisplayResetPin};
Adafruit_AS7341 sensor;

struct MeasurementFrame {
  uint16_t values[kChannelCount]{};
  unsigned long capturedAtMs{0};
  uint32_t sequence{0};
};

struct GainSetting {
  const char* label;
  as7341_gain_t libraryValue;
};

struct IntegrationSetting {
  const char* label;
  uint8_t atime;
  uint16_t durationMs;
};

constexpr uint16_t kSensorAstep{999};
constexpr GainSetting kGainSettings[] = {
    {"0.5x", AS7341_GAIN_0_5X}, {"1x", AS7341_GAIN_1X},
    {"2x", AS7341_GAIN_2X},     {"4x", AS7341_GAIN_4X},
    {"8x", AS7341_GAIN_8X},     {"16x", AS7341_GAIN_16X},
    {"32x", AS7341_GAIN_32X},   {"64x", AS7341_GAIN_64X},
    {"128x", AS7341_GAIN_128X}, {"256x", AS7341_GAIN_256X},
    {"512x", AS7341_GAIN_512X},
};
constexpr IntegrationSetting kIntegrationSettings[] = {
    {"50ms", 17, 50}, {"100ms", 35, 100}, {"200ms", 71, 200},
    {"300ms", 107, 300}, {"400ms", 143, 400}, {"600ms", 215, 600},
};
constexpr uint8_t kGainSettingCount = sizeof(kGainSettings) / sizeof(kGainSettings[0]);
constexpr uint8_t kIntegrationSettingCount = sizeof(kIntegrationSettings) / sizeof(kIntegrationSettings[0]);

const char* const kChannelJsonNames[kChannelCount] = {
    "415", "445", "480", "515", "555", "590", "630", "680", "nir", "clear",
};
const char* const kChannelDisplayNames[kChannelCount] = {
    "415", "445", "480", "515", "555", "590", "630", "680", "NIR", "CLR",
};

MeasurementFrame currentFrame;
uint8_t currentPage{0};
uint8_t gainIndex{8};       // 128x, como el firmware multicanal de IO Rodeo.
uint8_t integrationIndex{3}; // 300 ms, valor inicial del firmware IO Rodeo.
unsigned long lastPageChangeMs{0};
unsigned long lastMeasurementMs{0};
char serialLine[kSerialLineCapacity]{};
uint8_t serialLineLength{0};
bool discardingLine{false};
bool sensorReady{false};
bool autoPage{true};
bool channelDisplay{false};
uint8_t selectedChannel{0};
char captureId[33]{};
unsigned long captureRequestedMs{0};
uint16_t settleMs{0};
char displayLines[6][15]{};
uint8_t ledPwmPercent{kDefaultLedPwmPercent};

uint8_t pwmRawFromPercent(const uint8_t percent) {
  return static_cast<uint8_t>((static_cast<uint16_t>(percent) * 255U + 50U) / 100U);
}

void applyLedPwm() {
  analogWrite(kLedPwmPin, pwmRawFromPercent(ledPwmPercent));
}

void sendJsonString(const char* value) {
  tx.print('"');
  tx.print(value);
  tx.print('"');
}

bool applyGain(const uint8_t index) {
  return sensor.setGain(kGainSettings[index].libraryValue);
}

bool applyIntegration(const uint8_t index) {
  return sensor.setATIME(kIntegrationSettings[index].atime) &&
         sensor.setASTEP(kSensorAstep);
}

void armSensorReadWatchdog() {
#if defined(__AVR__)
  wdt_reset();
  wdt_enable(WDTO_8S);
#endif
}

void disarmSensorReadWatchdog() {
#if defined(__AVR__)
  wdt_disable();
#endif
}

// 1 = complete, 2 = failed. This intentionally mirrors Adafruit's canonical
// read-all-channels example; no channel is normalized or reconstructed here.
uint8_t readMeasurement(MeasurementFrame& frame) {
  // Adafruit 1.4.1 waits without a timeout for DATA_READY. The watchdog does
  // not alter the acquisition; it only restarts the Mega if that call hangs.
  armSensorReadWatchdog();
  const bool readSucceeded = sensor.readAllChannels();
  disarmSensorReadWatchdog();
  if (!readSucceeded || Wire.getWireTimeoutFlag()) {
    Wire.clearWireTimeoutFlag();
    return 2;
  }
  frame.values[0] = sensor.getChannel(AS7341_CHANNEL_415nm_F1);
  frame.values[1] = sensor.getChannel(AS7341_CHANNEL_445nm_F2);
  frame.values[2] = sensor.getChannel(AS7341_CHANNEL_480nm_F3);
  frame.values[3] = sensor.getChannel(AS7341_CHANNEL_515nm_F4);
  frame.values[4] = sensor.getChannel(AS7341_CHANNEL_555nm_F5);
  frame.values[5] = sensor.getChannel(AS7341_CHANNEL_590nm_F6);
  frame.values[6] = sensor.getChannel(AS7341_CHANNEL_630nm_F7);
  frame.values[7] = sensor.getChannel(AS7341_CHANNEL_680nm_F8);
  frame.values[8] = sensor.getChannel(AS7341_CHANNEL_NIR);
  frame.values[9] = sensor.getChannel(AS7341_CHANNEL_CLEAR);
  frame.capturedAtMs = millis();
  ++frame.sequence;
  return 1;
}

void renderDisplay(const MeasurementFrame& frame) {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(BLACK);
  snprintf(displayLines[0], 15, "G%s T%u %u/2", kGainSettings[gainIndex].label,
           kIntegrationSettings[integrationIndex].durationMs, currentPage + 1);

  const uint8_t firstChannel = currentPage * kPageSize;
  for (uint8_t row = 0; row < kPageSize; ++row) {
    const uint8_t channelIndex = firstChannel + row;
    if (frame.values[channelIndex] >= kOverflowCount) {
      snprintf(displayLines[row + 1], 15, "%-5s %5s", kChannelDisplayNames[channelIndex], "OVFL");
    } else {
      snprintf(displayLines[row + 1], 15, "%-5s %5u", kChannelDisplayNames[channelIndex], frame.values[channelIndex]);
    }
  }
  if (channelDisplay) {
    snprintf(displayLines[0], 15, "AS7341 @90");
    snprintf(displayLines[1], 15, "CANAL %s", kChannelDisplayNames[selectedChannel]);
    if (frame.values[selectedChannel] >= kOverflowCount)
      snprintf(displayLines[2], 15, "OVFL");
    else snprintf(displayLines[2], 15, "%u", frame.values[selectedChannel]);
    snprintf(displayLines[3], 15, "cuentas ADC");
    snprintf(displayLines[4], 15, "G%s T%u", kGainSettings[gainIndex].label,
             kIntegrationSettings[integrationIndex].durationMs);
    snprintf(displayLines[5], 15, "LECTURA REAL");
  }
  display.setTextWrap(false);
  for (uint8_t row = 0; row < 6; ++row) {
    display.setCursor(0, row * 8);
    display.print(displayLines[row]);
  }
  display.display();
}

void emitState() {
  tx.print(F("{\"type\":\"state\",\"device\":\"upch-mega-as7341\",\"protocol\":2,\"firmware\":\"2.3.0\",\"sensor_ready\":"));
  tx.print(sensorReady ? F("true") : F("false"));
  tx.print(F(",\"capabilities\":[\"pwm_control\"],\"auto_page\":"));
  tx.print(autoPage ? F("true") : F("false"));
  tx.print(F(",\"gain\":"));
  sendJsonString(kGainSettings[gainIndex].label);
  tx.print(F(",\"integration_time\":"));
  sendJsonString(kIntegrationSettings[integrationIndex].label);
  tx.print(F(",\"pwm_percent\":"));
  tx.print(ledPwmPercent);
  tx.print(F(",\"pwm_raw\":"));
  tx.print(pwmRawFromPercent(ledPwmPercent));
  tx.print(F(",\"page\":"));
  tx.print(currentPage);
  tx.print(F(",\"display_mode\":"));
  sendJsonString(channelDisplay ? "channel" : "multi");
  tx.print(F(",\"display_channel\":"));
  sendJsonString(kChannelJsonNames[selectedChannel]);
  tx.print(F(",\"display_lines\":["));
  for (uint8_t row = 0; row < 6; ++row) {
    if (row) tx.print(',');
    sendJsonString(displayLines[row]);
  }
  tx.print(']');
  tx.println(F("}"));
}

void emitTelemetry(const MeasurementFrame& frame) {
  tx.print(F("{\"type\":\"telemetry\",\"sequence\":"));
  tx.print(frame.sequence);
  tx.print(F(",\"millis\":"));
  tx.print(frame.capturedAtMs);
  tx.print(F(",\"gain\":"));
  sendJsonString(kGainSettings[gainIndex].label);
  tx.print(F(",\"integration_time\":"));
  sendJsonString(kIntegrationSettings[integrationIndex].label);
  tx.print(F(",\"pwm_percent\":"));
  tx.print(ledPwmPercent);
  tx.print(F(",\"pwm_raw\":"));
  tx.print(pwmRawFromPercent(ledPwmPercent));
  tx.print(F(",\"page\":"));
  tx.print(currentPage);
  tx.print(F(",\"channels\":{"));
  for (uint8_t index = 0; index < kChannelCount; ++index) {
    sendJsonString(kChannelJsonNames[index]);
    tx.print(':');
    tx.print(frame.values[index]);
    if (index + 1 < kChannelCount) {
      tx.print(',');
    }
  }
  tx.print(F("},\"capture_id\":"));
  sendJsonString(captureId);
  tx.print(F(",\"display_mode\":"));
  sendJsonString(channelDisplay ? "channel" : "multi");
  tx.print(F(",\"display_channel\":"));
  sendJsonString(kChannelJsonNames[selectedChannel]);
  tx.print(F(",\"display_lines\":["));
  for (uint8_t row = 0; row < 6; ++row) {
    if (row) tx.print(',');
    sendJsonString(displayLines[row]);
  }
  tx.println(F("]}"));
}

void emitAck(const char* command) {
  tx.print(F("{\"type\":\"ack\",\"command\":"));
  sendJsonString(command);
  tx.println(F("}"));
}

void emitError(const char* code) {
  tx.print(F("{\"type\":\"error\",\"code\":"));
  sendJsonString(code);
  tx.println(F("}"));
}

bool commandValueMatches(const char* command, const char* value) {
  return strcmp(command, value) == 0;
}

int8_t findGainIndex(const char* command) {
  for (uint8_t index = 0; index < kGainSettingCount; ++index) {
    if (commandValueMatches(command, kGainSettings[index].label)) {
      return static_cast<int8_t>(index);
    }
  }
  return -1;
}

int8_t findIntegrationIndex(const char* command) {
  for (uint8_t index = 0; index < kIntegrationSettingCount; ++index) {
    if (commandValueMatches(command, kIntegrationSettings[index].label)) {
      return static_cast<int8_t>(index);
    }
  }
  return -1;
}

void handleCommand(const char* command) {
  // Reject trailing objects/text, even though ArduinoJson permits trailing input.
  bool quoted = false, escaped = false, finished = false;
  int depth = 0;
  for (const char* p = command; *p; ++p) {
    if (finished) {
      if (*p != ' ' && *p != '\t' && *p != '\r') { emitError("invalid_message"); return; }
    } else if (quoted) {
      if (escaped) escaped = false;
      else if (*p == '\\') escaped = true;
      else if (*p == '"') quoted = false;
    } else if (*p == '"') quoted = true;
    else if (*p == '{' || *p == '[') ++depth;
    else if (*p == '}' || *p == ']') { if (--depth == 0) finished = true; }
  }
  if (!finished || quoted) { emitError("invalid_message"); return; }
  StaticJsonDocument<384> doc;
  if (deserializeJson(doc, command) || !doc.is<JsonObject>() ||
      !doc["type"].is<const char*>() || strcmp(doc["type"], "command") != 0 ||
      !doc["command"].is<const char*>()) {
    emitError("invalid_message");
    return;
  }
  const char* name = doc["command"];
  const char* value = doc["value"] | "";
  if (strcmp(name, "get_state") == 0) {
    emitAck("get_state");
    emitState();
    return;
  }
  if (!sensorReady) { emitError("sensor_missing"); return; }
  if (strcmp(name, "begin_capture") == 0) {
    const char* token = doc["capture_id"] | "";
    if (strlen(token) != 32 || strspn(token, "0123456789abcdef") != 32 ||
        !doc["settle_ms"].is<unsigned int>() || doc["settle_ms"].as<unsigned int>() > 10000) {
      emitError("capture_invalid"); return;
    }
    strcpy(captureId, token);
    settleMs = doc["settle_ms"];
    captureRequestedMs = millis();
    emitAck("begin_capture"); return;
  }
  if (strcmp(name, "set_display_channel") == 0) {
    for (uint8_t i = 0; i < kChannelCount; ++i) {
      if (strcmp(value, kChannelJsonNames[i]) == 0) {
        selectedChannel = i; channelDisplay = true;
        emitAck(name); emitState(); return;
      }
    }
    emitError("channel_invalid"); return;
  }
  if (strcmp(name, "set_auto_page") == 0) {
    if (!doc["value"].is<bool>()) { emitError("value_invalid"); return; }
    autoPage = doc["value"];
    lastPageChangeMs = millis();
    emitState(); return;
  }
  if (strcmp(name, "next_page") == 0) {
    channelDisplay = false;
    currentPage = (currentPage + 1) % 2;
    lastPageChangeMs = millis();
    emitAck("next_page");
    emitState();
    return;
  }
  if (strcmp(name, "previous_page") == 0) {
    channelDisplay = false;
    currentPage = (currentPage + 2 - 1) % 2;
    lastPageChangeMs = millis();
    emitAck("previous_page");
    emitState();
    return;
  }
  if (strcmp(name, "set_pwm") == 0) {
    if (!doc["value"].is<unsigned int>() || doc["value"].as<unsigned int>() > 100U) {
      emitError("pwm_invalid");
      return;
    }
    captureId[0] = '\0';
    ledPwmPercent = static_cast<uint8_t>(doc["value"].as<unsigned int>());
    applyLedPwm();
    emitAck("set_pwm");
    emitState();
    return;
  }
  if (strcmp(name, "set_gain") == 0) {
    const int8_t newGainIndex = findGainIndex(value);
    if (newGainIndex < 0) {
      emitError("gain_invalid");
      return;
    }
    captureId[0] = '\0';
    if (!applyGain(newGainIndex)) {
      sensorReady = false; emitError("sensor_config_failed"); emitState(); return;
    }
    gainIndex = static_cast<uint8_t>(newGainIndex);
    emitAck("set_gain");
    emitState();
    return;
  }
  if (strcmp(name, "set_integration") == 0) {
    const int8_t newIntegrationIndex = findIntegrationIndex(value);
    if (newIntegrationIndex < 0) {
      emitError("integration_invalid");
      return;
    }
    captureId[0] = '\0';
    if (!applyIntegration(newIntegrationIndex)) {
      sensorReady = false; emitError("sensor_config_failed"); emitState(); return;
    }
    integrationIndex = static_cast<uint8_t>(newIntegrationIndex);
    emitAck("set_integration");
    emitState();
    return;
  }
  emitError("command_invalid");
}

void pollSerial() {
  tx.pump();
  while (Serial.available() > 0) {
    if (tx.freeSpace() < 600) return;
    const char received = static_cast<char>(Serial.read());
    if (discardingLine) {
      if (received == '\n') discardingLine = false;
      continue;
    }
    if (received == '\n') {
      serialLine[serialLineLength] = '\0';
      if (serialLineLength > 0) {
        handleCommand(serialLine);
      }
      serialLineLength = 0;
      continue;
    }
    if (received != '\r' && serialLineLength + 1 < kSerialLineCapacity) {
      serialLine[serialLineLength++] = received;
    } else if (serialLineLength + 1 >= kSerialLineCapacity) {
      serialLineLength = 0;
      discardingLine = true;
      emitError("line_too_long");
    }
  }
}

void showSensorError() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(BLACK);
  const char* lines[] = {"ERROR AS7341", "SIN DATOS", "REVISA I2C", "Y ALIMENTACION", "REINICIA MEGA", ""};
  display.setTextWrap(false);
  for (uint8_t row = 0; row < 6; ++row) {
    strcpy(displayLines[row], lines[row]);
    display.setCursor(0, row * 8);
    display.print(displayLines[row]);
  }
  display.display();
}

}  // namespace

void configurarPWM() {
  pinMode(kLedPwmPin, OUTPUT);
  applyLedPwm();
}

void setup() {
  Serial.begin(115200);

  // PWM inicial de 25 % en D11: equivale a analogWrite(64).
  configurarPWM();
  Wire.begin();
  Wire.setWireTimeout(25000, true);

  display.begin();
  display.setContrast(55);
  display.setRotation(2);
  display.clearDisplay();
  display.display();

  sensorReady = sensor.begin();
  if (!sensorReady) {
    showSensorError();
    emitError("sensor_missing");
    while (true) {
      pollSerial();
    }
  }

  sensorReady = applyGain(gainIndex) && applyIntegration(integrationIndex);
  if (!sensorReady) { showSensorError(); emitError("sensor_config_failed"); }
  emitState();
}

void loop() {
  pollSerial();
  if (tx.freeSpace() < 600) return;
  if (!sensorReady) return;

  const unsigned long now = millis();
  if (captureId[0] && now - captureRequestedMs < settleMs) return;
  if (autoPage && now - lastPageChangeMs >= kPageIntervalMs) {
    lastPageChangeMs = now;
    currentPage = (currentPage + 1) % 2;
  }
  // Integration already times acquisition; do not add an idle integration period.
  const uint8_t result = readMeasurement(currentFrame);
  if (result == 0) return;
  lastMeasurementMs = now;
  if (result == 2) {
    captureId[0] = '\0';
    sensorReady = false;
    showSensorError();
    emitError("sensor_read_failed");
    emitState();
    return;
  }
  renderDisplay(currentFrame);
  emitTelemetry(currentFrame);
}
