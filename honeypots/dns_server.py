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

from __future__ import annotations

from contextlib import suppress

from twisted.internet import defer, reactor
from twisted.names import dns, error, client
from twisted.names.server import DNSServerFactory

from honeypots.base_server import BaseServer
from honeypots.helper import (
    server_arguments,
)


class QDNSServer(BaseServer):
    NAME = "dns_server"
    DEFAULT_PORT = 53

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.resolver_addresses = [("8.8.8.8", 53)]

    def server_main(self):
        _q_s = self

        class CustomClientResolver(client.Resolver):
            def queryUDP(self, queries, timeout=2):
                res = client.Resolver.queryUDP(self, queries, timeout)

                def queryFailed(reason):
                    return defer.fail(error.DomainError())

                res.addErrback(queryFailed)
                return res

        class CustomDNSServerFactory(DNSServerFactory):
            def gotResolverResponse(self, response, protocol, message, address):
                if address is None:
                    src_ip, src_port = "None", "None"
                else:
                    src_ip, src_port = address
                for items in response:
                    for item in items:
                        _q_s.logs.info(
                            {
                                "server": _q_s.NAME,
                                "action": "query",
                                "src_ip": src_ip,
                                "src_port": src_port,
                                "dest_ip": _q_s.ip,
                                "dest_port": _q_s.port,
                                "data": item.payload,
                            }
                        )
                return super().gotResolverResponse(response, protocol, message, address)

        class CustomDnsUdpProtocol(dns.DNSDatagramProtocol):
            def datagramReceived(self, data: bytes, addr: tuple[str, int]):
                _q_s.logs.info(
                    {
                        "server": _q_s.NAME,
                        "action": "connection",
                        "src_ip": addr[0],
                        "src_port": addr[1],
                        "dest_ip": _q_s.ip,
                        "dest_port": _q_s.port,
                        "data": data.decode(errors="replace"),
                    }
                )
                super().datagramReceived(data, addr)

        self.resolver = CustomClientResolver(servers=self.resolver_addresses)
        self.factory = CustomDNSServerFactory(clients=[self.resolver])
        self.protocol = CustomDnsUdpProtocol(controller=self.factory)
        reactor.listenUDP(self.port, self.protocol, interface=self.ip)
        reactor.listenTCP(self.port, self.factory, interface=self.ip)
        reactor.run()

    def test_server(self, ip=None, port=None, domain=None):
        with suppress(Exception):
            from dns.resolver import Resolver

            res = Resolver(configure=False)
            res.nameservers = [self.ip]
            res.port = self.port
            temp_domain = domain or "example.org"
            r = res.query(temp_domain, "a")


if __name__ == "__main__":
    parsed = server_arguments()
    if parsed.docker or parsed.aws or parsed.custom:
        qdnsserver = QDNSServer(ip=parsed.ip, port=parsed.port, config=parsed.config)
        qdnsserver.run_server()
