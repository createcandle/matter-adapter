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
        
        if not 'attribute_code' in self.details and property_id != 'data_mute':
            if self.DEBUG:
                print("\nERROR missing attribute_code in self.details of property: ", property_id)
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
            
            
            if self.device.attributes:
                if self.DEBUG:
                    print("property: set_value: self.device.attributes.keys(): ", self.device.attributes.keys())
            
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
                
                if 'attribute_code' in self.details:
                    # OnOff switch
                    #if self.details['attribute_code'] == 'OnOff.Attributes.OnOff':
                    if self.details['attribute_code'].endswith('OnOff.Attributes.OnOff'):
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
                    elif self.details['attribute_code'] == 'LevelControl.Attributes.CurrentLevel':
                        if self.DEBUG:
                            print("attempting to create cluster command for CurrentLevel")
                        
                        # TODO: check if these values should always be scaled from 255 to 100
                        
                        if isinstance(value,(int,float)):
                            #percentage = round(value / 2.55)
                            percentage = int(value)
                            if self.DEBUG:
                                print("set_value:  value -> percentage: ", value, percentage)
                            
                            #command = clusters.LevelControl.Commands.MoveToLevelWithOnOff(
                            command = clusters.LevelControl.Commands.MoveToLevel(
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
                    elif self.details['attribute_code'] == 'ColorControl.Attributes.ColorTemperatureMireds' and self.description and '@type' in self.description and str(self.description['@type']) == 'ColorTemperatureProperty':
                        if self.DEBUG:
                            print("set_value: attempting to create cluster command for ColorTemperatureMireds")
                        #if value == True:
                        
                        command = clusters.ColorControl.Commands.MoveToColorTemperature(
                                        #colorTemperature=value,
                                        colorTemperatureMireds=value,
                                        transitionTime=self.device.adapter.brightness_transition_time,
                                    )
                
                    # HSV Color
                    elif self.details['attribute_code'] == 'ColorControl.Attributes.CurrentHue' and self.description and '@type' in self.description and str(self.description['@type']) == 'ColorProperty':
                        if self.DEBUG:
                            print("Attempting to translate hex color to Hue and Saturation values")
                        if is_hex_color(value):
                            
                            hsv = hex_to_hsv(value)
                            print("HSV COLOR OUTPUT FROM HEX: ", value, hsv)
                            
                            command = clusters.ColorControl.Commands.MoveToHueAndSaturation(
                                    hue=int(hsv[0]),
                                    saturation=int(hsv[1]),
                                    TransitionTime=self.device.adapter.brightness_transition_time,
                                )
                        
                    
                    
                    # X Y Color
                    elif self.details['attribute_code'] == 'ColorControl.Attributes.CurrentX' and self.description and '@type' in self.description and str(self.description['@type']) == 'ColorProperty':
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
                                        TransitionTime=self.device.adapter.brightness_transition_time,
                                    )
                        
                        elif isinstance(value,int) or str(value).isdigit():
                            if self.DEBUG:
                                print("\nERROR: set_value: provided color was a number?: ", value)
                        
                        elif isinstance(value,str) and not str(value).isdigit():
                            if self.DEBUG:
                                print("trying if the string is a color name: ", value)
                            value_color_to_hex = colorNameToHex(value)
                            if value_color_to_hex.startswith('#'):
                                xy_tuple = hex_to_xy(value_color_to_hex) # translate hex to x + y (and brightness? Which is discarded?)
                                if self.DEBUG:
                                    print("color xy_tuple: ", xy_tuple)
                                
                                command = clusters.ColorControl.Commands.MoveToColor(
                                            colorX=int(xy_tuple.x),
                                            colorY=int(xy_tuple.y),
                                            # It's required in TLV. We don't implement transition time yet.
                                            transitionTime=self.device.adapter.brightness_transition_time,
                                        )
                            
                        #else: # could be a string like "green" or "blue"
                        #    if self.DEBUG:
                        #        print("\nERROR: set_value: attempting colorNameToHex for: ", value)
                            
                            
                        else:
                            if self.DEBUG:
                                print("set_value: INVALID COLOR.  value: ", value)
                
                    
                    elif self.description and '@type' in self.description and (str(self.description['@type']) == 'ColorProperty' or str(self.description['@type']) == 'ColorTemperatureProperty'):
                        if self.DEBUG:
                            print("\nERROR, set_value: unhandled attribute_code + color property capability, aborting.  attribute_code: ", self.details['attribute_code'])
                        return
                
                
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
                            was_sent = self.device.adapter.ws.send(json_message)
                            if self.DEBUG:
                                print("message sent? was_sent: ", was_sent)
                            self.update(value)
                
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


    def update(self, value, meta=None):
        # This is a quick way to set the value of this property. It checks that the value is indeed new, and then notifies the controller that the value was changed.
        
        if meta != None:
            if self.DEBUG:
                print("OK, Matter property received META data: ", meta)
        
        if self.device.data_mute:
            if self.DEBUG:
                print("update of value blocked by Data mute for: " + str(self.title))
            return
        
        if self.DEBUG:
            print("property: update. value: " + str(value) + ', existing value: ' + str(self.value))
            print("self.details: ", self.details) 
            
        
        try:
            if 'attribute_code' in self.details and '.Attributes.' in str(self.details['attribute_code']):
            
                cluster_name = str(self.details['attribute_code'].split('.Attributes.')[0])
                attribute_name = str(self.details['attribute_code'].split('.Attributes.')[1])
                
                if attribute_name == 'OnOff':
                    if str(value) == 'On':
                        value = True
                    elif str(value) == 'Off':
                        value = False
                    else:
                        if self.DEBUG:
                            print("OnOff update value: ", value)
                        
                elif attribute_name == 'CurrentPosition':
                    if str(value) == 'On':
                        value = 1
                    elif str(value) == 'Off':
                        value = 0
                    else:
                        if self.DEBUG:
                            print("CurrentPosition update value: ", value)
                        
                if value != None: # None values are allowed and encouraged
                    
                    if self.details['attribute_code'] == 'ColorControl.Attributes.CurrentX' and (isinstance(value,int) or str(value).isdigit()):
                        if self.DEBUG:
                            print("error: property: update: provided color was a number, but should be a hex value: ", value)
                            # TODO: change this to a hex color instead of returning
                        return
            
                    # turn into enum string value
                    if self.details['attribute_code'] in self.device.adapter.enums_lookup and isinstance(value,int) and value >= 0 and value < len(self.device.adapter.enums_lookup[ self.details['attribute_code'] ]) and 'type' in self.description and self.description['type'] == 'string':
                        value = str(self.device.adapter.enums_lookup[ self.details['attribute_code'] ][value])
            
                    # Adjust from percentage back to the range that the matter device expects (likely 0-100 -> 1-254)
                    elif self.details['attribute_code'] == 'LevelControl.Attributes.CurrentLevel' and isinstance(value,(int,float)):
                        if value < 0:
                            value = 0
                        elif value > 254:
                            value = 254
                
                        if 'minimum' in self.description:
                            if value < self.description['minimum']:
                                value = self.description['minimum']
                
                        if 'maximum' in self.description:
                            if value > self.description['maximum']:
                                value = self.description['maximum']
                    
                            delta = self.description['maximum'] - self.description['minimum']
                            #if delta > 100:
                            percentage_factor = delta / 100
                            if self.DEBUG:
                                print("percentage_factor: ", percentage_factor)
                            if value < 101: # the value coming from a percentage in the gateway should be between 0 and 100, so this check is superfluous
                                value = self.description['minimum'] + round(value * percentage_factor)
        
                            if value > self.description['maximum']:
                                if self.DEBUG:
                                    print("warning, percentage scaled value ended up bigger than the allowed maximum: ", value, self.description['maximum'] )
                                value = self.description['maximum']
                            if value < self.description['minimum']:
                                if self.DEBUG:
                                    print("warning, percentage scaled value ended up smaller than the allowed minimum: ", value, self.description['minimum'] )
                                value = self.description['minimum']
            
        except Exception as ex:
            print("ERROR: property: update: caught error trying to wrangle value based on attribute_code: ", self.id, ex)
            
        
        
        
        try:
            # Make sure color values are in the form of a HEX code with a # at the beginning
            if self.description and '@type' in self.description and str(self.description['@type']) == 'ColorProperty':
                if not is_hex_color(value):
                    if self.DEBUG:
                        print("\nERROR: property: update: aborting, value was not a valid hex color: ", value)
                    return
                    
            # Make sure values are of the expected type
            elif value != None:
                if self.description and 'type' in self.description:
                    if str(self.description['type']) == 'string':
                        value = str(value)
                        if 'enum' in self.description and len(self.description['enum']):
                            if not value in self.description['enum']:
                                uncameled_value = uncamel(value).replace('_',' ')
                                if uncameled_value in self.description['enum']:
                                    if self.DEBUG:
                                        print("OK, uncameled_value was found in enum: ", uncameled_value)
                                    value = uncameled_value
                                else:
                                    if self.DEBUG:
                                        print("ERROR, the property has an enum list, but the provided string was not present in that list.  self.id, value, enum: ", self.id, value, self.description['enum'])
                                    return
                    elif str(self.description['type']) == 'integer':
                        value = int(value)
                    elif str(self.description['type']) == 'boolean':
                        value = bool(value)
                        
        except Exception as ex:
            print("ERROR: property: update: caught error while trying ensure value is in correct format: ", self.id, ex)
        
        if self.DEBUG:
            print("PROPERTY UPDATE: FINAL VALUE: ", type(value), value)
        
        
        if value != self.value:
            self.value = value
            self.set_cached_value(value)
            self.device.notify_property_changed(self)

        return self.value
 
