
import re
from gateway_addon import Device, Action
from .matter_property import MatterProperty

from .matter_util import xy_to_hex

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
        self.title = 'Matter device'
        self.description = 'This is a Matter device'
        self._type = [] # holds capacilities
        
        self.node = node
        self.node_id = node['node_id']
        self.data_mute = False
        
        
        try:
            
            supported_attributes = {
                "BasicInformation.Attributes.VendorName":{'readOnly':True, 'type':'string'},    # Vendor name
                "BasicInformation.Attributes.ProductName":{'readOnly':True, 'type':'string'},   # Product name
                "BasicInformation.Attributes.UniqueID":{'readOnly':True, 'type':'string'},      # Unique ID
                "BasicInformation.Attributes.HardwareVersionString":{'readOnly':True, 'type':'string'}, # Hardware version string
                "BasicInformation.Attributes.SoftwareVersionString":{'readOnly':True, 'type':'string'}, # Software version string
                
                "OnOff.Attributes.OnOff":{
                    'readOnly': False, 
                    'type':'boolean', 
                    '@type':'OnOffProperty', 
                    'dev@type':'OnOffSwitch'}, # state
                    
                "BooleanState.Attributes.StateValue":{
                    'readOnly': True, 
                    'type':'boolean',
                    '@type':'BooleanProperty', 
                    'dev@type':'BinarySensor'}, # readOnly state
                "OccupancySensing.Attributes.Occupancy":{
                    'readOnly': True, 
                    'type':'boolean',
                    '@type': 'MotionProperty',
                    'dev@type':'MotionSensor'}, # occupancy
                    
                "RelativeHumidityMeasurement.Attributes.MeasuredValue":{
                    'readOnly':True, 
                    'type':'integer', 
                    'percent':True,
                    '@type':'LevelProperty',
                    'dev@type':'MultiLevelSensor'}, # humidity
                "TemperatureMeasurement.Attributes.MeasuredValue":{
                    'readOnly': True,
                    'type': 'number',
                    'multipleOf':0.1,
                    '@type': 'TemperatureProperty'},
                    'dev@type':'TemperatureSensor'} # temperature
                "PressureMeasurement.Attributes.MeasuredValue":{
                    'readOnly': True,
                    'type': 'number',
                    'multipleOf':0.1,
                    '@type': 'BarometricPressureProperty',
                    'dev@type': 'BarometricPressureSensor'}, # pressure
                "FlowMeasurement.Attributes.MeasuredValue":{
                    'readOnly':True, 
                    'type':'number',
                    'multipleOf':0.1,
                    '@type':'LevelProperty',
                    'dev@type':'MultiLevelSensor'}, # flow
                "IlluminanceMeasurement.Attributes.MeasuredValue":{
                    'readOnly':True, 
                    'type':'integer',
                    'multipleOf':1,
                    '@type':'LevelProperty',
                    'dev@type':'MultiLevelSensor'}, # illuminance
                    
                "LevelControl.Attributes.CurrentLevel":{
                    'readOnly': False, 
                    'type':'integer', 
                    'percent':True, 
                    '@type':'BrightnessProperty',
                    'dev@type':'Light'}, # light brightness
                "ColorControl.Attributes.ColorMode":{
                    'readOnly': False, 
                    'type':'string', 
                    '@type': 'ColorProperty',
                    'dev@type':'Light'}, # light color
                "ColorControl.Attributes.CurrentX":{
                    'readOnly': False, 
                    'type':'string', 
                    '@type': 'ColorProperty',
                    'dev@type':'Light'}, # color X coordinate. Y value will be loaded too if this one is an attribute
                "ColorControl.Attributes.ColorTemperatureMireds":{
                    'readOnly': False, 
                    'type':'integer', 
                    'minimum':-200,
                    'maximum':200,
                    '@type': 'ColorTemperatureProperty',
                    'dev@type':'Light'}, # Color temperature (in Mireds)
                
                    
                    
                # TODO: with color, the properties are all options for the 'light' capability. Done, removed dev@type
                # TODO: color temperature has minimum and maximum values (should use those), and both physical and 'level' (which to choose?). Done, should be overridden later
                # https://github.com/project-chip/connectedhomeip/blob/f24ce30a0e120e7bb8649c0ed2fa4558a03b28a5/examples/all-clusters-app/ameba/main/include/ColorControlCommands.h#L302
                    
            }
            supported_types = supported_attributes.keys()
            if self.DEBUG:
                print("all supported_types: " + str(supported_types))
            
            
            # Keep track of capabilities and titles we've used
            used_property_titles = [] # keep track of which property titles have been used already in this device, to avoid doubles.
            used_property_at_types = [] # keep track of which property @types have already been added to the device. Only one per type is allowed.
            
            # Check if it's useful to add DataMute property. If there is a readOnly property, then it is useful.
            add_data_mute = False
            
            
            
            # PREPARATION LOOP
            
            # As preparation, loop over the node and make a simple list of all shortened attributes
            if self.DEBUG:
                print("\n\n\n")
            all_short_attributes = {}
            for attribute_code in node['attributes'].keys():
                attr = node['attributes'][attribute_code]
                type_list = attr['attribute_type'].split('.')
                short_type = type_list[-3] + "." + type_list[-2] + "." + type_list[-1]
                all_short_attributes[short_type] = attribute_code
                if self.DEBUG:
                    print("Device: short type: " + str(short_type))
            if self.DEBUG:
                print("\n\n\n")
                
                
            # MAIN ATTRIBUTES TO PROPERTIES LOOP
            
            # Loop over all the node's attributes and only pay attention to the ones that are important
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
                            print("\n\n\n B I N G O: " + str(short_type))
                        
                        property_id = 'property-' + str(attr['attribute_id'])
                        
                        
                        # Only save actually useful attribute data in the persistent data.
                        if not device_id in self.adapter.persistent_data['nodez'].keys():
                            self.adapter.persistent_data['nodez'][device_id] = {
                                                                        'node_id':node['node_id'],
                                                                        'attributes':{}
                                                                    }
                            self.adapter.should_save = True
                        
                        
                        
                        # GET VENDOR NAME, PRODUCT NAME, AND UNIQUE ID
                        
                        try:
                            # Save vendor name in nodez dict
                            if short_type == 'BasicInformation.Attributes.VendorName':
                                if not 'vendor_name' in self.adapter.persistent_data['nodez'][device_id]:
                                    self.adapter.should_save = True
                                
                                self.adapter.persistent_data['nodez'][device_id]['vendor_name'] = attr['value']
                                if self.DEBUG:
                                    print("vendor_name: " + str(self.adapter.persistent_data['nodez'][device_id]['vendor_name']))
                                continue
                                
                            # Save product name in nodez dict
                            if short_type == 'BasicInformation.Attributes.ProductName':
                                if not 'product_name' in self.adapter.persistent_data['nodez'][device_id]:
                                    self.adapter.should_save = True
                                self.adapter.persistent_data['nodez'][device_id]['product_name'] = attr['value']
                                if self.DEBUG:
                                    print("product_name: " + str(self.adapter.persistent_data['nodez'][device_id]['product_name']))
                                continue
                                
                            # Save unique ID to nodez dict
                            if short_type == 'BasicInformation.Attributes.UniqueID':
                                if not 'unique_id' in self.adapter.persistent_data['nodez'][device_id]:
                                    self.adapter.should_save = True
                                self.adapter.persistent_data['nodez'][device_id]['unique_id'] = attr['value']
                                if self.DEBUG:
                                    print("unique_id: " + str(self.adapter.persistent_data['nodez'][device_id]['unique_id']))
                                continue
                                
                            # Save hardware version to nodez dict
                            if short_type == 'BasicInformation.Attributes.HardwareVersionString':
                                if not 'hardware_version' in self.adapter.persistent_data['nodez'][device_id]:
                                    self.adapter.should_save = True
                                self.adapter.persistent_data['nodez'][device_id]['hardware_version'] = attr['value']
                                if self.DEBUG:
                                    print("hardware_version: " + str(self.adapter.persistent_data['nodez'][device_id]['hardware_version']))
                                continue
                        
                            # Save software version to nodez dict
                            if short_type == 'BasicInformation.Attributes.SoftwareVersionString':
                                if not 'software_version' in self.adapter.persistent_data['nodez'][device_id]:
                                    self.adapter.should_save = True
                                self.adapter.persistent_data['nodez'][device_id]['software_version'] = attr['value']
                                if self.DEBUG:
                                    print("software_version: " + str(self.adapter.persistent_data['nodez'][device_id]['software_version']))
                                continue
                        
                        except Exception as ex:
                            print("Error extracting BasicInfo: " + str(ex))
                        
                        
                        # Save the message in persistent data so it can be used to regenerate the device later.
                        # TODO: actually, that's not necessary, the matter server keeps track of it just fine
                        if property_id not in self.adapter.persistent_data['nodez'][device_id].keys():
                            self.adapter.persistent_data['nodez'][device_id]['attributes'][property_id] = attr
                            self.adapter.should_save = True
                        
                        
                        
                        # GENERATE TITLE
                        
                        property_title = "Unknown"
                        try:
                            property_title = attr["attribute_name"]
                            if self.DEBUG:
                                print("original raw property title / attribute name: " + str(property_title))
                            
                            # Remove "String" from title, just in case the basicInfo stuff will be turned into properties too
                            if property_title.endswith('String'):
                                property_title = property_title.replace('String','')
                            
                            # Manually override some names
                            if property_title == 'OnOff':
                                property_title = 'State'
                            else:
                                capital_words = []
                                capital_words = re.findall('[A-Z][^A-Z]*', property_title)
                                property_title = " ".join(str(x) for x in capital_words)
                                
                            # Make sure the property title is unique
                            if not property_title in used_property_titles:
                                used_property_titles.append(property_title)
                            else:
                                keep_looping = True
                                index = 1
                                while keep_looping:
                                    index += 1
                                    possible_title = property_title + " " + str(index)
                                    if not possible_title in used_property_titles:
                                        property_title = possible_title
                                        used_property_titles.append(possible_title)
                                        keep_looping = False
                                        break
                        
                            if self.DEBUG:
                                print("Final property title: " + str(property_title))
                        
                        except Exception as ex:
                            print("Error finding a good property title: " + str(ex))
                        
                        
                        
                        
                        
                        # WEBTHINGS PROPERTY DESCRIPTION AND @-TYPES
                        
                        # Basic property description
                        description = {}
                        description['type'] = supported_attributes[short_type]['type']
                        description['readOnly'] = supported_attributes[short_type]['readOnly']
                        description['title'] = property_title # TODO: should title be in here?
                        
                        # Percentage shortcut
                        if 'percent' in supported_attributes[short_type]:
                            if supported_attributes[short_type]['percent'] == True: # This is always True the case if the attribute exists...
                                description['multipleOf'] = 1
                                description['minimum'] = 0
                                description['maximum'] = 100
                                description['unit'] = 'percent'
                        
                        # MultipleOf
                        if 'multipleOf' in supported_attributes[short_type]:
                            description['multipleOf'] = supported_attributes[short_type]['multipleOf']
                        
                        # Minimum and maximum number/integer limits
                        if 'minimum' in supported_attributes[short_type]:
                            description['minimum'] = supported_attributes[short_type]['minimum']
                        if 'maximum' in supported_attributes[short_type]:
                            description['maximum'] = supported_attributes[short_type]['maximum']
                        
                        
                        # If readOnly properties are present, then enable data mute
                        if description['readOnly'] == True:
                            add_data_mute = True
                        
                        
                        # ADD CAPABILITES
                        
                        if self.DEBUG:
                            print("new property_id: " + str(property_id) + ", type: " + str(attr['attribute_type']))
                        
                        def add_device_capability():
                            try:
                                if self.DEBUG:
                                    print("in add_device_capability. supported_attributes[short_type]: " + str(supported_attributes[short_type]))
                                if '@type' in supported_attributes[short_type]:
                                    if supported_attributes[short_type]['@type'] not in used_property_at_types:
                                        description['@type'] = supported_attributes[short_type]['@type']
                                        used_property_at_types.append(description['@type'])
                                    
                                        # Theoretically it would be nicer to check if ALL required properies for the dev@type exist. Also, currenty there is a tiny chance that the dev@type is never set
                                        if 'dev@type' in supported_attributes[short_type]:
                                            if not supported_attributes[short_type]['dev@type'] in self._type:
                                                self._type.append( supported_attributes[short_type]['dev@type'] )
                                                if self.DEBUG:
                                                    print("add new capability: " + str(supported_attributes[short_type]['dev@type']))
                                            else:
                                                if self.DEBUG:
                                                    print("capability already existed: " + str(supported_attributes[short_type]['dev@type']))
                            
                            except Exception as ex:
                                print("Device: error in add_device_capability: " + str(ex))
                        
                        # Add these attributes to each MatterProperty object
                        settings = {'short_type':short_type}
                        
                        # Add optional capabilities
                        add_device_capability()
                        
                        
                        
                        # OPTMIZE VALUES
                        
                        value = attr['value']
                        
                        # COLOR 
                        try:
                            # Turn XY Color in HEX color when parsing the X color
                            if short_type == 'ColorControl.Attributes.CurrentX' and 'ColorControl.Attributes.CurrentY' in all_short_attributes:
                                # Get Y value too
                                color_y_attribute_code = all_short_attributes['ColorControl.Attributes.CurrentY']
                                color_y_node = node['attributes'][color_y_attribute_code]
                                if self.DEBUG:
                                    print("color_y_node: " + str(color_y_node))
                                color_y_value = color_y_node['value']
                                if self.DEBUG:
                                    print("color x: " + str(value) + ", y: " + str(color_y_value))
                            
                                # TODO: in one line, theoretically:
                                # color_y_value = node['attributes'][ all_short_attributes['ColorControl.Attributes.CurrentY'] ]['value']
                            
                                # calculate hex string
                                value = xy_to_hex(value,color_y_value)
                            
                                #chip.clusters.Objects.ColorControl.Attributes.CurrentY
                            
                            # Override minimum and maximum mireds according to provided data
                            if short_type == 'ColorControl.Attributes.ColorTemperatureMireds':
                                if 'ColorControl.Attributes.ColorTempPhysicalMinMireds' in all_short_attributes and 'ColorControl.Attributes.ColorTempPhysicalMaxMireds' in all_short_attributes:
                                    description['minimum'] = node['attributes'][ all_short_attributes['ColorControl.Attributes.ColorTempPhysicalMinMireds'] ]['value']
                                    description['maximum'] = node['attributes'][ all_short_attributes['ColorControl.Attributes.ColorTempPhysicalMaxMireds'] ]['value']
                                    
                        except Exception as ex:
                            print("Device: error optimizing color value: " + str(ex))
                            
                            
                            
                            
                        # ADD PROPERTY
                        if self.DEBUG:
                            print("FINALIZED PROPERTY DESCRIPTION: " + str(description) + "\n\n")
                        # Add the MatterProperty to this device
                        self.properties[property_id] = MatterProperty(
                                        self,
                                        property_id,
                                        description,
                                        value,
                                        attr,
                                        settings)
                    
                                        
                except Exception as ex:
                    if self.DEBUG:
                        print("Device: error in generating property: " + str(ex))
                    
            
            # Add Data Mute if relevant. Add is as the last property, so it shows up last in the UI
            if add_data_mute:
                if not 'data_mute' in self.properties:
                    self.properties['data_mute'] = MatterProperty(
                                    self,
                                    "data_mute",
                                    {
                                        'title': "Data mute",
                                        'readOnly': False,
                                        'type': 'boolean'
                                    },
                                    self.data_mute,
                                    {'attribute_id':'data_mute'})
               

            # Update device title
            
            try:
                better_title = ""
                if 'product_name' in self.adapter.persistent_data['nodez'][device_id]:
                    better_title = str(self.adapter.persistent_data['nodez'][device_id]['product_name'])
                    
                    #if 'vendor_name' in self.adapter.persistent_data['nodez'][device_id]:
                    #    better_title = str(self.adapter.persistent_data['nodez'][device_id]['vendor_name']) + " " + better_title
                    
                if len(better_title) > 5:
                    self.title = better_title
                    
            except Exception as ex:
                print("Error generating better device title")

 
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


