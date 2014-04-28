==========
Smokematic
==========

:Info: Smokematic is a complete meat smoking automation system built on the
    `BeagleBone Black`_ (BBB) hardware platform
:Author: Brian Turek

About
=====

Smokematic was inspired by the HeaterMeter_ and a desire to drive down the
complexity of building your own control board from scratch.  The Smokematic
will control your pit temperature by tweaking air blower speed, alarm when your
food reaches a desired temperature, and even control mopping/basting an item.
It even works from phones and tablets to avoiding making you get up and getting
to a computer to check your smoker status.

Issues / Questions / Feedback
=============================

Please submit any bugs, issues, comments, or questions to the project's
`issue <https://github.com/Caligatio/smokematic/issues>`_ page.

Installation
============
  
A working Debian_ or Ubuntu_ Linux installation, then

  $ pip install smokematic
  
Usage
=====

Build a Smokematic cape according to the schematic provided in the git
repository.  Once complete, follow the installation instructions and then
simply run the *smokmatic* executable as root.  A default configuration file
is contained the *skel* directory but the program takes an optional command-line
argument that is the path to customized configuration file.  The interface is
accessible, by default, at port 8080 with a path of /static/index.html

It is recommended to use a program like supervisor_ to daemonize Smokematic.

Dependencies
============

Smokematic requires a compatible Linux installation running on the BBB.

* Debian_ or Ubuntu_ Linux (customized to the BBB)
* Tornado_
* Adafruit_BBIO_

.. _`BeagleBone Black`: http://beagleboard.org/Products/BeagleBone+Black

.. _Debian: http://elinux.org/BeagleBoardDebian

.. _Ubuntu: http://elinux.org/Beagleboard:Ubuntu_On_BeagleBone_Black

.. _Tornado: http://tornadoweb.org/

.. _Adafruit_BBIO: https://pypi.python.org/pypi/Adafruit_BBIO

.. _HeaterMeter: https://github.com/CapnBry/HeaterMeter

.. _supervisor: http://supervisord.org/

