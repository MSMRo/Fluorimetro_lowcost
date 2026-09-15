"""Protocolo JSON Lines no bloqueante para el puerto USB CDC de datos."""

import json
import usb_cdc


class UsbSerialProtocol:
    """Intercambia comandos y telemetría sin interferir con la pantalla."""

    def __init__(self, serial_port=None):
        self.serial_port = serial_port if serial_port is not None else usb_cdc.data
        self._buffer = b''
        self._sequence = 0

    def send(self, message_type, **data):
        """Envía un mensaje JSON terminado en salto de línea."""
        self._sequence += 1
        message = {'type': message_type, 'sequence': self._sequence}
        message.update(data)
        payload = (json.dumps(message, separators=(',', ':')) + '\n').encode('utf-8')
        self.serial_port.write(payload)

    def poll_commands(self):
        """Devuelve los comandos completos que llegaron desde la GUI."""
        if self.serial_port.in_waiting:
            self._buffer += self.serial_port.read(self.serial_port.in_waiting)

        commands = []
        while b'\n' in self._buffer:
            raw_message, self._buffer = self._buffer.split(b'\n', 1)
            if not raw_message:
                continue
            try:
                message = json.loads(raw_message.decode('utf-8'))
            except (TypeError, ValueError):
                self.send('error', message='JSON inválido recibido desde la GUI.')
                continue
            if not isinstance(message, dict) or message.get('type') != 'command':
                self.send('error', message='Se esperaba un mensaje de tipo command.')
                continue
            commands.append(message)
        return commands
