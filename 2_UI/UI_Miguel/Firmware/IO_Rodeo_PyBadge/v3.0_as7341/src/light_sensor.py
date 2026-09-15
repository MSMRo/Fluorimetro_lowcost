import adafruit_as7341
import adafruit_tsl2591

import constants


class LightSensorAS7341:

    AS7341_MAX_COUNT = 65535
    DEFAULT_GAIN = adafruit_as7341.Gain.GAIN_128X
    DEFAULT_INTEGRATION_TIME = (107, 999)
    CHANNEL_NAMES = constants.CHANNEL_NAMES_90
    CLEAR_CHANNEL = 9

    GAIN_TO_AGAIN = {
            adafruit_as7341.Gain.GAIN_0_5X: 0.5,
            adafruit_as7341.Gain.GAIN_1X: 1.0,
            adafruit_as7341.Gain.GAIN_2X: 2.0,
            adafruit_as7341.Gain.GAIN_4X: 4.0,
            adafruit_as7341.Gain.GAIN_8X: 8.0,
            adafruit_as7341.Gain.GAIN_16X: 16.0,
            adafruit_as7341.Gain.GAIN_32X: 32.0,
            adafruit_as7341.Gain.GAIN_64X: 64.0,
            adafruit_as7341.Gain.GAIN_128X: 128.0,
            adafruit_as7341.Gain.GAIN_256X: 256.0,
            adafruit_as7341.Gain.GAIN_512X: 512.0,
            }

    def __init__(self, i2c):
        try:
            self._device = adafruit_as7341.AS7341(i2c)
        except (ValueError, OSError, RuntimeError) as error:
            raise LightSensorIOError(error)
        self.gain = self.DEFAULT_GAIN
        self.integration_time = self.DEFAULT_INTEGRATION_TIME

    @property
    def max_counts(self):
        return self.AS7341_MAX_COUNT

    @property
    def raw_values(self):
        try:
            values = list(self._device.all_channels)
            values.append(self._device.channel_nir)
            values.append(self._device.channel_clear)
        except (ValueError, OSError, RuntimeError) as error:
            raise LightSensorIOError(error)
        return tuple(values)

    @property
    def values(self):
        return self.raw_values

    @property
    def saturated_indices(self):
        return tuple(
                index
                for index, value in enumerate(self.raw_values)
                if value >= self.max_counts
                )

    @property
    def value(self):
        value = self.raw_values[self.CLEAR_CHANNEL]
        if value >= self.max_counts:
            raise LightSensorOverflow('light sensor reading > max_counts')
        return value

    @property
    def irradiance(self):
        # Señal normalizada del canal clear para conservar las pantallas de
        # latest. No representa irradiancia absoluta sin calibración óptica.
        return self.value/(self.again*self.atime)

    @property
    def gain(self):
        return self._gain

    @gain.setter
    def gain(self, value):
        self._gain = value
        self._device.gain = value

    @property
    def again(self):
        return self.GAIN_TO_AGAIN[self._gain]

    @property
    def gain_str(self):
        return constants.AS7341_GAIN_TO_STR[self.gain]

    @property
    def integration_time(self):
        return self._integration_time

    @integration_time.setter
    def integration_time(self, value):
        atime, astep = value
        self._device.atime = atime
        self._device.astep = astep
        self._integration_time = value

    @property
    def atime(self):
        atime, astep = self.integration_time
        return (atime + 1)*(astep + 1)*2.78/1000.0

    @property
    def integration_time_str(self):
        return constants.AS7341_INTEGRATION_TIME_TO_STR[
                self.integration_time
                ]


class LightSensorTSL2591:

    TSL2591_MAX_COUNT_100MS = 36863  # 0x8FFF
    TSL2591_MAX_COUNT = 65535        # 0xFFFF

    DEFAULT_GAIN = adafruit_tsl2591.GAIN_MED
    DEFAULT_INTEGRATION_TIME = adafruit_tsl2591.INTEGRATIONTIME_500MS

    GAIN_TO_AGAIN = {
            adafruit_tsl2591.GAIN_LOW: 1.0,
            adafruit_tsl2591.GAIN_MED: 24.5,
            adafruit_tsl2591.GAIN_HIGH: 400.0,
            adafruit_tsl2591.GAIN_MAX: 9200,
            }

    # (uW/cm^2) por cuenta con tiempo=1ms y ganancia=1x.
    IRRADIANCE_COEFF = (
            100.0*GAIN_TO_AGAIN[adafruit_tsl2591.GAIN_HIGH]/264.1
            )

    def __init__(self, i2c):
        try:
            self._device = adafruit_tsl2591.TSL2591(i2c)
        except (ValueError, OSError, RuntimeError) as error:
            raise LightSensorIOError(error)
        self.gain = self.DEFAULT_GAIN
        self.integration_time = self.DEFAULT_INTEGRATION_TIME
        self.channel = 0

    @property
    def max_counts(self):
        if self.integration_time == adafruit_tsl2591.INTEGRATIONTIME_100MS:
            return self.TSL2591_MAX_COUNT_100MS
        return self.TSL2591_MAX_COUNT

    @property
    def value(self):
        value = self._device.raw_luminosity[self.channel]
        if value >= self.max_counts:
            raise LightSensorOverflow('light sensor reading > max_counts')
        return value

    @property
    def values(self):
        values = self._device.raw_luminosity
        for value in values:
            if value >= self.max_counts:
                raise LightSensorOverflow('light sensor reading > max_counts')
        return values

    @property
    def lux(self):
        return self._device.lux

    @property
    def irradiance(self):
        raw_value = self._device.raw_luminosity[0]/(self.again*self.atime)
        return raw_value*self.IRRADIANCE_COEFF

    @property
    def gain(self):
        return self._gain

    @gain.setter
    def gain(self, value):
        self._gain = value
        self._device.gain = value

    @property
    def again(self):
        return self.GAIN_TO_AGAIN[self._gain]

    @property
    def gain_str(self):
        return constants.TSL2591_GAIN_TO_STR[self.gain]

    @property
    def atime(self):
        return 100.0*self._integration_time + 100.0

    @property
    def integration_time(self):
        return self._integration_time

    @integration_time.setter
    def integration_time(self, value):
        self._integration_time = value
        self._device.integration_time = value

    @property
    def integration_time_str(self):
        return constants.TSL2591_INTEGRATION_TIME_TO_STR[
                self.integration_time
                ]


class LightSensorOverflow(Exception):
    pass


class LightSensorIOError(Exception):
    pass
