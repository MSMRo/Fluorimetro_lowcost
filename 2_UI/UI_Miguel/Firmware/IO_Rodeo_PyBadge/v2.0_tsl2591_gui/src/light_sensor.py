import adafruit_tsl2591


class LightSensorTSL2591:

    TSL2591_MAX_COUNT_100MS = 36863  # 0x8FFF
    TSL2591_MAX_COUNT = 65535        # 0xFFFF

    DEFAULT_GAIN = adafruit_tsl2591.GAIN_MED
    DEFAULT_INTEGRATION_TIME = adafruit_tsl2591.INTEGRATIONTIME_500MS

    GAIN_TO_AGAIN = { 
            adafruit_tsl2591.GAIN_LOW  :  1.0, 
            adafruit_tsl2591.GAIN_MED  :  24.5,  
            adafruit_tsl2591.GAIN_HIGH :  400.0, 
            adafruit_tsl2591.GAIN_MAX  :  9200,
            }

    # Irradiance conversion coefficient gives (uW/cm^2) per count with atime=1ms and gain=1x
    IRRADIANCE_COEFF = 100.0*GAIN_TO_AGAIN[adafruit_tsl2591.GAIN_HIGH]/264.1

    def __init__(self, i2c):

        # Set up light sensor
        try:
            self._device = adafruit_tsl2591.TSL2591(i2c)
        except (ValueError, OSError) as error:
            raise LightSensorIOError(error)
        self.gain = self.DEFAULT_GAIN 
        self.integration_time = self.DEFAULT_INTEGRATION_TIME 
        self.channel = 0

    @property
    def max_counts(self):
        if self.integration_time == adafruit_tsl2591.INTEGRATIONTIME_100MS:
            return self.TSL2591_MAX_COUNT_100MS 
        else:
            return self.TSL2591_MAX_COUNT 

    @property
    def value(self):
        value = self._device.raw_luminosity[self.channel]
        if value >= self.max_counts:
            raise LightSensorOverflow('light sensor reading > max_counts')
        #print(value)
        return value

    @property
    def values(self):
        values = self._device.raw_luminosity
        for v in values:
            if v >= self.max_counts:
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

    @property
    def again(self):
        return self.GAIN_TO_AGAIN[self._gain]

    @property
    def atime(self):
        return 100.0*self._integration_time + 100.0

    @gain.setter
    def gain(self, value):
        self._gain = value
        self._device.gain = value

    @property
    def integration_time(self):
        return self._integration_time

    @integration_time.setter
    def integration_time(self, value):
        self._integration_time = value
        self._device.integration_time = value


class LightSensorOverflow(Exception):
    pass

class LightSensorIOError(Exception):
    pass


