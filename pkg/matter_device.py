
from gateway_addon import Device, Action
from .matter_property import MatterProperty
#
# DEVICE
#



class MatterDevice(Device):
    """Matter device type."""

    def __init__(self, adapter, device_id, node):
        """
        Initialize the object.
        adapter -- the Adapter managing this device
        """

        Device.__init__(self, adapter, device_id)

        self.id = device_id
        self._id = device_id
        self.name = device_id
        self.adapter = adapter
        self.DEBUG = adapter.DEBUG
        self.title = 'Matter addon thing'
        self.description = 'This is a Matter device'
        
        self.node = node
        self.node_id = node['node_id']
        self.data_mute = False
        
        # We give this device a "capability". This will cause it to have an icon that indicates what it can do. 
        # Capabilities are always a combination of giving a this a capability type, and giving at least one of its properties a capability type.
        # For example, here the device is a "multi level switch", which means it should have a boolean toggle property as well as a numeric value property
        # There are a lot of capabilities, read about them here: https://webthings.io/schemas/
        
        #self._type = ['MultiLevelSwitch'] # a combination of a toggle switch and a numeric value

        try:
            
            supported_attributes = {
                "OnOff.Attributes.OnOff":{}
            }
            supported_types = supported_attributes.keys()
            if self.DEBUG:
                print("device: supported_types: " + str(supported_types))
            
            for attribute_code in node['attributes'].keys():
                
                
                try:
                    #attr = node[attribute]
                    attr = node['attributes'][attribute_code] # e.g. "0/29/0"
                    #if self.DEBUG:
                    #    print("Device: checking attribute: " + str(attr))
                    
                    type_list = attr['attribute_type'].split('.')
                    short_type = type_list[-3] + "." + type_list[-2] + "." + type_list[-1]
                    if self.DEBUG:
                        print("Device: short type: " + str(short_type))
                    
                    if short_type in supported_types:
                        if self.DEBUG:
                            print("\n\n\n B I N G O")
                        
                        property_id = 'property-' + str(attr['attribute_id'])
                        
                        # Save the message so it can be used to regenerate the device later. 
                        # Only save actually useful attribute data in the persistent data.
                        if not device_id in self.adapter.persistent_data['nodez'].keys():
                            self.adapter.persistent_data['nodez'][device_id] = {
                                                                        'node_id':node['node_id'],
                                                                        'attributes':{}
                                                                    }
                            self.adapter.should_save = True
                        if property_id not in self.adapter.persistent_data['nodez'][device_id].keys():
                            self.adapter.persistent_data['nodez'][device_id]['attributes'][property_id] = attr
                            self.adapter.should_save = True
                            
                        
                        if self.DEBUG:
                            print("nodez created")
                        
                        
                        # ON/OFF
                        if attr['attribute_type'] == 'chip.clusters.Objects.OnOff.Attributes.OnOff':
                            print("bingo, Attributes.OnOff")
                            value = attr['value']
                            
                            if self.DEBUG:
                                print("new property_id: " + str(property_id) + ", type: " + str(attr['attribute_type']))
                        
                            # Toggle switch
                            self.properties[property_id] = MatterProperty(
                                            self,
                                            "state",
                                            {
                                                '@type': 'OnOffProperty',
                                                'title': "State",
                                                'readOnly': False,
                                                'type': 'boolean'
                                            },
                                            value,
                                            attr)
                        
                        
                        
                            
                            # Binary read-only
                            # clusters.BooleanState.Attributes.StateValue
                            # clusters.OccupancySensing.Attributes.Occupancy
                            
                            # sensors: https://github.com/home-assistant/core/blob/dev/homeassistant/components/matter/sensor.py
                            # clusters.RelativeHumidityMeasurement.Attributes.MeasuredValue
                            # clusters.TemperatureMeasurement.Attributes.MeasuredValue
                            
                            # light: https://github.com/home-assistant/core/blob/dev/homeassistant/components/matter/light.py
                            # clusters.LevelControl.Attributes.CurrentLevel
                                        
                                        
                            self.properties['data_mute'] = MatterProperty(
                                            self,
                                            "Data mute",
                                            {
                                                'title': "Data mute",
                                                'readOnly': False,
                                                'type': 'boolean'
                                            },
                                            self.data_mute,
                                            {'attribute_id':'data_mute'})
                                        
                except Exception as ex:
                    if self.DEBUG:
                        print("Device: error in generating property: " + str(ex))
                    
                    
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
            
        except Exception as ex:
            if self.DEBUG:
                print("Error adding properties to thing: " + str(ex))

        if self.DEBUG:
            print("thing has been created.")



