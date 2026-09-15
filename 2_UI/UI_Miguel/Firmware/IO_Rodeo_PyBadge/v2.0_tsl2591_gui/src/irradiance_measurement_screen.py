import board
import displayio
import constants
import fonts
import adafruit_itertools
from adafruit_display_text import label


class IrradianceMeasurementScreen:


    ANCHOR_POINT = (0.0, 0.5)

    HEADER_TO_VALUE_SPACING = 22

    HEADER1_LABEL_X_POSITION = 5 
    HEADER1_LABEL_Y_POSITION = 12 

    VALUE1_LABEL_X_POSITION = 20
    VALUE1_LABEL_Y_POSITION = HEADER1_LABEL_Y_POSITION + HEADER_TO_VALUE_SPACING

    UNITS1_LABEL_X_POSITION = 90 
    UNITS1_LABEL_Y_POSITION = VALUE1_LABEL_Y_POSITION

    HEADER2_LABEL_X_POSITION = HEADER1_LABEL_X_POSITION
    HEADER2_LABEL_Y_POSITION = 64 

    VALUE2_LABEL_X_POSITION = VALUE1_LABEL_X_POSITION
    VALUE2_LABEL_Y_POSITION = HEADER2_LABEL_Y_POSITION + HEADER_TO_VALUE_SPACING

    UNITS2_LABEL_X_POSITION = UNITS1_LABEL_X_POSITION
    UNITS2_LABEL_Y_POSITION = VALUE2_LABEL_Y_POSITION

    BATTERY_LABEL_X_POSITION = 30      
    BATTERY_LABEL_Y_POSITION = 114

    SENSOR_INDICES = [0,1]


    def __init__(self):
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
        text_color = constants.COLOR_TO_RGB['orange']
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

        # Create units1 text label
        units_str = ' '
        text_color = constants.COLOR_TO_RGB['orange']
        self.units1_label = label.Label(
                fonts.font_10pt, 
                text = units_str, 
                color = text_color, 
                scale = font_scale,
                anchor_point = self.ANCHOR_POINT,
                )
        self.units1_label.anchored_position = (
                self.UNITS1_LABEL_X_POSITION,
                self.UNITS1_LABEL_Y_POSITION, 
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
        text_color = constants.COLOR_TO_RGB['orange']
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

        # Create units2 text label
        units_str = ' '
        text_color = constants.COLOR_TO_RGB['orange']
        self.units2_label = label.Label(
                fonts.font_10pt, 
                text = units_str, 
                color = text_color, 
                scale = font_scale,
                anchor_point = self.ANCHOR_POINT,
                )
        self.units2_label.anchored_position = (
                self.UNITS2_LABEL_X_POSITION,
                self.UNITS2_LABEL_Y_POSITION, 
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
        self.group.append(self.units1_label)
        self.group.append(self.header2_label)
        self.group.append(self.value2_label)
        self.group.append(self.units2_label)
        self.group.append(self.bat_label)

        self.header_labels = (self.header1_label, self.header2_label)
        self.value_labels  = (self.value1_label,  self.value2_label)
        self.units_labels  = (self.units1_label,  self.units2_label)

    @property
    def has_selected_sensor(self):
        return False 

    def set_measurement(self, measurement):
        measurement_items = ( 
                measurement.label, 
                measurement.value, 
                self.header_labels, 
                self.value_labels,
                self.units_labels,
                )
        for name, value, header_label, value_label, units_label in zip(*measurement_items):
            header_label.text = f'{name}'
            if type(value) == float:
                if value <= 10:
                    value_text = f'{value:.3f}'
                else:
                    value_text = f'{value:.2f}'
            else: 
                value_text = f'{value}'
            value_label.text = value_text.replace('0','O')
            if measurement.units is None:
                units_text = ''
            else:
                units_text = f'{measurement.units}'
            units_label.text = units_text
                
            if value == constants.OVERFLOW_STR:
                color = constants.COLOR_TO_RGB['red']
            else:
                color = constants.COLOR_TO_RGB['orange']
            value_label.color = color

    def set_bat(self, value):
        self.bat_label.text = f'battery {value:1.1f}V'

    def show(self):
        board.DISPLAY.root_group = self.group

    def update(self, measurement, battery_monitor): 
        self.set_measurement(measurement)
        self.set_bat(battery_monitor.voltage_lowpass)

