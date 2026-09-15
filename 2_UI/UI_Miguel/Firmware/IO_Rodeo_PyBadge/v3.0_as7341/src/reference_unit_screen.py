import board
import displayio
import constants
import fonts
import adafruit_itertools
from adafruit_display_text import label


class ReferenceUnitScreen:


    ANCHOR_POINT = (0.0, 0.5)

    HEADER_TO_VALUE_SPACING = 32

    HEADER_LABEL_X_POSITION = 5 
    HEADER_LABEL_Y_POSITION = 22 

    VALUE_LABEL_X_POSITION = 20
    VALUE_LABEL_Y_POSITION = HEADER_LABEL_Y_POSITION + HEADER_TO_VALUE_SPACING

    UNITS_LABEL_X_POSITION = 90 
    UNITS_LABEL_Y_POSITION = VALUE_LABEL_Y_POSITION

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

        # Create header text label
        header_str = 'header'
        text_color = constants.COLOR_TO_RGB['white']
        self.header_label = label.Label(
                fonts.font_10pt, 
                text = header_str, 
                color = text_color, 
                scale = font_scale,
                anchor_point = self.ANCHOR_POINT,
                )
        self.header_label.anchored_position = ( 
                self.HEADER_LABEL_X_POSITION, 
                self.HEADER_LABEL_Y_POSITION,
                )

        # Create value text label
        dummy_value = 0.0
        value_str = f'{dummy_value:1.2f}'.replace('0','O')
        text_color = constants.COLOR_TO_RGB['orange']
        self.value_label = label.Label(
                fonts.font_10pt, 
                text = value_str, 
                color = text_color, 
                scale = font_scale,
                anchor_point = self.ANCHOR_POINT,
                )
        self.value_label.anchored_position = (
                self.VALUE_LABEL_X_POSITION,
                self.VALUE_LABEL_Y_POSITION, 
                )

        # Create units text label
        units_str = ' '
        text_color = constants.COLOR_TO_RGB['orange']
        self.units_label = label.Label(
                fonts.font_10pt, 
                text = units_str, 
                color = text_color, 
                scale = font_scale,
                anchor_point = self.ANCHOR_POINT,
                )
        self.units_label.anchored_position = (
                self.UNITS_LABEL_X_POSITION,
                self.UNITS_LABEL_Y_POSITION, 
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
        self.group.append(self.header_label)
        self.group.append(self.value_label)
        self.group.append(self.units_label)
        self.group.append(self.bat_label)

    @property
    def has_selected_sensor(self):
        return False 

    def set_measurement(self, measurement):
        name  = measurement.label
        value = measurement.value
        units = measurement.units
        self.header_label.text = f'{name}'
        if type(value) == float:
            if value <= 10:
                value_text = f'{value:.3f}'
            else:
                value_text = f'{value:.2f}'
        else: 
            value_text = f'{value}'
        self.value_label.text = value_text.replace('0','O')
        if measurement.units is None:
            units_text = ''
        else:
            units_text = f'{units}'
        self.units_label.text = units_text
            
        if value == constants.OVERFLOW_STR:
            color = constants.COLOR_TO_RGB['red']
        else:
            color = constants.COLOR_TO_RGB['orange']
        self.value_label.color = color

    def set_bat(self, value):
        self.bat_label.text = f'battery {value:1.1f}V'

    def show(self):
        board.DISPLAY.root_group = self.group

    def update(self, measurement, battery_monitor): 
        self.set_measurement(measurement)
        self.set_bat(battery_monitor.voltage_lowpass)

