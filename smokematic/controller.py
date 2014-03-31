import datetime
import logging

import tornado.gen

PID_INTERVAL = 60

class PidController(object):
    """
    PID controller
    """
    def __init__(self, blower_ctrl, blower_speed, curr_temp):
        """
        Initializes the PID controller

        :param blower_ctrl: Function that sets the blower speed
        :type blower_ctrl: func
        :param blower_speed: Function that gets the current blower speed
        :type blower_speed: func
        :param curr_temp: Function that gets the current temperature
        :type curr_temp: func
        """
        self._blower_ctrl = blower_ctrl
        self._blower_speed = blower_speed
        self._curr_temp = curr_temp

        self._setpoint = None
        self._enabled = False

        self._k_p = None
        self._k_i = None
        self._k_d = None
        self._ci = 0

        self._pid_periodic_handle = None

        self._last_error = 0

    def get_setpoint(self):
        """
        Returns the current temperature setpoint
        
        :returns: The current temperature setpoint
        :rtype: int
        """ 
        return self._setpoint

    def set_setpoint(self, setpoint):
        """
        Sets the new temperature setpoint

        :param setpoint: The new temperature setpoint
        :type setpoint: int
        :raises: ValueError
        """
        if setpoint < 32:
            raise ValueError('Setpoint temperature must be above freezing')

        self._setpoint = setpoint
        self._ci = 0
        self.enable()

    def set_coefficients(self, p, i, d):
        """
        Sets the PID coefficients

        :param p: The proportional coefficient (p)
        :type p: float
        :param i: The integral coefficient (i)
        :type i: float
        :param d: The derivative coefficient (d)
        :type d: float
        """
        self._k_p = p
        self._k_i = i
        self._k_d = d

    def enable(self):
        """
        Enables the PID controller

        :raises: RuntimeError
        """
        if self._enabled:
            return

        if not self._k_p or not self._k_i or not self._k_d:
            raise RuntimeError('PID coefficients must be set before enabling')

        if not self._setpoint:
            raise RuntimeError('Temperature setpoint must be set before enabling')

        ioloop = tornado.ioloop.IOLoop.instance()

        self._pid_periodic_handle = tornado.ioloop.PeriodicCallback(
            self._pid_calc,
            PID_INTERVAL * 1000)

        self._ci = 0
        self._pid_periodic_handle.start()
        self._enabled = True

    def disable(self):
        """
        Disables the PID controller
        """
        if not self._enabled:
            return

        self._pid_periodic_handle.stop()
        self._pid_periodic_handle = None

        self._enabled = False

    def set_manual_speed(fan_speed):
        """
        Overrides the PID controller with a manual blower speed
        """
        self.disable()

        self._blower_ctrl(fan_speed)

    def get_pid_status(self):
        """"
        Returns the current PID status

        :returns: Whether the PID is enabled
        :rtype: bool
        """
        return self._enabled

    def _pid_calc(self):
        """
        Main PID calculation function
        """
        curr_temp = self._curr_temp()
        curr_blower = self._blower_speed()

        error = self._setpoint - curr_temp
        
        p_part = self._k_p * error
       
        # Anti-windup check
        if (error > 0 and curr_blower < 100) or (error < 0 and curr_blower > 0):
            self._ci += error * PID_INTERVAL
        i_part = self._k_i * self._ci

        d_part = self._k_d * ((error - self._last_error) / PID_INTERVAL)

        new_speed = int(min(100, max(0, p_part + i_part + d_part)))
        self._blower_ctrl(new_speed)

        logging.debug('PID results: Read {}, Wanted {}, P={} I={} D={}, Set fan to {}'.format(
            curr_temp,
            self._setpoint,
            p_part, 
            i_part,
            d_part,
            new_speed))

        if curr_temp >= self._setpoint:
            self._ci *= 0.10

        self._last_error = error
