import board
import collections
import adafruit_tsl2591

__version__ = '0.1.1'

CALIBRATIONS_FILE = 'calibrations.json'
CONFIGURATION_FILE = 'configuration.json'
SPLASHSCREEN_BMP = 'assets/splashscreen.bmp'

LOOP_DT = 0.1
BLANK_DT = 0.05
DEBOUNCE_DT = 0.6 
NUM_BLANK_SAMPLES = 50 
BATTERY_AIN_PIN = board.A6

DEFAULT_REF_IRRADIANCE_180 = 1000.0
NUM_SAMPLE_180 = 10

BUTTON = { 
        'left'  : 7,
        'up'    : 6, 
        'down'  : 5, 
        'right' : 4, 
        'menu'  : 3, 
        'norm'  : 2, 
        'itime' : 1, 
        'gain'  : 0, 
        }

COLOR_TO_RGB = collections.OrderedDict([ 
    ('black'  , 0x000000), 
    ('gray'   , 0x818181), 
    ('red'    , 0xff0000), 
    ('green'  , 0x00ff00),
    ('blue'   , 0x0000ff),
    ('white'  , 0xffffff), 
    ('orange' , 0xffb447),
    ])

STR_TO_GAIN = collections.OrderedDict([
        ('low'  , adafruit_tsl2591.GAIN_LOW ),
        ('med'  , adafruit_tsl2591.GAIN_MED ),
        ('high' , adafruit_tsl2591.GAIN_HIGH),
        ('max'  , adafruit_tsl2591.GAIN_MAX ),
        ])
GAIN_TO_STR = {v:k for k,v in STR_TO_GAIN.items()}

STR_TO_INTEGRATION_TIME = collections.OrderedDict([
        ('100ms', adafruit_tsl2591.INTEGRATIONTIME_100MS),
        ('200ms', adafruit_tsl2591.INTEGRATIONTIME_200MS),
        ('300ms', adafruit_tsl2591.INTEGRATIONTIME_300MS),
        ('400ms', adafruit_tsl2591.INTEGRATIONTIME_400MS),
        ('500ms', adafruit_tsl2591.INTEGRATIONTIME_500MS),
        ('600ms', adafruit_tsl2591.INTEGRATIONTIME_600MS),
        ])
INTEGRATION_TIME_TO_STR = {v:k for k,v in STR_TO_INTEGRATION_TIME.items()}

OVERFLOW_STR = 'OVFL'
ABOUT_STR = 'About'
MU_STR = '\u03BC'
CM2_STR = 'cm\u00B2'
