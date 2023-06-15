from commons import *
import sys, getopt
import urllib.request

from update_ip_files import DeviceType, update_ip_files

class ConfigNotFoundException(Exception):
    pass

def update_conf_file(server_ip):
    with open(wg_config_file_path) as wg_config_file:
        wg_config_file_new = ""
        lines = wg_config_file.readlines()
        found_peer = False
        new_file_ready = False
        for line in lines:
            if line.find("[Peer]") != -1:
                found_peer = True
            if line.find("Endpoint") != -1 and found_peer:
                wg_config_file_new += "Endpoint = " + server_ip + "\n"
            else:
                wg_config_file_new += line
                new_file_ready = True
    if new_file_ready:
        with open(wg_config_file_path, "w") as wg_config_file:
            wg_config_file.write(wg_config_file_new)
    return

def main(argv):
    device_type = DeviceType.CLIENT
    opts, args = getopt.getopt(argv, "t:", ["type="])
    for opt, arg in opts:
        if opt == '-h':
            print('-t \t type: c or s')
            sys.exit()
        elif opt in ("-t", "--type"):
            device_type = DeviceType.SERVER if arg.lower().startswith("s") else DeviceType.CLIENT

    server_ip_old = None
    server_ip = None
    client_ip = None

    try:
        client_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
    except Exception:
        error_client_ip = True
        print(f"Cannot retrieve my IP")
    if client_ip is not None:
        print(f"My IP is {client_ip}")
        with open(client_file_name_local, "w") as client_file:
            client_file.write(client_ip + ":" + client_port)

    with open(server_file_name_local) as server_file_local:
        server_ip_old = server_file_local.read().strip()
    server_ip_downloaded, client_ip_uploaded, server_ip = update_ip_files(device_type)
    print(f"Other IP is {server_ip}")
    if client_ip_uploaded:
        print(f"My IP has been uploaded successfully")
    else:
        print(f"My IP has NOT been uploaded")
    if server_ip_downloaded:
        print(f"Server IP has been downloaded successfully")
    else:
        print(f"Server IP has NOT been downloaded")
    print(f"Other IP is {server_ip}")

    if server_ip is None:
        with open(server_file_name_local) as server_file_local:
            server_ip = server_file_local.read()
    if server_ip_old == server_ip:
        print("Nothing to update in local wg config")
        return
    update_conf_file(server_ip)


if __name__ == '__main__':
    main(sys.argv[1:])
