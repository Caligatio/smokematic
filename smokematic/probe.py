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
    def __init__(self, probe_pin, sh_a, sh_b, sh_c):
        """
        Initializes the controller for a temperature probe

        :param probe_pin: The BBB ADC pin to use, e.g. P9_39
        :type probe_pin: str
        :param sh_a: The Steinhart-Hart A coefficient
        :type sh_a: float
        :param sh_b: The Steinhart-Hart B coefficient
        :type sh_b: float
        :param sh_c: The Steinhart-Hart C coefficient
        :type sh_c: float
        """
        self._sh_a = sh_a
        self._sh_b = sh_b
        self._sh_c = sh_c

        self._probe_pin = probe_pin
        self._ema_temp = None
        self._last_temp = None

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
