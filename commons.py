client_file_name_local = "my_ip.txt"
client_port = "51820"
server_file_name_local = "other_ip.txt"

wg_config_file_path = "/etc/wireguard/wg0.conf"

class FileUpdateException(Exception):
    def __init__(self, e: Exception, m):
        super(e)
        self.message = m
