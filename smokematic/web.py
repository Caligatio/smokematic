import json
import logging

import tornado.ioloop
import tornado.web

from baster import Baster
from blower import Blower
from probe import Probe
from controller import PidController

class BlowerHandler(tornado.web.RequestHandler):
    def put(self):
        controller = self.application.settings['controller']
        try:
            data = json.loads(self.request.body)
            speed = data['speed']

            try:
                controller.set_manual_speed(speed)
                ret_dict = {
                    'status': 'success',
                    'data': {'speed': speed}}
                self.set_status(200)
            except ValueError as e:
                ret_dict = {
                    'status': 'fail',
                    'data': {'speed' : str(e)}}
                self.set_status(400)
            except Exception as e:
                ret_dict = {
                    'status': 'error',
                    'message': str(e)}
                self.set_status(500)
        except KeyError:
            ret_dict = {
                'status': 'fail',
                'data': {'speed': 'speed setting must be present'}}
            self.set_status(400)
        except ValueError:
            ret_dict = {
                'status': 'fail',
                'data': {'speed': 'speed setting must be present in JSON'}}
            self.set_status(400)
        
        self.content_type = 'application/json'
        self.finish('{}\n'.format(json.dumps(ret_dict)))

    def get(self):
        blower = self.application.settings['blower']
        ret_dict = {
            'status': 'success',
            'data': {'speed': blower.get_speed()}}

        self.finish('{}\n'.format(json.dumps(ret_dict)))

class ProbeHandler(tornado.web.RequestHandler):
    def get(self, probe_key=None):
        probes = self.application.settings['probes']
        if not probe_key:
            ret_dict = {
                'status': 'success',
                'data' : {}}
            for key in probes.keys():
                ret_dict['data'][key] = probes[key].get_temp()
            self.set_status(200)
        else:
            try:
                ret_dict = {
                    'status': 'success',
                    'data' : {
                        probe_key: probes[probe_key].get_temp()}}
            except KeyError:
                ret_dict = {
                    'status': 'fail',
                    'data' : {
                        'probe_key': '{} is not a valid probe_key'.format(
                            probe_key)}}
                self.set_status(400)
            except Exception as e:
                ret_dict = {
                    'status': 'error',
                    'message': str(e)} 
                self.set_status(500)

        self.content_type = 'application/json'
        self.finish('{}\n'.format(json.dumps(ret_dict)))


class BasterHandler(tornado.web.RequestHandler):
    def post(self):
        baster = self.application.settings['baster']
        try:
            data = json.loads(self.request.body)

            duration = float(data['duration'])
            try:
                baster.baste(duration)
                ret_dict = {
                    'status': 'success',
                    'data': {'duration': duration}}
                self.set_status(200)
            except ValueError as e:
                ret_dict = {
                    'status': 'fail',
                    'data': {'duration' : str(e)}}
                self.set_status(400)
            except Exception as e:
                ret_dict = {
                    'status': 'error',
                    'message': str(e)}
                self.set_status(500)
        except KeyError:
            ret_dict = {
                'status': 'fail',
                'data': {'duration': 'duration setting must be present'}}
            self.set_status(400)
        except ValueError:
            ret_dict = {
                'status': 'fail',
                'data': {'duration': 'duration setting must be present in JSON'}}
            self.set_status(400)
        
        self.content_type = 'application/json'
        self.finish('{}\n'.format(json.dumps(ret_dict)))

def main():
    blower = Blower("P9_14")
    baster = Baster("P8_14")

    int_probe = Probe('Thermoworks Pro-Series', 'P9_39')
    amb_probe = Probe('Maverick ET-72/73', 'P9_40')

    controller = PidController(
        blower.set_speed,
        blower.get_speed,
        amb_probe.get_temp)

    controller.set_coefficients(3, 0.005, 20)
    controller.set_setpoint(75)
    controller.enable()

    application = tornado.web.Application([
        (r'/blower', BlowerHandler),
        (r'/baster', BasterHandler),
        (r'/probes(?:/(?P<probe_key>(?:int)|(?:amb)))?', ProbeHandler)],
        blower = blower,
        baster = baster,
        controller = controller,
        probes = {'int': int_probe, 'amb': amb_probe})

    application.listen(8080)
    tornado.ioloop.IOLoop.instance().start()

if '__main__' == __name__:
    logging.basicConfig(level=logging.DEBUG)

    tornado_logger = logging.getLogger('tornado')
    tornado_logger.setLevel(logging.ERROR)
    main()
