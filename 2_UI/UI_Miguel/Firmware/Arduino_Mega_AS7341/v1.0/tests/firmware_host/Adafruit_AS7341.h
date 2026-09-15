#pragma once
#include "Arduino.h"
enum as7341_gain_t { AS7341_GAIN_0_5X, AS7341_GAIN_1X, AS7341_GAIN_2X,
  AS7341_GAIN_4X, AS7341_GAIN_8X, AS7341_GAIN_16X, AS7341_GAIN_32X,
  AS7341_GAIN_64X, AS7341_GAIN_128X, AS7341_GAIN_256X, AS7341_GAIN_512X };
enum as7341_color_channel_t {
  AS7341_CHANNEL_415nm_F1, AS7341_CHANNEL_445nm_F2,
  AS7341_CHANNEL_480nm_F3, AS7341_CHANNEL_515nm_F4,
  AS7341_CHANNEL_CLEAR_0, AS7341_CHANNEL_NIR_0,
  AS7341_CHANNEL_555nm_F5, AS7341_CHANNEL_590nm_F6,
  AS7341_CHANNEL_630nm_F7, AS7341_CHANNEL_680nm_F8,
  AS7341_CHANNEL_CLEAR, AS7341_CHANNEL_NIR
};
inline bool testReady = true;
inline bool testReadSuccess = true;
inline as7341_gain_t testLastGain = AS7341_GAIN_0_5X;
inline uint8_t testLastAtime = 0;
inline uint16_t testLastAstep = 0;
inline uint16_t testChannels[12] = {101, 202, 303, 404, 505, 606,
                                   707, 808, 909, 1001, 1102, 1203};
struct Adafruit_AS7341 {
  bool begin() { return true; }
  bool setGain(as7341_gain_t gain) {
    testLastGain = gain;
    return true;
  }
  bool setATIME(uint8_t atime) {
    testLastAtime = atime;
    return true;
  }
  bool setASTEP(uint16_t astep) {
    testLastAstep = astep;
    return true;
  }
  bool readAllChannels() { return testReadSuccess; }
  uint16_t getChannel(as7341_color_channel_t channel) {
    return testChannels[static_cast<uint8_t>(channel)];
  }
 protected:
  void* i2c_dev = nullptr;
};
