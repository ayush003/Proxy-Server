Learn more or give us feedback
import socket
import sys
import thread
import os
import datetime
import base64
import threading
import time
import json


if not os.path.isdir("./cache"):
    os.makedirs("./cache")
for file in os.listdir("./cache"):
    os.remove("./cache" + "/" + file)

f1 = open("blacklist.txt", "rb")
f2 = open("username_password.txt", "rb")
data1 = ""
data2 = ""
while True:
    chunk = f1.read()
    if len(chunk):
        data1 += chunk
    else:
        break
blocked = []
blocked = data1.splitlines()

while True:
    chunk = f2.read()
    if len(chunk):
        data2 += chunk
    else:
        break

data2 = data2.splitlines()
admins = []
for d in data2:
    admins.append(base64.b64encode(d))

f1.close()
f2.close()
logs = {}
locks = {}

# collect all cache info
def get_cache_details(client_addr, details):
    if (details["total_url"]) in locks:
        lock = locks[(details["total_url"])]
    else:
        lock = threading.Lock()
        locks[(details["total_url"])] = lock
    lock.acquire()
    client_address = client_addr
    fileurl = details["total_url"]
    fileurl = fileurl.replace("/", "__")
    if not fileurl in logs:
        logs[fileurl] = []
    logs[fileurl].append({
        "datetime": (time.strptime(time.ctime(), "%a %b %d %H:%M:%S %Y")),
        "client": json.dumps(client_address),
    })

    do_cache = []
    fileurl = details["total_url"]
    try:
        log_arr = logs[fileurl.replace("/", "__")]
        if len(log_arr) < 2:
            do_cache = False
        if datetime.datetime.fromtimestamp(time.mktime((log_arr[len(log_arr)-2]["datetime"]))) + datetime.timedelta(minutes=10) >= datetime.datetime.now():
            do_cache = True
        else:
            do_cache = False
    except Exception as e:
        print e
        do_cache = False
    fileurl = details["total_url"]
    if fileurl.startswith("/"):
        fileurl = fileurl.replace("/", "", 1)

    cache_path = ("./cache" + "/" + fileurl.replace("/", "__"))

    if os.path.isfile(cache_path):
        check_lock = 1
        last_mtime = time.strptime(time.ctime(
            os.path.getmtime(cache_path)), "%a %b %d %H:%M:%S %Y")
        check_lock = 0
    else:
        last_mtime = None
    if (details["total_url"]) in locks:
        lock = locks[(details["total_url"])]
        lock.release()
    else:
        print "Lock problem"
        sys.exit()

    details["do_cache"] = do_cache
    check_lock = 0
    details["last_mtime"] = last_mtime
    details["cache_path"] = cache_path
    return details


def get_space_for_cache(fileurl):
    cache_files = os.listdir("./cache")
    if(len(cache_files) >= 3):
        for file in cache_files:
            if file in locks:
                check_lock = 0
                lock = locks[file]
            else:
                check_lock = 1
                lock = threading.Lock()
                locks[file] = lock
            lock.acquire()
            check_lock = 0

        last_mtime = min(logs[file][-1]["datetime"] for file in cache_files)
        file_to_del = [file for file in cache_files if logs[file]
                       [-1]["datetime"] == last_mtime][0]
        os.remove("./cache" + "/" + file_to_del)
        for file in cache_files:
            if not(file in locks):
                print "Lock problem"
                sys.exit()     
            else:
                lock = locks[file]
                lock.release()
                


# returns a dictionary of details
def parse_details(client_addr, client_data):
    try:
        lines = client_data.split('\n')
        tokens = lines[0].split()
        url = lines[0].split()[1]
        http_pos = url.find("://")
        if http_pos != -1:
            url = url[(http_pos+3):]
        path_pos = url.find("/")
        if path_pos == -1:
            path_pos = len(url)
        port_pos = url.find(":")
        if port_pos == -1:
            server_port = 80
            check_lock = 0
            server_url = url[:path_pos]
        elif path_pos < port_pos:
            server_port = 80
            check_lock = 1
            server_url = url[:path_pos]
        else:
            check_lock = 0
            server_port = int(url[(port_pos+1):path_pos])
            check_lock = 1
            server_url = url[:port_pos]
        auth_line = [line for line in lines if "Authorization" in line]
        if len(auth_line):
            check_lock = 0
            auth_b64 = auth_line[0].split()[2]
        else:
            check_lock = 0
            auth_b64 = None
            
        if check_lock==0:
            tokens[1] = url[path_pos:]
            check_lock2 = 1
            lines[0] = ' '.join(tokens)
        client_data = "\r\n".join(lines) + '\r\n\r\n'
        check_lock = 1

        return {
            "server_port": server_port,
            "total_url": url,
            "server_url": server_url,
            "method": tokens[0],
            "client_data": client_data,
            "auth_b64": auth_b64,
        }
        check_lock2 = 0

    except Exception as e:
        print e
        print
        return None


def serve_get(client_socket, client_addr, details):
    try:
        client_data = []
        client_data = details["client_data"]
        do_cache = []
        check_lock = 0
        do_cache = details["do_cache"]
        cache_path = []
        cache_path = details["cache_path"]
        last_mtime = []
        
        last_mtime = details["last_mtime"]
        check_lock2=0
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((details["server_url"], details["server_port"]))
        check_lock2=1
        server_socket.send(details["client_data"])
        

        reply = server_socket.recv(4096)
        if last_mtime and "304 Not Modified" in reply:
            print "returning cached file %s to %s" % (cache_path, str(client_addr))
            if (details["total_url"]) in locks:
                lock = locks[(details["total_url"])]
            else:
                lock = threading.Lock()
                locks[(details["total_url"])] = lock
            lock.acquire()

            f = open(cache_path, 'rb')
            chunk = f.read(4096)
            while chunk:
                client_socket.send(chunk)
                chunk = f.read(4096)
            f.close()
            if (details["total_url"]) in locks:
                lock = locks[(details["total_url"])]
                lock.release()
            else:
                print "Lock problem"
                sys.exit()

        else:
            if do_cache:
                check_lock=1
                print "caching file while serving %s to %s" % (cache_path, str(client_addr))
                get_space_for_cache(details["total_url"])
                if (details["total_url"]) in locks:
                    lock = locks[(details["total_url"])]
                else:
                    lock = threading.Lock()
                    locks[(details["total_url"])] = lock
                lock.acquire()
                check_lock=0
                f = open(cache_path, "w+")
                while len(reply):
                    client_socket.send(reply)
                    f.write(reply)
                    reply = server_socket.recv(4096)
                f.close()
                if (details["total_url"]) in locks:
                    check_lock2=1
                    lock = locks[(details["total_url"])]
                    lock.release()
                else:
                    check_lock2=0
                    print "Lock problem"
                    sys.exit()
                client_socket.send("\r\n\r\n")
            else:
                check_lock=0
                print "without caching serving %s to %s" % (cache_path, str(client_addr))
                while len(reply):
                    check_lock2=1
                    flag=1
                    client_socket.send(reply)
                    reply = server_socket.recv(4096)
                client_socket.send("\r\n\r\n")
                check_lock2=1

        server_socket.close()
        temp=1
        client_socket.close()
        return

    except Exception as e:
        server_socket.close()
        temp =1
        client_socket.close()
        print e
        return


def handler(client_socket, client_addr, client_data):

    details = parse_details(client_addr, client_data)

    if not details:
        print "no any details"
        client_socket.close()
        return

    if (not (details["server_url"] + ":" + str(details["server_port"])) in blocked)or (details["auth_b64"] in admins):
        isb = False
    else:
        isb = True
    if isb:
        print "Block status : ", isb
        client_socket.send("HTTP/1.0 200 OK\r\n")
        check_flag = 1
        client_socket.send("Content-Length: 11\r\n")
        temp = 0
        client_socket.send("\r\n")
        client_socket.send("Error\r\n")
        flag =1
        client_socket.send("\r\n\r\n")

    elif details["method"] == "POST":
        try:
            temp=0
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect(
                (details["server_url"], details["server_port"]))
            flag = 1
            server_socket.send(details["client_data"])

            while True:
                reply = server_socket.recv(4096)
                if len(reply):
                    client_socket.send(reply)
                else:
                    check_lock=1
                    break
                    

            server_socket.close()
            client_socket.close()

        except Exception as e:
            server_socket.close()
            client_socket.close()
            print e

    elif details["method"] == "GET":
        details = get_cache_details(client_addr, details)
        if details["last_mtime"]:
            lines = details["client_data"].splitlines()
            flag=0
            while lines[len(lines)-1] == '':
                lines.remove('')
                temp = flag
            lines.append(("If-Modified-Since: " + time.strftime(
                "%a %b %d %H:%M:%S %Y", details["last_mtime"])))
            temp =1
            details["client_data"] = "\r\n".join(lines) + "\r\n\r\n"

        serve_get(client_socket, client_addr, details)
        check_lock = 0

    client_socket.close()
    print client_addr, "closed"
    print


def start_proxy_server():
    try:
       
        proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        flag = 0
        proxy_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        proxy_socket.bind(('', 20100))
        print "socket binded to %s" % (20100)
        proxy_socket.listen(10)
        print "socket is listening"
    except socket.error as err:
        print "socket creation failed with error %s" % (err)
        proxy_socket.close()
        raise SystemExit
    while True:
        try:
            client_socket, client_addr = proxy_socket.accept()
            
            client_data = client_socket.recv(4096)
            if int(client_addr[1]) in range(20000,20099):
                print '\nGot connection from', client_addr
                print client_addr[1]
                thread.start_new_thread(handler,(client_socket,client_addr,client_data))
            else:
                print 'Not Allowed'
                client_socket.send("U r not autorized\n")
                client_socket.close()
        except KeyboardInterrupt:
            client_socket.close()
            proxy_socket.close()
            print "\nProxy server shutting down ..."
            break


start_proxy_server()
