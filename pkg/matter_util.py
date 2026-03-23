# helper functions for Matter adapter

#import re
import sys
import json
import math
from collections import namedtuple

# for creating enum lookup
import chip.clusters.Objects as cluster_details
#from chip.clusters.Objects import ChipClusters
#from chip.clusters.Objects import GetClusterInfoById, ListClusterInfo, ListClusterCommands, ListClusterAttributes

from chip.clusters.ClusterObjects import ALL_ATTRIBUTES, ALL_CLUSTERS, ALL_EVENTS
from matter_server.client.models.device_types import ALL_TYPES

#print("DIR cluster_details: ", dir(cluster_details))

#print()
#print("ChipClusters.ListClusterInfo: ", ChipClusters.ListClusterInfo())


clusters_to_ignore = [
    "Globals",
    "Identify",
    "Groups",
    "Descriptor",
    "Binding",
    #"AccessControl",
    "Actions",
    "OtaSoftwareUpdateProvider",
    "OtaSoftwareUpdateRequestor",
    "LocalizationConfiguration",
    "TimeFormatLocalization",
    "UnitLocalization",
    "PowerSourceConfiguration",
    "GeneralCommissioning",
    "NetworkCommissioning",
    "DiagnosticLogs",
    "GeneralDiagnostics",
    "SoftwareDiagnostics",
    "ThreadNetworkDiagnostics",
    "WiFiNetworkDiagnostics",
    "EthernetNetworkDiagnostics",
    "TimeSynchronization",
    "BridgedDeviceBasicInformation",
    "AdministratorCommissioning",
    "OperationalCredentials",
    "GroupKeyManagement",
    #"FixedLabel",
    #"UserLabel",
    "ProxyConfiguration",
    "ProxyDiscovery",
    "ProxyValid",
    "IcdManagement",
    "ScenesManagement",
    "Messages",
    "EnergyEvseMode",
    "WiFiNetworkManagement",
    "ThreadBorderRouterManagement",
    "ThreadNetworkDirectory",
    "WakeOnLan",
    "Channel",
    "TargetNavigator",
    "ContentLauncher",
    "ApplicationLauncher",
    "ApplicationBasic",
    "AccountLogin",
    "ContentControl",
    "ContentAppObserver",
    "ZoneManagement",
    #"CameraAvStreamManagement",
    "CameraAvSettingsUserLevelManagement",
    "WebRTCTransportProvider",
    "WebRTCTransportRequestor",
    "PushAvStreamTransport",
    "EcosystemInformation",
    "CommissionerControl",
    "JointFabricDatastore",
    "JointFabricAdministrator",
    "TlsCertificateManagement",
    "TlsClientManagement",
    #"MeterIdentification",
    "CommodityMetering",
    "UnitTesting",
    "FaultInjection",
    "SampleMei",
    ]




# Turns color names into HEX color values. Useful with voice control
def colorNameToHex(color):
    colors = {"alice blue":"#f0f8ff","antique white":"#faebd7","aqua":"#00ffff","aquamarine":"#7fffd4","azure":"#f0ffff",
    "beige":"#f5f5dc","bisque":"#ffe4c4","black":"#000000","blanched almond":"#ffebcd","blue":"#0000ff","blue violet":"#8a2be2","brown":"#a52a2a","burlywood":"#deb887",
    "cadet blue":"#5f9ea0","chartreuse":"#7fff00","chocolate":"#d2691e","coral":"#ff7f50","cornflower blue":"#6495ed","cornsilk":"#fff8dc","crimson":"#dc143c","cyan":"#00ffff",
    "dark blue":"#00008b","darkcyan":"#008b8b","dark golden rod":"#b8860b","darkgray":"#a9a9a9","dark green":"#006400","darkkhaki":"#bdb76b","dark magenta":"#8b008b","dark olive green":"#556b2f",
    "dark orange":"#ff8c00","dark orchid":"#9932cc","dark red":"#8b0000","dark salmon":"#e9967a","dark sea green":"#8fbc8f","dark slate blue":"#483d8b","dark slate gray":"#2f4f4f","dark turquoise":"#00ced1",
    "dark violet":"#9400d3","deep pink":"#ff1493","deep sky blue":"#00bfff","dim gray":"#696969","dodger blue":"#1e90ff",
    "firebrick":"#b22222","floral white":"#fffaf0","forest green":"#228b22","fuchsia":"#ff00ff",
    "gainsboro":"#dcdcdc","ghostwhite":"#f8f8ff","gold":"#ffd700","golden rod":"#daa520","gray":"#808080","green":"#008000","green yellow":"#adff2f",
    "honeydew":"#f0fff0","hot pink":"#ff69b4",
    "indian red ":"#cd5c5c","indigo":"#4b0082","ivory":"#fffff0","khaki":"#f0e68c",
    "lavender":"#e6e6fa","lavender blush":"#fff0f5","lawn green":"#7cfc00","lemon chiffon":"#fffacd","light blue":"#add8e6","light coral":"#f08080","light cyan":"#e0ffff","light goldenrod yellow":"#fafad2",
    "light grey":"#d3d3d3","light green":"#90ee90","light pink":"#ffb6c1","light salmon":"#ffa07a","light sea green":"#20b2aa","light sky blue":"#87cefa","light slate gray":"#778899","light steel blue":"#b0c4de",
    "light yellow":"#ffffe0","lime":"#00ff00","lime green":"#32cd32","linen":"#faf0e6",
    "magenta":"#ff00ff","maroon":"#800000","medium aquamarine":"#66cdaa","medium blue":"#0000cd","medium orchid":"#ba55d3","medium purple":"#9370d8","medium sea green":"#3cb371","medium slate blue":"#7b68ee",
    "medium spring green":"#00fa9a","mediumturquoise":"#48d1cc","medium violet red":"#c71585","midnight blue":"#191970","mintcream":"#f5fffa","mistyrose":"#ffe4e1","moccasin":"#ffe4b5",
    "navajo white":"#ffdead","navy":"#000080",
    "oldlace":"#fdf5e6","olive":"#808000","olive drab":"#6b8e23","orange":"#ffa500","orange red":"#ff4500","orchid":"#da70d6",
    "pale golden rod":"#eee8aa","pale green":"#98fb98","pale turquoise":"#afeeee","pale violet red":"#d87093","papayawhip":"#ffefd5","peachpuff":"#ffdab9","peru":"#cd853f","pink":"#ffc0cb","plum":"#dda0dd","powder blue":"#b0e0e6","purple":"#800080",
    "rebecca purple":"#663399","red":"#ff0000","rosy brown":"#bc8f8f","royal blue":"#4169e1",
    "saddlebrown":"#8b4513","salmon":"#fa8072","sandy brown":"#f4a460","sea green":"#2e8b57","seashell":"#fff5ee","sienna":"#a0522d","silver":"#c0c0c0","sky blue":"#87ceeb","slate blue":"#6a5acd","slategray":"#708090","snow":"#fffafa","spring green":"#00ff7f","steel blue":"#4682b4",
    "tan":"#d2b48c","teal":"#008080","thistle":"#d8bfd8","tomato":"#ff6347","turquoise":"#40e0d0",
    "violet":"#ee82ee",
    "wheat":"#f5deb3","white":"#ffffff","white smoke":"#f5f5f5",
    "yellow":"#ffff00","yellow green":"#9acd32"}

    if color.lower() in color: #(typeof colors[color.toLowerCase()] != 'undefined')
        return colors[color.lower()]
    else:
        print("colorNameToHex: no match. Returning white (#ffffff)")
        return "#ffffff"



XYPoint = namedtuple('XYPoint', ['x', 'y'])


def is_hex_color(color):
    if isinstance(color,str):
        color = color.strip().rstrip()
        if (color.startswith('#') and len(color) == 7) or len(color) == 6:
            valid_chars = ['1','2','3','4','5','6','7','8','9','0','A','B','C','D','E','F']
            for i in range(len(color) - 1, len(color) - 7, -1):
                print(i, "color[i]: ", color[i])
                if color[i].upper() not in valid_chars:
                    return False
            return True
    return False
            

# from: https://github.com/benknight/hue-python-rgb-converter/blob/master/rgbxy/__init__.py
def hex_to_xy(hex):
    try:
        hex = str(hex).replace('#', '')
        print("hex_to_xy: parsing hex: " + str(hex))
        #self, red_i, green_i, blue_i
    
        red_i = hex_to_red(hex)
        green_i = hex_to_green(hex)
        blue_i = hex_to_blue(hex)
    
        red = red_i / 255.0
        green = green_i / 255.0
        blue = blue_i / 255.0

        r = ((red + 0.055) / (1.0 + 0.055))**2.4 if (red > 0.04045) else (red / 12.92)
        g = ((green + 0.055) / (1.0 + 0.055))**2.4 if (green > 0.04045) else (green / 12.92)
        b = ((blue + 0.055) / (1.0 + 0.055))**2.4 if (blue > 0.04045) else (blue / 12.92)

        X = r * 0.664511 + g * 0.154324 + b * 0.162028
        Y = r * 0.283881 + g * 0.668433 + b * 0.047685
        Z = r * 0.000088 + g * 0.072310 + b * 0.986039

        cx = X / (X + Y + Z)
        cy = Y / (X + Y + Z)

        # Check if the given XY value is within the colourreach of Hue lamps.
        xy_point = XYPoint(cx, cy)
    
        # TODO: how to deal with color reach?
        #in_reach = self.check_point_in_lamps_reach(xy_point)

        #if not in_reach:
        #    xy_point = self.get_closest_point_to_point(xy_point)

        return xy_point
    except Exception as ex:
        print("Util: error in hex_to_xy: " + str(ex))
        return XYPoint(0.5, 0.5) # Wild guess..
        

def hex_to_red(hex):
    """Parses a valid hex color string and returns the Red RGB integer value."""
    return int(hex[0:2], 16)

def hex_to_green(hex):
    """Parses a valid hex color string and returns the Green RGB integer value."""
    return int(hex[2:4], 16)

def hex_to_blue(hex):
    """Parses a valid hex color string and returns the Blue RGB integer value."""
    return int(hex[4:6], 16)

def hex_to_rgb(h):
    """Converts a valid hex color string to an RGB array."""
    rgb = (hex_to_red(h), hex_to_green(h), hex_to_blue(h))
    return rgb

def rgb_to_hex(r, g, b):
    """Converts RGB to hex."""
    return '%02x%02x%02x' % (r, g, b)


def xy_to_hex(x, y, bri=1):
    try:
        xy_point = XYPoint(x, y)
        #if not self.check_point_in_lamps_reach(xy_point):
            # Calculate the closest point on the color gamut triangle
            # and use that as xy value See step 6 of color to xy.
        #    xy_point = self.get_closest_point_to_point(xy_point)

        # Calculate XYZ values Convert using the following formulas:
        Y = bri
        X = (Y / xy_point.y) * xy_point.x
        Z = (Y / xy_point.y) * (1 - xy_point.x - xy_point.y)

        # Convert to RGB using Wide RGB D65 conversion
        r = X * 1.656492 - Y * 0.354851 - Z * 0.255038
        g = -X * 0.707196 + Y * 1.655397 + Z * 0.036152
        b = X * 0.051713 - Y * 0.121364 + Z * 1.011530

        # Apply reverse gamma correction
        r, g, b = map(
            lambda x: (12.92 * x) if (x <= 0.0031308) else ((1.0 + 0.055) * pow(x, (1.0 / 2.4)) - 0.055),
            [r, g, b]
        )

        # Bring all negative components to zero
        r, g, b = map(lambda x: max(0, x), [r, g, b])

        # If one component is greater than 1, weight components by that value.
        max_component = max(r, g, b)
        if max_component > 1:
            r, g, b = map(lambda x: x / max_component, [r, g, b])

        r, g, b = map(lambda x: int(x * 255), [r, g, b])

        # Convert the RGB values to your color object The rgb values from the above formulas are between 0.0 and 1.0.
        #return (r, g, b)
        return '%02x%02x%02x' % (r, g, b)
    
    except Exception as ex:
        print("Util: error in xy_to_hex: " + str(ex))
        return '#FFAA00' # orange


#
#   HSV - HUE SATURATION AND (BRIGHTNESS) VALUE
#

# from https://codeigo.com/python/convert-hex-to-rgb-and-hsv/
def hex_to_hsv(h):
    if str(h).startswith('#'):
        h = str(h)[1:]
    return rgb2hsv(hex_to_red(h),hex_to_green(h),hex_to_blue(h))

def rgb2hsv(r, g, b):
	# Normalize R, G, B values
	r, g, b = r / 255.0, g / 255.0, b / 255.0
 
	# h, s, v = hue, saturation, value
	max_rgb = max(r, g, b)    
	min_rgb = min(r, g, b)   
	difference = max_rgb-min_rgb 
 
	# if max_rgb and max_rgb are equal then h = 0
	if max_rgb == min_rgb:
    		h = 0
	 
	# if max_rgb==r then h is computed as follows
	elif max_rgb == r:
    		h = (60 * ((g - b) / difference) + 360) % 360
 
	# if max_rgb==g then compute h as follows
	elif max_rgb == g:
    		h = (60 * ((b - r) / difference) + 120) % 360
 
	# if max_rgb=b then compute h
	elif max_rgb == b:
    		h = (60 * ((r - g) / difference) + 240) % 360
 
	# if max_rgb==zero then s=0
	if max_rgb == 0:
    		s = 0
	else:
    		s = (difference / max_rgb) * 100
 
	# compute v
	v = max_rgb * 100
	# return rounded values of H, S and V
	return tuple(map(round, (h, s, v)))
 
#print(rgb2hsv(24, 12, 39))


#print("is_hex_color: ", is_hex_color('#FF0077'))
#hsv = hex_to_hsv('#FF0077')
#print("HSV OUTPUT: ", hsv)


# HSV to RGB

#scalar = float # a scale value (0.0 to 1.0)
#def hsv_to_rgb( h:scalar, s:scalar, v:scalar, a:scalar ) -> tuple:
def hsv_to_rgb( h, s, v, a):
    if s:
        if h == 1.0: h = 0.0
        i = int(h*6.0); f = h*6.0 - i
        
        w = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        
        if i==0: return (v, t, w, a)
        if i==1: return (q, v, w, a)
        if i==2: return (w, v, t, a)
        if i==3: return (w, q, v, a)
        if i==4: return (t, w, v, a)
        if i==5: return (v, w, q, a)
    else: return (v, v, v, a)


def hsv_to_hex(h,s,v=1,a=1):
    rgba = hsv_to_rgb(h,s,v,a)
    print("hsv_to_hex:  rgba: ", rgba)
    return rgb_to_hex(rgba[0],rgba[1],rgba[2])









def humanize_cluster_id(cluster_id):
    if str(cluster_id).isdigit():
        cluster_id = int(cluster_id)
        cluster = f"{ALL_CLUSTERS[cluster_id].__name__}"
        return cluster
    return str(cluster_id)
    
def humanize_attribute_id(cluster_id,attribute_id):
    if str(cluster_id).isdigit() and str(attribute_id).isdigit():
        cluster_id = int(cluster_id)
        attribute_id = int(attribute_id)
        attribute = f"{ALL_ATTRIBUTES[cluster_id][attribute_id].__name__}"
        return attribute
    return str(attribute_id)

def humanize(code):
    if '/' in str(code):
        parts = str(code).split('/')
        #print("humanize: parts: ", parts)
        if len(parts) == 3:
            cluster_id = int(parts[1])
            attribute_id = int(parts[2])
            #cluster = f"{ALL_CLUSTERS[cluster_id].__name__}"
            #print("humanize: cluster: ", cluster)
            #attribute = f"{ALL_ATTRIBUTES[cluster_id][attribute_id].__name__}"
            #print("humanize: attribute: ", cluster)
            code = humanize_cluster_id(cluster_id) + '.Attributes.' + humanize_attribute_id(cluster_id,attribute_id)
            #print("humanize: final code: ", code)
    return str(code)




# 6 = OnOff
# 8 = LevelControl
# 40 = BasicInformation
# 44 = TimeFormatLocalization
# 47 = PowerSource
# 51 = GeneralDiagnostics
# 59 = Switch
# 768 = ColorControl

def get_commands_for_cluster_id(cluster_id):
    commands_lookup = {}
    #print("in get_commands_for_cluster.  cluster_id: ", cluster_id)
    if str(cluster_id).isdigit():
        cluster_id = int(cluster_id)
        try:
            
            if cluster_id in ALL_CLUSTERS:
                cluster_name = f"{ALL_CLUSTERS[cluster_id].__name__}"
                commands = getattr(ALL_CLUSTERS[cluster_id], 'Commands')
                commands_dir_list = dir(commands)
                for key in commands_dir_list:
                    if str(key).startswith('__'):
                        continue
                    if str(key) == 'TestEventTrigger':
                        continue
                    elif str(key) == 'TimeSnapshot':
                        continue
                    command = getattr(ALL_CLUSTERS[cluster_id].Commands, key)
                    command_dict = command.__dict__
                    command_id = command_dict['command_id']
                    
                    if not cluster_name in commands_lookup:
                        commands_lookup[cluster_name] = {}
                        
                        
                    if not str(key) in commands_lookup[cluster_name]:
                        commands_lookup[cluster_name][str(key)] = {'id':command_id,'name':str(key)}
                        #commands_lookup[cluster_name]['id_from_name'][str(key)] = command_id
                        #commands_lookup[cluster_name]['name_from_id'][str(command_id)] = str(key)
                        
                        # commands instance:  ColorControl.Commands.MoveColorTemperature(moveMode=0, rate=0, colorTemperatureMinimumMireds=0, colorTemperatureMaximumMireds=0, optionsMask=0, optionsOverride=0)
                        # TODO: if need be, in the future the individual parameters could also be added
                        
            #else:
            #    print("\nERROR: get_commands_for_cluster: cluster_id not spotted in ALL_CLUSTERS: ", cluster_id)
        except Exception as ex:
            pass
            #print("\nERROR, get_commands_for_cluster: caught error trying to get commands: ", ex)
    
    #print("FINAL commands_lookup: ", commands_lookup)   
    return commands_lookup 

#get_commands_for_cluster(768)

#print("\n\n\nListClusterInfo: ")
#ListClusterInfo()

#print("\n\n\nListClusterCommands: ")
#ListClusterCommands()

#print("\n\n\nListClusterAttributes: ")
#ListClusterAttributes()



def get_events_lookup():
    events_lookup = {}
    for key, value in ALL_EVENTS.items():
        print("+", key)
        
        events_list = []
        
        
        #print("-> ", type(value), str(value))
        for key2 in value:
            #print("key2: ", key2, value[key2].__name__)
            events_list.append(value[key2].__name__)
            #print("type(value[key2]): ", type(value[key2]), value[key2].__dict__)
            #for key3 in value[key2].__dict__:
            #    if(str(key3).startswith('__')):
            #        continue
            #    print("---> key3: ", key3)
        
        if len(events_list):
            
            events_lookup[humanize_cluster_id(int(key))] = events_list
        #print("")
        #print(">>", dir(value))
        #for key2, value2 in value:
        #    print("ALL_EVENTS key2,value2: ", key2, value2)
        

    #print("")
    return events_lookup



def get_enums_lookup():
    enums_lookup = {}

    try:
        dir_list = dir(cluster_details)
        for key in dir_list:
            if str(key).startswith('__'):
                continue
            #print("get_enums_lookup: checking key: ", key)
            
    
            try:
                instance = getattr(cluster_details, str(key))()
                enums = getattr(instance, 'Enums')
                if enums:
                    
                    for attr, value in enums.__dict__.items():
                        if str(attr).startswith('__'):
                            continue
                        #print("-->", enums.__dict__[attr])
                        #print("---->", list(enums.__dict__[attr]))
                        enum_list = list(enums.__dict__[attr])
                        names = [member.name for member in enum_list]
                        #print("names: ", names)
                        enums_lookup[str(key)] = []
                        for enum_name in names:
                            #print("enum_name: ", enum_name)
                            if str(enum_name).startswith('k'):
                                enums_lookup[str(key)].append(str(enum_name)[1:])
                            else:
                                enums_lookup[str(key)].append(str(enum_name))
                    
                        #print([e.name for e in enum_list])
                        #for item_index in enum_list:
                        #    print("....", item_index, enum_list[item_index])
                
            except Exception as ex:
                pass
                #print("no enums for key: ", key)
            #print(dir(instance))
            #print("instance: ", instance)

        #for subclass in cluster_details.__subclasses__():
        #    print("subclass name: ", subclass.__name__)    
    
        #for key in str(dir_list).splitlines():
        #    print("key: ", key)
        #    if str(key).startswith('__'):
        #        continue
            #my_instance = MyClass()
            #print(dir(cluster_details[key]))
    
    
    
    except Exception as ex:
        print("matter_util.py: caught error creating enums lookup: ", ex)
    
    #print("enums_lookup: ", enums_lookup)
    return enums_lookup

#def show_clusters():
#    
#    print("ALL_ATTRIBUTES: ", ALL_ATTRIBUTES)
#    for cluster_id in range(3,16):
#        #if str(cluster_id) in ALL_ATTRIBUTES:
#        for attribute_id, attribute in ALL_ATTRIBUTES[cluster_id].items():
#            print(cluster_id, ": ", attribute_id, " -> ", attribute)


# Turns numbered attributes style list into human readable attributes tree
def process_node(node):
    """Process a node."""
    endpoints = {}
    cluster_warn = set()

    new_attributes={}
    
    clusters_to_ignore = ['OtaSoftwareUpdateRequestor','AccessControl','Descriptor','IcdManagement','OperationalCredentials','WiFiNetworkDiagnostics','ThreadNetworkDiagnostics','AdministratorCommissioning','NetworkCommissioning','GeneralCommissioning','GroupKeyManagement','Identify','Groups']

    for attr_path, value in node["attributes"].items():
        endpoint_id, cluster_id, attr_id = attr_path.split("/")
        cluster_id = int(cluster_id)
        endpoint_id = int(endpoint_id)
        attr_id = int(attr_id)
        
        
        if cluster_id == 5: # "Scenes" cluster is not officially supported anymore. Even though IKEA still uses it?
            continue
        
        attribute_path=''
        if cluster_id in ALL_CLUSTERS:
            cluster_name = f"{ALL_CLUSTERS[cluster_id].__name__}"
            if cluster_name in clusters_to_ignore:
                continue
                
            print("process_node:  cluster_id,cluster_name: ", cluster_id, cluster_name)
            attribute_path = f"{ALL_CLUSTERS[cluster_id].__name__}.Attributes."
        else:
            if cluster_id not in cluster_warn:
                print("Unknown cluster ID: {}".format(cluster_id))
                cluster_warn.add(cluster_id)
            cluster_name = f"{cluster_id} (unknown)"
            attribute_path = f"{cluster_id}.Attributes."

        if cluster_id in ALL_ATTRIBUTES and attr_id in ALL_ATTRIBUTES[cluster_id]:
            attr_name = f"{ALL_ATTRIBUTES[cluster_id][attr_id].__name__}"
            attribute_path += attr_name
        else:
            if cluster_id not in cluster_warn:
                print(
                    "Unknown attribute ID: {} in cluster {} ({})".format(
                        attr_id, cluster_name, cluster_id
                    )
                )
            attr_name = f"{attr_id} (unknown)"
            attribute_path += f"{attr_id}"
        
        endpoint_name = 'Endpoint' + str(endpoint_id)
        if not endpoint_name in new_attributes:
            new_attributes[endpoint_name] = {}
            
        
        if endpoint_id not in endpoints:
            endpoints[endpoint_id] = {}

        if cluster_name not in endpoints[endpoint_id]:
            endpoints[endpoint_id][cluster_name] = {}

        if attribute_path not in new_attributes[endpoint_name]:
            new_attributes[endpoint_name][attribute_path] = value

        endpoints[endpoint_id][cluster_name][attr_name] = value
        if attr_name == 'AcceptedCommandList' and isinstance(value,list):
            accepted_commands = get_commands_for_cluster_id(cluster_id)
            if accepted_commands and attr_name in accepted_commands:
                humanized_commands_list = {}
                for command_name in list(accepted_commands[attr_name].keys()):
                    if self.DEBUG:
                        print("checking if command is supported: ", command_name)
                    if 'id' in accepted_commands[attr_name] and accepted_commands[attr_name]['id'] in value:
                        if self.DEBUG:
                            print("process_node: COMMAND IS ACCEPTED: ", attribute_path, command_name)
                        humanized_commands_list[str(accepted_commands[attr_name]['id'])] = command_name
                    else:
                        if self.DEBUG:
                            print("process_node: COMMAND IS _NOT_ ACCEPTED: ", attribute_path, command_name)
            
            
        
        
        

    # Augment device types
    for endpoint in endpoints.values():
        if not (descriptor_cls := endpoint.get("Descriptor")):
            continue

        if not (device_types := descriptor_cls.get("DeviceTypeList")):
            continue
        try:
            for device_type in device_types:
                if "deviceType" in device_type:
                    device_type_id = device_type["deviceType"]
                    if device_type_id in ALL_TYPES:
                        device_type_name = ALL_TYPES[device_type_id].__name__
                    else:
                        device_type_name = f"{device_type} (unknown)"

                    device_type["name"] = device_type_name
                    device_type["hex"] = f"0x{device_type_id:04x}"
        except Exception as ex:
            print("matter_util.py: caught error in process_node while trying to figure out device type: ", ex)
        
    node['attributes_list'] = new_attributes
    
    node["attributes"] = {
        f"Endpoint{endpoint_id}": clusters
        for endpoint_id, clusters in endpoints.items()
    }
    




def uncamel(value):
    output = ''
    if isinstance(value,str) and len(value) > 1:
        for char in value:
            if char.isupper():
                output += "_" + char.lower()
            else:
                output += char
        if output.startswith("_"):
            output = output[1:]
    if output == '':
        output = str(value)
    return output



def boolean_list_to_number(bools):
    return ((1 if bools[0] else 0) << 0) | \
           ((1 if bools[1] else 0) << 1) | \
           ((1 if bools[2] else 0) << 2) | \
           ((1 if bools[3] else 0) << 3) | \
           ((1 if bools[4] else 0) << 4) | \
           ((1 if bools[5] else 0) << 5) | \
           ((1 if bools[6] else 0) << 6) | \
           ((1 if bools[7] else 0) << 7)

def number_to_boolean_list(num):
    return [bool((num >> i) & 1) for i in range(8)]




"""
From Zigbee2MQTT addon
        
# thanks to https://stackoverflow.com/questions/20283401/php-how-to-convert-rgb-color-to-cie-1931-color-specification
def HEXtoXY(hex) { 
	hex = hex.replace(/^#/, '')
	aRgbHex = hex.match(/.{1,2}/g)
	red = int(aRgbHex[0], 16);
	green = int(aRgbHex[1], 16);
	blue = int(aRgbHex[2], 16);

	red = (red > 0.04045) ? Math.pow((red + 0.055) / (1.0 + 0.055), 2.4) : (red / 12.92);
	green = (green > 0.04045) ? Math.pow((green + 0.055) / (1.0 + 0.055), 2.4) : (green / 12.92);
	blue = (blue > 0.04045) ? Math.pow((blue + 0.055) / (1.0 + 0.055), 2.4) : (blue / 12.92);
	var X = red * 0.664511 + green * 0.154324 + blue * 0.162028;
	var Y = red * 0.283881 + green * 0.668433 + blue * 0.047685;
	var Z = red * 0.000088 + green * 0.072310 + blue * 0.986039;
	var fx = X / (X + Y + Z);
	var fy = Y / (X + Y + Z);

	return [fx.toPrecision(2), fy.toPrecision(2)];
}



function XYtoHEX(x, y, bri) { // and needs brightness too
	const z = 1.0 - x - y;
	if (x == 0) {
		x = 0.00001
	};
	if (y == 0) {
		y = 0.00001
	};
	if (bri == 0) {
		bri = 1
	};
	const Y = bri / 255.0; // Brightness of lamp
	const X = (Y / y) * x;
	const Z = (Y / y) * z;
	var r = X * 1.612 - Y * 0.203 - Z * 0.302;
	var g = -X * 0.509 + Y * 1.412 + Z * 0.066;
	var b = X * 0.026 - Y * 0.072 + Z * 0.962;

	r = r <= 0.0031308 ? 12.92 * r : (1.0 + 0.055) * Math.pow(r, (1.0 / 2.4)) - 0.055;
	g = g <= 0.0031308 ? 12.92 * g : (1.0 + 0.055) * Math.pow(g, (1.0 / 2.4)) - 0.055;
	b = b <= 0.0031308 ? 12.92 * b : (1.0 + 0.055) * Math.pow(b, (1.0 / 2.4)) - 0.055;

	const maxValue = Math.max(r, g, b);
	r /= maxValue;
	g /= maxValue;
	b /= maxValue;
	r = r * 255;
	if (r < 0) {
		r = 0
	};
	if (r > 255) {
		r = 255
	};
	g = g * 255;
	if (g < 0) {
		g = 0
	};
	if (g > 255) {
		g = 255
	};
	b = b * 255;
	if (b < 0) {
		b = 0
	};
	if (b > 255) {
		b = 255
	};

	r = Math.floor(r).toString(16);
	g = Math.floor(g).toString(16);
	b = Math.floor(b).toString(16);

	if (r.length < 2)
		r = "0" + r;
	if (g.length < 2)
		g = "0" + g;
	if (b.length < 2)
		b = "0" + b;

	return "#" + r + g + b;
}
"""






"""
def process_node_old(node):
    endpoints = {}
    cluster_warn = set()

    for attr_path, value in node["attributes"].items():
        endpoint_id, cluster_id, attr_id = attr_path.split("/")
        cluster_id = int(cluster_id)
        endpoint_id = int(endpoint_id)
        attr_id = int(attr_id)

        if cluster_id in ALL_CLUSTERS:
            cluster_name = f"{ALL_CLUSTERS[cluster_id].__name__} ({cluster_id} / 0x{cluster_id:04x})"
        else:
            if cluster_id not in cluster_warn:
                print("Unknown cluster ID: {}".format(cluster_id))
                cluster_warn.add(cluster_id)
            cluster_name = f"{cluster_id} (unknown)"

        if cluster_id in ALL_ATTRIBUTES and attr_id in ALL_ATTRIBUTES[cluster_id]:
            attr_name = f"{ALL_ATTRIBUTES[cluster_id][attr_id].__name__} ({attr_id} / 0x{attr_id:04x})"
        else:
            if cluster_id not in cluster_warn:
                print(
                    "Unknown attribute ID: {} in cluster {} ({})".format(
                        attr_id, cluster_name, cluster_id
                    )
                )
            attr_name = f"{attr_id} (unknown)"

        if endpoint_id not in endpoints:
            endpoints[endpoint_id] = {}

        if cluster_name not in endpoints[endpoint_id]:
            endpoints[endpoint_id][cluster_name] = {}

        endpoints[endpoint_id][cluster_name][attr_name] = value

    # Augment device types
    for endpoint in endpoints.values():
        if not (descriptor_cls := endpoint.get("Descriptor (29 / 0x001d)")):
            continue

        if not (device_types := descriptor_cls.get("DeviceTypeList (0 / 0x0000)")):
            continue
        try:
            for device_type in device_types:
                if "deviceType" in device_type:
                    device_type_id = device_type["deviceType"]
                    if device_type_id in ALL_TYPES:
                        device_type_name = ALL_TYPES[device_type_id].__name__
                    else:
                        device_type_name = f"{device_type} (unknown)"

                    device_type["name"] = device_type_name
                    device_type["hex"] = f"0x{device_type_id:04x}"
        except Exception as ex:
            print("matter_util.py: caught error in process_node: ", ex)
        

    node["attributes"] = {
        f"Endpoint {endpoint_id}": clusters
        for endpoint_id, clusters in endpoints.items()
    }

"""





        
