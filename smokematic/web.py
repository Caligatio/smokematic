import json

import tornado.ioloop
import tornado.web

from blower import Blower
from probe import Probe

class BlowerHandler(tornado.web.RequestHandler):
    def put(self):
        try:
            data = json.loads(self.request.body)

            blower = self.application.settings['blower']
            speed = data['blower_speed']
            try:
                blower.speed = speed
                ret_dict = {
                    'status': 'success',
                    'data': {'blower_speed': speed}}
                self.set_status(200)
            except ValueError as e:
                ret_dict = {
                    'status': 'fail',
                    'data': {'blower_speed' : str(e)}}
                self.set_status(400)
            except Exception as e:
                ret_dict = {
                    'status': 'error',
                    'message': str(e)}
                self.set_status(500)
        except KeyError:
            ret_dict = {
                'status': 'fail',
                'data': {'blower_speed': 'blower_speed setting must be present'}}
            self.set_status(400)
        except ValueError:
            ret_dict = {
                'status': 'fail',
                'data': {'blower_speed': 'blower_speed setting must be present in JSON'}}
            self.set_status(400)
        
        self.content_type = 'application/json'
        self.finish('{}\n'.format(json.dumps(ret_dict)))

    def get(self):
        blower = self.application.settings['blower']
        ret_dict = {
            'status': 'success',
            'data': {'blower_speed': blower.speed}}

        self.finish('{}\n'.format(json.dumps(ret_dict)))

class ProbeHandler(tornado.web.RequestHandler):
    def get(self, probe_key=None):
        probes = self.application.settings['probes']
        if not probe_key:
            ret_dict = {
                'status': 'success',
                'data' : {}}
            for key in probes.keys():
                ret_dict['data'][key] = probes[key].temperature
            self.set_status(200)
        else:
            try:
                ret_dict = {
                    'status': 'success',
                    'data' : {
                        probe_key: probes[probe_key].temperature}}
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

def main():
    blower = Blower("P9_14")
    int_probe = Probe('Thermoworks Pro-Series', 'P9_39')
    amb_probe = Probe('Maverick ET-72/73', 'P9_40')
    application = tornado.web.Application([
        (r'/blower', BlowerHandler),
        (r'/probes(?:/(?P<probe_key>(?:int)|(?:amb)))?', ProbeHandler)],
        blower = blower,
        probes = {'int': int_probe, 'amb': amb_probe})

    application.listen(8080)
    tornado.ioloop.IOLoop.instance().start()

if '__main__' == __name__:
    main()
