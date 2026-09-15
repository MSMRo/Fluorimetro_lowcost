#include <cassert>
#include <iostream>
#include "../../firmware/mega_as7341_multichannel/firmware.cpp"

void drain() { for (int i = 0; i < 20; ++i) tx.pump(); }

int main() {
  setup();
  assert(testPwmPin == 11 && testPwmValue == 64);
  assert(ledPwmPercent == 25);
  assert(integrationIndex == 3);
  assert(testLastGain == AS7341_GAIN_128X);
  assert(testLastAtime == 107);
  assert(testLastAstep == 999);
  const as7341_gain_t expectedGains[] = {
      AS7341_GAIN_0_5X, AS7341_GAIN_1X,   AS7341_GAIN_2X,
      AS7341_GAIN_4X,   AS7341_GAIN_8X,   AS7341_GAIN_16X,
      AS7341_GAIN_32X,  AS7341_GAIN_64X,  AS7341_GAIN_128X,
      AS7341_GAIN_256X, AS7341_GAIN_512X,
  };
  for (uint8_t index = 0; index < kGainSettingCount; ++index) {
    assert(applyGain(index));
    assert(testLastGain == expectedGains[index]);
  }
  const uint8_t expectedAtimes[] = {17, 35, 71, 107, 143, 215};
  for (uint8_t index = 0; index < kIntegrationSettingCount; ++index) {
    assert(applyIntegration(index));
    assert(testLastAtime == expectedAtimes[index]);
    assert(testLastAstep == 999);
  }
  // Regression: la API canónica entrega ambos bancos en el orden público.
  currentFrame = MeasurementFrame{};
  testMillis = 0;
  assert(readMeasurement(currentFrame) == 1);
  const uint16_t expectedRawChannels[] = {
      101, 202, 303, 404, 707, 808, 909, 1001, 1203, 1102,
  };
  for (uint8_t index = 0; index < kChannelCount; ++index) {
    assert(currentFrame.values[index] == expectedRawChannels[index]);
  }
  drain();
  Serial.output.clear();
  emitTelemetry(currentFrame);
  drain();
  StaticJsonDocument<2048> rawTelemetry;
  assert(!deserializeJson(rawTelemetry, Serial.output));
  for (uint8_t index = 0; index < kChannelCount; ++index) {
    assert(rawTelemetry["channels"][kChannelJsonNames[index]] ==
           expectedRawChannels[index]);
  }
  assert(rawTelemetry["pwm_percent"] == 25);
  assert(rawTelemetry["pwm_raw"] == 64);
  Serial.output.clear();
  emitState();
  drain();
  StaticJsonDocument<2048> state;
  assert(!deserializeJson(state, Serial.output));
  assert(strcmp(state["capabilities"][0], "pwm_control") == 0);
  testReadSuccess = false;
  assert(readMeasurement(currentFrame) == 2);
  testReadSuccess = true;
  handleCommand("{ \"type\" : \"command\", \"command\" : \"set_gain\", \"value\" : \"64x\" }");
  assert(gainIndex == 7);
  assert(testLastGain == AS7341_GAIN_64X);
  handleCommand("{\"type\":\"command\",\"command\":\"set_integration\",\"value\":\"200ms\"}");
  assert(integrationIndex == 2);
  assert(testLastAtime == 71);
  assert(testLastAstep == 999);
  handleCommand("{\"type\":\"command\",\"command\":\"set_pwm\",\"value\":0}");
  assert(ledPwmPercent == 0 && testPwmPin == 11 && testPwmValue == 0);
  handleCommand("{\"type\":\"command\",\"command\":\"set_pwm\",\"value\":100}");
  assert(ledPwmPercent == 100 && testPwmValue == 255);
  handleCommand("{\"type\":\"command\",\"command\":\"set_pwm\",\"value\":25}");
  assert(ledPwmPercent == 25 && testPwmValue == 64);
  handleCommand("{\"type\":\"command\",\"command\":\"begin_capture\",\"capture_id\":\"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\",\"settle_ms\":1000}");
  assert(strlen(captureId) == 32);
  handleCommand("{\"type\":\"command\",\"command\":\"set_pwm\",\"value\":50}");
  assert(captureId[0] == '\0' && ledPwmPercent == 50 && testPwmValue == 128);
  handleCommand("{\"type\":\"command\",\"command\":\"set_pwm\",\"value\":25}");
  handleCommand("{\"type\":\"command\",\"command\":\"set_pwm\",\"value\":101}");
  assert(ledPwmPercent == 25 && testPwmValue == 64);
  drain();
  handleCommand("{\"type\":\"command\",\"command\":\"set_gain\",\"value\":\"1x\"}junk");
  assert(gainIndex == 7);
  handleCommand("{\"type\":\"command\",\"command\":\"set_gain\",\"value\":\"invalid\"}");
  assert(gainIndex == 7);
  Serial.input = std::string(140, 'x') + "{\"type\":\"command\",\"command\":\"next_page\"}\n";
  pollSerial();
  assert(currentPage == 0);
  Serial.input = "{\"type\":\"command\",\"command\":\"next_page\"}\n";
  pollSerial();
  assert(currentPage == 1);
  drain();
  for (uint8_t gain = 0; gain < kGainSettingCount; ++gain) {
    gainIndex = gain;
    for (uint8_t integration = 0; integration < kIntegrationSettingCount; ++integration) {
      integrationIndex = integration;
      for (uint8_t page = 0; page < 2; ++page) {
        currentPage = page;
        currentFrame.values[page * 5] = 65535;
        renderDisplay(currentFrame);
        for (unsigned line = 0; line < 6; ++line) {
          assert(strlen(displayLines[line]) <= 14);
          assert(display.lines[line] == displayLines[line]);
        }
        assert(strstr(displayLines[1], "OVFL"));
        Serial.output.clear();
        emitTelemetry(currentFrame);
        drain();
        StaticJsonDocument<2048> telemetry;
        assert(!deserializeJson(telemetry, Serial.output));
        for (unsigned line = 0; line < 6; ++line)
          assert(strcmp(telemetry["display_lines"][line], displayLines[line]) == 0);
      }
    }
  }
  for (uint8_t channel = 0; channel < kChannelCount; ++channel) {
    channelDisplay = true;
    selectedChannel = channel;
    renderDisplay(currentFrame);
    for (unsigned line = 0; line < 6; ++line) {
      assert(strlen(displayLines[line]) <= 14);
      assert(display.lines[line] == displayLines[line]);
    }
    Serial.output.clear();
    emitTelemetry(currentFrame); drain();
    StaticJsonDocument<2048> document;
    assert(!deserializeJson(document, Serial.output));
    assert(strcmp(document["display_channel"], kChannelJsonNames[channel]) == 0);
  }
  handleCommand("{\"type\":\"command\",\"command\":\"next_page\"}");
  assert(!channelDisplay);
  drain();
  currentFrame.sequence = 0;
  integrationIndex = 3;
  testMillis = 100;
  handleCommand("{\"type\":\"command\",\"command\":\"begin_capture\",\"capture_id\":\"0123456789abcdef0123456789abcdef\",\"settle_ms\":1000}");
  assert(strlen(captureId) == 32);
  drain();
  loop();
  assert(currentFrame.sequence == 0);
  testMillis = 1200;
  loop();
  assert(currentFrame.sequence == 1);
  drain();
  testReadSuccess = false;
  testMillis = 2000;
  loop();
  assert(!sensorReady && captureId[0] == '\0');
  std::cout << "Firmware host: public AS7341 API, raw channels, configuration, parser, display, capture barrier and PWM OK\n";
}
