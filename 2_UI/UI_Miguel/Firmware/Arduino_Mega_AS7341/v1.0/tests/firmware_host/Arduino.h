#pragma once
#include <cstdint>
#include <cstring>
#include <cstdio>
#include <string>
#include <type_traits>
#define F(value) value
#define OUTPUT 1
inline uint8_t testPwmPin = 0;
inline int testPwmValue = -1;
inline void pinMode(uint8_t, uint8_t) {}
inline void analogWrite(uint8_t pin, int value) { testPwmPin = pin; testPwmValue = value; }
inline unsigned long testMillis = 0;
inline unsigned long millis() { return testMillis; }
struct Print {
  virtual size_t write(uint8_t) = 0;
  void print(const char* value) { while (*value) write(*value++); }
  void print(char value) { write(value); }
  template <class T> void print(T value) { print(std::to_string(value).c_str()); }
  template <class T> void println(T value) { print(value); write('\n'); }
};
struct FakeSerial {
  std::string input, output;
  void begin(unsigned long) {}
  int available() { return static_cast<int>(input.size()); }
  int availableForWrite() { return 64; }
  void write(uint8_t* value, size_t length) { output.append(reinterpret_cast<char*>(value), length); }
  int read() { char c = input.front(); input.erase(0, 1); return c; }
  void print(const char* value) { output += value; }
  void print(char value) { output += value; }
  template <class T> void print(T value) { output += std::to_string(value); }
  template <class T> void println(T value) { print(value); output += '\n'; }
};
inline FakeSerial Serial;
