import threading
import socket
import time
from kivy.logger import Logger
from kivy.properties import OptionProperty, ObjectProperty, StringProperty, ListProperty, BooleanProperty, NumericProperty, DictProperty
from kivy.uix.widget import Widget
debug = True


def dprint(message):
    if debug:
        Logger.info("TVMP: "+str(message))


def split_at_n(text, splitter, n):
    groups = text.split(splitter)
    return splitter.join(groups[:n]), splitter.join(groups[n:])


class Connector(Widget):
    main_socket = ObjectProperty(allownone=True)
    secondary_socket = ObjectProperty(allownone=True)
    server_socket = ObjectProperty(allownone=True)
    server_timeout = NumericProperty(0)
    max_timeout = NumericProperty(30)

    available_addresses = ListProperty()
    timeout_time = NumericProperty(10)

    update_thread = ObjectProperty(allownone=True)
    mode = StringProperty('scanning')
    last_mode = StringProperty('scanning')
    cancel_thread = BooleanProperty(False)

    connect_action = StringProperty('Connect...')  #the action the user should take next
    connect_status = StringProperty('Ready To Connect')  #current status of the connector
    connection_retries = NumericProperty(0)
    max_connection_tries = NumericProperty(30)
    local_ip = StringProperty()
    remote_ip = StringProperty()
    connect_ip = StringProperty()
    broadcast_address = StringProperty('')
    app_name = StringProperty('')
    port = NumericProperty(0)
    delay_time = NumericProperty(1)
    connect_external = BooleanProperty(False)

    ignore_connect = StringProperty()
    ignore_index = NumericProperty(0)
    connected = BooleanProperty(False)
    connecting = BooleanProperty(False)

    def __init__(self, **kwargs):
        self.register_event_type('on_ask_connect')
        self.register_event_type('on_connect')
        self.register_event_type('on_disconnect')
        self.register_event_type('on_receive')
        self.register_event_type('on_mode')
        self.register_event_type('on_connected')
        super().__init__(**kwargs)

    def start(self):
        #Starts the connection update thread
        dprint("Start connect thread")
        if self.update_thread is not None:
            dprint("Connect thread already running")
            return
        #self.connect_status = 'Ready To Connect'
        self.cancel_thread = False
        self.local_ip = self.get_ip()
        self.update_thread = threading.Thread(target=self.update_thread_function)
        self.update_thread.start()

    def stop(self):
        self.cancel_thread = True
        while self.update_thread:
            pass
        self.cleanup()
        self.cleanup_server()
        self.mode = 'scanning'
        self.last_mode = 'scanning'

    def restart(self, external=False):
        #Cancel thread and wait for restart
        dprint("Restart connect thread")
        self.connect_external = external
        self.cancel_thread = True
        while self.update_thread:
            pass
        self.start()

    def cleanup(self):
        dprint("Reset sockets")
        if self.main_socket is not None:
            self.main_socket.close()
            self.main_socket = None
        if self.secondary_socket is not None:
            self.secondary_socket.close()
            self.secondary_socket = None

    def cleanup_server(self):
        dprint("Reset server socket")
        if self.server_socket is not None:
            try:
                self.server_socket.shutdown(2)
            except:
                pass
            self.server_socket.close()
            self.server_socket = None

    def connect_action_call(self):
        #performs the command indicated by 'connect_action'
        dprint("Connect action called")
        if self.mode == 'scanning':
            if self.connect_external:
                self.mode = 'portforward'
            else:
                self.mode = 'connecting'
        elif self.mode in ['connecting', 'connected', 'connectto']:
            if self.mode == 'connected':
                self.cleanup_server()
                self.connect_status = 'Disconnected'
                self.dispatch('on_disconnect')
            self.mode = 'scanning'

    def refuse_connect(self):
        dprint("Connection refused locally")
        self.ignore_connect = self.connect_ip

    def connect_to(self):
        #sets self.mode = 'connectto' if possible, called when should connect to server
        dprint("Trying to connect...")
        if self.mode == 'scanning':
            self.remote_ip = self.connect_ip
            self.mode = 'connectto'

    def init_update_thread(self):
        self.available_addresses = []
        self.connected = False
        self.connecting = False
        if self.mode == 'scanning':
            dprint("Init scanning mode")
            self.delay_time = 1
            self.connect_action = 'Connect...'
            if self.connect_external:
                pass
            else:
                #setup transmitter
                self.broadcast_address = self.local_ip.rsplit('.', 1)[0] + '.255'
                dprint("Broadcast address: "+self.broadcast_address)
                self.main_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
                self.main_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                self.main_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.main_socket.bind(("", self.port))
                self.main_socket.settimeout(0)

                #setup receiver
                self.secondary_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
                self.secondary_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.secondary_socket.bind(("", self.port))
                self.secondary_socket.settimeout(.1)
        elif self.mode == 'portforward':
            dprint("Init port forwarding request")
            self.delay_time = 1
            self.connecting = True
            self.connection_retries = 0
            self.connect_action = 'Cancel'
            self.connect_status = 'Setting Up Port Forward'
            self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            SSDP_ADDR = "239.255.255.250"
            SSDP_PORT = 1900
            SSDP_MX = 2
            SSDP_ST = "urn:schemas-upnp-org:device:InternetGatewayDevice:1"
            ssdpRequest = "M-SEARCH * HTTP/1.1\r\n" + \
                          "HOST: %s:%d\r\n" % (SSDP_ADDR, SSDP_PORT) + \
                          "MAN: \"ssdp:discover\"\r\n" + \
                          "MX: %d\r\n" % (SSDP_MX,) + \
                          "ST: %s\r\n" % (SSDP_ST,) + "\r\n"

            self.main_socket.sendto(bytes(ssdpRequest, 'utf-8'), (SSDP_ADDR, SSDP_PORT))
        elif self.mode == 'connecting':
            dprint("Init connecting mode")
            self.delay_time = 1
            self.connecting = True
            self.connection_retries = 0
            self.connect_action = 'Cancel'
            self.connect_status = 'Waiting For Reply'

            #setup server
            self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.main_socket.bind(("", self.port))
            self.main_socket.settimeout(.1)
            self.main_socket.listen(1)

            #setup transmitter
            self.secondary_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            self.secondary_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.secondary_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.secondary_socket.settimeout(0)
        elif self.mode == 'connectto':
            dprint("Init connect-to mode")
            self.delay_time = 1
            self.connecting = True
            self.connect_action = 'Cancel'
            self.connect_status = 'Connecting...'
            self.server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
            self.server_socket.settimeout(10)
        elif self.mode == 'connected':
            dprint("Init connected mode")
            self.server_timeout = 0
            self.server_socket.setblocking(True)
            self.server_socket.settimeout(0.1)
            self.delay_time = 0.1
            self.connected = True
            self.connect_action = 'Disconnect'
            self.connect_status = 'Connected'
            self.dispatch('on_connect')

    def update_thread_function(self):
        dprint("Starting update thread")
        self.init_update_thread()
        delay = 0
        while not self.cancel_thread:
            delay += 1
            if self.mode != self.last_mode:
                #mode changed, restart updater
                dprint("Update mode changed to: "+self.mode)
                self.dispatch('on_mode')
                self.last_mode = self.mode
                self.cleanup()
                self.update_thread = None
                self.start()
                return
            if delay >= 10:
                status = self.update_send()
                if status is False:
                    self.cleanup()
                    self.init_update_thread()
                    continue
                delay = 0
            status = self.update_receive()
            if status is False:
                self.cleanup()
                self.init_update_thread()
                continue
            self.server_timeout += 0.1
            #time.sleep(.1)
        dprint("Ending update thread")
        self.cleanup()
        self.update_thread = None

    def update_send(self):
        mode = self.last_mode
        if mode == 'scanning':
            #connection scanner and transmitter
            if self.connect_external:
                #external connection mode, dont do anything
                pass
            else:
                if self.main_socket is None:
                    return False
                #send message
                plain_message = self.app_name+' Looking for multiplayer from:'+self.local_ip
                send_message = str.encode(plain_message)
                dprint("Send message: "+plain_message)
                self.main_socket.sendto(send_message, (self.broadcast_address, self.port))
        elif mode == 'portforward':
            #We only want the message sent once, so do nothing here
            pass
        elif mode == 'connecting':
            #Transmitter asking for client to connect
            self.connection_retries += 1
            if self.connection_retries > self.max_connection_tries:
                #timed out waiting for a connection
                return self.fail_connect("Connect Timed Out")
            plain_message = self.app_name+' Starting server for:'+self.remote_ip+'|'+str(self.connection_retries)
            send_message = str.encode(plain_message)
            dprint("Connection message: "+plain_message)
            try:
                self.secondary_socket.sendto(send_message, (self.broadcast_address, self.port))
            except Exception as e:
                return self.fail_connect(str(e))
        elif mode == 'connectto':
            try:
                self.server_socket.connect((self.remote_ip, self.port))
                dprint("Connected to: "+str(self.remote_ip)+' on port: '+str(self.port))
                self.dispatch('on_connected')
                self.mode = 'connected'
            except Exception as e:
                self.mode = 'scanning'
                dprint("Failed to connect")
                self.connect_status = 'Failed To Connect!'
        elif mode == 'connected':
            self.send('0')
        return True

    def fail_connect(self, message):
        dprint(message)
        self.connect_status = message
        self.mode = 'scanning'
        return False

    def update_receive(self):
        mode = self.last_mode
        if mode == 'scanning':
            if self.connect_external:
                pass
            else:
                #check for messages
                try:
                    message, address = self.secondary_socket.recvfrom(4096)
                    ip, port = address
                    if ip != self.local_ip:
                        message = message.decode("utf-8")
                        dprint("Scanning received: (" + str(ip) + ":" + str(port) + ")" + message)
                        if message.startswith(self.app_name+' Looking for multiplayer from:'):
                            in_available = False
                            for available in self.available_addresses:
                                if available['ip'] == ip:
                                    available['refresh_time'] = time.time()
                                    in_available = True
                                    break
                            if not in_available:
                                self.available_addresses.append({'ip': ip, 'refresh_time': time.time()})
                        elif message.startswith(self.app_name+' Starting server for:'+self.local_ip):
                            if ip == self.ignore_connect:
                                try:
                                    ignore_index = int(message.split('|')[1])
                                except:
                                    ignore_index = 0
                                if ignore_index > self.ignore_index:
                                    self.ignore_index = ignore_index
                                else:
                                    self.ignore_index = 0
                                    self.ignore_connect = ''
                            else:
                                self.connect_ip = ip
                                self.dispatch('on_ask_connect')
                except Exception as e:
                    if str(e) != 'timed out':
                        return False
                self.prune_availables()
        elif mode == 'portforward':
            self.connect_status = 'Attempting Port Forward'
            try:
                #Parse the received data
                message, address = self.main_socket.recvfrom(4096)
                ip, port = address
                message = message.decode('utf-8').split('\r\n')
                location_url = ''
                for chunk in message:
                    if chunk.lower().startswith('location:'):
                        location_url = chunk.split(': ')[1]
                        break

                #Download the xml port forwarding info
                from kivy.network.urlrequest import UrlRequest
                if location_url:
                    dprint('Port forward info link: '+location_url)
                    request = UrlRequest(location_url, timeout=self.timeout_time)
                    request.wait()
                    xml_data = request.result
                    router_url = split_at_n(location_url, '/', 3)[0]
                else:
                    return self.fail_connect('No Info Provided By Router')

                #Parse the xml file
                from xml.dom.minidom import parseString, Document
                xml_tree = parseString(xml_data)
                service_types = xml_tree.getElementsByTagName('serviceType')

                def find_xml_node(nodes, text):
                    for node in nodes:
                        if text in node.childNodes[0].data:
                            return node
                    return None

                found_type = 'WANIPConnection'
                found_xml = find_xml_node(service_types, found_type)
                if found_xml is None:
                    found_type = 'WANPPPConnection'
                    found_xml = find_xml_node(service_types, found_type)
                if found_xml is None:
                    return self.fail_connect('No Port Forwarding Available')
                control_url = found_xml.parentNode.getElementsByTagName('controlURL')[0].childNodes[0].data
                if not control_url:
                    return self.fail_connect('No Port Forwarding Available')

                #Create data to send to router
                send_data = Document()
                send_envelope = send_data.createElementNS('', 's:Envelope')
                send_envelope.setAttribute('xmlns:s', 'http://schemas.xmlsoap.org/soap/envelope/')
                send_envelope.setAttribute('s:encodingStyle', 'http://schemas.xmlsoap.org/soap/encoding/')
                send_body = send_data.createElementNS('', 's:Body')
                send_function = send_data.createElementNS('', 'u:AddPortMapping')
                send_function.setAttribute('xmlns:u', 'urn:schemas-upnp-org:service:'+found_type+':1')
                arguments = [
                    ('NewExternalPort', str(self.port)),  # specify port on router
                    ('NewProtocol', 'TCP'),  # specify protocol
                    ('NewInternalPort', str(self.port)),  # specify port on internal host
                    ('NewInternalClient', self.local_ip),  # specify IP of internal host
                    ('NewEnabled', '1'),  # turn mapping ON
                    ('NewPortMappingDescription', 'Tetrivium Port Forward'),  # add a description
                    ('NewLeaseDuration', '0')]  # how long should it be opened?
                argument_list = []
                for k, v in arguments:
                    tmp_node = send_data.createElement(k)
                    tmp_text_node = send_data.createTextNode(v)
                    tmp_node.appendChild(tmp_text_node)
                    argument_list.append(tmp_node)
                for arg in argument_list:
                    send_function.appendChild(arg)
                send_body.appendChild(send_function)
                send_envelope.appendChild(send_body)
                send_data.appendChild(send_envelope)
                send_xml = send_data.toxml()

                #Send data to router to request port forward
                headers = {'SOAPAction': '"urn:schemas-upnp-org:service:'+found_type+':1#AddPortMapping"', 'Content-Type': 'text/xml'}
                send_request = UrlRequest(router_url+control_url, req_body=send_xml, req_headers=headers, timeout=self.timeout_time)
                send_request.wait()
                status = send_request.resp_status
                if status != 200:
                    return self.fail_connect('Port Forward Denied By Router')
                dprint('Port Forward Accepted')
                self.mode = 'connecting'
                #import code; vars = globals().copy(); vars.update(locals()); shell = code.InteractiveConsole(vars); shell.interact()

            except Exception as e:
                if str(e) != 'timed out':
                    dprint('Port forward request timed out')
                    return False
                else:
                    dprint(e)
                    return self.fail_connect('Unable To Request Port Forward')
        elif mode == 'connecting':
            #Server receiving connections
            self.connect_status = 'Waiting For Reply'
            try:
                connection, client_address = self.main_socket.accept()
                if client_address[0] != self.remote_ip:
                    #incorrect connection address
                    return self.fail_connect("Incorrect connection: "+str(connection)+" ("+str(client_address)+")")
                else:
                    #correct connection
                    dprint("Correct connection: "+str(connection)+" ("+str(client_address)+")")
                    self.server_socket = connection
                    self.mode = 'connected'
                    self.dispatch('on_connected')
            except Exception as e:
                if str(e) != 'timed out':
                    self.mode = 'scanning'
                    return False
                pass
        elif mode == 'connectto':
            pass
        elif mode == 'connected':
            message_data = self.recv()
            if message_data:
                messages = message_data.split('|')
                for message in messages:
                    if message:
                        self.server_timeout = 0
                        if message != '0':
                            dprint("Message received: "+message)
                            self.dispatch('on_receive', message)
            if self.server_timeout > self.max_timeout:
                dprint("Connection timed out")
                self.cleanup_server()
                self.connect_status = 'Connection Timed Out'
                self.dispatch('on_disconnect')
                self.mode = 'scanning'
        return True

    def recv(self):
        if self.mode == 'connected':
            try:
                message = self.server_socket.recv(4096)
                message = message.decode("utf-8")
                return message
            except Exception as e:
                if str(e) != 'timed out':
                    self.cleanup_server()
                    self.dispatch('on_disconnect')
                    self.connect_status = "Disconnected"
                    self.mode = 'scanning'

    def send(self, message):
        if self.mode == 'connected':
            try:
                encoded_message = str.encode(message+'|')
                status = self.server_socket.send(encoded_message)
                dprint("Send message: "+message+" ("+str(status)+")")
            except Exception as e:
                return None

    def get_ip(self):
        if self.connect_external:
            return ''
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # doesn't even have to be reachable
                s.connect(('10.255.255.255', 1))
                ip = s.getsockname()[0]
            except:
                ip = '127.0.0.1'
            finally:
                s.close()
            dprint("Found local ip: "+str(ip))
            return ip

    def prune_availables(self):
        #clean up available addresses if they are expired

        current_time = time.time()
        for available in reversed(self.available_addresses):
            update_time = current_time - available['refresh_time']
            if update_time > self.timeout_time:
                self.available_addresses.remove(available)

    def on_ask_connect(self):
        pass

    def on_mode(self, *_):
        pass

    def on_connect(self):
        pass

    def on_disconnect(self):
        pass

    def on_receive(self, message):
        pass

    def on_connected(self, *_):
        pass
