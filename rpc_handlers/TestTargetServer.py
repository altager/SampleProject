from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ThreadingMixIn


class TestTargetServer(ThreadingMixIn, SimpleXMLRPCServer):
    def __init__(self, address):
        super(TestTargetServer, self).__init__(address)
        self.stop = False

    def run_server(self, test_instance=None):
        self.register_introspection_functions()
        self.register_instance(test_instance)
        self.register_function(self.run_server)
        self.register_function(self.stop_server)
        print("TestAgentServer running on %s:%s..." % (self.server_address[0], self.server_address[1]))
        self.serve_forever()

    def serve_forever(self):
        # For earlier versions of Python(Jython 2.5)
        # For Python >=2.7 self.shutdown()
        while not self.stop:
            self.handle_request()

    def stop_server(self):
        self.stop = True
