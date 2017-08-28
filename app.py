import logging
import os
import socket
import xmlrpc.client
from datetime import datetime
from multiprocessing.pool import ThreadPool

import tornado.options
from tornado.escape import json_decode
from tornado.ioloop import IOLoop
from tornado.options import define, options
from tornado.web import RequestHandler, Application
from tornado.websocket import WebSocketHandler

define("port", default=8000, help="run on the given port", type=int)

from rpc_handlers.TestAgentClient import TestAgentClient

ws_listeners = []
_workers = ThreadPool(4)

module_logger = logging.getLogger(__name__)


def run_background(func, args=()):
    _workers.apply_async(func, args)


class MainHandler(RequestHandler):
    def get(self):
        self.render("index.html")


class CliHandler(WebSocketHandler):
    def open(self):
        module_logger.log(logging.INFO, "WebSocket connection opened")

    def on_message(self, data):
        module_logger.log(logging.INFO, data)
        received_data = None
        try:
            received_data = json_decode(data)
        except TypeError as e:
            module_logger.log(logging.ERROR, "Bad JSON data")
        for key in received_data:
            if key == "ts_address":
                self.test_server_connect(received_data[key])
            elif key == "tests":
                module_logger.log(logging.INFO, received_data[key])
                run_background(self.run_tests, (received_data[key],))
            else:
                module_logger.log(logging.ERROR, "Invalid key {0}".format(received_data))

    def on_close(self):
        module_logger.log(logging.INFO, "WebSocket connection closed.")

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

    def run_tests(self, data):
        test_methods = data.split(' ')
        del (test_methods[0])
        socket.setdefaulttimeout(3000)
        for i in test_methods:
            try:
                self.write_message("[{0}][RUNNING] {1}".format(str(datetime.now()), i))
                received_data = (getattr(self.tc.connection, i)())
                module_logger.log(logging.INFO,
                                  "[{0}][PASSED] {1} {2} Received data: {3}".format(str(datetime.now()), i, self,
                                                                                    received_data))
                self.write_message("[{0}][PASSED] {1} Received data: {2}".format(str(datetime.now()), i, received_data))
            except xmlrpc.client.Fault as err:
                module_logger.log(logging.INFO, "[{0}][FAILED] {1} {2}".format(str(datetime.now()), i, err.faultString))
                self.write_message("[{0}][FAILED] {1} {2}".format(str(datetime.now()), i, err.faultString))
            except xmlrpc.client.ProtocolError as err:
                module_logger.log(logging.ERROR,
                                  "[{0}][ERROR][CODE={1}] {2}".format(str(datetime.now()), err.errcode, err.errmsg))
                self.write_message("[{0}][ERROR][CODE={1}] {2}".format(str(datetime.now()), err.errcode, err.errmsg))
            except IOError as err:
                module_logger.log(logging.ERROR,
                                  "[{0}][ERROR][CODE={1}] {2}".format(str(datetime.now()), err.errno, err.strerror))
                self.write_message("[{0}][ERROR][CODE={1}] {2}".format(str(datetime.now()), err.errno, err.strerror))


class App(Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/cli", CliHandler),
        ]
        settings = dict(template_path=os.path.join(os.path.dirname(__file__), "templates"),
                        static_path=os.path.join(os.path.dirname(__file__), "static"), )
        Application.__init__(self, handlers, **settings)


def main():
    tornado.options.parse_command_line()
    app = App()
    app.listen(options.port)
    module_logger.log(logging.INFO, "Server started listening on port {0}".format(options.port))
    IOLoop.current().start()


if __name__ == "__main__":
    main()
