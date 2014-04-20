from setuptools import setup

setup(
    name = "smokematic",
    version = "0.1.0",
    author = "Brian Turek",
    author_email = "brian.turek@gmail.com",
    description = "A smoking automation system using the Beaglebon Black",
    license = "BSD",
    url = "https://github.com/Caligatio/smokematic",
    packages=['smokematic'],
    entry_points = {
        "console_scripts": [
            "smokematic = smokematic:entry"
        ]
    },

    install_requires = [
        "tornado",
        "Adafruit_BBIO",
        "jsonschema"
    ],
    include_package_data=True
)
