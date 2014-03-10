from collections import deque
import math

import Adafruit_BBIO.ADC as ADC
import tornado.ioloop

HIGH_RESIST = 10000

class Probe(object):
    """
    Controller for a temperature probe
    """
    def __init__(self, probe_type, probe_pin):
        """
        Initializes the controller for a temperature probe

        :param probe_type: The model of the probe
        :type probe_type: str
        :param probe_pin: The BBB ADC pin to use, e.g. P9_39
        :type probe_pin: str
        """
        if 'Maverick ET-72/73' == probe_type:
            self._sh_a = 2.4723753e-04
            self._sh_b = 2.3402251e-04
            self._sh_c = 1.3879768e-07
        elif 'Thermoworks Pro-Series' == probe_type:
            self._sh_a = 6.6853001e-04
            self._sh_b = 2.2231022e-04
            self._sh_c = 9.9680632e-08
        else:
            raise ValueError('Unspported thermal probe type')

        # Going to call a temperature read every 10 seconds so keep the last minute's worth
        self._readings = deque(maxlen=6)

        self._probe_pin = probe_pin

        ADC.setup()

        # Take a temperature immediately
        self._take_temperature()

        # Setup a periodic call every 10 seconds to take the temperature
        self._periodic_temp = tornado.ioloop.PeriodicCallback(
            self._take_temperature,
            10000)
        self._periodic_temp.start()
        
    @property
    def temperature(self):
        """
        Returns the average of the last minute's worth of temperature readings

        :returns: The current temperature
        :rtype: int
        """
        return sum(self._readings)/len(self._readings)
    
    def _take_temperature(self):
        """
        Takes a temperature reading from the probe

        Reads the ADC and uses the Steinhart-Hart equation to convert the read
        voltage to degrees fahrenheit.  Appends the results to the internal queue
        """
        value = ADC.read(self._probe_pin)
        resistance = (HIGH_RESIST * value) / (1 - value)
        invert_temp_k = self._sh_a + self._sh_b * math.log(resistance) + \
            self._sh_c * math.pow(math.log(resistance), 3)
        temp_k = 1 / invert_temp_k
        temp_f = (9.0 / 5.0) * (temp_k - 273.15) + 32
       
        self._readings.append(temp_f) 
