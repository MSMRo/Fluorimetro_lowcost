import gc
import sys
import time
import busio
import board
import keypad
import constants
import adafruit_itertools
import adafruit_tca9548a

import measurement
from light_sensor import LightSensorAS7341
from light_sensor import LightSensorTSL2591
from light_sensor import LightSensorIOError

from battery_monitor import BatteryMonitor
from configuration import Configuration
from configuration import ConfigurationError

class Mode:
    MEASURE = 0
    MENU    = 1
    MESSAGE = 2
    ABORT   = 3


class Colorimeter:

    SCREEN_MODULES = (
            'count_measurement_screen',
            'reference_unit_screen',
            'spectral_measurement_screen',
            'menu_screen',
            'message_screen',
            )

    DEFAULT_MEASUREMENTS = [
            measurement.RawCount.NAME,
            measurement.RelativeUnit.NAME,
            measurement.Multichannel90.NAME,
            ]
            
    def __init__(self):

        # Screens
        self.measurement_screen = None
        self.message_screen = None
        self.menu_screen = None
        self.measurement = None
        board.DISPLAY.brightness = 1.0

        self.menu_items = list(self.DEFAULT_MEASUREMENTS)
        self.menu_items.append(constants.ABOUT_STR)
        self.menu_view_pos = 0
        self.menu_item_pos = 0

        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.i2c_mux = adafruit_tca9548a.PCA9546A(self.i2c)

        self.pad = keypad.ShiftRegisterKeys( 
                clock=board.BUTTON_CLOCK, 
                data=board.BUTTON_OUT, 
                latch=board.BUTTON_LATCH, 
                key_count=8, 
                value_when_pressed=True,
                )

        # Load Configuration
        self.configuration = Configuration()
        try:
            self.configuration.load()
        except ConfigurationError as error:
            # Unable to load configuration file or not a dict after loading
            self.mode = Mode.MESSAGE
            self.message_screen.set_message(error)
            self.message_screen.set_to_error()

        # Setup 90 degree light sensor 
        try:
            self.light_sensor_90 = LightSensorAS7341(self.i2c_mux[3])
        except LightSensorIOError as error:
            self.mode = Mode.ABORT
            error_msg = f'missing sensor? {error}'
            self.message_screen.set_message(error_msg,ok_to_continue=False)
            self.message_screen.set_to_abort()
        else:
            if self.configuration.gain_sensor_90 is not None:
                self.light_sensor_90.gain = self.configuration.gain_sensor_90
            if self.configuration.itime_sensor_90 is not None:
                self.light_sensor_90.integration_time = self.configuration.itime_sensor_90

        # Setup 180 degree light sensor 
        try:
            self.light_sensor_180 = LightSensorTSL2591(self.i2c_mux[0])
        except LightSensorIOError as error:
            self.mode = Mode.ABORT
            error_msg = f'missing sensor? {error}'
            self.message_screen.set_message(error_msg,ok_to_continue=False)
            self.message_screen.set_to_abort()
        else:
            if self.configuration.gain_sensor_180 is not None:
                self.light_sensor_180.gain = self.configuration.gain_sensor_180
            if self.configuration.itime_sensor_180 is not None:
                self.light_sensor_180.integration_time = self.configuration.itime_sensor_180

        self.light_sensors = self.light_sensor_90, self.light_sensor_180

        # Set default/startup measurement
        if self.configuration.startup in self.menu_items:
            measurement_name = self.configuration.startup
        else:
            if self.configuration.startup is not None:
                self.mode = Mode.MESSAGE
                error_msg = f'startup measurement {self.configuration.startup} not found'
                self.message_screen.set_message(error_msg)
                self.message_screen.set_to_error()
            measurement_name = self.menu_items[0] 
        self.menu_item_pos = self.menu_items.index(measurement_name)
        self.mode = Mode.MEASURE

            
        # Setup up battery monitoring settings cycles 
        self.battery_monitor = BatteryMonitor()
        self.setup_gain_and_itime_cycles()


    def setup_gain_and_itime_cycles(self):
        self.gain_cycle_sensor_90 = adafruit_itertools.cycle(
                constants.AS7341_GAIN_TO_STR
                )
        gain_config = self.configuration.gain_sensor_90
        if gain_config is not None:
            while next(self.gain_cycle_sensor_90) != gain_config: 
                continue

        self.itime_cycle_sensor_90 = adafruit_itertools.cycle(
                constants.AS7341_INTEGRATION_TIME_TO_STR
                )
        itime_config = self.configuration.itime_sensor_90
        if itime_config is not None:
            while next(self.itime_cycle_sensor_90) != itime_config:
                continue

        self.gain_cycle_sensor_180 = adafruit_itertools.cycle(
                constants.TSL2591_GAIN_TO_STR
                )
        gain_config = self.configuration.gain_sensor_180
        if gain_config is not None:
            while next(self.gain_cycle_sensor_180) != gain_config: 
                continue

        self.itime_cycle_sensor_180 = adafruit_itertools.cycle(
                constants.TSL2591_INTEGRATION_TIME_TO_STR
                )
        itime_config = self.configuration.itime_sensor_180
        if itime_config is not None:
            while next(self.itime_cycle_sensor_180) != itime_config:
                continue


    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, new_mode):
        self.delete_screens()
        if new_mode == Mode.MEASURE:
            measurement_name = self.menu_items[self.menu_item_pos]
            self.measurement = measurement.from_name(
                    measurement_name, 
                    self.light_sensors,
                    self.configuration,
                    )
            self.measurement_screen = self.measurement.create_screen()
        elif new_mode in (Mode.MESSAGE, Mode.ABORT):
            from message_screen import MessageScreen

            self.message_screen = MessageScreen()
        elif new_mode == Mode.MENU:
            from menu_screen import MenuScreen

            self.menu_screen = MenuScreen()
            self.menu_view_pos = 0
            self.menu_item_pos = 0
            self.update_menu_screen()
        self._mode = new_mode

    def delete_screens(self):
        board.DISPLAY.root_group = None
        self.measurement_screen = None
        self.message_screen = None
        self.menu_screen = None
        self.measurement = None
        gc.collect()
        for module_name in self.SCREEN_MODULES:
            if module_name in sys.modules:
                del sys.modules[module_name]
        gc.collect()
    

    @property
    def num_menu_items(self):
        return len(self.menu_items)

    def incr_menu_item_pos(self):
        if self.menu_item_pos < self.num_menu_items-1:
            self.menu_item_pos += 1
        diff_pos = self.menu_item_pos - self.menu_view_pos
        if diff_pos > self.menu_screen.items_per_screen-1:
            self.menu_view_pos += 1

    def decr_menu_item_pos(self):
        if self.menu_item_pos > 0:
            self.menu_item_pos -= 1
        if self.menu_item_pos < self.menu_view_pos:
            self.menu_view_pos -= 1

    def update_menu_screen(self):
        if self.menu_screen is not None:
            n0 = self.menu_view_pos
            n1 = n0 + self.menu_screen.items_per_screen
            view_items = []
            for i, item in enumerate(self.menu_items[n0:n1]):
                item_text = f'{n0+i} {item}' 
                view_items.append(item_text)
            self.menu_screen.set_menu_items(view_items)
            pos = self.menu_item_pos - self.menu_view_pos
            self.menu_screen.set_curr_item(pos)

    def handle_button_events(self):
        event = self.pad.events.get()
        if self.mode == Mode.MEASURE:
            self.on_measure_mode_button(event)
        elif self.mode == Mode.MENU:
            self.on_menu_mode_button(event)
        elif self.mode == Mode.MESSAGE: 
            self.on_message_mode_button(event)

    def on_measure_mode_button(self, event): 
        if event is None or event.pressed:
            return
        if event.key_number == constants.BUTTON['menu']:
            self.mode = Mode.MENU
            self.menu_view_pos = 0
            self.menu_item_pos = 0
            self.update_menu_screen()
        elif event.key_number == constants.BUTTON['gain']: 
            if self.measurement.is_multichannel:
                self.light_sensor_90.gain = next(self.gain_cycle_sensor_90)
            elif self.measurement_screen.has_selected_sensor:
                if self.measurement_screen.selected_sensor == 0:
                    self.light_sensor_90.gain = next(self.gain_cycle_sensor_90)
                if self.measurement_screen.selected_sensor == 1:
                    self.light_sensor_180.gain = next(self.gain_cycle_sensor_180)
        elif event.key_number == constants.BUTTON['itime']: 
            if self.measurement.is_multichannel:
                self.light_sensor_90.integration_time = next(
                        self.itime_cycle_sensor_90
                        )
            elif self.measurement_screen.has_selected_sensor:
                if self.measurement_screen.selected_sensor == 0:
                    self.light_sensor_90.integration_time = next(self.itime_cycle_sensor_90)
                if self.measurement_screen.selected_sensor == 1:
                    self.light_sensor_180.integration_time = next(self.itime_cycle_sensor_180)
        elif event.key_number == constants.BUTTON['right']:
            if self.measurement.is_multichannel:
                self.measurement.next_page()
            elif self.measurement_screen.has_selected_sensor:
                if self.measurement_screen.has_selected_sensor:
                    self.measurement_screen.selected_sensor_next()
        elif event.key_number == constants.BUTTON['left']:
            if self.measurement.is_multichannel:
                self.measurement.previous_page()
        elif event.key_number == constants.BUTTON['norm']:
            self.measurement.update_norm_sample()

    def on_menu_mode_button(self, event): 
        if event is None or event.pressed:
            return
        if event.key_number == constants.BUTTON['menu']: 
            self.mode = Mode.MEASURE
        elif event.key_number == constants.BUTTON['up']: 
            self.decr_menu_item_pos()
        elif event.key_number == constants.BUTTON['down']: 
            self.incr_menu_item_pos()
        elif event.key_number == constants.BUTTON['right']: 
            selected_item = self.menu_items[self.menu_item_pos]
            if selected_item == constants.ABOUT_STR:
                self.mode = Mode.MESSAGE
                about_msg = f'firmware version {constants.__version__}'
                self.message_screen.set_message(about_msg) 
                self.message_screen.set_to_about()
            else:
                self.mode = Mode.MEASURE
        self.update_menu_screen()

    def on_message_mode_button(self, event):
        if event is None or event.pressed:
            return
        if event.key_number == constants.BUTTON['menu']: 
            self.mode = Mode.MENU

    def run(self):
        while True:

            # Deal with any button presses
            self.handle_button_events()

            # Update display based on the current operating mode
            if self.mode == Mode.MEASURE:
                self.measurement_screen.update(self.measurement, self.battery_monitor)
                self.measurement_screen.show()

            elif self.mode == Mode.MENU:
                self.menu_screen.show()

            elif self.mode in (Mode.MESSAGE, Mode.ABORT):
                self.message_screen.show()

            self.battery_monitor.update()
            time.sleep(constants.LOOP_DT)
            gc.collect()
