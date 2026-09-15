#pragma once
#include "Arduino.h"
struct Adafruit_PCD8544 {
  std::string lines[6];
  unsigned row = 0;
  Adafruit_PCD8544(int, int, int) {}
  void begin() {}
  void setContrast(int) {}
  void setRotation(int) {}
  void clearDisplay() { for (auto& line : lines) line.clear(); }
  void setTextSize(int) {}
  void setTextColor(int) {}
  void setTextWrap(bool) {}
  void setCursor(int, int y) { row = y / 8; }
  void print(const char* value) { lines[row] += value; }
  void println(const char* value) { print(value); ++row; }
  void display() {}
};
