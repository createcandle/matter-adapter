
import re
from gateway_addon import Device, Action
from .matter_property import MatterProperty

from .matter_util import xy_to_hex, uncamel
#from matter_server.common.helpers.util import dataclass_from_dict,dataclass_to_dict,create_attribute_path_from_attribute
#from matter_server.common.helpers.util import create_attribute_path_from_attribute

import chip.clusters.Objects as cluster_details



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
        self._type = [] # holds capabilities
        
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
                'BasicInformation.Attributes.VendorName':{'readOnly':True, 'type':'string'},    # Vendor name
                'BasicInformation.Attributes.ProductName':{'readOnly':True, 'type':'string'},   # Product name
                'BasicInformation.Attributes.UniqueID':{'readOnly':True, 'type':'string'},      # Unique ID
                'BasicInformation.Attributes.HardwareVersionString':{'readOnly':True, 'type':'string'}, # Hardware version string
                'BasicInformation.Attributes.SoftwareVersionString':{'readOnly':True, 'type':'string'}, # Software version string
                
                'OnOff.Attributes.OnOff':{
                    'title':'State',
                    'readOnly': False, 
                    'type':'boolean', 
                    '@type':'OnOffProperty', 
                    'dev@type':'OnOffSwitch'}, # state
                    
                'PowerSource.Attributes.BatPercentRemaining':{
                    'title':'Battery level',
                    'readOnly': True,
                    'percent':True,
                    'type':'integer'},
                'PowerSource.Attributes.BatReplacementNeeded':{
                    'title':'Replace battery',
                    'readOnly': True, 
                    'type':'boolean'},
                    
                'Switch.Attributes.CurrentPosition':{
                    'readOnly': True,
                    'type':'integer'},
                    
                'BooleanState.Attributes.StateValue':{
                    'title':'State',
                    'readOnly': True, 
                    'type':'boolean',
                    '@type':'BooleanProperty', 
                    'dev@type':'BinarySensor'}, # readOnly state
                
                'RelativeHumidityMeasurement.Attributes.MeasuredValue':{
                    'title':'Humidity',
                    'readOnly':True, 
                    'type':'integer', 
                    'percent':True,
                    '@type':'LevelProperty',
                    'dev@type':'MultiLevelSensor'}, # humidity
                'TemperatureMeasurement.Attributes.MeasuredValue':{
                    'readOnly': True,
                    'type': 'number',
                    'multipleOf':0.1,
                    '@type': 'TemperatureProperty',
                    'dev@type':'TemperatureSensor'}, # temperature
                'PressureMeasurement.Attributes.MeasuredValue':{
                    'title':'Pressure',
                    'readOnly': True,
                    'type': 'number',
                    'multipleOf':0.1,
                    '@type': 'BarometricPressureProperty',
                    'dev@type': 'BarometricPressureSensor'}, # pressure
                'FlowMeasurement.Attributes.MeasuredValue':{
                    'readOnly':True, 
                    'type':'number',
                    'multipleOf':0.1,
                    '@type':'LevelProperty',
                    'dev@type':'MultiLevelSensor'}, # flow
                'IlluminanceMeasurement.Attributes.MeasuredValue':{
                    'readOnly':True, 
                    'type':'integer',
                    'multipleOf':1,
                    '@type':'LevelProperty',
                    'dev@type':'MultiLevelSensor'}, # illuminance
                    
                'LevelControl.Attributes.CurrentLevel':{
                    'title':'Brightness',
                    'readOnly': False, 
                    'type':'integer', 
                    'percent':True, 
                    '@type':'BrightnessProperty',
                    'dev@type':'Light'}, # light brightness
                    
                'ColorControl.Attributes.ColorMode':{
                    'readOnly': False, 
                    'type':'string', 
                    '@type': 'ColorProperty',
                    'dev@type':'Light'}, # light color
                'ColorControl.Attributes.CurrentX':{
                    'title':'Color',
                    'readOnly': False, 
                    'type':'string', 
                    '@type': 'ColorProperty',
                    'dev@type':'Light'}, # color X coordinate. Y value will be loaded too if this one is an attribute
                'ColorControl.Attributes.ColorTemperatureMireds':{
                    'title':'Color temperature',
                    'readOnly': False, 
                    'type':'integer', 
                    'minimum':3000, 
                    'maximum':7000, 
                    '@type': 'ColorTemperatureProperty', 
                    'dev@type':'Light'}, # Color temperature (in Mireds)
                
                
                
                #'OccupancySensing.Attributes.Occupancy':{
                #    'readOnly': True, 
                #    'type':'boolean',
                #    '@type': 'MotionProperty',
                #    'dev@type':'MotionSensor'}, # occupancy
                'OccupancySensing.Attributes.Occupancy':{
                    'title':'Occupancy',
                    'readOnly': True, 
                    'type':'boolean', 
                    '@type': 'OccupiedProperty', 
                    'dev@type':'OccupancySensor'},
                
                'OccupancySensing.Attributes.OccupancySensorTypeEnum':{
                    'title':'Sensor type',
                    'readOnly': True,
                    'type':'string',
                    'enum':['PIR','Ultrasonic','PIRAndUltrasonic','PhysicalContact']},
                    
                'SmokeCOAlarm.Attributes.AlarmStateEnum':{
                    'readOnly': True,
                    'type':'string',
                    'enum':['Normal','Warning','Critical']},
                'SmokeCOAlarm.Attributes.SensitivityEnum':{
                    'title':'Sensitivity',
                    'readOnly': True, 
                    'type':'string',
                    'enum':['High','Standard','Low']},
                
                #'SmokeCOAlarm.Attributes.FeatureMap':{
                #    'title':'Type',
                #    'readOnly': True, 
                #    'type':'string',
                #    'enum':['SmokeAlarm','COAlarm']},
                'SmokeCOAlarm.Attributes.ExpressedStateEnum':{
                    'title':'Status',
                    'readOnly':True,
                    'type':'string',
                    'enum':['Normal','SmokeAlarm','COAlarm','BatteryAlert','Testing','HardwareFault','EndOfService','InterconnectSmoke','InterconnectCO']},
                'SmokeCOAlarm.Attributes.ContaminationStateEnum':{
                    'title':'Contamination state',
                    'readOnly': True, 
                    'type':'string',
                    'enum':['Normal','Low','Warning','Critical']},
                
                
                    
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
                                print("\nattribute_code: ", attribute_code)
                    
                            if not '.Attributes.' in str(attribute_code):
                                if self.DEBUG:
                                    print("\nWARNING, no '.Attributes.' in attribute_code? ", attribute_code)
                                continue
                        
                            attribute_name = str(attribute_code.split('.Attributes.')[1])
                            
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
                                        print("  this attribute seems to have a useable simple value: ", node['attributes_list'][endpoint_name][attribute_code])
                                    early_value = node['attributes_list'][endpoint_name][attribute_code]
                                    if attribute_name in self.adapter.enums_lookup:
                                        if self.DEBUG:
                                            print("  enum available: ", attribute_name, self.adapter.enums_lookup[attribute_name])
                                        
                                        if isinstance(early_value,int) and early_value >=0 and early_value < len(self.adapter.enums_lookup[attribute_name]):
                                            early_value = self.adapter.enums_lookup[attribute_name][early_value]
                                            if self.DEBUG:
                                                print("  early switch of property value from number to string from enums_lookup: ", early_value)
                                    
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['value'] = early_value
                                    #if self.DEBUG:
                                    #    print("value set to persistent data")
                                
                                if attribute_code in supported_types:
                                    if self.DEBUG:
                                        print("  first_loop: nice, this attribute is in supported_types")
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['supported'] = True
                                #else:
                                #    if self.DEBUG:
                                #        print("first_loop: this attribute is NOT in supported_types")
                        
                                if not 'enabled' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]:
                                    if self.DEBUG:
                                        print("  adding enabled attribute")
                                    if attribute_code in supported_types and not attribute_code.startswith('BasicInformation'):
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['enabled'] = True
                                    else:
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['enabled'] = False
                                    self.adapter.should_save = True
                                #else:
                                #    if self.DEBUG:
                                #        print("this attribute already has an enabled state: ", self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['enabled'])
                            
                                # GET VENDOR NAME, PRODUCT NAME, AND UNIQUE ID
                        
                                try:
                                    # Save vendor name in nodez dict
                                    if attribute_code in node['attributes_list'][endpoint_name]:
                                        if attribute_code == 'BasicInformation.Attributes.VendorName' and isinstance(node['attributes_list'][endpoint_name][attribute_code],str):
                                            if not 'vendor_name' in self.adapter.persistent_data['nodez'][device_id]:
                                                self.adapter.should_save = True
         
                                            self.adapter.persistent_data['nodez'][device_id]['vendor_name'] = str(node['attributes_list'][endpoint_name][attribute_code])
                                            if self.DEBUG:
                                                print("  vendor_name: " + str(self.adapter.persistent_data['nodez'][device_id]['vendor_name']))
                                
         
                                        # Save product name in nodez dict
                                        elif attribute_code == 'BasicInformation.Attributes.ProductName' and isinstance(node['attributes_list'][endpoint_name][attribute_code],str):
                                            if not 'product_name' in self.adapter.persistent_data['nodez'][device_id]:
                                                self.adapter.should_save = True
                                            self.adapter.persistent_data['nodez'][device_id]['product_name'] = str(node['attributes_list'][endpoint_name][attribute_code])
                                            if self.DEBUG:
                                                print("  product_name: " + str(self.adapter.persistent_data['nodez'][device_id]['product_name']))
                                
         
                                        # Save unique ID to nodez dict
                                        elif attribute_code == 'BasicInformation.Attributes.UniqueID' and isinstance(node['attributes_list'][endpoint_name][attribute_code],(str,int,float)):
                                            if not 'unique_id' in self.adapter.persistent_data['nodez'][device_id]:
                                                self.adapter.should_save = True
                                            self.adapter.persistent_data['nodez'][device_id]['unique_id'] = str(node['attributes_list'][endpoint_name][attribute_code])
                                            if self.DEBUG:
                                                print("  unique_id: " + str(self.adapter.persistent_data['nodez'][device_id]['unique_id']))
                                
         
                                        # Save hardware version to nodez dict
                                        elif attribute_code == 'BasicInformation.Attributes.HardwareVersionString' and isinstance(node['attributes_list'][endpoint_name][attribute_code],str):
                                            if not 'hardware_version' in self.adapter.persistent_data['nodez'][device_id]:
                                                self.adapter.should_save = True
                                            self.adapter.persistent_data['nodez'][device_id]['hardware_version'] = str(node['attributes_list'][endpoint_name][attribute_code])
                                            if self.DEBUG:
                                                print("  hardware_version: " + str(self.adapter.persistent_data['nodez'][device_id]['hardware_version']))
                                
 
                                        # Save software version to nodez dict
                                        if attribute_code == 'BasicInformation.Attributes.SoftwareVersionString' and isinstance(node['attributes_list'][endpoint_name][attribute_code],str):
                                            if not 'software_version' in self.adapter.persistent_data['nodez'][device_id]:
                                                self.adapter.should_save = True
                                            self.adapter.persistent_data['nodez'][device_id]['software_version'] = str(node['attributes_list'][endpoint_name][attribute_code])
                                            if self.DEBUG:
                                                print("  software_version: " + str(self.adapter.persistent_data['nodez'][device_id]['software_version']))
                                        
 
                                except Exception as ex:
                                    print("\ncaught error extracting BasicInfo: " + str(ex))
                            
                            
                        except Exception as ex:
                            print("\ncaught error doing first loop over attributes: ", ex)
                        
                        
                        
                    
                    
                    #if self.DEBUG:
                    #    print("\n\n\n")
                    #    print("persistent attributes data: ", self.adapter.persistent_data['nodez'][device_id]['attributes'])
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
                            
                            
                            
                            # For the old style output
                            #attr = node['attributes_list'][endpoint_name][attribute_code] # e.g. "0/29/0"
                            #if self.DEBUG:
                            #    print("Device: checking attribute: " + str(attr))
                        
                            #if isinstance(attr,dict) and not 'attribute_type' in attr:
                            #    if self.DEBUG:
                            #        print("skipping attribute without an 'attribute_type' key")
                                #continue
                        
                            # TODO: setting on a name and remove this switching from 'attribute_code' to 'attribute_code' here
                        
                            if not '.Attributes.' in str(attribute_code):
                                if self.DEBUG:
                                    print("\n\nERROR, no .Attributes. in attribute_code?: ", attribute_code)
                                continue
                        
                            # For the old style output
                            #if attribute_code == None and isinstance(attr,dict) and 'attribute_type' in attr:
                            #    type_list = str(attr['attribute_type']).split('.')
                            #    attribute_code = type_list[-3] + "." + type_list[-2] + "." + type_list[-1]
                            #    if self.DEBUG:
                            #        print("Device: old short type: " + str(attribute_code))
                    
                            
                            if self.DEBUG:
                                print("Device: final attribute_code: ", attribute_code)
                                
                                
                            try:
                                if attribute_code in node['attributes_list'][endpoint_name]:
                                    
                                    # TODO: technically the value has already been placed in the persistent data in the first loop over all the attributes
                                    # and with the hacky properties, this is even more relevant, since those ONLY have a value in persistent data, and never in node data
                                    
                                    if isinstance(node['attributes_list'][endpoint_name][attribute_code],(str,int,float,bool)):
                                        #self.adapter.persistent_data['nodez'][device_id]['attributes'][underscored_property_name] = node['attributes_list'][attribute_code]
                                        property_value = node['attributes_list'][endpoint_name][attribute_code]
                                         
                                    #elif isinstance(node['attributes_list'][endpoint_name][attribute_code],dict) and 'value' in node['attributes_list'][endpoint_name][attribute_code]:
                                    #    #self.adapter.persistent_data['nodez'][device_id]['attributes'][underscored_property_name] = attr['value']
                                    #    property_value = attr['value']
                                
                                    else:
                                        if self.DEBUG:
                                            print("Value fell through (probably an array).  node['attributes_list'][attribute_code]: ", node['attributes_list'][endpoint_name][attribute_code])
                                    
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
                            
                            
                            cluster_name = str(attribute_code.split('.Attributes.')[0])
                            attribute_name = str(attribute_code.split('.Attributes.')[1])
                            property_id = 'property-' + endpoint_name + '-' + cluster_name + '-' + attribute_name
                            property_title = uncamel(attribute_name).replace('_',' ')
                            if self.DEBUG:
                                print("- cluster_name: ", cluster_name)
                                print("- attribute_name: ", attribute_name)
                                print("- early property_title: ", property_title)
                                
                            if not 'property' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]:
                                self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property'] = {'attribute_code':attribute_code, 'id':property_id, 'cluster_name':cluster_name, 'attribute_name':attribute_name, '@type':[]}
                                self.adapter.should_save = True
                                
                            if not 'id' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']:
                                self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['id'] = property_id
                                self.adapter.should_save = True
                                
                            if not '@type' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']:
                                self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type'] = []
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
                                    property_title = str(underscored_property_name).replace("_string","")
                                    property_title = property_title.replace("_enum","")
                                    property_title = property_title.capitalize()
                                    property_title = property_title.replace('_',' ')
                                    if self.DEBUG:
                                        print("raw property_title: " + str(property_title))
                                    if attribute_code in supported_attributes and 'title' in supported_attributes[attribute_code].keys():
                                        property_title = str(supported_attributes[attribute_code]['title'])
                                
                                    elif attribute_name == 'OnOff':
                                        property_title = 'State'
                                        
                                    elif attribute_name == 'CurrentPosition' and attribute_code.startswith('Switch'):
                                        property_title = 'State'
                                
                                    elif attribute_name == 'MeasuredValue':
                                        property_title = cluster_name.replace('Measurement','')
                                        property_title = uncamel(property_title).replace('_',' ')
                                
                                
                                    if self.DEBUG:
                                        print("nicer property_title: " + str(property_title))
                                    
                                    # Make sure the property title is unique
                                    try:
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
                                            print("\nERROR, fixing missing endpoint in persistent data?: ", device_id, endpoint_name)
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name] = {}
                                    if not attribute_code in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name]:
                                        if self.DEBUG:
                                            print("\nERROR, fixing missing attribute_code in persistent data?: ", device_id, attribute_code)
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
                                    if attribute_code in supported_attributes:
                                        if 'type' in supported_attributes[attribute_code]:
                                            description['type'] = supported_attributes[attribute_code]['type']
                                        if 'readOnly' in supported_attributes[attribute_code]:
                                            description['readOnly'] = supported_attributes[attribute_code]['readOnly']
                                
                                        # Percentage shortcut, can be overwritten later on
                                        if 'percent' in attribute_code.lower() or ('percent' in supported_attributes[attribute_code] and supported_attributes[attribute_code]['percent'] == True): # This is always True the case if the attribute exists...
                                            description['multipleOf'] = 1
                                            description['minimum'] = 0
                                            description['maximum'] = 100
                                            description['unit'] = 'percent'
                            
                                        # MultipleOf
                                        if 'multipleOf' in supported_attributes[attribute_code]:
                                            description['multipleOf'] = supported_attributes[attribute_code]['multipleOf']
                
                                        # Minimum and maximum number/integer limits
                                        if 'minimum' in supported_attributes[attribute_code]:
                                            description['minimum'] = supported_attributes[attribute_code]['minimum']
                                        if 'maximum' in supported_attributes[attribute_code]:
                                            description['maximum'] = supported_attributes[attribute_code]['maximum']
                                        
                                
                                    elif 'percent' in attribute_code.lower(): # This is always True the case if the attribute exists...
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
                                        print("initial new description: ", attribute_code, description)
                
                                    def add_device_capability():
                                        try:
                                            if self.DEBUG:
                                                print("in add_device_capability. supported_attributes[attribute_code]: " + str(supported_attributes[attribute_code]))
                                            if attribute_code in supported_attributes:
                                                if '@type' in supported_attributes[attribute_code]:
                                                    if supported_attributes[attribute_code]['@type'] not in used_property_at_types:
                                                        description['@type'] = supported_attributes[attribute_code]['@type']
                                                        used_property_at_types.append(description['@type'])
                            
                                                # Theoretically it would be nicer to check if ALL required properies for the dev@type exist. Also, currenty there is a tiny chance that the dev@type is never set
                                                if 'dev@type' in supported_attributes[attribute_code]:
                                                    if not supported_attributes[attribute_code]['dev@type'] in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type']:
                                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type'].append( supported_attributes[attribute_code]['dev@type'] )
                                                    
                                                    if not supported_attributes[attribute_code]['dev@type'] in self._type:
                                                        #self._type.append( supported_attributes[attribute_code]['dev@type'] )
                                                        if self.DEBUG:
                                                            print("add new capability: " + str(supported_attributes[attribute_code]['dev@type']))
                                                    else:
                                                        if self.DEBUG:
                                                            print("capability already existed: " + str(supported_attributes[attribute_code]['dev@type']))
                                                
                                            
                                            elif 'percent' in attribute_code.lower() and attribute_code != 'BatPercentRemaining':
                                                description['@type'] = 'LevelProperty'
                                                
                                                # TODO:
                                                # It would be useful to then also add either 'MultiLevelSensor' or 'MultiLevelSwitch' to the dev@type. But for that we need to know if this is a read-only or read-write cluster/attribute
                                                
                                                #if not supported_attributes[attribute_code]['dev@type'] in self._type:
                                                
                                        except Exception as ex:
                                            print("Device: error in add_device_capability: " + str(ex))
                
                                    # Add these attributes to each MatterProperty object
                                    #settings = {'attribute_code':attribute_code}
                            
                                
                            
                                    # Add optional capabilities
                                    add_device_capability()
                
                
                                    
                                    # Add some more capabilities by checking matter attributes
                                    
                                    
                
                
                
                
                
                                    # OPTMIZE VALUES
                
                                    #value = attr['value']
                
                                    # COLOR 
                                    try:
                                        # Turn XY Color in HEX color when parsing the X color
                                        if attribute_code == 'ColorControl.Attributes.CurrentX' and 'ColorControl.Attributes.CurrentY' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name]:
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
                                        if attribute_code == 'ColorControl.Attributes.ColorTemperatureMireds':
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
                                # already handled earlier
                                #if not '@type' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']:
                                #    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type'] = []
                                if not 'property' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]:
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property'] = {}
                                if not 'dev@type' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']:
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type'] = []
                                if not 'description' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']:
                                    print("ERROR, still missing description in property in persistent data. Aborting.")
                                    break
                                
                                
                                if not 'OnOffSwitch' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type']:
                                    if attribute_code == 'Switch.Attributes.CurrentPosition' and 'Switch.Attributes.NumberOfPositions' in node['attributes_list'][endpoint_name]:
                                        if node['attributes_list'][endpoint_name]['Switch.Attributes.NumberOfPositions'] == 2:
                                            self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type'].append('OnOffSwitch')
                                            self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['@type'] = 'OnOffProperty'
                                            #self._type.append("OnOffSwitch")
                                        # TODO: how to handle switches with multiple positions? if it's a read-write cluster, create actions for each one to toggle them?
                                        # TODO: or integrate with a potential variables/ranges/sliders addon, and immediately set one up?
                                    elif attribute_code == 'OnOff.Attributes.OnOff':
                                        if not 'OnOffSwitch' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type']:
                                            self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type'].append('OnOffSwitch')
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['@type'] = 'OnOffProperty'
                                        if 'LevelControl.Attributes.CurrentLevel' in node['attributes_list'][endpoint_name] and not 'Light' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type']:
                                            self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type'].append('Light')
                                
                                # LEVELCONTROL MIN AND MAX LEVEL
                                if attribute_code.endswith('.MinLevel') and isinstance(node['attributes_list'][endpoint_name][attribute_code],(int,float)):
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['minimum'] = node['attributes_list'][endpoint_name][attribute_code]
                                elif attribute_code.endswith('.MaxLevel') and isinstance(node['attributes_list'][endpoint_name][attribute_code],(int,float)):
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['maximum'] = node['attributes_list'][endpoint_name][attribute_code]
                                
                                #self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type']
                                
                                if attribute_code.startswith('ColorControl.'):
                                    if not 'Light' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type']:
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type'].append('Light')
                                    
                                    # COLOR TEMPERATURE MIN-MAX
                                    if attribute_code == 'ColorControl.Attributes.ColorTempPhysicalMinMireds' and \
                                      isinstance(node['attributes_list'][endpoint_name][attribute_code],(int,float)) and \
                                      'ColorControl.Attributes.ColorTempPhysicalMaxMireds' in node['attributes_list'][endpoint_name] and \
                                      isinstance(node['attributes_list'][endpoint_name]['ColorControl.Attributes.ColorTempPhysicalMaxMireds'],(int,float)):
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['minimum'] = node['attributes_list'][endpoint_name][attribute_code]
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['maximum'] = node['attributes_list'][endpoint_name][attribute_code]
                                
                                
                                
                                # MEASUREMENT
                                
                                # measurement tolerance
                                measurement_types = [None,'mV','mA','mA','mA','Mw','mVAR','mVA','mV','mA','mW','mHz',None,'mA','mWh']
                                if attribute_code.endswith('.Tolerance') and isinstance(node['attributes_list'][endpoint_name][attribute_code],(int)) and node['attributes_list'][endpoint_name][attribute_code] > 0 and node['attributes_list'][endpoint_name][attribute_code] < len(measurement_types):
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['unit'] = measurement_types[node['attributes_list'][endpoint_name][attribute_code]]
                                
                                if attribute_code.endswith('.MeasuredValue'):
                                    if attribute_code.replace('.MeasuredValue','.MinMeasuredValue') in node['attributes_list'][endpoint_name] and \
                                      isinstance(node['attributes_list'][endpoint_name][attribute_code.replace('.MeasuredValue','.MinMeasuredValue')],(int,float)) and \
                                      attribute_code.replace('.MeasuredValue','.MaxMeasuredValue') in node['attributes_list'][endpoint_name] and \
                                      isinstance(node['attributes_list'][endpoint_name][attribute_code.replace('.MeasuredValue','.MaxMeasuredValue')],(int,float)):
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['minimum'] = node['attributes_list'][endpoint_name][attribute_code.replace('.MeasuredValue','.MinMeasuredValue')]
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['maximum'] = node['attributes_list'][endpoint_name][attribute_code.replace('.MeasuredValue','.MaxMeasuredValue')]
                                
                                # MEASUREMENT MIN-MAX
                                if attribute_code.endswith('.RangeMin ') and \
                                  not 'minimum' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description'] and \
                                  isinstance(node['attributes_list'][endpoint_name][attribute_code],(int,float)) and \
                                  attribute_code.replace('.RangeMin','.RangeMax') in node['attributes_list'][endpoint_name][attribute_code]:
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['minimum'] = node['attributes_list'][endpoint_name][attribute_code]
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['maximum'] = node['attributes_list'][endpoint_name][attribute_code.replace('.RangeMin','.RangeMax')]
                                
                                
                                if attribute_code == 'OccupancySensing.Attributes.OccupancySensorTypeEnum' and isinstance(node['attributes_list'][endpoint_name][attribute_code],int):
                                    occupancy_sensor_types = ['PIR','Ultrasonic','PIRAndUltrasonic','PhysicalContact']
                                    if node['attributes_list'][endpoint_name][attribute_code] >= 0 and node['attributes_list'][endpoint_name][attribute_code] < len(occupancy_sensor_types):
                                        property_value = occupancy_sensor_types[node['attributes_list'][endpoint_name][attribute_code]]
                                    
                                    
                                # ElectricalEnergyMeasurement is more about high-level electricity flowing in or out (sending solar energy back to the grid, for example)
                                # ElectricalPowerMeasurement seems more like a simple monitoring device
                                
                                """
                                capability_translations = {
                                    'TemperatureMeasurement':'TemperatureSensor',
                                    'PressureMeasurement':'BarometricPressureSensor',
                                    'RelativeHumidityMeasurement':'HumiditySensor',
                                    'OccupancySensing':'OccupancySensor',
                                    'SmokeCOAlarm':'SmokeSensor',
                                    'ElectricalPowerMeasurement':'EnergyMonitor',
                                }
                                """
                                #if attribute_code.startsWith('TemperatureMeasurement.') and not 'TemperatureSensor' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type']:
                                #    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type'].append('TemperatureSensor')
                                
                                
                                #ElectricalPowerMeasurement.Attributes.
                                
                                
                                
                                
                                #if 'Measurement.' in attribute_code:
                                
                                
                                # GET ENUM VALUE
                                
                                
                                
                                # with the enums lookup this should not be necessary anymore
                                if attribute_name in self.adapter.enums_lookup:
                                    if self.DEBUG:
                                        print("adding enum to device.  attribute_code,enum: ", attribute_code, self.adapter.enums_lookup[attribute_name])
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['type'] = 'string'
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['enum'] = self.adapter.enums_lookup[attribute_name]
                                    if isinstance(property_value,int) and property_value >=0 and property_value < len(self.adapter.enums_lookup[attribute_name]):
                                        property_value = self.adapter.enums_lookup[attribute_name][property_value]
                                        if self.DEBUG:
                                            print("switched property value from number to string from enums_lookup: ", property_value)
                                
                                elif attribute_code.endswith('Enum') and \
                                  attribute_code in supported_attributes and \
                                  'enum' in supported_attributes[attribute_code].keys() and \
                                  isinstance(node['attributes_list'][endpoint_name][attribute_code],int) and \
                                  node['attributes_list'][endpoint_name][attribute_code] >= 0 and \
                                  node['attributes_list'][endpoint_name][attribute_code] < len(supported_attributes[attribute_code]['enum']):
                                    if self.DEBUG:
                                        print("\nWARNING, unexpectedly enums_lookup was not used for: ", attribute_code)
                                    property_value = str(supported_attributes[attribute_code]['enum'][ node['attributes_list'][endpoint_name][attribute_code] ])
                                    if 'title' in supported_attributes[attribute_code]:
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['title'] = str(supported_attributes[attribute_code]['title'])
                                
                                        
                                #
                                # APPLY FROM PERSISTENT DATA
                                #
                                
                                # Apply any found capability dev@types to the thing we're creating
                                for dev_at_type in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type']:
                                    if not dev_at_type in self._type:
                                        if self.DEBUG:
                                            print("adding dev_at_type to thing: ", dev_at_type)
                                        self._type.append(dev_at_type)
                                    else:
                                        if self.DEBUG:
                                            print("dev_at_type has already been added to thing: ", dev_at_type)
                                
                                
                            except Exception as ex:
                                print("\ncaught error trying to upgrade @type: ", ex)
                                
                                
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

