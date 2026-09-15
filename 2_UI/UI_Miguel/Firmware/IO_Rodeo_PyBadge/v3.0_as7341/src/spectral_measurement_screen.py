import board
import displayio
import constants
import fonts
from adafruit_display_text import label


class SpectralMeasurementScreen:

    ROW_COUNT = 5

    def __init__(self):
        self.color_to_index = {
                key:index for index, key in enumerate(constants.COLOR_TO_RGB)
                }
        self.palette = displayio.Palette(len(constants.COLOR_TO_RGB))
        for index, color_tuple in enumerate(constants.COLOR_TO_RGB.items()):
            self.palette[index] = color_tuple[1]

        self.bitmap = displayio.Bitmap(
                board.DISPLAY.width,
                board.DISPLAY.height,
                len(constants.COLOR_TO_RGB),
                )
        self.bitmap.fill(self.color_to_index['black'])
        self.tile_grid = displayio.TileGrid(
                self.bitmap,
                pixel_shader=self.palette,
                )

        self.header_label = label.Label(
                fonts.font_10pt,
                text='Multichannel @90',
                color=constants.COLOR_TO_RGB['white'],
                anchor_point=(0.5, 0.5),
                anchored_position=(board.DISPLAY.width//2, 9),
                )

        self.row_labels = []
        for row in range(self.ROW_COUNT):
            y_position = 25 + row*17
            row_label = label.Label(
                    fonts.font_10pt,
                    text='---nm       -----',
                    color=constants.COLOR_TO_RGB['orange'],
                    anchor_point=(0.0, 0.5),
                    anchored_position=(5, y_position),
                    )
            self.row_labels.append(row_label)

        self.settings_label = label.Label(
                fonts.font_10pt,
                text='G--- T---',
                color=constants.COLOR_TO_RGB['gray'],
                anchor_point=(0.0, 0.5),
                anchored_position=(4, 116),
                )
        self.page_label = label.Label(
                fonts.font_10pt,
                text='1/2',
                color=constants.COLOR_TO_RGB['gray'],
                anchor_point=(0.5, 0.5),
                anchored_position=(115, 116),
                )
        self.bat_label = label.Label(
                fonts.font_10pt,
                text='0.0V',
                color=constants.COLOR_TO_RGB['gray'],
                anchor_point=(1.0, 0.5),
                anchored_position=(158, 116),
                )

        self.group = displayio.Group()
        self.group.append(self.tile_grid)
        self.group.append(self.header_label)
        for row_label in self.row_labels:
            self.group.append(row_label)
        self.group.append(self.settings_label)
        self.group.append(self.page_label)
        self.group.append(self.bat_label)

    @property
    def has_selected_sensor(self):
        return False

    def set_measurement(self, measurement):
        values = measurement.value
        start = measurement.page*self.ROW_COUNT
        stop = start + self.ROW_COUNT

        for row_label, name, value in zip(
                self.row_labels,
                measurement.label[start:stop],
                values[start:stop],
                ):
            row_label.text = '{:<7} {:>8}'.format(
                    name,
                    str(value).replace('0', 'O'),
                    )
            if value == constants.OVERFLOW_STR:
                row_label.color = constants.COLOR_TO_RGB['red']
            else:
                row_label.color = constants.COLOR_TO_RGB['orange']

        self.settings_label.text = 'G{} T{}'.format(
                measurement.sensor_90.gain_str.replace('x', ''),
                measurement.sensor_90.integration_time_str.replace('ms', ''),
                )
        self.page_label.text = '{}/2'.format(measurement.page + 1)

    def set_bat(self, value):
        self.bat_label.text = f'{value:1.1f}V'

    def show(self):
        board.DISPLAY.root_group = self.group

    def update(self, measurement, battery_monitor):
        self.set_measurement(measurement)
        self.set_bat(battery_monitor.voltage_lowpass)
