"""
//  -------------------------------------------------------------
//  author        Giga
//  project       qeeqbox/honeypots
//  email         gigaqeeq@gmail.com
//  description   app.py (CLI)
//  licensee      AGPL-3.0
//  -------------------------------------------------------------
//  contributors list qeeqbox/social-analyzer/graphs/contributors
//  -------------------------------------------------------------
"""

from warnings import filterwarnings
filterwarnings(action='ignore', module='.*OpenSSL.*')

from dns.resolver import query as dsnquery
from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ClientFactory, Factory
from twisted.python import log as tlog
from requests import get
from subprocess import Popen
from email.parser import BytesParser
from os import path
from honeypots.helper import close_port_wrapper, get_free_port, kill_server_wrapper, server_arguments, setup_logger, disable_logger
from uuid import uuid4


class QHTTPProxyServer():
    def __init__(self, ip=None, port=None, mocking=None, logs=None, logs_location=None):
        self.ip = ip or '0.0.0.0'
        self.port = port or 8080
        self.mocking = mocking or ''
        self.process = None
        self._logs = logs or ''
        self.logs_location = logs_location or ''
        self.uuid = 'honeypotslogger' + '_' + __class__.__name__ + '_' + str(uuid4())[:8]
        self.logs = setup_logger(self.uuid, self.logs_location, self._logs)
        disable_logger(1, tlog)

    def http_proxy_server_main(self):
        _q_s = self

        class CustomProtocolParent(Protocol):

            def __init__(self):
                self.buffer = None
                self.client = None

            def resolve_domain(self, request_string):
                try:
                    _, parsed_request = request_string.split(b'\r\n', 1)
                    headers = BytesParser().parsebytes(parsed_request)
                    host = headers["host"].split(":")
                    _q_s.logs.info(["servers", {'server': 'http_proxy_server', 'action': 'query', 'ip': self.transport.getPeer().host, 'port': self.transport.getPeer().port, 'payload': host[0]}])
                    # return "127.0.0.1"
                    return dsnquery(host[0], 'A')[0].address
                except Exception as e:
                    _q_s.logs.error(["errors", {'server': 'http_proxy_server', 'error': 'resolve_domain', "type": "error -> " + repr(e)}])
                return None

            def dataReceived(self, data):
                _q_s.logs.info(["servers", {'server': 'http_proxy_server', 'action': 'connection', 'ip': self.transport.getPeer().host, 'port': self.transport.getPeer().port}])
                try:
                    ip = self.resolve_domain(data)
                    if ip:
                        factory = ClientFactory()
                        factory.CustomProtocolParent_ = self
                        factory.protocol = CustomProtocolChild
                        reactor.connectTCP(ip, 80, factory)
                    else:
                        self.transport.loseConnection()

                    if self.client:
                        self.client.write(data)
                    else:
                        self.buffer = data
                except BaseException:
                    pass

            def write(self, data):
                self.transport.write(data)

        class CustomProtocolChild(Protocol):
            def connectionMade(self):
                self.write(self.factory.CustomProtocolParent_.buffer)

            def dataReceived(self, data):
                self.factory.CustomProtocolParent_.write(data)

            def write(self, data):
                self.transport.write(data)

        factory = Factory()
        factory.protocol = CustomProtocolParent
        reactor.listenTCP(port=self.port, factory=factory, interface=self.ip)
        reactor.run()

    def run_server(self, process=False, auto=False):
        if process:
            if auto:
                port = get_free_port()
                if port > 0:
                    self.port = port
                    self.process = Popen(['python3', path.realpath(__file__), '--custom', '--ip', str(self.ip), '--port', str(self.port), '--mocking', str(self.mocking), '--logs', str(self._logs), '--logs_location', str(self.logs_location), '--uuid', str(self.uuid)])
                    if self.process.poll() is None:
                        self.logs.info(["servers", {'server': 'http_proxy_server', 'action': 'process', 'status': 'success', 'ip': self.ip, 'port': self.port}])
                    else:
                        self.logs.info(["servers", {'server': 'http_proxy_server', 'action': 'process', 'status': 'error', 'ip': self.ip, 'port': self.port}])
                else:
                    self.logs.info(["servers", {'server': 'http_proxy_server', 'action': 'setup', 'status': 'error', 'ip': self.ip, 'port': self.port}])
            elif self.close_port() and self.kill_server():
                self.process = Popen(['python3', path.realpath(__file__), '--custom', '--ip', str(self.ip), '--port', str(self.port), '--mocking', str(self.mocking), '--logs', str(self._logs), '--logs_location', str(self.logs_location), '--uuid', str(self.uuid)])
                if self.process.poll() is None:
                    self.logs.info(["servers", {'server': 'http_proxy_server', 'action': 'process', 'status': 'success', 'ip': self.ip, 'port': self.port}])
                else:
                    self.logs.info(["servers", {'server': 'http_proxy_server', 'action': 'process', 'status': 'error', 'ip': self.ip, 'port': self.port}])
        else:
            self.http_proxy_server_main()

    def test_server(self, ip=None, port=None, domain=None):
        try:
            _ip = ip or self.ip
            _port = port or self.port
            _domain = domain or "http://yahoo.com"
            get(_domain, proxies={"http": 'http://{}:{}'.format(_ip, _port)}).text.encode('ascii', 'ignore')
        except BaseException:
            pass

    def close_port(self):
        ret = close_port_wrapper('http_proxy_server', self.ip, self.port, self.logs)
        return ret

    def kill_server(self):
        ret = kill_server_wrapper('http_proxy_server', self.uuid, self.process)
        return ret


if __name__ == '__main__':
    parsed = server_arguments()
    if parsed.docker or parsed.aws or parsed.custom:
        qhttpproxyserver = QHTTPProxyServer(ip=parsed.ip, port=parsed.port, mocking=parsed.mocking, logs=parsed.logs, logs_location=parsed.logs_location)
        qhttpproxyserver.run_server()
