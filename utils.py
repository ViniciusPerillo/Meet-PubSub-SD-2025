import socket
import ipaddress

def get_ipv6():
    hostname = socket.gethostname()
    try:
        addrs = socket.getaddrinfo(hostname, None, socket.AF_INET6)
        for addr in addrs:
            ip = addr[4][0]
            ip_obj = ipaddress.IPv6Address(ip)
            if ip_obj.is_global:
                return ip
    except socket.gaierror:
        pass
    return None
        
def convert_ipv6_str_to_bin(ip_str: str) -> int:
    return int(ipaddress.IPv6Address(ip_str))

def convert_bin_to_ipv6_str(ip_bin: int) -> str:
    return str(ipaddress.IPv6Address(ip_bin))

def convert_ipv6_list_to_bin(list_ips_str: list[str]) -> int:
    list_sec = []
    for ip_str in list_ips_str:
        list_sec.extend([f'{sec:0>4}' for sec in ip_str.split(':')])

    return int(''.join(list_sec), 16)


def convert_bin_to_ipv6_list(list_ips_bin: int) -> list[str]:
    j = 2
    hex_list = hex(list_ips_bin)
    list_ips_str = []
    stop = False
    
    while not stop:
        list_sec = [hex_list[j:j+32][i:i+4] for i in range(0,32,4)]
        ip_str = ':'.join(list_sec)
        if ip_str == ':::::::':
            stop = True
        else:
            list_ips_str.append(ip_str)
            j += 32

    return list_ips_str
        

    