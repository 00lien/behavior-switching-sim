import unittest
from pubsub import pub
from .drone_trajectory import NBPlot
import numpy as np
import random
import time

class TestBuilder(unittest.TestCase):
    def test_drone_builder(self):
        n = NBPlot(figure_width=15)
        n.plot(None)

        for i in range(100):
            pub.sendMessage('odo', loc = [
                {
                    'ip': '1',
                    'x': random.uniform(-5, 5),
                    'y': random.uniform(-5, 5),
                    'z': random.uniform(-5, 5),
                }
            ])
            time.sleep(0.1)