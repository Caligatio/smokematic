from setuptools import setup

long_description = open("README.rst").read()

setup(
    name='smokematic',
    version='0.1.0',
    author='Brian Turek',
    author_email='brian.turek@gmail.com',
    description='A smoking (cooking) automation system built on the Beaglebone Black',
    long_description=long_description,
    license='BSD',
    url='https://github.com/Caligatio/smokematic',
    packages=['smokematic'],
    entry_points={
        'console_scripts': [
            'smokematic=smokematic:entry'
        ]
    },
    install_requires=[
        'tornado',
        'Adafruit_BBIO'
    ],
    include_package_data=True,
    classifiers= [
        'License :: OSI Approved :: BSD License',
        'Development Status :: 4 - Beta',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Programming Language :: JavaScript',
        'Topic :: Home Automation',
        'Topic :: Software Development :: Embedded Systems'
    ],
    zip_safe=False
)
