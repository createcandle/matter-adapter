import os
import sys
# This helps the addon find python libraries it comes with, which are stored in the "lib" folder. The "package.sh" file will download Python libraries that are mentioned in requirements.txt and place them there.
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')) 

import json
#import asyncio
#from aiorun import run
from gateway_addon import Property
from chip.clusters import Objects as clusters # also loaded as dependency from matter_server, see below
#from chip.clusters import ClusterCommand

#from dataclasses import dataclass, asdict, field, InitVar
#from dataclasses import MISSING, asdict, fields, is_dataclass

try:
    from matter_server.common.helpers.util import dataclass_from_dict,dataclass_to_dict
    #from matter_server.common.models.api_command import APICommand
    from matter_server.common.models import APICommand
    #from matter_server.common.models.message import CommandMessage
    from matter_server.common.models import CommandMessage
    #from matter_server.common.json_utils import CHIPJSONDecoder, CHIPJSONEncoder
    #from matter_server.vendor.chip.clusters import Objects as clusters
except Exception as ex:
    print("Error loading matter_server parts: " + str(ex))


from .matter_util import *

    
#
# PROPERTY
#

class MatterProperty(Property):

    def __init__(self, device, property_id, description, value, details=None): # description here means the dictionary that described the property, not a text description.
        # This creates the initial property
        #print("Property: property_id: " + str(property_id))
        
        if not isinstance(property_id,str):
            if device.DEBUG:
                print("\nERROR, invalid property_id provided")
            return
            
        if not isinstance(description,dict):
            if device.DEBUG:
                print("\nERROR, invalid description dict provided")
            return
            
        if not isinstance(details,dict):
            if device.DEBUG:
                print("\nERROR, no details dict provided")
            return
            
        Property.__init__(self, device, property_id, description)
        
        self.DEBUG = device.DEBUG
        
        if self.DEBUG:
            print("\nIN PROPERTY INIT.  property_id: ", property_id)
        
        self.device = device
        
        self.id = property_id
        self._id = property_id
        self.name = property_id
        
        self.description = description # a dictionary that holds the details about the property type
        self.details = details
        
        self.value = value
        
        if 'title' in description:
            if self.DEBUG:
                print("property: setting title to: ", str(description['title']))
            self.title = str(description['title'])
        elif 'title' in details:
            if self.DEBUG:
                print("property: setting title to: ", str(details['title']))
            self.title = str(details['title'])
        else:
            if self.DEBUG:
                print("\nERROR: property: missing title in description and self.details of property: ", property_id)
            self.title = property_id
        
        if not 'short_type' in self.details and property_id != 'data_mute':
            if self.DEBUG:
                print("\nERROR missing short_type in self.details of property: ", property_id)
            return
        
        self.set_cached_value(value)
        self.device.notify_property_changed(self)
        
        if self.DEBUG:
            print("property: initiated: " + str(self.title) + ", with value: " + str(value))
            self.device.adapter.should_save = True

            
        

    def set_value(self, value):
        # This gets called by the controller whenever the user changes the value inside the interface. For example if they press a button, or use a slider.
        if self.DEBUG:
            print("property: set_value called for " + str(self.title))
            print("property: set_value to: " + str(value))
        try:
            
            # Data Mute is a little different
            if self.id == 'matter-data_mute':
                self.device.data_mute = bool(value)
                
            # Turn property changes into Matter commands
            else:
                message = None
                command = None
                command_name = 'Move'
                
                if self.description['readOnly'] == True:
                    if self.DEBUG:
                        print("Error / impossible: readOnly property cannot be changed")
                    return
                
                if 'short_type' in self.details:
                    # OnOff switch
                    #if self.details['short_type'] == 'OnOff.Attributes.OnOff':
                    if self.details['short_type'].endswith('OnOff.Attributes.OnOff'):
                        if self.DEBUG:
                            print("attempting to create cluster command for OnOff")
                            #print("clusters: ", clusters)
                            #print("clusters.OnOff: ", clusters.OnOff)
                            #print("clusters.OnOff.Commands: ", clusters.OnOff.Commands)
                            #print("clusters.OnOff.Commands.On(): ", clusters.OnOff.Commands.On())
                        
                        if value == True:
                            command = clusters.OnOff.Commands.On()
                            command_name = 'On'
                        else:
                            command = clusters.OnOff.Commands.Off()
                            command_name = 'Off'
                        if self.DEBUG:
                            print("command: ", command)
                
                    # Brightness
                    elif self.details['short_type'] == 'LevelControl.Attributes.CurrentLevel':
                        if self.DEBUG:
                            print("attempting to create cluster command for CurrentLevel")
                        
                        # TODO: check if these values should always be scaled from 255 to 100
                        
                        if isinstance(value,(int,float)):
                            #percentage = round(value / 2.55)
                            percentage = int(value)
                            if self.DEBUG:
                                print("set_value:  value -> percentage: ", value, percentage)
                            
                            command = clusters.LevelControl.Commands.MoveToLevelWithOnOff(
                                        level=percentage,
                                        transitionTime=self.device.adapter.brightness_transition_time,
                                        )
                        elif isinstance(value,bool):
                            if self.DEBUG:
                                print("\nWARNING: set_value: currentLevel received a boolean instead of a number")
                            if value:
                                percentage = 100
                            else:
                                percentage = 0
                            command = clusters.LevelControl.Commands.MoveToLevelWithOnOff(
                                        level=percentage,
                                        transitionTime=self.device.adapter.brightness_transition_time,
                                        )
                
                    # Color temperature
                    elif self.details['short_type'] == 'ColorControl.Attributes.ColorTemperatureMireds':
                        if self.DEBUG:
                            print("set_value: attempting to create cluster command for ColorTemperatureMireds")
                        #if value == True:
                        
                        command = clusters.ColorControl.Commands.MoveToColorTemperature(
                                        #colorTemperature=value,
                                        colorTemperatureMireds=value,
                                        transitionTime=self.device.adapter.brightness_transition_time,
                                    )
                
                    # Color
                    elif self.details['short_type'] == 'ColorControl.Attributes.CurrentX':
                        if self.DEBUG:
                            print("set_value: attempting to create cluster command for CurrentX and CurrentY")
                    
                        
                        
                        if isinstance(value,str) and ((not value.startswith('#') and len(value) == 6) or (value.startswith('#') and len(value) == 7)):
                            if self.DEBUG:
                                print("going to call hex_to_xy with: ", value)
                            xy_tuple = hex_to_xy(value) # translate hex to x + y (and brightness? Which is discarded?)
                            if self.DEBUG:
                                print("color xy_tuple: ", xy_tuple)
                                
                            command = clusters.ColorControl.Commands.MoveToColor(
                                        colorX=int(xy_tuple.x),
                                        colorY=int(xy_tuple.y),
                                        transitionTime=self.device.adapter.brightness_transition_time,
                                    )
                        
                        elif isinstance(value,int) or str(value).isdigit():
                            if self.DEBUG:
                                print("\nERROR: set_value: provided color was a number?: ", value)
                        
                        elif isinstance(value,str) and not str(value).isdigit():
                            if self.DEBUG:
                                print("trying if the string is a color name: ", valuex)
                            value = colorNameToHex(value)
                            if value.startswith('#'):
                                xy_tuple = hex_to_xy(value) # translate hex to x + y (and brightness? Which is discarded?)
                                if self.DEBUG:
                                    print("color xy_tuple: ", xy_tuple)
                                
                                command = clusters.ColorControl.Commands.MoveToColor(
                                            colorX=int(xy_tuple.x),
                                            colorY=int(xy_tuple.y),
                                            # It's required in TLV. We don't implement transition time yet.
                                            transitionTime=self.device.adapter.brightness_transition_time,
                                        )
                            
                        else: # could be a string like "green" or "blue"
                            if self.DEBUG:
                                print("\nERROR: set_value: attempting colorNameToHex for: ", value)
                            
                            
                        
                            if self.DEBUG:
                                print("set_value: INVALID COLOR")
                
                # If a matching command was found, then it can be forwarder to the Matter server
                if command == None:
                    if self.DEBUG:
                        print("Property: set_value: ERROR, COMMAND WAS STILL NONE")
                else:
                    
                    try:
                        command_name = command.__class__.__name__
                        if self.DEBUG:
                            print("command_name from command: ", command_name)
                    except:
                        if self.DEBUG:
                            print("\nERROR: getting command_name failed")
                        try:
                            command_name = command.__name__
                        except:
                            if self.DEBUG:
                                print("\nERROR: getting command_name failed twice")
                            return
                            
                    if self.DEBUG:
                        #print("set_value: dir of command: ", dir(command))
                        print("node_id: ", self.details['node_id'])
                        print("self.details['endpoint']: ", self.details['endpoint'])
                        print("command.cluster_id", command.cluster_id)
                        print("command.command_id", command.command_id)
                        print("command_name: ", command_name)
                        
                        
                    
                    #command = clusters.OnOff.Commands.Toggle() # test
                    payload = dataclass_to_dict(command)
                    if self.DEBUG:
                        print("Property: set_value: payload: payload,payload.keys(): ", payload, payload.keys())
                    #if len(payload.keys()):
                    if self.DEBUG:
                        print("\n\nForwarding value to Matter server. payload as dict: " + str(payload))
                    
                    message = {
                        "message_id": "device_command",
                        "command": "device_command",
                        "args": {
                            "node_id": int(self.details['node_id']),
                            "endpoint_id": int(self.details['endpoint']),
                            "payload": payload,
                            "cluster_id": int(command.cluster_id),
                            "command_name": str(command_name)
                        }
                      }
                
                    
                    if message != None:
                    
                        # send device command
                        if self.DEBUG:
                            dump = json.dumps(message, sort_keys=True, indent=4, separators=(',', ': '))
                            if self.DEBUG:
                                print("\n.\n) ) )\n.\nsending change value message to the Matter network: " + str(dump))
                        json_message = json.dumps(message)
                        
                        if self.device.adapter.ws:
                            self.device.adapter.ws.send(json_message)
                            if self.DEBUG:
                                print("message sent?")
                
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
            
            
        
        except Exception as ex:
            print("property: set_value error: " + str(ex))
        
        if self.DEBUG:
            self.device.adapter.should_save = True
    #def send_to_matter(self,command):
    #    run(self.run_matter(), shutdown_callback=self.handle_stop)


    def update(self, value):
        # This is a quick way to set the value of this property. It checks that the value is indeed new, and then notifies the controller that the value was changed.
        
        if self.device.data_mute:
            if self.DEBUG:
                print("update of value blocked by Data mute for: " + str(self.title))
            return
        
        if self.DEBUG:
            print("property: update. value: " + str(value) + ', existing value: ' + str(self.value))
            print("self.details: ", self.details) 
            
        if 'short_type' in self.details and self.details['short_type'] == 'ColorControl.Attributes.CurrentX' and (isinstance(value,int) or str(value).isdigit()):
            if self.DEBUG:
                print("error: property: update: provided color was a number, but should be a hex value: ", value)
            return
            
        if 'short_type' in self.details and self.details['short_type'] == 'LevelControl.Attributes.CurrentLevel' and isinstance(value,(int,float)):
            if value < 0:
                value = 0
            elif value > 254:
                value = 254
                
            if value < 101:
                value = round(value * 2.54)
        
        if value != self.value:
            self.value = value
            self.set_cached_value(value)
            self.device.notify_property_changed(self)

 
