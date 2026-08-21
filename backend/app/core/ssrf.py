import socket
import ipaddress
import urllib.parse
from app.core.exceptions import ValidationError

class SSRFProtection:
    BLOCKED_NETWORKS = [
        ipaddress.ip_network("0.0.0.0/8"),
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("100.64.0.0/10"),
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("169.254.0.0/16"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.0.0.0/24"),
        ipaddress.ip_network("192.0.2.0/24"),
        ipaddress.ip_network("192.88.99.0/24"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("198.18.0.0/15"),
        ipaddress.ip_network("198.51.100.0/24"),
        ipaddress.ip_network("203.0.113.0/24"),
        ipaddress.ip_network("224.0.0.0/4"),
        ipaddress.ip_network("240.0.0.0/4"),
        ipaddress.ip_network("255.255.255.255/32"),
        # IPv6
        ipaddress.ip_network("::/128"),
        ipaddress.ip_network("::1/128"),
        ipaddress.ip_network("fc00::/7"),
        ipaddress.ip_network("fe80::/10"),
    ]

    BLOCKED_HOSTNAMES = {
        "localhost",
        "127.0.0.1",
        "::1",
        "metadata.google.internal",
        "instance-data",
        "169.254.169.254",
    }

    @classmethod
    def validate_url(cls, url: str) -> None:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ["http", "https"]:
            raise ValidationError(f"Unsupported protocol scheme: {parsed.scheme}")

        hostname = parsed.hostname
        if not hostname:
            raise ValidationError("Target URL missing hostname")

        if hostname.lower() in cls.BLOCKED_HOSTNAMES:
            raise ValidationError(f"Prohibited target hostname: {hostname}")

        # Resolve DNS safely and check resolved IP
        try:
            addr_info = socket.getaddrinfo(hostname, None)
            for item in addr_info:
                ip_str = item[4][0]
                ip_obj = ipaddress.ip_address(ip_str)
                for net in cls.BLOCKED_NETWORKS:
                    if ip_obj in net:
                        raise ValidationError(
                            f"SSRF Protection: Target resolves to private or restricted IP {ip_str}"
                        )
        except socket.gaierror:
            # Domain could not be resolved in DNS
            pass
