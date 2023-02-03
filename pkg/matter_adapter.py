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
#import datetime
#import requests  # noqa
#import threading
#import subprocess

# This loads the parts of the addon.
from gateway_addon import Database, Adapter, Device, Property
# Database - needed to read from the settings database. If your addon doesn't have any settings, then you don't need this.

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

import aiohttp
from aiorun import run
import coloredlogs

path.insert(1, dirname(dirname(abspath(__file__))))
#from matter_server.client.client import MatterClient  # noqa: E402
from matter_server.server.server import MatterServer  # noqa: E402



# client
import threading
import websocket
import _thread

#import rel


logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

DEFAULT_VENDOR_ID = 0xFFF1
DEFAULT_FABRIC_ID = 1
DEFAULT_PORT = 5580
DEFAULT_URL = f"http://127.0.0.1:{DEFAULT_PORT}/ws"
DEFAULT_STORAGE_PATH = '/home/pi/.webthings/data/matter-adapter/matter_server'#os.path.join(Path.home(), ".matter_server")

print("Path.home(): " + str(Path.home()))





class MatterAdapter(Adapter):
    """Adapter for addon """

    def __init__(self, verbose=False):
        """
        Initialize the object.

        verbose -- whether or not to enable verbose logging
        """
        
        print("Starting adapter init")

        self.ready = False # set this to True once the init process is complete.
        self.addon_id = 'matter'
        
        
        self.name = self.__class__.__name__ # TODO: is this needed?
        Adapter.__init__(self, self.addon_id, self.addon_id, verbose=verbose)

        # set up some variables
        self.DEBUG = True

        self.should_save_persistent = False
        
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
        
        self.busy_discovering = False
        
        self.pairing_failed = False
        
        # Hotspot
        self.use_hotspot = True
        self.hotspot_ssid = ""
        self.hotspot_password = ""
        self.wifi_ssid = ""
        self.wifi_password = ""
        
        # Create some path strings. These point to locations on the drive.
        self.addon_path = os.path.join(self.user_profile['addonsDir'], self.addon_id) # addonsDir points to the directory that holds all the addons (/home/pi/.webthings/addons).
        self.data_path = os.path.join(self.user_profile['dataDir'], self.addon_id)
        self.persistence_file_path = os.path.join(self.data_path, 'persistence.json') # dataDir points to the directory where the addons are allowed to store their data (/home/pi/.webthings/data)
        
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


        self.hotspot_addon_installed = False
        if os.path.isdir(self.hotspot_addon_path):
            self.hotspot_addon_installed = True
            
        if self.use_hotspot and self.hotspot_addon_installed:
            # Figure out the Hotspot addon's SSID and password
            self.load_hotspot_config()
            
            if self.hotspot_ssid != "" and self.hotspot_password != "":
                self.wifi_ssid = self.hotspot_ssid
                self.wifi_password = self.hotspot_password
            
                

        # Now we check if all the values that should exist actually do

        #if 'state' not in self.persistent_data:
        #    self.persistent_data['state'] = False
        

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

        if not os.path.isdir("/data"):
            print("Error, could not find /data, which the server will be looking for")

        
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
            print("in client_thread. zzz")
        
        try:
            time.sleep(3)
            if self.DEBUG:
                print("zzz done")
            #rel.set_sleep(0.1)
            #rel.set_turbo(0.0001)
        
            #url = f"http://127.0.0.1:{self.port}/ws"
            url = "ws://127.0.0.1:" + str(self.port) + "/ws"
            websocket.enableTrace(True)
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
        
        
    def on_message(self, ws, message):
        print("\n.\nclient: on_message: " + str(message) + "\n\n")
        try:
            
            message = json.loads(message)
            if self.DEBUG:
                print("parsed message: " + str(message))
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
                    
                    # Pass WiFi credentials to Matter
                    if self.wifi_ssid != "" and self.wifi_password != "":
                        if self.DEBUG:
                            print("Sharing wifi credentials with Matter server")
                        
                        wifi_message = {
                                "message_id": "set_wifi_credentials",
                                "command": "set_wifi_credentials",
                                "args": {
                                    "ssid": str(self.wifi_ssid),
                                    "credentials": str(self.wifi_password)
                                }
                              }
                        
                        json_wifi_message = json.dumps(wifi_message)
                
                        self.ws.send(json_wifi_message)
                    
                    
                    # Request Matter nodes list
                    self.get_nodes()
                    
                    
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
                    
                    
                elif message['_type'].endwith("message.ErrorResultMessage"):
                    if self.DEBUG:
                        print("\nRECEIVED ERROR MESSAGE\n")
                        
                    if message['message_id'] == 'commission_with_code':
                        if self.DEBUG:
                            print("commission_with_code failed")
                        self.pairing_failed = True
                        
                    
            else:
                print("Warning, there was no _type in the message")
        
                #self.should_save_persistent = True
        
        except Exception as ex:
            if self.DEBUG:
                print("client: error in on_message: " + str(ex))
        
        

    def on_error(self, ws, error):
        if self.DEBUG:
            print("\n.\nclient: on_error: " + str(message))

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



    def start_matter_pairing(self,pairing_type,code,device):
        if self.DEBUG:
            print("\n\nin start_matter_pairing. Pairing type: " + str(pairing_type)", Code: " + str(code) + ", device: " + str(device))
        self.pairing_failed = False
        
        try:
            if self.client_connected:
                if self.DEBUG:
                    print("start_pairing: Client is connected, so sending commissioning code to Matter server.")
            
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
            
            if self.should_save_persistent:
                if self.DEBUG:
                    print("Should save persistent was True. Saving data to persistent file.")
                self.should_save_persistent = False
                self.save_persistent_data()

    
    #def something_happened(self, message):
    #    print("\n\nBINGO\nin something_happened. Message: " + str(message))

    #def client_unsubscribe(self, message):
    #    print("\n\nBINGO\n client_unsubscribe happened. Message: " + str(message))
    

    async def run_matter(self):
        """Run the Matter server and client."""
        if self.DEBUG:
            print("\nin run_matter")
        
        # start Matter Server
        await self.server.start()
        
        """
        # run the client
        url = f"http://127.0.0.1:{self.port}/ws"
        async with aiohttp.ClientSession() as session:
            print("client session started")
            async with MatterClient(url, session) as client:
                print("client started")
                self.client = client
                
                await self.client.connect() # could give an error saying it's already connected
            
                # start listening
                await self.client.start_listening()
                
                self.unsubscribe = await self.client.subscribe(self.client_unsubscribe)
                
                set_wifi_result_code = await self.client.set_wifi_credentials('ssid_name','wifi_password')
                print("\n\nset_wifi_result_code: " + str(set_wifi_result_code))
                
                self.matter_nodes = await self.client.get_nodes()
                print("\n\nmatter nodes: " + str(self.matter_nodes))
                
                
        """
                

    async def handle_stop(self, loop: asyncio.AbstractEventLoop):
        print("\nin handle_stop for server")
        """Handle server stop."""
        await self.server.stop()












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
        """ Happens when the user addon / system is shut down."""
        if self.DEBUG:
            print("Stopping matter addon")
        
        
        #if self.client != None:
        #    self.client.stop()
            
        if self.server != None:
            self.server.stop()
        
            
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







#
# DEVICE
#

# This addon is very basic, in that it only creates a single thing.
# The device can be seen as a "child" of the adapter

# Adapter
# - Device  <- you are here
# - - Property  
# - Api handler


class MatterDevice(Device):
    """Internet Radio device type."""

    def __init__(self, adapter):
        """
        Initialize the object.
        adapter -- the Adapter managing this device
        """

        Device.__init__(self, adapter, 'matter')

        self._id = 'matter-thing' # TODO: probably only need the first of these
        self.id = 'matter-thing'
        self.adapter = adapter
        self.DEBUG = adapter.DEBUG

        self.name = 'thing1' # TODO: is this still used? hasn't this been replaced by title?
        self.title = 'Matter addon thing'
        self.description = 'Write a description here'
        
        # We give this device a "capability". This will cause it to have an icon that indicates what it can do. 
        # Capabilities are always a combination of giving a this a capability type, and giving at least one of its properties a capability type.
        # For example, here the device is a "multi level switch", which means it should have a boolean toggle property as well as a numeric value property
        # There are a lot of capabilities, read about them here: https://webthings.io/schemas/
        
        #self._type = ['MultiLevelSwitch'] # a combination of a toggle switch and a numeric value

        try:
            
            # Let's add four properties:
            
            # This create a toggle switch property
            self.properties["state"] = MatterProperty(
                            self,
                            "state",
                            {
                                '@type': 'OnOffProperty', # by giving the property this "capability", it will create a special icon indicating what it can do. Note that it's a string (while on the device it's an array).
                                'title': "State example",
                                'readOnly': False,
                                'type': 'boolean'
                            },
                            self.adapter.persistent_data['state']) # we give the new property the value that was remembered in the persistent data store
                            


        except Exception as ex:
            if self.DEBUG:
                print("error adding properties to thing: " + str(ex))

        if self.DEBUG:
            print("thing has been created.")


#
# PROPERTY
#
# The property can be seen as a "child" of a device

# Adapter
# - Device
# - - Property  <- you are here
# - Api handler

class MatterProperty(Property):

    def __init__(self, device, name, description, value):
        # This creates the initial property
        
        # properties have:
        # - a unique id
        # - a human-readable title
        # value. The current value of this property
        
        Property.__init__(self, device, name, description)
        
        self.device = device # a way to easily access the parent device, of which this property is a child.
        
        # you could go up a few levels to get values from the adapter:
        # print("debugging? " + str( self.device.adapter.DEBUG ))
        
        # TODO: set the ID properly?
        self.id = name
        self.name = name # TODO: is name still used?
        self.title = name # TODO: the title isn't really being set?
        self.description = description # a dictionary that holds the details about the property type
        self.value = value # the value of the property
        
        # Notifies the controller that this property has a (initial) value
        self.set_cached_value(value)
        self.device.notify_property_changed(self)
        
        if self.device.DEBUG:
            print("property: initiated: " + str(self.title) + ", with value: " + str(value))


    def set_value(self, value):
        # This gets called by the controller whenever the user changes the value inside the interface. For example if they press a button, or use a slider.
        print("property: set_value called for " + str(self.title))
        print("property: set value to: " + str(value))
        
        try:
            
            # Depending on which property this is, you could have it do something. That method could be anywhere, but in general it's clean to keep the methods at a higher level (the adapter)
            # This means that in this example the route the data takes is as follows: 
            # 1. User changes the property in the interface
            # 2. Controller calls set_value on property
            # 3. In this example the property routes the intended value to a method on the adapter (e.g. set_state). See below.
            # 4. The method on the adapter then does whatever it needs to do, and finally tells the property's update method so that the new value is updated, and the controller is sent a return message that the value has indeed been changed.
            
            #  If you wanted to you could simplify this by calling update directly. E.g.:
            # self.update(value)
            
            if self.id == 'state':
                self.device.adapter.set_state(bool(value))
        
            elif self.id == 'slider':
                self.device.adapter.set_slider(int(value))
        
            elif self.id == 'dropdown':
                self.device.adapter.set_dropdown(str(value))
        
            # The controller is waiting 60 seconds for a response from the addon that the new value is indeed set. If "notify_property_changed" isn't used before then, the controller will revert the value in the interface back to what it was.
            
        
        except Exception as ex:
            print("property: set_value error: " + str(ex))


    def update(self, value):
        # This is a quick way to set the value of this property. It checks that the value is indeed new, and then notifies the controller that the value was changed.
        
        print("property: update. value: " + str(value))
         
        if value != self.value:
            self.value = value
            self.set_cached_value(value)
            self.device.notify_property_changed(self)



    
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


