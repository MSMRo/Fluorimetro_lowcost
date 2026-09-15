import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from exporter import CsvExporter
from telemetry_writer import TelemetryWriter
from test_experiments import frame


class FlakyExporter(CsvExporter):
    def __init__(self, path):
        super().__init__(path)
        self.fail_next = True

    def append(self, received_at, telemetry):
        if self.fail_next:
            self.fail_next = False
            raise OSError('fallo simulado')
        super().append(received_at, telemetry)


class TelemetryWriterTests(unittest.TestCase):
    def test_exporter_can_be_used_after_error_is_consumed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            primary = CsvExporter(root / 'session.csv')
            secondary = FlakyExporter(root / 'record.csv')
            writer = TelemetryWriter(primary)
            now = datetime.now(timezone.utc)
            writer.append(now, frame(), secondary)
            self.assertTrue(writer.drain())
            self.assertEqual(writer.take_error(secondary), 'fallo simulado')
            writer.append(now, frame(seq=2), secondary)
            self.assertTrue(writer.drain())
            self.assertEqual(secondary.count, 1)
            self.assertTrue(writer.close())


if __name__ == '__main__':
    unittest.main()
