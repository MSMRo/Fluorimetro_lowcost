import board
import displayio
import constants
import fonts
import adafruit_itertools
from adafruit_display_text import label


class CountMeasurementScreen:


    ANCHOR_POINT = (0.0, 0.5)

    HEADER_TO_GAIN_SPACING = 22

    HEADER1_LABEL_X_POSITION = 5 
    HEADER1_LABEL_Y_POSITION = 12 

    VALUE1_LABEL_X_POSITION = 110
    VALUE1_LABEL_Y_POSITION = HEADER1_LABEL_Y_POSITION

    GAIN1_LABEL_X_POSITION = HEADER1_LABEL_X_POSITION
    GAIN1_LABEL_Y_POSITION = HEADER1_LABEL_Y_POSITION + HEADER_TO_GAIN_SPACING

    ITIME1_LABEL_X_POSITION = 80 
    ITIME1_LABEL_Y_POSITION = GAIN1_LABEL_Y_POSITION

    HEADER2_LABEL_X_POSITION = HEADER1_LABEL_X_POSITION
    HEADER2_LABEL_Y_POSITION = 64 

    VALUE2_LABEL_X_POSITION = VALUE1_LABEL_X_POSITION
    VALUE2_LABEL_Y_POSITION = HEADER2_LABEL_Y_POSITION

    GAIN2_LABEL_X_POSITION = HEADER1_LABEL_X_POSITION
    GAIN2_LABEL_Y_POSITION = HEADER2_LABEL_Y_POSITION + HEADER_TO_GAIN_SPACING 

    ITIME2_LABEL_X_POSITION = 80 
    ITIME2_LABEL_Y_POSITION = GAIN2_LABEL_Y_POSITION

    BATTERY_LABEL_X_POSITION = 30      
    BATTERY_LABEL_Y_POSITION = 114

    SENSOR_INDICES = [0,1]


    def __init__(self):

        self.selected_sensor = None  
        self.setup_selected_sensor_cycle()

        # Setup color palette
        self.color_to_index = {k:i for (i,k) in enumerate(constants.COLOR_TO_RGB)}
        self.palette = displayio.Palette(len(constants.COLOR_TO_RGB))
        for i, palette_tuple in enumerate(constants.COLOR_TO_RGB.items()):
            self.palette[i] = palette_tuple[1]   

        # Create tile grid
        self.bitmap = displayio.Bitmap( 
                board.DISPLAY.width, 
                board.DISPLAY.height, 
                len(constants.COLOR_TO_RGB)
                )
        self.bitmap.fill(self.color_to_index['black'])
        self.tile_grid = displayio.TileGrid(self.bitmap,pixel_shader=self.palette)
        font_scale = 1

        # Create header1 text label
        header1_str = 'header1'
        text_color = constants.COLOR_TO_RGB['white']
        self.header1_label = label.Label(
                fonts.font_10pt, 
                text = header1_str, 
                color = text_color, 
                scale = font_scale,
                anchor_point = self.ANCHOR_POINT,
                )
        self.header1_label.anchored_position = ( 
                self.HEADER1_LABEL_X_POSITION, 
                self.HEADER1_LABEL_Y_POSITION,
                )

        # Create value1 text label
        dummy_value = 0.0
        value_str = f'{dummy_value:1.2f}'.replace('0','O')
        text_color = constants.COLOR_TO_RGB['white']
        self.value1_label = label.Label(
                fonts.font_10pt, 
                text = value_str, 
                color = text_color, 
                scale = font_scale,
                anchor_point = self.ANCHOR_POINT,
                )
        self.value1_label.anchored_position = (
                self.VALUE1_LABEL_X_POSITION,
                self.VALUE1_LABEL_Y_POSITION, 
                )

        # Create text label for gain1 information
        gain_str = 'gain xxx' 
        text_color = constants.COLOR_TO_RGB['orange']
        self.gain1_label = label.Label(
                fonts.font_10pt, 
                text=gain_str, 
                color=text_color, 
                scale=font_scale,
                anchor_point = self.ANCHOR_POINT,
                )
        self.gain1_label.anchored_position = (
                self.GAIN1_LABEL_X_POSITION,
                self.GAIN1_LABEL_Y_POSITION,
                )

        # Create text label for integration time 1 information
        itime_str = 'time xxxms' 
        text_color = constants.COLOR_TO_RGB['orange']
        self.itime1_label = label.Label(
                fonts.font_10pt, 
                text=itime_str, 
                color=text_color, 
                scale=font_scale,
                anchor_point = self.ANCHOR_POINT,
                )
        self.itime1_label.anchored_position = (
                self.ITIME1_LABEL_X_POSITION,
                self.ITIME1_LABEL_Y_POSITION,
                )
        
        # Create header2 text label
        header2_str = 'header2'
        text_color = constants.COLOR_TO_RGB['white']
        self.header2_label = label.Label(
                fonts.font_10pt, 
                text = header2_str, 
                color = text_color, 
                scale = font_scale,
                anchor_point = self.ANCHOR_POINT,
                )
        self.header2_label.anchored_position = ( 
                self.HEADER2_LABEL_X_POSITION,
                self.HEADER2_LABEL_Y_POSITION,
                )

        # Create value2 text label
        dummy_value = 0.0
        value_str = f'{dummy_value:1.2f}'.replace('0','O')
        text_color = constants.COLOR_TO_RGB['white']
        self.value2_label = label.Label(
                fonts.font_10pt, 
                text = value_str, 
                color = text_color, 
                scale = font_scale,
                anchor_point = self.ANCHOR_POINT,
                )
        self.value2_label.anchored_position = (
                self.VALUE2_LABEL_X_POSITION, 
                self.VALUE2_LABEL_Y_POSITION,
                )

        # Create text label for gain 2 information
        gain_str = 'gain xxx' 
        text_color = constants.COLOR_TO_RGB['orange']
        self.gain2_label = label.Label(
                fonts.font_10pt, 
                text=gain_str, 
                color=text_color, 
                scale=font_scale,
                anchor_point = self.ANCHOR_POINT,
                )
        self.gain2_label.anchored_position = (
                self.GAIN2_LABEL_X_POSITION,
                self.GAIN2_LABEL_Y_POSITION,
                )

        # Create text label for integration time 1 information
        itime_str = 'time xxxms' 
        text_color = constants.COLOR_TO_RGB['orange']
        self.itime2_label = label.Label(
                fonts.font_10pt, 
                text=itime_str, 
                color=text_color, 
                scale=font_scale,
                anchor_point = self.ANCHOR_POINT,
                )
        self.itime2_label.anchored_position = (
                self.ITIME2_LABEL_X_POSITION,
                self.ITIME2_LABEL_Y_POSITION,
                )

        # Create integration time/window text label
        #bat_str = 'battery 100%'
        bat_str = 'battery 0.0V'
        text_color = constants.COLOR_TO_RGB['gray']
        self.bat_label = label.Label(
                fonts.font_10pt, 
                text = bat_str, 
                color = text_color, 
                scale = font_scale,
                anchor_point = self.ANCHOR_POINT,
                )
        self.bat_label.anchored_position = (        
                self.BATTERY_LABEL_X_POSITION,
                self.BATTERY_LABEL_Y_POSITION,
                )
        
        # Ceate display group and add items to it
        self.group = displayio.Group()
        self.group.append(self.tile_grid)
        self.group.append(self.header1_label)
        self.group.append(self.value1_label)
        self.group.append(self.gain1_label)
        self.group.append(self.itime1_label)
        self.group.append(self.header2_label)
        self.group.append(self.value2_label)
        self.group.append(self.gain2_label)
        self.group.append(self.itime2_label)
        self.group.append(self.bat_label)

        self.header_labels = (self.header1_label, self.header2_label)
        self.value_labels = (self.value1_label, self.value2_label)

    @property
    def has_selected_sensor(self):
        return True

    def setup_selected_sensor_cycle(self):
        select_sensor_values = [None] + self.SENSOR_INDICES
        self.selected_sensor_cycle = adafruit_itertools.cycle(select_sensor_values)
        while next(self.selected_sensor_cycle) != self.selected_sensor:
            continue

    def selected_sensor_next(self):
        self.selected_sensor = next(self.selected_sensor_cycle)

    def set_measurement(self, measurement):
        measurement_items = ( 
                self.SENSOR_INDICES, 
                measurement.label, 
                measurement.value, 
                self.header_labels, 
                self.value_labels,
                )
        for index, name, value, header_label, value_label in zip(*measurement_items):
            if index == self.selected_sensor:
                mark = '|'
            else:
                mark = ' '
            header_label.text = f'{mark}{name}'
            if measurement.units is None:
                if type(value) == float:
                    value_text = f'{value:1.2f}'
                else: 
                    value_text = f'{value}'
            else:
                if type(value) == float:
                    value_text = f'{value:1.2f} {measurement.units}'
                else: 
                    value_text = f'{value} {measurement.units}'
            value_label.text = value_text.replace('0','O')
            if value == constants.OVERFLOW_STR:
                color = constants.COLOR_TO_RGB['red']
            else:
                color = constants.COLOR_TO_RGB['white']
            value_label.color = color

    def set_gain(self,values):
        labels = (self.gain1_label, self.gain2_label)
        for value, label in zip(values, labels):
            if value is not None:
                value_str = constants.GAIN_TO_STR[value]
                label.text = f'gain={value_str}'
            else:
                label.text = ''

    def set_integration_time(self,values):
        labels = (self.itime1_label, self.itime2_label)
        for value, label in zip(values, labels):
            if value is not None:
                value_str = constants.INTEGRATION_TIME_TO_STR[value]
                label.text = f'time={value_str}'
            else:
                label.text = ''

    def set_bat(self, value):
        self.bat_label.text = f'battery {value:1.1f}V'

    def show(self):
        board.DISPLAY.root_group = self.group

    def update(self, measurement, battery_monitor): 
        self.set_measurement(measurement)
        self.set_gain((
            measurement.sensor_90.gain, 
            measurement.sensor_180.gain,
            ))
        self.set_integration_time((
            measurement.sensor_90.integration_time, 
            measurement.sensor_180.integration_time,
            ))
        self.set_bat(battery_monitor.voltage_lowpass)

