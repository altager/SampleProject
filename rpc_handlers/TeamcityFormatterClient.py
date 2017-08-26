from rpc_handlers import TestAgentClient
import logging
import socket
import xmlrpc.client

module_logger = logging.getLogger(__name__)


class TeamcityFormatterClient(TestAgentClient):
    def iterate_test_run(self, test_suite, res_timeout=1000, nonstop_mode=False, test_method_prefix='test'):
        socket.setdefaulttimeout(res_timeout)
        module_logger.log(logging.INFO, self.extract_test_methods(test_method_prefix))
        suite_result = True
        print("##teamcity[testSuiteStarted name='%s']" % test_suite)
        for test_method in self.test_methods_list:
            print("##teamcity[testStarted name='%s']" % test_method)
            try:
                getattr(self.connection, test_method)()
            except xmlrpc.client.ProtocolError as err:
                print("[ERROR][CODE={0}] {1}".format(err.errcode, err.errmsg))
                print("[Failed] Test %s is Failed" % test_method)
                print("##teamcity[testFailed name='%s']" % test_method)
                if not nonstop_mode:
                    suite_result = False
                    break
            except IOError as err:
                print("[ERROR][CODE={0}] {1}".format(err.errno, err.strerror))
                print("[Failed] Test %s is Failed" % test_method)
                print("##teamcity[testFailed name='%s']" % test_method)
                if not nonstop_mode:
                    suite_result = False
                    break
            except xmlrpc.client.Fault as err:
                ex, message = err.faultString.replace("|", "||").replace("'", "|'").replace("\n", "|n").replace("[", "|[").replace("]", "|]").replace("\r", "|r").split(":", 1)
                print("""[ERROR]{0}""".format(ex + ':' + message))
                print("""[Failed] Test %s is Failed""" % test_method)
                print("""##teamcity[testFailed name='{0}' message='{1}' details='{2}']""".format(test_method, ex, message))
                if not nonstop_mode:
                    suite_result = False
                    break
            else:
                print("[PASSED] Test %s is Passed" % test_method)
            print("##teamcity[testFinished name='%s']" % test_method)
        print("##teamcity[testSuiteFinished name='%s']" % test_suite)
        return suite_result
