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

from base64 import b64encode, b64decode
from contextlib import suppress
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from json import dumps
from ssl import wrap_socket
from urllib.parse import urlparse
from zlib import compressobj, DEFLATED

from honeypots.base_server import BaseServer
from honeypots.helper import (
    server_arguments,
    create_certificate,
    check_bytes,
)


class QElasticServer(BaseServer):
    NAME = "elastic_server"
    DEFAULT_PORT = 9200
    DEFAULT_USERNAME = "elastic"

    def server_main(self):
        _q_s = self

        class CustomElasticServerHandler(SimpleHTTPRequestHandler):
            server_version = ""
            sys_version = ""

            def _dump_headers(self):
                headers = {}
                with suppress(Exception):
                    for item, value in dict(self.headers).items():
                        headers.update({check_bytes(item): check_bytes(value)})

                _q_s.logs.info(
                    {
                        "server": _q_s.NAME,
                        "action": "dump",
                        "data": check_bytes(self.raw_requestline),
                        "src_ip": self.client_address[0],
                        "src_port": self.client_address[1],
                        "dest_ip": _q_s.ip,
                        "dest_port": _q_s.port,
                        "headers": headers,
                    }
                )
                return headers

            def _remove_headers(self, headers):
                for header in headers:
                    for current_header in self._headers_buffer[:]:
                        if header.lower() in current_header.lower():
                            self._headers_buffer.remove(current_header)

            def _compress_gzip(self, content):
                compressobj_z = compressobj(-1, DEFLATED, 31)
                return compressobj_z.compress(content) + compressobj_z.flush()

            def _set_response_gzip(self, content, code):
                self.send_response(code)
                gzip_compressed_data = self._compress_gzip(content)
                self.send_header("content-encoding", "gzip")
                self.send_header("content-length", str(len(gzip_compressed_data)))
                self.send_header("content-type", "application/json; charset=UTF-8")
                self.end_headers()
                return gzip_compressed_data

            def do_HEAD(self):
                self.send_response(200)
                self.send_header("content-encoding", "gzip")
                self.send_header("content-type", "application/json; charset=UTF-8")
                self.end_headers()

            def _set_response_gzip_auth(self, content, code):
                self._dump_headers()
                self.send_response(code)
                self._remove_headers([b"server:", b"date:"])
                gzip_compressed_data = self._compress_gzip(content)
                self.send_header("content-encoding", "gzip")
                self.send_header("content-length", str(len(gzip_compressed_data)))
                self.send_header("content-type", "application/json; charset=UTF-8")
                self.send_header("WWW-Authenticate", 'Basic realm="security" charset="UTF-8"')
                self.end_headers()
                return gzip_compressed_data

            def do_GET(self):
                username = ""
                password = ""
                e_name = "045dffec8b60"
                e_cluster_name = "R&DBackup"
                e_host = "172.17.0.2"
                e_transport_address = e_host + ":9300"
                e_build_type = "en"
                e_os_name = "Linux"
                e_os_pretty_name = "CentOS Linux 8"
                e_os_version = "5.8.0-53-generic"

                key = self.server.get_auth_key()
                if self.headers.get("Authorization") is None:
                    _q_s.logs.info(
                        {
                            "server": _q_s.NAME,
                            "action": "login",
                            "status": "failed",
                            "src_ip": self.client_address[0],
                            "src_port": self.client_address[1],
                            "dest_ip": _q_s.ip,
                            "dest_port": _q_s.port,
                            "username": username,
                            "password": password,
                        }
                    )
                    auth_paylaod = bytes(
                        dumps(
                            {
                                "error": {
                                    "root_cause": [
                                        {
                                            "type": "security_exception",
                                            "reason": "unable to authenticate user [{}] for REST request [/]".format(
                                                username
                                            ),
                                            "header": {
                                                "WWW-Authenticate": 'Basic realm="security" charset="UTF-8"'
                                            },
                                        }
                                    ],
                                    "type": "security_exception",
                                    "reason": "unable to authenticate user [{}] for REST request [/]".format(
                                        username
                                    ),
                                    "header": {
                                        "WWW-Authenticate": 'Basic realm="security" charset="UTF-8"'
                                    },
                                },
                                "status": 401,
                            }
                        ),
                        "utf-8",
                    )
                    self.wfile.write(self._set_response_gzip_auth(auth_paylaod, 401))
                elif self.headers.get("Authorization") == "Basic " + str(key):
                    extracted = ""
                    _q_s.logs.info(
                        {
                            "server": _q_s.NAME,
                            "action": "login",
                            "status": "success",
                            "src_ip": self.client_address[0],
                            "src_port": self.client_address[1],
                            "dest_ip": _q_s.ip,
                            "dest_port": _q_s.port,
                            "username": _q_s.username,
                            "password": _q_s.password,
                        }
                    )
                    with suppress(Exception):
                        extracted = urlparse(self.path).path
                    if extracted == "/":
                        normal_payload = bytes(
                            dumps(
                                {
                                    "name": e_name,
                                    "cluster_name": e_cluster_name,
                                    "cluster_uuid": "09cf5BKcTCG2U8z2ndwGEw",
                                    "version": {
                                        "number": "7.12.1",
                                        "build_flavor": "default",
                                        "build_type": e_build_type,
                                        "build_hash": "3186837139b9c6b6d23c3200870651f10d3343b7",
                                        "build_date": "2021-04-20T20:56:39.040728659Z",
                                        "build_snapshot": False,
                                        "lucene_version": "8.8.0",
                                        "minimum_wire_compatibility_version": "6.8.0",
                                        "minimum_index_compatibility_version": "6.0.0-beta1",
                                    },
                                    "tagline": "You Know, for Search",
                                }
                            ),
                            "utf-8",
                        )
                        self.wfile.write(self._set_response_gzip(normal_payload, 200))
                    elif extracted.startswith("/_nodes"):
                        _nodes_payload = bytes(
                            dumps(
                                {
                                    "_nodes": {"total": 1, "successful": 1, "failed": 0},
                                    "cluster_name": e_cluster_name,
                                    "nodes": {
                                        "rvyTV3xvTgyt74ti4u12bw": {
                                            "name": e_name,
                                            "transport_address": e_transport_address,
                                            "host": e_host,
                                            "src_ip": e_host,
                                            "version": "7.12.1",
                                            "build_flavor": "default",
                                            "build_type": e_build_type,
                                            "build_hash": "3186837139b9c6b6d23c3200870651f10d3343b7",
                                            "roles": [
                                                "data",
                                                "data_cold",
                                                "data_content",
                                                "data_frozen",
                                                "data_hot",
                                                "data_warm",
                                                "ingest",
                                                "master",
                                                "ml",
                                                "remote_cluster_client",
                                                "transform",
                                            ],
                                            "attributes": {
                                                "ml.machine_memory": "16685318144",
                                                "xpack.installed": "true",
                                                "transform.node": "true",
                                                "ml.max_open_jobs": "20",
                                                "ml.max_jvm_size": "8342470656",
                                            },
                                            "process": {
                                                "refresh_interval_in_millis": 1000,
                                                "id": 7,
                                                "mlockall": False,
                                            },
                                        },
                                        "os": {
                                            "refresh_interval_in_millis": 1000,
                                            "name": e_os_name,
                                            "pretty_name": e_os_pretty_name,
                                            "arch": "amd64",
                                            "version": e_os_version,
                                            "available_processors": 32,
                                            "allocated_processors": 8,
                                        },
                                        "process": {
                                            "refresh_interval_in_millis": 1000,
                                            "id": 7,
                                            "mlockall": False,
                                        },
                                    },
                                }
                            ),
                            "utf-8",
                        )
                        self.wfile.write(self._set_response_gzip(_nodes_payload, 200))
                    elif extracted.startswith("/_cluster/health"):
                        _cluster_health_payload = bytes(
                            dumps(
                                {
                                    "cluster_name": e_cluster_name,
                                    "status": "green",
                                    "timed_out": False,
                                    "number_of_nodes": 1,
                                    "number_of_data_nodes": 1,
                                    "active_primary_shards": 0,
                                    "active_shards": 0,
                                    "relocating_shards": 0,
                                    "initializing_shards": 0,
                                    "unassigned_shards": 0,
                                    "delayed_unassigned_shards": 0,
                                    "number_of_pending_tasks": 0,
                                    "number_of_in_flight_fetch": 0,
                                    "task_max_waiting_in_queue_millis": 0,
                                    "active_shards_percent_as_number": 100.0,
                                }
                            ),
                            "utf-8",
                        )
                        self.wfile.write(self._set_response_gzip(_cluster_health_payload, 200))
                    elif extracted.startswith("/_"):
                        _index = extracted.split("/")[1].lower()
                        _payload = bytes(
                            dumps(
                                {
                                    "error": {
                                        "root_cause": [
                                            {
                                                "type": "invalid_index_name_exception",
                                                "reason": f'Invalid index name [{_index}], must not start with "_".',
                                                "index_uuid": "_na_",
                                                "index": _index,
                                            }
                                        ],
                                        "type": "invalid_index_name_exception",
                                        "reason": f'Invalid index name [{_index}], must not start with "_".',
                                        "index_uuid": "_na_",
                                        "index": _index,
                                    },
                                    "status": 400,
                                }
                            ),
                            "utf-8",
                        )
                        self.wfile.write(self._set_response_gzip(_payload, 400))
                    else:
                        _search = extracted.split("/")[1].lower()
                        _search_payload = bytes(
                            dumps(
                                {
                                    "error": {
                                        "root_cause": [
                                            {
                                                "type": "index_not_found_exception",
                                                "reason": f"no such index [{_search}]",
                                                "resource.type": "index_or_alias",
                                                "resource.id": _search,
                                                "index_uuid": "_na_",
                                                "index": _search,
                                            }
                                        ],
                                        "type": "index_not_found_exception",
                                        "reason": f"no such index [{_search}]",
                                        "resource.type": "index_or_alias",
                                        "resource.id": _search,
                                        "index_uuid": "_na_",
                                        "index": _search,
                                    },
                                    "status": 404,
                                }
                            ),
                            "utf-8",
                        )
                        self.wfile.write(self._set_response_gzip(_search_payload, 404))
                else:
                    authorization_string = self.headers.get("Authorization").split(" ")
                    basic = b64decode(authorization_string[1]).decode("utf-8")
                    username, password = basic.split(":")
                    _q_s.logs.info(
                        {
                            "server": _q_s.NAME,
                            "action": "login",
                            "status": "failed",
                            "src_ip": self.client_address[0],
                            "src_port": self.client_address[1],
                            "dest_ip": _q_s.ip,
                            "dest_port": _q_s.port,
                            "username": username,
                            "password": password,
                        }
                    )
                    auth_paylaod = bytes(
                        dumps(
                            {
                                "error": {
                                    "root_cause": [
                                        {
                                            "type": "security_exception",
                                            "reason": "missing authentication credentials for REST request [/]",
                                            "header": {
                                                "WWW-Authenticate": 'Basic realm="security" charset="UTF-8"'
                                            },
                                        }
                                    ],
                                    "type": "security_exception",
                                    "reason": "missing authentication credentials for REST request [/]",
                                    "header": {
                                        "WWW-Authenticate": 'Basic realm="security" charset="UTF-8"'
                                    },
                                },
                                "status": 401,
                            }
                        ),
                        "utf-8",
                    )
                    self.wfile.write(self._set_response_gzip_auth(auth_paylaod, 401))

            do_POST = do_GET
            do_PUT = do_GET
            do_DELETE = do_GET

            def send_error(self, code, message=None):
                self.error_message_format = "Error!"
                SimpleHTTPRequestHandler.send_error(self, code, message)

            def log_message(self, format, *args):
                return

            def handle_one_request(self):
                _q_s.logs.info(
                    {
                        "server": _q_s.NAME,
                        "action": "connection",
                        "src_ip": self.client_address[0],
                        "src_port": self.client_address[1],
                        "dest_ip": _q_s.ip,
                        "dest_port": _q_s.port,
                    }
                )
                return SimpleHTTPRequestHandler.handle_one_request(self)

        class CustomElasticServer(ThreadingHTTPServer):
            key = b64encode(bytes("%s:%s" % ("elastic", "changeme"), "utf-8")).decode("ascii")

            def __init__(self, address, handlerClass=CustomElasticServerHandler):
                super().__init__(address, handlerClass)

            def set_auth_key(self, username, password):
                self.key = b64encode(f"{username}:{password}".encode()).decode("ascii")

            def get_auth_key(self):
                return self.key

        with create_certificate() as (cert, key):
            server = CustomElasticServer((self.ip, self.port))
            server.set_auth_key(self.username, self.password)
            server.socket = wrap_socket(
                server.socket,
                keyfile=key,
                certfile=cert,
                server_side=True,
            )
            server.serve_forever()

    def test_server(self, ip=None, port=None, username=None, password=None):
        with suppress(Exception):
            from elasticsearch import Elasticsearch

            _ip = ip or self.ip
            _port = port or self.port
            _username = username or self.username
            _password = password or self.password
            es = Elasticsearch(
                [f"https://{_ip}:{_port}"],
                http_auth=(_username, _password),
                verify_certs=False,
            )
            es.search(index="test", body={}, size=99)


if __name__ == "__main__":
    parsed = server_arguments()
    if parsed.docker or parsed.aws or parsed.custom:
        qelasticserver = QElasticServer(
            ip=parsed.ip,
            port=parsed.port,
            username=parsed.username,
            password=parsed.password,
            options=parsed.options,
            config=parsed.config,
        )
        qelasticserver.run_server()
