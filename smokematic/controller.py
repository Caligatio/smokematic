from collections import namedtuple
import logging
import time

import tornado.gen

PID_INTERVAL = 60

StatPoint = namedtuple(
    'StatPoint',
    ['pit_temp', 'setpoint', 'blower_speed', 'food_temps']
)

class Controller(object):
    """
    Controller class used to centralize all temperature related operations
    """
    UNINITIALIZED = 0
    PROFILE_RUNNING = 1
    OVERRIDE = 2

    def __init__(self, blower, pit_probe, *food_probes):
        """
        Initializes the Controller

        :param blower: The blower object
        :type blower: Blower
        :param pit_probe: The pit Probe object
        :type pit_probe: Probe
        :param food_probes: List of at least one food probe
        :type food_probes: List of Probes
        """
        self._pit_probe = pit_probe
        self._blower = blower
        self._food_probes = food_probes

        self._pid = Pid(blower, pit_probe)

        self._profile_periodic_handle = None
        self._stats_periodic_handle = None
        self._cook_profile = None
        self._profile_time_start = None
        self._state = Controller.UNINITIALIZED
        self._stats_history = {}

    def set_pid_coefficients(self, p, i, d):
        """
        Sets new PID coefficients

        :param p: The P coefficient
        :type p: float
        :param i: The I coefficient
        :type i: float
        :param d: The D coefficient
        :type d: float
        """
        self._pid.set_coefficients(p, i, d)

    def get_pid_coefficients(self):
        """
        Returns the current PID coefficients

        :returns: Tuple containing the P, I, D coefficients
        :rtype: Tuple
        """
        return self._pid.get_coefficients()

    def set_profile(self, profile):
        """
        Sets a new cooking profile

        :param profile: A dictionary with numeric minute keys and temperature
            values
        :type prfile: dict
        """
        if 0 not in profile:
            raise ValueError('Profile must have a temperature for time 0')

        self._cook_profile = profile
        self._profile_time_start = time.time()

        self._set_temperature_from_profile()

        if self._profile_periodic_handle:
            self._profile_periodic_handle.stop()

        self._profile_periodic_handle = tornado.ioloop.PeriodicCallback(
            self._set_temperature_from_profile,
            60000)

        self._stats_history = {}
        self._record_stats()
        self._stats_periodic_handle = tornado.ioloop.PeriodicCallback(
            self._record_stats,
            60000)

        self._profile_periodic_handle.start()
        self._stats_periodic_handle.start()

        self._state = Controller.PROFILE_RUNNING

    def _record_stats(self):
        """
        Records the current smoker stats
        """
        if self._stats_history:
            new_time = max(self._stats_history.keys()) + 1
        else:
            new_time = 0

        self._stats_history[new_time] = StatPoint(
            self._pit_probe.get_temp(),
            self.get_setpoint(),
            self._blower.get_speed(),
            [probe.get_temp() for probe in self._food_probes])

    def get_stat_history(self, sample_rate=1):
        """
        Returns the temperature history sampled every ```sample_rate``` minutes

        :param sample_rate: The desired sample rate in minutes
        :type sample_rate: int
        :returns: Dictionary of minute:temperature pairs
        :rtype: Dict
        """
        return {str(k):v for k, v in self._stats_history.items() if k % sample_rate == 0}

    def _set_temperature_from_profile(self):
        """
        Sets the temperature based upon the cooking profile
        """
        now = time.time()
        time_offset = (now - self._profile_time_start) / 60

        sorted_times = sorted(self._cook_profile.keys())

        for profile_time in sorted_times:
            if time_offset >= profile_time:
                if self.get_setpoint() != self._cook_profile[profile_time]:
                    self._pid.set_setpoint(self._cook_profile[profile_time])

    def get_state(self):
        """
        Returns the state of the controller

        :returns: Controller state
        :rtype: int
        """
        return self._state

    def override_temp(self, temp):
        """
        Overrides the cooking profile with a single temperature

        :param temp: The manual temperature
        :type temp: float
        """
        if self._profile_periodic_handle:
            self._profile_periodic_handle.stop()
            self._profile_periodic_handle = None

        self._pid.set_setpoint(temp)
        self._state = Controller.OVERRIDE

    def get_setpoint(self):
        """
        Gets the current setpoint temperature

        :returns: Current setpoint temperature
        :rtype: float
        """
        return self._pid.get_setpoint()

    def resume_profile(self):
        """
        Resumes the cooking profile after a manual override
        """
        if self._profile_periodic_handle:
            self._profile_periodic_handle.stop()

        self._set_temperature_from_profile()
        self._profile_periodic_handle = tornado.ioloop.PeriodicCallback(
            self._set_temperature_from_profile,
            1000)

        self._profile_periodic_handle.start()
        self._state = Controller.PROFILE_RUNNING

class Pid(object):
    """
    PID controller
    """
    def __init__(self, blower, pit_probe):
        """
        Initializes the PID controller

        :param blower: Blower object
        :type blower: Blower
        :param pit_probe: Pit probe object
        :type pit_probe: Probe
        """
        self._blower = blower
        self._pit_probe = pit_probe

        self._setpoint = None
        self._enabled = False

        self._k_p = None
        self._k_i = None
        self._k_d = None
        self._ci = 0

        self._pid_periodic_handle = None

        self._last_error = None

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
        self._last_error = None
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

    def get_coefficients(self):
        """
        Returns the current PID coefficients

        :returns: Tuple containing the P, I, D coefficients
        :rtype: Tuple
        """
        return (self._k_p, self._k_i, self._k_d)

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

        self._pid_periodic_handle = tornado.ioloop.PeriodicCallback(
            self._pid_calc,
            PID_INTERVAL * 1000)

        self._ci = 0
        self._last_error = None
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

    def set_manual_speed(self, fan_speed):
        """
        Overrides the PID controller with a manual blower speed
        """
        self.disable()

        self._blower.set_speed(fan_speed)

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
        curr_temp = self._pit_probe.get_temp()
        curr_blower = self._blower.get_speed()

        error = self._setpoint - curr_temp

        if curr_temp >= self._setpoint:
            self._ci *= 0.10

        p_part = self._k_p * error

        # Anti-windup check
        if (error > 0 and curr_blower < 100) or (error < 0 and curr_blower > 0):
            self._ci += error * PID_INTERVAL
        i_part = self._k_i * self._ci

        if self._last_error is not None:
            d_part = self._k_d * ((error - self._last_error) / PID_INTERVAL)
        else:
            d_part = 0

        new_speed = int(min(100, max(0, p_part + i_part + d_part)))
        self._blower.set_speed(new_speed)

        logging.debug('PID results: Read {}, Wanted {}, P={} I={} D={}, Set fan to {}'.format(
            curr_temp,
            self._setpoint,
            p_part,
            i_part,
            d_part,
            new_speed))

        self._last_error = error
