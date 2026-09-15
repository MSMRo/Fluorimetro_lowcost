from ulab import numpy as np
import constants
from count_measurement_screen import CountMeasurementScreen
from irradiance_measurement_screen import IrradianceMeasurementScreen
from reference_unit_screen import ReferenceUnitScreen
from light_sensor import LightSensorOverflow

class Measurement:

    NAME  = 'Measurment'
    LABEL = 'Label'
    UNITS = None

    def __init__(self, sensor_90, sensor_180, config):
        self.sensor_90  = sensor_90
        self.sensor_180 = sensor_180
        self.config = config

    @property
    def name(self):
        return self.NAME

    @property
    def label(self):
        return self.LABEL

    @property
    def units(self):
        return self.UNITS

    @property
    def value(self):
        return 0.0

    @property
    def create_screen(self):
        return None

    def update_norm_sample(self):
        pass


class RawCount(Measurement):
    
    NAME  = 'Raw Count'
    LABEL = 'Count @90', 'Count @180'

    @property
    def value(self): 
        try:
            value_90  = self.sensor_90.value
        except LightSensorOverflow:
            value_90 = constants.OVERFLOW_STR
        try:
            value_180 = self.sensor_180.value 
        except LightSensorOverflow:
            value_180 = constants.OVERFLOW_STR
        return value_90, value_180

    def create_screen(self):
        return CountMeasurementScreen()


class Irradiance(Measurement):

    NAME  = f'Irradiance'
    LABEL = f'{NAME} @90', f'{NAME} @180' 
    UNITS = f'{constants.MU_STR}W/{constants.CM2_STR}'

    @property
    def value(self):
        try:
            value_90 = self.sensor_90.irradiance
        except LightSensorOverflow:
            value_90 = constants.OVERFLOW_STR
        try:
            value_180 = self.sensor_180.irradiance
        except LightSensorOverflow:
            value_180 = constants.OVERFLOW_STR
        return value_90, value_180

    def create_screen(self): 
        return IrradianceMeasurementScreen()


class RelativeUnit(Measurement):

    NAME  = f'Relative Units'
    LABEL = f'{NAME} @90'
    UNITS = f'{constants.MU_STR}W/{constants.CM2_STR}'

    def __init__(self, sensor_90, sensor_180, config):
        super().__init__(sensor_90, sensor_180, config)
        self.norm_sample_180 = None 
        self.ref_irradiance_180 = config.ref_irradiance_180

    @property
    def value(self):
        if self.norm_sample_180 is not None:
            value_90 = self.sensor_90.irradiance
            ref_value_90 = self.ref_irradiance_180*(value_90/self.norm_sample_180)
        else:
            ref_value_90 = '___.__'
        return ref_value_90

    def create_screen(self):
        return ReferenceUnitScreen()

    def update_norm_sample(self):
        samples = np.zeros(constants.NUM_SAMPLE_180)
        for i in range(constants.NUM_SAMPLE_180):
            samples[i] = self.sensor_180.irradiance
        median_sample = np.median(samples)
        if median_sample > 0.0:
            self.norm_sample_180 = np.median(samples)
        else:
            self.norm_sample_180 = None 
            raise ZeroNormalizationSample("normalization sample is 0")


class ZeroNormalizationSample(Exception):
    pass


MEASUREMENTS = [RawCount, Irradiance, RelativeUnit]
NAME_TO_MEASUREMENT = {item.NAME:item for item in MEASUREMENTS}

def from_name(name, sensors, config):
    return NAME_TO_MEASUREMENT[name](*sensors, config)
