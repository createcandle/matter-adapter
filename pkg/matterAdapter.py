"""

Matter addon for Candle Controller / Webthings Gateway.

This addon has the following hierarchy:

Adapter
- Device (1x)
- - Property (4x)
- API handler


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
from gateway_addon import Database, Adapter, Device, Property, APIHandler, APIResponse
# Database - needed to read from the settings database. If your addon doesn't have any settings, then you don't need this.

# Not sure what this is used for, but leave it in.
_TIMEOUT = 3

# Not sure what this is used for either, but leave it in.
_CONFIG_PATHS = [
    os.path.join(os.path.expanduser('~'), '.webthings', 'config'),
]

# Not sure what this is used for either, but leave it in.
if 'WEBTHINGS_HOME' in os.environ:
    _CONFIG_PATHS.insert(0, os.path.join(os.environ['WEBTHINGS_HOME'], 'config'))





import argparse
import asyncio
import logging
from os.path import abspath, dirname
from pathlib import Path
from sys import path

import aiohttp
from aiorun import run
import coloredlogs

path.insert(1, dirname(dirname(abspath(__file__))))
from matter_server.client.client import MatterClient  # noqa: E402
from matter_server.server.server import MatterServer  # noqa: E402

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

DEFAULT_VENDOR_ID = 0xFFF1
DEFAULT_FABRIC_ID = 1
DEFAULT_PORT = 5580
DEFAULT_URL = f"http://127.0.0.1:{DEFAULT_PORT}/ws"
DEFAULT_STORAGE_PATH = os.path.join(Path.home(), ".matter_server")






class MatterAdapter(Adapter):
    """Adapter for addon """

    def __init__(self, verbose=False):
        """
        Initialize the object.

        verbose -- whether or not to enable verbose logging
        """
        
        print("Starting adapter init")

        self.ready = False # set this to True once the init process is complete.
        self.addon_name = 'matter'
        
        
        self.name = self.__class__.__name__ # TODO: is this needed?
        Adapter.__init__(self, self.addon_name, self.addon_name, verbose=verbose)

        # set up some variables
        self.DEBUG = True
        self.a_number_setting = 0
        
        # this is a completely random set of items. It is sent to the user interface through the API handler, which till turn it into a list
        self.items_list = [
                        {'name':'Item 1', 'value':55},
                        {'name':'Item 2', 'value':25},
                        {'name':'Item 4', 'value':200},
                        {'name':'Item 3', 'value':88},
                    ]



        # There is a very useful variable called "user_profile" that has useful values from the controller.
        print("self.user_profile: " + str(self.user_profile))
        
        
        
        
        self.storage_path = "/home/pi/.webthings/data/matter-adapter"
        self.port = 5580
        
        
        # This addon has a "hidden parent" itself, the manager_proxy.
        #print("self.adapter.manager_proxy: " + str(self.adapter.manager_proxy))
        
        
        
        
        # Create some path strings. These point to locations on the drive.
        self.addon_path = os.path.join(self.user_profile['addonsDir'], self.addon_name) # addonsDir points to the directory that holds all the addons (/home/pi/.webthings/addons).
        self.data_path = os.path.join(self.user_profile['dataDir'], self.addon_name)
        self.persistence_file_path = os.path.join(self.data_path, 'persistence.json') # dataDir points to the directory where the addons are allowed to store their data (/home/pi/.webthings/data)
        
        # Create the data directory if it doesn't exist yet
        if not os.path.isdir(self.data_path):
            print("making missing data directory")
            os.mkdir(self.data_path)
        
        if sys.platform == 'darwin':
            print("running on a Mac")
			
			
        self.persistent_data = {}
            
        # 1. Get persistent data
        try:
            with open(self.persistence_file_path) as f:
                self.persistent_data = json.load(f)
                if self.DEBUG:
                    print('self.persistent_data was loaded from file: ' + str(self.persistent_data))
                    
        except:
            if self.DEBUG:
                print("Could not load persistent data (if you just installed the add-on then this is normal)")

        # 2. now that we have the persistent data (except on the first run), we allow the basic settings to override some of the values, if they are set.

        try:
            self.add_from_config()
        except Exception as ex:
            print("Error loading config: " + str(ex))

        # 3. Now we check if all the values that should exist actually do

        if 'state' not in self.persistent_data:
            self.persistent_data['state'] = False

        if 'slider' not in self.persistent_data:
            self.persistent_data['slider'] = 0
            
        if 'dropdown' not in self.persistent_data:
            self.persistent_data['dropdown'] = 'Auto'



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


        
        
        
        # make sure storage path exists
        if not os.path.isdir(self.storage_path):
            print("creating matter_server storage path: " + str(self.storage_path))
            os.mkdir(self.storage_path)

        if not os.path.isdir("/data"):
            print("creating /data path")
            os.mkdir("/data")
            #os.system('sudo mkdir /data; chown pi:pi /data')

        # Init matter server
        self.server = MatterServer(
            self.storage_path, DEFAULT_VENDOR_ID, DEFAULT_FABRIC_ID, int(self.port)
        )

            

        # run the server
        run(self.run_matter(), shutdown_callback=self.handle_stop)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        # Just in case any new values were created in the persistent data store, let's save if to disk
        self.save_persistent_data()
        
        # The addon is now ready
        self.ready = True 





    def add_from_config(self):
        """ This retrieves the addon settings from the controller """
        print("in add_from_config")
        try:
            database = Database(self.addon_name)
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
                
            if 'A boolean setting' in config:
                self.persistent_data['a_boolean_setting'] = bool(config['A boolean setting']) # sometime you may want the addon settings to override the persistent value
                if self.DEBUG:
                    print("A boolean setting preference was in config: " + str(self.a_boolean_setting))

            if 'A number setting' in config:
                #print("-Debugging was in config")
                self.a_number_setting = int(config['A number setting'])
                if self.DEBUG:
                    print("A number setting preference was in config: " + str(not self.a_number_setting))
            

        except Exception as ex:
            print("Error in add_from_config: " + str(ex))





    async def run_matter(self):
        """Run the Matter server and client."""
        print("in run_matter")
        
        # start Matter Server
        await self.server.start()

        # run the client
        url = f"http://127.0.0.1:{self.port}/ws"
        async with aiohttp.ClientSession() as session:
            print("client session started")
            async with MatterClient(url, session) as client:
                print("client started")
                self.client = client
                # start listening
                await self.client.start_listening()

    async def handle_stop(self, loop: asyncio.AbstractEventLoop):
        print("in handle_stop")
        """Handle server stop."""
        await self.server.stop()












    #
    #  CHANGING THE PROPERTIES
    #

    # It's nice to have a central location where a change in a property is managed.

    def set_state(self,state):
        try:
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
                
        
        
        
    def set_slider(self,value):
        try:
            print("in set_slider with value: " + str(value))
        
            # saves the new state in the persistent data file, so that the addon can restore the correct state if it restarts
            self.persistent_data['slider'] = value
            self.save_persistent_data() 
        
            try:
                self.devices['matter-thing'].properties['slider'].update( value )
            except Exception as ex:
                print("error setting slider value on thing: " + str(ex))
            
        except Exception as ex:
            print("error in set_slider: " + str(ex))
        
        
        
    def set_dropdown(self,value):
        try:
            print("in set_dropdown with value: " + str(value))
        
            # saves the new state in the persistent data file, so that the addon can restore the correct state if it restarts
            self.persistent_data['dropdown'] = value
            self.save_persistent_data() 
        
            # A cool feature: you can create popups in the interface this way:
            self.send_pairing_prompt("new dropdown value: " + str(value))
        
            try:
                self.devices['matter-thing'].properties['dropdown'].update( value )
            except Exception as ex:
                print("error setting dropdown value on thing: " + str(ex))
        
        except Exception as ex:
            print("error in set_dropdown: " + str(ex))




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
            print("Bye!")
            
        try:
            self.devices['matter-thing'].properties['status'].update( "Bye")
        except Exception as ex:
            print("Error setting status on thing: " + str(ex))
        
        # Tell the controller to show the device as disconnected. This isn't really necessary, as the controller will do this automatically.
        self.devices['matter-thing'].connected_notify(False)
        
        # A final chance to save the data.
        self.save_persistent_data()


    def remove_thing(self, device_id):
        """ Happens when the user deletes the thing."""
        print("user deleted the thing")
        try:
            # We don't have to delete the thing in the addon, but we can.
            obj = self.get_device(device_id)
            self.handle_device_removed(obj) # Remove from device dictionary
            if self.DEBUG:
                print("User removed thing")
        except:
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

            with open(self.persistence_file_path) as f:
                if self.DEBUG:
                    print("saving: " + str(self.persistent_data))
                try:
                    json.dump( self.persistent_data, open( self.persistence_file_path, 'w+' ) )
                except Exception as ex:
                    print("Error saving to persistence file: " + str(ex))
                return True
            #self.previous_persistent_data = self.persistent_data.copy()

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
        self.title = 'Matter addon 1 thing'
        self.description = 'Write a description here'
        
        # We give this device a "capability". This will cause it to have an icon that indicates what it can do. 
        # Capabilities are always a combination of giving a this a capability type, and giving at least one of its properties a capability type.
        # For example, here the device is a "multi level switch", which means it should have a boolean toggle property as well as a numeric value property
        # There are a lot of capabilities, read about them here: https://webthings.io/schemas/
        
        self._type = ['MultiLevelSwitch'] # a combination of a toggle switch and a numeric value

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
                            
                            
            # Creates a percentage slider
            self.properties["slider"] = MatterProperty( # (here "slider" is just a random name)
                            self,
                            "slider",
                            {
                                '@type': 'LevelProperty', # by giving the property this "capability", it will create a special icon indicating what it can do.
                                'title': "Slider example",
                                'type': 'integer',
                                'readOnly': False,
                                'minimum': 0,
                                'maximum': 100,
                                'unit': 'percent'
                            },
                            self.adapter.persistent_data['slider'])
                        
                        
            # This property shows a simple string in the interface. The user cannot change this string in the UI, it's "read-only" 
            self.properties["status"] = MatterProperty(
                            self,
                            "status",
                            {
                                'title': "Status",
                                'type': 'string',
                                'readOnly': True
                            },
                            "Hello world")


            self.properties["dropdown"] = MatterProperty(
                            self,
                            "dropdown",
                            {
                                'title': "Dropdown example",
                                'type': 'string',
                                'readOnly': False,
                                'enum': ['Auto', 'Option 1', 'Option 2'],
                            },
                            self.adapter.persistent_data['dropdown']) 



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






#
#  API HANDLER
#

# In this example the api-handler is created by the adapter. This is arbitary, you could have the adapter be the child of the api-handler if you prefered.

# Adapter  
# - Device  
# - - Property  
# - Api handler  <- you are here



class MatterAPIHandler(APIHandler):
    """API handler."""

    def __init__(self, adapter, verbose=False):
        """Initialize the object."""
        print("INSIDE API HANDLER INIT")
        
        self.adapter = adapter
        self.DEBUG = self.adapter.DEBUG


        # Intiate extension addon API handler
        try:
            
            APIHandler.__init__(self, self.adapter.addon_name) # gives the api handler the same id as the adapter
            self.manager_proxy.add_api_handler(self) # tell the controller that the api handler now exists
            
        except Exception as e:
            print("Error: failed to init API handler: " + str(e))
        
        
    #
    #  HANDLE REQUEST
    #

    def handle_request(self, request):
        """
        Handle a new API request for this handler.

        request -- APIRequest object
        """
        
        try:
        
            if request.method != 'POST':
                return APIResponse(status=404) # we only accept POST requests
            
            if request.path == '/ajax': # you could have all kinds of paths. In this example we only use this one, and use the 'action' variable to denote what we want to api handler to do

                try:
                    
                    
                    action = str(request.body['action']) 
                    
                    if self.DEBUG:
                        print("API handler is being called. Action: " + str(action))
                        print("request.body: " + str(request.body))
                    
                    
                    # INIT
                    if action == 'init':
                        if self.DEBUG:
                            print("API: in init")
                        
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({
                                      'a_number_setting':self.adapter.a_number_setting,
                                      'thing_state' : self.adapter.persistent_data['state'],
                                      'slider_value':self.adapter.persistent_data['slider'],
                                      'items_list':self.adapter.items_list,
                                      'debug': self.adapter.DEBUG
                                      }),
                        )
                        
                    
                    # ADD
                    # The add API call append a new item to the list directly
                    elif action == 'add':
                        if self.DEBUG:
                            print("API: in add")
                        state = False
                        
                        try:
                            name = str(request.body['name'])
                            value = str(request.body['value'])
                            
                            self.adapter.items_list.append( {'name':name, 'value':value} )
                            
                            state = True
                            
                        except Exception as ex:
                            if self.DEBUG:
                                print("Error adding: " + str(ex))
                        
                        
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state' : state}),
                        )
                    
                    
                    # DELETE
                    # In this example we call out to a separate delete method instead of handling the action directly
                    elif action == 'delete':
                        if self.DEBUG:
                            print("API: in delete")
                        
                        state = False
                        
                        try:
                            name = str(request.body['name'])
                            
                            state = self.delete_item(name) # This method returns True if deletion was succesful
                            
                        except Exception as ex:
                            if self.DEBUG:
                                print("Error deleting: " + str(ex))
                        
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state' : state}),
                        )
                    
                    
                    else:
                        print("Error, that action is not possible")
                        return APIResponse(
                            status=404
                        )
                        
                        
                    
                        
                        
                except Exception as ex:
                    if self.DEBUG:
                        print("Ajax error: " + str(ex))
                    return APIResponse(
                        status=500,
                        content_type='application/json',
                        content=json.dumps({"error":"Error in API handler"}),
                    )
                    
            else:
                if self.DEBUG:
                    print("invalid path: " + str(request.path))
                return APIResponse(status=404)
                
        except Exception as e:
            if self.DEBUG:
                print("Failed to handle UX extension API request: " + str(e))
            return APIResponse(
                status=500,
                content_type='application/json',
                content=json.dumps({"error":"General API error"}),
            )
        

        # That's a lot of "apiResponse", but we need to make sure that there is always a response sent to the UI


    
    # Loop over all the items in the list, which is stored inside the adapter instance.
    def delete_item(self,name):
        print("in delete_item. Name: " + str(name))
        for i in range(len(self.adapter.items_list)):
            if self.adapter.items_list[i]['name'] == name:
                # Found it
                del self.adapter.items_list[i]
                print("deleted item from list")
                return True
                
        # If we end up there, the name wasn't found in the list
        return False


