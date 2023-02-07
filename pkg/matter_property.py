
import json
from gateway_addon import Property
from chip.clusters import Objects as clusters
from chip.clusters import ClusterCommand
from dataclasses import dataclass, asdict, field, InitVar


#
# PROPERTY
#

class MatterProperty(Property):

    def __init__(self, device, name, description, value, attribute): # description here means the dictionary that described the property, not a text description.
        # This creates the initial property
        property_id = 'property-' + str(attribute['attribute_id'])
        print("Property: property_id: " + str(property_id))
        Property.__init__(self, device, property_id, description)
        
        self.device = device
        self.DEBUG = device.DEBUG
        
        self.id = property_id
        self._id = property_id
        self.name = property_id
        self.title = property_id
        self.description = description # a dictionary that holds the details about the property type
        self.value = value # the initial value of the property
        
        self.attribute = attribute
        
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
            if self.id == 'matter-data_mute':
                self.device.data_mute = bool(value)
                
            else:
                #print("property attribute: " + str(self.attribute))
                #print("DIR: " + str(dir(clusters.OnOff.Commands)))
		        
                mock_cluster_command = ClusterCommand()
                message = {
                        "message_id": "device_command",
                        "command": "device_command",
                        "args": {
                            "endpoint": int(self.attribute['endpoint']),
                            "node_id": int(self.attribute['node_id']),
                            "payload": mock_cluster_command #{'value':'Toggle'} #asdict(clusters.OnOff.Commands.Off())
                        }
                      }
                  
                """
                message = {
                    'node_id':self.device.node_id,
                    endpoint=self._device_type_instance.endpoint,
                    command=clusters.OnOff.Commands.On()
                }
            
                if self.id == 'state':
                    self.device.adapter.set_state(bool(value))
                    message['endpoint] = 
        
                elif self.id == 'slider':
                    self.device.adapter.set_slider(int(value))
        
                elif self.id == 'dropdown':
                    self.device.adapter.set_dropdown(str(value))
                """
            
            
        
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


    def update(self, value):
        # This is a quick way to set the value of this property. It checks that the value is indeed new, and then notifies the controller that the value was changed.
        
        print("property: update. value: " + str(value))
         
        if value != self.value:
            self.value = value
            self.set_cached_value(value)
            self.device.notify_property_changed(self)




"""
def dataclass_to_dict(obj_in: object, skip_none: bool = False) -> dict:
    if skip_none:
        dict_obj = asdict(
            obj_in, dict_factory=lambda x: {k: v for (k, v) in x if v is not None}
        )
    else:
        dict_obj = asdict(obj_in)

    def _convert_value(value: Any) -> Any:
        if isinstance(value, list):
            return [_convert_value(x) for x in value]
        if isinstance(value, Nullable) or value == NullValue:
            return None
        if isinstance(value, dict):
            return _clean_dict(value)
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, bytes):
            return b64encode(value).decode()
        if isinstance(value, float32):
            return float(value)
        if type(value) == type:
            return f"{value.__module__}.{value.__qualname__}"
        if isinstance(value, Exception):
            return None
        return value

    def _clean_dict(_dict_obj: dict) -> dict:
        _final = {}
        for key, value in _dict_obj.items():
            if isinstance(key, int):
                key = str(key)
            _final[key] = _convert_value(value)
        return _final

    dict_obj["_type"] = f"{obj_in.__module__}.{obj_in.__class__.__qualname__}"
    return _clean_dict(dict_obj)
"""