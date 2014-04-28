import json
import pkg_resources
import sys

from smokematic.web import main

def entry():
    """
    Main entry point into smokematic, checks to see if a positional argument
    was passed and, if it there was, uses that as the config file
    """
    if 2 == len(sys.argv):
        f = open(sys.argv[1])
        config = json.load(f)
        f.close()
        main(config)
    else:
        config_filename = pkg_resources.resource_filename(
            __name__,
            '/skel/config.json'
        )
        f = open(config_filename)
        config = json.load(f)
        f.close()
        main(config)

if '__main__' == __name__:
    entry()
