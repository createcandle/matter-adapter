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
import subprocess
#import datetime
#import requests  # noqa
#import threading
#import subprocess

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


import asyncio
import logging
import argparse
from os.path import abspath, dirname
from pathlib import Path
from sys import path

#import aiohttp
from aiorun import run
import coloredlogs

path.insert(1, dirname(dirname(abspath(__file__))))
#from matter_server.client.client import MatterClient  # noqa: E402
from matter_server.server.server import MatterServer  # noqa: E402

# DEV
from chip.clusters import Objects as clusters
from chip.clusters import ClusterCommand

# client
import threading
import websocket
import _thread

#import rel

import traceback


logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

DEFAULT_VENDOR_ID = 0xFFF1
DEFAULT_FABRIC_ID = 1
DEFAULT_PORT = 5580
DEFAULT_URL = f"http://127.0.0.1:{DEFAULT_PORT}/ws"
DEFAULT_STORAGE_PATH = '/home/pi/.webthings/data/matter-adapter/matter_server'#os.path.join(Path.home(), ".matter_server")

print("Path.home(): " + str(Path.home()))

logging.basicConfig(level=logging.DEBUG)
#logging.basicConfig(handlers=None, level="DEBUG")
#coloredlogs.install(level="DEBUG")


class MatterAdapter(Adapter):
    """Adapter for addon """

    def __init__(self, verbose=False):
        """
        Initialize the object.

        verbose -- whether or not to enable verbose logging
        """
        
        print("Starting adapter init")

        self.ready = False # set this to True once the init process is complete.
        self.addon_id = 'matter-adapter'
        
        
        self.name = self.__class__.__name__ # TODO: is this needed?
        Adapter.__init__(self, self.addon_id, self.addon_id, verbose=verbose)

        # set up some variables
        self.DEBUG = True

        self.should_save = False
        
        # There is a very useful variable called "user_profile" that has useful values from the controller.
        #print("self.user_profile: " + str(self.user_profile))
        
        self.running = True
        self.server = None
        #self.client = None
        #self.unsubscribe = None
        
        self.port = 5580
        self.message_counter = 0
        self.client_connected = 0
        
        self.discovered = []
        self.nodes = []
        
        self.certificates_updated = False
        self.last_certificates_download_time = 0
        
        self.busy_discovering = False
        self.pairing_failed = False
        
        
        pwd = run_command('pwd')
        print("\n\n\n\n\n\n\n\n\n\n\n\n\n" + str(pwd))
        
        
        
        
        # Hotspot
        self.use_hotspot = True
        self.hotspot_ssid = ""
        self.hotspot_password = ""
        
        
        # WiFi
        self.wifi_ssid = ""
        self.wifi_password = ""
        self.wifi_set = False
        
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
        
        # Create some path strings. These point to locations on the drive.
        self.addon_path = os.path.join(self.user_profile['addonsDir'], self.addon_id) # addonsDir points to the directory that holds all the addons (/home/pi/.webthings/addons).
        self.data_path = os.path.join(self.user_profile['dataDir'], self.addon_id)
        self.persistence_file_path = os.path.join(self.data_path, 'persistence.json') # dataDir points to the directory where the addons are allowed to store their data (/home/pi/.webthings/data)
        #self.certs_dir_path = os.path.join(self.data_path, 'paa-root-certs')
        pwd = run_command('pwd')
        pwd = pwd.rstrip()
        
        self.certs_dir_path = pwd + '/credentials/development/paa-root-certs'
        print("self.certs_dir_path: " + str(self.certs_dir_path))
        
        self.certs_downloader_path = os.path.join(self.addon_path, 'download_certificates.py')
        self.hotspot_addon_path = os.path.join(self.user_profile['addonsDir'], 'hotspot')
        self.hotspot_persistence_path = os.path.join(self.user_profile['dataDir'], 'hotspot', 'persistence.json')
        
        
        # Create the data directory if it doesn't exist yet
        if not os.path.isdir(self.data_path):
            print("making missing data directory")
            os.mkdir(self.data_path)
        
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


        
            
                

        # Now we check if all the values that should exist actually do
        
        if 'wifi_ssid' not in self.persistent_data:
            self.persistent_data['wifi_ssid'] = ""
        
        if 'wifi_password' not in self.persistent_data:
            self.persistent_data['wifi_password'] = ""

        if 'nodez' not in self.persistent_data:
            self.persistent_data['nodez'] = {}

        print("PERSISTENT DATA")
        #print(json.dumps(self.persistent_data, None,4))
        print(json.dumps(self.persistent_data))

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
            os.system('mkdir -p ' + self.certs_dir_path)

        # /data
        if not os.path.isdir("/data"):
            print("Error! Could not find /data, which the server will be looking for")

        
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
        self.server = MatterServer(
            self.data_path, DEFAULT_VENDOR_ID, DEFAULT_FABRIC_ID, int(self.port)
        )

        # run the server. This is blocking.
        run(self.run_matter(), shutdown_callback=self.handle_stop)
        
        
        #self.server.start()
        
        # How to shut down nicely?
        # https://pypi.org/project/aiorun/
        # loop = asyncio.get_event_loop()
        # loop.stop()
        
        
        
        
        
        
        
        
        #if self.unsubscribe != None:
        #    print("self.unsubscribe DIR: " + str(dir(self.unsubscribe)))
        
        
        #if self.client != None:
        #    print("\nself.client DIR: " + str(dir(self.client)))
        #    self.client.disconnect()
        
        if self.server != None:
            print("\nself.server DIR: " + str(dir(self.server)))
            self.server.stop()
        
        
        
        
        # Just in case any new values were created in the persistent data store, let's save it to disk
        #self.save_persistent_data()
        
        # The addon is now ready
        self.ready = True 
        if self.DEBUG:
            print("Matter adapter init complete")
        exit()



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
                    
        except Exception as ex:
            print("Error in add_from_config: " + str(ex))



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
            print("in client_thread. zzz to wait for matter server")
        
        try:
            time.sleep(3)
            if self.DEBUG:
                print("client thread: zzz done, starting client")
            #rel.set_sleep(0.1)
            #rel.set_turbo(0.0001)
        
            #url = f"http://127.0.0.1:{self.port}/ws"
            url = "ws://127.0.0.1:" + str(self.port) + "/ws"
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
            print(":::\n:::\n:::\nCLIENT THREAD: BEYOND RUN FOREVER")
            """
            
            """
        except Exception as ex:
            print("General error in client thread: " + str(ex))
        
        
    def on_message(self, ws, message="{}"):
        print("\n.\nclient: on_message: " + str(message) + "\n\n")
        try:
            
            # matter_server.common.models.message.SuccessResultMessage
            
            message = json.loads(message)
            #if self.DEBUG:
            #    print("parsed message: " + str(message))
            if '_type' in message:
                if message['_type'] == "matter_server.common.models.server_information.ServerInfo":
                    if self.DEBUG:
                        print("\n\nRECEIVED MATTER SERVER INFO\n\n")
                    self.client_connected = True
                    
                    
                    # Start listening
                    if self.DEBUG:
                        print("Sending start_listening command")
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
                        print("Sending start_listening command")
                    self.ws.send(
                            json.dumps({
                                "message_id": "diagnostics",
                                "command": "diagnostics"
                            })
                          )
                    
                    # Request Matter nodes list
                    if self.DEBUG:
                        print("Asking for nodes list")
                    self.get_nodes()
                    
                    
                
                # Handle success messages
                elif message['_type'].endswith("message.SuccessResultMessage"):
                    if self.DEBUG:
                        print("\n\nOK message.SuccessResultMessage\n\n")
                    
                    if message['message_id'] == 'start_listening':
                        if self.DEBUG:
                            print("OK LISTENING")
                    
                    elif message['message_id'] == 'set_wifi_credentials':
                        if self.DEBUG:
                            print("OK WIFI CREDENTIALS SET")
                    
                    elif message['message_id'] == 'discover' and 'result' in message.keys():
                        if self.DEBUG:
                            print("OK DISCOVER RESPONSE")
                        self.discovered = message['result']
                        self.busy_discovering = False
                
                    elif message['message_id'] == 'commission_with_code':
                        if self.DEBUG:
                            print("\n\nNew device paired succesfully\n\n")
                        self.send_pairing_prompt("New device paired succesfully")
                        self.get_nodes()
                    
                    elif message['message_id'] == 'node_added':
                        if self.DEBUG:
                            print("\n\nNew device paired succesfully\n\n")
                    
                    elif message['message_id'] == 'get_nodes':
                        if self.DEBUG:
                            print("\n\nGET NODES succesfull\n\n")
                        self.nodes = message['result']
                        self.parse_nodes()
                    
                
                
                # Handle event messages
                elif message['_type'].endswith("message.EventMessage"):
                
                    if 'event' in message.keys():
                        if message['event'] == 'node_added':
                            if self.DEBUG:
                                print("\nRECEIVED NODE ADDED MESSAGE\n")
                
                        
                        if message['event'] == 'attribute_updated':
                            if self.DEBUG:
                                print("\nINCOMING PROPERTY CHANGE\n")
                            self.route_property_change(message['data'])
                
                
                
                # Handle error messages
                elif message['_type'].endswith("message.ErrorResultMessage"):
                    if self.DEBUG:
                        print("\nRECEIVED ERROR MESSAGE\n")
                        
                    if message['message_id'] == 'commission_with_code':
                        if self.DEBUG:
                            print("commission_with_code failed")
                        self.pairing_failed = True
                        
                    
            else:
                print("Warning, there was no _type in the message")
        
                #self.should_save = True
        
        except Exception as ex:
            if self.DEBUG:
                print("client: error in on_message: " + str(ex))
        
        

    def on_error(self, ws, error):
        if self.DEBUG:
            print("\n.\nclient: on_error: " + str(error))

    def on_close(self, ws, close_status_code, close_msg):
        if self.DEBUG:
            print("\n.\nclient: on_close. Status code: " + str(close_status_code) +  ", message: "+ str(close_msg))

    def on_open(self, ws):
        if self.DEBUG:
            print("\n.\nclient: opened connection")
        #print("ws: " + str(ws))
        
        
    def get_nodes(self):
        try:
            if self.client_connected:
                
                if self.DEBUG:
                    print("start_pairing: Client is connected, so asking for latest node list")
                
                message = {
                        "message_id": "get_nodes",
                        "command": "get_nodes"
                      }
                json_message = json.dumps(message)
                self.ws.send(json_message)
            
                return True
                
        except Exception as ex:
            print("Error in start_pairing: " + str(ex))
        
        return False



    def discover(self):
        try:
            if self.client_connected:
                
                self.busy_discovering = True
                
                if self.DEBUG:
                    print("discover: Client is connected, so sending discover command to Matter server")
                
                
                message = {
                        "message_id": "discover",
                        "command": "discover"
                      }
                
                json_message = json.dumps(message)
                self.ws.send(json_message)
                
            
                return True
                
        except Exception as ex:
            print("Error in start_pairing: " + str(ex))
        
        return False



    # Download the latest certificates
    def download_certs(self):
        if self.DEBUG:
            print("in download_certs")
        if time.time() - 21600 > self.persistent_data['last_certificates_download_time']:
            if self.DEBUG:
                print("downloading latest certificates")
            self.certificates_updated = False
            certificates_download_command = "python3 " + str(self.certs_downloader_path) + " --use-main-net-http --paa-trust-store-path " + str(self.certs_dir_path)
            if self.DEBUG:
                print("certificates download command: " + str(certificates_download_command))
            download_certs_output = run_command(certificates_download_command,120)
            print("download_certs_output: " + str(download_certs_output))
            
            if len(download_certs_output) < 5:
                self.certificates_updated = True
                #self.last_certificates_download_time = time.time()
                self.persistent_data['last_certificates_download_time'] = int(time.time())
                self.should_save = True
                return True
            else:
                return False
        else:
            self.certificates_updated = True
            return True



    # Pass WiFi credentials to Matter
    def set_wifi_credentials(self):
        if self.DEBUG:
            print("in set_wifi_credentials. self.wifi_ssid: " + str(self.wifi_ssid))
            print("in set_wifi_credentials. self.wifi_password: " + str(self.wifi_password))
        try:
            if self.client_connected == False:
                if self.DEBUG:
                    print("Cannot set wifi credentials, client is not connected to Matter server")
                
            elif self.wifi_ssid != "" and self.wifi_password != "":
                    #if self.wifi_ssid != "" and self.wifi_password != "":
                    if self.DEBUG:
                        print("Sharing wifi credentials with Matter server")
                
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
                        print("\n.\n) ) )\n.\nsending wifi credentials: " + str(wifi_message))
                    json_wifi_message = json.dumps(wifi_message)
        
                    self.ws.send(json_wifi_message)
                    return True
                
            else:
                if self.DEBUG:
                    print("Cannot set wifi credentials, as there are no credentials to set yet")
        except Exception as ex:
            if self.DEBUG:
                print("Error in set wifi credentials: " + str(ex))
        
        return False


    def start_matter_pairing(self,pairing_type,code):
        if self.DEBUG:
            print("\n\n\n\nin start_matter_pairing. Pairing type: " + str(pairing_type) + ", Code: " + str(code))
        self.pairing_failed = False
        
        # Download the latest certificates if they haven't been updated in a while
        self.download_certs()
        
        
        
        try:
            if self.client_connected:
                if self.DEBUG:
                    print("start_pairing: Client is connected, so sending commissioning code to Matter server.")
        
                # Set the wifi credentials
                if self.set_wifi_credentials():
                    time.sleep(5)
        
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
            
        except Exception as ex:
            print("Error in start_pairing: " + str(ex))
        
        return False




    def clock(self):
        if self.DEBUG:
            print("in clock")
        while self.running:
            time.sleep(1)
            
            if self.should_save:
                if self.DEBUG:
                    print("Should save persistent was True. Saving data to persistent file.")
                self.should_save = False
                self.save_persistent_data()

    
    #def something_happened(self, message):
    #    print("\n\nBINGO\nin something_happened. Message: " + str(message))

    #def client_unsubscribe(self, message):
    #    print("\n\nBINGO\n client_unsubscribe happened. Message: " + str(message))
    

    async def run_matter(self):
        """Run the Matter server and client."""
        if self.DEBUG:
            print("\nin run_matter")
        
        # Start Matter Server
        await self.server.start()
        
        
        

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
            print("in parse_nodes")
        for node in self.nodes:
            try:
                #if self.DEBUG:
                #    print("parse nodes: number: " + str(node_number))
                #node = self.nodes[node_number]
                node_id = node['node_id']
                device_id = 'matter-' + str(node_id)
                if self.DEBUG:
                    print("device_id: " + str(device_id))
            
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
        
        
        #if self.client != None:
        #    self.client.stop()
            
        if self.server != None:
            self.server.stop()
        
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
        #if self.DEBUG:
        if self.DEBUG:
            print("goodbye")
        return



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
        except:
            if self.DEBUG:
                print("Could not remove thing from devices")




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


    
    # Loop over all the items in the list, which is stored inside the adapter instance.
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


def run_command(cmd, timeout_seconds=30):
    try:
        p = subprocess.run(cmd, timeout=timeout_seconds, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)

        if p.returncode == 0:
            return str(p.stdout)
        else:
            if p.stderr:
                return str(p.stderr)

    except Exception as e:
        print("Error running command: "  + str(e))
        return None