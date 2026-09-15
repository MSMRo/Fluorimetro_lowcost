#pragma once
struct FakeWire {
  void begin() {}
  void setWireTimeout(unsigned long, bool) {}
  bool getWireTimeoutFlag() { return false; }
  void clearWireTimeoutFlag() {}
};
inline FakeWire Wire;
