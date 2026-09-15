import gc
import board
import sys
sys.path.append('src')
from splash_screen import SplashScreen

# Show splash screen and display while other stuff loads
splash_screen = SplashScreen()
splash_screen.show()

# Import and start colorimeter
from colorimeter import Colorimeter 

# Release the splash bitmap before constructing the application screens.
board.DISPLAY.root_group = None
splash_screen = None
if 'splash_screen' in sys.modules:
    del sys.modules['splash_screen']
gc.collect()

colorimeter = Colorimeter()
colorimeter.run()
