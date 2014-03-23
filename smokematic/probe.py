import math

import Adafruit_BBIO.ADC as ADC
import tornado.ioloop

SAMPLE_PERIOD = 3

HIGH_RESIST = 10000
EMA_MULT = (2.0 / ((60.0 / SAMPLE_PERIOD) + 1.0))

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

        self._probe_pin = probe_pin
        self._ema_temp = None

        ADC.setup()

        # Take a temperature immediately
        self._take_temperature()

        # Setup a periodic call every 1 second to take the temperature
        self._periodic_temp = tornado.ioloop.PeriodicCallback(
            self._take_temperature,
            SAMPLE_PERIOD * 1000)
        self._periodic_temp.start()
        
    def get_temp(self):
        """
        Returns the exponential moving average temperature from the last minute

        :returns: The EMA temperature
        :rtype: float
        """
        return self._ema_temp

    def _take_temperature(self):
        """
        Takes a temperature reading from the probe

        Reads the ADC and uses the Steinhart-Hart equation to convert the read
        voltage to degrees fahrenheit.
        """
        value = ADC.read(self._probe_pin)
        resistance = (HIGH_RESIST * value) / (1 - value)
        log_resistance = math.log(resistance)
        invert_temp_k = self._sh_a + self._sh_b * log_resistance + self._sh_c * math.pow(log_resistance, 3)
        temp_k = 1 / invert_temp_k
        temp_f = (9.0 / 5.0) * (temp_k - 273.15) + 32
       
        self._last_temp = temp_f

        if not self._ema_temp:
            self._ema_temp = temp_f

        self._ema_temp = (self._last_temp - self._ema_temp) * EMA_MULT + self._ema_temp