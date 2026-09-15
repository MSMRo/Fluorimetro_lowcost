import usb_cdc

# Deja la consola de CircuitPython intacta y habilita un segundo puerto CDC
# exclusivo para la GUI. Este archivo se ejecuta antes de code.py.
usb_cdc.enable(console=True, data=True)

