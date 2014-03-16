import datetime

import Adafruit_BBIO.GPIO as GPIO
import tornado.gen

class Baster(object):
    """
    Controller for the baster
    """
    def __init__(self, baster_pin):
        """
        Initializes the controller for a baster and sets it closed

        :param baster_pin: The BBB GPIO to use, e.g. P8_14
        :type baster_pin: str
        """
        self._baster_pin = baster_pin
        self._baste_off_handle = None

        GPIO.setup(self._baster_pin, GPIO.OUT)
        GPIO.output(self._baster_pin, GPIO.LOW)

        
    def baste(self, duration):
        """
        Bastes for the defined ``duration`` seconds

        :param duration: The desired baste duration in seconds
        :type duration: float
        :raises: ValueError
        """
        ioloop = tornado.ioloop.IOLoop.instance()

        if 0 >= duration:
            raise ValueError('Baste duration must be >= 0')

        if self._baste_off_handle:
            ioloop.remove_timeout(self._baste_off_handle)
            self._baste_off_handle = None

        GPIO.output(self._baster_pin, GPIO.HIGH)
        self._baste_off_handle = ioloop.add_timeout(datetime.timedelta(seconds=duration), self._baste_off)

    def _baste_off(self):
        """
        Turns off the basting
        """
        GPIO.output(self._baster_pin, GPIO.LOW)

