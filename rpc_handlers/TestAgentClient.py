import xmlrpc.client
import xml.etree.ElementTree as ET
import logging

from . import module_logger


def value_from_test_config_xml(key, xml_config_path):
    try:
        return ET.parse(xml_config_path).find(key).text
    except Exception:
        module_logger.log(logging.ERROR, "[ERROR] Test config doesn't exists!")
    return None


class TestAgentClient:
    def __init__(self, server_ip):
        self.test_methods_list = []
        self.connection = TestAgentClient.connector(server_ip)
        module_logger.log(logging.INFO, self.connection)
        self.address_list = []

    @staticmethod
    def connector(server_ip):
        conn_str = "http://%s" % server_ip
        client_conn_build = xmlrpc.client.ServerProxy(conn_str, allow_none=True)
        return client_conn_build

    def extract_test_methods(self, test_method_prefix):
        try:
            for test_method in self.connection.system.listMethods():
                if test_method[:len(test_method_prefix)] == test_method_prefix:
                    self.test_methods_list.append(test_method)
        except IOError as err:
            module_logger.log(logging.ERROR, "[ERROR][CODE={0}] {1}".format(err.errno, err.strerror))
            raise
        return self.test_methods_list