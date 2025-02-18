"""
//  -------------------------------------------------------------
//  author        Giga
//  project       qeeqbox/honeypots
//  email         gigaqeeq@gmail.com
//  description   app.py (CLI)
//  licensee      AGPL-3.0
//  -------------------------------------------------------------
//  contributors list qeeqbox/honeypots/graphs/contributors
//  -------------------------------------------------------------
"""

from contextlib import suppress
from struct import unpack

from twisted.internet import reactor
from twisted.internet.protocol import Factory, Protocol

from honeypots.base_server import BaseServer
from honeypots.helper import (
    server_arguments,
    check_bytes,
)


class QPostgresServer(BaseServer):
    NAME = "postgres_server"
    DEFAULT_PORT = 5432

    def server_main(self):
        _q_s = self

        class CustomPostgresProtocol(Protocol):
            _state = None
            _variables = {}

            def read_data_custom(self, data):
                _data = data.decode("utf-8")
                length = unpack("!I", data[0:4])
                encoded_list = _data[8:-1].split("\x00")
                self._variables = dict(zip(*([iter(encoded_list)] * 2)))

            def read_password_custom(self, data):
                data = data.decode("utf-8")
                self._variables["password"] = data[5:].split("\x00")[0]

            def connectionMade(self):
                self._state = 1
                self._variables = {}
                _q_s.logs.info(
                    {
                        "server": _q_s.NAME,
                        "action": "connection",
                        "src_ip": self.transport.getPeer().host,
                        "src_port": self.transport.getPeer().port,
                        "dest_ip": _q_s.ip,
                        "dest_port": _q_s.port,
                    }
                )

            def dataReceived(self, data):
                if self._state == 1:
                    self._state = 2
                    self.transport.write(b"N")
                elif self._state == 2:
                    self.read_data_custom(data)
                    self._state = 3
                    self.transport.write(b"R\x00\x00\x00\x08\x00\x00\x00\x03")
                elif self._state == 3:
                    if data[0] == 112 and "user" in self._variables:
                        self.read_password_custom(data)
                        username = check_bytes(self._variables["user"])
                        password = check_bytes(self._variables["password"])
                        status = "failed"
                        if username == _q_s.username and password == _q_s.password:
                            username = _q_s.username
                            password = _q_s.password
                            status = "success"
                        _q_s.logs.info(
                            {
                                "server": _q_s.NAME,
                                "action": "login",
                                "status": status,
                                "src_ip": self.transport.getPeer().host,
                                "src_port": self.transport.getPeer().port,
                                "dest_ip": _q_s.ip,
                                "dest_port": _q_s.port,
                                "username": username,
                                "password": password,
                            }
                        )

                    self.transport.loseConnection()
                else:
                    self.transport.loseConnection()

            def connectionLost(self, reason):
                self._state = 1
                self._variables = {}

        factory = Factory()
        factory.protocol = CustomPostgresProtocol
        reactor.listenTCP(port=self.port, factory=factory, interface=self.ip)
        reactor.run()

    def test_server(self, ip=None, port=None, username=None, password=None):
        with suppress(Exception):
            from psycopg2 import connect

            _ip = ip or self.ip
            _port = port or self.port
            _username = username or self.username
            _password = password or self.password
            x = connect(host=_ip, port=_port, user=_username, password=_password)


if __name__ == "__main__":
    parsed = server_arguments()
    if parsed.docker or parsed.aws or parsed.custom:
        qpostgresserver = QPostgresServer(
            ip=parsed.ip,
            port=parsed.port,
            username=parsed.username,
            password=parsed.password,
            options=parsed.options,
            config=parsed.config,
        )
        qpostgresserver.run_server()
