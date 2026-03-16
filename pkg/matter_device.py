
import re
from gateway_addon import Device, Action
from .matter_property import MatterProperty

from .matter_util import xy_to_hex, uncamel
#from matter_server.common.helpers.util import dataclass_from_dict,dataclass_to_dict,create_attribute_path_from_attribute
#from matter_server.common.helpers.util import create_attribute_path_from_attribute


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
        self.description = 'A Matter device'
        self._type = [] # holds capacilities
        
        # Improve device title
        try:
            better_title = ""
            if 'attributes_list' in node:
                
                for endpoint_name in node['attributes_list']:
                    if 'BasicInformation.Attributes.ProductName' in node['attributes_list'][endpoint_name]:
                        better_title = str(node['attributes_list'][endpoint_name]['BasicInformation.Attributes.ProductName'])
                
                    if len(better_title) < 5 and 'BasicInformation.Attributes.VendorName' in node['attributes_list'][endpoint_name]:
                        better_title = str(node['attributes_list'][endpoint_name]['BasicInformation.Attributes.VendorName'])
                    
                    if len(better_title) > 5:
                        self.title = better_title
        except Exception as ex:
            print("device: caught error generating better device title: ", ex)
        
        self.node = node
        self.node_id = node['node_id']
        self.data_mute = False
        
        # Only save actually useful attribute data in the persistent data.
        if not device_id in list(self.adapter.persistent_data['nodez'].keys()):
            self.adapter.persistent_data['nodez'][device_id] = {
                                                        'node_id':node['node_id'],
                                                        'attributes':{},
                                                    }
            self.adapter.should_save = True
        
        
        self.update_from_node(node)
        
    
    def reparse_node(self):
        if self.DEBUG:
            print("Device: in reparse_node")
        if self.node:
            self.update_from_node(self.node)
            return True
        return False
            
    def update_from_node(self, node):
        if self.DEBUG:
            print("Device: in update_from_node")
        device_id = self.id
        
        # TODO: if this is a complete node, then self.node should be updated with it
        
        try:
            
            supported_attributes = {
                "BasicInformation.Attributes.VendorName":{'readOnly':True, 'type':'string'},    # Vendor name
                "BasicInformation.Attributes.ProductName":{'readOnly':True, 'type':'string'},   # Product name
                "BasicInformation.Attributes.UniqueID":{'readOnly':True, 'type':'string'},      # Unique ID
                "BasicInformation.Attributes.HardwareVersionString":{'readOnly':True, 'type':'string'}, # Hardware version string
                "BasicInformation.Attributes.SoftwareVersionString":{'readOnly':True, 'type':'string'}, # Software version string
                
                "OnOff.Attributes.OnOff":{
                    'title':'State',
                    'readOnly': False, 
                    'type':'boolean', 
                    '@type':'OnOffProperty', 
                    'dev@type':'OnOffSwitch'}, # state
                    
                "PowerSource.Attributes.BatPercentRemaining":{
                    'title':'Battery level',
                    'readOnly': True,
                    'percent':True,
                    'type':'integer'},
                "PowerSource.Attributes.BatReplacementNeeded":{
                    'title':'Replace battery',
                    'readOnly': True, 
                    'type':'boolean'},
                    
                "Switch.Attributes.CurrentPosition":{
                    'readOnly': True,
                    'type':'integer'},
                    
                "BooleanState.Attributes.StateValue":{
                    'title':'State',
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
                    'title':'Humidity',
                    'readOnly':True, 
                    'type':'integer', 
                    'percent':True,
                    '@type':'LevelProperty',
                    'dev@type':'MultiLevelSensor'}, # humidity
                "TemperatureMeasurement.Attributes.MeasuredValue":{
                    'readOnly': True,
                    'type': 'number',
                    'multipleOf':0.1,
                    '@type': 'TemperatureProperty',
                    'dev@type':'TemperatureSensor'}, # temperature
                "PressureMeasurement.Attributes.MeasuredValue":{
                    'title':'Pressure',
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
                    'title':'Brightness',
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
                    'title':'Colour',
                    'readOnly': False, 
                    'type':'string', 
                    '@type': 'ColorProperty',
                    'dev@type':'Light'}, # color X coordinate. Y value will be loaded too if this one is an attribute
                "ColorControl.Attributes.ColorTemperatureMireds":{
                    'title':'Colour temperature',
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
            supported_types = list(supported_attributes.keys())
            if self.DEBUG:
                print("all supported_types: " + str(supported_types))
            
            
            # Keep track of capabilities and titles we've used
            used_property_titles = [] # keep track of which property titles have been used already in this device, to avoid doubles.
            used_property_at_types = [] # keep track of which property @types have already been added to the device. Only one per type is allowed.
            
            # Check if it's useful to add DataMute property. If there is a readOnly property, then it is useful.
            add_data_mute = False
            
            # these clusters should theoretically already be parsed out in process_node in matter_util.py
            # This list is manually copied from matter_util.py
            clusters_to_ignore = ['OtaSoftwareUpdateRequestor','AccessControl','Descriptor','IcdManagement','OperationalCredentials','WiFiNetworkDiagnostics','ThreadNetworkDiagnostics','AdministratorCommissioning','NetworkCommissioning','GeneralCommissioning','GroupKeyManagement','Identify','Groups']
            
            # PREPARATION LOOP
            
            # As preparation, loop over the node and make a simple list of all shortened attributes
            if self.DEBUG:
                print("\n\n\n")
            all_short_attributes = {}
            #if 'attributes' in node:
            if 'attributes_list' in node:
                
                if not 'nodez' in self.adapter.persistent_data:
                    self.adapter.persistent_data['nodez'] = {}
                    
                if not device_id in self.adapter.persistent_data['nodez']:
                    self.adapter.persistent_data['nodez'][device_id] = {}
                
                if not 'attributes' in self.adapter.persistent_data['nodez'][device_id]:
                    self.adapter.persistent_data['nodez'][device_id]['attributes'] = {}
                    
                for endpoint_name in list(node['attributes_list'].keys()):
                    if self.DEBUG:
                        print("checking endpoint: ", endpoint_name)
                        
                    if not endpoint_name in self.adapter.persistent_data['nodez'][device_id]['attributes']:
                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name] = {}
                        
                    #for attribute_code in list(node['attributes'].keys()):
                    for attribute_code in list(node['attributes_list'][endpoint_name].keys()):
                    
                        try:
                            should_skip = False
                            for cluster_to_ignore in clusters_to_ignore:
                                if attribute_code.startswith(cluster_to_ignore):
                                    should_skip = True
                                    break
                            if should_skip:
                                if self.DEBUG:
                                    print("\nWARNING, STILL FOUND an attribute_code that is in clusters_to_ignore: ", attribute_code)
                                continue
                    
                            if self.DEBUG:
                                print("attribute_code: ", attribute_code)
                    
                            if not '.Attributes.' in str(attribute_code):
                                if self.DEBUG:
                                    print("\nWARNING, no '.Attributes.' in attribute_code? ", attribute_code)
                                continue
                        
                            if not endpoint_name in self.adapter.persistent_data['nodez'][device_id]['attributes']:
                                if self.DEBUG:
                                    print("adding missing endpoint to persistent data")
                                self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name] = {}
                            
                            #if 'Candle.' in attribute_code:
                                
                                
                            #if ('Candle.' in attribute_code and self.adapter.add_hacky_properties) or (attribute_code in node['attributes_list'][endpoint_name] and isinstance(node['attributes_list'][endpoint_name][attribute_code],(str,int,float,bool)) ):
                            if 'Candle.' in attribute_code or (attribute_code in node['attributes_list'][endpoint_name] and isinstance(node['attributes_list'][endpoint_name][attribute_code],(str,int,float,bool)) ):
                                
                                if not attribute_code in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name]:
                                    if self.DEBUG:
                                        print("adding to persistent_data:  device_id,attribute_code: ", device_id, attribute_code)
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code] = {}
                                    self.adapter.should_save = True
                                
                                if attribute_code in node['attributes_list'][endpoint_name]:
                                    if self.DEBUG:
                                        print("this attribute seems to have a useable simple value: ", node['attributes_list'][endpoint_name][attribute_code])
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['value'] = node['attributes_list'][endpoint_name][attribute_code]
                                    if self.DEBUG:
                                        print("value set to persistent data")
                                
                                if attribute_code in supported_types:
                                    if self.DEBUG:
                                        print("first_loop: nice, this attribute is in supported_types")
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['supported'] = True
                                else:
                                    if self.DEBUG:
                                        print("first_loop: this attribute is NOT in supported_types")
                        
                                if not 'enabled' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]:
                                    if self.DEBUG:
                                        print("adding enabled attribute")
                                    if attribute_code in supported_types and not attribute_code.startswith('BasicInformation'):
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['enabled'] = True
                                    else:
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['enabled'] = False
                                    self.adapter.should_save = True
                                else:
                                    if self.DEBUG:
                                        print("this attribute already has an enabled state: ", self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['enabled'])
                            
                                # GET VENDOR NAME, PRODUCT NAME, AND UNIQUE ID
                        
                                try:
                                    # Save vendor name in nodez dict
                                    if attribute_code in node['attributes_list'][endpoint_name]:
                                        if attribute_code == 'BasicInformation.Attributes.VendorName' and isinstance(node['attributes_list'][endpoint_name][attribute_code],str):
                                            if not 'vendor_name' in self.adapter.persistent_data['nodez'][device_id]:
                                                self.adapter.should_save = True
         
                                            self.adapter.persistent_data['nodez'][device_id]['vendor_name'] = str(node['attributes_list'][endpoint_name][attribute_code])
                                            if self.DEBUG:
                                                print("vendor_name: " + str(self.adapter.persistent_data['nodez'][device_id]['vendor_name']))
                                
         
                                        # Save product name in nodez dict
                                        elif attribute_code == 'BasicInformation.Attributes.ProductName' and isinstance(node['attributes_list'][endpoint_name][attribute_code],str):
                                            if not 'product_name' in self.adapter.persistent_data['nodez'][device_id]:
                                                self.adapter.should_save = True
                                            self.adapter.persistent_data['nodez'][device_id]['product_name'] = str(node['attributes_list'][endpoint_name][attribute_code])
                                            if self.DEBUG:
                                                print("product_name: " + str(self.adapter.persistent_data['nodez'][device_id]['product_name']))
                                
         
                                        # Save unique ID to nodez dict
                                        elif attribute_code == 'BasicInformation.Attributes.UniqueID' and isinstance(node['attributes_list'][endpoint_name][attribute_code],(str,int,float)):
                                            if not 'unique_id' in self.adapter.persistent_data['nodez'][device_id]:
                                                self.adapter.should_save = True
                                            self.adapter.persistent_data['nodez'][device_id]['unique_id'] = str(node['attributes_list'][endpoint_name][attribute_code])
                                            if self.DEBUG:
                                                print("unique_id: " + str(self.adapter.persistent_data['nodez'][device_id]['unique_id']))
                                
         
                                        # Save hardware version to nodez dict
                                        elif attribute_code == 'BasicInformation.Attributes.HardwareVersionString' and isinstance(node['attributes_list'][endpoint_name][attribute_code],str):
                                            if not 'hardware_version' in self.adapter.persistent_data['nodez'][device_id]:
                                                self.adapter.should_save = True
                                            self.adapter.persistent_data['nodez'][device_id]['hardware_version'] = str(node['attributes_list'][endpoint_name][attribute_code])
                                            if self.DEBUG:
                                                print("hardware_version: " + str(self.adapter.persistent_data['nodez'][device_id]['hardware_version']))
                                
 
                                        # Save software version to nodez dict
                                        if attribute_code == 'BasicInformation.Attributes.SoftwareVersionString' and isinstance(node['attributes_list'][endpoint_name][attribute_code],str):
                                            if not 'software_version' in self.adapter.persistent_data['nodez'][device_id]:
                                                self.adapter.should_save = True
                                            self.adapter.persistent_data['nodez'][device_id]['software_version'] = str(node['attributes_list'][endpoint_name][attribute_code])
                                            if self.DEBUG:
                                                print("software_version: " + str(self.adapter.persistent_data['nodez'][device_id]['software_version']))
                                        
 
                                except Exception as ex:
                                    print("caught error extracting BasicInfo: " + str(ex))
                            
                            
                        except Exception as ex:
                            print("caught error doing first loop over attributes: ", ex)
                        
                        
                        
                    
                    
                    if self.DEBUG:
                        print("\n\n\n")
                        print("persistent attributes data: ", self.adapter.persistent_data['nodez'][device_id]['attributes'])
                        print("\n\n\n")
            
                    # MAIN ATTRIBUTES TO PROPERTIES LOOP
            
            
            
                for endpoint_name in list(self.adapter.persistent_data['nodez'][device_id]['attributes'].keys()):
                    # Loop over all the node's attributes and only pay attention to the ones that are important
                    if self.DEBUG:
                        print("endpoint_name again: ", endpoint_name)
                    for attribute_code in list(self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name].keys()):
                        
                        property_value = None
                        
                        try:
                            
                            # If hacky properties are disabled, then stop here
                            if 'hacky' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code] and self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['hacky'] == True and self.adapter.add_hacky_properties == False:
                                if self.DEBUG:
                                    print("skipping hacky attribute because hacky properties are disabled: ", attribute_code)
                                continue
                                
                            
                            # If the attribute is not enabled as a thing property, then stop here
                            if self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['enabled'] == False:
                                if self.DEBUG:
                                    print("skipping attribute that is not enabled.  attribute_code: ", attribute_code)
                                continue
                            
                            
                            
                            if self.DEBUG:
                                print("\n\n+\nattribute_code again: ", attribute_code)
                            
                            short_type = None
                            
                            # For the old style output
                            #attr = node['attributes_list'][endpoint_name][attribute_code] # e.g. "0/29/0"
                            #if self.DEBUG:
                            #    print("Device: checking attribute: " + str(attr))
                        
                            #if isinstance(attr,dict) and not 'attribute_type' in attr:
                            #    if self.DEBUG:
                            #        print("skipping attribute without an 'attribute_type' key")
                                #continue
                        
                            # TODO: setting on a name and remove this switching from 'attribute_code' to 'short_type' here
                        
                            if '.Attributes.' in str(attribute_code):
                                short_type = str(attribute_code)
                            else:
                                if self.DEBUG:
                                    print("no .Attributes. in attribute_code?")
                                continue
                        
                            # For the old style output
                            #if short_type == None and isinstance(attr,dict) and 'attribute_type' in attr:
                            #    type_list = str(attr['attribute_type']).split('.')
                            #    short_type = type_list[-3] + "." + type_list[-2] + "." + type_list[-1]
                            #    if self.DEBUG:
                            #        print("Device: old short type: " + str(short_type))
                    
                            
                            if self.DEBUG:
                                print("Device: final short_type: ", short_type)
                            
                            if isinstance(short_type,str) and '.Attributes.' in short_type:
                                
                                try:
                                    if attribute_code in node['attributes_list'][endpoint_name]:
                                        
                                        # TODO: technically the value has already been placed in the persistent data in the first loop over all the attributes
                                        # and with the hacky properties, this is even more relevant, since those ONLY have a value in persistent data, and never in node data
                                        
                                        if isinstance(node['attributes_list'][endpoint_name][attribute_code],(str,int,float,bool)):
                                            #self.adapter.persistent_data['nodez'][device_id]['attributes'][underscored_property_name] = node['attributes_list'][short_type]
                                            property_value = node['attributes_list'][endpoint_name][attribute_code]
                                             
                                        #elif isinstance(node['attributes_list'][endpoint_name][attribute_code],dict) and 'value' in node['attributes_list'][endpoint_name][attribute_code]:
                                        #    #self.adapter.persistent_data['nodez'][device_id]['attributes'][underscored_property_name] = attr['value']
                                        #    property_value = attr['value']
                                    
                                        else:
                                            if self.DEBUG:
                                                print("Value fell through (probably an array).  node['attributes_list'][short_type]: ", node['attributes_list'][endpoint_name][attribute_code])
                                        
                                    # Could be a value from a hacky attribute, which would not exist in the node dict
                                    elif 'value' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]:
                                        property_value = self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['value']
                                    
                                    if self.DEBUG:
                                        print("property_value for attribute_code: ", attribute_code, property_value)
                                    
                                    #if value != None:
                                    #self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['value'] = value
                                
                                
                                    
                                except Exception as ex:
                                    if self.DEBUG:
                                        print("device: caught error extracting value: " + str(ex))
                                
                                
                                cluster_name = str(short_type.split('.Attributes.')[0])
                                attribute_name = str(short_type.split('.Attributes.')[1])
                                property_id = 'property-' + endpoint_name + '-' + cluster_name + '-' + attribute_name
                                property_title = uncamel(attribute_name).replace('_',' ')
                                if self.DEBUG:
                                    print("- cluster_name: ", cluster_name)
                                    print("- attribute_name: ", attribute_name)
                                    print("- early property_title: ", property_title)
                                    
                                if not 'property' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]:
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property'] = {'short_type':short_type, 'id':property_id, 'cluster_name':cluster_name, 'attribute_name':attribute_name}
                                    self.adapter.should_save = True
                                    
                                if not 'id' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']:
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['id'] = property_id
                                    self.adapter.should_save = True
                                    
                                underscored_property_name = uncamel(attribute_name)
                                
                                if underscored_property_name.startswith('bat_'):
                                    underscored_property_name = underscored_property_name.replace('bat_','battery_')
                                
                                if self.DEBUG:
                                    print("property_id: ", property_id)
                                    print("underscored_property_name: ", underscored_property_name)
                                    
                                
                                
                    
                                
                    
                                # GENERATE TITLE
                                
                                
                                try:
                                    if not 'title' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']:
                                        property_title = underscored_property_name.replace("_string","")
                                        property_title = property_title.capitalize()
                                        property_title = property_title.replace('_',' ')
                                        if self.DEBUG:
                                            print("raw property_title: " + str(property_title))
                                        if short_type in supported_attributes and 'title' in supported_attributes[short_type].keys():
                                            property_title = str(supported_attributes[short_type]['title'])
                                    
                                        elif attribute_name == 'OnOff':
                                            property_title = 'State'
                                            
                                        elif attribute_name == 'CurrentPosition' and short_type.startswith('Switch'):
                                            property_title = 'State'
                                    
                                        elif attribute_name == 'MeasuredValue':
                                            property_title = cluster_name.replace('Measurement','')
                                            property_title = uncamel(property_title).replace('_',' ')
                                    
                                    
                                        if self.DEBUG:
                                            print("nicer property_title: " + str(property_title))
                                        try:
                                            # Make sure the property title is unique
                                            if not property_title in used_property_titles:
                                                used_property_titles.append(property_title)
                                            else:
                                                if self.DEBUG:
                                                    print("WARNING, property title was already used: ", property_title)
                                                
                                                title_with_endpoint_number = property_title + ' ' + str(endpoint_name).replace('Endpoint','')
                                                if not title_with_endpoint_number in used_property_titles:
                                                    property_title = title_with_endpoint_number
                                                    used_property_title.append(title_with_endpoint_number)
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
                                            print("ERROR: device: caught error finding a good property title: " + str(ex))
                                    
                                        if self.DEBUG:
                                            print("Final property title: ", attribute_code, property_title)
                                        
                                        # An error here should be impossible.. but you never know.
                                        if not endpoint_name in self.adapter.persistent_data['nodez'][device_id]['attributes']:
                                            if self.DEBUG:
                                                print("ERROR, fixing missing endpoint in persistent data?: ", device_id, endpoint_name)
                                            self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name] = {}
                                        if not attribute_code in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name]:
                                            if self.DEBUG:
                                                print("ERROR, fixing missing attribute_code in persistent data?: ", device_id, attribute_code)
                                            self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name] = {}
                                        if not 'property' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]:
                                            if self.DEBUG:
                                                print("\n\nERROR, missing 'property' in persistent data?: ", device_id, attribute_code)
                                            continue
                                            #self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name]['property'] = {'enabled':False}
                                            
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['title'] = str(property_title)
                                except Exception as ex:
                                    if self.DEBUG:
                                        print("device: caught error wrangling title: " + str(ex))
                                    
                                    
                                
                                
                    
                    
                                    
                    
                                # WEBTHINGS PROPERTY DESCRIPTION AND @-TYPES
                                try:
                                    if not 'description' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']:
                                        # Basic property description
                                        description = {}
                                    
                                        description['title'] = str(property_title)
                                        description['description'] = 'A Matter device'
                                        if short_type in supported_attributes:
                                            if 'type' in supported_attributes[short_type]:
                                                description['type'] = supported_attributes[short_type]['type']
                                            if 'readOnly' in supported_attributes[short_type]:
                                                description['readOnly'] = supported_attributes[short_type]['readOnly']
                                    
                                            # Percentage shortcut, can be overwritten later on
                                            if 'percent' in short_type.lower() or ('percent' in supported_attributes[short_type] and supported_attributes[short_type]['percent'] == True): # This is always True the case if the attribute exists...
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
                                            
                                    
                                        elif 'percent' in short_type.lower(): # This is always True the case if the attribute exists...
                                            description['type'] = 'number'
                                            description['multipleOf'] = 1
                                            description['minimum'] = 0
                                            description['maximum'] = 100
                                            description['unit'] = 'percent'
                                        
                                        if not 'type' in description:
                                            if isinstance(property_value,int):
                                                description['type'] = 'number'
                                            elif isinstance(property_value,str):
                                                description['type'] = 'string'
                                            elif isinstance(property_value,bool):
                                                description['type'] = 'boolean'
                                            else:
                                                if self.DEBUG:
                                                    print("\nERROR, getting description type from value itsel fell through. Will fall back to using 'string'")
                                        
                                        if not 'type' in description:
                                            description['type'] = 'string'
                                            
                                        # TODO: does the controller automatically add forms?
                                        #description["forms"] = [{"href": "properties/" + str(property_id)}]
                    
                                        # ADD CAPABILITES
                    
                                        if self.DEBUG:
                                            print("initial new description: ", short_type, description)
                    
                                        def add_device_capability():
                                            try:
                                                if self.DEBUG:
                                                    print("in add_device_capability. supported_attributes[short_type]: " + str(supported_attributes[short_type]))
                                                if short_type in supported_attributes:
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
                                                
                                                
                                                elif 'percent' in short_type.lower() and short_type != 'BatPercentRemaining':
                                                    description['@type'] = 'LevelProperty'
                                                
                                                    #if not supported_attributes[short_type]['dev@type'] in self._type:
                                                    
                                            except Exception as ex:
                                                print("Device: error in add_device_capability: " + str(ex))
                    
                                        # Add these attributes to each MatterProperty object
                                        #settings = {'short_type':short_type}
                                
                                    
                                
                                        # Add optional capabilities
                                        add_device_capability()
                    
                    
                    
                                        # OPTMIZE VALUES
                    
                                        #value = attr['value']
                    
                                        # COLOR 
                                        try:
                                            # Turn XY Color in HEX color when parsing the X color
                                            if short_type == 'ColorControl.Attributes.CurrentX' and 'ColorControl.Attributes.CurrentY' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name]:
                                                # Get Y value too
                                                color_y_value = node['attributes_list'][endpoint_name]['ColorControl.Attributes.CurrentY']
                                                if self.DEBUG:
                                                    print("color x: " + str(property_value) + ", y: " + str(color_y_value))
                        
                                                # TODO: in one line, theoretically:
                                                # color_y_value = node['attributes'][ all_short_attributes['ColorControl.Attributes.CurrentY'] ]['value']
                        
                                                # calculate hex string
                                                property_value = xy_to_hex(property_value,color_y_value)
                        
                                                #chip.clusters.Objects.ColorControl.Attributes.CurrentY
                        
                                            # Override minimum and maximum mireds according to provided data
                                            if short_type == 'ColorControl.Attributes.ColorTemperatureMireds':
                                                if 'ColorControl.Attributes.ColorTempPhysicalMinMireds' in node['attributes_list'][endpoint_name] and 'ColorControl.Attributes.ColorTempPhysicalMaxMireds' in node['attributes_list'][endpoint_name]:
                                                    if isinstance(node['attributes_list'][endpoint_name]['ColorControl.Attributes.ColorTempPhysicalMinMireds'],int) and isinstance(node['attributes_list'][endpoint_name]['ColorControl.Attributes.ColorTempPhysicalMaxMireds'],int):
                                                        description['minimum'] = node['attributes_list'][endpoint_name]['ColorControl.Attributes.ColorTempPhysicalMinMireds']
                                                        description['maximum'] = node['attributes_list'][endpoint_name]['ColorControl.Attributes.ColorTempPhysicalMaxMireds']
                                
                                        except Exception as ex:
                                            print("Device: error optimizing color value: " + str(ex))
                                    
                                    
                                        # Add some values that are needed to communicate back to the Matter network in matter_property.py
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['endpoint'] = int(endpoint_name.replace('Endpoint',''))
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['node_id'] = self.node_id
                                    
                                    
                                        # Finally, add the initial version of the thing description into the persistent data
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description'] = description
                                        
                                except Exception as ex:
                                    print("caught error creating description for property to place in persistent storage: ", ex)
                                    
                                    
                                try:
                                
                                    # If readOnly properties are present, then enable data mute
                                    if 'readOnly' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description'] and bool(self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['readOnly']) == True:
                                        add_data_mute = True
                                    
                                    # ADD PROPERTY
                                    if self.DEBUG:
                                        print("CREATING PROPERTY FROM: " + str(self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']) + "\n\n")
                                        print("-- with value: ", property_value)
                                    # Add the MatterProperty to this device
                                
                                    if not property_id in self.properties:
                                        if 'type' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']:
                                            self.properties[property_id] = MatterProperty(
                                                        self,
                                                        str(property_id),
                                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description'].copy(),
                                                        property_value,
                                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property'].copy())
                                        else:
                                            if self.DEBUG:
                                                print("\nERROR, almost created thing with missing type in description: ", property_id, self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property'])
                                
                                    elif isinstance(property_value,(str,int,float,bool)):
                                        if self.DEBUG:
                                            print("update_from_node: that property already exists, but will attempt to update its value to: ", property_value)
                                    
                                        try:
                                            target_property = self.find_property(str(property_id))
    
                                            if target_property:
                                                target_property.update(property_value)
                                        except Exception as ex:
                                            print("caught error trying to upate property_value: ", ex)
                                    else:
                                        if self.DEBUG:
                                            print("\nWARNING: update_from_node: that property already exists, but the property_value was an unexpected type: ", property_id, property_value)
                                    
                                except Exception as ex:
                                    print("caught error creating or updating property: ", ex)
                                
                                    
                    
                                        
                        except Exception as ex:
                            if self.DEBUG:
                                print("Device: error in generating property: " + str(ex))
                    
            else:
                if self.DEBUG:
                    print("Device: error no attributes in node?: ", node)
                    
            # Add Data Mute if relevant. Add it as the last property, so it shows up last in the UI
            if add_data_mute:
                if not 'data_mute' in self.properties:
                    self.properties['data_mute'] = MatterProperty(
                                    self,
                                    "data_mute",
                                    {
                                        'title':'Data mute',
                                        'readOnly': False,
                                        'type': 'boolean'
                                    },
                                    self.data_mute, # True or False
                                    {'id':'data_mute','title': "Data mute"})
               


            
        except Exception as ex:
            if self.DEBUG:
                print("caught general error adding properties to thing: " + str(ex))

        if self.DEBUG:
            print("thing has been created.")

