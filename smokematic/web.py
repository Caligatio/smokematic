import json
import logging

import tornado.ioloop
import tornado.web
import tornado.websocket

from baster import Baster
from blower import Blower
from probe import Probe
from controller import Controller

class StatusWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        self._update_handle = tornado.ioloop.PeriodicCallback(self.send_update_info, 1000)
        self._update_handle.start()

    def send_full_info(self):
        pass

    def send_update_info(self):
        self.write_message({
            'pit_temp': self.application.settings['probes']['pit'].get_temp(),
            'food1_temp': self.application.settings['probes']['food1'].get_temp(),
            'setpoint': self.application.settings['controller'].get_setpoint(),
            'blower_speed': self.application.settings['blower'].get_speed()})

    def on_close(self):
        self._update_handle.stop()

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

class ProfileHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            data = json.loads(self.request.body)
            controller = self.application.settings['controller']

            temperature = data['temperature']

            try:
                controller.override_temp(temperature)
                ret_dict = {
                    'status': 'success',
                    'data': {'temperature': temperature}}
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
                'data': {'duration': 'temperature setting must be present'}}
            self.set_status(400)
        except ValueError:
            ret_dict = {
                'status': 'fail',
                'data': {'duration': 'temperature setting must be present in JSON'}}
            self.set_status(400)
        
        self.content_type = 'application/json'
        self.finish('{}\n'.format(json.dumps(ret_dict)))
 
    def put(self):
        try:
            data = json.loads(self.request.body)
            controller = self.application.settings['controller']

            input_profile = data['profile']
            profile = {}
            for k,v in input_profile.items():
                profile[int(k)] = float(v)
                
            try:
                controller.set_profile(profile)
                ret_dict = {
                    'status': 'success',
                    'data': {'profile': profile}}
                self.set_status(200)
            except ValueError as e:
                ret_dict = {
                    'status': 'fail',
                    'data': {'profile' : str(e)}}
                self.set_status(400)
            except Exception as e:
                ret_dict = {
                    'status': 'error',
                    'message': str(e)}
                self.set_status(500)
        except KeyError:
            ret_dict = {
                'status': 'fail',
                'data': {'profile': 'profile setting must be present'}}
            self.set_status(400)
        except ValueError:
            ret_dict = {
                'status': 'fail',
                'data': {'profile': 'profile setting must be present in JSON'}}
            self.set_status(400)
        
        self.content_type = 'application/json'
        self.finish('{}\n'.format(json.dumps(ret_dict)))

class PidHandler(tornado.web.RequestHandler):
     def put(self):
        try:
            data = json.loads(self.request.body)
            controller = self.application.settings['controller']

            input_coefficients = data['coefficients']
            coefficients = {}
            for k,v in input_coefficients.items():
                coefficients[k] = float(v)
                
            try:
                controller.set_pid_coefficients(
                    coefficients['p'],
                    coefficients['i'],
                    coefficients['d'])

                ret_dict = {
                    'status': 'success',
                    'data': {'coefficients': coefficients}}
                self.set_status(200)
            except ValueError as e:
                ret_dict = {
                    'status': 'fail',
                    'data': {'coefficients' : str(e)}}
                self.set_status(400)
            except Exception as e:
                ret_dict = {
                    'status': 'error',
                    'message': str(e)}
                self.set_status(500)
        except KeyError:
            ret_dict = {
                'status': 'fail',
                'data': {'coefficients': 'coefficients setting must be present with p, i, and d values'}}
            self.set_status(400)
        except ValueError:
            ret_dict = {
                'status': 'fail',
                'data': {'coefficients': 'coefficients setting must be present in JSON'}}
            self.set_status(400)
        
        self.content_type = 'application/json'
        self.finish('{}\n'.format(json.dumps(ret_dict)))

 
def main():
    blower = Blower("P9_14")
    baster = Baster("P8_14")

    food1_probe = Probe('Thermoworks Pro-Series', 'P9_39')
    pit_probe = Probe('Maverick ET-72/73', 'P9_40')

    controller = Controller(
        blower,
        pit_probe,
        food1_probe)

    controller.set_pid_coefficients(3, 0.005, 20)

    application = tornado.web.Application(
        [
            (r'/status', StatusWebSocket),
            (r'/profile', ProfileHandler),
            (r'/pid', PidHandler),
            (r'/baster', BasterHandler)],
        static_path = 'static',
        blower = blower,
        baster = baster,
        controller = controller,
        probes = {'food1': food1_probe, 'pit': pit_probe})

    application.listen(8080)
    tornado.ioloop.IOLoop.instance().start()

if '__main__' == __name__:
    logging.basicConfig(level=logging.DEBUG)

    tornado_logger = logging.getLogger('tornado')
    tornado_logger.setLevel(logging.INFO)
    main()
