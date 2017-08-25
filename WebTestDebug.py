from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application
from tornado.websocket import WebSocketHandler
from tornado.escape import json_decode
from tornado.httpserver import HTTPServer
from multiprocessing.pool import ThreadPool
from TestAgentClient import TestAgentClient
from datetime import datetime
import socket
import xmlrpc.client
import os


ws_listeners = []
_workers = ThreadPool(15)


def run_background(func, args=()):
    _workers.apply_async(func, args)


class MainHandler(RequestHandler):
    def get(self):
        self.render("index.html")


class CliHandler(WebSocketHandler):
    def open(self):
        print("WebSocket connection opened")

    def on_message(self, data):
        print(data)
        received_data = None
        try:
            received_data = json_decode(data)
        except TypeError as e:
            print("Bad JSON data. Msg:{0}".format(e.message))
        for key in received_data:
            if key == "ts_address":
                #if not received_data[key] == '':
                self.test_server_connect(received_data[key])
            elif key == "tests":
                print(received_data[key])
                self.test_methods_run(received_data[key])
            else:
                print("Invalid key {0}".format(received_data))

    def on_close(self):
        print("WebSocket connection closed.")

    def test_server_connect(self, data):
        self.tc = TestAgentClient(data)
        self.write_message(str(self.tc))
        result = {}
        try:
            for i in self.tc.extract_test_methods('test'):
                result[i] = i
        except IOError as e:
            result["Error"] = e.strerror
        self.write_message(result)

    def test_methods_run(self, data):
        run_background(self.run_tests, (data,))

    def run_tests(self, data):
        test_methods = data.split(' ')
        del(test_methods[0])
        socket.setdefaulttimeout(3000)
        for i in test_methods:
            try:
                self.write_message("[{0}][RUNNING] {1}".format(str(datetime.now()), i))
                received_data = (getattr(self.tc.connection, i)())
                print("[{0}][PASSED] {1} {2} Received data: {3}".format(str(datetime.now()), i, self, received_data))
                self.write_message("[{0}][PASSED] {1} Received data: {2}".format(str(datetime.now()), i, received_data))
            except xmlrpc.client.Fault as err:
                self.write_message("[{0}][FAILED] {1} {2}".format(str(datetime.now()), i, err.faultString))
            except xmlrpc.client.ProtocolError as err:
                self.write_message("[{0}][ERROR][CODE={1}] {2}".format(str(datetime.now()), err.errcode, err.errmsg))
            except IOError as err:
                self.write_message("[{0}][ERROR][CODE={1}] {2}".format(str(datetime.now()), err.errno, err.strerror))


class MyApplication(Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/cli", CliHandler),
        ]
        settings = dict(template_path=os.path.join(os.path.dirname(__file__), "templates"), static_path=os.path.join(os.path.dirname(__file__), "static"), )
        Application.__init__(self, handlers, **settings)


if __name__ == "__main__":
    application = MyApplication()
    http_server = HTTPServer(application)
    application.listen(8000)
    try:
        IOLoop.instance().start()
    except Exception as exc:
        print ("Error: {0}".format(str(exc)))