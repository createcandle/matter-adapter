
import json
#import asyncio
#from aiorun import run
from gateway_addon import Property
from chip.clusters import Objects as clusters # also loaded as dependency from matter_server, see below
from chip.clusters import ClusterCommand

#from dataclasses import dataclass, asdict, field, InitVar
#from dataclasses import MISSING, asdict, fields, is_dataclass

try:
    from matter_server.common.helpers.util import dataclass_from_dict,dataclass_to_dict
    from matter_server.common.models.api_command import APICommand
    from matter_server.common.models.message import CommandMessage
    #from matter_server.common.json_utils import CHIPJSONDecoder, CHIPJSONEncoder
    #from matter_server.vendor.chip.clusters import Objects as clusters
except Exception as ex:
    print("Error loading matter_server parts: " + str(ex))


from .matter_util import *

    
#
# PROPERTY
#

class MatterProperty(Property):

    def __init__(self, device, name, description, value, attribute,settings=None): # description here means the dictionary that described the property, not a text description.
        # This creates the initial property
        property_id = 'property-' + str(attribute['attribute_id'])
        print("Property: property_id: " + str(property_id))
        Property.__init__(self, device, property_id, description)
        
        self.DEBUG = device.DEBUG
        
        self.device = device
        
        self.id = property_id
        self._id = property_id
        self.name = property_id
        self.title = property_id
        self.description = description # a dictionary that holds the details about the property type
        self.value = value # the initial value of the property
        
        self.attribute = attribute
        
        
        if settings != None:
            for key, value in setings.items():
                print("creating self." + str(key) + ", with value: " + str(value))
                self[key] = value
        
        # Notifies the controller that this property has a (initial) value
        self.set_cached_value(value)
        self.device.notify_property_changed(self)
        
        
        
        
        if self.device.DEBUG:
            print("property: initiated: " + str(self.title) + ", with value: " + str(value))


    def set_value(self, value):
        # This gets called by the controller whenever the user changes the value inside the interface. For example if they press a button, or use a slider.
        print("property: set_value called for " + str(self.title))
        print("property: set value to: " + str(value))
        print("self.attribute: " + str(self.attribute))
        try:
            
            # Data Mute is a little different
            if self.id == 'matter-data_mute':
                self.device.data_mute = bool(value)
                
            # Turn property changes into Matter commands
            else:
                message = None
                command = None
                
                if self.description['readOnly'] == True:
                    print("Error / impossible: readOnly property cannot be changed")
                    return
                
                
                #if self.title.lower() == 'state' or self.short_type = 'OnOff.Attributes.OnOff':
                # OnOff switch
                if self.short_type == 'OnOff.Attributes.OnOff':
                    print("attempting to create cluster command for OnOff")
                    if value == True:
                        command = clusters.OnOff.Commands.On()
                    else:
                        command = clusters.OnOff.Commands.Off()
                
                # Brightness
                elif self.short_type == 'LevelControl.Attributes.CurrentLevel':
                    print("attempting to create cluster command for CurrentLevel")
                    if value == True:
                        command = clusters.LevelControl.Commands.MoveToLevelWithOnOff(
                                        level=int(value),
                                        transitionTime=self.device.adapter.brightness_transition_time,
                                        )
                
                # Color temperature
                elif self.short_type == 'ColorControl.Attributes.ColorTemperatureMireds':
                    print("attempting to create cluster command for ColorTemperatureMireds")
                    #if value == True:
                        
                    clusters.ColorControl.Commands.MoveToColorTemperature(
                                    colorTemperature=value,
                                    # It's required in TLV. We don't implement transition time yet.
                                    transitionTime=self.device.adapter.brightness_transition_time,
                                )
                
                # color
                elif self.short_type == 'ColorControl.Attributes.CurrentX':
                    print("attempting to create cluster command for CurrentX and CurrentY")
                    if not value.startswith('#'): # could be a string like "green" or "blue"
                        value = colorNameToHex(value)
                    else:
                        xy_tuple = hex_to_xy(value) # translate hex to x + y (and brightness? Which is discarded?)
                        
                    command = clusters.ColorControl.Commands.MoveToColor(
                                    colorX=int(xy_tuple.x),
                                    colorY=int(xy_tuple.y),
                                    # It's required in TLV. We don't implement transition time yet.
                                    transitionTime=self.device.adapter.brightness_transition_time,
                                )
                
                
                # If a matching command was found, then it can be sent to the Matter server
                if command == None:
                    print("ERROR, COMMAND WAS STILL NONE")
                else:
                    print("\n\nSTART\n\n")
                    #command = clusters.OnOff.Commands.Toggle() # test
                    payload = dataclass_to_dict(command)
                    print("\n\n_____\npayload as dict: " + str(payload))
                    message = {
                            "message_id": "device_command",
                            "command": "device_command",
                            "args": {
                                "endpoint": int(self.attribute['endpoint']),
                                "node_id": int(self.attribute['node_id']),
                                "payload": payload
                            }
                          }
                
                    
                    if message != None:
                    
                        # send device command
                        if self.DEBUG:
                            dump = json.dumps(message, sort_keys=True, indent=4, separators=(',', ': '))
                            print("\n.\n) ) )\n.\nsending change value message to the Matter network: " + str(dump))
                        json_message = json.dumps(message)

                        self.device.adapter.ws.send(json_message)
                    
                
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

    #def send_to_matter(self,command):
    #    run(self.run_matter(), shutdown_callback=self.handle_stop)


    def update(self, value):
        # This is a quick way to set the value of this property. It checks that the value is indeed new, and then notifies the controller that the value was changed.
        
        if self.device.data_mute:
            if self.DEBUG:
                print("update of value blocked by Data mute for: " + str(self.title))
            return
        
        print("property: update. value: " + str(value))
         
        if value != self.value:
            self.value = value
            self.set_cached_value(value)
            self.device.notify_property_changed(self)

 