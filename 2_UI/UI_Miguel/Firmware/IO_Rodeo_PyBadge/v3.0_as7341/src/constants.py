import board
import collections
import adafruit_as7341
import adafruit_tsl2591

__version__ = '0.1.2-upch'

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

TSL2591_STR_TO_GAIN = collections.OrderedDict([
        ('low'  , adafruit_tsl2591.GAIN_LOW ),
        ('med'  , adafruit_tsl2591.GAIN_MED ),
        ('high' , adafruit_tsl2591.GAIN_HIGH),
        ('max'  , adafruit_tsl2591.GAIN_MAX ),
        ])
TSL2591_GAIN_TO_STR = collections.OrderedDict(
        ((v,k) for k,v in TSL2591_STR_TO_GAIN.items())
        )

TSL2591_STR_TO_INTEGRATION_TIME = collections.OrderedDict([
        ('100ms', adafruit_tsl2591.INTEGRATIONTIME_100MS),
        ('200ms', adafruit_tsl2591.INTEGRATIONTIME_200MS),
        ('300ms', adafruit_tsl2591.INTEGRATIONTIME_300MS),
        ('400ms', adafruit_tsl2591.INTEGRATIONTIME_400MS),
        ('500ms', adafruit_tsl2591.INTEGRATIONTIME_500MS),
        ('600ms', adafruit_tsl2591.INTEGRATIONTIME_600MS),
        ])
TSL2591_INTEGRATION_TIME_TO_STR = collections.OrderedDict(
        ((v,k) for k,v in TSL2591_STR_TO_INTEGRATION_TIME.items())
        )

AS7341_STR_TO_GAIN = collections.OrderedDict([
        ('0.5x', adafruit_as7341.Gain.GAIN_0_5X),
        ('1x',   adafruit_as7341.Gain.GAIN_1X),
        ('2x',   adafruit_as7341.Gain.GAIN_2X),
        ('4x',   adafruit_as7341.Gain.GAIN_4X),
        ('8x',   adafruit_as7341.Gain.GAIN_8X),
        ('16x',  adafruit_as7341.Gain.GAIN_16X),
        ('32x',  adafruit_as7341.Gain.GAIN_32X),
        ('64x',  adafruit_as7341.Gain.GAIN_64X),
        ('128x', adafruit_as7341.Gain.GAIN_128X),
        ('256x', adafruit_as7341.Gain.GAIN_256X),
        ('512x', adafruit_as7341.Gain.GAIN_512X),
        ])
AS7341_GAIN_TO_STR = collections.OrderedDict(
        ((v,k) for k,v in AS7341_STR_TO_GAIN.items())
        )

# ASTEP=999. El tiempo resultante es
# (ATIME + 1) * (ASTEP + 1) * 2.78 microsegundos.
AS7341_STR_TO_INTEGRATION_TIME = collections.OrderedDict([
        ('50ms',  (17, 999)),
        ('100ms', (35, 999)),
        ('200ms', (71, 999)),
        ('300ms', (107, 999)),
        ('400ms', (143, 999)),
        ('600ms', (215, 999)),
        ])
AS7341_INTEGRATION_TIME_TO_STR = collections.OrderedDict(
        ((v,k) for k,v in AS7341_STR_TO_INTEGRATION_TIME.items())
        )

# Alias del firmware latest para el TSL2591 de 180 grados.
STR_TO_GAIN = TSL2591_STR_TO_GAIN
GAIN_TO_STR = TSL2591_GAIN_TO_STR
STR_TO_INTEGRATION_TIME = TSL2591_STR_TO_INTEGRATION_TIME
INTEGRATION_TIME_TO_STR = TSL2591_INTEGRATION_TIME_TO_STR

CHANNEL_NAMES_90 = (
        '415nm',
        '445nm',
        '480nm',
        '515nm',
        '555nm',
        '590nm',
        '630nm',
        '680nm',
        'NIR',
        'clear',
        )
NUM_CHANNELS_90 = len(CHANNEL_NAMES_90)

OVERFLOW_STR = 'OVFL'
ABOUT_STR = 'About'
MU_STR = '\u03BC'
CM2_STR = 'cm\u00B2'
