import gc
import time
import busio
import board
import analogio
import digitalio
import keypad
import constants
import adafruit_itertools
import adafruit_tca9548a

import measurement
from light_sensor import LightSensorTSL2591
from light_sensor import LightSensorIOError

from battery_monitor import BatteryMonitor
from configuration import Configuration
from configuration import ConfigurationError
from menu_screen import MenuScreen
from message_screen import MessageScreen
from serial_protocol import UsbSerialProtocol

class Mode:
    MEASURE = 0
    MENU    = 1
    MESSAGE = 2
    ABORT   = 3


class Colorimeter:

    DEFAULT_MEASUREMENTS = [
            measurement.RawCount.NAME,
            measurement.Irradiance.NAME,
            measurement.RelativeUnit.NAME,
            ]
            
    def __init__(self):

        # Screens
        self.measurement_screen = None
        self.message_screen = None
        self.menu_screen = None
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
        self.serial_protocol = UsbSerialProtocol()

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
            self.light_sensor_90 = LightSensorTSL2591(self.i2c_mux[1])
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
        self.serial_protocol.send(
            'hello',
            firmware_version=constants.__version__,
            modes=self.DEFAULT_MEASUREMENTS,
            )
        self.send_state()


    def setup_gain_and_itime_cycles(self):
        self.gain_cycle_sensor_90 = adafruit_itertools.cycle(constants.GAIN_TO_STR) 
        while next(self.gain_cycle_sensor_90) != self.light_sensor_90.gain:
            continue

        self.itime_cycle_sensor_90 = adafruit_itertools.cycle(constants.INTEGRATION_TIME_TO_STR)
        while next(self.itime_cycle_sensor_90) != self.light_sensor_90.integration_time:
            continue

        self.gain_cycle_sensor_180 = adafruit_itertools.cycle(constants.GAIN_TO_STR) 
        while next(self.gain_cycle_sensor_180) != self.light_sensor_180.gain:
            continue

        self.itime_cycle_sensor_180 = adafruit_itertools.cycle(constants.INTEGRATION_TIME_TO_STR)
        while next(self.itime_cycle_sensor_180) != self.light_sensor_180.integration_time:
            continue

    def sensor_state(self):
        return {
            'sensor_90': {
                'gain': constants.GAIN_TO_STR[self.light_sensor_90.gain],
                'integration_time': constants.INTEGRATION_TIME_TO_STR[
                    self.light_sensor_90.integration_time],
                },
            'sensor_180': {
                'gain': constants.GAIN_TO_STR[self.light_sensor_180.gain],
                'integration_time': constants.INTEGRATION_TIME_TO_STR[
                    self.light_sensor_180.integration_time],
                },
            }

    def send_state(self):
        if not hasattr(self, 'light_sensors'):
            return
        mode_name = self.measurement.name if self.mode == Mode.MEASURE else 'Menu'
        self.serial_protocol.send(
            'state',
            mode=mode_name,
            sensors=self.sensor_state(),
            battery={'voltage': self.battery_monitor.voltage_lowpass},
            )

    def set_measurement_mode(self, measurement_name):
        if measurement_name not in self.DEFAULT_MEASUREMENTS:
            raise ValueError('Modo de medición desconocido.')
        self.menu_item_pos = self.menu_items.index(measurement_name)
        self.mode = Mode.MEASURE

    def set_sensor_setting(self, sensor_name, setting, value):
        sensors = {
            'sensor_90': self.light_sensor_90,
            'sensor_180': self.light_sensor_180,
            }
        sensor = sensors[sensor_name]
        if setting == 'gain':
            sensor.gain = constants.STR_TO_GAIN[value]
        elif setting == 'integration_time':
            sensor.integration_time = constants.STR_TO_INTEGRATION_TIME[value]
        else:
            raise ValueError('Configuración de sensor desconocida.')
        self.setup_gain_and_itime_cycles()

    def handle_serial_commands(self):
        for command_message in self.serial_protocol.poll_commands():
            command = command_message.get('command')
            try:
                if command == 'get_state':
                    pass
                elif command == 'set_mode':
                    self.set_measurement_mode(command_message['mode'])
                elif command == 'set_sensor_setting':
                    self.set_sensor_setting(
                        command_message['sensor'],
                        command_message['setting'],
                        command_message['value'],
                        )
                elif command == 'normalize':
                    self.measurement.update_norm_sample()
                else:
                    raise ValueError('Comando desconocido.')
            except (KeyError, ValueError, measurement.ZeroNormalizationSample) as error:
                self.serial_protocol.send('error', command=command, message=str(error))
            else:
                self.serial_protocol.send('ack', command=command)
                self.send_state()

    def display_value(self, value, is_count_measurement):
        if is_count_measurement and type(value) == float:
            value_text = f'{value:1.2f}'
        elif type(value) == float:
            if value <= 10:
                value_text = f'{value:.3f}'
            else:
                value_text = f'{value:.2f}'
        else:
            value_text = f'{value}'
        return value_text.replace('0', 'O')

    def send_telemetry(self):
        if self.mode != Mode.MEASURE:
            return
        labels = self.measurement.label
        values = self.measurement.value
        is_count = self.measurement.name == measurement.RawCount.NAME
        if type(labels) == tuple:
            telemetry_labels = {'sensor_90': labels[0], 'sensor_180': labels[1]}
            telemetry_values = {'sensor_90': values[0], 'sensor_180': values[1]}
        else:
            telemetry_labels = {'sensor_90': labels, 'sensor_180': None}
            telemetry_values = {'sensor_90': values, 'sensor_180': None}
        display_values = {
            'sensor_90': self.display_value(telemetry_values['sensor_90'], is_count),
            'sensor_180': (
                self.display_value(telemetry_values['sensor_180'], is_count)
                if telemetry_values['sensor_180'] is not None else ''
                ),
            }
        self.serial_protocol.send(
            'telemetry',
            mode=self.measurement.name,
            labels=telemetry_labels,
            values=telemetry_values,
            display_values=display_values,
            units=self.measurement.units,
            sensors=self.sensor_state(),
            battery={'voltage': self.battery_monitor.voltage_lowpass},
            )


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
            self.message_screen = MessageScreen()
        elif new_mode == Mode.MENU:
            self.menu_screen = MenuScreen()
            self.menu_view_pos = 0
            self.menu_item_pos = 0
            self.update_menu_screen()
        self._mode = new_mode

    def delete_screens(self):
        print('hi')
        self.measurement_screen = None 
        self.message_screen = None 
        self.menu_screen = None 
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
            if self.measurement_screen.has_selected_sensor:
                if self.measurement_screen.selected_sensor == 0:
                    self.set_sensor_setting(
                        'sensor_90',
                        'gain',
                        constants.GAIN_TO_STR[next(self.gain_cycle_sensor_90)],
                        )
                if self.measurement_screen.selected_sensor == 1:
                    self.set_sensor_setting(
                        'sensor_180',
                        'gain',
                        constants.GAIN_TO_STR[next(self.gain_cycle_sensor_180)],
                        )
        elif event.key_number == constants.BUTTON['itime']: 
            if self.measurement_screen.has_selected_sensor:
                if self.measurement_screen.selected_sensor == 0:
                    self.set_sensor_setting(
                        'sensor_90',
                        'integration_time',
                        constants.INTEGRATION_TIME_TO_STR[
                            next(self.itime_cycle_sensor_90)],
                        )
                if self.measurement_screen.selected_sensor == 1:
                    self.set_sensor_setting(
                        'sensor_180',
                        'integration_time',
                        constants.INTEGRATION_TIME_TO_STR[
                            next(self.itime_cycle_sensor_180)],
                        )
        elif event.key_number == constants.BUTTON['right']:
            if self.measurement_screen.has_selected_sensor:
                if self.measurement_screen.has_selected_sensor:
                    self.measurement_screen.selected_sensor_next()
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

            # Procesar primero las órdenes de la GUI. No bloquea la pantalla.
            self.handle_serial_commands()

            # Deal with any button presses
            self.handle_button_events()

            # Update display based on the current operating mode
            if self.mode == Mode.MEASURE:
                self.measurement_screen.update(self.measurement, self.battery_monitor)
                self.measurement_screen.show()
                self.send_telemetry()

            elif self.mode == Mode.MENU:
                self.menu_screen.show()

            elif self.mode in (Mode.MESSAGE, Mode.ABORT):
                self.message_screen.show()

            self.battery_monitor.update()
            time.sleep(constants.LOOP_DT)
            gc.collect()
