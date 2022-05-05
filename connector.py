"""
Notes/todo:
    currently restarting the main connector thread, or changing modes can be pretty messy... need to unify this better
    should look into 'un-forwarding' a port when a 'ConflictInMappingEntry' error happens
    add direct connection, non port-forwarded option (with ability to set port)
    sometimes detected external ip address might be wrong for some reason?
    add option for bluetooth networking - https://gist.github.com/tito/7432757
"""

import threading
import socket
import time
from kivy.logger import Logger
from kivy.properties import OptionProperty, ObjectProperty, StringProperty, ListProperty, BooleanProperty, NumericProperty, DictProperty
from kivy.uix.widget import Widget
from xml.dom.minidom import parseString
from xml.dom.minidom import Node as xml_node
from kivy.clock import Clock

from kivy.network.urlrequest import UrlRequest

debug = True


def dprint(message):
    if debug:
        Logger.info("TVMP: "+str(message))


def split_at_n(text, splitter, n):
    groups = text.split(splitter)
    return splitter.join(groups[:n]), splitter.join(groups[n:])


class PortForwarder(Widget):
    #This class only handles port forwarding

    timeout_time = NumericProperty(10)
    protocol = StringProperty('TCP')
    local_port = NumericProperty(1)
    external_port = NumericProperty(1)
    local_ip = StringProperty()
    external_local_ip = StringProperty()
    description = StringProperty()
    duration = NumericProperty(0)

    socket = None
    gateway = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup_socket()

    def xml_to_dict(self, root):
        #converts a minidom into something that can actually be understood...
        data = {}
        children = root.childNodes
        for node in children:
            if node.nodeType == xml_node.TEXT_NODE:
                continue
            tag_name = node.tagName
            if len(node.childNodes) == 1 and node.childNodes[0].nodeType == xml_node.TEXT_NODE:
                #this is actually a text node
                data[tag_name] = node.childNodes[0].data
            else:
                #this is a node group
                if tag_name not in data:
                    data[tag_name] = []
                data[tag_name].append(self.xml_to_dict(node))
        return data

    def parse_device_xml(self, xml_string):
        #converts an xml string into a somewhat usable format
        devices = []
        xml = parseString(xml_string)
        root = xml.getElementsByTagName('root')[0]
        device_nodes = root.getElementsByTagName('device')
        for device in device_nodes:
            try:
                device_xml = self.xml_to_dict(device)
                device_type = device_xml['deviceType']
                services = device_xml['serviceList'][0]['service']
                devices.append({'deviceType': device_type, 'services': services})
            except Exception as e:
                pass
        return devices

    def setup_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.local_ip, self.local_port))
        self.socket.settimeout(2)

    def send_ssdp_request(self):
        SSDP_ADDR = "239.255.255.250"
        SSDP_PORT = 1900
        SSDP_MX = 2
        SSDP_ST = "urn:schemas-upnp-org:device:InternetGatewayDevice:1"
        ssdpRequest = "M-SEARCH * HTTP/1.1\r\n" + \
                      "HOST: %s:%d\r\n" % (SSDP_ADDR, SSDP_PORT) + \
                      "MAN: \"ssdp:discover\"\r\n" + \
                      "MX: %d\r\n" % (SSDP_MX,) + \
                      "ST: %s\r\n" % (SSDP_ST,) + "\r\n"
    
        #Send request for network interface information
        dprint('Sending M-SEARCH request')
        self.socket.sendto(bytes(ssdpRequest, 'utf-8'), (SSDP_ADDR, SSDP_PORT))

    def parse_device_data(self, device_data):
        elements = device_data.split('\r\n')
        parsed_data = {}
        for element in elements:
            element_split = element.split(':', 1)
            if len(element_split) == 1:
                parsed_data[element_split[0].lower()] = ''
            elif len(element_split) == 2:
                parsed_data[element_split[0].lower()] = element_split[1].strip()
        return parsed_data

    def get_next_device(self):
        try:
            message, address = self.socket.recvfrom(4096)
            ip, port = address
            device_data = self.parse_device_data(message.decode('utf-8'))
            dprint('Found device: '+str(device_data))
            return device_data
        except Exception as e:
            dprint(e)
            return None

    def find_gateway(self):
        #Receive network interface data
        retries = 0
        while retries < 10:
            retries += 1
            #sends out a request to find the network gateway device
            self.send_ssdp_request()

            device_data = self.get_next_device()
            if device_data:
                if 'st' in device_data:
                    if 'InternetGatewayDevice' in device_data['st']:
                        if 'location' in device_data:
                            return device_data
            #if device_data is None:
            #    return None
        return None

    def xml_request(self, xml_content):
        xml_header = '<?xml version="1.0"?>'
        xml_header += '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
        xml_header += '<s:Body>'
        xml_footer = '</s:Body>'
        xml_footer += '</s:Envelope>'
        return xml_header+xml_content+xml_footer

    def xml_content_port_forward(self, local_port, external_port, protocol, local_ip, description, duration):
        xml_content = '<u:AddPortMapping xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1">'
        xml_content += '<NewExternalPort>'+str(external_port)+'</NewExternalPort>'
        xml_content += '<NewProtocol>'+protocol+'</NewProtocol>'
        xml_content += '<NewInternalPort>'+str(local_port)+'</NewInternalPort>'
        xml_content += '<NewInternalClient>'+local_ip+'</NewInternalClient>'
        xml_content += '<NewEnabled>1</NewEnabled>'
        xml_content += '<NewPortMappingDescription>'+description+'</NewPortMappingDescription>'
        xml_content += '<NewLeaseDuration>'+str(duration)+'</NewLeaseDuration>'
        xml_content += '</u:AddPortMapping>'
        return xml_content

    def xml_content_request_ip(self):
        xml_content = '<u:GetExternalIPAddress xmlns:u="urn:schemas-upnp-org:service:WANPPPConnection:1">'
        xml_content += '</u:GetExternalIPAddress>'
        return xml_content

    def find_port_forward_service(self, devices):
        service = None
        for device in devices:
            service = self.find_service(device, 'WANIPConnection')
            if service is None:
                service = self.find_service(device, 'WANPPPConnection')
            if service is not None:
                if 'controlURL' in service:
                    break
                else:
                    service = None
        return service

    def find_service(self, device, service_name):
        services = device['services']
        for service in services:
            if 'serviceType' in service:
                if service_name in service['serviceType']:
                    return service
        return None

    def port_forward(self):
        device_data = self.find_gateway()
        if device_data is None:
            return 'Unable to find internet gateway device'
        device_data_url = device_data['location']
        dprint('Port forward info link: ' + device_data_url)
        request = UrlRequest(device_data_url, timeout=self.timeout_time)
        request.wait()
        xml_string = request.result

        devices = self.parse_device_xml(xml_string)
        base_url = split_at_n(device_data_url, '/', 3)[0]
        port_forward_service = self.find_port_forward_service(devices)
        if port_forward_service is None:
            return 'No port forward service found'
        service_type = port_forward_service['serviceType']
        control_url = port_forward_service['controlURL']
        request_url = base_url+control_url

        #request external ip address
        try:
            external_ip_xml = self.xml_request(self.xml_content_request_ip())
            status, result = self.send_request(service_type, 'GetExternalIPAddress', request_url, external_ip_xml)
            ip = result.split('<NewExternalIPAddress>')[1].split('</NewExternalIPAddress>')[0]
            self.external_local_ip = ip
            dprint('Found external ip: '+ip)
        except Exception as e:
            dprint('Unable to request external ip: '+str(e))
            self.external_local_ip = ''
        
        port_forward_xml = self.xml_request(self.xml_content_port_forward(self.local_port, self.external_port, self.protocol, self.local_ip, self.description, self.duration))
        status, result = self.send_request(service_type, 'AddPortMapping', request_url, port_forward_xml)
        if status != 200:
            return 'Port forward request not accepted'
        dprint('Port Forward Accepted')
        return True

    def send_request(self, service_type, command, request_url, xml):
        headers = {'SOAPAction': '"'+service_type+'#'+command+'"', 'Content-Type': 'text/xml'}
        send_request = UrlRequest(request_url, req_body=xml, req_headers=headers, timeout=self.timeout_time)
        send_request.wait()
        result = send_request.result
        status = send_request.resp_status
        return status, result

    def port_forward_upnpy(self):
        #alternate method, uses the upnpy library to set up a port forward

        try:
            import upnpy
            up = upnpy.UPnP()
        except:
            dprint('upnpy library not found')
            return 'upnpy library not found'
        try:
            devices = up.discover(delay=2)
            router = up.get_igd()
        except Exception as e:
            dprint(e)
            return 'Unable To Find Router'
        services = router.get_services()
        service = None
        found_services = []
        for check_service in services:
            service_type = check_service.type_
            found_services.append(service_type)
            if service_type == 'WANPPPConnection':
                service = check_service
        if service is None:
            dprint('WANPPPConnection service not found in: ' + ','.join(found_services))
            return 'Port Forwarding Not Supported'
        try:
            ips = service.GetExternalIPAddress()
            external_local_ip = list(ips.values())[0]
            dprint('Found external ip: ' + external_local_ip)
        except:
            external_local_ip = ''
        self.external_local_ip = external_local_ip
        try:
            port = str(self.local_port)
            local_ip = self.local_ip
            status = service.AddPortMapping(NewRemoteHost='', NewExternalPort=port, NewProtocol='TCP', NewInternalPort=port, NewInternalClient=local_ip, NewEnabled=1, NewPortMappingDescription='Tetrivium Port Forward', NewLeaseDuration=0)
        except Exception as e:
            dprint('Unable to port forward: ' + str(e))
            return 'Unable To Port Forward'
        return True


class Connector(Widget):
    main_socket = ObjectProperty(allownone=True)  #Used for sending messages when trying to discover other devices
    secondary_socket = ObjectProperty(allownone=True)  #Used for receiving messages when trying to discover other devices
    server_socket = ObjectProperty(allownone=True)  #Used for the direct connection to other devices
    server_timeout = NumericProperty(0)
    max_timeout = NumericProperty(30)

    available_addresses = ListProperty()
    timeout_time = NumericProperty(10)

    update_thread = ObjectProperty(allownone=True)
    mode = StringProperty('scanning')
    cancel_thread = BooleanProperty(False)

    connect_action = StringProperty('Connect...')  #the action the user should take next
    connect_status = StringProperty('Ready To Connect')  #current status of the connector
    connection_retries = NumericProperty(0)
    max_connection_tries = NumericProperty(30)
    local_ip = StringProperty()
    external_local_ip = StringProperty()  #Local ip address used in port forwarding
    remote_ip = StringProperty()  #Ip that is currently being connected to
    connect_ip = StringProperty()  #Ip that wants to be connected to
    connect_connection = None
    broadcast_address = StringProperty('')
    app_name = StringProperty('')
    port = NumericProperty(0)
    delay_time = NumericProperty(1)
    forwarded_port = NumericProperty(0)

    ignore_connect = StringProperty()
    ignore_index = NumericProperty(0)
    connected = BooleanProperty(False)
    connecting = BooleanProperty(False)
    port_forwarding = BooleanProperty(False)
    thinking = BooleanProperty(False)
    connect_mode = StringProperty('local')  #local, port_forward, direct, bluetooth

    def __init__(self, **kwargs):
        self.register_event_type('on_ask_connect')
        self.register_event_type('on_connect')
        self.register_event_type('on_disconnect')
        self.register_event_type('on_receive')
        self.register_event_type('on_mode')
        self.register_event_type('on_connected')
        self.register_event_type('on_thinking')
        super().__init__(**kwargs)

    def start(self, *_):
        #Starts the connection update thread, cannot be called if thread is already running

        dprint("Start connect thread")
        if self.update_thread is not None:
            dprint("Connect thread already running")
            return
        #self.connect_status = 'Ready To Connect'
        self.cancel_thread = False
        self.thinking = False
        self.local_ip = self.get_ip()
        self.update_thread = threading.Thread(target=self.update_thread_function)
        self.update_thread.start()

    def stop(self):
        #Stops the connect update thread, blocks and waits for it to end

        dprint('Shutting down connect thread')
        while self.update_thread:
            self.cancel_thread = True
        self.cleanup()
        self.cleanup_server()
        self.mode = 'scanning'
        self.connect_status = 'Ready To Connect'

    def restart(self, new_mode='scanning'):
        #Cancel thread and wait for restart

        dprint("Restart connect thread")
        while self.update_thread:
            self.cancel_thread = True
        self.dispatch('on_mode')
        self.mode = new_mode
        self.start()

    def close_socket(self, sock):
        if sock is not None:
            try:
                sock.shutdown(2)
            except:
                pass
            sock.close()

    def cleanup(self):
        dprint("Reset sockets")
        self.close_socket(self.main_socket)
        self.main_socket = None
        self.close_socket(self.secondary_socket)
        self.secondary_socket = None

    def cleanup_server(self):
        dprint("Reset server socket")
        self.close_socket(self.server_socket)
        self.server_socket = None

    def connect_action_call(self):
        #Called externally when the user wants to activate the command indicated by the current 'connect_action'

        dprint("Connect action called")
        if self.mode == 'scanning':
            if self.connect_mode == 'local':
                self.restart('connecting')
            else:
                self.restart('connectto')
        elif self.mode in ['connecting', 'connected', 'connectto']:
            if self.mode == 'connected':
                self.connect_status = 'Disconnected'
                self.dispatch('on_disconnect')
            else:
                self.connect_status = 'Canceled Connection'
            self.restart('scanning')

    def init_port_forward(self):
        #Completes the port forwarding process by using the PortForwarder class

        self.thinking = True
        self.connect_status = 'Setting Up Port Forwarding...'
        self.connect_action = 'Please Wait...'
        dprint('Start port forward detection')
        port_forwarder = PortForwarder(local_port=self.port, external_port=self.port, local_ip=self.local_ip, description='Tetrivium Port Forward')
        port_forwarded = port_forwarder.port_forward()
        self.external_local_ip = port_forwarder.external_local_ip
        if port_forwarded is not True:
            dprint('Port forward failed: '+port_forwarded+', trying alternate method')
            port_forwarded = port_forwarder.port_forward_upnpy()
        self.thinking = False
        self.connect_action = 'Connect...'
        if port_forwarded is True:
            self.forwarded_port = self.port
            dprint('Port forward successful on port: '+str(self.port))
            self.connect_status = 'Port Forwarded: '+str(self.port)
            self.port_forwarding = True
            return True
        else:
            dprint('Unable to set up port forwarding')
            self.connect_status = port_forwarded
            return False

    def refuse_connect(self, block=False):
        #Called externally when the user declines a requested connection from another

        dprint("Connection refused locally")
        if block:
            self.ignore_connect = self.connect_ip
        if self.connect_mode != 'local':
            self.connect_connection = None
            self.restart()

    def connect_to(self):
        #Called externally when the user accepts a pending connection

        if self.connect_mode != 'local':
            connection = self.connect_connection
            dprint("Accept connection: " + str(connection))
            self.mode = 'connect'
        else:
            #sets mode = 'connectto', called when should connect to server
            dprint("Trying to connect...")
            self.remote_ip = self.connect_ip
            self.restart('connectto')

    def init_update_thread(self):
        #Resets all sockets and variables for whatever the current mode is.  This should be called whenever the mode changes.

        self.available_addresses = []
        self.connected = False
        self.connecting = False
        if self.mode == 'scanning':
            dprint("Init scanning mode")
            self.delay_time = 1
            self.connect_action = 'Connect...'
            if self.connect_mode == 'port_forward' and (not self.port_forwarding or self.port != self.forwarded_port):
                set_forwarding = self.init_port_forward()
                if not set_forwarding:
                    self.cancel_thread = True
                    return
            if self.connect_mode == 'local':
                #setup transmitter
                self.broadcast_address = self.local_ip.rsplit('.', 1)[0] + '.255'
                dprint("Broadcast address: "+self.broadcast_address)
                self.main_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
                self.main_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                self.main_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.main_socket.bind((self.local_ip, self.port))
                self.main_socket.settimeout(0)
    
                #setup receiver
                self.secondary_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
                self.secondary_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.secondary_socket.bind(("", self.port))
                self.secondary_socket.settimeout(.1)
            else:
                #setup receiver for direct connection (direct tcp connection this time)
                self.main_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
                self.main_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.main_socket.bind(("", self.port))
                self.main_socket.settimeout(.1)
                self.main_socket.listen(1)
        elif self.mode == 'connecting':
            #Start up the connection server, and send a message to the other computer asking them to connect
            dprint("Init connecting mode")
            self.delay_time = 1
            self.connecting = True
            self.connection_retries = 0
            self.connect_action = 'Cancel'
            self.connect_status = 'Waiting For Reply'

            #setup server
            self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.main_socket.bind(("", self.port))  #Bind to listen on all interfaces on this machine at self.port
            self.main_socket.settimeout(.1)
            self.main_socket.listen(1)

            #setup transmitter
            self.secondary_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)  #Opens a UDP socket
            self.secondary_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.secondary_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  #Prevents errors about the socket already being in use
            self.secondary_socket.settimeout(0)
            self.secondary_socket.bind((self.local_ip, self.port))
        elif self.mode == 'connectto':
            #This mode is activated when connecting to the other device that has already started its server through the 'connecting' mode
            dprint("Init connect-to mode")
            self.delay_time = 1
            self.connecting = True
            self.connect_action = 'Cancel'
            self.connect_status = 'Connecting...'
            self.server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)  #Opens a TCP socket
            #self.server_socket.bind((self.local_ip, self.port))
            if self.connect_mode != 'local':
                timeout = 5
            else:
                timeout = 10
            self.server_socket.settimeout(timeout)
        elif self.mode == 'connected':
            #This device is now connected to the other device, ready to send messages
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
        #Handles the continuous connection stuff such as sending/receiving messages and changing modes

        dprint("Starting update thread")
        self.init_update_thread()
        delay = 0
        while not self.cancel_thread:
            if self.mode == 'connect':
                self.dispatch('on_mode')
                self.cleanup()
                self.cleanup_server()
                if self.connect_connection:
                    self.mode = 'connected'
                    self.server_socket = self.connect_connection
                    self.connect_connection = None
                else:
                    self.mode = 'scanning'
                self.init_update_thread()
            delay += 1
            if delay >= 10:
                #Send messages, once a second
                status = self.update_send()
                if status is False:
                    #Something went wrong, soft restart stuff
                    self.cleanup()
                    self.cleanup_server()
                    if not self.cancel_thread:
                        self.init_update_thread()
                    continue
                delay = 0
            #Receive messages, once every 0.1 second
            status = self.update_receive()
            if status is False:
                #Something went wrong, soft restart stuff
                self.cleanup()
                self.cleanup_server()
                if not self.cancel_thread:
                    self.init_update_thread()
                continue
            self.server_timeout += 0.1
        dprint("Ending update thread")
        self.cleanup()
        self.cleanup_server()
        self.update_thread = None

    def update_send(self):
        #Sends regular connection request or keepalive messages to the other
        #May change self.mode
        #Returns true or false depending on connected status

        mode = self.mode
        if mode == 'scanning':
            #connection scanner and transmitter
            if self.connect_mode == 'local':
                if self.main_socket is None:
                    return False
                #send message
                plain_message = self.app_name+' Looking for multiplayer from:'+self.local_ip
                send_message = str.encode(plain_message)
                dprint("Send message: "+plain_message)
                self.main_socket.sendto(send_message, (self.broadcast_address, self.port))
            else:
                #external connection mode, dont do anything
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
            if self.connect_mode != 'local':
                self.broadcast_address = self.remote_ip
            try:
                self.secondary_socket.sendto(send_message, (self.broadcast_address, self.port))
            except Exception as e:
                return self.fail_connect(str(e))
        elif mode == 'connectto':
            try:
                self.connect_connection = self.server_socket
                self.server_socket = None
                self.connect_connection.connect((self.remote_ip, self.port))
                dprint("Connected to: "+str(self.remote_ip)+' on port: '+str(self.port))
                self.mode = 'connect'
                return False
            except Exception as e:
                if str(e) == 'timed out' and self.connect_mode != 'local':
                    self.connect_connection.close()
                    self.connect_connection = None
                    return False
                else:
                    dprint("Failed to connect")
                    self.connect_status = 'Failed To Connect!'
                    self.mode = 'scanning'
                    return False
        elif mode == 'connected':
            #send keepalive message
            self.send('0')
        return True

    def fail_connect(self, message, status=None):
        #Helper function for a disconnect

        dprint(message)
        if status is None:
            status = message
        self.connect_status = status
        self.dispatch('on_mode')
        self.mode = 'scanning'
        return False

    def update_receive(self):
        #Checks for messages or a connection from the other, depending on self.mode
        #May change mode depending on the message
        #Returns True or False

        mode = self.mode
        if mode == 'scanning':
            if self.connect_mode != 'local':
                #Wait for a connection
                try:
                    connection, client_address = self.main_socket.accept()
                    dprint('Received connection from: '+str(client_address))
                    ip, port = client_address
                    self.connect_ip = ip
                    self.connect_connection = connection
                    self.dispatch('on_ask_connect')
                except Exception as e:
                    if str(e) != 'timed out':
                        return self.fail_connect(str(e), status='Failed To Connect')
                    pass
            else:
                #check for messages
                try:
                    message, address = self.secondary_socket.recvfrom(4096)
                    ip, port = address
                    message = message.decode("utf-8")
                    if message.startswith(self.app_name+' Starting server for:'+self.local_ip):
                        dprint("Game start request received from: ("+ip+":"+str(port)+") : "+message)
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
                    else:
                        if ip != self.local_ip:
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
                except Exception as e:
                    if str(e) != 'timed out':
                        dprint(e)
                        return False
                self.prune_availables()
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
                    self.connect_connection = connection
                    self.mode = 'connect'
                    return False
            except Exception as e:
                if str(e) != 'timed out':
                    return self.fail_connect(str(e), 'Failed To Connect')
                pass
        elif mode == 'connectto':
            pass
        elif mode == 'connected':
            try:
                message_data = self.server_socket.recv(4096)
                message_data = message_data.decode("utf-8")
            except Exception as e:
                message_data = None
                if str(e) != 'timed out':
                    self.dispatch('on_disconnect')
                    return self.fail_connect(str(e), 'Disconnected')

            if message_data:
                messages = message_data.split('|')
                for message in messages:
                    if message:
                        self.server_timeout = 0
                        if message != '0':
                            dprint("Message received: "+message)
                            self.dispatch('on_receive', message)
            if self.server_timeout > self.max_timeout:
                self.dispatch('on_disconnect')
                return self.fail_connect('Connection Timed Out')
        return True

    def send(self, message):
        #When connected, send a message to the other, returns True or False

        if self.mode == 'connected':
            try:
                encoded_message = str.encode(message+'|')
                status = self.server_socket.send(encoded_message)
                dprint("Send message: "+message+" ("+str(status)+")")
                return True
            except Exception as e:
                pass
        return False

    def get_ip(self):
        #Returns the current local ip address using a socket

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            #doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except:
            ip = '127.0.0.1'
        finally:
            s.shutdown(2)
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

    def on_thinking(self, *_):
        pass
