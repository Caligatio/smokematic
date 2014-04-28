import datetime
import functools

import Adafruit_BBIO.PWM as PWM
import tornado.gen

PWM_FREQUENCY = 18000
LOW_SPEED = 15

class Blower(object):
    """
    Controller for a blower
    """
    def __init__(self, blower_pin):
        """
        Initializes the controller for a blower and sets the blower speed to 0

        :param blower_pin: The BBB PWM to use, e.g. P9_14
        :type blower_pin: str
        """
        self._blower_pin = blower_pin
        self._speed = 0
        self._low_speed_handle = None

        PWM.start(blower_pin, 0)
        PWM.stop(blower_pin)
        PWM.cleanup()

    def get_speed(self):
        """
        The speed of the blower, from 0-100

        :returns: Returns the current speed
        :rtype: int
        """
        return self._speed

    def set_speed(self, speed):
        """
        Sets the speed of the blower

        Setting the speed to <15 will engage the "low speed" mode which
        toggles the motor full power for ``speed`` percent of the time

        :param speed: The desired speed
        :type speed: int
        :raises: ValueError
        """
        ioloop = tornado.ioloop.IOLoop.instance()

        if speed < 0 or speed > 100:
            raise ValueError('Fan speed must be between 0-100')

        if self._low_speed_handle:
            ioloop.remove_timeout(self._low_speed_handle)
            self._low_speed_handle = None

        if self._speed < LOW_SPEED and speed > 0:
            # Want to give the fan a full kick to start spinning
            PWM.start(self._blower_pin, 100, PWM_FREQUENCY, 0)

            # Only want full speed for 1 second so add a timeout to then set
            # the real speed
            partial_real_speed = functools.partial(
                self._set_speed,
                speed)
            ioloop.add_timeout(
                datetime.timedelta(seconds=1),
                partial_real_speed)
        else:
            self._set_speed(speed)

        self._speed = speed
        return self._speed

    def _set_speed(self, speed):
        """
        Sets the speed of the fan without the high-powered spin up

        :param speed: The new desired speed from 0-100
        :type speed: int
        """
        if speed > LOW_SPEED:
            PWM.start(self._blower_pin, speed, PWM_FREQUENCY, 0)
        elif speed > 0:
            self._set_low_speed(speed)
        else:
            PWM.start(self._blower_pin, 0, PWM_FREQUENCY, 0)

    def _set_low_speed(self, speed, enable_fan=True):
        """
        Sets the speed of the fan in "low speed" mode

        :param speed: The new desired speed from 0-:const:`LOW_SPEED`
        :type speed: int
        :param enable_fan: Whether to enable or disable the fan
        :type enable_fan: bool
        """
        ioloop = tornado.ioloop.IOLoop.instance()
        period = float(100) / speed

        if enable_fan:
            # This should be 1 second but the spin-up takes half a second
            timeout_len = 2
        else:
            timeout_len = period-1

        PWM.start(self._blower_pin, 100 if enable_fan else 0, PWM_FREQUENCY, 0)

        toggle_partial = functools.partial(
            self._set_low_speed,
            speed,
            not enable_fan)

        self._low_speed_handle = ioloop.add_timeout(
            datetime.timedelta(seconds=timeout_len),
            toggle_partial)

