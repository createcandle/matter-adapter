
import re
from gateway_addon import Device, Action
from .matter_property import MatterProperty

#from .matter_util import xy_to_hex, uncamel, number_to_boolean_list, clusters_to_ignore, hsv_to_hex
from .matter_util import *
#from matter_server.common.helpers.util import dataclass_from_dict,dataclass_to_dict,create_attribute_path_from_attribute
#from matter_server.common.helpers.util import create_attribute_path_from_attribute

import chip.clusters.Objects as cluster_details

import traceback


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
        
        if self.DEBUG:
            print("Device: self.node_id: ", self.node_id)
        
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
                    'minimum':0,
                    'maximum':1,
                    'type':'integer'},
                'PowerSource.Attributes.BatReplacementNeeded':{
                    'title':'Replace battery',
                    'readOnly': True, 
                    'type':'boolean'},
                    
                'Switch.Attributes.CurrentPosition':{
                    'readOnly': True,
                    'type':'integer'},
                    
                # This is a virtual attribute that it not in the Matter spec
                'Switch.Attributes.CurrentPositionEvent':{
                    'readOnly': True,
                    'type':'string'},
                    
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
                    
                'LevelControl.Attributes.CurrentLevel':{ # Could be for a light, but also for audio
                    'readOnly': False, 
                    'type':'integer', 
                    'percent':True},
                    
                'ColorControl.Attributes.CurrentHue':{
                    'title':'Hue',
                    'readOnly': False, 
                    'type':'integer'}, # light color
                
                #'ColorControl.Attributes.ColorMode':{
                #    'readOnly': False, 
                #    'type':'string'}, # light color
                'ColorControl.Attributes.CurrentX':{
                    'title':'Color',
                    'readOnly': False, 
                    'type':'string'}, # color X coordinate. Y value will be loaded too if this one is an attribute
                'ColorControl.Attributes.ColorTemperatureMireds':{
                    'title':'Color temperature',
                    'readOnly': False, 
                    'type':'integer', 
                    'minimum':3000, 
                    'maximum':7000}, # Color temperature (in Mireds)
                
                
                
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
                    'type':'string'},
                    #'enum':['PIR','Ultrasonic','PIRAndUltrasonic','PhysicalContact']},
                    
                'SmokeCOAlarm.Attributes.AlarmStateEnum':{
                    'readOnly': True,
                    'type':'string'},
                    #'enum':['Normal','Warning','Critical']},
                'SmokeCOAlarm.Attributes.SensitivityEnum':{
                    'title':'Sensitivity',
                    'readOnly': True, 
                    'type':'string'},
                    #'enum':['High','Standard','Low']},
                
                #'SmokeCOAlarm.Attributes.FeatureMap':{
                #    'title':'Type',
                #    'readOnly': True, 
                #    'type':'string',
                #    'enum':['SmokeAlarm','COAlarm']},
                'SmokeCOAlarm.Attributes.ExpressedStateEnum':{
                    'title':'Status',
                    'readOnly':True,
                    'type':'string'},
                   # 'enum':['Normal','SmokeAlarm','COAlarm','BatteryAlert','Testing','HardwareFault','EndOfService','InterconnectSmoke','InterconnectCO']},
                'SmokeCOAlarm.Attributes.ContaminationStateEnum':{
                    'title':'Contamination state',
                    'readOnly': True, 
                    'type':'string'}
                    #'enum':['Normal','Low','Warning','Critical']},
                
                
                    
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
            #clusters_to_ignore = ['OtaSoftwareUpdateRequestor','AccessControl','Descriptor','IcdManagement','OperationalCredentials','WiFiNetworkDiagnostics','ThreadNetworkDiagnostics','AdministratorCommissioning','NetworkCommissioning','GeneralCommissioning','GroupKeyManagement','Identify','Groups']
            
            
            
            #
            # PREPARATION LOOP
            #
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
                    
                    
                    #
                    #  PRE-PRE-CHECK - add virtual event attribute
                    #
                    
                    attribute_code_list = list(node['attributes_list'][endpoint_name].keys())
                    
                    available_clusters = []
                    # figure out available clusters within this endpoint
                    for attribute_code in attribute_code_list:
                        if '.Attributes.' in str(attribute_code):
                            cluster_name = str(attribute_code.split('.Attributes.')[0])
                            if not cluster_name in available_clusters:
                                available_clusters.append(cluster_name)
                                if cluster_name in self.adapter.events_lookup:
                                    if self.DEBUG:
                                        print("this cluster has events: ", cluster_name)
                                    attribute_code_list.append(str(cluster_name) + '.Attributes.RecentEvent')
                                else:
                                    if self.DEBUG:
                                        print("this cluster does not have events: ", cluster_name)
                    #if 'Switch.Attributes.CurrentPosition' in attribute_code_list:
                    #    if not 'Switch.Attributes.CurrentPositionEvent' in attribute_code_list:
                    #        attribute_code_list.append('Switch.Attributes.CurrentPositionEvent')
                    
                    
                    #for attribute_code in list(node['attributes'].keys()):
                    for attribute_code in attribute_code_list:
                        
                        try:
                            
                            cluster_name = str(attribute_code.split('.Attributes.')[0])
                            
                            if cluster_name in clusters_to_ignore:
                                if self.DEBUG:
                                    print("skipping cluster: ", cluster_name)
                                continue
                            else:
                                if self.DEBUG:
                                    print("\nattribute_code: ", attribute_code)
                    
                            if not '.Attributes.' in str(attribute_code):
                                if self.DEBUG:
                                    print("\nWARNING, no '.Attributes.' in attribute_code? ", attribute_code)
                                continue
                        
                            attribute_name = str(attribute_code.split('.Attributes.')[1])
                            
                            if attribute_name == 'FeatureMap':
                                if self.DEBUG:
                                    print("skipping FeatureMap")
                                continue
                            
                            #if not endpoint_name in self.adapter.persistent_data['nodez'][device_id]['attributes']:
                            #    if self.DEBUG:
                            #        print("adding missing endpoint to persistent data")
                            #    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name] = {}
                            
                            #if 'Candle.' in attribute_code:
                                
                                
                            #if ('Candle.' in attribute_code and self.adapter.add_hacky_properties) or (attribute_code in node['attributes_list'][endpoint_name] and isinstance(node['attributes_list'][endpoint_name][attribute_code],(str,int,float,bool)) ):
                            if 'Candle.' in attribute_code or attribute_code.endswith('.RecentEvent') or (attribute_code in node['attributes_list'][endpoint_name] and isinstance(node['attributes_list'][endpoint_name][attribute_code],(str,int,float,bool)) ):
                                
                                if not attribute_code in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name]:
                                    if self.DEBUG:
                                        print("adding to persistent_data:  device_id,attribute_code: ", device_id, attribute_code)
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code] = {}
                                    self.adapter.should_save = True
                                
                                if attribute_code in node['attributes_list'][endpoint_name]:
                                    if self.DEBUG:
                                        print("  this attribute seems to have a useable simple value: ", node['attributes_list'][endpoint_name][attribute_code])
                                    early_value = node['attributes_list'][endpoint_name][attribute_code]
                                    
                                    # Switch value to an enums string
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
                                
                                # Set an initial value for virtual 'hacky' attributes
                                elif 'Candle.' in attribute_code:
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['value'] = None
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['supported'] = True
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['enabled'] = True
                                
                                #Set an intial value for virtual 'event' attribute
                                elif attribute_code.endswith('.Attributes.RecentEvent'):
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['value'] = 'None'
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['supported'] = True
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['enabled'] = True
                                else:
                                    if self.DEBUG:
                                        print("warning: attribute_code fell through: no early value is being set for: ", attribute_code)
                                
                                if attribute_code in supported_types:
                                    #if self.DEBUG:
                                    #    print("  first_loop: nice, this attribute is in supported_types")
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['supported'] = True
                                else:
                                    if self.DEBUG:
                                        print("first_loop: this attribute is NOT in supported_types")
                        
                                if not 'enabled' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]:
                                    if self.DEBUG:
                                        print("  adding enabled attribute")
                                    if attribute_code.endswith('.Attributes.RecentEvent') or (attribute_code in supported_types and not attribute_code.startswith('BasicInformation')):
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
                            
                            
                            elif attribute_code in node['attributes_list'][endpoint_name] and isinstance(node['attributes_list'][endpoint_name][attribute_code],list):
                                
                                if attribute_name == 'AcceptedCommandList':
                                    if self.DEBUG:
                                        print("checking out accepted_commands_list (AcceptedCommandList) for attribute_code: ", attribute_code)
                                    if cluster_name in self.adapter.commands_lookup:
                                        if self.DEBUG:
                                            print("ACCEPTED COMMANDS LOOKUP EXISTS FOR cluster_name: ", cluster_name)
                                        if not attribute_code in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name]:
                                            if self.DEBUG:
                                                print("adding AcceptedCommandList list to persistent_data:  device_id,attribute_code: ", device_id, attribute_code)
                                            self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code] = {'enabled':False}
                                            self.adapter.should_save = True
                                        
                                        for command_name in list(self.adapter.commands_lookup[cluster_name].keys()):
                                            if self.DEBUG:
                                                print("checking if command is supported: ", command_name)
                                            if 'id' in self.adapter.commands_lookup[cluster_name][command_name] and self.adapter.commands_lookup[cluster_name][command_name]['id'] in node['attributes_list'][endpoint_name][attribute_code]:
                                                if self.DEBUG:
                                                    print("COMMAND IS ACCEPTED: ", command_name)
                                                if not 'accepted_commands' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]:
                                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['accepted_commands'] = {}
                                                if not command_name in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['accepted_commands']:
                                                    self.adapter.should_save = True
                                                self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['accepted_commands'][command_name] = self.adapter.commands_lookup[cluster_name][command_name]
                                            else:
                                                if self.DEBUG:
                                                    print("COMMAND IS _NOT_ ACCEPTED: ", command_name)
                                                        
                                        
                                        
                                    else:
                                        print("WARNING, this cluster was not in the commands lookup table: ", cluster_name)
                                
                            else:
                                if self.DEBUG:
                                    print("WARNING, attribute_code fell through during first round: ", attribute_code)
                            
                            
                        except Exception as ex:
                            print("\nERROR: caught error doing first loop over attributes: ", ex)
                        
                        
                        
                    
                    
                    #if self.DEBUG:
                    #    print("\n\n\n")
                    #    print("persistent attributes data: ", self.adapter.persistent_data['nodez'][device_id]['attributes'])
                    #    print("\n\n\n")
            
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
                            
                            if not attribute_code in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name]:
                                self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code] = {}
                            
                            if not 'enabled' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]:
                                if self.DEBUG:
                                    print("\nERROR, enabled was missing from persistent data for attribute_code: ", attribute_code)
                                #self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['enabled'] = False
                                if attribute_code in supported_types and not attribute_code.startswith('BasicInformation'):
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['enabled'] = True
                                else:
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['enabled'] = False
                                self.adapter.should_save = True
                            
                            
                            #
                            #
                            #      S K I P   I F   N O T   E N A B L E D
                            #
                            #
                            
                            
                            # If the attribute is not enabled as a thing property, then stop here
                            if self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['enabled'] == False:
                                if self.DEBUG:
                                    print("skipping attribute that is not enabled.  attribute_code: ", attribute_code)
                                continue
                            
                            if not '.Attributes.' in str(attribute_code):
                                if self.DEBUG:
                                    print("\n\nERROR, no .Attributes. in attribute_code?: ", attribute_code)
                                continue
                                
                            
                            if self.DEBUG:
                                print("\n\n+\nattribute_code again: ", attribute_code)
                            
                            
                            cluster_name = str(attribute_code.split('.Attributes.')[0])
                            attribute_name = str(attribute_code.split('.Attributes.')[1])
                            property_id = 'property-' + endpoint_name + '-' + cluster_name + '-' + attribute_name
                            
                            if self.DEBUG:
                                print("- cluster_name: ", cluster_name)
                                print("- attribute_name: ", attribute_name)
                                print("- property_id: ", property_id)
                                
                            
                            
                            #
                            #
                            #  GET INTIIAL VALUE
                            #  
                            #
                            try:
                                if attribute_code in node['attributes_list'][endpoint_name]:
                                    
                                    # TODO: technically the value has already been placed in the persistent data in the first loop over all the attributes
                                    # and with the hacky properties, this is even more relevant, since those ONLY have a value in persistent data, and never in node data
                                    
                                    if isinstance(node['attributes_list'][endpoint_name][attribute_code],(str,int,float,bool)):
                                        property_value = node['attributes_list'][endpoint_name][attribute_code]
                                         
                                    else:
                                        if self.DEBUG:
                                            print("Value fell through (probably an array).  node['attributes_list'][attribute_code]: ", node['attributes_list'][endpoint_name][attribute_code])
                                    
                                # Could be a value from a hacky attribute, which would not exist in the node dict
                                elif 'value' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]:
                                    property_value = self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['value']
                                
                                if self.DEBUG:
                                    print("- early value: ", property_value)
                                    
                                #if value != None:
                                #self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['value'] = value
                            
                                
                                
                            except Exception as ex:
                                if self.DEBUG:
                                    print("\nERROR: device: caught error extracting initial value: " + str(ex))
                                    print(traceback.format_exc())
                            
                            
                            # GENERATE TITLE
                            
                            try:
                                property_title = '' + attribute_name
                                property_title.replace('OnOff','State')
                                if property_title.startswith('Current') and not property_title.endswith('Current'):
                                    property_title.replace('Current','')
                                    
                                #elif attribute_name == 'CurrentPosition' and attribute_code.startswith('Switch'):
                                #    property_title = 'State'
                                
                                if '.Attributes.' in property_title:
                                    property_title = str(property_title.split('.Attributes.')[1])
                                #property_title = uncamel(property_title).replace('_',' ')
                                property_title = uncamel(property_title)
                            
                                if property_title.startswith('bat_'):
                                    property_title = property_title.replace('bat_','battery_')
                                property_title = property_title.replace("_string","")
                                property_title = property_title.replace("_enum","")
                                property_title = property_title.capitalize()
                                property_title = property_title.replace('_',' ')
                                if self.DEBUG:
                                    print("raw property_title: " + str(property_title))
                                
                                # Override title if there is one defined in supported_attributes
                                if attribute_code in supported_attributes and 'title' in supported_attributes[attribute_code].keys():
                                    property_title = str(supported_attributes[attribute_code]['title'])
                            
                                # Use the cluster name as the title basis
                                elif attribute_name == 'MeasuredValue' or attribute_name == 'MeasuredValueEvent':
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
                                            used_property_titles.append(title_with_endpoint_number)
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
                                    print("- Final property title: ", attribute_name, " -> ", property_title)
                                
                            except Exception as ex:
                                if self.DEBUG:
                                    print("\nERROR: device: caught error wrangling title: " + str(ex))
                            
                            
                            try:
                                
                                #
                                #   PROPERTY DICT IS NOW ENSURED
                                #
                                
                                if not 'property' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]:
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property'] = {'attribute_code':attribute_code, 'id':property_id, 'cluster_name':cluster_name, 'attribute_name':attribute_name}
                                    self.adapter.should_save = True
                                
                                if not 'description' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']:
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description'] = {}
                                
                                if not 'dev@type' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']:
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type'] = []
                                    self.adapter.should_save = True
                                
                                # Add some values that are needed to communicate back to the Matter network in matter_property.py
                                self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['id'] = property_id
                                self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['endpoint'] = int(endpoint_name.replace('Endpoint',''))
                                self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['node_id'] = self.node_id
                                self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['attribute_code'] = attribute_code
                                
                                
                            
                                if self.DEBUG:
                                    print("property_id: ", property_id)
                                    
                            except Exception as ex:
                                if self.DEBUG:
                                    print("device: caught error doing early persistent_data ensuring: " + str(ex))
                                    print(traceback.format_exc())
                                    
                            
                                
                            
                            
                
                            
                
                            
                                
                            #
                            #
                            #  CREATING / UPDATING PROPERTY DESCRIPTION
                            #
                            #
                            
                
                
                            # WEBTHINGS PROPERTY DESCRIPTION AND @-TYPES
                            try:
                                
                                # Basic property description from supported_types
                                
                            
                                self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['title'] = str(property_title)
                                self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['description'] = 'A Matter device'
                                if attribute_code in supported_attributes:
                                    if 'type' in supported_attributes[attribute_code]:
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['type'] = supported_attributes[attribute_code]['type']
                                    if 'readOnly' in supported_attributes[attribute_code]:
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['readOnly'] = supported_attributes[attribute_code]['readOnly']
                            
                                    # Percentage shortcut, can be overwritten later on
                                    if 'percent' in attribute_code.lower() or ('percent' in supported_attributes[attribute_code] and supported_attributes[attribute_code]['percent'] == True): # This is always True the case if the attribute exists...
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['multipleOf'] = 1
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['minimum'] = 0
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['maximum'] = 100
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['unit'] = 'percent'
                        
                                    # MultipleOf
                                    if 'multipleOf' in supported_attributes[attribute_code]:
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['multipleOf'] = supported_attributes[attribute_code]['multipleOf']
            
                                    # Minimum and maximum number/integer limits
                                    if 'minimum' in supported_attributes[attribute_code]:
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['minimum'] = supported_attributes[attribute_code]['minimum']
                                    if 'maximum' in supported_attributes[attribute_code]:
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['maximum'] = supported_attributes[attribute_code]['maximum']
                                    
                            
                                elif 'percent' in attribute_code.lower(): # This is always True the case if the attribute exists...
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['type'] = 'number'
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['multipleOf'] = 1
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['minimum'] = 0
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['maximum'] = 100
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['unit'] = 'percent'
                                
                                if not 'type' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']:
                                    if isinstance(property_value,int) or str(property_value).isdigit():
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['type'] = 'number'
                                    elif isinstance(property_value,str):
                                        if property_value == 'On' or property_value == 'Off':
                                            self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['type'] = 'boolean'
                                        else:
                                            self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['type'] = 'string'
                                    elif isinstance(property_value,bool):
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['type'] = 'boolean'
                                    else:
                                        if self.DEBUG:
                                            print("\nERROR, getting description type from value itself fell through. Will fall back to using 'string'")
                                
                                if not 'type' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']:
                                    if self.DEBUG:
                                        print("\n\n\n\nERROR, 'type' was still missing from property description: ", self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description'])
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['type'] = 'string'
                                    
                                # TODO: does the controller automatically add forms?
                                #description["forms"] = [{"href": "properties/" + str(property_id)}]
            
                                
            
                                if self.DEBUG:
                                    print("initial description: ", attribute_code, self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description'])
            
                               
                            except Exception as ex:
                                if self.DEBUG:
                                    print("caught error creating description for property to place in persistent storage: ", ex)
                                    print(traceback.format_exc())
                                
                                
                                
                                
                                
                                
                            
                            #
                            #
                            #     ADD CAPABILITES
                            #
                            #    
                                
                            try:
                                
                                
                                # TODO: analyse featuremap.
                                # 1. turn .FeatureMap into a list of booleans using number_to_boolean_list()
                                # 2. Check that list agains some data source
                                # 3. Use that info to determine optimal capabilities as well as which properties make sense to enable by default
                                
                                # 4. OR use the already implemented AcceptedCommandsList, as that also gives an indication about what the device supports
                                
                                #
                                #
                                #  START WITH ADDING CAPABILITIES FROM supported_types
                                #
                                #
                                
                                try:
                                    
                                    if attribute_code in supported_attributes:
                                        if self.DEBUG:
                                            print("attribute code is in supported_attributes: ", attribute_code, supported_attributes[attribute_code])
                                        if '@type' in supported_attributes[attribute_code]:
                                            if supported_attributes[attribute_code]['@type'] not in used_property_at_types:
                                                self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['@type'] = supported_attributes[attribute_code]['@type']
                                                used_property_at_types.append(self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['@type'])
                                            else:
                                                if self.DEBUG:
                                                    print("WARNING, SKIPPING, property capablity was already used in this device: ", description['@type'])
                    
                                        # Theoretically it would be nicer to check if ALL required properies for the dev@type exist. Also, currenty there is a tiny chance that the dev@type is never set
                                        if 'dev@type' in supported_attributes[attribute_code]:
                                            if not supported_attributes[attribute_code]['dev@type'] in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type']:
                                                self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type'].append( supported_attributes[attribute_code]['dev@type'] )
                                            
                                            #if not supported_attributes[attribute_code]['dev@type'] in self._type:
                                            #    #self._type.append( supported_attributes[attribute_code]['dev@type'] )
                                            #    if self.DEBUG:
                                            #        print("add new capability: " + str(supported_attributes[attribute_code]['dev@type']))
                                            #else:
                                            #    if self.DEBUG:
                                            #        print("capability already existed: " + str(supported_attributes[attribute_code]['dev@type']))
                                        
                                    
                                    elif 'percent' in attribute_code.lower() and attribute_code != 'BatPercentRemaining' and not '@type' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']:
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['@type'] = 'LevelProperty'
                                        
                                        # TODO:
                                        # It would be useful to then also add either 'MultiLevelSensor' or 'MultiLevelSwitch' to the dev@type. But for that we need to know if this is a read-only or read-write cluster/attribute
                                        
                                        #if not supported_attributes[attribute_code]['dev@type'] in self._type:
                                        
                                except Exception as ex:
                                    if self.DEBUG:
                                        print("Device: caught error adding capabilties from supported_types: " + str(ex))
                                        print(traceback.format_exc())
                                
                                
                                
                                
                                
                                
                                
                                
                                
                                
                                
                                
                                if not 'description' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']:
                                    if self.DEBUG:
                                        print("ERROR, somehow still missing description in property in persistent data. Aborting.")
                                    break
                                
                                
                                if attribute_code.endswith('.RecentEvent')
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['readOnly'] = True
                                
                                elif attribute_code == 'OnOff.Attributes.OnOff':
                                    if not 'OnOffSwitch' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type']:
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type'].append('OnOffSwitch')
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['@type'] = 'OnOffProperty'
                                                                        
                                
                                elif attribute_code == 'Switch.Attributes.CurrentPosition' and 'Switch.Attributes.NumberOfPositions' in node['attributes_list'][endpoint_name]:
                                    if node['attributes_list'][endpoint_name]['Switch.Attributes.NumberOfPositions'] == 2:
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['@type'] = 'OnOffProperty'
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['type'] = 'boolean'
                                        if not 'OnOffSwitch' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type']:
                                            self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type'].append('OnOffSwitch')
                                                
                                            #self._type.append("OnOffSwitch")
                                        # TODO: how to handle switches with multiple positions? if it's a read-write cluster, create actions for each one to toggle them?
                                        # TODO: or integrate with a potential variables/ranges/sliders addon, and immediately set one up?
                                    else:
                                        if not 'LevelControl.Attributes.CurrentLevel' in node['attributes_list'][endpoint_name]:
                                            if not 'MultiLevelSwitch' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type']:
                                                self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type'].append('MultiLevelSwitch')
                                            self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['type'] = 'integer'
                                            self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['minimum'] = 0
                                            self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['maximum'] = int(node['attributes_list'][endpoint_name]['Switch.Attributes.NumberOfPositions'])
                                            self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['@type'] = 'LevelProperty'
                                
                                
                                # LEVELCONTROL
                                # Is it a light or something like an an audio device?
                                if attribute_code.endswith('.CurrentLevel'):
                                    if 'ColorControl.Attributes.FeatureMap' in node['attributes_list'][endpoint_name]:
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name]['LevelControl.Attributes.CurrentLevel']['property']['description']['@type'] = 'BrightnessProperty'
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name]['LevelControl.Attributes.CurrentLevel']['property']['description']['title'] = 'Brightness'
                                        if not 'Light' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type']:
                                            self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type'].append('Light')
                                    else:
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name]['LevelControl.Attributes.CurrentLevel']['property']['description']['@type'] = 'LevelProperty'
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name]['LevelControl.Attributes.CurrentLevel']['property']['description']['title'] = 'Level'
                                        if not 'MultiLevelSwitch' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type']:
                                            self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type'].append('MultiLevelSwitch')
                                
                                
                                # LEVELCONTROL MIN AND MAX LEVEL
                                if attribute_code.endswith('.MinLevel') and isinstance(node['attributes_list'][endpoint_name][attribute_code],(int,float)):
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['minimum'] = node['attributes_list'][endpoint_name][attribute_code]
                                elif attribute_code.endswith('.MaxLevel') and isinstance(node['attributes_list'][endpoint_name][attribute_code],(int,float)):
                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['maximum'] = node['attributes_list'][endpoint_name][attribute_code]
                                
                                
                                
                                
                                try:
                                    # COLOR
                                    if attribute_code.startswith('ColorControl'):
                                        if not 'Light' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type']:
                                            self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type'].append('Light')
                                    
                                    
                                        # What is determining the color at the moment?
                                        # 0 CurrentHue and CurrentSaturation
                                        # 1 CurrentX and CurrentY
                                        # 2 ColorTemperatureMireds
                                        # 3 EnhancedCurrentHue and CurrentSaturation
                                    
                                        if 'ColorControl.Attributes.EnhancedColorMode' in node['attributes_list'][endpoint_name]:
                                            if self.DEBUG:
                                                print("currently determining the color is: ", node['attributes_list'][endpoint_name]['ColorControl.Attributes.EnhancedColorMode'])
                                        
                                            
                                        # COLOR 
                                        try:
                                            if self.DEBUG:
                                                print("colorControl: property_value before: ", property_value)
                                            # for the basic non-enhanced hue it seems the value can range between 0 and 254 (int8)
                                            if attribute_code == 'ColorControl.Attributes.CurrentHue': # and not str(property_value).startswith('#')
                                                if 'ColorControl.Attributes.CurrentHue' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name] and \
                                                  'ColorControl.Attributes.CurrentSaturation' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name] and \
                                                  'ColorControl.Attributes.CurrentHue' in node['attributes_list'][endpoint_name] and \
                                                  'ColorControl.Attributes.CurrentSaturation' in node['attributes_list'][endpoint_name] and \
                                                  isinstance(node['attributes_list'][endpoint_name]['ColorControl.Attributes.CurrentHue'],(int,float)) and \
                                                  isinstance(node['attributes_list'][endpoint_name]['ColorControl.Attributes.CurrentSaturation'],(int,float)):
                                                    hsv_to_hex_color = hsv_to_hex(node['attributes_list'][endpoint_name]['ColorControl.Attributes.CurrentHue'] , node['attributes_list'][endpoint_name]['ColorControl.Attributes.CurrentSaturation'])
                                                    if self.DEBUG:
                                                        print("HSV to HEX color: ", hsv_to_hex_color)
                                                    if is_hex_color(hsv_to_hex_color):
                                                        if not str(hsv_to_hex_color).startswith('#'):
                                                            hsv_to_hex_color = '#' + hsv_to_hex_color
                                                        property_value = hsv_to_hex_color
                                                    
                                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['@type'] = 'ColorProperty'
                                                        if not 'ColorControl' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type']:
                                                            self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type'].append('ColorControl')
                                                    
                                                    
                                            # Turn XY Color in HEX color when parsing the X color
                                            elif attribute_code == 'ColorControl.Attributes.CurrentX': # and not str(property_value).startswith('#')
                                                if 'ColorControl.Attributes.CurrentY' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name]:
                                                    # Get Y value too
                                                    color_x_value = node['attributes_list'][endpoint_name]['ColorControl.Attributes.CurrentX']
                                                    color_y_value = node['attributes_list'][endpoint_name]['ColorControl.Attributes.CurrentY']
                                                    if self.DEBUG:
                                                        print("color x: " + str(color_x_value) + ", y: " + str(color_y_value))
                
                                                    # value can range between 0 and 65279 (int16)
                
                                                    # TODO: in one line, theoretically:
                                                    # color_y_value = node['attributes'][ all_short_attributes['ColorControl.Attributes.CurrentY'] ]['value']
                
                                                    # calculate hex string
                                                    property_value = xy_to_hex(color_x_value,color_y_value)
                                                    if self.DEBUG:
                                                        print("initial color value from xy_to_hex: ", property_value)
                                                    if isinstance(property_value,str) and not property_value.startswith('#') and len(property_value) == 6:
                                                        property_value = '#' + property_value
                                    
                                        
                                            if attribute_code == 'ColorControl.Attributes.CurrentX':
                                                # Does it have CurrentHue attribute?
                                                if 'ColorControl.Attributes.CurrentHue' in node['attributes_list'][endpoint_name] and 'ColorControl.Attributes.CurrentSaturation' in node['attributes_list'][endpoint_name]:
                                                    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['@type'] = 'ColorProperty'
                                                    if not 'ColorControl' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type']:
                                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type'].append('ColorControl')
                                      
                                        

                                                
                            
                                        except Exception as ex:
                                            if self.DEBUG:
                                                print("Device: caught error optimizing color value: " + str(ex))
                                                print(traceback.format_exc())
                                    
                                        # COLOR TEMPERATURE MIN-MAX
                                        # already handled below for color-temperature-only bulbs
                                        #if attribute_code == 'ColorControl.Attributes.ColorTempPhysicalMinMireds' and \
                                        #  isinstance(node['attributes_list'][endpoint_name][attribute_code],(int,float)) and \
                                        #  'ColorControl.Attributes.ColorTempPhysicalMaxMireds' in node['attributes_list'][endpoint_name] and \
                                        #  isinstance(node['attributes_list'][endpoint_name]['ColorControl.Attributes.ColorTempPhysicalMaxMireds'],(int,float)):
                                        #    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['minimum'] = node['attributes_list'][endpoint_name][attribute_code]
                                        #    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['maximum'] = node['attributes_list'][endpoint_name][attribute_code]
                                
                                
                                
                                
                                
                                
                                
                                    #if attribute_code == 'ColorControl.Attributes.CurrentHue':
                                    #    if 'ColorControl.Attributes.CurrentSaturation' in node['attributes_list'][endpoint_name]:
                                    #        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['@type'] = 'ColorProperty'
                                     
                                    # Override minimum and maximum mireds according to provided data
                                    if attribute_code == 'ColorControl.Attributes.ColorTemperatureMireds':
                                        # TODO: does this affect actual color control?
                                        if 'ColorControl.Attributes.ColorTempPhysicalMinMireds' in node['attributes_list'][endpoint_name] and 'ColorControl.Attributes.ColorTempPhysicalMaxMireds' in node['attributes_list'][endpoint_name]:
                                            if isinstance(node['attributes_list'][endpoint_name]['ColorControl.Attributes.ColorTempPhysicalMinMireds'],int) and isinstance(node['attributes_list'][endpoint_name]['ColorControl.Attributes.ColorTempPhysicalMaxMireds'],int):
                                                self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['minimum'] = node['attributes_list'][endpoint_name]['ColorControl.Attributes.ColorTempPhysicalMinMireds']
                                                self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['maximum'] = node['attributes_list'][endpoint_name]['ColorControl.Attributes.ColorTempPhysicalMaxMireds']
                                    
                                        # Color temperature only
                                        if not 'ColorControl.Attributes.CurrentHue' in node['attributes_list'][endpoint_name]:
                                            if not 'Light' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type']:
                                                self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type'].append('Light')
                                            self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['@type'] = 'ColorTemperatureProperty'
                                
                                    
                                except Exception as ex:
                                    if self.DEBUG:
                                        print("Device: caught error adding color capabilties: " + str(ex))
                                        print(traceback.format_exc())
                                
                                
                                # MEASUREMENT
                                try:
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
                                    
                                    
                                except Exception as ex:
                                    if self.DEBUG:
                                        print("Device: caught error adding measurement capabilties: " + str(ex))
                                
                                
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
                                #if attribute_code.startswith('TemperatureMeasurement.') and not 'TemperatureSensor' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type']:
                                #    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['dev@type'].append('TemperatureSensor')
                                
                                
                                
                                
                                
                                
                                
                                
                                
                                
                                # GET ENUM VALUE
                                
                                
                                
                                try:
                                    
                                    # GET EVENTS ENUM
                                    
                                    if attribute_code.endswith('.RecentEvent') and cluster_name in self.adapter.events_lookup:
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['enum'] = self.adapter.events_lookup[cluster_name]
                                        if self.DEBUG:
                                            print("set RecentEvent enum for attribute_code: ", attribute_code, self.adapter.events_lookup[cluster_name])
                                    
                                    
                                    
                                    # GET ENUM LIST FROM ENUMS_LOOKUP
                                    
                                    if attribute_name in self.adapter.enums_lookup:
                                        if attribute_code.endswith('Enum'):
                                            if self.DEBUG:
                                                print("adding enum to device.  attribute_code,enum: ", attribute_code, self.adapter.enums_lookup[attribute_name])
                                            if not 'type' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']:
                                                self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['type'] = 'string'
                                            if self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['type'] == 'string':
                                                self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['enum'] = self.adapter.enums_lookup[attribute_name]
                                                if isinstance(property_value,int) and property_value >=0 and property_value < len(self.adapter.enums_lookup[attribute_name]):
                                                    property_value = str(self.adapter.enums_lookup[attribute_name][property_value])
                                                    if self.DEBUG:
                                                        print("OK, switched property value from number to string from enums_lookup: ", property_value, self.adapter.enums_lookup[attribute_name])
                                    
                                            else:
                                                if self.DEBUG:
                                                    print("unexpectedly an attribute_code that ends with Enum does not have 'string' as its property type: ", attribute_code,  self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property'])
                                        else:
                                            if self.DEBUG:
                                                print("Interesting, there is enum for an attribute_name that does not end with Enum: ", attribute_name, self.adapter.enums_lookup[attribute_name])
                                
                                    # with the enums lookup this should not be necessary anymore
                                    # TODO: Remove? or could override enums here from the supported dict, perhaps to get even nicer names
                                    elif attribute_code.endswith('Enum') and \
                                      attribute_code in supported_attributes and \
                                      'enum' in supported_attributes[attribute_code].keys() and \
                                      isinstance(node['attributes_list'][endpoint_name][attribute_code],int) and \
                                      node['attributes_list'][endpoint_name][attribute_code] >= 0 and \
                                      isinstance(supported_attributes[attribute_code]['enum'],list) and \
                                      node['attributes_list'][endpoint_name][attribute_code] < len(supported_attributes[attribute_code]['enum']):
                                        if self.DEBUG:
                                            print("\nWARNING, unexpectedly enums_lookup was not used for: ", attribute_code)
                                        if str(node['attributes_list'][endpoint_name][attribute_code]) in supported_attributes[attribute_code]['enum']:
                                            if self.DEBUG:
                                                print("setting property value to option that was found in enum: ", str(node['attributes_list'][endpoint_name][attribute_code]))
                                            property_value = str(supported_attributes[attribute_code]['enum'][ int(node['attributes_list'][endpoint_name][attribute_code]) ])
                                        #if 'title' in supported_attributes[attribute_code]:
                                        #    self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['title'] = str(supported_attributes[attribute_code]['title'])
                                
                                
                                    # Make enum options nicer to read
                                    if 'enum' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']:
                                        uncameled_enum_options = []
                                        if self.DEBUG:
                                            print("BEFORE: camel case enum options: " + str(self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['enum']))
                                        if str(property_value) in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['enum']:
                                            property_value = uncamel(property_value).replace('_',' ')
                                            if self.DEBUG:
                                                print("uncameled the property value too: ", property_value)
                                        for enum_option in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['enum']:
                                            uncameled_enum_options.append(uncamel(enum_option).replace('_',' '))
                                        if self.DEBUG:
                                            print("AFTER: uncameled_enum_options: " + str(uncameled_enum_options))
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['enum'] = uncameled_enum_options
                                        
                                        if property_value == None:
                                            property_value = 'None'
                                        elif not str(property_value) in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['enum']:
                                            if self.DEBUG:
                                                print("\nERROR, did not find property_value in uncameled enum list, setting it to 'None': " + str(property_value))
                                            property_value = 'None'
                                            
                                        # Ensure there is a 'None' enum option
                                        if not 'None' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['enum']:
                                            self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description']['enum'].append('None')
                                    
                                    
                                except Exception as ex:
                                    if self.DEBUG:
                                        print("Device: caught error adding enum lists: " + str(ex))
                                        print(traceback.format_exc())
                                
                                
                                #
                                #  APPLY USER OVERRIDES
                                #
                                
                                try:
                                    if 'description_customizations' in self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']:
                                        self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description'] = self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description'] | self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['property']['description_customizations']
                                
                                except Exception as ex:
                                    if self.DEBUG:
                                        print("Device: caught error adding user customizations: " + str(ex))
                                        print(traceback.format_exc())
                                
                                
                                
                                
                                
                                
                                #
                                # APPLY FROM PERSISTENT DATA
                                #
                                try:
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
                                    print("Device: caught error applying dev@type to device: " + str(ex))
                                
                                
                            except Exception as ex:
                                if self.DEBUG:
                                    print("\ncaught error trying to upgrade @type: ", ex)
                                    print(traceback.format_exc())
                                
                                
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
                                if self.DEBUG:
                                    print("device: caught error creating property: ", ex)
                                    print(traceback.format_exc())
                                    
                    
                                        
                        except Exception as ex:
                            if self.DEBUG:
                                print("Device: caught general error in generating property: " + str(ex))
                                print(traceback.format_exc())
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

