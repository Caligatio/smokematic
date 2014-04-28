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
        self._baste_periodic_handle = None
        self._duration = 0
        self._frequency = 0

        GPIO.setup(self._baster_pin, GPIO.OUT)
        GPIO.output(self._baster_pin, GPIO.LOW)

    def config(self, frequency, duration):
        """
        Configures the baster to baste for duration seconds every
        frequency minutes

        :param frequency: The frequency, in minutes, to baste
        :type freqeuncy: float
        :param duration: The duration, in seconds, to baste
        :type duration: float
        :raises: ValueError
        """
        if 0 > frequency:
            raise ValueError('Baste frequency  must be >= 0')

        if 0 >= duration:
            raise ValueError('Baste duration must be > 0')

        self._duration = duration
        self._frequency = frequency

        if self._baste_periodic_handle:
            self._baste_periodic_handle.stop()
            self._baste_periodic_handle = None

        if self._baste_off_handle:
            tornado.ioloop.IOLoop.instance().remove_timeout(
                self._baste_off_handle
            )
            self._baste_off_handle = None

        self._baste_off()

        if frequency > 0:

            self._baste_periodic_handle = tornado.ioloop.PeriodicCallback(
                self._baste,
                frequency * 60 * 1000)
            self._baste_periodic_handle.start()
            self._baste()

    def get_settings(self):
        """
        Returns the current baste frequency and duration

        :returns: Tuple containing the baste frequency and duration
        :rtype: Tuple
        """
        return (self._frequency, self._duration)

    def _baste(self):
        """
        Bastes for the defined duration set in config
        """
        ioloop = tornado.ioloop.IOLoop.instance()

        if self._baste_off_handle:
            ioloop.remove_timeout(self._baste_off_handle)
            self._baste_off_handle = None

        GPIO.output(self._baster_pin, GPIO.HIGH)
        self._baste_off_handle = ioloop.add_timeout(
            datetime.timedelta(seconds=self._duration),
            self._baste_off)

    def _baste_off(self):
        """
        Turns off the basting
        """
        GPIO.output(self._baster_pin, GPIO.LOW)

