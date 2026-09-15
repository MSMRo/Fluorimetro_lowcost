import constants
from json_settings_file import JsonSettingsFile


class ConfigurationError(Exception):
    pass


class Configuration(JsonSettingsFile):

    FILE_TYPE = 'configuration'
    FILE_NAME = constants.CONFIGURATION_FILE
    LOAD_ERROR_EXCEPTION = ConfigurationError

    def check(self):
        sensor_mappings = {
                'sensor_90': (
                    constants.AS7341_STR_TO_GAIN,
                    constants.AS7341_STR_TO_INTEGRATION_TIME,
                    ),
                'sensor_180': (
                    constants.TSL2591_STR_TO_GAIN,
                    constants.TSL2591_STR_TO_INTEGRATION_TIME,
                    ),
                }

        for sensor_name, mappings in sensor_mappings.items():
            gain_mapping, itime_mapping = mappings
            gain_key = f'gain_{sensor_name}'
            itime_key = f'itime_{sensor_name}'

            gain_str = self.data.get(gain_key)
            if gain_str not in gain_mapping:
                self.error_dict[gain_key] = (
                        f'{self.FILE_TYPE} unknown gain {gain_str}'
                        )

            itime_str = self.data.get(itime_key)
            if itime_str not in itime_mapping:
                self.error_dict[itime_key] = (
                        f'{self.FILE_TYPE} unknown integration time {itime_str}'
                        )

        ref_key = 'ref_irradiance_180'
        if ref_key in self.data:
            try:
                float(self.data[ref_key])
            except (TypeError, ValueError):
                self.error_dict[ref_key] = (
                        f'unable to convert {ref_key} to float'
                        )
        else:
            self.data[ref_key] = constants.DEFAULT_REF_IRRADIANCE_180

        for name in self.error_dict:
            if name in self.data:
                del self.data[name]

    def itime(self, sensor_name):
        itime_key = f'itime_{sensor_name}'
        itime_str = self.data.get(itime_key)
        if sensor_name == 'sensor_90':
            mapping = constants.AS7341_STR_TO_INTEGRATION_TIME
        else:
            mapping = constants.TSL2591_STR_TO_INTEGRATION_TIME
        return mapping.get(itime_str)

    def gain(self, sensor_name):
        gain_key = f'gain_{sensor_name}'
        gain_str = self.data.get(gain_key)
        if sensor_name == 'sensor_90':
            mapping = constants.AS7341_STR_TO_GAIN
        else:
            mapping = constants.TSL2591_STR_TO_GAIN
        return mapping.get(gain_str)

    @property
    def itime_sensor_90(self):
        return self.itime('sensor_90')

    @property
    def itime_sensor_180(self):
        return self.itime('sensor_180')

    @property
    def gain_sensor_90(self):
        return self.gain('sensor_90')

    @property
    def gain_sensor_180(self):
        return self.gain('sensor_180')

    @property
    def startup(self):
        return self.data.get('startup', None)

    @property
    def ref_irradiance_180(self):
        return float(self.data['ref_irradiance_180'])
