"""
Matter addon for Candle Controller.

    START_LISTENING = "start_listening"
    SERVER_DIAGNOSTICS = "diagnostics"
    SERVER_INFO = "server_info"
    GET_NODES = "get_nodes"
    GET_NODE = "get_node"
    COMMISSION_WITH_CODE = "commission_with_code"
    COMMISSION_ON_NETWORK = "commission_on_network"
    SET_WIFI_CREDENTIALS = "set_wifi_credentials"
    SET_THREAD_DATASET = "set_thread_dataset"
    OPEN_COMMISSIONING_WINDOW = "open_commissioning_window"
    DISCOVER = "discover"
    INTERVIEW_NODE = "interview_node"
    DEVICE_COMMAND = "device_command"
    REMOVE_NODE = "remove_node"

"""



import os
import sys
# This helps the addon find python libraries it comes with, which are stored in the "lib" folder. The "package.sh" file will download Python libraries that are mentioned in requirements.txt and place them there.
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')) 

import json
import time
#import requests
import subprocess
#import datetime
#import requests  # noqa
#import threading
import subprocess

# This loads the parts of the addon.
from gateway_addon import Database, Adapter, Device, Property
# Database - needed to read from the settings database. If your addon doesn't have any settings, then you don't need this.
from .matter_device import MatterDevice

try:
    from .matter_adapter_api_handler import *
except Exception as ex:
    print("Error, unable to load MatterAdapterApiHandler (which is used for UI extention): " + str(ex))


# Not sure what this is used for, but leave it in.
_TIMEOUT = 3

# Not sure what this is used for either, but leave it in.
_CONFIG_PATHS = [
    os.path.join(os.path.expanduser('~'), '.webthings', 'config'),
]

# Not sure what this is used for either, but leave it in.
if 'WEBTHINGS_HOME' in os.environ:
    _CONFIG_PATHS.insert(0, os.path.join(os.environ['WEBTHINGS_HOME'], 'config'))



import logging
import argparse
from os.path import abspath, dirname
from pathlib import Path
from sys import path

#import aiohttp
import asyncio
#from aiorun import run
import coloredlogs

path.insert(1, dirname(dirname(abspath(__file__))))
#from matter_server.client.client import MatterClient  # noqa: E402
#from matter_server.server.server import MatterServer  # noqa: E402

# DEV
from chip.clusters import Objects as clusters
#from chip.clusters import ClusterCommand

# client
import threading
import websocket
import _thread

from threading import Lock

#import rel

import traceback


logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

DEFAULT_VENDOR_ID = 0xFFF1
DEFAULT_FABRIC_ID = 1
DEFAULT_PORT = 5580
DEFAULT_URL = f"http://127.0.0.1:{DEFAULT_PORT}/ws"
DEFAULT_STORAGE_PATH = '/home/pi/.webthings/data/matter-adapter' #os.path.join(Path.home(), ".matter_server")

print("Path.home(): " + str(Path.home()))

logging.basicConfig(level=logging.DEBUG)
#logging.basicConfig(handlers=None, level="DEBUG")
#coloredlogs.install(level="DEBUG")

# matter BLE discriminator is maybe 3840
# https://github.com/project-chip/connectedhomeip/issues/26968


class MatterAdapter(Adapter):
    """Adapter for addon """

    def __init__(self, verbose=False):
        """
        Initialize the object.

        verbose -- whether or not to enable verbose logging
        """
        
        print("Starting Matter adapter init")

        self.ready = False # set this to True once the init process is complete.
        self.addon_id = 'matter-adapter'
        
        
        self.name = self.__class__.__name__ # TODO: is this needed?
        Adapter.__init__(self, self.addon_id, self.addon_id, verbose=verbose)

        # set up some variables
        self.DEBUG = True
        self.DEBUG2 = True
        
        self.should_save = False
        
        # There is a very useful variable called "user_profile" that has useful values from the controller.
        #print("self.user_profile: " + str(self.user_profile))
        
        self.running = True
        self.server = None
        self.server_process = None
        #self.client = None
        #self.unsubscribe = None
        
        self.port = 5580
        self.message_counter = 0
        self.client_connected = 0
        
        self.vendor_id = ""
        
        self.discovered = []
        self.nodes = []
        
        self.certificates_updated = False
        self.busy_updating_certificates = False
        self.last_certificates_download_time = 0
        self.time_between_certificate_downloads = 21600
        
        self.busy_discovering = False
        self.pairing_failed = False
        self.busy_pairing = False
        
        self.brightness_transition_time = 0
        
        self.share_node_code = "" # used with open window
        self.device_was_deleted = False # set to True is a device is deleted from the Matter fabric
        
        self.s_print_lock = Lock()
        
        
        # Hotspot
        self.use_hotspot = True
        self.hotspot_ssid = ""
        self.hotspot_password = ""
        
        
        # WiFi
        self.wifi_ssid = ""
        self.wifi_password = ""
        self.wifi_set = False
        
        # not recommended  https://github.com/home-assistant-libs/python-matter-server
        #os.system('sudo sysctl -w net.ipv6.conf.all.forwarding=1')
        #os.system('sudo sysctl -w net.ipv6.conf.wlan0.accept_ra=2')
        #os.system('sudo sysctl -w net.ipv6.conf.wlan0.accept_ra_rt_info_max_plen=64')
        
        # prefered for thread support:
        #os.system('sudo sysctl -w net.ipv6.conf.wlan0.accept_ra=1')
        #os.system('sudo sysctl -w net.ipv6.conf.wlan0.accept_ra_rt_info_max_plen=64')
        
        """
        #self.candle_wifi_ssid = ""
        #self.candle_wifi_password = ""
        potential_candle_wifi_ssid = ""
        potential_candle_wifi_ssid = run_command('sudo cat /etc/wpa_supplicant/wpa_supplicant.conf | grep ssid')
        print("potential_candle_wifi_ssid: " + str(potential_candle_wifi_ssid))
        
        # get Candle's current WiFi SSID
        count = 0
        for i in potential_candle_wifi_ssid:
            if i == '"':
                count = count + 1
        if count == 2:
            potential_candle_wifi_ssid = potential_candle_wifi_ssid.split('"')[1::2]
            if len(potential_candle_wifi_ssid) == 1:
                print("potential_candle_wifi_ssid after split: " + str(potential_candle_wifi_ssid))
                potential_candle_wifi_ssid = potential_candle_wifi_ssid[0]
                potential_candle_wifi_ssid = potential_candle_wifi_ssid.rstrip()
                if len(potential_candle_wifi_ssid) > 1:
                    self.candle_wifi_ssid = potential_candle_wifi_ssid
                
        # get Candle's current WiFi password
        potential_candle_wifi_password = run_command('sudo cat /etc/wpa_supplicant/wpa_supplicant.conf | grep psk')
        print("potential_candle_wifi_password: " + str(potential_candle_wifi_password))
        print("len(potential_candle_wifi_password): " + str(len(potential_candle_wifi_password)))
        if len(potential_candle_wifi_password) > 9:
            potential_candle_wifi_password = potential_candle_wifi_password.replace('psk=','')
            print("potential_candle_wifi_password: " + str(potential_candle_wifi_password))
            potential_candle_wifi_password = potential_candle_wifi_password.rstrip()
            self.candle_wifi_password = potential_candle_wifi_password
        
        print("Candle's WiFi SSID: " + str(self.candle_wifi_ssid))
        print("Candle's WiFi password: " + str(self.candle_wifi_password))
        """
        
        #print("user profile: " + str(self.user_profile))
        
        
        
        # Create some path strings. These point to locations on the drive.
        self.addon_path = os.path.join(self.user_profile['addonsDir'], self.addon_id) # addonsDir points to the directory that holds all the addons (/home/pi/.webthings/addons).
        self.lib_path = os.path.join(self.addon_path, 'lib')
        self.data_path = os.path.join(self.user_profile['dataDir'], self.addon_id)
        self.persistence_file_path = os.path.join(self.data_path, 'persistence.json') # dataDir points to the directory where the addons are allowed to store their data (/home/pi/.webthings/data)
        self.chip_factory_ini_file_path = os.path.join(self.user_profile['baseDir'],'hasdata','chip_factory.ini')
        #self.certs_dir_path = os.path.join(self.data_path, 'paa-root-certs')
        
        os.chdir(self.data_path)
        
        pwd = run_command('pwd')
        pwd = pwd.rstrip()
        #print("PWD:" + str(pwd))
        self.certs_dir_path = pwd + '/credentials/development/paa-root-certs'
        #print("self.certs_dir_path: " + str(self.certs_dir_path))
        
        self.certs_downloader_path = os.path.join(self.addon_path, 'download_certificates.py')
        self.hotspot_addon_path = os.path.join(self.user_profile['addonsDir'], 'hotspot')
        self.hotspot_persistence_path = os.path.join(self.user_profile['dataDir'], 'hotspot', 'persistence.json')
        
        
        # Create the data directory if it doesn't exist yet
        if not os.path.isdir(self.data_path):
            print("making missing data directory")
            os.system('mkdir -p ' + str(self.data_path))
        
        self.persistent_data = {}
        
        
        # Get persistent data
        try:
            with open(self.persistence_file_path) as f:
                self.persistent_data = json.load(f)
                if self.DEBUG:
                    print('self.persistent_data was loaded from file: ' + str(self.persistent_data))
                    
        except:
            if self.DEBUG:
                print("Could not load persistent data (if you just installed the add-on then this is normal)")


        # LOAD CONFIG
        try:
            self.add_from_config()
        except Exception as ex:
            print("Error loading config: " + str(ex))



        # Override vendor ID
        if len(self.vendor_id) > 2 and len(self.vendor_id) < 7:
            if os.path.exists(self.chip_factory_ini_file_path):
                if self.DEBUG:
                    print("replacing vendor-id in chip_factory.ini with: " + str(self.vendor_id))
                os.system("sed -i 's/.*vendor-id=*.*/vendor-id=" + str(self.vendor_id) + "/' chip_factory.ini")
                
        if os.path.exists(self.chip_factory_ini_file_path):
            if self.DEBUG:
                print("OK, CHIP FACTORY FILE EXISTS")
                

        # Now we check if all the values that should exist actually do
        
        if 'wifi_ssid' not in self.persistent_data:
            self.persistent_data['wifi_ssid'] = ""
        
        if 'wifi_password' not in self.persistent_data:
            self.persistent_data['wifi_password'] = ""

        if 'nodez' not in self.persistent_data:
            self.persistent_data['nodez'] = {}

        #print("PERSISTENT DATA")
        #print(json.dumps(self.persistent_data, None,4))
        #print(json.dumps(self.persistent_data))

        if self.persistent_data['wifi_ssid'] != "" and self.persistent_data['wifi_password'] != "":
            self.wifi_ssid = self.persistent_data['wifi_ssid']
            self.wifi_password = self.persistent_data['wifi_password']
            
        if 'last_certificates_download_time' not in self.persistent_data:
            self.persistent_data['last_certificates_download_time'] = 0
            

        # Allow the use_hotspot setting to override the wifi credentials
        # TODO: check if the hotspot addon is actually running?
        self.hotspot_addon_installed = False
        if os.path.isdir(self.hotspot_addon_path):
            self.hotspot_addon_installed = True
            
        if self.use_hotspot and self.hotspot_addon_installed:
            # Figure out the Hotspot addon's SSID and password
            self.load_hotspot_config()
            
            if self.hotspot_ssid != "" and self.hotspot_password != "":
                self.wifi_ssid = self.hotspot_ssid
                self.wifi_password = self.hotspot_password



        # Start the API handler. This will allow the user interface to connect
        try:
            if self.DEBUG:
                print("starting api handler")
            self.api_handler = MatterAPIHandler(self, verbose=True)
            if self.DEBUG:
                print("Adapter: API handler initiated")
        except Exception as e:
            if self.DEBUG:
                print("Error, failed to start API handler: " + str(e))


        # Create the thing
        """
        try:
            # Create the device object
            matter_device = MatterDevice(self)
            
            # Tell the controller about the new device that was created. This will add the new device to self.devices too
            self.handle_device_added(matter_device)
            
            if self.DEBUG:
                print("matter_device created")
                
            # You can set the device to connected or disconnected. If it's in disconnected state the thing will visually be a bit more transparent.
            self.devices['matter-thing'].connected = True
            self.devices['matter-thing'].connected_notify(True)

        except Exception as ex:
            print("Could not create internet_radio_device: " + str(ex))
        """
        
        
        # Make sure storage path exists
        if not os.path.isdir(self.data_path):
            print("creating matter_server storage path: " + str(self.data_path))
            os.mkdir(self.data_path)
            
        if not os.path.isdir(self.certs_dir_path):
            print("making certificates directory")
            os.system('mkdir -p ' + self.certs_dir_path)

        # /data
        if not os.path.isdir("/data"):
            print("Error! Could not find /data, which the server will be looking for")
            time.sleep(30)
            exit()
        
        # Download the latest certificates
        self.download_certs()
        
        # Start client thread
        if self.DEBUG:
            print("Init: starting the client thread")
        try:
            self.t = threading.Thread(target=self.client_thread)
            self.t.daemon = True
            self.t.start()
        except Exception as ex:
            if self.DEBUG:
                print("Error starting the client thread: " + str(ex))
                print(traceback.format_exc())
        
        # Start clock thread
        if self.DEBUG:
            print("Init: starting the clock thread")
        try:
            self.ct = threading.Thread(target=self.clock)
            self.ct.daemon = True
            self.ct.start()
        except Exception as ex:
            if self.DEBUG:
                print("Error starting the clock thread: " + str(ex))
        
        

        # Init matter server
        #self.server = MatterServer(
        #    self.data_path, DEFAULT_VENDOR_ID, DEFAULT_FABRIC_ID, int(self.port)
        #)

        
        
        pwd = run_command('pwd')
        print("PWD after chdir: " + str(pwd))
        
        
        """
		while self.running:
            output = self.server_process.stdout.readline()
            print("self.server_process.poll(): " + str(self.server_process.poll()))
            #if output == '' and self.server_process.poll() is not None:
            #    break
            if output:
                print("STD OUT CAPTURED: " + str( output.strip() ))
            time.sleep(0.01)
		"""
        if self.DEBUG:
            print("run_process: beyond the while loop")
        #rc = self.server_process.poll()
        #if self.DEBUG:
        #    print("rc: " + str(rc))

        print("BEYOND SERVER START WITH SUBPROCESS")

        # Run the server. This is blocking.
        """
        run(self.run_matter(), shutdown_callback=self.handle_stop)
        
        
        if self.server != None:
            #print("\nself.server DIR: " + str(dir(self.server)))
            self.server.stop()
        
        # Just in case any new values were created in the persistent data store, let's save it to disk
        #self.save_persistent_data()
        
        # The addon is now ready
        
        if self.DEBUG:
            print("Matter adapter init end. Calling exit.")
        time.sleep(5)
        os.system("pkill -f 'python3 /home/pi/.webthings/addons/matter-adapter/main.py' --signal SIGKILL")
        exit()
        """


    def s_print(self, *a, **b):
        """Thread safe print function"""
        with self.s_print_lock:
            print(*a, **b)
        
    def add_from_config(self):
        """ This retrieves the addon settings from the controller """
        print("in add_from_config")
        try:
            database = Database(self.addon_id)
            if not database.open():
                print("Error. Could not open settings database")
                return

            config = database.load_config()
            database.close()

        except:
            print("Error. Failed to open settings database. Closing proxy.")
            self.close_proxy() # this will purposefully "crash" the addon. It will then we restarted in two seconds, in the hope that the database is no longer locked by then
            return
            
        try:
            if not config:
                print("Warning, no config.")
                return

            # Let's start by setting the user's preference about debugging, so we can use that preference to output extra debugging information
            if 'Debugging' in config:
                self.DEBUG = bool(config['Debugging'])
                if self.DEBUG:
                    print("Debugging enabled")

            if self.DEBUG:
                print(str(config)) # Print the entire config data

            if "Use Hotspot addon as WiFi network for devices" in config:
                self.use_hotspot = bool(config["Use Hotspot addon as WiFi network for devices"])
                if self.DEBUG:
                    print("Use hotspot preference was in settings: " + str(self.use_hotspot))
                    
            if "Vendor ID" in config:
                if len(config["Vendor ID"]) > 2:
                    self.vendor_id = str(config["Vendor ID"])
                    if self.DEBUG:
                        print("Vendor ID override was in settings: " + str(self.vendor_id))
                    
            if 'Brightness transition duration' in config:
                self.brightness_transition_time = int(config["Brightness transition duration"])
                if self.DEBUG:
                    print("Brightness transition preference was in settings: " + str(self.brightness_transition_time))
                    
        except Exception as ex:
            print("Error in add_from_config: " + str(ex))


    """
    def run_process(self,command):
        process = subprocess.Popen(command.split(command), stdout=subprocess.PIPE)
        while self.running:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print("STD OUT CAPTURED: " + str( output.strip() ))
        if self.DEBUG:
            print("run_process: beyond the while loop")
        rc = process.poll()
        return rc
    """


    # Check the Hotspot addon's settings for the SSID and Password
    def load_hotspot_config(self):
        """ This retrieves the HOTSPOT addon settings from the controller """
        if self.DEBUG:
            print("load_hotspot_config")
        try:
            database = Database('hotspot')
            if not database.open():
                print("Error. Could not open hotspot settings database")
                return False

            config = database.load_config()
            database.close()

        except:
            print("Error. Failed to open Hotspot settings database.")
            return False
            
        try:
            if not config:
                print("Warning, no hotspot config.")
                return False

            # Hotspot name
            try:
                if 'Hotspot name' in config:
                    if self.DEBUG:
                        print("-Hotspot name is present in the config data.")
                    self.hotspot_ssid = str(config['Hotspot name'])
            except Exception as ex:
                print("Error loading hotspot name from config: " + str(ex))
        
            # Hotspot password
            try:
                if 'Hotspot password' in config:
                    if self.DEBUG:
                        print("-Hotspot password is present in the config data.")
                    self.hotspot_password = str(config['Hotspot password'])
            except Exception as ex:
                print("Error loading hotspot password from config: " + str(ex))
        
        except Exception as ex:
            print("Error in load_hotspot_config: " + str(ex))




    def client_thread(self):
        if self.DEBUG:
            self.s_print("in client_thread. zzz to wait for matter server")
        
        try:
            time.sleep(4)
            if self.DEBUG:
                self.s_print("client thread: zzz done, starting client")
            #rel.set_sleep(0.1)
            #rel.set_turbo(0.0001)
        
            #url = f"http://127.0.0.1:{self.port}/ws"
            url = "ws://127.0.0.1:" + str(self.port) + "/ws"
            if self.DEBUG:
                print("attempting to open websocked connection to matter server. URL: " + str(url))
                
            websocket.enableTrace(False)
            self.ws = websocket.WebSocketApp(url, #"wss://127.0.0.1",
                                      on_open=self.on_open,
                                      on_message=self.on_message,
                                      on_error=self.on_error,
                                      on_close=self.on_close)

            self.ws.run_forever(reconnect=5)
            #ws.run_forever(dispatcher=rel, reconnect=5)  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
            #rel.signal(2, rel.abort)  # Keyboard Interrupt
            #rel.dispatch()
            self.s_print(":::\n:::\n:::\nCLIENT THREAD: BEYOND RUN FOREVER")
            """
            
            """
        except Exception as ex:
            print("General error in client thread: " + str(ex))
        
        
        
    def on_message(self, ws, message="{}"):
        if self.DEBUG:
            self.s_print("\n.\nclient: in on_message.  Message: " + str(message)[:100] + "...etc" + "\n\n")
        try:
            
            # matter_server.common.models.message.SuccessResultMessage
            
            message = json.loads(message)
            #if self.DEBUG:
            #    print("parsed message: " + str(message))
            if '_type' in message:
                if message['_type'] == "matter_server.common.models.server_information.ServerInfo":
                    if self.DEBUG:
                        self.s_print("\n\nRECEIVED MATTER SERVER INFO\n\n")
                    self.client_connected = True
                    
                    # Start listening
                    if self.DEBUG:
                        self.s_print("Sending start_listening command")
                    self.ws.send(
                            json.dumps({
                                "message_id": "start_listening",
                                "command": "start_listening"
                            })
                          )
                          
                    # Set the wifi credentials
                    self.set_wifi_credentials()
                    
                    # Get diagnostic data
                    if self.DEBUG:
                        self.s_print("Sending start_listening command")
                    self.ws.send(
                            json.dumps({
                                "message_id": "diagnostics",
                                "command": "diagnostics"
                            })
                          )
                    
                    # Request Matter nodes list
                    if self.DEBUG:
                        self.s_print("Asking for nodes list")
                    self.get_nodes()
                    
                
                # Handle success messages
                elif message['_type'].endswith("message.SuccessResultMessage"):
                    if self.DEBUG:
                        self.s_print("\n\nOK message.SuccessResultMessage\n\n")
                    
                    if message['message_id'] == 'start_listening':
                        if self.DEBUG:
                            self.s_print("OK LISTENING")
                    
                    elif message['message_id'] == 'set_wifi_credentials':
                        if self.DEBUG:
                            self.s_print("OK WIFI CREDENTIALS SET")
                    
                    elif message['message_id'] == 'discover' and 'result' in message.keys():
                        if self.DEBUG:
                            self.s_print("OK DISCOVER RESPONSE")
                        self.discovered = message['result']
                        self.busy_discovering = False
                
                    elif message['message_id'] == 'commission_with_code':
                        if self.DEBUG:
                            self.s_print("\n\nNew device paired succesfully\n\n")
                        self.send_pairing_prompt("New device paired succesfully")
                        self.get_nodes()
                    
                    elif message['message_id'] == 'node_added':
                        if self.DEBUG:
                            self.s_print("\n\nNew device paired succesfully\n\n")
                    
                    elif message['message_id'] == 'get_nodes':
                        if self.DEBUG:
                            self.s_print("\n\nGET NODES succesfull\n\n")
                        self.nodes = message['result']
                        self.parse_nodes()
                        self.ready = True # the addon should now have recreated the things
                        
                    elif message['message_id'].startswith('get_node_'):
                        if self.DEBUG:
                            self.s_print("\n\nGET NODE succesfull\n\n")
                        device_info = message['result']
                        if self.DEBUG:
                            self.s_print("DEVICE INFO: " + str(json.dumps(device_info)))
                            
                    elif message['message_id'] == 'remove_node':
                        if self.DEBUG:
                            self.s_print("\n\nremove_node was succesfull\n\n")
                        self.device_was_deleted = True
                        #self.nodes = message['result']
                        #self.parse_nodes()
                        self.get_nodes()
                        
                    elif message['message_id'] == 'open_commissioning_window':
                        if self.DEBUG:
                            self.s_print("\n\nopen_commissioning_window was succesfull\n\n")
                        try:
                            self.share_node_code = message['result']
                        except Exception as ex:
                            self.s_print("Error in open_commissioning_window -> getting pairing code")
                
                
                # Handle event messages
                elif message['_type'].endswith("message.EventMessage"):
                
                    if 'event' in message.keys():
                        if message['event'] == 'node_added':
                            if self.DEBUG:
                                self.s_print("\nRECEIVED NODE ADDED MESSAGE\n")
                
                        if message['event'] == 'attribute_updated':
                            if self.DEBUG:
                                self.s_print("\nADAPTER: INCOMING PROPERTY CHANGE\n")
                            self.route_property_change(message['data'])
                
                
                # Handle error messages
                elif message['_type'].endswith("message.ErrorResultMessage"):
                    if self.DEBUG:
                        self.s_print("\nRECEIVED ERROR MESSAGE\n")
                        
                    """
                        INVALID_COMMAND = 1
                        NOT_FOUND = 2
                        STACK_ERROR = 3
                        UNKNOWN_ERROR = 99
                    """
                        
                    if message['message_id'] == 'commission_with_code':
                        if self.DEBUG:
                            self.s_print("commission_with_code failed")
                        self.pairing_failed = True
                        
                    elif message['message_id'] == 'open_commissioning_window' or message['message_id'] =='commission_on_network':
                        if self.DEBUG:
                            self.s_print("open_commissioning_window failed")
                        self.share_node_code = ""
                        self.pairing_failed = True
                    else:
                        if self.DEBUG:
                            self.s_print("unhandled error message, message_id: " + str(message['message_id']))
                        
            else:
                if self.DEBUG:
                    self.s_print("Warning, there was no _type in the message")
        
        
            if 'error_code' in message:
                if self.DEBUG:
                    print("message contained an error code.")
                
                if 'details' in message:
                    if self.DEBUG:
                        print("Error details: " + str(message['details']))
        
                #self.should_save = True
        
        except Exception as ex:
            if self.DEBUG:
                self.s_print("client: error in on_message: " + str(ex))
        
        

    def on_error(self, ws, error):
        if self.DEBUG:
            self.s_print("\n.\nclient: on_error: " + str(error))

    def on_close(self, ws, close_status_code, close_msg):
        if self.DEBUG:
            self.s_print("\n.\nclient: on_close. Status code: " + str(close_status_code) +  ", message: "+ str(close_msg))

    def on_open(self, ws):
        if self.DEBUG:
            self.s_print("\n.\nclient: opened connection")
        #print("ws: " + str(ws))
        
        
    def get_nodes(self):
        try:
            if self.client_connected:
                
                if self.DEBUG:
                    self.s_print("get_nodes: Client is connected, so asking for latest node list")
                
                message = {
                        "message_id": "get_nodes",
                        "command": "get_nodes"
                      }
                json_message = json.dumps(message)
                self.ws.send(json_message)
                
                return True
            else:
                if self.DEBUG:
                    self.s_print("Error in get_nodes: client was not connected yet")
                
        except Exception as ex:
            print("Error in get_nodes: " + str(ex))
        
        return False


    def get_node(self, node_id):
        try:
            if self.client_connected:
                
                if self.DEBUG:
                    self.s_print("get-node: Client is connected, so asking for info on single node")
                
                message = {
                        "message_id": "get_node",
                        "command": "get_node",
                        "args": {
                            "node_id": node_id
                        }
                        
                      }
                json_message = json.dumps(message)
                self.ws.send(json_message)
            
                return True
                
        except Exception as ex:
            self.s_print("Error in get_node: " + str(ex))
        
        return False



    # open_commissioning_window
    def share_node(self, node_id):
        try:
            if self.client_connected:
                
                if self.DEBUG:
                    self.s_print("share-node: Client is connected, so asking to open commissioning window")
                
                message = {
                        "message_id": "open_commissioning_window",
                        "command": "open_commissioning_window",
                        "args": {
                            "node_id": node_id
                        }
                        
                      }
                json_message = json.dumps(message)
                self.ws.send(json_message)
            
                return True
                
        except Exception as ex:
            self.s_print("Error in share_node: " + str(ex))
        
        return False
        
        
        {
          "message_id": "open_commissioning_window",
          "command": "open_commissioning_window",
          "args": {
            "node_id": node_id
          }
        }
        
        """
        async def open_commissioning_window(
                self,
                node_id: int,
                timeout: int = 300,
                iteration: int = 1000,
                option: int = 0,
                discriminator: Optional[int] = None,
            ) -> int:
        
                #Open a commissioning window to commission a device present on this controller to another.
                #Returns code to use as discriminator.
                
                return cast(
                    int,
                    await self.send_command(
                        APICommand.OPEN_COMMISSIONING_WINDOW,
                        node_id=node_id,
                        timeout=timeout,
                        iteration=iteration,
                        option=option,
                        discriminator=discriminator,
                    ),
                )
        
        """
        


    # Not currently used
    def discover(self):
        try:
            if self.client_connected:
                
                self.busy_discovering = True
                
                if self.DEBUG:
                    self.s_print("discover: Client is connected, so sending discover command to Matter server")
                
                
                message = {
                        "message_id": "discover",
                        "command": "discover"
                      }
                
                json_message = json.dumps(message)
                self.ws.send(json_message)
                
            
                return True
                
        except Exception as ex:
            self.s_print("Error in discover: " + str(ex))
        
        return False



    # Download the latest certificates
    def download_certs(self):
        if self.DEBUG:
            self.s_print("in download_certs")
        if time.time() - self.time_between_certificate_downloads > self.persistent_data['last_certificates_download_time']:
            if self.DEBUG:
                self.s_print("downloading latest certificates")
            self.busy_updating_certificates = True
            self.certificates_updated = False
            certificates_download_command = "python3 " + str(self.certs_downloader_path) + " --use-main-net-http --paa-trust-store-path " + str(self.certs_dir_path)
            if self.DEBUG:
                self.s_print("certificates download command: " + str(certificates_download_command))
            download_certs_output = run_command(certificates_download_command,300)
            if self.DEBUG:
                self.s_print("download_certs_output: " + str(download_certs_output))
            
            self.busy_updating_certificates = False
            if download_certs_output != None:
                self.certificates_updated = True
            
                if len(str(download_certs_output)) > 5:
                    self.certificates_updated = True
                    #self.last_certificates_download_time = time.time()
                    self.persistent_data['last_certificates_download_time'] = int(time.time())
                    self.should_save = True
                    return True
                else:
                    if self.DEBUG:
                        self.s_print("Error, certificates didn't seem to download (output was None)")
                    return False
            
            else:
                if self.DEBUG:
                    self.s_print("Error, certificates didn't seem to download (download_certs_output was None)")
                return False
        else:
            self.certificates_updated = True
            return True



    # Pass WiFi credentials to Matter
    def set_wifi_credentials(self):
        if self.DEBUG:
            self.s_print("in set_wifi_credentials. self.wifi_ssid: " + str(self.wifi_ssid))
            self.s_print("in set_wifi_credentials. self.wifi_password: " + str(self.wifi_password))
        try:
            if self.client_connected == False:
                if self.DEBUG:
                    self.s_print("Cannot set wifi credentials, client is not connected to Matter server")
                
            elif self.wifi_ssid != "" and self.wifi_password != "":
                if self.DEBUG:
                    self.s_print("Sharing wifi credentials with Matter server")

                """
                if self.candle_wifi_ssid != "" and self.candle_wifi_password != "":
                    if self.DEBUG:
                        print("SHARING CANDLE'S WIFI CREDENTIALS")
                    wifi_message = {
                            "message_id": "set_wifi_credentials",
                            "command": "set_wifi_credentials",
                            "args": {
                                "ssid": str(self.candle_wifi_ssid),
                                "credentials": str(self.candle_wifi_password)
                            }
                          }
                else:

                if self.DEBUG:
                    print("SHARING WIFI CREDENTIALS")
                """
                wifi_message = {
                        "message_id": "set_wifi_credentials",
                        "command": "set_wifi_credentials",
                        "args": {
                            "ssid": str(self.wifi_ssid),
                            "credentials": str(self.wifi_password)
                        }
                      }

                # send wifi credentials
                if self.DEBUG:
                    self.s_print("\n.\n) ) )\n.\nsending wifi credentials: " + str(wifi_message))
                json_wifi_message = json.dumps(wifi_message)

                self.ws.send(json_wifi_message)
                return True
                
            else:
                if self.DEBUG:
                    self.s_print("Cannot set wifi credentials, as there are no credentials to set yet")
        except Exception as ex:
            if self.DEBUG:
                self.s_print("Error in set wifi credentials: " + str(ex))
        
        return False


    def start_matter_pairing(self,pairing_type,code):
        if self.DEBUG:
            self.s_print("\n\n\n\nin start_matter_pairing. Pairing type: " + str(pairing_type) + ", Code: " + str(code))
        self.pairing_failed = False
        # Download the latest certificates if they haven't been updated in a while
        #self.download_certs()
        
        
        try:
            if self.client_connected:
                if self.DEBUG:
                    print("start_pairing: Client is connected, so sending commissioning code to Matter server.")
        
                self.busy_pairing = True
        
        
        
                # Set the wifi credentials
                self.set_wifi_credentials()
                
                time.sleep(6) # TODO: Dodgy
        
        
                os.system('sudo btmgmt -i hci0 power off')
                os.system('sudo btmgmt -i hci0 bredr off')
                os.system('sudo btmgmt -i hci0 power on')
        
                
                
                # create pairing message
                message = None
                if pairing_type == 'commission_with_code':
                    message = {
                            "message_id": "commission_with_code",
                            "command": "commission_with_code",
                            "args": {
                                "code": code
                            }
                        }
            
                elif pairing_type == 'commission_on_network': #1234567
                    message = {
                            "message_id": "commission_on_network",
                            "command": "commission_on_network",
                            "args": {
                                "setup_pin_code": code 
                            }
                        }
                
                # Send pairing message
                if message != None:
                    json_message = json.dumps(message)
                    self.ws.send(json_message)
        
                    return True
            
            else:
                if self.DEBUG:
                     self.s_print("start_matter_pairing: error, client is not connected")
            
        except Exception as ex:
            self.s_print("Error in start_pairing: " + str(ex))
        
        return False




    def clock(self):
        if self.DEBUG:
            self.s_print("in clock")
        
        python3_path = run_command('readlink $(which python3)')
        python3_path = "/usr/bin/" + python3_path.rstrip()
        # /home/pi/.webthings/addons/matter-adapter/lib/
        matter_server_command = str(python3_path) + ' -m matter_server.server --storage-path ' + str(self.data_path)
        if self.vendor_id != "":
            matter_server_command = matter_server_command + " --vendorid " + str(self.vendor_id)
        
        
        if not os.path.exists(self.data_path):
            self.s_print("ERROR DATA PATH DOES NOT EXIST")
            
        if not os.path.exists(self.lib_path):
            self.s_print("ERROR LIB PATH DOES NOT EXIST")
            
        matter_server_command_shell = "PYTHONPATH=" + str(self.lib_path) + " " +  str(matter_server_command)
        
        self.s_print("")
        self.s_print("full matter server start command: " + str(matter_server_command_shell))
        self.s_print("")
        matter_server_command_array = matter_server_command.split()
        self.s_print("full matter server start command array: " + str(matter_server_command_array))
        #self.run_process(matter_server_command)
        
        
        my_env = os.environ.copy()
        my_env["PYTHONPATH"] = str(self.lib_path) + ":" # + my_env["PYTHONPATH"]
        self.s_print("my_env[PYTHONPATH]: " + str(my_env["PYTHONPATH"]))
        
        #'PYTHONPATH=/home/pi/.webthings/addons/matter-adapter/lib /usr/bin/python3.9 -m matter_server.server --storage-path /home/pi/.webthings/data/matter-adapter'
        
        #self.server_process = subprocess.Popen("/usr/bin/python3.9 bla.py", stdout=subprocess.PIPE, env=my_env, shell=True)
        #self.server_process = subprocess.Popen(matter_server_command_shell, stdout=subprocess.PIPE, env=my_env, shell=True)
        self.server_process = subprocess.Popen(matter_server_command_array, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=my_env)
        os.set_blocking(self.server_process.stdout.fileno(), False)
        os.set_blocking(self.server_process.stderr.fileno(), False)
        
        print("clock: self.running: " + str(self.running))
        dd = 1
        while self.running:
            time.sleep(0.01)
            #self.s_print("clock tick")
            # Check if there is output from the server process
            
            if self.DEBUG2:
                dd += 1
                if dd == 100:
                    dd = 0
                    self.s_print("tick tock")
            
            #if self.server_process != None:
            #if self.DEBUG:
            #    self.s_print("clock: server_process exists")
                #self.s_print("poll: " + str(self.server_process.poll()))

            try:
                for line in iter(self.server_process.stdout.readline,b''):
                    if self.DEBUG:
                        self.s_print("CAPTURED STDOUT: " + str(line.decode().rstrip()))
                
                for line in iter(self.server_process.stderr.readline,b''):
                    line = line.decode()
                    if self.DEBUG:
                        self.s_print("CAPTURED STDERR: " + str(line.rstrip()))
                    if 'Traceback' in line:
                        self.pairing_failed = True
                        self.busy_pairing = False
                        self.send_pairing_prompt("Error, Matter server crashed")
                    if 'over BLE failed' in line:
                        self.pairing_failed = True
                        self.busy_pairing = False
                        self.send_pairing_prompt("Bluetooth commissioning failed")
                    if 'error.NodeInterviewFailed' in line:
                        self.pairing_failed = True
                        self.busy_pairing = False
                        self.send_pairing_prompt("Interviewing Matter device failed")
                    if 'Commission with code failed for node' in line:
                        self.pairing_failed = True
                        self.busy_pairing = False
                        self.send_pairing_prompt("Interviewing Matter device just failed")
                    
                    
                    if 'address already in use' in line:
                        self.s_print("ERROR, THERE ALREADY IS A MATTER SERVER RUNNING")
                    #output = self.server_process.stdout.readline()
                    #error_line = self.server_process.stderr.readline()


                #for x in range(60):
                #    self.s_print(x)

                #if self.DEBUG:
                #    self.s_print("clock run_process: beyond the for loop")
            except Exception as ex:
                self.s_print("Error in clock try: " + str(ex))
            #else:
            #    self.s_print("self.server_process is None")
              
            # Save persistent data
            if self.should_save:
                if self.DEBUG:
                    self.s_print("Should save persistent was True. Saving data to persistent file.")
                self.should_save = False
                self.save_persistent_data()


    
    #def something_happened(self, message):
    #    print("\n\nBINGO\nin something_happened. Message: " + str(message))

    #def client_unsubscribe(self, message):
    #    print("\n\nBINGO\n client_unsubscribe happened. Message: " + str(message))
    

    async def run_matter(self):
        """Run the Matter server."""
        if self.DEBUG:
            print("\nin run_matter")
        
        # Start Matter Server
        await self.server.start()
        # print("------------------when do I run?--------------------------------------------------")
        # loop.stop()
        
        
        

    async def handle_stop(self, loop: asyncio.AbstractEventLoop):
        print("\nin handle_stop for server")
        """Handle server stop."""
        await self.server.stop()



    def route_property_change(self,data):
        if self.DEBUG:
            print("in route_property_change. Data: " + str(data))
        try:
            device_id = 'matter-' + str(data['node_id'])
            target_device = self.get_device(device_id)
            
            if target_device == None:
                if self.DEBUG:
                    print("route_property_change: missing device")
            else:
                property_id = 'property-' + str(data['attribute_id'])
                target_property = target_device.find_property(property_id)
        
                if target_property == None:
                    if self.DEBUG:
                        print("route_property_change: missing property")
                else:
                    value = data['value']
                    self.devices[device_id].properties[property_id].update( value )
            
                    
        except Exception as ex:
            print("Error in route_property_change: " + str(ex))

        """
        client: on_message: {
          "event": "attribute_updated",
          "data": {
            "node_id": 52,
            "endpoint": 1,
            "cluster_id": 6,
            "cluster_type": "chip.clusters.Objects.OnOff",
            "cluster_name": "OnOff",
            "attribute_id": 0,
            "attribute_type": "chip.clusters.Objects.OnOff.Attributes.OnOff",
            "attribute_name": "OnOff",
            "value": true
          },
          "_type": "matter_server.common.models.message.EventMessage"
        }
            
        """
        
    

    # Create new devices from Matter nodes
    def parse_nodes(self):
        if self.DEBUG:
            print("in parse_nodes. self.nodes length: " + str(len(self.nodes)))
        for node in self.nodes:
            try:
                #if self.DEBUG:
                #    print("parse nodes: number: " + str(node_number))
                #node = self.nodes[node_number]
                node_id = node['node_id']
                device_id = 'matter-' + str(node_id)
                if self.DEBUG:
                    print("device_id: " + str(device_id))
            
                # already handled by device
                #if not device_id in self.persistent_data['nodez']:
                #    self.persistent_data['nodez'][device_id] = {'device_id':device_id,'node_id':node_id,'attributes':{}}
                #    self.adapter.should_save = True
                    
            
                target_device = self.get_device(device_id)
                if target_device == None:
                    if self.DEBUG:
                        print("This device does not exist yet. It must be created.")
                    
                    new_device = MatterDevice(self, device_id, node)
                    self.handle_device_added(new_device)
                
                else:
                    if self.DEBUG:
                        print("target_device has already been created")
            except Exception as ex:
                if self.DEBUG:
                    print("error in parse_nodes: " + str(ex))
            
        """
        client: on_message: {
          "message_id": "get_nodes",
          "result": [
            {
              "node_id": 52,
              "date_commissioned": "2023-02-06T16:14:17.021028",
              "last_interview": "2023-02-06T16:14:17.021037",
              "interview_version": 1,
              "attributes": {
                "0/29/0": {
                  "node_id": 52,
                  "endpoint": 0,
                  "cluster_id": 29,
                  "cluster_type": "chip.clusters.Objects.Descriptor",
                  "cluster_name": "Descriptor",
                  "attribute_id": 0,
                  "attribute_type": "chip.clusters.Objects.Descriptor.Attributes.DeviceTypeList",
                  "attribute_name": "DeviceTypeList",
                  "value": [
                    {
                      "type": 22,
                      "revision": 1
                    }
                  ]
                },
                "0/29/1": {
                  "node_id": 52,
                  "endpoint": 0,
                  "cluster_id": 29,
                  "cluster_type": "chip.clusters.Objects.Descriptor",
                  "cluster_name": "Descriptor",
                  "attribute_id": 1,
                  "attribute_type": "chip.clusters.Objects.Descriptor.Attributes.ServerList",
                  "attribute_name": "ServerList",
                  "value": [
                    29,
                    31,
                    40,
                    42,
                    48,
                    49,
                    51,
                    60,
                    62,
                    63
                  ]
                },
        
        """
                    





    #
    #  CHANGING THE PROPERTIES
    #

    # It's nice to have a central location where a change in a property is managed.

    def set_state(self,state):
        try:
            if self.DEBUG:
                print("in set_state with state: " + str(state))
        
            # saves the new state in the persistent data file, so that the addon can restore the correct state if it restarts
            self.persistent_data['state'] = state
            self.save_persistent_data() 
        
            # A cool feature: you can create popups in the interface this way:
            if state == True:
                self.send_pairing_prompt("You switched on the thing") # please don't overdo it with the pairing prompts..
        
            # We tell the property to change its value. This is a very round-about way, and you could place all this logic inside the property instead. It's a matter of taste.
            try:
                self.devices['matter-thing'].properties['state'].update( state )
            except Exception as ex:
                print("error setting state on thing: " + str(ex))
        
        except Exception as ex:
            print("error in set_state: " + str(ex))
                
        

    #
    # The methods below are called by the controller
    #

    def start_pairing(self, timeout):
        """
        Start the pairing process. This starts when the user presses the + button on the things page.
        
        timeout -- Timeout in seconds at which to quit pairing
        """
        print("in start_pairing. Timeout: " + str(timeout))
        
        
    def cancel_pairing(self):
        """ Happens when the user cancels the pairing process."""
        # This happens when the user cancels the pairing process, or if it times out.
        print("in cancel_pairing")
        

    def unload(self):
        """ Shuts down the addon """
        if self.DEBUG:
            print("Stopping matter addon")
        
        self.running = False
        
        try:
            run_loop = asyncio.get_running_loop()
            run_loop.stop()
        except Exception as ex:
            print("Error getting asyncio loop: " + str(ex))
        
        #if self.client != None:
        #    self.client.stop()
            
        
        
        # loop = asyncio.get_event_loop()
        # loop.stop()
        
            
        #try:
        #    self.devices['matter-thing'].properties['status'].update( "Bye")
        #except Exception as ex:
        #    print("Error setting status on thing: " + str(ex))
        
        # Tell the controller to show the device as disconnected. This isn't really necessary, as the controller will do this automatically.
        #self.devices['matter-thing'].connected_notify(False)
        
        # A final chance to save the data.
        self.save_persistent_data()
        
        time.sleep(4)
        if self.server_process != None:
            #self.server.stop()
            time.sleep(1)
            os.system("pkill -f 'matter_server.server' --signal SIGKILL")
            os.system("pkill -f 'matter_server.server' --signal SIGKILL")
        
        # does it reach this?
        if self.DEBUG:
            print("goodbye")
        return True



    def remove_thing(self, device_id):
        """ Happens when the user deletes the thing."""
        if self.DEBUG:
            print("user deleted the thing")
        try:
            # We don't have to delete the thing in the addon, but we can.
            obj = self.get_device(device_id)
            self.handle_device_removed(obj) # Remove from device dictionary
            if self.DEBUG:
                print("User removed thing")
        except Exception as ex:
            if self.DEBUG:
                print("Could not remove thing from devices: " + str(ex))




    #
    # This saves the persistent_data dictionary to a file
    #
    
    def save_persistent_data(self):
        if self.DEBUG:
            print("Saving to persistence data store")

        try:
            if not os.path.isfile(self.persistence_file_path):
                open(self.persistence_file_path, 'a').close()
                if self.DEBUG:
                    print("Created an empty persistence file")
            else:
                if self.DEBUG:
                    print("Persistence file existed. Will try to save to it.")

            out_file = open(str(self.persistence_file_path), "w") 
            json.dump(self.persistent_data, out_file, indent = 4) 
            out_file.close()
            if self.DEBUG:
                print("persistent data saved to: " + str(self.persistence_file_path))
            return True

        except Exception as ex:
            if self.DEBUG:
                print("Error: could not store data in persistent store: " + str(ex) )
        
        return False


    
    def remove_node(self, node_id):
        if self.DEBUG:
            print("in remove_node. node_id: " + str(node_id))
        
        self.get_nodes()
        time.sleep(3)
        
        matter_id = 'matter-' + str(node_id)
        if matter_id in self.nodes:
            if self.DEBUG:
                print("remove_node: Node seems to exist, will delete it")
            message = {
                    "message_id": "remove_node",
                    "command": "remove_node",
                    "args": {
                        "node_id": node_id
                    }
                  }
            json_message = json.dumps(message)
            self.ws.send(json_message)
        
        else:
            if self.DEBUG:
                print("remove_node: node doesn't seem to exist (already deleted?). Skipping delete")
            self.device_was_deleted = True # pretend it was just deleted
            
        return True
        
              
        
        
    
    # Loop over all the items in the list, which is stored inside the adapter instance.
    """
    def delete_item(self,name):
        print("in delete_item. Name: " + str(name))
        for i in range(len(self.items_list)):
            if self.items_list[i]['name'] == name:
                # Found it
                del self.items_list[i]
                print("deleted item from list")
                return True
                
        # If we end up there, the name wasn't found in the list
        return False
    """
    

def run_command(cmd, timeout_seconds=30):
    try:
        p = subprocess.run(cmd, timeout=timeout_seconds, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)

        if p.returncode == 0:
            return str(p.stdout).rstrip()
        else:
            if p.stderr:
                return str(p.stderr).rstrip()

    except Exception as e:
        print("Error running command: "  + str(e))
        return None