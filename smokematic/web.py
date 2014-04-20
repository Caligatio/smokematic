import json
import logging
import os.path

import tornado.ioloop
import tornado.web
import tornado.websocket

from baster import Baster
from blower import Blower
from probe import Probe
from controller import Controller

class StatusWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        self._update_handle = tornado.ioloop.PeriodicCallback(self.send_update_info, 5000)
        self._update_handle.start()
        self.send_full_info()

    def send_full_info(self):
        controller = self.application.settings['controller']
        stat_points = controller.get_stat_history(1)

        initial_message_data = {}

        for time_offset, data in stat_points.items():
            initial_message_data[time_offset] = {
                'pit_temp': data.pit_temp,
                'food_temp': data.food_temps,
                'setpoint': data.setpoint,
                'blower_speed': data.blower_speed}
 
        self.write_message({
            'type': 'initial',
            'data': initial_message_data})

    def send_update_info(self):
        self.write_message({
            'type': 'update',
            'data': {
                'pit_temp': self.application.settings['probes']['pit'].get_temp(),
                'food_temp': [probe.get_temp() for probe in self.application.settings['probes']['food']],
                'setpoint': self.application.settings['controller'].get_setpoint(),
                'blower_speed': self.application.settings['blower'].get_speed()}})

    def on_close(self):
        self._update_handle.stop()

class BasteHandler(tornado.web.RequestHandler):
    def get(self):
        baster = self.application.settings['baster']
        baster_settings = baster.get_settings()

        self.content_type = 'application/json'
        self.finish('{}\n'.format(
            json.dumps(
                {
                    'status': 'success',
                    'data': {
                        'frequency': baster_settings[0],
                        'duration': baster_settings[1]}})))
                
    def put(self):
        baster = self.application.settings['baster']
        try:
            data = json.loads(self.request.body)

            duration = float(data['duration'])
            frequency = float(data['frequency'])
            try:
                baster.config(frequency, duration)
                ret_dict = {
                    'status': 'success',
                    'data': {'duration': duration, 'frequency': frequency}}
                self.set_status(200)
            except ValueError as e:
                ret_dict = {
                    'status': 'fail',
                    'data': {'message' : str(e)}}
                self.set_status(400)
            except Exception as e:
                ret_dict = {
                    'status': 'error',
                    'message': str(e)}
                self.set_status(500)
        except KeyError:
            ret_dict = {
                'status': 'fail',
                'data': {'message': 'frequency and duration setting must be present'}}
            self.set_status(400)
        except ValueError:
            ret_dict = {
                'status': 'fail',
                'data': {'message': 'frequency and duration setting must be present in JSON'}}
            self.set_status(400)
        
        self.content_type = 'application/json'
        self.finish('{}\n'.format(json.dumps(ret_dict)))

class OverrideHandler(tornado.web.RequestHandler):
    def get(self):
        controller = self.application.settings['controller']

        override_status = controller.get_state() == Controller.OVERRIDE
        self.content_type = 'application/json'
        self.finish('{}\n'.format(
            json.dumps(
                {
                    'status': 'success',
                    'data': {
                        'override': override_status,
                        'temperature': controller.get_setpoint() if override_status else None}})))
        
    def put(self):
        try:
            data = json.loads(self.request.body)
            controller = self.application.settings['controller']

            temperature = float(data['temperature'])

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
 
    def delete(self):
        controller = self.application.settings['controller']
        ret_dict = {}

        if controller.get_state() != Controller.OVERRIDE:
            ret_dict = {
                'status': 'fail',
                'data': 'Currently not in override mode'
            }
            self.set_status(400)
        else:
            controller.resume_profile()
            ret_dict = {
                'status': 'success',
                'data': 'Cooking profile resumed'
            }

        self.content_type = 'application/json'
        self.finish('{}\n'.format(json.dumps(ret_dict)))

class ProfileHandler(tornado.web.RequestHandler):
    def get(self):
        controller = self.application.settings['controller']

        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=cooking_profile.json')
        stat_points = controller.get_stat_history(5)
        self.finish('{}\n'.format(json.dumps({k:v.pit_temp for k,v in stat_points.items()})))

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
    def get(self):
        controller = self.application.settings['controller']
        coefficients = controller.get_pid_coefficients()

        self.content_type = 'application/json'
        self.finish('{}\n'.format(
            json.dumps(
                {
                'status': 'success',
                'data': {
                    'coefficients': {
                        'p': coefficients[0],
                        'i': coefficients[1],
                        'd': coefficients[2]}}})))

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

 
def main(config):
    logging_mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    logging_level = logging_mapping[config['logging']['level']]
    
    logging.basicConfig(level=logging_level)
    
    # Tornado is a bit chatty on the log so never go to DEBUG
    tornado_logger = logging.getLogger('tornado')
    tornado_logger.setLevel(max(logging_level, logging.INFO))
    
    current_path = os.path.dirname(__file__)

    blower = Blower(config['blower']['pin'])
    baster = Baster(config['baster']['pin'])

    pit_probe = Probe(
        config['pit_probe']['pin'],
        config['pit_probe']['sh_a'],
        config['pit_probe']['sh_b'],
        config['pit_probe']['sh_c']
    )
    
    food_probes = []
    
    for food_probe in config['food_probes']:
        food_probes.append(
            Probe(
                food_probe['pin'],
                food_probe['sh_a'],
                food_probe['sh_b'],
                food_probe['sh_c']
            )
        )

    controller = Controller(
        blower,
        pit_probe,
        *food_probes)

    controller.set_pid_coefficients(
        config['pid_coefficients']['k_p'],
        config['pid_coefficients']['k_i'],
        config['pid_coefficients']['k_d'],
    )

    controller.set_profile({0: config['initial_setpoint']})

    application = tornado.web.Application(
        [
            (r'/status', StatusWebSocket),
            (r'/profile', ProfileHandler),
            (r'/override', OverrideHandler),
            (r'/pid', PidHandler),
            (r'/baste', BasteHandler)],
        static_path = os.path.join(current_path, 'webgui'),
        blower = blower,
        baster = baster,
        controller = controller,
        probes = {'food': food_probes, 'pit': pit_probe})

    application.listen(config['server']['port'])
    tornado.ioloop.IOLoop.instance().start()

