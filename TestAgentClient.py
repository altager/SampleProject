# -*- coding: utf-8 -*-
import xmlrpc.client
import xml.etree.ElementTree as ET
import socket


def value_from_test_config_xml(key, xml_config_path):
    try:
        value = ET.parse(xml_config_path).find(key).text
    except Exception:
        print("[ERROR] Test config doesn't exists!")
    return value


class TestAgentClient():
    def __init__(self, server_ip):
        self.test_methods_list = []
        self.connection = TestAgentClient.connector(server_ip)
        print (self.connection)
        self.address_list = []

    @staticmethod
    def connector(server_ip):
        #TODO: multiple connector to TestServers from conn_list
        conn_str = "http://%s" % server_ip
        client_conn_build = xmlrpc.client.ServerProxy(conn_str, allow_none=True)
        return client_conn_build

    def extract_test_methods(self, test_method_prefix):
        try:
            for test_method in self.connection.system.listMethods():
                if test_method[:len(test_method_prefix)] == test_method_prefix:
                    self.test_methods_list.append(test_method)
        except IOError as err:
            print("[ERROR][CODE={0}] {1}".format(err.errno, err.strerror))
        return self.test_methods_list

    def iterate_test_run(self, test_suite, res_timeout = 1000, nonstop_mode = False, test_method_prefix = 'test'):
        socket.setdefaulttimeout(res_timeout)
        print(self.extract_test_methods(test_method_prefix))
        suite_result = True
        print("##teamcity[testSuiteStarted name='%s']" % test_suite)
        for test_method in self.test_methods_list:
            print("##teamcity[testStarted name='%s']" % test_method)
            try:
                getattr(self.connection, test_method)()
            except xmlrpc.ProtocolError as err:
                print("[ERROR][CODE={0}] {1}".format(err.errcode, err.message))
                print("[Failed] Test %s is Failed" % test_method)
                print("##teamcity[testFailed name='%s']" % test_method)
                if (nonstop_mode == False):
                    suite_result = False
                    break
            except IOError as err:
                print("[ERROR][CODE={0}] {1}".format(err.errno, err.strerror))
                print("[Failed] Test %s is Failed" % test_method)
                print("##teamcity[testFailed name='%s']" % test_method)
                if (nonstop_mode == False):
                    suite_result = False
                    break
            except xmlrpc.Fault as err:
                ex, message = err.faultString.replace("|", "||").replace("'", "|'").replace("\n", "|n").replace("[", "|[").replace("]", "|]").replace("\r", "|r").split(":", 1)
                print("""[ERROR]{0}""".format(ex + ':' + message))
                print("""[Failed] Test %s is Failed""" % test_method)
                print("""##teamcity[testFailed name='{0}' message='{1}' details='{2}']""".format(test_method, ex, message))
                if (nonstop_mode == False):
                    suite_result = False
                    break
            else:
                print("[PASSED] Test %s is Passed" % test_method)
            print("##teamcity[testFinished name='%s']" % test_method)
        print("##teamcity[testSuiteFinished name='%s']" % test_suite)
        return suite_result

