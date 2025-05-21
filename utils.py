import socket

def get_ipv6():
    hostname = socket.gethostname()
    addrs = socket.getaddrinfo(hostname, None, socket.AF_INET6)
    for addr in addrs:
        ip = addr[4][0]
        if ip[0] == '2' or ip[0] == '3':
            return ip
        
def convert_ipv6_str_to_bin(ip_str: str) -> int:
    list_sec = [f'{sec:0>4}' for sec in ip_str.split(':')]
    ip_bin = int(''.join(list_sec), 16)

    return ip_bin

def convert_bin_to_ipv6_str(ip_bin: int) -> str:
   list_sec = [hex(ip_bin)[i:i+4] for i in range(2,34,4)]
   return ':'.join(list_sec)


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
        

    


