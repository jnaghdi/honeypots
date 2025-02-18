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

from twisted.internet import reactor
from twisted.protocols.sip import Base

from honeypots.base_server import BaseServer
from honeypots.helper import (
    server_arguments,
    check_bytes,
)


class QSIPServer(BaseServer):
    NAME = "sip_server"
    DEFAULT_PORT = 5060

    def server_main(self):
        _q_s = self

        class CustomSIPServer(Base):
            def handle_request(self, message, addr):
                headers = {}

                _q_s.logs.info(
                    {
                        "server": _q_s.NAME,
                        "action": "connection",
                        "src_ip": addr[0],
                        "src_port": addr[1],
                    }
                )

                for item, value in message.headers.items():
                    headers.update({check_bytes(item): ",".join(map(check_bytes, value))})

                _q_s.logs.info(
                    {
                        "server": _q_s.NAME,
                        "action": "request",
                        "src_ip": addr[0],
                        "src_port": addr[1],
                        "data": headers,
                    }
                )
                response = self.responseFromRequest(200, message)
                response.creationFinished()
                self.deliverResponse(response)

        reactor.listenUDP(port=self.port, protocol=CustomSIPServer(), interface=self.ip)
        reactor.run()

    def test_server(self, ip=None, port=None, username=None, password=None):
        with suppress(Exception):
            from socket import socket, AF_INET, SOCK_DGRAM, IPPROTO_UDP

            _ip = ip or self.ip
            _port = port or self.port
            _username = username or self.username
            _password = password or self.password
            sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
            sock.sendto(
                b"INVITE sip:user_1@test.test SIP/2.0\r\nTo: <sip:user_2@test.test>\r\nFrom: sip:user_3@test.test.test;tag=none\r\nCall-ID: 1@0.0.0.0\r\nCSeq: 1 INVITE\r\nContact: sip:user_3@test.test.test\r\nVia: SIP/2.0/TCP 0.0.0.0;branch=34uiddhjczqw3mq23\r\nContent-Length: 1\r\n\r\nT",
                (_ip, _port),
            )
            sock.close()


if __name__ == "__main__":
    parsed = server_arguments()
    if parsed.docker or parsed.aws or parsed.custom:
        QSIPServer = QSIPServer(
            ip=parsed.ip,
            port=parsed.port,
            username=parsed.username,
            password=parsed.password,
            options=parsed.options,
            config=parsed.config,
        )
        QSIPServer.run_server()
