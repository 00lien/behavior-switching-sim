import unittest
from unittest.mock import MagicMock
from .factory import Factory, Drone

class TestBuilder(unittest.TestCase):
    def test_drone_builder(self):
        d = Factory.buildCommonDrone('123.134.13.2')
        assert type(d) is Drone
        assert d.getIp() == '123.134.13.2'

    def test_drone_builder_command_send(self):
        d = Factory.buildCommonDrone('123.134.13.2')
        d.LOGGER.info = MagicMock()
        d.send_command("hello")
        assert d.LOGGER.info.called