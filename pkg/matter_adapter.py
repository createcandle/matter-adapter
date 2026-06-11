"""
Matter addon for Candle Controller.
    START_LISTENING = "start_listening"
    SERVER_DIAGNOSTICS = "diagnostics"
    SERVER_INFO = "server_info"
    GET_NODES = "get_nodes"
    GET_NODE = "get_node"
    COMMISSION_WITH_CODE = "commission_with_code"
    COMMISSION_ON_NETWORK = "commission_on_network"
    SET_WIFI_CREDENTIALS = "set_wifi_credentials"
    SET_THREAD_DATASET = "set_thread_dataset"
    OPEN_COMMISSIONING_WINDOW = "open_commissioning_window"
    DISCOVER = "discover"
    INTERVIEW_NODE = "interview_node"
    DEVICE_COMMAND = "device_command"
    REMOVE_NODE = "remove_node"
    GET_VENDOR_NAMES = "get_vendor_names"
    READ_ATTRIBUTE = "read_attribute"
    WRITE_ATTRIBUTE = "write_attribute"
    PING_NODE = "ping_node"
    GET_NODE_IP_ADDRESSES = "get_node_ip_addresses"
    IMPORT_TEST_NODE = "import_test_node"
    CHECK_NODE_UPDATE = "check_node_update"
    UPDATE_NODE = "update_node"
    SET_DEFAULT_FABRIC_LABEL = "set_default_fabric_label"
    SET_ACL_ENTRY = "set_acl_entry"
    SET_NODE_BINDING = "set_node_binding"

    discoverCommissionableNodes
    getMatterFabrics
    removeMatterFabric
"""


# sudo /home/pi/.webthings/addons/matter-adapter/thread/ot-ctl state



import os
import re
import sys
# This helps the addon find python libraries it comes with, which are stored in the "lib" folder. The "package.sh" file will download Python libraries that are mentioned in requirements.txt and place them there.
lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')
if lib_path not in sys.path:
	sys.path.append(lib_path)

import json
import time
#import requests
#import subprocess
#import datetime
#import requests  # noqa
#import threading
import subprocess


# This loads the parts of the addon.
from gateway_addon import Database, Adapter, Device, Property
# Database - needed to read from the settings database. If your addon doesn't have any settings, then you don't need this.
from .matter_device import MatterDevice

#from .matter_util import process_node, uncamel, humanize, humanize_cluster_id, get_enums_lookup, get_commands_for_cluster_id, clusters_to_ignore
from .matter_util import *



try:
    from .matter_adapter_api_handler import *
except Exception as ex:
    print("Error, unable to load MatterAdapterApiHandler (which is used for UI extention): " + str(ex))

import traceback




# Not sure what this is used for, but leave it in.
_TIMEOUT = 3

# Not sure what this is used for either, but leave it in.
_CONFIG_PATHS = [
    os.path.join(os.path.expanduser('~'), '.webthings', 'config'),
]

# Not sure what this is used for either, but leave it in.
if 'WEBTHINGS_HOME' in os.environ:
    _CONFIG_PATHS.insert(0, os.path.join(os.environ['WEBTHINGS_HOME'], 'config'))




import logging
import argparse
from os.path import abspath, dirname
from pathlib import Path
#from sys import path

#import aiohttp
import asyncio
#from aiorun import run
import coloredlogs

sys.path.insert(1, dirname(dirname(abspath(__file__))))
#from matter_server.client.client import MatterClient  # noqa: E402
#from matter_server.server.server import MatterServer  # noqa: E402

# DEV
#from chip.clusters import Objects as clusters
#from chip.clusters import ClusterCommand

#import json
# Clusters.ThreadNetworkDiagnostics.Enums
#print(json.dumps(clusters,indent=4))


# Import the ability to turn objects into dictionaries, and vice-versa
#from matter_server.common.helpers.util import dataclass_from_dict,dataclass_to_dict,create_attribute_path_from_attribute

"""
from matter_server.common.helpers.util import dataclass_from_dict,dataclass_to_dict
from matter_server.common.models import (
    CommandMessage,
    ErrorResultMessage,
    EventMessage,
    MessageType,
    ServerInfoMessage,
    SuccessResultMessage,
)
"""

# client
import threading
import websocket
import _thread

from threading import Lock

#import rel

import traceback


logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)


DEFAULT_VENDOR_ID = 0xFFF1
DEFAULT_FABRIC_ID = 1
DEFAULT_PORT = 5580
DEFAULT_URL = f"http://127.0.0.1:{DEFAULT_PORT}/ws"
#DEFAULT_STORAGE_PATH = '/home/pi/.webthings/data/matter-adapter/hasdata' #os.path.join(Path.home(), ".matter_server")
DEFAULT_STORAGE_PATH = os.path.join(Path.home(), ".webthings","data","matter-adapter","hasdata")

#print("Path.home(): " + str(Path.home()))

logging.basicConfig(level=logging.DEBUG)
#logging.basicConfig(handlers=None, level="DEBUG")
#coloredlogs.install(level="DEBUG")

# matter BLE discriminator is maybe 3840
# https://github.com/project-chip/connectedhomeip/issues/26968


class MatterAdapter(Adapter):
    """Adapter for addon """

    def __init__(self, verbose=False):
        """
        Initialize the object.

        verbose -- whether or not to enable verbose logging
        """

        #print("Starting Matter adapter init")

        self.ready = False # set this to True once the init process is complete.
        self.addon_id = 'matter-adapter'


        self.name = self.__class__.__name__ # TODO: is this needed?
        Adapter.__init__(self, self.addon_id, self.addon_id, verbose=verbose)


        self.boot_path = '/boot'
        if os.path.isdir('/boot/firmware'):
            self.boot_path = '/boot/firmware'

        

        matter_already_running_check = str(run_command('ps aux | grep matter'))
        if 'matter_server' in matter_already_running_check:
            print("\n\nMatter adapter: ERROR, a matter_server instance seemed to already be running!\nUsing pkill to stop it..\n\n")
            os.system('sudo pkill -f matter_server')
            time.sleep(5)


        matter_http_server_pid = str(run_command(r"sudo lsof -i :5580 | grep ':5580 (ESTABLISHED)' | awk -F' ' '{print $2}'"))
        if matter_http_server_pid and str(matter_http_server_pid).isdigit():
            print("\n\nMatter adapter: ERROR, matter HTTP seemed to still/already be running!\nUsing sudo kill -9 to stop it..\n\n")
            run_command('sudo kill -9 ' + str(matter_http_server_pid))
            time.sleep(5)
        

        """
        # too complex
        if ':5580 (ESTABLISHED)' in matter_http_server_check:
            if
            matter_http_server_check = matter_http_server_check.replace('python3.1','')
            matter_http_server_check = matter_http_server_check.replace('python3','')
            matter_http_server_check = matter_http_server_check.strip()
            first_word = .split(' ',1)[0]
            matter_http_server_pid = matter_http_server_check.split(' ',1)[0]
            if matter_http_server_pid.isdigit():
                
            else:
                print("matter_http_server_pid was not a number?: ", matter_http_server_pid)
        """
        


        #print(run_command('printenv'))

        self.s_print_lock = Lock()

        # set up some variables
        self.DEBUG = False
        self.DEBUG2 = False
        self.DEVICE_DEBUG = False

        self.should_save = False
        self.auto_enable_properties = True

        #show_clusters()
        #return

        # There is a very useful variable called "user_profile" that has useful values from the controller.
        #print("self.user_profile: " + str(self.user_profile))

        self.nmcli_installed = False
        nmcli_check = run_command('which nmcli')
        if isinstance(nmcli_check,str) and str(nmcli_check).startswith('/'):
            self.nmcli_installed = True

        self.running = True
        self.addon_start_time = time.time()

        self.server = None
        self.server_process = None
        self.matter_server_type = 'Python'
        self.matter_collision_detected = False

        self.matter_network_interface_found = False
        self.actual_interfaces = []
        self.available_interfaces = []
        #if self.nmcli_installed:
        #    self.update_network_interfaces()
        

        #self.client = None
        #self.unsubscribe = None

        self.port = 5580
        self.message_counter = 0
        self.matter_client_connected = False
        self.disable_matter_dashboard = True

        #self.vendor_id = ""
        self.missing_vendor_id = False

        self.discovered = []
        self.nodes = []

        self.raw_mdns = ''
        self.last_get_nodes_timestamp = 0

        #self.switch_events = ['Switch latched','Initial press','Long press','Short release','Long release','Multi press ongoing','Multi press complete']

        self.certificates_updated = False
        self.busy_updating_certificates = False
        self.time_between_certificate_downloads = 14 * 86400 # 14 days

        self.busy_discovering = False
        self.pairing_failed = False
        self.busy_pairing = False
        self.last_pairing_start_time = 0
        self.last_pairing_update_time = 0
        self.pairing_phase = 0
        self.pairing_phase_message = ''
        self.pairing_attempt = -1
        self.pairing_method = None # i.e. bluetooth
        self.wireless_type = 'unknown' # can be 'unknown', 'wifi' or 'thread'
        self.last_decoded_pairing_code = ''
        self.last_found_pairing_code = ''
        self.last_found_pin_code = ''
        self.last_used_pairing_type = None

        self.device_was_deleted = False # set to True is a device is deleted from the Matter fabric

        self.share_node_code = "" # used with open window

        self.brightness_transition_time = 0

        self.add_hacky_properties = True

        self.missing_devices = []
        self.node_thing_id_lookup = {} # map the Matter node ID's to the unique device ID's of the actual matter devices
    
        # THREAD / OTBR
        self.thread_network_name = 'CandleThread'
        self.otbr_thread = None
        self.found_thread_radio_again = False
        self.found_new_thread_radio = False
        self.found_a_thread_radio_once = False
        self.thread_radio_went_missing = False
        self.thread_radio_is_alive_count = 0 # how many spinel messages have been received
        self.last_thread_radio_is_alive_timestamp = 0
        self.help_thread_devices_to_connect_to_the_internet = False
        self.thread_netdata_registered = False
        self.thread_region = 'EU'
        self.use_candle_meshlocal_prefix = False
        
        self.thread_add_factory_config_file = False

        self.otbr_starting_timestamp = None
        self.otbr_stopping_timestamp = 0
        self.last_time_otbr_started = time.time()
        self.should_start_otbr = True
        self.should_start_thread_mesh = False
        self.should_create_thread_mesh = False
        self.otbr_started = False # This is the first stage, done by otbr-agent

        self.thread_set_active = False # This is the second stage, managed by ot-ctl. TODO This variable is not really used for anything, and is just confusing now
        self.informed_matter_server_about_thread = False
        self.thread_running = False # becomes true when Thread is completely up
        self.thread_error = ''
        self.otbr_agent_process = None
        self.otbr_stdout_messages = []
        self.thread_channel = 26
        self.thread_dataset = ''
        self.thread_dataset_loaded = False
        self.thread_state_info = ''
        self.thread_netdata_info = ''
        
        self.turn_wifi_back_on_at = 0
        self.extension_cable_recommended = False
        self.last_time_otbr_restarted = 0
        self.serial_before = None # used to detect newly plugged in USB sticks by comparing before and after of lsusb
        self.last_received_server_info = None
        self.noise_counter = 0  # resets every 5 seconds
        self.timeout_counter = 0 # resets every 5 seconds
        self.all_timeout_counter = 0 # keeps track of total timeout count
        self.previous_noise_counter = 0 # used to count noise per time unit
        self.noise_delta = 0 # hot many instances of noise were counted during 5 seconds
        self.previous_timeout_counter = 0
        self.timeout_delta = 0

        self.thread_diagnostics = {}
        self.reconnected_devices = {} # holds node ID's (integers) of reconnected devices

        self.enums_lookup = get_enums_lookup()
        self.events_lookup = get_events_lookup()

        self.completed_command_clusters = [] # Will be filled with cluster_id's that have already been lookup up through get_commands_for_cluster_id
        self.commands_lookup = {} # will be filled as needed by calling get_commands_for_cluster_id(). The first key is the cluster_name



        self.should_start_matter_time = 0 # experiment to wait a while before starting matter, and give thread some time to set itself up first.
        self.should_start_matter = False
        self.matter_server_running = False
        self.matter_running = False
        self.default_matter_fabric_name = "Home"
        self.matter_fabrics = None
        self.matter_stopping_timestamp = 0
        self.get_ips_interval = 600 # every 10 minutes request all the IP addresses
        self.last_get_ips_timestamp = time.time()
        self.last_matter_ip_check_response_timestamp = 0
        self.should_request_all_nodes_info = True

        # Matter time sync
        self.matter_devices_with_time_sync = []
        self.time_sync_interval = 3600 # every hour sync the clocks
        self.last_time_sync_time = time.time() #int(str(run_command('date +%s')).strip().rstrip())
        self.timezone_name = str(run_command('date +%Z')).strip().rstrip()

        self.last_matter_update_check_timestamp = 0
        self.last_matter_update_check_response_timestamp = 0

        

        #print("self.user_profile: ", self.user_profile)
        #print("")
        #print("self.preferences: ", self.preferences)
        #print("")




        # Hotspot
        self.use_hotspot = True
        self.hotspot_ssid = ""
        self.hotspot_password = ""
        self.hotspot_net_number = None
        if os.path.exists('/boot/firmware/candle_hotspot_net_number.txt'):
            net_number_check = run_command('cat /boot/firmware/candle_hotspot_net_number.txt')
            if isinstance(net_number_check,str):
                net_number_check = net_number_check.rstrip()
                if net_number_check.isdigit():
                    self.hotspot_net_number = int(net_number_check)


        # WiFi
        self.wifi_ssid = ""
        self.wifi_password = ""
        self.wifi_set = False
        self.wifi_restored_early = False # Test to see if WiFi really remains down for the intended duration

        self.wifi_congestion_data = {}

        # not recommended  https://github.com/home-assistant-libs/python-matter-server
        #os.system('sudo sysctl -w net.ipv6.conf.all.forwarding=1')
        #os.system('sudo sysctl -w net.ipv6.conf.wlan0.accept_ra=2')
        #os.system('sudo sysctl -w net.ipv6.conf.wlan0.accept_ra_rt_info_max_plen=64')

        # prefered for thread support:
        #os.system('sudo sysctl -w net.ipv6.conf.wlan0.accept_ra=1')
        #os.system('sudo sysctl -w net.ipv6.conf.wlan0.accept_ra_rt_info_max_plen=64')



        """
        #self.candle_wifi_ssid = ""
        #self.candle_wifi_password = ""
        potential_candle_wifi_ssid = ""
        potential_candle_wifi_ssid = run_command('sudo cat /etc/wpa_supplicant/wpa_supplicant.conf | grep ssid')
        self.s_print("potential_candle_wifi_ssid: " + str(potential_candle_wifi_ssid))

        # get Candle's current WiFi SSID
        count = 0
        for i in potential_candle_wifi_ssid:
            if i == '"':
                count = count + 1
        if count == 2:
            potential_candle_wifi_ssid = potential_candle_wifi_ssid.split('"')[1::2]
            if len(potential_candle_wifi_ssid) == 1:
                self.s_print("potential_candle_wifi_ssid after split: " + str(potential_candle_wifi_ssid))
                potential_candle_wifi_ssid = potential_candle_wifi_ssid[0]
                potential_candle_wifi_ssid = potential_candle_wifi_ssid.rstrip()
                if len(potential_candle_wifi_ssid) > 1:
                    self.candle_wifi_ssid = potential_candle_wifi_ssid

        # get Candle's current WiFi password
        potential_candle_wifi_password = run_command('sudo cat /etc/wpa_supplicant/wpa_supplicant.conf | grep psk')
        self.s_print("potential_candle_wifi_password: " + str(potential_candle_wifi_password))
        self.s_print("len(potential_candle_wifi_password): " + str(len(potential_candle_wifi_password)))
        if len(potential_candle_wifi_password) > 9:
            potential_candle_wifi_password = potential_candle_wifi_password.replace('psk=','')
            self.s_print("potential_candle_wifi_password: " + str(potential_candle_wifi_password))
            potential_candle_wifi_password = potential_candle_wifi_password.rstrip()
            self.candle_wifi_password = potential_candle_wifi_password

        self.s_print("Candle's WiFi SSID: " + str(self.candle_wifi_ssid))
        self.s_print("Candle's WiFi password: " + str(self.candle_wifi_password))
        """

        #print("user profile: " + str(self.user_profile))



        # Create some path strings. These point to locations on the drive.
        self.addon_path = os.path.join(self.user_profile['addonsDir'], self.addon_id) # addonsDir points to the directory that holds all the addons (/home/pi/.webthings/addons).
        self.lib_path = os.path.join(self.addon_path, 'lib')
        self.data_dir_path = os.path.join(self.user_profile['dataDir'], self.addon_id)
        self.other_dir_path = os.path.join(self.addon_path,'other')

        #self.hasdata_dir_path = os.path.join(self.user_profile['baseDir'],'hasdata')
        self.hasdata_dir_path = os.path.join(self.data_dir_path,'hasdata')
        self.hasdata_backup_dir_path = os.path.join(self.data_dir_path,'hasdata_backup')

        # Create the data directory if it doesn't exist yet
        if not os.path.isdir(self.data_dir_path):
            #print("making missing data directory")
            os.system('mkdir -p ' + str(self.data_dir_path))
        
        if not os.path.isdir(self.hasdata_dir_path):
            #print("making missing data directory")
            os.system('mkdir -p ' + str(self.hasdata_dir_path))

        self.persistence_file_path = os.path.join(self.data_dir_path, 'persistence.json') # dataDir points to the directory where the addons are allowed to store their data (/home/pi/.webthings/data)

        self.chip_factory_ini_file_path = os.path.join(self.hasdata_dir_path,'chip_factory.ini')
        self.data_chip_factory_ini_file_path = os.path.join(self.data_dir_path, 'chip_factory.ini')
        #self.credentials_dir_path = os.path.join(self.data_dir_path, 'paa-root-certs')
        self.credentials_dir_path = os.path.join(self.data_dir_path,'credentials','development','paa-root-certs')
        #self.matter_server_base_path = os.path.join(self.addon_path,'matterjs-server')
        #self.matter_serverjs_start_path = os.path.join(self.matter_server_base_path,'packages','matter-server','dist','esm','MatterServer.js') # node_modules/matter-server/dist/esm
        #self.matter_serverjs_start_path = os.path.join(self.matter_server_base_path,'node_modules','matter-server','dist','esm','MatterServer.js')
        self.matter_serverjs_start_path = os.path.join(self.addon_path,'node_modules','matter-server','dist','esm','MatterServer.js')

        self.candle_hotspot_block_ip6_internet_path = os.path.join(self.boot_path, 'candle_hotspot_block_ip6_internet.txt')


        self.otbr_agent_path = os.path.join(self.addon_path,'thread','otbr-agent')
        self.ot_ctl_path = os.path.join(self.addon_path,'thread','ot-ctl')
        self.otbr_web_path = os.path.join(self.addon_path,'thread','otbr-web')
        self.chip_tool_path = os.path.join(self.addon_path,'thread','chip-tool')


        if os.path.isfile(str(self.otbr_agent_path)):
            os.system('chmod +x ' + str(self.otbr_agent_path))
        else:
            self.s_print("\nERROR, otbr-agent is missing!\n")
            return

        if os.path.isfile(str(self.ot_ctl_path)):
            os.system('chmod +x ' + str(self.ot_ctl_path))
        else:
            self.s_print("\nERROR, ot-ctl is missing!\n")
            return

        if os.path.isfile(str(self.chip_tool_path)):
            os.system('chmod +x ' + str(self.chip_tool_path))
        else:
            self.s_print("\nERROR, chip-tool is missing!\n")
            return

        if os.path.isfile(str(self.otbr_web_path)):
            os.system('chmod +x ' + str(self.otbr_web_path))

        self.addon_thread_dir_path = os.path.join(self.addon_path,'thread')
        self.data_thread_dir_path = os.path.join(self.data_dir_path,'thread')
        if not os.path.isdir(str(self.data_thread_dir_path)):
            #print("creating missing data/thread dir: ", self.data_thread_dir_path)
            os.system('mkdir -p ' + str(self.data_thread_dir_path))

        os.chdir(self.data_dir_path)

        pwd = str(run_command('pwd'))
        pwd = pwd.rstrip()

        #self.credentials_dir_path = os.path.join(self.data_dir_path,'credentials','development','paa-root-certs')
        #self.credentials_dir_path = pwd + '/credentials/development/paa-root-certs'
        #print("self.credentials_dir_path: " + str(self.credentials_dir_path))


        self.certs_downloader_path = os.path.join(self.addon_path, 'download_certificates.py')

        # deprecated, as Candle 3.0 has hotspot functionality built-in
        self.hotspot_addon_path = os.path.join(self.user_profile['addonsDir'], 'hotspot')
        self.hotspot_persistence_path = os.path.join(self.user_profile['dataDir'], 'hotspot', 'persistence.json')




        self.persistent_data = {}


        # Get persistent data
        try:
            if os.path.isfile(self.persistence_file_path):
                with open(self.persistence_file_path) as f:
                    self.persistent_data = json.load(f)
                    if self.DEBUG:
                        self.s_print('self.persistent_data was loaded from file: ', JSON.dumps(self.persistent_data,indent=4))

        except Exception as ex:
            if self.DEBUG:
                self.s_print("caught error loading persistent data: ", ex)
            self.persistent_data = {}

        if not 'thread_dataset' in self.persistent_data:
            self.persistent_data['thread_dataset'] = ''
            self.should_save = True

        if 'thread_dataset' in self.persistent_data and isinstance(self.persistent_data['thread_dataset'], str) and len(self.persistent_data['thread_dataset']) > 40:
            self.thread_dataset = self.persistent_data['thread_dataset']

        if not 'thing_index' in self.persistent_data:
            self.persistent_data['thing_index'] = 10
            self.should_save = True

        if not 'leaderweight' in self.persistent_data:
            self.persistent_data['leaderweight'] = 255
            self.should_save = True
        
        if not 'vendor_id' in self.persistent_data:
            self.persistent_data['vendor_id'] = None

        if not 'actual_matter_network_interface' in self.persistent_data:
            self.persistent_data['actual_matter_network_interface'] = None

        if not 'matter_network_interface' in self.persistent_data:
            self.persistent_data['matter_network_interface'] = None

        if not 'onboarding_complete' in self.persistent_data:
            self.persistent_data['onboarding_complete'] = False

        #self.vendor_id = self.persistent_data['vendor_id']

        # LOAD CONFIG
        try:
            self.add_from_config()
        except Exception as ex:
            self.s_print("Error loading config: " + str(ex))

        if self.DEBUG:
            self.s_print("PWD:" + str(pwd))
            self.s_print("initial self.thread_dataset: ", self.thread_dataset)
            self.s_print("")
            self.s_print("\nself.enums_lookup: ", self.enums_lookup)
            self.s_print("")
            self.s_print("\nself.events_lookup: ", self.events_lookup)
            self.s_print("")
            
        #print("")
        #print("\nself.enums_lookup: ", self.enums_lookup)
        #print("")


        # Override vendor ID
        """
        if len(self.vendor_id) > 2 and len(self.vendor_id) < 7:
            #if os.path.exists(self.chip_factory_ini_file_path):
            if os.path.exists(self.data_chip_factory_ini_file_path):
                
                decimal_vendor_id = int(self.vendor_id, 16)

                if os.path.exists(self.chip_factory_ini_file_path):
                    #if self.DEBUG:
                    #    self.s_print("\nWARNING, replacing vendor-id in chip_factory.ini with: " + str(self.vendor_id) + ", in: " + str(self.chip_factory_ini_file_path))
                    os.system("sed -i 's/.*vendor-id=*.*/vendor-id=" + str(decimal_vendor_id) + "/' " + str(self.chip_factory_ini_file_path))

                if os.path.isfile('/data/chip_factory.ini'):
                    #if self.DEBUG:
                    #    self.s_print("\nWARNING, replacing vendor-id in chip_factory.ini with: " + str(self.vendor_id) + ", in: /boot/chip_factory.ini")
                    os.system("sed -i 's/.*vendor-id=*.*/vendor-id=" + str(decimal_vendor_id) + "/' /data/chip_factory.ini")

                if os.path.exists(self.data_chip_factory_ini_file_path):
                    #if self.DEBUG:
                    #    self.s_print("\nWARNING, replacing vendor-id in chip_factory.ini with: " + str(self.vendor_id) + ", in: " + str(self.data_chip_factory_ini_file_path))
                    os.system("sed -i 's/.*vendor-id=*.*/vendor-id=" + str(decimal_vendor_id) + "/' " + str(self.data_chip_factory_ini_file_path))
        """

        # Now we check if all the values that should exist actually do

        if 'wifi_ssid' not in self.persistent_data:
            self.persistent_data['wifi_ssid'] = ""

        if 'wifi_password' not in self.persistent_data:
            self.persistent_data['wifi_password'] = ""

        if 'nodez' not in self.persistent_data:
            self.persistent_data['nodez'] = {}
            self.should_save = True

        if 'pairing_codes' not in self.persistent_data:
            self.persistent_data['pairing_codes'] = {}
            self.should_save = True

        if self.persistent_data['wifi_ssid'] != "" and self.persistent_data['wifi_password'] != "":
            self.wifi_ssid = self.persistent_data['wifi_ssid']
            self.wifi_password = self.persistent_data['wifi_password']

        if 'last_certificates_download_time' not in self.persistent_data:
            self.persistent_data['last_certificates_download_time'] = 0
        elif self.persistent_data['last_certificates_download_time'] > time.time() - self.time_between_certificate_downloads:
            self.certificates_updated = True

        if 'thread_radio_serial_port' not in self.persistent_data:
            self.persistent_data['thread_radio_serial_port'] = None

        if 'matter_network_interface' not in self.persistent_data:
            self.persistent_data['matter_network_interface'] = None


        # Allow the use_hotspot setting to override the wifi credentials
        # TODO: check if the hotspot addon is actually running?
        self.hotspot_addon_installed = False
        if os.path.isdir(self.hotspot_addon_path):
            self.hotspot_addon_installed = True
        

        #print("self.persistent_data: ", json.dumps(self.persistent_data,indent=4))
        

        if not os.path.exists('/boot/firmware/candle_hotspot.txt'):
            self.use_hotspot = False

            if self.persistent_data['matter_network_interface'] == 'Hotspot (recommended)':
                if self.DEBUG:
                    print("WARNING, settings persistent_data['matter_network_interface'] from Hotspot to None, since hotspot is disabled")
                self.persistent_data['matter_network_interface'] = None

        self.check_onboarding_state()

        #print("self.nmcli_installed: ", self.nmcli_installed)

        
        if self.use_hotspot and self.persistent_data['matter_network_interface'] == 'Hotspot (recommended)' and (self.nmcli_installed or self.hotspot_addon_installed):
            # Figure out the Hotspot addon's SSID and password
            self.load_hotspot_config()

            if self.hotspot_ssid != "" and self.hotspot_password != "":
                self.wifi_ssid = self.hotspot_ssid
                self.wifi_password = self.hotspot_password

        



        # Start the API handler. This will allow the user interface to connect
        try:
            if self.DEBUG:
                self.s_print("starting api handler")
            self.api_handler = MatterAPIHandler(self, verbose=True)
            if self.DEBUG:
                self.s_print("Adapter: API handler initiated")
        except Exception as e:
            if self.DEBUG:
                self.s_print("Error, failed to start API handler: " + str(e))


        # Create the thing
        """
        try:
            # Create the device object
            matter_device = MatterDevice(self)

            # Tell the controller about the new device that was created. This will add the new device to self.devices too
            self.handle_device_added(matter_device)

            if self.DEBUG:
                self.s_print("matter_device created")

            # You can set the device to connected or disconnected. If it's in disconnected state the thing will visually be a bit more transparent.
            self.devices['matter-thing'].connected = True
            self.devices['matter-thing'].connected_notify(True)

        except Exception as ex:
            self.s_print("Could not create internet_radio_device: " + str(ex))
        """


        # Make sure storage path exists
        if not os.path.isdir(self.data_dir_path):
            if self.DEBUG:
                self.s_print("creating matter_server storage path: " + str(self.data_dir_path))
            os.mkdir(self.data_dir_path)

        if not os.path.isdir(self.credentials_dir_path):
            if self.DEBUG:
                self.s_print("making certificates directory")
            os.system('mkdir -p ' + str(self.credentials_dir_path))
            self.download_certs()


        if not os.path.isdir(self.hasdata_dir_path):
            os.system('mkdir -p ' + str(self.hasdata_dir_path))

        # /data
        if not os.path.exists("/data"):
            if self.DEBUG:
                self.s_print("Warning, could not find /data, which the Matter-server will be looking for. Creating symlink to ~/.webthings/data/matter-adapter")
            #while self.running:
            #    time.sleep(1)
            os.system('sudo ln -s ' + str(self.data_dir_path) + ' /data')


        self.update_network_interfaces()

        # Wait for onboarding to complete
        while self.running and self.persistent_data['matter_network_interface'] == None:
            time.sleep(1)
            self.check_onboarding_state()

        if self.nmcli_installed:
            waiting_for_network_interface_counter = 0
            while self.running and self.matter_network_interface_found == False:
                waiting_for_network_interface_counter += 1
                while self.running and waiting_for_network_interface_counter < 5:
                    time.sleep(1)
                if waiting_for_network_interface_counter > 5:
                    waiting_for_network_interface_counter = 0
                self.update_network_interfaces()

        
        self.update_network_interfaces()
        

        

        if self.DEBUG:
            self.get_ips_interval = 120

        # Start clock thread
        if self.DEBUG:
            self.s_print("Init: starting the clock thread")
        try:
            self.ct = threading.Thread(target=self.clock)
            self.ct.daemon = True
            self.ct.start()
        except Exception as ex:
            if self.DEBUG:
                self.s_print("caught error starting the clock thread: " + str(ex))
        
        try:
            
            if self.DEBUG:
                self.s_print("init: creating start_servers thread")
            self.matter_servers_thread = threading.Thread(target=self.start_servers)
            self.matter_servers_thread.daemon = True
            self.matter_servers_thread.start()
        except Exception as ex:
            if self.DEBUG:
                self.s_print("caught error starting the matter servers thread: " + str(ex))


        # Init matter server
        #self.server = MatterServer(
        #    self.data_dir_path, DEFAULT_VENDOR_ID, DEFAULT_FABRIC_ID, int(self.port)
        #)

        #self.start_servers()

        pwd = run_command('pwd')
        if self.DEBUG:
            self.s_print("PWD after chdir: " + str(pwd))
            print("init done\n")

        #time.sleep(60)
        #self.ready = True

        #self.wifi_congestion_data = self.wifi_congestion_scan()






    def start_servers(self):
        if self.running:
            # Download the latest Matter certificates
            #self.download_certs()

            # ensure that the ip6table_filter kernel module is loaded
            run_command('sudo modprobe ip6table_filter')

            current_nmcli = str(run_command('nmcli | cat'))

            # TOOO: this overrides the Hotspot's internet blocking settings. The user should be informed of this (or it should not do it)
            os.system('sudo sysctl "net.ipv6.conf.all.disable_ipv6=0 net.ipv4.conf.all.forwarding=1 net.ipv6.conf.all.forwarding=1"')
            #os.system('sudo sysctl "net.ipv6.conf.all.accept_ra=2 net.ipv6.conf.all.accept_ra_rt_info_max_plen=64"')
            #if 'wlan0' in current_nmcli:
            #    os.system('sudo sysctl -w net.ipv6.conf.wlan0.accept_ra=2 net.ipv6.conf.wlan0.accept_ra_rt_info_max_plen=64')
            #if 'wlan1' in current_nmcli:
            #    os.system('sudo sysctl -w net.ipv6.conf.wlan1.accept_ra=2 net.ipv6.conf.wlan1.accept_ra_rt_info_max_plen=64')
            #if 'uap0' in current_nmcli:
            #    os.system('sudo sysctl -w net.ipv6.conf.uap0.accept_ra=2 net.ipv6.conf.uap0.accept_ra_rt_info_max_plen=64')
            if 'wpan0' in current_nmcli:
                os.system('sudo sysctl -w net.ipv6.conf.wpan0.accept_ra=2 net.ipv6.conf.wpan0.accept_ra_rt_info_max_plen=64')


            # If a radio is found, then it also starts OTBR
            if self.DEBUG:
                self.s_print("start_servers: calling find_thread_radio")
            self.find_thread_radio()

            # Start matter.server client
            if self.DEBUG:
                self.s_print("\nstart_servers: starting the otbr_loop thread")
            try:
                self.otbr_t = threading.Thread(target=self.otbr_loop)
                self.otbr_t.daemon = True
                self.otbr_t.start()
            except Exception as ex:
                if self.DEBUG:
                    self.s_print("caught error starting the OTBR loop thread: " + str(ex))
                    self.s_print(traceback.format_exc())

            time.sleep(5)

            if self.DEBUG:
                self.s_print("start_servers: is self.otbr_starting_timestamp None or a number?: ", self.otbr_starting_timestamp)


            # if it's starting, then wait until the thread network has fully started
            thread_wait_counter = 0
            #if self.otbr_starting_timestamp != None:
            if self.should_start_otbr or (isinstance(self.otbr_starting_timestamp,(int,float)) and self.otbr_starting_timestamp > time.time() - 9):
                if self.DEBUG:
                    print("start_servers: going to wait 2 minutes (at most) until Thread has started before starting Matter")

                while self.running and self.thread_running == False:
                    if self.DEBUG:
                        self.s_print(str(120 - thread_wait_counter) + ". start_servers: waiting for self.thread_running to be True.  len(self.otbr_stdout_messages): ", len(self.otbr_stdout_messages))

                    time.sleep(1)
                    thread_wait_counter += 1
                    self.s_print("thread_wait_counter: ", thread_wait_counter)
                    
                    if thread_wait_counter == 60:
                        if self.DEBUG:
                            self.s_print("Thread is heading for a timeout... " + str(120 - thread_wait_counter))

                    if thread_wait_counter > 120:
                        self.thread_error = 'Thread is having trouble starting. Try rebooting the controller.'
                        if self.DEBUG:
                            self.s_print("\nTIMEOUT ERROR: after about two minutes thread still hasn't started. Starting matter server anyway..")
                        self.should_start_matter = True
                        break
                    #if self.otbr_starting_timestamp == None:
                    #    if self.DEBUG:
                    #        self.s_print("\nOTBR ERROR: start_servers: while waiting for Thread to start the self.otbr_starting_timestamp became None again")
                    #    self.should_start_matter = True
                    #    break
                    if self.otbr_starting_timestamp != None and time.time() - self.otbr_starting_timestamp > 120:
                        if self.DEBUG:
                            self.s_print("\nTIMEOUT ERROR: after literally two minutes thread still hasn't started. Starting matter server anyway..")
                        self.should_start_matter = True
                        break

                # This could be set from the OTBR loop instead    
                #self.should_start_matter = True


            else:
                if self.DEBUG:
                    self.s_print("\nstart_servers: no thread? setting self.should_start_matter to true")
                       
                self.should_start_matter = True
            
            current_nmcli = str(run_command('nmcli | cat'))

            #if self.DEBUG:
            #    self.should_start_matter = False

            # TOOO: this overrides the Hotspot's internet blocking settings. The user should be informed of this (or it should not do it)
            os.system('sudo sysctl "net.ipv6.conf.all.disable_ipv6=0 net.ipv4.conf.all.forwarding=1 net.ipv6.conf.all.forwarding=1"')
            #os.system('sudo sysctl "net.ipv6.conf.all.accept_ra=2 net.ipv6.conf.all.accept_ra_rt_info_max_plen=64"')
            #if 'wlan0' in current_nmcli:
            #    os.system('sudo sysctl -w net.ipv6.conf.wlan0.accept_ra=2 net.ipv6.conf.wlan0.accept_ra_rt_info_max_plen=64')
            #if 'wlan1' in current_nmcli:
            #    os.system('sudo sysctl -w net.ipv6.conf.wlan1.accept_ra=2 net.ipv6.conf.wlan1.accept_ra_rt_info_max_plen=64')
            #if 'uap0' in current_nmcli:
            #    os.system('sudo sysctl -w net.ipv6.conf.uap0.accept_ra=2 net.ipv6.conf.uap0.accept_ra_rt_info_max_plen=64')
            if 'wpan0' in current_nmcli:
                os.system('sudo sysctl -w net.ipv6.conf.wpan0.accept_ra=2 net.ipv6.conf.wpan0.accept_ra_rt_info_max_plen=64')

            # Ensure there's a bridge
            #self.ensure_bridge()


            # Start matter.server client
            if self.DEBUG:
                self.s_print("\nstart_servers: starting the matter.server client thread")
            try:
                self.t = threading.Thread(target=self.client_thread)
                self.t.daemon = True
                self.t.start()
            except Exception as ex:
                if self.DEBUG:
                    self.s_print("Error starting the client thread: " + str(ex))
                    self.s_print(traceback.format_exc())


            if self.DEBUG:
                print("start_servers: self.should_start_matter should hopefully be true now: ", self.should_start_matter)
            while self.running:

                if self.should_start_matter:
                    if self.DEBUG:
                        self.s_print("start_servers: self.should_start_matter was True")
                    self.should_start_matter = False

                    # Start the Matter.server
                    if self.DEBUG:
                        self.s_print("\nstart_servers: calling start_matter_server")
                    self.start_matter_server()
                    if self.DEBUG:
                        self.s_print("start_servers: beyond start_matter_server")
                time.sleep(1)



        else:
            if self.DEBUG:
                self.s_print("start_servers: aborting, self.running is False")

        if self.DEBUG:
            self.s_print("start_servers: reached end of start_server, which will close this thread")



    def s_print(self, *a, **b):
        """Thread safe print function"""
        with self.s_print_lock:
            print(*a, **b)



    def add_from_config(self):
        """ This retrieves the addon settings from the controller """
        self.s_print("in add_from_config")
        try:
            database = Database(self.addon_id)
            if not database.open():
                self.s_print("Error. Could not open settings database")
                self.close_proxy()
                return

            config = database.load_config()
            database.close()

        except:
            self.s_print("Error. Failed to open settings database. Closing proxy.")
            self.close_proxy() # this will purposefully "crash" the addon. It will then we restarted in two seconds, in the hope that the database is no longer locked by then
            return

        try:
            if not config:
                self.s_print("Warning, no config.")
                return

            # Let's start by setting the user's preference about debugging, so we can use that preference to output extra debugging information
            if 'Debugging' in config:
                self.DEBUG = bool(config['Debugging'])

                #
                #
                self.DEVICE_DEBUG = False
                #
                #

                if self.DEBUG:
                    self.s_print("Debugging enabled")
                if self.DEVICE_DEBUG:
                    self.s_print("DEVICE Debugging enabled")


            if self.DEBUG:
                self.s_print("matter adapter config: ", str(config)) # Print the entire config data

            if "Days between updating certificates" in config:
                self.time_between_certificate_downloads = int(config["Days between updating certificates"]) * 86400

            if "Do not use Hotspot as WiFi network for devices" in config:
                self.use_hotspot = not bool(config["Do not use Hotspot as WiFi network for devices"])
                if self.DEBUG:
                    self.s_print("Use hotspot preference was in settings: " + str(self.use_hotspot))

            #if "Vendor ID" in config:
            #    if len(config["Vendor ID"]) > 2:
            #        self.persistent_data['vendor_id'] = str(config["Vendor ID"])
            #        if self.DEBUG:
            #            self.s_print("Vendor ID override was in settings: " + strself.persistent_data['vendor_id']))

            if "Region" in config:
                self.thread_region = str(config["Region"])
                if self.DEBUG:
                    self.s_print("Thread region was in settings: " + str(self.thread_region))
            
            if "Thread network name" in config:
                self.thread_network_name = str(config["Thread network name"])
                #self.thread_network_name = self.thread_network_name.replace(' ','')
                self.thread_network_name = re.sub(r'[^a-zA-Z0-9]', '', self.thread_network_name)
                if len(self.thread_network_name) < 2 or len(self.thread_network_name) > 20:
                    self.thread_network_name = 'CandleThread'
                if self.DEBUG:
                    self.s_print("Thread network name was in settings: " + str(self.thread_network_name))


            if "Help Thread devices to connect to the internet" in config:
                self.help_thread_devices_to_connect_to_the_internet = bool(config["Help Thread devices to connect to the internet"])
                if self.DEBUG:
                    self.s_print("Help Thread devices to connect to the internet preference was in settings: " + str(self.help_thread_devices_to_connect_to_the_internet))

            if 'Brightness transition duration' in config:
                self.brightness_transition_time = int(config["Brightness transition duration"])
                if self.DEBUG:
                    self.s_print("Brightness transition preference was in settings: " + str(self.brightness_transition_time))

            #if 'Thread dataset' in config:
            #    raw_dataset = str(config["Thread dataset"]).strip().rstrip()
            #    if len(raw_dataset) > 20:
            #        self.thread_dataset = raw_dataset
            #        self.persistent_data['thread_dataset'] = raw_dataset
            #        if self.DEBUG:
            #            self.s_print("Thread dataset preference was in settings, and long enough.  self.thread_dataset is now: " + str(self.thread_dataset))
            #    else:
            #        if self.DEBUG:
            #            self.s_print("Thread dataset preference was in settings, but not long enough: -->" + str(raw_dataset) + "<--")

            if 'Thread channel' in config:
                self.thread_channel = int(config["Thread channel"])
                if self.DEBUG:
                    self.s_print("Thread channel preference was in settings: " + str(self.thread_channel))

            if 'Enable Matter server dashboard' in config:
                self.disable_matter_dashboard = not bool(config["Enable Matter server dashboard"])
                if self.DEBUG:
                    self.s_print("Matter server dashboard preference was in settings. self.disable_matter_dashboard is now: " + str(self.disable_matter_dashboard))

            if 'Matter server type' in config:
                self.matter_server_type = str(config["Matter server type"])
                if self.DEBUG:
                    self.s_print("Matter server type preference was in settings: " + str(self.matter_server_type))
            
            if 'Default Matter fabric name' in config:
                new_default_matter_fabric_name = str(config["Default Matter fabric name"]).strip()
                if len(new_default_matter_fabric_name) > 1 and len(new_default_matter_fabric_name) < 30:
                    self.default_matter_fabric_name = new_default_matter_fabric_name
                if self.DEBUG:
                    self.s_print("Default Matter fabric name was in settings: " + str(self.default_matter_fabric_name))
        
            if 'Use Candle meshlocalprefix when creating a new Thread network' in config:
                self.use_candle_meshlocal_prefix = str(config["Use Candle meshlocalprefix when creating a new Thread network"])
                if self.DEBUG:
                    self.s_print("Candle meshlocalprefix preference was in settings: " + str(self.use_candle_meshlocal_prefix))
            

            


        except Exception as ex:
            self.s_print("caught error in add_from_config: " + str(ex))






    # If OTBR starts, then it (should) block this loop
    # TODO: it doesn't clock the loop
    def otbr_loop(self):

        while self.running:

            #if self.DEBUG:
            #    self.s_print("otbr_loop:")
            #    self.s_print("- self.otbr_started: ", self.otbr_started)
            #    self.s_print("- self.thread_radio_went_missing: ", self.thread_radio_went_missing)
            #    self.s_print("- self.found_thread_radio_again: ", self.found_thread_radio_again)
            #    self.s_print("- self.found_new_thread_radio: ", self.found_new_thread_radio)
            #    self.s_print("- self.thread_set_active: ", self.thread_set_active)
            #    self.s_print("- self.last_time_otbr_restarted: ", self.last_time_otbr_restarted)

            if self.should_start_otbr == True and self.otbr_started == False and self.otbr_starting_timestamp == None and self.last_time_otbr_restarted < int(time.time()) - 30 and (self.found_thread_radio_again or self.found_new_thread_radio) and self.thread_radio_went_missing == False:
                if self.DEBUG:
                    self.s_print("otbr_loop: conditions are perfect. calling start_otbr")
                self.last_time_otbr_restarted = int(time.time())
                self.start_otbr()
                if self.DEBUG:
                    print("BEYOND START_OTBR")

            time.sleep(5)

        if self.DEBUG:
            self.s_print("otbr_loop: beyond while loop. self.running should be false: ", self.running)






    def update_network_interfaces(self):
        if self.DEBUG:
            print("debug: in update_network_interfaces")
        actual_interfaces = ['uap0']
        available_interfaces = ['Hotspot (recommended)']
        found_it = False

        interfaces_check = run_command(r"nmcli | grep 'connected' | grep -v 'disconnected' | grep ': ' | grep -v 'p2p-dev-' | grep -v 'lo:' | grep -v 'wpan0:' | sed 's/\://' | awk '{print $1}'")
        if self.DEBUG:
            print("update_network_interfaces: interfaces_check: \n", interfaces_check, "\n")
        
        if isinstance(interfaces_check,str):
            
            for line in interfaces_check.splitlines():
                line = line.rstrip().strip()
                line = line.lower()
                
                if line == 'wpan0' or line == 'lo':
                    continue

                if line != 'uap0':
                    actual_interfaces.append(line)
                    
                if (line == 'uap0' or line == 'wlan1'):
                    pass
                elif (line == 'eth0' or line == 'wlan0'):
                    if 'Home network' not in available_interfaces:
                        available_interfaces.append('Home network')
                else:
                    if 'Advanced' not in available_interfaces:
                        available_interfaces.append('Advanced')

        else:
            if self.DEBUG:
                print("\nERROR: update_network_interfaces: interfaces_check output was not string")

        if self.DEBUG:
            print("\nupdate_network_interfaces: available_interfaces: \n", json.dumps(available_interfaces,indent=4), "\n");
            print("\nupdate_network_interfaces: actual_interfaces: \n", json.dumps(actual_interfaces,indent=4), "\n");
        self.actual_interfaces = actual_interfaces
        self.available_interfaces = available_interfaces

        actual_matter_network_interface = None
        if self.persistent_data['matter_network_interface'] == 'Hotspot (recommended)':
            if 'wlan1' in self.actual_interfaces:
                actual_matter_network_interface = 'wlan1'
                found_it = True
            elif 'uap0' in self.actual_interfaces:
                actual_matter_network_interface = 'uap0'
                found_it = True
            #else:
            #    actual_matter_network_interface = 'uap0'

        elif self.persistent_data['matter_network_interface'] == 'Home network':
            if 'eth1' in self.actual_interfaces:
                actual_matter_network_interface = 'eth1'
                found_it = True
            elif 'eth0' in self.actual_interfaces:
                actual_matter_network_interface = 'eth0'
                found_it = True
            elif 'wlan0' in self.actual_interfaces:
                actual_matter_network_interface = 'wlan0'
                found_it = True
            elif 'mlan0' in self.actual_interfaces:
                actual_matter_network_interface = 'mlan0'
                found_it = True
            else:
                if self.DEBUG:
                    print("\nWARNNG: update_network_interfaces: no connected home interface found!\n")

        elif self.persistent_data['matter_network_interface'] == 'All networks':
            actual_matter_network_interface = 'all'
            found_it = True

        elif self.persistent_data['matter_network_interface'] == 'Advanced':
            if self.DEBUG:
                print("update_network_interfaces:matter_network_interface is set to advanced")

            if isinstance(self.persistent_data['actual_matter_network_interface'],str) and len(self.persistent_data['actual_matter_network_interface']) > 1:
                if self.persistent_data['actual_matter_network_interface'] in actual_interfaces:
                    actual_matter_network_interface = self.persistent_data['actual_matter_network_interface']
                    found_it = True
                    if self.DEBUG:
                        print("update_network_interfaces: OK, advanced interface selection is in actual connected interfaces: ", self.persistent_data['actual_matter_network_interface'], actual_interfaces)
                else:
                    if self.DEBUG:
                        print("\nWARNNG: update_network_interfaces: no advanced network interface was not found in actual connected interfaces!: ", self.persistent_data['actual_matter_network_interface'], actual_interfaces)
            else:
                if self.DEBUG:
                    print("\nERROR: update_network_interfaces: should use advanced interface selection, but self.persistent_data['actual_matter_network_interface'] is somehow not a valid string: ", self.persistent_data['actual_matter_network_interface'])
        
        if found_it and isinstance(actual_matter_network_interface,str):
            if actual_matter_network_interface != self.persistent_data['actual_matter_network_interface']:
                self.persistent_data['actual_matter_network_interface'] = actual_matter_network_interface
                if self.DEBUG:
                    print("update_network_interfaces: self.persistent_data['actual_matter_network_interface'] changed to: ", self.actual_matter_network_interface)
        
        self.matter_network_interface_found = found_it
        if self.DEBUG:
            print("update_network_interfaces: was a valid network interface found?: ", found_it)

        return available_interfaces



    # Get real tty port from:
    # ls -la /dev/serial/by-id/usb-*

    def find_thread_radio(self):
        if self.DEBUG:
            print("debug: in find_thread_radio")
        found_thread_radio_again = False
        found_new_thread_radio = False
        if os.path.isdir('/dev/serial/by-id'):
            serial_by_id_output = run_command('ls /dev/serial/by-id')
            if self.DEBUG:
                print("debug: find_thread_radio:  serial_by_id_output: ", serial_by_id_output)
            if isinstance(serial_by_id_output,str) and len(str(serial_by_id_output)) > 5:

                if 'No such file or directory' in str(serial_by_id_output):
                    if self.DEBUG:
                        print("ERROR, find_thread_radio: no /dev/serial/by-id!")
                    self.found_new_thread_radio = False
                    self.found_thread_radio_again = False
                    return False
            
                if isinstance(self.serial_before,str):
                    if self.DEBUG:
                        self.s_print("find_thread_radio:  self.serial_before is a string: \n\n" + str(self.serial_before) + "\n\n")
                    for line in str(serial_by_id_output).splitlines():
                        line = str(line).strip().rstrip()
                        if not line in self.serial_before:
                            self.persistent_data['thread_radio_serial_port'] = line
                            if self.DEBUG:
                                self.s_print("find_thread_radio: found a new thread radio line: " + str(line))
                            found_new_thread_radio = True
                            self.found_new_thread_radio = True
                            self.serial_before = None
                            self.should_save = True
                            break

                if found_new_thread_radio == False:
                    if 'thread_radio_serial_port' in self.persistent_data and isinstance(self.persistent_data['thread_radio_serial_port'],str) and len(str(self.persistent_data['thread_radio_serial_port'])) > 3:
                        for line in serial_by_id_output.splitlines():
                            if str(self.persistent_data['thread_radio_serial_port']) == str(line).strip().rstrip():
                                if self.found_thread_radio_again == False and self.otbr_started == False:
                                    if self.DEBUG:
                                        self.s_print("Found the thread radio again")
                                found_thread_radio_again = True
                                self.found_thread_radio_again = True
                                break

                    # TODO: this should be removed, since the SkyConnect could also have zigbee firmware. Maybe leave it, but only run it if there is no zigbee2mqtt addon installed
                    """
                    if found_thread_radio_again == False:
                        for line in serial_by_id_output.splitlines():
                            line = str(line).strip().rstrip()
                            if 'SkyConnect' in line or 'Nabu_Casa' in line:
                                self.persistent_data['thread_radio_serial_port'] = line
                                if self.otbr_started == False:
                                    if self.DEBUG:
                                        self.s_print("Found a new thread radio: ", line)
                                    self.should_save = True
                                found_new_thread_radio = True
                                break
                    """
        else:
            if self.DEBUG:
                self.s_print("find_thread_radio:  /dev/serial/by-id is not a directory - no serial devices")

        self.found_thread_radio_again = found_thread_radio_again
        self.found_new_thread_radio = found_new_thread_radio

        if self.found_new_thread_radio:
            self.check_onboarding_state()
            
        if self.found_thread_radio_again or self.found_new_thread_radio:
            if self.DEBUG:
                print("find_thread_radio: OK, a radio has been found.  self.found_new_thread_radio,self.found_thread_radio_again: ", self.found_new_thread_radio, self.found_thread_radio_again)
            self.found_a_thread_radio_once = True
            self.thread_radio_went_missing = False
            if self.otbr_started == False: # and self.otbr_starting_timestamp == None:
                if self.DEBUG:
                    print("find_thread_radio: SUCCESS, setting should_start_otbr to True")
                self.should_start_otbr = True

        else:
            #if self.DEBUG:
            #    self.s_print("\nNO THREAD RADIO FOUND\n")
            if self.found_a_thread_radio_once:
                if self.DEBUG:
                    if self.thread_radio_went_missing == False:
                        print("find_thread_radio: setting self.thread_radio_went_missing to True")
                self.thread_radio_went_missing = True
                self.thread_radio_is_alive_count = 0
                
                    

        return (self.found_thread_radio_again or self.found_new_thread_radio)




    def add_otbr_iptables(self):

        current_nmcli = str(run_command('nmcli | cat'))
        current_iptables = run_command('sudo iptables -S')
        if isinstance(current_iptables,str):
            #if 'wpan0' in current_nmcli:
            if not 'wpan0' in current_iptables:
                if self.DEBUG:
                    self.s_print("add_otbr_iptables: adding wpan0 masquerade iptables")

                # OpenThread NAT64
                os.system('sudo iptables -t mangle -A PREROUTING -i wpan0 -j MARK --set-mark 0x1001')
                os.system('sudo iptables -t nat -A POSTROUTING -m mark --mark 0x1001 -j MASQUERADE')
                os.system('sudo iptables -t filter -A FORWARD -o uap0 -j ACCEPT')
                os.system('sudo iptables -t filter -A FORWARD -i uap0 -j ACCEPT')

            # If the user has plugged in a wifi dongle
            if 'wlan1' in current_nmcli and 'wlan1' not in current_iptables:
                os.system('sudo iptables -t filter -A FORWARD -o wlan1 -j ACCEPT')
                os.system('sudo iptables -t filter -A FORWARD -i wlan1 -j ACCEPT')
                






    def import_thread_dataset(self,new_dataset):
        if self.DEBUG:
            print("in import_thread_dataset.  new_dataset: ", new_dataset)
        if isinstance(new_dataset,str) and len(new_dataset) > 40:
            
            print(str(self.run_ot_ctl_command('factoryreset')))

            # This is probably a bad idea
            #if os.path.isdir(self.data_thread_dir_path):
            #    os.system('rm ' + str(self.data_thread_dir_path) + '/*')

            load_dataset_check = str(self.run_ot_ctl_command('dataset init tlvs ' + str(new_dataset), 60)).rstrip()

            #print(str(self.run_ot_ctl_command('dataset set active ' + str(new_dataset))))
            if load_dataset_check == 'Done':
                self.thread_dataset = new_dataset
                if self.persistent_data['thread_dataset'] == '' or self.persistent_data['vendor_id'] == '':
                    if self.DEBUG:
                        print("import_thread_dataset:  lowering leaderweight to 60")
                    self.persistent_data['leaderweight'] = 254 # Lower than the 'main' controller

                self.persistent_data['thread_dataset'] = new_dataset
                
                self.save_persistent_data()
                
                #self.find_thread_radio()
                if self.persistent_data['vendor_id'] != '' and self.found_thread_radio_again or self.found_new_thread_radio:
                    if str(self.run_ot_ctl_command('ifconfig up')).rstrip() == 'Done':
                        if str(self.run_ot_ctl_command('thread start')).rstrip() == 'Done':
                            if self.DEBUG:
                                print("Imported dataset and re-enabled thread")
            else:
                if self.DEBUG:
                    print("ERROR importing dataset with 'dataset init tlvs' command: ", load_dataset_check)
            





    #
    #  START OTBR
    #



    def start_otbr(self):
        if self.DEBUG:
            self.s_print("in start_otbr. Initial self.otbr_starting_timestamp should be none: ", self.otbr_starting_timestamp)
        self.otbr_starting_timestamp = time.time()
#       #self.otbr_thread = threading.Thread(target=self.really_start_otbr)
#       #self.otbr_thread.daemon = True
#       #self.otbr_thread.start()
#       self.really_start_otbr()
#
#   def really_start_otbr(self):
#        if self.DEBUG:
#            self.s_print("in really_start_otbr")
        try:
            #if self.shell == None:
            #    self.shell = subprocess.Popen(['/bin/bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

            if self.otbr_agent_process == None:
                #thread_radio_url = "spinel+hdlc+uart:///dev/ttyUSB0?uart-baudrate=460800"

                thread_radio_url = "spinel+hdlc+uart:///dev/ttyUSB0?uart-baudrate=460800"
                if 'thread_radio_serial_port' in self.persistent_data and isinstance(self.persistent_data['thread_radio_serial_port'],str) and len(str(self.persistent_data['thread_radio_serial_port'])) > 3:
                    thread_radio_url = "spinel+hdlc+uart:///dev/serial/by-id/" + str(self.persistent_data['thread_radio_serial_port']) + "?uart-baudrate=460800"

                    real_tty_path = str(run_command('ls -la /dev/serial/by-id/' + str(self.persistent_data['thread_radio_serial_port']))).strip().rstrip()
                    if ' -> ../../' in real_tty_path:
                        real_tty_path = real_tty_path.split(' -> ../../')[1]
                        if real_tty_path and str(real_tty_path).startswith('tty') and len(str(real_tty_path)) < 10:
                            thread_radio_url = "spinel+hdlc+uart:///dev/" + str(real_tty_path) + "?uart-baudrate=460800"


                    # &uart-init-deassert

                current_nmcli = str(run_command('nmcli | cat'))


                self.thread_radio_url = thread_radio_url

                self.thread_backbone_interface = 'wlan0'
                if os.path.isfile('/boot/firmware/candle_hotspot.txt'):
                    self.thread_backbone_interface = 'uap0'
                    if 'wlan1:' in current_nmcli:
                        self.thread_backbone_interface = 'wlan1'


                #
                # OTBR webserver settings are present at:
                #
                # cat /etc/default/otbr-web
                # OTBR_WEB_OPTS="-p 8084 -a 0.0.0.0"
                #

                if self.DEBUG:
                    self.s_print("\n. . . . __start_otbr__ . . . . ")
                    self.s_print("self.otbr_agent_path: ", self.otbr_agent_path)
                    self.s_print("_start_otbr:  thread_radio_url: ", thread_radio_url)
                    self.s_print("self.thread_backbone_interface: ", self.thread_backbone_interface)
                    self.s_print("self.data_thread_dir_path: ", self.data_thread_dir_path)

                if not os.path.isfile(str(self.otbr_agent_path)):
                    if self.DEBUG:
                        self.s_print("\nERORR, self.otbr_agent_path file did not exist: ", self.otbr_agent_path)
                    return
                if not os.path.isdir(str(self.data_thread_dir_path)):
                    if self.DEBUG:
                        self.s_print("\nERORR, self.data_thread_dir_path dir did not exist: ", self.data_thread_dir_path)
                    return

                #os.system('sudo sysctl "net.ipv6.conf.all.disable_ipv6=0 net.ipv4.conf.all.forwarding=1 net.ipv6.conf.all.forwarding=1"')

                """
                net.ipv6.conf.all.disable_ipv6=0
                net.ipv4.conf.all.forwarding=1
                net.ipv6.conf.all.forwarding=1
                net.ipv6.conf.all.accept_ra=2
                net.ipv6.conf.all.accept_ra_rt_info_max_plen=64
                net.ipv6.conf.eno1.accept_ra=2
                net.ipv6.conf.wpan0.accept_ra=2
                """

                self.hotspot_ip6_blocked = False
                # TODO: this clashes with the 'block ip6 internet' option for the hotspot..
                if os.path.isfile(self.candle_hotspot_block_ip6_internet_path):
                    self.hotspot_ip6_blocked = True
                #else:
                #    os.system('sudo sysctl "net.ipv6.conf.all.disable_ipv6=0 net.ipv4.conf.all.forwarding=1 net.ipv6.conf.all.forwarding=1"')
                

                
                # net.ipv6.conf.uap0.accept_ra=2 net.ipv6.conf.wpan0.accept_ra=2 net.ipv6.conf.wlan1.accept_ra=2

                os.system('sudo sysctl -w net.ipv6.conf.wpan0.accept_ra=2 net.ipv6.conf.wpan0.accept_ra_rt_info_max_plen=64')
                #os.system('sudo sysctl -w net.ipv6.conf.eth0.accept_ra=2')

                openthread_conf_path = os.path.join(self.other_dir_path, str(self.thread_region).lower() + '_openthread.conf')

                """
                # TODO

                should these environment variables be set?
                OPENTHREAD_CONFIG_BORDER_ROUTING_MULTI_AIL_DETECTION_AUTO_ENABLE_MODE 0
                https://openthread.google.cn/reference/config/group/config-border-routing

                # OPENTHREAD_CONFIG_IP6_SLAAC_ENABLE

                # https://github.com/orgs/openthread/discussions/11219

                

                """

                # ,"--vendor-name","CandleSmartHome","--model-name","CandleController", # unrecognized option '--vendor-name'
                agent_command_array = ["sudo",str(self.otbr_agent_path),"--data-path",str(self.data_thread_dir_path),"--syslog-disable","--debug-level","7","--thread-ifname","wpan0","-B", str(self.thread_backbone_interface)]
                if self.thread_add_factory_config_file == True:
                    agent_command_array.extend(["factory-config-file",str(openthread_conf_path)])
                    
                agent_command_array.extend([str(self.thread_radio_url)])

                #
                # trel://wlan0
                # enables router-to-router communication over the IP backbone
                #

                self.otbr_stdout_messages = []

                if self.DEBUG:
                    self.s_print("\n\nOTBR agent_command_array: ", str(agent_command_array), "\n\n")
                    self.s_print("\n\nTHREAD AGENT COMMAND:\n\n" + str( " ".join(agent_command_array) ) + "\n\n")

                self.otbr_agent_process = subprocess.Popen(agent_command_array, stderr=subprocess.DEVNULL, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                #os.set_blocking(self.otbr_agent_process.stdout.fileno(), False)
                #os.set_blocking(self.otbr_agent_process.stderr.fileno(), False)
                #self.tcpdump = subprocess.Popen(["sudo","tcpdump","-i","any","'udp port 5353 and (host 224.0.0.251 or host ff02::fb)'","-n"], stderr=subprocess.DEVNULL, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                time.sleep(.1)
                try:
                    if self.otbr_agent_process and self.otbr_agent_process.poll() == None:
                        self.last_time_otbr_started = time.time()
                        self.should_start_otbr = False
                        time.sleep(2)
                        os.system('sudo sysctl -w net.ipv6.conf.wpan0.accept_ra=2 net.ipv6.conf.wpan0.accept_ra_rt_info_max_plen=64')
                except Exception as ex:
                    if self.DEBUG:
                        self.s_print("caught error checking if otbr process is running: ", ex)


                # sudo tcpdump -i any 'udp port 5353 and (host 224.0.0.251 or host ff02::fb)'

                # avahi-browse -r -t _meshcop._udp

                # shows IP multicast information:
                # ipmaddr


                if self.otbr_agent_process:
                    if self.DEBUG:
                        self.s_print("self.otbr_agent_process has been created")

                    if self.otbr_agent_process.poll() == None:
                        if self.DEBUG:
                            print("otbr_agent_process is running OK")


                        while self.otbr_agent_process != None and self.otbr_agent_process.poll() == None:
                            time.sleep(1)
                            try:
                                # Each loop parse at most 1000 OTBR stdout messages
                                if self.otbr_agent_process:
                                    for i in range(1000):
                                        msg = self.otbr_agent_process.stdout.readline()
                                        decoded_message = str(msg.decode()).strip().rstrip()
                                        # note to self: do not put a print statement here
                                        if len(decoded_message) > 1:
                                            self.otbr_stdout_messages.append(decoded_message)
                                        elif decoded_message == '':
                                            print("number of lines read from otbr_agent_process stdout: ", i)
                                            break

                                if len(self.otbr_stdout_messages):
                                    self.parse_otbr_messages()

                            except Exception as ex:
                                print("caught error trying to read messages from self.otbr_agent_process: ", ex)




                        #    self.s_print("starting thread to read from OTBR stdout")
                        #self.stdout_thread = threading.Thread(target=read_otbr_stdout)
                        #self.stdout_thread.daemon = True
                        #self.stdout_thread.start()
                else:
                    self.s_print("error, self.otbr_agent_process subprocess was not created? ", self.otbr_agent_process)


            else:
                if self.DEBUG:
                    self.s_print("_start_otbr: self.self.otbr_agent_process was not None?")
                if self.last_thread_radio_is_alive_timestamp < time.time() - 120:
                    if self.DEBUG:
                        self.s_print("is has been over two minutes since the thread radio last responded")
                        self.s_print("- self.otbr_started: ", self.otbr_started)
                        self.s_print("- self.thread_radio_went_missing: ", self.thread_radio_went_missing)
                        self.s_print("- self.found_thread_radio_again: ", self.found_thread_radio_again)
                        self.s_print("- self.found_new_thread_radio: ", self.found_new_thread_radio)
                        self.s_print("- self.thread_set_active: ", self.thread_set_active)
                        self.s_print("- self.last_time_otbr_restarted: ", self.last_time_otbr_restarted)


                    self.thread_error = 'The Thread radio is not responding'

                    if self.last_time_otbr_started < time.time() - 120:
                        self.last_time_otbr_started = time.time() - 60
                        if self.DEBUG:
                            self.s_print("Radio is not responsing? calling really_stop_otbr to try again")
                        self.really_stop_otbr()

                    #if self.thread_set_active == False:
                    #    if self.DEBUG:
                    #        self.s_print("calling really_stop_otbr to try again")




            #self.shell.stdin.write((str(command) + '\n').encode())
            #self.shell.stdin.flush()
        except Exception as ex:
            if self.DEBUG:
                self.s_print("caught error in really_start_otbr: " + str(ex))


    def parse_otbr_messages(self):
        if self.DEBUG:
            print("\n", self.thread_radio_is_alive_count, "\n <-thread_radio_is_alive_count")
            print("in parse_otbr_messages.  len(self.otbr_stdout_messages): ", len(self.otbr_stdout_messages))
            
        if self.DEBUG and self.thread_radio_is_alive_count < 100:
            self.s_print("\nclock: total otbr_stdout_messages length: ", len(self.otbr_stdout_messages))

        wpan_check = str(run_command('ip link show | grep wpan0'))
        if 'state' in wpan_check:
            if self.otbr_started == False:
                if self.DEBUG:
                    print("wpan0 state - OTBR has started succesfully")

                # sysctl net.ipv6.conf.all.disable_ipv6 = 0 net.ipv4.conf.all.forwarding = 1 net.ipv6.conf.all.forwarding = 1 net.ipv6.conf.all.accept_ra_rt_info_max_plen = 64 net.ipv6.conf.all.accept_ra = 2
                os.system('sudo sysctl -w net.ipv6.conf.wpan0.accept_ra=2 net.ipv6.conf.wpan0.accept_ra_rt_info_max_plen=64')
            self.otbr_started = True

        if 'state DOWN' in wpan_check:
            bring_up_wpan0_output = str(run_command('sudo ip link set wpan0 up'))
            if self.DEBUG:
                self.s_print("bring_up_wpan0_output: ", bring_up_wpan0_output)


        while len(self.otbr_stdout_messages):
            otbr_message = self.otbr_stdout_messages.pop(0)
            if self.DEBUG and self.thread_radio_is_alive_count < 100:
                self.s_print("parse_otbr_messages: otbr_message: ", otbr_message)

            if 'Received spinel frame' in otbr_message:
                self.thread_radio_is_alive_count += 1
                self.last_thread_radio_is_alive_timestamp = int(time.time())
                if self.DEBUG and self.thread_radio_is_alive_count < 100:
                    self.s_print("parse_otbr_messages: self.thread_radio_is_alive_count is now: ", self.thread_radio_is_alive_count)

            if 'failed set request 0x12 status: -110' in otbr_message:
                if self.DEBUG:
                    self.s_print("parse_otbr_messages: the Thread radio may need to use an extension cord")
                self.thread_error = 'You may need to use a USB extension cable for your Thread dongle'
                self.extension_cable_recommended = True

            elif 'Failed to communicate with RCP' in otbr_message:
                if self.DEBUG:
                    self.s_print("\nERROR, spotted message indicating the thread radio isn't responding")
                self.thread_error = 'The Thread radio is not responding'

            elif ('SrpAdvProxy---: Started' in otbr_message or 'Evaluating routing policy' in otbr_message or self.thread_radio_is_alive_count > 20) and self.thread_set_active == False:
                if self.DEBUG:
                    self.s_print("parse_otbr_messages: calling start_thread_mesh")
                self.thread_set_active = True
                self.thread_radio_went_missing = False
                self.should_start_thread_mesh = True
                

            elif '... noise:-128' in otbr_message:
                #if self.DEBUG:
                #    self.s_print("Thread radio is receiving a lot of noise?")
                self.noise_counter += 1
                #self.thread_error = 'The thread radio is receiving a lot of noise. You may need to use a USB extension cable for your Thread dongle'
                #self.extension_cable_recommended = True

            elif 'Wait for response timeout' in otbr_message:
                self.timeout_counter += 1
                self.all_timeout_counter += 1
                if self.DEBUG:
                    self.s_print("\nWARNING, otbr got timeout - usb stick or device not responding?  self.all_timeout_counter: ", self.all_timeout_counter)



    #
    #  START MATTER.SERVER
    #


    def start_matter_server(self):
        if self.DEBUG:
            self.s_print("in start_matter_server.  self.matter_server_type: ", self.matter_server_type)

        if not os.path.exists(self.hasdata_dir_path):
            self.s_print("\nERROR, start_matter_server: hasdata_dir_path did not exist yet. Creating it now.")
            os.system('mkdir -p ' + str(self.hasdata_dir_path))

        if not os.path.exists(self.matter_serverjs_start_path):
            if self.DEBUG:
                self.s_print("\nERROR, falling back to Python because matter_serverjs_start_path could not be found: ", self.matter_serverjs_start_path)
            self.matter_server_type = 'Python'

        #
        #  PYTHON VERSION
        #
        # This is the 'old' version, which will NOT get updates. 
        # It uses less memory and disk space than the new Node JS version (below)

        if self.matter_server_type == 'Python':
            if self.DEBUG:
                self.s_print("\n\n Starting PYTHON version of Matter.server\n\n")
            python3_path = str(run_command('readlink $(which python3)'))
            python3_path = "/usr/bin/" + str(python3_path).rstrip()

            if self.DEBUG:
                self.s_print("start_matter_server:  python3_path: ", python3_path)

            if not os.path.exists(python3_path):
                if self.DEBUG:
                    self.s_print("start_matter_server: error, could not find python binary at path: ", python3_path)
                python3_path = 'python3'
            # /home/pi/.webthings/addons/matter-adapter/lib/
            #matter_server_command = str(python3_path) + ' -m matter_server.server --storage-path ' + str(self.data_dir_path)
            matter_server_command = str(python3_path) + ' -m matter_server.server --storage-path ' + str(self.hasdata_dir_path)

            if self.persistent_data['vendor_id'] != "":
                decimal_vendor_id = int(self.persistent_data['vendor_id'], 16)
                #matter_server_command = matter_server_command + " --vendorid " + str(self.persistent_data['vendor_id'])
                matter_server_command = matter_server_command + " --vendorid " + str(decimal_vendor_id)

            if self.nmcli_installed == True:
                if isinstance(self.persistent_data['matter_network_interface'],str) and self.persistent_data['matter_network_interface'] == 'all':
                    if self.DEBUG:
                        self.s_print("start_matter_server: WARNING, allowing Matter on all network interfaces!")
                elif isinstance(self.persistent_data['actual_matter_network_interface'],str) and len(self.persistent_data['actual_matter_network_interface']) > 1:
                    if self.persistent_data['actual_matter_network_interface'] != 'all':
                        matter_server_command = matter_server_command + " --primary-interface " + str(self.persistent_data['actual_matter_network_interface'])
                else:
                    print("\nERROR\nERROR: actual_matter_network_interface was not a string! Starting matter server anyway, but without setting --primary-interface")

            #if not os.path.isdir('/data/credentials'):
            #    os.system('mkdir -p /data/credentials')
            #matter_server_command = matter_server_command + " --paa-root-cert-dir /data/credentials"

            #bluetooth_check = str(run_command('hcitool dev'))
            bluetooth_check = str(run_command('hciconfig -a'))

            if 'hci0' in bluetooth_check:
                matter_server_command = matter_server_command + " --bluetooth-adapter 0"
            elif 'hci1' in bluetooth_check:
                matter_server_command = matter_server_command + " --bluetooth-adapter 1"

            #matter_server_command = matter_server_command + " --bypass-attestation-verifier true"


            if not os.path.exists(self.data_dir_path):
                self.s_print("ERROR DATA PATH DOES NOT EXIST")

            if not os.path.exists(self.lib_path):
                self.s_print("ERROR LIB PATH DOES NOT EXIST")

            #matter_server_command = "PYTHONPATH=" + str(self.lib_path) + " " +  str(matter_server_command)

            if self.DEBUG:
                self.s_print("")
                self.s_print("full matter server start command: " + str(matter_server_command))
                self.s_print("")

            matter_server_command_array = matter_server_command.split()

            if self.DEBUG:
                self.s_print("full matter server start command array: " + str(matter_server_command_array))
            #self.run_process(matter_server_command)


            my_env = os.environ.copy()
            my_env["PYTHONPATH"] = str(self.lib_path) + ":" # + my_env["PYTHONPATH"]
            if self.DEBUG:
                self.s_print("my_env[PYTHONPATH]: " + str(my_env["PYTHONPATH"]))

            #'PYTHONPATH=/home/pi/.webthings/addons/matter-adapter/lib /usr/bin/python3.9 -m matter_server.server --storage-path /home/pi/.webthings/data/matter-adapter'

            #self.server_process = subprocess.Popen("/usr/bin/python3.9 bla.py", stdout=subprocess.PIPE, env=my_env, shell=True)
            #self.server_process = subprocess.Popen(matter_server_command_shell, stdout=subprocess.PIPE, env=my_env, shell=True)
            self.server_process = subprocess.Popen(matter_server_command_array, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=my_env)
            os.set_blocking(self.server_process.stdout.fileno(), False)
            os.set_blocking(self.server_process.stderr.fileno(), False)
            
            
        #
        #  NODE JS VERSION
        #
        # This is the 'new' version, which will get updates. 
        # But it's currently (early 2026) in an alpha state. And it uses more memory and disk space.
        
        else:
            if self.DEBUG:
                self.s_print("\n\n Starting NodeJS version of Matter.server\n\n")
            
            # ALL AVAILABLE FLAGS ARE DOCUMENTED HERE: https://github.com/matter-js/matterjs-server/blob/main/docs/cli.md
            #matter_server_command = 'npm run server --

            # node --enable-source-maps packages/matter-server/dist/esm/MatterServer.js
            
            # npm run server -- --production-mode

            # npm run server -- 

            # self.matter_server_start_path = os.path.join(self.matter_server_base_path,'packages','matter-server','dist','esm','MatterServer.js')

            #matter_server_command = '/home/pi/node24 ' + self.matter_serverjs_start_path + ' --enable-source-maps --disable-dashboard '
            matter_server_command = 'exec node --enable-source-maps ' + self.matter_serverjs_start_path  #+ ' --disable-dashboard '
            if self.disable_matter_dashboard:
                matter_server_command += ' --disable-dashboard'
            #node --enable-source-maps packages/matter-server/dist/esm/MatterServer.js
            matter_server_command = matter_server_command + ' --storage-path ' + str(self.hasdata_dir_path)



            if self.DEBUG:
                matter_server_command += ' --log-level debug'
            else:
                matter_server_command += ' --log-level critical'

            if self.nmcli_installed == True:
                if isinstance(self.persistent_data['matter_network_interface'],str) and self.persistent_data['matter_network_interface'] == 'all':
                    if self.DEBUG:
                        self.s_print("start_matter_server: WARNING, allowing Matter on all network interfaces!")
                elif isinstance(self.persistent_data['actual_matter_network_interface'],str) and len(self.persistent_data['actual_matter_network_interface']) > 1:
                    if self.persistent_data['actual_matter_network_interface'] != 'all':
                        matter_server_command = matter_server_command + " --primary-interface " + str(self.persistent_data['actual_matter_network_interface'])
                else:
                    print("\nERROR\nERROR: actual_matter_network_interface was not a string! Starting matter server anyway, but without setting --primary-interface")

            # --listen-address 192.168.12.1  # REPEATABLE, so should then also bind to wpan0 if that has an IP address


            #matter_server_command = matter_server_command + " --ble"

            if self.persistent_data['vendor_id'] != "":
                decimal_vendor_id = int(self.persistent_data['vendor_id'], 16)
                #matter_server_command = matter_server_command + " --vendorid " + str(self.persistent_data['vendor_id'])
                matter_server_command = matter_server_command + " --vendorid " + str(decimal_vendor_id)



            #if not os.path.isdir('/data/credentials'):
            #    os.system('mkdir -p /data/credentials')
            #matter_server_command = matter_server_command + " --paa-root-cert-dir /data/credentials"

            #bluetooth_check = str(run_command('hcitool dev'))
            bluetooth_check = str(run_command('hciconfig -a'))
            if 'hci0' in bluetooth_check:
                matter_server_command = matter_server_command + " --bluetooth-adapter 0"
            elif 'hci1' in bluetooth_check:
                matter_server_command = matter_server_command + " --bluetooth-adapter 1"

            matter_server_command = matter_server_command + " --production-mode"

            #matter_server_command = matter_server_command + " --bypass-attestation-verifier true"

            if not os.path.exists(self.lib_path):
                self.s_print("ERROR LIB PATH DOES NOT EXIST")

            if self.DEBUG:
                self.s_print("")
                self.s_print("full matter server start command: " + str(matter_server_command))
                self.s_print("")

            matter_server_command_array = matter_server_command.split()

            if self.DEBUG:
                self.s_print("full matter server start command array: " + str(matter_server_command_array))
            #self.run_process(matter_server_command)


            my_env = os.environ.copy()
            #my_env["PYTHONPATH"] = str(self.lib_path) + ":" # + my_env["PYTHONPATH"]
            #if self.DEBUG:
            #    self.s_print("my_env[PYTHONPATH]: " + str(my_env["PYTHONPATH"]))

            #'PYTHONPATH=/home/pi/.webthings/addons/matter-adapter/lib /usr/bin/python3.9 -m matter_server.server --storage-path /home/pi/.webthings/data/matter-adapter'

            #self.server_process = subprocess.Popen("/usr/bin/python3.9 bla.py", stdout=subprocess.PIPE, env=my_env, shell=True)
            #self.server_process = subprocess.Popen(matter_server_command_shell, stdout=subprocess.PIPE, env=my_env, shell=True)
            #self.server_process = subprocess.Popen(matter_server_command_array, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=my_env, cwd=self.matter_server_base_path)
            self.server_process = subprocess.Popen(matter_server_command_array, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=my_env, cwd=self.addon_path)
            os.set_blocking(self.server_process.stdout.fileno(), False)
            os.set_blocking(self.server_process.stderr.fileno(), False)


        time.sleep(1)
        if self.server_process != None and self.server_process.poll() == None:
            if self.DEBUG:
                self.s_print("self.server_process is OK. Succesfully Started Matter.server")
            self.matter_server_running = True
            self.should_start_matter_time = 0
        else:
            if self.DEBUG:
                print("ERROR, matter.server self.server_process exited immediately after its creation!")
            try:
                if self.server_process != None:
                    self.server_process.terminate()
                    time.sleep(1)
            except exception as ex:
                print("\ncaught ERROR calling server_process.terminate after it immediately crashed: ", ex)
            self.server_process = None
            self.matter_server_running = False
            self.should_start_matter_time = int(time.time()) + 20




    # Currently unused, but could optimize which Thread channel to select. Apple always chooses 26 though, so that might not be a bad choice either.
    def wifi_congestion_scan(self):
        if self.DEBUG:
            self.s_print("in wifi_congestion_scan (BLOCKED)")

        return
        channel_data = {}
        channels_output = str(run_command("sudo iwlist wlan0  channel | grep -v 'available frequencies' | grep -v 'Current Frequency'"))
        if 'Channel ' in channels_output:
            for channel_line in channels_output.splitlines():
                if 'Channel ' in channel_line and ' GHz' in channel_line:
                    channel_number = channel_line.split(' : ',1)[0].strip().rstrip()
                    #channel_number = channel_number.replace('Channel ','').strip().rstrip()
                    frequency = channel_line.split(' : ',1)[1]
                    frequency = frequency.replace(' GHz','').strip().rstrip()


                    if frequency.isdigit():
                        channel_data[channel_number] = {'nr':channel_number.replace('Channel ','').strip().rstrip(), 'frequency':frequency}

                        # sudo iw dev wlan0 scan freq 2412
                        #frequency_data = run_command('sudo iw dev wlan0 scan freq ' + str(frequency))
                        frequency_data = str(run_command('sudo iw dev wlan0 scan freq ' + str(frequency) + ' | grep "channel utilisation"'))
                        if '* channel utilisation: ' in frequency_data and '/' in frequency_data:
                            utilisation = frequency_data.split('* channel utilisation: ',1)[1]
                            if '/' in utilisation:
                                utilisation = utilisation.split('/',1)[0]
                                if utilisation.isdigit():
                                    channel_data[channel_number]['utilisation'] = int(utilisation)

                        if '* station count: ' in frequency_data and '/' in frequency_data:
                            station_count = frequency_data.split('* station count: ',1)[1]
                            station_count = station_count.strip().rstrip()
                            if len(station_count) < 4 and station_count.isdigit():
                                channel_data[channel_number]['station_count'] = int(station_count)
        return channel_data



    # TODO: implement a feature to find all nearby Thread networks using otbr cli/agent


    # Gets called once the Thread radio is alive and ready
    def start_thread_mesh(self):
        if self.DEBUG:
            self.s_print("in start_thread_mesh")
        dataset_loaded = False

        ip_link_show_output = str(run_command('ip link show'))
        if self.DEBUG:
            self.s_print("start_thread_mesh:  ip_link_show_output: \n" + str(ip_link_show_output))

        if 'wpan0' not in ip_link_show_output:
            time.sleep(5)
            ip_link_show_output = str(run_command('ip link show'))



        if os.path.isfile(self.ot_ctl_path) and 'wpan0' in ip_link_show_output:

            if self.DEBUG:
                self.s_print("start_thread_mesh: calling add_otbr_iptables")
            self.add_otbr_iptables()

            if self.DEBUG:
                self.s_print("start_thread_mesh: setting txpower to 8")
            txpower_output = self.run_ot_ctl_command('txpower 8')
            if self.DEBUG:
                self.s_print("txpower_output: ", txpower_output)
            
            time.sleep(1)

            self.update_thread_state_info()


            very_early_dataset = str(self.run_ot_ctl_command('dataset active -x')).replace('Done','').rstrip().strip()
            if self.DEBUG:
                print("very_early_dataset: ", very_early_dataset)
            
            if 'thread_dataset' in self.persistent_data and isinstance(self.persistent_data['thread_dataset'],str) and len(self.persistent_data['thread_dataset']) > 40:
                if self.persistent_data['thread_dataset'] in very_early_dataset:
                    if self.DEBUG:
                        print("start_thread_mesh: DATASET ALREADY LOADED RIGHT FROM THE START")
                    dataset_loaded = True
                    self.thread_dataset_loaded = True

                if 'etached' in self.thread_state_info:
                    if self.DEBUG:
                        self.s_print("start_thread_mesh: very early initial state was detached")
                        #self.s_print("start_thread_mesh: very early initial dataset: \n", self.run_ot_ctl_command('dataset'))

                    self.run_ot_ctl_command('leaderweight ' + str(self.persistent_data['leaderweight']))
                    self.run_ot_ctl_command('state leader')
                    
                
                time.sleep(1)

                self.update_thread_state_info()


            #initial_thread_state = str(self.run_ot_ctl_command('state')).rstrip()
            
            #if self.DEBUG:
            #    self.s_print("initial_thread_state: \n" + str(initial_thread_state))

            




            if dataset_loaded == True:
                if self.DEBUG:
                    self.s_print("\n+\n++\n+++\nIT SEEMS THREAD DATASET WAS ALREADY LOADED AUTOMATICALLY BY OTBR-AGENT")

            else:
                if 'isabled' not in self.thread_state_info and 'etached' not in self.thread_state_info:
                    if self.DEBUG:
                        self.s_print("\nstart_thread_mesh: Thread is already running?!\n" + str(self.thread_state_info))
                        self.s_print("\nstart_thread_mesh: Stopping Thread first\n" + str(self.thread_state_info))
                    if str(self.run_ot_ctl_command('thread stop')).rstrip() == 'Done':
                        if str(self.run_ot_ctl_command('ifconfig down')).rstrip() == 'Done':
                            if self.DEBUG:
                                self.s_print("start_thread_mesh: brought down thread first")
                    #if self.DEBUG:
                    #   print("start_thread_mesh: doing ifconfig wpan0 down")
                
                #run_command('sudo ifconfig wpan0 down')

            
                # TODO: is this a good idea? Ensure thread is stopped and ifconfig down called first?
                #self.thread_running = False



                if self.should_create_thread_mesh == False and 'thread_dataset' in self.persistent_data and isinstance(self.persistent_data['thread_dataset'],str) and len(self.persistent_data['thread_dataset']) > 40:
                    if self.DEBUG:
                        self.s_print("\n+\n++\n+++\nOK, there is a thread dataset in persistent data. Will attempt to load it.")
                    #dataset networkkey
                    #if str(self.run_ot_ctl_command('dataset set active ' + str(self.persistent_data['thread_dataset']))).rstrip() == 'Done':
                    load_dataset_check = str(self.run_ot_ctl_command('dataset init tlvs ' + str(self.persistent_data['thread_dataset']), 60)).rstrip()
                    #load_dataset_check = str(self.run_ot_ctl_command('dataset set active ' + str(self.persistent_data['thread_dataset']), 60)).rstrip()
                    if self.DEBUG:
                        self.s_print("load_dataset_check: ", load_dataset_check)

                    #if str(self.run_ot_ctl_command('dataset init active ' + str(self.persistent_data['thread_dataset']))).rstrip() == 'Done':
                    if load_dataset_check == 'Done':
                        
                        if self.DEBUG:
                            self.s_print("OK, thread dataset from persistent data was set")
                            initial_dataset = str(self.run_ot_ctl_command('dataset')).rstrip()
                            self.s_print("start_thread_mesh: loaded dataset from persistent data?: \n\n", initial_dataset, "\n\n")

                        if str(self.run_ot_ctl_command('dataset commit active')).rstrip() == 'Done':
                            if self.DEBUG:
                                self.s_print("create_new_thread_dataset: OK, called dataset commit active on loaded existing thread dataset")
                            dataset_loaded = True
                            self.thread_dataset_loaded = True
                            
                            up_check = str(self.run_ot_ctl_command('ifconfig up')).rstrip()
                            if up_check == 'Done':
                                if self.DEBUG:
                                    self.s_print("loaded dataset from persistent data, and OTBR ifconfig up done")
                                if str(self.run_ot_ctl_command('thread start')).rstrip() == 'Done':
                                    if self.DEBUG:
                                        self.s_print("loaded dataset from persistent data, and Start Thread done")
                                    
                                    if self.DEBUG:
                                        self.s_print("\nstart_thread_mesh: OK, Thread has now fully started\n")
                                    dataset_loaded = True
                                    self.thread_dataset_loaded = True
                            else:
                                if self.DEBUG:
                                    self.s_print("WARNING, loaded dataset, but ifconfig up failed: ", up_check)
                                self.thread_error = 'Failed to bring up wpan0'

                        else:
                            if self.DEBUG:
                                print("Error, failed to commit active the dataset that was set from persistent data")

                        #if self.DEBUG:
                        #    self.s_print("OK, thread dataset from persistent data was successfully initialised")
                        #    initial_dataset = str(self.run_ot_ctl_command('dataset')).rstrip()
                        #    self.s_print("loaded initial_dataset?: \n\n", initial_dataset, "\n\n")
                        
                        #if str(self.run_ot_ctl_command('dataset set active ' + str(self.persistent_data['vendor_id']))).rstrip() == 'Done':
                            #if self.DEBUG:
                            #    print("OK, existing dataset was succesfully set to active with vendor_id: ", self.persistent_data['vendor_id'])
                        
                        
                        

                        #else:
                        #    if self.DEBUG:
                        #        self.s_print("\nERROR, dataset set active FAILED.  vendor_id: ", self.persistent_data['vendor_id'])
                        #    self.thread_error = 'Setting the Thread dataset to active failed.  vendor_id: ' + str(vendor_id)

                        #if str(self.run_ot_ctl_command('dataset networkname CandleThread')).rstrip() == 'Done':
                            #if str(self.run_ot_ctl_command('set channel ' + str(self.thread_channel))).rstrip() == 'Done':
                            #    if self.DEBUG:
                            #        self.s_print("channel set")
                    elif 'timed out after' in load_dataset_check:
                        if self.DEBUG:
                            self.s_print("ERROR: start_thread_mesh: loading the dataset timed out")
                        self.thread_error = 'Loading the Thread dataset timed out'
                    else:
                        if self.DEBUG:
                            self.s_print("ERROR: start_thread_mesh: loading the existing Thread dataset fell through.  load_dataset_check: ", load_dataset_check)



            
                else:
                    if self.DEBUG:
                        self.s_print("\nWARNING: start_thread_mesh: no thread dataset in persistent data, or self.should_create_thread_mesh: ", self.should_create_thread_mesh)
                    dataset_loaded = self.create_new_thread_dataset()


            if dataset_loaded == False:
                if self.DEBUG:
                    self.s_print("\nERROR, start_thread_mesh: FAILED TO LOAD EXISTING DATASET OR CREATE A NEW ONE\n")
                self.thread_dataset_loaded = False

                self.thread_error = 'FAILED TO LOAD OR CREATE THREAD NETWORK CODE'


                #
                # LOADING DATASET FAILED
                #

                #if 'thread_dataset' in self.persistent_data and isinstance(self.persistent_data['thread_dataset'], str) and len(self.persistent_data['thread_dataset']) > 40:
                #    if self.DEBUG:
                #        print("\nERROR, dataset was not loaded, but there is a thread dataset in persistent data. Did loading the dataset time-out?")
                #    self.thread_error = 'Error, failed to load Thread dataset'
                
                
                
                #else:

                #    dataset_loaded = self.create_new_thread_dataset()


            if dataset_loaded:
                #self.thread_running = True

                self.should_start_matter_time = int(time.time()) + 30

                try:
                    time.sleep(1)

                    self.update_thread_state_info()

                    if self.DEBUG:
                        dataset_check = str(self.run_ot_ctl_command('dataset')).rstrip()
                        self.s_print("OK, DATASET LOADED\ndataset_check: \n" + dataset_check)


                    # 
                    # TODO: TEMPORARY TESTING !!!
                    #

                    if self.DEBUG:
                        self.help_thread_devices_to_connect_to_the_internet = True

                    if self.help_thread_devices_to_connect_to_the_internet:
                        if self.DEBUG:
                            print("help_thread_devices_to_connect_to_the_internet is True")

                        if self.use_hotspot and self.hotspot_net_number != None:

                            # netdata publish prefix fd00:1234:5678::/64 paos med
                            #netdata_prefix_command = 'netdata publish prefix fd00:' + str(self.hotspot_net_number) + '::/64 paos high'
                            #if str(self.run_ot_ctl_command(netdata_prefix_command)).rstrip() == 'Done':
                            #    if self.DEBUG:
                            #        self.s_print("\nsuccesfully published Hotspot Ipv6 prefix to Thread network netdata:\n", netdata_prefix_command)

                            # netdata publish route fd00:1234:5678::/64 s high
                            netdata_route_command = 'netdata publish route fd00:' + str(self.hotspot_net_number) + '::1/64 paros high'
                            if str(self.run_ot_ctl_command(netdata_route_command)).rstrip() == 'Done':
                                if self.DEBUG:
                                    self.s_print("start_thread_mesh: succesfully published Hotpot route to Candle controller to Thread network netdata:\n", netdata_route_command,"\n")

                        if str(self.run_ot_ctl_command('netdata register')).rstrip() == 'Done':
                            if self.DEBUG:
                                self.s_print("\nstart_thread_mesh: OK, netdata register seems to have succeeded")
                            self.thread_netdata_registered = True
                        else:
                            if self.DEBUG:
                                self.s_print("\nERROR: start_thread_mesh: failed to provide the thread network with internet access details")
                            self.thread_netdata_registered = False

                    
                    leaderweight_check = str(self.run_ot_ctl_command('leaderweight ' + str(self.persistent_data['leaderweight']))).rstrip()
                    if leaderweight_check == 'Done':
                        if self.DEBUG:
                            self.s_print("start_thread_mesh: leaderweight set to: ", self.persistent_data['leaderweight'])
                    else:
                        if self.DEBUG:
                            self.s_print("\nERROR: start_thread_mesh: failed to set leaderweight to: ", self.persistent_data['leaderweight'], ",\n - leaderweight_check: ", leaderweight_check)

                    #elif 'isabled' in self.thread_state_info or 'etached' in self.thread_state_info:




                    ifconfig_up_check = str(self.run_ot_ctl_command('ifconfig up')).rstrip()
                    if ifconfig_up_check == 'Done':
                        if self.DEBUG:
                            self.s_print("start_thread_mesh: OK, OTBR ifconfig up done")
                        
                        start_thread_check = str(self.run_ot_ctl_command('thread start')).rstrip()
                        if start_thread_check == 'Done':
                            self.thread_running = True
                            self.should_start_thread_mesh = False
                            if self.DEBUG:
                                self.s_print("\nstart_thread_mesh: OK, Thread has now fully started\n")
                        else:
                            if self.DEBUG:
                                self.s_print("\nERROR: start_thread_mesh: start thread failed.  start_thread_check: ", start_thread_check)

                    else:
                        if self.DEBUG:
                            self.s_print("\nERROR: start_thread_mesh: ifconfig up failed.  ifconfig_up_check: ", ifconfig_up_check)


                    if self.DEBUG:
                        self.s_print("Debugging enabled -> getting thread netdata")
                        self.thread_netdata_info = str(self.run_ot_ctl_command('netdata show'))
                        time.sleep(3)
                        self.thread_netdata_info += '\n'
                        self.thread_netdata_info += str(self.run_ot_ctl_command('ipaddr'))
                        self.s_print("self.thread_netdata_info: ", self.thread_netdata_info)


                    time.sleep(1)

                except Exception as ex:
                    print("caught error after thead dataset was loaded: ", ex)
                
                
                self.update_thread_state_info()

                if 'connect session failed' in self.thread_state_info:
                    if self.DEBUG:
                        print("ERROR: start_thread_mesh:  spotted 'connect session failed' in thread state")
                    time.sleep(10)
                    self.update_thread_state_info()



                if 'connect session failed' in self.thread_state_info:
                    if self.DEBUG:
                        print("ERROR: start_thread_mesh:  still spotted 'connect session failed' in thread state 10 seconds later")
                    self.thread_error = 'Thread reconnection failure'
                    self.thread_running = False
                    self.should_start_thread_mesh = True
                    self.should_start_matter_time = 0

                elif 'leader' in self.thread_state_info or 'router' in self.thread_state_info:
                    self.thread_running = True
                    self.should_start_thread_mesh = False
                    self.thread_error = ''
                    if self.DEBUG:
                        self.s_print("\nOK - Thread is leader or router\n" + str(self.thread_state_info))
                    self.should_start_matter_time = int(time.time()) + 20

                elif 'child' in self.thread_state_info:
                    self.thread_running = True
                    self.should_start_thread_mesh = False
                    self.thread_error = 'Thread is running, but not as the leader'
                    if self.DEBUG:
                        self.s_print("\nERROR, Thread state is child")
                    self.should_start_matter_time = int(time.time()) + 20

                elif 'isabled' in self.thread_state_info or 'etached' in self.thread_state_info:
                    if self.DEBUG:
                        self.s_print("\nWARNING, dataset loaded, but thread started in disabled or detached state. Attempting to bring it up.")
                    #run_command('sudo ifconfig wpan0 up')
                    if str(self.run_ot_ctl_command('ifconfig up')).rstrip() == 'Done':
                        if str(self.run_ot_ctl_command('thread start')).rstrip() == 'Done':
                            self.update_thread_state_info()
                            if 'leader' in self.thread_state_info or 'router' in self.thread_state_info:
                                if self.DEBUG:
                                    self.s_print("\nOK, Thread has now fully started\n")
                                self.thread_running = True
                                self.should_start_thread_mesh = False

                            else:
                                if self.DEBUG:
                                    self.s_print("ERROR, Thread has not started properly. Will attempt to improve.")
                                #self.thread_running = False
                                self.run_ot_ctl_command('leaderweight ' + str(self.persistent_data['leaderweight']))
                                self.run_ot_ctl_command('state leader')
                                time.sleep(1)
                                self.update_thread_state_info()
                                if 'leader' in self.thread_state_info or 'router' in self.thread_state_info:
                                    if self.DEBUG:
                                        self.s_print("\nThread's unexpected state has been improved.  The new Thread state: ", self.thread_state_info)
                                    self.thread_running = True
                                    self.should_start_thread_mesh = False
                                else:
                                    self.thread_running = False
                                    self.thread_error = 'Thread entered unexpected state: ' + str(self.thread_state_info).rstrip()
                                    

                            self.should_start_matter_time = int(time.time()) + 20

                else:
                    if self.DEBUG:
                        self.s_print("\nERROR, checking if thread has started fell through.  Unexpected thread_state: \n" + str(self.thread_state_info))
                    time.sleep(1)
                    self.thread_set_active = False


                if self.thread_running:
                    active_dataset = self.run_ot_ctl_command('dataset active -x')
                    if self.DEBUG:
                        self.s_print("dataset loaded, in theory. dataset active -x: " + str(active_dataset))

                    if isinstance(active_dataset,str) and 'Done' in active_dataset and len(active_dataset) > 40 and not active_dataset.startswith('Error'):
                        self.thread_dataset = str(active_dataset).replace('Done','').strip().rstrip()
                        if self.DEBUG:
                            print("self.thread_dataset from 'dataset active -x' command: ", self.thread_dataset)

                        if len(self.thread_dataset) < 40:
                            self.thread_dataset = ''
                            time.sleep(1)
                            self.thread_set_active = False
                            if self.DEBUG:
                                self.s_print("\nERROR, thread_dataset from dataset active -x was too short to be valid: ", self.thread_dataset)
                            return


                        if self.DEBUG:
                            self.s_print("self.thread_dataset: -->" + str(self.thread_dataset) + "<--")
                        
                        #if not 'thread_dataset' in self.persistent_data:
                        #    self.persistent_data['thread_dataset'] = "" + str(self.thread_dataset)
                        #    self.should_save = True

                        if 'thread_dataset' in self.persistent_data and isinstance(self.persistent_data['thread_dataset'],str) and len(self.persistent_data['thread_dataset']) > 40:
                            if str(self.thread_dataset) == str(self.persistent_data['thread_dataset']):
                                if self.DEBUG:
                                    self.s_print("OK, the thread dataset is still the same")
                                
                            else:
                                if self.DEBUG:
                                    self.s_print("\nERROR, thread dataset is different from the version in persistent data!")
                                    self.s_print("\n\n", str(self.thread_dataset) + "\n != \n" + str(self.persistent_data['thread_dataset']) + "\n\n")
                                self.thread_error = 'Thread dataset mismatch!'
                                #if len(self.thread_dataset) < len(self.persistent_data['thread_dataset']):
                                #    self.thread_dataset = ''
                    else:
                        if self.DEBUG:
                            self.s_print("\nERROR, active thread dataset is way too short: " + str(active_dataset))
                        self.thread_error = 'Failed to load Thread dataset'
                        self.thread_dataset_loaded = False
                        

                else:
                    if self.DEBUG:
                        self.s_print("\nERROR, could not get thread to run!\n")
                    time.sleep(1)
                    self.thread_set_active = False

            else:
                if self.DEBUG:
                    self.s_print("\nERROR, no Thread dataset loaded!\n")
                time.sleep(1)
                self.thread_dataset_loaded = False
                self.thread_set_active = False

                # Start Matter server anyway
                self.should_start_matter = True

            if self.thread_set_active and isinstance(self.thread_dataset,str) and len(self.thread_dataset) > 40:
                if self.matter_server_running == True and self.matter_client_connected == True:
                    # Send Thread dataset info to Matter.server if it's already running
                    self.tell_matter_about_thread_dataset()

                self.s_print("\n__THREAD DETAILS__")
                self.s_print(str(self.run_ot_ctl_command('dataset active -x')))
                self.s_print(str(self.run_ot_ctl_command('netdata show')))
                self.s_print(str(self.run_ot_ctl_command('ipaddr')))
                self.s_print("")
                self.s_print(str(run_command('sudo sysctl -a | grep .wpan0.')))
                self.s_print("")
            else:
                if self.DEBUG:
                    self.s_print("\n__THREAD DETAILS__")
                    self.s_print("\nERROR, no Thread dataset loaded!\n")

            
                


        else:
            self.s_print("\nERROR, start_thread_mesh: ot-ctl does not exist, or 'wpan0' not in ip link show\nself.ot_ctl_path: " + str(self.ot_ctl_path) + "\n" + str(ip_link_show_output) + "\n\n")
            time.sleep(1)
            self.thread_dataset_loaded = False
            self.thread_set_active = False





    def update_thread_state_info(self):
        self.thread_state_info = str(self.run_ot_ctl_command('state'))
        self.thread_state_info = self.thread_state_info.replace('Done','')
        self.thread_state_info = self.thread_state_info.rstrip()
        self.thread_state_info = self.thread_state_info.strip()
        if self.DEBUG:
            self.s_print("update_thread_state_info: Thread state is now: " + str(self.thread_state_info))



    #
    #  CREATING BRAND NEW THREAD DATASET
    #


    def create_new_thread_dataset(self):
        dataset_loaded = False
        if self.DEBUG:
            self.s_print('in create_new_thread_dataset')
            self.s_print("\n\n!\n\nWARNING, creating brand new thread dataset\n\n")

        try:
            if self.run_ot_ctl_command('dataset init new'):
                panid = '0x' + str(run_command('openssl rand -hex 1')).rstrip()
                extpanid = str(run_command('openssl rand -hex 8')).rstrip()
                networkkey = str(run_command('openssl rand -hex 16')).rstrip()
                if len(extpanid) > 4 and len(networkkey) > 8:
                    if str(self.run_ot_ctl_command('dataset panid ' + str(panid))).rstrip() == 'Done': #0xdead
                        if str(self.run_ot_ctl_command('dataset extpanid ' + str(extpanid))).rstrip() == 'Done': # dead1111dead2222
                            if str(self.run_ot_ctl_command('dataset networkname ' + str(self.thread_network_name))).rstrip() == 'Done':
                                
                                #if str(self.run_ot_ctl_command('set channel ' + str(self.thread_channel))).rstrip() == 'Done':
                                #    if self.DEBUG:
                                #        self.s_print("channel set")
                                if str(self.run_ot_ctl_command('dataset channel ' + str(self.thread_channel))).rstrip() == 'Done':
                                    if self.DEBUG:
                                        self.s_print("\ncreate_new_thread_dataset: OK, new dataset channel was set to: ", str(self.thread_channel))
                                    
                                    if str(self.run_ot_ctl_command('dataset networkkey ' + str(networkkey))).rstrip() == 'Done': #11112233445566778899DEAD1111DEAD
                                        if self.DEBUG:
                                            self.s_print("\ncreate_new_thread_dataset: OK, new dataset network key was set")
                                        
                                        #set_active_output = str(self.run_ot_ctl_command('dataset set active ' + str(self.persistent_data['vendor_id']))).rstrip()
                                        #if set_active_output == 'Done':
                                        #    if self.DEBUG:
                                        #        print("OK, brand new dataset was succesfully set to active with vendor_id: ", self.persistent_data['vendor_id'])
                                        #else:
                                        #    if self.DEBUG:
                                        #        self.s_print("create_new_thread_dataset: failed to set new dataset to active with vendor_ID: \n", set_active_output)
                                        if self.use_candle_meshlocal_prefix == True:
                                            if str(self.run_ot_ctl_command('dataset meshlocalprefix fd00:ca4d:1e00:0::')).rstrip() == 'Done':
                                                if self.DEBUG:
                                                    print("succesfully set Candle meshlocal prefix (fd00:ca4d:1e00:0::)")
                                            else:
                                                if self.DEBUG:
                                                    self.s_print("\nERROR:start_thread_mesh: failed to set Candle dataset prefix (fd00:ca4d:1e00:0::) on new mesh dataset")

                                        if str(self.run_ot_ctl_command('dataset commit active')).rstrip() == 'Done':
                                            if self.DEBUG:
                                                self.s_print("create_new_thread_dataset: OK, called dataset commit active on brand new thread dataset")

                                            active_dataset = self.run_ot_ctl_command('dataset active -x')
                                            if self.DEBUG:
                                                self.s_print("create_new_thread_dataset: dataset loaded, in theory. dataset active -x: " + str(active_dataset))

                                            if isinstance(active_dataset,str) and 'Done' in active_dataset and len(active_dataset) > 40:
                                                self.thread_dataset = str(active_dataset).replace('Done','').strip().rstrip()
                                                if self.DEBUG:
                                                    self.s_print("create_new_thread_dataset: self.thread_dataset from 'dataset active -x' command: ", self.thread_dataset)
                                                    self.s_print("\ncreate_new_thread_dataset: SAVING NEW THREAD DATASET TO PERSISTENT DATA\n")
                                                self.persistent_data['thread_dataset'] = self.thread_dataset
                                                self.save_persistent_data()
                                                
                                                dataset_loaded = True
                                                self.thread_dataset_loaded = True
                                            
                                            else:
                                                if self.DEBUG:
                                                    self.s_print("\nERROR:start_thread_mesh: failed to commit new dataset to active")
                                    else:
                                        if self.DEBUG:
                                            self.s_print("\nERROR: start_thread_mesh: failed to set new networkkey")
                                else:
                                    if self.DEBUG:
                                        self.s_print("\nERROR:start_thread_mesh: failed to set new channel")
                            else:
                                if self.DEBUG:
                                    self.s_print("\nERROR:start_thread_mesh: failed to set new networkname to: ", + str(self.thread_network_name))

        except Exception as ex:
            self.s_print("caught error in create_new_thread_dataset: ", ex)
        

        return dataset_loaded






    def parse_mt_pairing_code(self,code):
        if self.DEBUG:
            self.s_print("in parse_mt_pairing_code. code: ", code)
        parsed_output = None
        if isinstance(code,str) and code.upper().startswith('MT:') and os.path.isfile(self.chip_tool_path):
            if self.DEBUG:
                self.s_print("parse_mt_pairing_code: attempting decode")
            parsed_output = self.run_chip_tool_command('payload parse-setup-payload ' + str(code))
            if self.DEBUG:
                self.s_print("parse_mt_pairing_code:  parsed_output: ", parsed_output)
        else:
            if self.DEBUG:
                self.s_print("ERROR: parse_mt_pairing_code: invalid parameters.  code: ", code)
        return parsed_output



    def really_stop_otbr(self):
        if self.DEBUG:
            self.s_print("in really_stop_otbr")

        if self.otbr_stopping_timestamp > time.time() - 2:
            if self.DEBUG:
                self.s_print("Warning, really_stop_otbr was already called less than two seconds ago, so essentially as it was already busy stopping OTBR. Aborting.")
            return False

        self.should_start_thread_mesh = False
        self.otbr_stopping_timestamp = time.time()



        # If a Thread USB stick gets unplugged it makes sense to stop the Thread agent. 
        # But what about matter? Maybe stop matter right when Thread gets started instead? Always give Thread some time to compose itself?


        # Stop Matter first
        #stopped_matter_server_first = None
        #if self.matter_server:
        #    stopped_matter_server_first = self.really_stop_matter()
        #    if self.DEBUG:
        #        self.s_print("really_stop_otbr: had to stop Matter server first. Did that work? ", stopped_matter_server_first)


        if self.otbr_agent_process != None and self.otbr_agent_process.poll() == None:
            self.run_ot_ctl_command('thread stop')
            self.run_ot_ctl_command('ifconfig down')
            #run_command('sudo ifconfig wpan0 down')
            if self.DEBUG:
                self.s_print("really_stop_otbr: called ot-ctl thread stop and ot-ctl ifconfig down")
            if self.otbr_agent_process and self.otbr_agent_process != None:
                self.otbr_agent_process.terminate()
                time.sleep(0.3)
                if self.otbr_agent_process and self.otbr_agent_process.poll() == None:
                    if self.DEBUG:
                        self.s_print("warning, otbr_agent_process is still alive after .terminate() Doing .kill()")
                    self.otbr_agent_process.kill()
                    time.sleep(0.2)
                    if self.otbr_agent_process and self.otbr_agent_process.poll() == None:
                        if self.DEBUG:
                            self.s_print("\nERROR, otbr_agent_process is still alive after .kill(). Calling pkill..")
                        os.system('sudo pkill -f otbr-agent')
        self.otbr_agent_process = None
        #self.thread_radio_is_alive_count = 0
        self.thread_set_active = False
        self.thread_error = ''
        self.thread_running = False
        self.should_start_otbr = False
        self.otbr_started = False
        self.otbr_starting_timestamp = None
        self.otbr_stopping_timestamp == 0

        return True


    def really_stop_matter(self):
        self.should_start_matter = False
        self.should_start_matter_time = 0
        
        if self.matter_stopping_timestamp > time.time() - 2:
            if self.DEBUG:
                self.s_print("Warning, really_stop_matter was already called less than two seconds ago, so essentially as it was already busy stopping Matter. Aborting.")
            return False

        self.matter_stopping_timestamp = time.time()
        if self.server_process != None and self.server_process.poll() == None:
            if self.DEBUG:
                self.s_print("really_stop_mtter: matter process exist. Attempting to stop it now..")

            self.server_process.terminate()
            time.sleep(1)
            if self.server_process and self.server_process.poll() == None:
                if self.DEBUG:
                    self.s_print("warning, server_process is still alive after .terminate(). Doing .kill()")
                self.server_process.kill()
                time.sleep(0.2)
                if self.server_process and self.server_process.poll() == None:
                    if self.DEBUG:
                        self.s_print("\nERROR, server_process is still alive after .kill(). Calling pkill..")
                    os.system('sudo pkill -f matter_server')
        self.server_process = None
        return True



    # Check the Hotspot addon's settings for the SSID and Password
    def load_hotspot_config(self):
        """ This retrieves the HOTSPOT addon settings from the controller """
        if self.DEBUG:
            self.s_print("load_hotspot_config")


        if self.nmcli_installed and os.path.isfile('/boot/firmware/candle_hotspot.txt'):

            hotspot_ssid = run_command("nmcli con show Candle_hotspot | grep 802-11-wireless.ssid | awk '{print $2,$3,$4,$5}'")
            if isinstance(hotspot_ssid,str) and len(hotspot_ssid) > 4:
                self.hotspot_ssid = str(hotspot_ssid)

            if os.path.isfile('/boot/firmware/candle_hotspot_password.txt'):
                hotspot_password = str(run_command('cat /boot/firmware/candle_hotspot_password.txt')).strip().rstrip()
                if len(hotspot_password) == 0 or len(hotspot_password) > 7:
                    self.hotspot_password = hotspot_password
            else:
                self.hotspot_password = ''

            if self.DEBUG:
                self.s_print("load_hotspot_config:  self.hotspot_ssid is now: -->" + str(self.hotspot_ssid) + "<--")
                self.s_print("load_hotspot_config:  self.hotspot_password is now: -->" + str(self.hotspot_password) + "<--")

        #elif self.nmcli_installed and not os.path.isfile('/boot/firmware/candle_hotspot.txt'):
        #    self.hotspot_ssid = None
        #    self.hotspot_password = None


        else:
            self.hotspot_ssid = ""
            self.hotspot_password = ""

            try:
                database = Database('hotspot')
                if not database.open():
                    self.s_print("Error. Could not open hotspot settings database")
                    return False

                config = database.load_config()
                database.close()

            except Exception as ex:
                self.s_print("Error. Failed to open Hotspot settings database: ", ex)
                return False

            try:
                if not config:
                    self.s_print("Warning, no hotspot config.")
                    return False

                # Hotspot name
                try:
                    if 'Hotspot name' in config:
                        if self.DEBUG:
                            self.s_print("-Hotspot name is present in the config data.")
                        self.hotspot_ssid = str(config['Hotspot name'])
                except Exception as ex:
                    self.s_print("Error loading hotspot name from config: " + str(ex))

                # Hotspot password
                try:
                    if 'Hotspot password' in config:
                        if self.DEBUG:
                            self.s_print("-Hotspot password is present in the config data.")
                        self.hotspot_password = str(config['Hotspot password'])
                except Exception as ex:
                    self.s_print("Error loading hotspot password from config: " + str(ex))

            except Exception as ex:
                self.s_print("Error in load_hotspot_config: " + str(ex))




    def client_thread(self):
        if self.DEBUG:
            self.s_print("in client_thread. zzz to wait for matter server")

        try:
            for x in range(10):
                time.sleep(1)
                if self.DEBUG:
                    self.s_print("client thread: zzz")

            if self.DEBUG:
                self.s_print("client thread: ZZZZZ DONE.  Actually starting Matter client now...")
            #rel.set_sleep(0.1)
            #rel.set_turbo(0.0001)

            #url = f"http://127.0.0.1:{self.port}/ws"
            url = "ws://127.0.0.1:" + str(self.port) + "/ws"
            if self.DEBUG:
                self.s_print("attempting to open websocked connection to matter server. URL: " + str(url))
                #websocket.enableTrace(True)
            #else:
            websocket.enableTrace(False)
            self.ws = websocket.WebSocketApp(url, #"wss://127.0.0.1",
                                      on_open=self.on_open,
                                      on_message=self.on_message,
                                      on_error=self.on_error,
                                      on_close=self.on_close
                                      #on_ping=self.on_ping,
                                      #on_pong=self.on_pong
                                      )

            self.ws.run_forever(reconnect=5)
            #ws.run_forever(dispatcher=rel, reconnect=5)  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
            #rel.signal(2, rel.abort)  # Keyboard Interrupt
            #rel.dispatch()
            self.s_print(":::\n:::\n:::\nCLIENT THREAD: BEYOND RUN FOREVER\n:::\n:::\n:::\n")
            """

            """
        except Exception as ex:
            self.s_print("\nERROR, caught general error in client thread: " + str(ex))



    def on_ping(self):
        if self.DEBUG:
            self.s_print("ping")

    def on_pong(self):
        if self.DEBUG:
            self.s_print("pong")

    def on_message(self, ws, message="{}"):
        if self.DEBUG:
            self.s_print("\n.\nclient: in on_message.  Message: " + str(message)[:700] + " \n...etc" + "\n\n")
        try:

            # matter_server.common.models.message.SuccessResultMessage

            message = json.loads(message)
            #if self.DEBUG:
            #    self.s_print("parsed message: " + str(message))


            if 'event' in message.keys():


                """
                Clusters may also have Events, which can be thought of as a record of past state transitions.
                While Attributes represent the current states, events are a journal of the past, and include a
                monotonically increasing counter, a timestamp and a priority. They enable capturing state
                transitions, as well as data modeling that is not readily achieved with attributes.
                - source: https://developers.home.google.com/matter/primer/device-data-model
                """

                if message['event'] == 'server_info_updated':
                    if self.DEBUG:
                        self.s_print("\nRECEIVED server_info_updated MESSAGE\n")
                    self.matter_running = True
                    if 'data' in message:
                        self.last_received_server_info = message['data']
                        #self.matter_fabrics = message['data']
                    """
                    "event": "server_info_updated",
                    "data": {
                        "fabric_id": 1,
                        "compressed_fabric_id": 9642393818747714247,
                        "schema_version": 11,
                        "min_supported_schema_version": 9,
                        "sdk_version": "2025.7.0",
                        "wifi_credentials_set": true,
                        "thread_credentials_set": false,
                        "bluetooth_enabled": true
                    }

                    """

                    #self.get_matter_fabrics()


                elif message['event'] == 'node_added':
                    if self.DEBUG:
                        self.s_print("\nRECEIVED NODE ADDED MESSAGE\n")

                #elif message['event'] == 'node_event':
                #    if self.DEBUG:
                #        self.s_print("\nADAPTER: INCOMING NODE EVENT\n")

                elif message['event'] == 'attribute_updated':
                    self.handle_event(message)

                elif message['event'] == 'node_event':
                    if self.DEBUG:
                        self.s_print("\nADAPTER: INCOMING NODE OR PROPERTY CHANGE\n", message['event'], "\n", message)
                    #if 'attributes' in message['data']:
                    #    process_node(message['data'])
                    self.handle_event(message)

                elif message['event'] == 'node_updated':
                    if self.DEBUG:
                        self.s_print("attempting to feed node data into self.parse_node")
                    self.parse_node(message)


            elif 'fabric_id' in message and 'schema_version' in message and 'sdk_version' in message:
                self.matter_client_connected = True
                #self.matter_running = True

                # Set the wifi credentials
                self.set_wifi_credentials()

                # Set the thread credentials
                self.tell_matter_about_thread_dataset()

                # Set the default matter fabric name
                self.set_default_matter_fabric_name()

                # Start listening
                if self.DEBUG:
                    self.s_print("Sending start_listening command")
                self.ws.send(
                        json.dumps({
                            "message_id": "start_listening",
                            "command": "start_listening"
                        })
                      )



                # Get diagnostic data
                #if self.DEBUG:
                #    self.s_print("Sending diagnostics command")
                #self.ws.send(
                #        json.dumps({
                #            "message_id": "diagnostics",
                #            "command": "diagnostics"
                #        })
                #      )

                # Request Matter nodes list
                if self.DEBUG:
                    self.s_print("Asking for nodes list")
                self.get_nodes()

                return

            elif '_type' in message or 'message_id' in message:
                if '_type' in message and message['_type'] == "matter_server.common.models.server_information.ServerInfo":
                    if self.DEBUG:
                        self.s_print("\n\nRECEIVED MATTER SERVER INFO\n\n")
                    self.matter_server_running = True
                    self.matter_client_connected = True


                # Figuring out what type of message it is can be done this way: https://github.com/matter-js/python-matter-server/blob/0f44085cdfba51b92a88c7eb59ecd147dcb8b755/matter_server/client/connection.py#L167

                # Handle success messages, which contain 'result'
                elif (('_type' in message and message['_type'].endswith("message.SuccessResultMessage")) or 'message_id' in message) and 'result' in message:
                    #if self.DEBUG:
                    #    self.s_print("\n\nOK message.SuccessResultMessage\n\n")

                    #try:
                    #    classy = dataclass_from_dict(SuccessResultMessage,message)
                    #    self.s_print("classy: ", classy)
                    #except Exception as ex:
                    #    self.s_print("caught error transforming message to human-readable version: ", ex)


                    if self.DEBUG:
                        self.s_print("\n\nPARSING MESSAGE WITH A MESSAGE_ID\n\n")

                    if message['message_id'] == "get_matter_fabrics":
                        if self.DEBUG:
                            self.s_print("OK! get_matter_fabrics was succesfull:  message: ", message)

                    elif message['message_id'] == "commission_with_code":
                        if self.DEBUG:
                            self.s_print("OK! Device was paired! result: ", message['result'])
                        #self.discovered = message['result']
                        self.busy_discovering = False
                        self.busy_pairing = False
                        self.pairing_phase = 100
                        self.pairing_phase_message = 'Pairing completed successfully'
                        self.last_pairing_update_time = 0
                        self.get_nodes(True) # True = force

                       # matter_device.py adds it to self.persistent_data['pairing_codes']

                    elif message['message_id'] == 'start_listening':
                        if self.DEBUG:
                            self.s_print("OK LISTENING")
                        self.matter_running = True

                    elif message['message_id'] == 'set_wifi_credentials':
                        if self.DEBUG:
                            self.s_print("OK WIFI CREDENTIALS SET")
                    
                    # discoverCommissionableNodes
                    elif message['message_id'] == 'discover_commissionable_nodes':
                        if self.DEBUG:
                            self.s_print("OK DISCOVER_COMMISSIONABLE_NODES RESPONSE: ", message)
                        self.busy_discovering = False
                        if 'result' in message.keys():
                            self.discovered = message['result']

                    #elif message['message_id'] == 'discover':
                    #    if self.DEBUG:
                    #        self.s_print("OK DISCOVER RESPONSE: ", message)
                    #    self.busy_discovering = False
                    #    if 'result' in message.keys():
                    #        self.discovered = message['result']
                        

                    
                    elif message['message_id'] == 'get_diagnostics':
                        if self.DEBUG:
                            self.s_print("get_diagnostics was successful.  message: ", message)

                    elif message['message_id'] == 'commission_with_code':
                        if self.DEBUG:
                            self.s_print("\n\nNew device paired successfully\n\n")
                        self.send_pairing_prompt("New device paired successfully")
                        self.get_nodes()

                    elif message['message_id'] == 'node_added':
                        if self.DEBUG:
                            self.s_print("\n\nNew device paired successfully\n\n")

                    elif message['message_id'].startswith('get_node_ip_addresses_'):
                        if self.DEBUG:
                            self.s_print("\n\nreceived successful get_node_ip_addresses information\n\n")
                            self.s_print("successful check_node_update message: ", message)
                        if 'result' in message:
                            node_id = str(message['message_id']).replace('get_node_ip_addresses_','')
                            if node_id.isdigit():
                                node_id = int(node_id)
                                if self.DEBUG:
                                    print("get_node_ip_addresses success:  atttempting to add/update ip_addresses for node_id: ", str(node_id))
                                for thing_id in self.persistent_data['nodez']:
                                    if 'node_id' in self.persistent_data['nodez'][str(thing_id)] and str(self.persistent_data['nodez'][str(thing_id)]['node_id']) == str(node_id):
                                        if self.DEBUG:
                                            print("get_node_ip_addresses success:  OK, adding/updating ip_addresses for thing_id", str(thing_id))
                                        self.persistent_data['nodez'][str(thing_id)]['ip_addresses'] = message['result']
                                        self.persistent_data['nodez'][str(thing_id)]['ip_addresses_timestamp'] = int(time.time())
                                        break
                        self.last_matter_ip_check_response_timestamp = int(time.time())
                        
                    elif message['message_id'] == 'get_nodes':
                        if 'result' in message:
                            if self.DEBUG:
                                self.s_print("\n\nGET NODES successful\n\n")
                                
                            #self.nodes = message['result']
                            
                            self.parse_nodes(message['result'])
                            self.ready = True # the addon should now have recreated the things

                    elif message['message_id'].startswith('get_node_'):
                        if self.DEBUG:
                            self.s_print("\n\nGET NODE successful\n\n")
                        device_info = message['result']
                        if self.DEBUG:
                            self.s_print("DEVICE INFO: " + str(json.dumps(device_info)))

                        self.parse_node(message)


                        """
                        node_id = message['message_id'].replace('get_node_','')

                        thing_id = 'matter-' + str(node_id)
                        if str(node_id) in self.node_thing_id_lookup:
                            thing_id = 'matter-' + self.node_thing_id_lookup[str(node_id)]
                            if self.DEBUG:
                                print("remove_node succes: found thing_id in node_thing_id_lookup: ", node_id ," -> ", thing_id)
                        else:
                            #thing_id = 'matter-' + md5_hash(str(node_id)) # small chance, as this would only be a valid thing_id if the device did not have a UniqueID matter property
                            for nodez_thing_id in self.persistent_data['nodez']:
                                if 'node_id' in self.persistent_data['nodez'][str(nodez_thing_id)] and isinstance(self.persistent_data['nodez'][str(nodez_thing_id)]['node_id'],int) and self.persistent_data['nodez'][str(nodez_thing_id)]['node_id'] == node_id:
                                    thing_id = nodez_thing_id
                                    if self.DEBUG:
                                        print("remove_node succes: WARNING, could not find node_id in node_thing_id_lookup, but it was found in self.persistent_data['nodez']: ", node_id ," -> ", thing_id)
                                    break
                        """
                        

                    elif message['message_id'].startswith('update_node_'):
                        if self.DEBUG:
                            self.s_print("\n\nUPDATE NODE successful\n\n")
                        if self.DEBUG:
                            self.s_print("SUCCESFUL UPDATE MESSAGE: \n" + str(json.dumps(message,indent=4)))



                    elif message['message_id'].startswith('remove_node_'):
                        if self.DEBUG:
                            self.s_print("\n\nremove_node was successful\n\n", message)
                        self.device_was_deleted = True

                        node_id = message['message_id'].replace('remove_node_','')

                        thing_id = 'matter-' + str(node_id)
                        if str(node_id) in self.node_thing_id_lookup:
                            thing_id = 'matter-' + self.node_thing_id_lookup[str(node_id)]
                            if self.DEBUG:
                                print("remove_node succes: found thing_id in node_thing_id_lookup: ", node_id ," -> ", thing_id)
                        else:
                            #thing_id = 'matter-' + md5_hash(str(node_id)) # small chance, as this would only be a valid thing_id if the device did not have a UniqueID matter property
                            for nodez_thing_id in self.persistent_data['nodez']:
                                if 'node_id' in self.persistent_data['nodez'][str(nodez_thing_id)] and isinstance(self.persistent_data['nodez'][str(nodez_thing_id)]['node_id'],int) and self.persistent_data['nodez'][str(nodez_thing_id)]['node_id'] == node_id:
                                    thing_id = nodez_thing_id
                                    if self.DEBUG:
                                        print("remove_node succes: WARNING, could not find node_id in node_thing_id_lookup, but it was found in self.persistent_data['nodez']: ", node_id ," -> ", thing_id)
                                    break

                        if self.DEBUG:
                            self.s_print("remove_node:  thing_id: ",  thing_id)
                        if thing_id in self.persistent_data['nodez']:
                            del self.persistent_data['nodez'][thing_id]
                            self.should_save = True
                            if self.DEBUG:
                                self.s_print("remove_node: also removed thing_id from persistent_data: ", thing_id)

                        obj = self.get_device(str(thing_id))
                        if obj:
                            self.handle_device_removed(obj) # Remove from device dictionary
                            if self.DEBUG:
                                self.s_print("remove_node success, and then also removed thing")
                        else:
                            if self.DEBUG:
                                self.s_print("remove_node success, but could not find thing to remove")
                        

                        #self.nodes = message['result']
                        #self.parse_nodes()
                        #self.get_nodes(True)


                    elif message['message_id'].startswith('check_node_update_'):
                        if self.DEBUG:
                            self.s_print("\n\nreceived successful check_node_update information\n\n")
                            self.s_print("successful check_node_update message: ", message)
                        node_id = str(message['message_id']).replace('check_node_update_','')
                        if node_id.isdigit():
                            node_id = int(node_id)
                            for thing_id in self.persistent_data['nodez']:
                                if 'node_id' in self.persistent_data['nodez'][str(thing_id)] and isinstance(self.persistent_data['nodez'][str(thing_id)]['node_id'],int) and self.persistent_data['nodez'][str(thing_id)]['node_id'] == node_id:
                                    if self.DEBUG:
                                        print("setting update details:  thing_id:", str(thing_id))
                                    self.persistent_data['nodez'][str(thing_id)]['update'] = message
                                    self.persistent_data['nodez'][str(thing_id)]['update']['last_update_check_timestamp'] = int(time.time())
                                    break
                        self.last_matter_update_check_response_timestamp = int(time.time())


                    elif message['message_id'] == 'open_commissioning_window' or message['message_id'] == 'commission_on_network':

                        if 'result' in message and isinstance(message['result'],str):
                            self.share_node_code = message['result']
                            if self.DEBUG:
                                self.s_print("\n\nopen_commissioning_window or commission_on_network was successful?  self.share_node_code: ", self.share_node_code, "\n\n")


                    elif message['message_id'] == 'timesync_command':
                        if self.DEBUG:
                            print("Timesync succeeded: ", message)


                    elif message['message_id'] == 'set_thread_dataset':
                        if self.DEBUG:
                            print("set_thread_dataset succeeded. Response message: ", message)
                        self.matter_running = True

                    elif message['message_id'] == 'set_default_fabric_label':
                        if self.DEBUG:
                            print("set_default_fabric_label succeeded. Response message: ", message)
                        self.matter_running = True
                    else:
                        if self.DEBUG:
                            print("Received an unexpected success message: ", message)
                    # Handle event messages
                    #elif ('_type' in message and message['_type'].endswith("message.EventMessage")) or 'message_id' in message:




                #
                #  HANDLE MATTER SERVER FAILURES
                #

                # Handle error messages
                elif (('_type' in message and message['_type'].endswith("message.ErrorResultMessage")) or 'message_id' in message) and 'error_code' in message:
                    if self.DEBUG:
                        self.s_print("\nRECEIVED ERROR MESSAGE\nerror_code: " + str(message['error_code']) )
                        if 'details' in message:
                            self.s_print("Error details: ", message['details'])

                    """
                        INVALID_COMMAND = 1
                        NOT_FOUND = 2
                        STACK_ERROR = 3
                        UNKNOWN_ERROR = 99
                    """

                    if message['message_id'] == "get_matter_fabrics":
                        if self.DEBUG:
                            self.s_print("get_matter_fabrics FAILED:  message: ", message)

                    elif message['message_id'] == 'get_diagnostics':
                        if self.DEBUG:
                            self.s_print("get_diagnostics FAILED")

                    elif message['message_id'] == "device_command":
                        if self.DEBUG:
                            self.s_print("Error was from trying to change a device value")

                    elif message['message_id'] == 'commission_with_code':
                        if self.DEBUG:
                            self.s_print("commission_with_code failed")
                        self.pairing_failed = True

                    elif message['message_id'] == 'open_commissioning_window' or message['message_id'] == 'commission_on_network':
                        if self.DEBUG:
                            self.s_print("open_commissioning_window failed")
                        self.share_node_code = ""
                        self.pairing_failed = True

                    elif message['message_id'] == 'timesync_command':
                        if self.DEBUG:
                            self.s_print("timesync_command failed: ", message)

                    # discoverCommissionableNodes
                    elif message['message_id'] == 'discover_commissionable_nodes':
                        if self.DEBUG:
                            self.s_print("DISCOVER_COMMISSIONABLE_NODES FAILED.  Message: ", message)
                        self.busy_discovering = False

                    elif message['message_id'].startswith('check_node_update_'):
                        if self.DEBUG:
                            self.s_print("\n\nchecking node firmware update apparently failed\n\n")
                            self.s_print("failed check_node_update message: ", message)
                        self.last_matter_update_check_response_timestamp = int(time.time())

                    elif message['message_id'].startswith('update_node_'):
                        if self.DEBUG:
                            self.s_print("\n\nUPDATE NODE FAILED\n\n")
                        if self.DEBUG:
                            self.s_print("FAILED UPDATE MESSAGE: \n" + str(json.dumps(message,indent=4)))

                    elif message['message_id'].startswith('get_node_ip_addresses_'):
                        if self.DEBUG:
                            self.s_print("\n\ngetting node IP addresses failed:\n\n", message)

                    elif message['message_id'].startswith('remove_node_'):
                        if self.DEBUG:
                            self.s_print("\n\nremove_node failed:\n\n", message)
                        self.device_was_deleted = False
                        #self.nodes = message['result']
                        #self.parse_nodes()
                        self.get_nodes(True)

                    elif message['message_id'] == 'set_default_fabric_label':
                        if self.DEBUG:
                            print("set_default_fabric_label FAILED. Response message: ", message)

                    else:
                        if self.DEBUG:
                            self.s_print("\nERROR: interesting, an unanticipated error message. message_id: " + str(message['message_id']) + "\n")





            elif 'error_code' in message:
                self.pairing_failed = True
                if self.DEBUG:
                    self.s_print("message contained an error code: ", message['error_code'])

                if 'details' in message:
                    if self.DEBUG:
                        self.s_print("Error details: " + str(message['details']))

                #self.should_save = True


            else:
                if self.DEBUG:
                    self.s_print("\nWarning, coming message fell through: " + json.dumps(message,indent=4))

        except Exception as ex:
            if self.DEBUG:
                self.s_print("client: error in on_message: " + str(ex))


    def on_error(self, ws, error):
        if self.DEBUG:
            self.s_print("\n.\nclient: on_error: " + str(error))

    def on_close(self, ws, close_status_code, close_msg):
        if self.DEBUG:
            self.s_print("\n.\nclient: on_close. Status code: " + str(close_status_code) +  ", message: "+ str(close_msg))

    def on_open(self, ws):
        if self.DEBUG:
            self.s_print("\n.\nclient: opened connection")
        #print("ws: " + str(ws))


    def get_nodes(self, forced=False):
        try:
            if self.matter_client_connected: # and self.matter_running:
                if forced or self.last_get_nodes_timestamp < time.time() - 30:
                    self.last_get_nodes_timestamp = time.time()

                    if self.DEBUG:
                        self.s_print("get_nodes: Client is connected. Asking for latest node list.  forced: ", forced)

                    message = {
                            "message_id": "get_nodes",
                            "command": "get_nodes"
                        }
                    json_message = json.dumps(message)
                    self.ws.send(json_message)

                    return True
                else:
                    if self.DEBUG:
                        self.s_print("get_nodes: skipping 'get_nodes' command: already did get_nodes recently")
            else:
                if self.DEBUG:
                    self.s_print("Error in get_nodes: client was not connected yet")

        except Exception as ex:
            if self.DEBUG:
                self.s_print("caught error in get_nodes: " + str(ex))

        return False


    def get_node(self, node_id):
        try:
            if self.matter_client_connected: # and self.matter_running:

                if self.DEBUG:
                    self.s_print("get-node: Client is connected, so asking for info on single node")

                message = {
                        "message_id": "get_node_" + str(node_id),
                        "command": "get_node",
                        "args": {
                            "node_id": node_id
                        }
                      }
                json_message = json.dumps(message)
                self.ws.send(json_message)

                return True

        except Exception as ex:
            self.s_print("Error in get_node: " + str(ex))

        return False



    # open_commissioning_window
    def share_node(self, node_id):
        try:
            if self.matter_client_connected and self.matter_running:

                if self.DEBUG:
                    self.s_print("share-node: Client is connected, so asking to open commissioning window")

                message = {
                        "message_id": "open_commissioning_window",
                        "command": "open_commissioning_window",
                        "args": {
                            "node_id": node_id
                        }

                      }
                json_message = json.dumps(message)
                self.ws.send(json_message)

                return True

        except Exception as ex:
            self.s_print("Error in share_node: " + str(ex))

        return False

        """
        {
          "message_id": "open_commissioning_window",
          "command": "open_commissioning_window",
          "args": {
            "node_id": node_id
          }
        }


        async def open_commissioning_window(
                self,
                node_id: int,
                timeout: int = 300,
                iteration: int = 1000,
                option: int = 0,
                discriminator: Optional[int] = None,
            ) -> int:

                #Open a commissioning window to commission a device present on this controller to another.
                #Returns code to use as discriminator.

                return cast(
                    int,
                    await self.send_command(
                        APICommand.OPEN_COMMISSIONING_WINDOW,
                        node_id=node_id,
                        timeout=timeout,
                        iteration=iteration,
                        option=option,
                        discriminator=discriminator,
                    ),
                )

        """



    # Not currently used
    def discover(self):
        try:
            if self.matter_client_connected and self.matter_running:

                self.busy_discovering = True

                if self.DEBUG:
                    self.s_print("discover: Client is connected, so sending discover command to Matter server")

                message = {
                        "message_id": "discover_commissionable_nodes",
                        "command": "discover_commissionable_nodes",
                        "args":{}
                      }

                json_message = json.dumps(message)
                self.ws.send(json_message)

                return True

        except Exception as ex:
            self.s_print("caught error in discover: " + str(ex))

        return False



    # Download the latest certificates
    def download_certs(self):
        if self.DEBUG:
            self.s_print("in download_certs")

        if self.time_between_certificate_downloads == 0:
            if self.DEBUG:
                self.s_print("download_certs: time_between_certificate_downloads is zero. Aborting update attempt")
            self.certificates_updated = True
            return True

        if time.time() - self.time_between_certificate_downloads > self.persistent_data['last_certificates_download_time']:
            if self.DEBUG:
                self.s_print("downloading latest certificates")
            self.pairing_phase_message = 'Updating certificates'
            self.busy_updating_certificates = True
            self.certificates_updated = False
            certificates_download_command = "python3 " + str(self.certs_downloader_path) + " --use-main-net-http --paa-trust-store-path " + str(self.credentials_dir_path)
            if self.DEBUG:
                self.s_print("certificates download command: " + str(certificates_download_command))
            download_certs_output = run_command(certificates_download_command,300)
            if self.DEBUG:
                self.s_print("download_certs_output: " + str(download_certs_output))

                if 'Failed to resolve' in str(download_certs_output):
                    self.s_print("\nFAILED TO DOWNLOAD CERTIFICATES\n")

            self.busy_updating_certificates = False
            if download_certs_output != None:
                self.certificates_updated = True
                self.persistent_data['last_certificates_download_time'] = int(time.time())
                self.should_save = True

                #if len(str(download_certs_output)) > 5:
                if os.path.isdir(self.credentials_dir_path) and len(os.listdir(self.credentials_dir_path)) > 10:
                    self.certificates_updated = True
                    self.persistent_data['last_certificates_download_time'] = int(time.time())
                    self.should_save = True
                    #return True
                else:
                    if self.DEBUG:
                        self.s_print("Error, certificates didn't seem to download (output was None)")
                    self.send_pairing_prompt("failed to download certificates")
                    #return False
                return True

            else:
                if self.DEBUG:
                    self.s_print("Error, certificates didn't seem to download (download_certs_output was None)")
                return False
        else:
            self.certificates_updated = True
            return True



    # Pass WiFi credentials to Matter
    def set_wifi_credentials(self):
        if self.DEBUG:
            self.s_print("in set_wifi_credentials. self.wifi_ssid: " + str(self.wifi_ssid))
            self.s_print("in set_wifi_credentials. self.wifi_password: " + str(self.wifi_password))
        try:
            if self.matter_client_connected and self.matter_running == False:
                if self.DEBUG:
                    self.s_print("Cannot set wifi credentials, client is not connected to Matter server")

            elif self.wifi_ssid != "" and self.wifi_password != "":
                if self.DEBUG:
                    self.s_print("Sharing wifi credentials with Matter server")

                """
                if self.candle_wifi_ssid != "" and self.candle_wifi_password != "":
                    if self.DEBUG:
                        self.s_print("SHARING CANDLE'S WIFI CREDENTIALS")
                    wifi_message = {
                            "message_id": "set_wifi_credentials",
                            "command": "set_wifi_credentials",
                            "args": {
                                "ssid": str(self.candle_wifi_ssid),
                                "credentials": str(self.candle_wifi_password)
                            }
                          }
                else:

                if self.DEBUG:
                    self.s_print("SHARING WIFI CREDENTIALS")
                """
                wifi_message = {
                        "message_id": "set_wifi_credentials",
                        "command": "set_wifi_credentials",
                        "args": {
                            "ssid": str(self.wifi_ssid),
                            "credentials": str(self.wifi_password)
                        }
                      }

                # send wifi credentials
                if self.DEBUG:
                    self.s_print("\n.\n) ) )\n.\nsending wifi credentials: " + str(wifi_message))
                json_wifi_message = json.dumps(wifi_message)

                self.ws.send(json_wifi_message)
                return True

            else:
                if self.DEBUG:
                    self.s_print("Cannot set wifi credentials, as there are no credentials to set yet")
        except Exception as ex:
            if self.DEBUG:
                self.s_print("Error in set wifi credentials: " + str(ex))

        return False



    # Pass Thread credentials to Matter
    def tell_matter_about_thread_dataset(self):
        if self.DEBUG:
            self.s_print("in tell_matter_about_thread_dataset. self.thread_dataset: " + str(self.thread_dataset))
        try:
            if self.thread_running == False:
                if self.DEBUG:
                    self.s_print("Cannot set thread dataset, thread is not running")

            elif self.matter_client_connected and self.matter_running == False:
                if self.DEBUG:
                    self.s_print("Cannot set thread dataset, client is not connected to Matter server")

            elif isinstance(self.thread_dataset,str) and len(self.thread_dataset) > 40:
                if self.DEBUG:
                    self.s_print("Sharing thread dataset with Matter server")

                thread_message = {
                        "message_id": "set_thread_dataset",
                        "command": "set_thread_dataset",
                        "args": {
                            "dataset": str(self.thread_dataset)
                        }
                      }

                # send thread credentials
                if self.DEBUG:
                    self.s_print("\n.\n) ) )\n.\nsending Thread credentials: " + str(thread_message))
                json_thread_message = json.dumps(thread_message)

                self.ws.send(json_thread_message)
                return True

            else:
                if self.DEBUG:
                    self.s_print("cannot set thread dataset for matter.server, as there is no dataset to set yet.  self.thread_dataset: ", self.thread_dataset)

        except Exception as ex:
            if self.DEBUG:
                self.s_print("caught error in set thread dataset: " + str(ex))

        return False


    # Pass default fabric name to Matter
    def set_default_matter_fabric_name(self):
        if self.DEBUG:
            self.s_print("in set_default_matter_fabric_name.  self.default_matter_fabric_name: " + str(self.default_matter_fabric_name))
        try:
            if self.matter_client_connected == False: # and self.matter_running == False:
                if self.DEBUG:
                    self.s_print("Cannot set default thread name, client is not connected to Matter server")

            else:
                if len(str(self.default_matter_fabric_name)) < 2:
                    self.default_matter_fabric_name = 'Home'
                if self.DEBUG:
                    self.s_print("Sharing default fabric name with Matter server: ", self.default_matter_fabric_name)

                name_message = {
                        "message_id": "set_default_fabric_label",
                        "command": "set_default_fabric_label",
                        "args": {
                            "label": str(self.default_matter_fabric_name)
                        }
                      }

                # send name
                if self.DEBUG:
                    self.s_print("\n.\n) ) )\n.\nsending default name message: " + str(name_message))
                json_name_message = json.dumps(name_message)

                self.ws.send(json_name_message)
                return True

        except Exception as ex:
            if self.DEBUG:
                self.s_print("caught error in set set_default_matter_fabric_name: " + str(ex))

        return False








    #
    #   START MATTER PAIRING
    #


    def start_matter_pairing(self,pairing_type=None):
        if self.DEBUG:
            self.s_print("\n\n\n\nin start_matter_pairing. Pairing type: " + str(pairing_type))
        try:
            self.last_pairing_start_time = int(time.time())
            self.last_pairing_update_time = self.last_pairing_start_time

            if self.turn_wifi_back_on_at > self.last_pairing_start_time:
                self.turn_wifi_back_on_at = 0
                if self.DEBUG:
                    print("start_matter_pairing: turning WiFi back on first")
                run_command('nmcli radio wifi on')

            self.pairing_failed = False
            self.pairing_phase = 0
            self.busy_pairing = True
            # Download the latest certificates if they haven't been updated in some time
            self.download_certs()

            if isinstance(pairing_type,str) and len(pairing_type) > 5:
                if self.DEBUG:
                    print("start_matter_pairing: setting last_used_pairing_type to: ", pairing_type)
                self.last_used_pairing_type = pairing_type
            elif self.last_used_pairing_type != None:
                pairing_type = self.last_used_pairing_type
            if not isinstance(pairing_type,str):
                self.pairing_failed = True
                return False

            self.pairing_attempt += 1
            if self.pairing_attempt >= 5:
                self.pairing_failed = True
                self.pairing_phase = -1
                self.pairing_attempt = -1
                self.pairing_phase_message = 'All pairing attempts failed'
                self.busy_pairing = False
                if self.DEBUG:
                    print("start_matter_pairing: it seems all pairing attempts failed")
                return False



            if self.thread_dataset == '' and self.thread_radio_is_alive_count > 2:
                if self.DEBUG:
                    self.s_print("\nERROR: start_matter_pairing: no self.thread_dataset yet!\n")

                #if self.thread_dataset == '':
                #    if self.DEBUG:
                #        self.s_print("\nWARNING: start_matter_pairing: self.thread_dataset was still empty, but thread radio seems to be alive. Attempting to get thread dataset.")
                #    active_dataset = self.run_ot_ctl_command('dataset active -x')
                #    if isinstance(active_dataset,str) and 'Done' in active_dataset:
                #        self.thread_dataset = str(active_dataset).replace('Done','').strip().rstrip()

            if self.DEBUG:
                self.s_print("start_matter_pairing: self.thread_dataset: ", self.thread_dataset)

            # TODO call chip-tool binary directly if need be, or as a fall-back
            #if str(code).upper().startswith('MT:'):
            #    expanded_code = self.parse_mt_pairing_code(code)
            #    self.s_print("start_matter_pairing: expanded_code: ", expanded_code)

            is_thread_device = False

            if self.wireless_type == 'thread' and self.pairing_attempt < 4:
                is_thread_device = True
            elif self.wireless_type == 'unknown' and self.pairing_attempt == 4:
                is_thread_device = True


            if is_thread_device and self.last_found_pairing_code and len(str(self.thread_dataset)) > 40:
                try:
                    if self.DEBUG:
                        self.s_print("\n\nstart_matter_pairing: attempting to decode self.last_found_pairing_code: \n->" + str(self.last_found_pairing_code) + "<--")


                    if isinstance(self.last_decoded_pairing_code,str) and 'Long discriminator:' in self.last_decoded_pairing_code and 'Passcode:' in self.last_decoded_pairing_code:

                        vendor_id = ''
                        if 'VendorID:' in self.last_decoded_pairing_code:
                            vendor_id = self.last_decoded_pairing_code.split('VendorID:')[1]
                            vendor_id = vendor_id.split('\n',1)[0]
                            vendor_id = vendor_id.strip().rstrip()

                        discriminator = self.last_decoded_pairing_code.split('Long discriminator:')[1]
                        discriminator = discriminator.split('(')[0].strip().rstrip()

                        passcode = decoded_pairing_code.split('Passcode:')[1]
                        passcode = passcode.strip().rstrip().strip().rstrip()

                        if self.DEBUG:
                            self.s_print('start_matter_pairing:  vendor_id: -->' + str(vendor_id) + '<--', len(vendor_id))
                            self.s_print('start_matter_pairing:  discriminator: -->' + str(discriminator) + '<--', len(discriminator))
                            self.s_print('start_matter_pairing:  passcode: -->' + str(passcode) + '<--', len(passcode))

                        if len(discriminator) > 0 and len(passcode) >= 8:

                            self.pairing_phase = 6
                            self.turn_wifi_back_on_at = time.time() + 55
                            self.pairing_phase_message = 'Turning of WiFi for 60 seconds in an attempt to limit Bluetooth interference'
                            time.sleep(3)
                            self.pairing_phase = 8
                            run_command('nmcli radio wifi off')
                            time.sleep(1)
                            self.pairing_phase = 9


                            if self.pairing_attempt == 0 or self.pairing_attempt == 2:
                                self.pairing_phase_message = 'Turning Bluetooth off and on again first, perhaps that will help'
                                os.system('sudo btmgmt -i hci0 power off')
                                #if self.pairing_attempt == 2:
                                os.system('sudo btmgmt -i hci0 bredr off')
                                time.sleep(1)
                                os.system('sudo btmgmt -i hci0 power on')
                                time.sleep(1)
                                if self.pairing_attempt == 2:
                                    time.sleep(5)
                            self.pairing_phase = 12




                            self.pairing_phase_message = 'Attempting to find new device'
                            # ./chip-tool pairing ble-thread 1301 hex:[LONGHEX] 20202021 3840
                            pairing_command = 'pairing ble-thread ' + str(self.persistent_data['thing_index']) + ' hex:' + str(self.thread_dataset) + ' ' + str(passcode) + ' ' + str(discriminator)
                            if self.DEBUG:
                                self.s_print("\n\npairing_command: " + str(pairing_command) + "\n\n")

                            self.persistent_data['thing_index'] += 1
                            self.should_save = True

                            self.pairing_phase = 15


                            #os.system('sudo btmgmt -i hci0 power off')
                            #os.system('sudo btmgmt -i hci0 bredr off')
                            #os.system('sudo btmgmt -i hci0 power on')
                            #time.sleep(1)

                            pairing_output = self.run_chip_tool_command(pairing_command)
                            if self.DEBUG:
                                self.s_print("\n\n--->\n\nun_chip_tool_command pairing_output: " + str(pairing_output))

                            return True

                        else:
                            if self.DEBUG:
                                self.s_print("discriminator and passcode were of unexpected length: ", len(discriminator), len(passcode))

                    else:
                        if self.DEBUG:
                            self.s_print("ERROR, was unable to decode the pairing code? ", self.last_decoded_pairing_code)
                    # ./chip-tool pairing ble-thread 1301 hex:[LONGHEX] 20202021 3840

                except Exception as ex:
                    self.s_print("start_matter_pairing: caught error trying to unpack matter pairing code: ", ex)

                self.pairing_failed = True
                return False



            try:
                if self.matter_client_connected and self.matter_running:
                    if self.DEBUG:
                        self.s_print("start_pairing: Client is connected, so sending commissioning code to Matter server.")

                    self.busy_pairing = True
                    self.pairing_phase_message = 'Setting credentials'


                    # Set the wifi credentials
                    if self.pairing_attempt == 0:
                        self.set_wifi_credentials()
                        self.pairing_phase = 2
                        self.tell_matter_about_thread_dataset()
                        self.pairing_phase = 4
                        self.pairing_phase_message = 'Credentials set'

                    self.pairing_phase = 6

                    if self.pairing_attempt == 0:
                        self.pairing_phase_message = 'Turning of WiFi for 60 seconds in an attempt to limit Bluetooth interference'
                        self.turn_wifi_back_on_at = time.time() + 60
                        time.sleep(3) # TODO: Dodgy

                    elif self.pairing_attempt == 2:
                        self.pairing_phase_message = 'Turning of WiFi for 40 seconds in an attempt to limit Bluetooth interference'
                        self.turn_wifi_back_on_at = time.time() + 40
                        time.sleep(3) # TODO: Dodgy


                    elif self.pairing_attempt == 3:
                        self.pairing_phase_message = 'Turning of WiFi for 20 seconds in an attempt to limit Bluetooth interference'
                        self.turn_wifi_back_on_at = time.time() + 20
                        time.sleep(3) # TODO: Dodgy



                    self.pairing_phase = 6
                    if self.pairing_attempt == 0 or self.pairing_attempt == 3:
                        run_command('nmcli radio wifi off')
                        time.sleep(1)
                    self.pairing_phase = 8

                    if self.pairing_attempt == 0 or self.pairing_attempt == 2:
                        self.pairing_phase_message = 'Turning Bluetooth off and on again first, perhaps that will help'
                        os.system('sudo btmgmt -i hci0 power off')
                        if self.pairing_attempt == 2:
                            os.system('sudo btmgmt -i hci0 bredr off')
                        time.sleep(1)
                        os.system('sudo btmgmt -i hci0 power on')
                        time.sleep(1)
                        if self.pairing_attempt == 2:
                            time.sleep(5)
                    self.pairing_phase = 10

                    # create pairing message
                    message = None
                    if pairing_type == 'commission_with_code':
                        message = {
                                "message_id": "commission_with_code",
                                "command": "commission_with_code",
                                "args": {
                                    "code": self.last_found_pairing_code,
                                    "network_only": False # NEW
                                }
                            }

                    elif pairing_type == 'commission_on_network': #1234567
                        message = {
                                "message_id": "commission_on_network",
                                "command": "commission_on_network",
                                "args": {
                                    "setup_pin_code": self.last_found_pin_code
                                }
                            }


                    if self.DEBUG:
                        self.s_print("\nstart_matter_pairing: sending this message: \n", json.dumps(message,indent=4))

                    # Send pairing message
                    if message != None:
                        json_message = json.dumps(message)
                        self.ws.send(json_message)
                        self.pairing_phase = 20
                        self.pairing_phase_message = 'Attempting to pair'
                        return True

                else:
                    self.pairing_phase_message = 'Error, Matter is not running'
                    if self.DEBUG:
                         self.s_print("start_matter_pairing: error, client is not connected")
                         self.send_pairing_prompt("Error, Matter client is not connected")

            except Exception as ex:
                self.s_print("caught error in start_pairing: " + str(ex))
                self.pairing_phase_message = 'An unexpected error occured trying to start pairing'

        except Exception as ex:
            self.s_print("start_matter_pairing: caught error: ", ex)

        self.pairing_phase = 0
        #self.busy_pairing = False
        return False




    def clock(self):
        if self.DEBUG:
            self.s_print("in clock")

        #print("clock: self.running: " + str(self.running))
        last_tick_tock_time = time.time()
        dd = 1
        seconds_counter = 0
        while self.running:
            time.sleep(0.01)
            #self.s_print("clock tick")
            # Check if there is output from the server process

            #if self.DEBUG:
            #    self.s_print("clock dd: " + str(dd))

            dd += 1
            if dd == 100:
                dd = 0
                seconds_counter += 1
                #print("clock: seconds_counter: ", seconds_counter)

                now_stamp = time.time()

                if self.thread_radio_is_alive_count > 999990:
                    self.thread_radio_is_alive_count = 0

                if self.last_get_ips_timestamp + self.get_ips_interval < now_stamp:
                    if self.DEBUG:
                        print("Clock: get_ips_interval has passed. Calling get_node_ips() to update all node IP addresses")
                    self.last_get_ips_timestamp = now_stamp
                    
                    get_ips_thread = threading.Thread(target=self.get_node_ips)
                    get_ips_thread.daemon = True
                    get_ips_thread.start()

                if seconds_counter > 5:
                    seconds_counter = 0
                    self.noise_delta = self.noise_counter - self.previous_noise_counter
                    self.previous_noise_counter = self.noise_counter

                    self.timeout_delta = self.timeout_counter - self.previous_timeout_counter
                    self.previous_timeout_counter = self.timeout_counter
                    
                    if self.thread_dataset_loaded and self.thread_radio_went_missing == False and self.thread_running == False:
                        state_check = str(self.run_ot_ctl_command('state'))
                        if 'leader' in state_check or 'router' in state_check or 'child' in state_check:
                            if self.DEBUG:
                                print("Clock: self.thread_running was False, but it actually seems to be running. Setting it to True")
                            self.thread_running = True
                            self.should_start_thread_mesh = False
                    

                    if self.should_request_all_nodes_info:
                        self.should_request_all_nodes_info = False


                    if self.DEBUG:
                        self.s_print("*")
                        self.s_print("* 5 SECOND LOOP")
                        self.s_print("* self.thread_radio_went_missing: ", self.thread_radio_went_missing)
                        self.s_print("* self.found_new_thread_radio   : ", self.found_new_thread_radio)
                        self.s_print("* self.found_thread_radio_again :  ", self.found_thread_radio_again)
                        self.s_print("* self.should_start_otbr        : ", self.should_start_otbr)
                        self.s_print("* self.otbr_started             :  ", self.otbr_started)
                        self.s_print("* should_create_thread_mesh     : ", self.should_create_thread_mesh)
                        self.s_print("* self.should_start_thread_mesh : ", self.should_start_thread_mesh)
                        self.s_print("* self.thread_running           :  ", self.thread_running)
                        self.s_print("* self.should_start_matter_time :  ", self.should_start_matter_time)
                        self.s_print("* self.should_start_matter      : ", self.should_start_matter)
                        self.s_print("* self.matter_server_running    :  ", self.matter_server_running)
                        self.s_print("* self.matter_client_connected  :  ", self.matter_client_connected)


                    if self.thread_radio_went_missing or (self.found_thread_radio_again == False and self.found_new_thread_radio == False): # or self.should_start_otbr 
                        if self.DEBUG:
                            self.s_print("clock: calling self.find_thread_radio")
                            self.s_print("clock: self.should_start_otbr, self.otbr_started, self.found_thread_radio_again: ", self.should_start_otbr, self.otbr_started, self.found_thread_radio_again)
                        self.find_thread_radio()


                    # Load the Thread dataset once OTBR is ready
                    elif self.should_start_thread_mesh == True and self.otbr_started == True and self.thread_dataset_loaded == False and (self.found_thread_radio_again or self.found_new_thread_radio) and self.thread_radio_went_missing == False:
                        if self.DEBUG:
                            self.s_print("clock 5 second loop: conditions are perfect for the next step. calling self.start_thread_mesh")
                        self.start_thread_mesh()
                        if self.DEBUG:
                             self.s_print("clock 5 second loop: beyond start_thread_mesh")

                        time.sleep(2)
                        if self.thread_dataset_loaded == True and self.thread_running == True:
                            if self.DEBUG:
                                self.s_print("clock 5 second loop: thread dataset was loaded/created succesfully. Setting should_start_thread_mesh to false.")
                            self.should_start_thread_mesh = False
                        else:
                            if self.DEBUG:
                                self.s_print("ERROR: clock 5 second loop: start_thread_mesh failed?")
                                self.s_print(" - self.should_start_thread_mesh: ", self.should_start_thread_mesh)
                                self.s_print(" - self.thread_dataset_loaded: ", self.thread_dataset_loaded)
                                self.s_print(" - self.thread_running: ", self.thread_running)
                            if self.thread_error == '':
                                self.thread_error = 'Radio ready, but loading network code failed'


                    elif self.thread_radio_went_missing == False and self.thread_running == True:
                        state_check = str(self.run_ot_ctl_command('state'))
                        if 'Done' in state_check and 'leader' not in state_check:
                            if self.DEBUG:
                                self.s_print("\nWARNING: clock 5 second loop: Not a thread leader. Requesting to become it again.  state_check was:", state_check)
                            self.run_ot_ctl_command('leaderweight ' + str(self.persistent_data['leaderweight']))
                            self.run_ot_ctl_command('state leader')
                            time.sleep(1)
                            state_check = str(self.run_ot_ctl_command('state'))

                        if 'Done' in state_check and 'leader' in state_check:
                            commissioner_check = str(self.run_ot_ctl_command('commissioner state'))
                            if 'Done' in commissioner_check and 'active' not in commissioner_check:
                                if self.DEBUG:
                                    self.s_print("\nWARNING: clock 5 second loop: leader, but not commissioner. Petitioning to become commissioner again.  commissioner_check was: ", commissioner_check)
                                self.run_ot_ctl_command('commissioner start')

                    
                    if isinstance(self.persistent_data['thread_radio_serial_port'], str) and len(self.persistent_data['thread_radio_serial_port']) > 5:
                        if self.thread_radio_went_missing == False:
                            if not os.path.exists('/dev/serial/by-id/' + str(self.persistent_data['thread_radio_serial_port'])):
                                if self.DEBUG:
                                    self.s_print("\nERROR: clock 5 second loop: thread radio USB stick has disappeared?:  thread_radio_serial_port: ", str(self.persistent_data['thread_radio_serial_port']))
                                self.thread_radio_is_alive_count = 0
                                self.found_new_thread_radio = False
                                self.found_thread_radio_again = False
                                if self.found_a_thread_radio_once:
                                    if self.DEBUG:
                                        self.s_print("clock 5 second loop: found a Thread radio once, so setting self.thread_radio_went_missing to True")
                                    self.thread_radio_went_missing = True
                                if self.otbr_started or self.thread_running:
                                    if self.DEBUG:
                                        self.s_print("clock 5 second loop: WARNING, Thread radio went missing while OTBR was started or Thread was running. calling self.really_stop_otbr()")
                                        self.s_print("- self.otbr_started: ", self.otbr_started)
                                        self.s_print("- self.thread_running: ", self.thread_running)
                                    self.really_stop_otbr()
                        
                    if self.DEBUG:
                        self.s_print("*")



                #self.s_print("tick tock")
                passed_time = time.time() - last_tick_tock_time

                if self.DEBUG:
                    self.s_print("clock: actual seconds that passed: ", passed_time)
                last_tick_tock_time = time.time()

                if passed_time > 2:
                    if self.DEBUG:
                        self.s_print("\n\n\nWARNING, CLOCK WAS VERY DELAYED: ", passed_time, "\n\n\n")




                # Check if the thread radio was unplugged
                if self.found_a_thread_radio_once == True and self.thread_radio_went_missing == False and 'thread_radio_serial_port' in self.persistent_data and isinstance(self.persistent_data['thread_radio_serial_port'],str) and len(str(self.persistent_data['thread_radio_serial_port'])) > 3:

                    if self.thread_running == True:
                        if os.path.isdir('/dev/serial/by-id'):
                            serial_by_id_output = run_command('ls /dev/serial/by-id')
                        else:
                            serial_by_id_output = ''
                            
                        if isinstance(serial_by_id_output,str):  # and len(str(serial_by_id_output)) > 5
                            if not str(self.persistent_data['thread_radio_serial_port']) in serial_by_id_output:
                                if self.DEBUG:
                                    self.s_print("Thread radio was just unplugged? did not spot radio in serial ports list: ", self.persistent_data['thread_radio_serial_port'])
                                self.found_thread_radio_again == False
                                self.found_new_thread_radio == False
                                if self.thread_radio_went_missing == False:
                                    self.send_pairing_prompt("Thread radio was unplugged")
                                    self.found_thread_radio_again = False
                                    self.found_new_thread_radio = False
                                    self.really_stop_otbr()
                                
                                    if self.busy_pairing:
                                        if self.DEBUG:
                                            self.s_print("Thread radio was uplugged during pairing.")
                                        self.busy_pairing = False
                                        if self.turn_wifi_back_on_at > 0:
                                            self.turn_wifi_back_on_at = 0
                                            if self.DEBUG:
                                                self.s_print("Thread radio was uplugged during pairing -> Forcing WiFi back on.")
                                            run_command('nmcli radio wifi on')

                                        self.pairing_failed = True
                                        self.pairing_phase = -1
                                
                                self.thread_radio_went_missing = True

                        if self.thread_radio_went_missing == False:
                            wpan0_check = run_command('ip link show')
                            if isinstance(wpan0_check,str) and not 'wpan0' in wpan0_check:
                                if self.DEBUG:
                                    self.s_print("\nERROR: wpan0 no longer seems to exist even though in theory Thread is running")
                                self.thread_error = "The Thread network was not created. Try rebooting."
                                self.really_stop_otbr()
                                self.should_start_otbr = True


                    #if self.thread_radio_went_missing == False:
                    #    self.ensure_bridge()

                #if self.found_a_thread_radio_once == True and self.thread_radio_went_missing == False:

                
                if self.should_start_matter_time != 0 and self.should_start_matter_time < time.time():
                    self.should_start_matter = True
                    self.should_start_matter_time = 0




                """
                # Check if the thread radio was unplugged

                if self.found_a_thread_radio_once:

                    if self.last_thread_radio_is_alive_timestamp < time.time() - 30:
                        pass

                    elif self.last_thread_radio_is_alive_timestamp < time.time() - 300:

                        self.find_thread_radio()

                        if self.thread_radio_went_missing and self.found_thread_radio_again == False and self.found_new_thread_radio == False and self.otbr_started:
                            if self.DEBUG:
                                self.s_print("Thread radio was unplugged? Stopping OTBR")
                            self.send_pairing_prompt("Thread radio was unplugged?")
                            self.really_stop_otbr()
                        elif self.thread_radio_went_missing and (self.found_thread_radio_again or self.found_new_thread_radio) and self.otbr_started == False and self.thread_set_active == False and self.otbr_agent_process == None:
                            if self.DEBUG:
                                self.s_print("auto-restarting the Thread border router to connect to the USB stick again")
                            self.send_pairing_prompt("Thread radio was plugged in again?")
                            #self.start_otbr()
                """





            #if self.server_process != None:
            #if self.DEBUG:
            #    self.s_print("clock: server_process exists")
                #self.s_print("poll: " + str(self.server_process.poll()))

            if self.turn_wifi_back_on_at != 0 and self.turn_wifi_back_on_at < time.time():
                self.turn_wifi_back_on_at = 0
                if self.DEBUG:
                    self.s_print("Turning WiFi on gain")
                #self.send_pairing_prompt("Turning WiFi on again")
                run_command('nmcli radio wifi on')
                if self.pairing_phase > 0 and self.pairing_phase != 100:
                    self.pairing_phase += 10







            """
            try:
                if self.otbr_agent_process != None and self.otbr_agent_process.poll() == None:

                    for i in range(1000):
                        msg = self.otbr_agent_process.stdout.readline()
                        decoded_message = str(msg.decode()).strip().rstrip()
                        # note to self: do not put a print  statement here
                        if len(decoded_message) > 1:
                            self.otbr_stdout_messages.append(decoded_message)
                        elif decoded_message == '':
                            print("number of lines read from otbr_agent_process stdout: ", i)
                            break

                elif self.otbr_agent_process != None and self.stopping_otbr == False:
                    if self.DEBUG:
                        self.s_print("self.otbr_agent_process has unexptectedly stopped (self.stopping_otbr is False). Calling really_stop_otbr to clean up")
                    self.really_stop_otbr()



            except Exception as ex:
                if self.DEBUG:
                    print("\ncaught errort trying otbr_agent_process.poll(): ", ex)



            """


            if len(self.otbr_stdout_messages):
                self.parse_otbr_messages()


            try:
                if self.server_process and self.server_process.poll() == None:
                    for line in iter(self.server_process.stdout.readline,b''):
                        if self.DEBUG:
                            self.s_print("CAPTURED MATTTER STDOUT: " + str(line.decode().rstrip()))

                        # nothing is coming out of stdout


                    for line in iter(self.server_process.stderr.readline,b''):
                        line = line.decode()
                        if self.DEBUG:
                            self.s_print("CAPTURED MATTTER STDERR: " + str(line.rstrip()))
                        if 'Device discriminator does not match' in line:
                            if self.DEBUG:
                                self.s_print("\n\nERROR: pairing: Device discriminator does not match\n\n")
                            self.pairing_failed = True
                            #self.busy_pairing = False
                            self.pairing_phase_message = 'Device discriminator does not match. Are you pairing two devices simultaneously?'
                            self.pairing_phase = -1
                        if 'collides with an existing FabricAdmin instance' in line:
                            if self.DEBUG:
                                self.s_print("\n\nERROR: matter server fabric config issue\n\n")
                            self.matter_collision_detected = True
                        if 'address already in use' in line:
                            if self.DEBUG:
                                self.s_print("\n\nERROR: matter server running twice?\n\n")
                            self.pairing_failed = True
                            #self.busy_pairing = False
                            self.pairing_phase_message = 'Matter server is running twice??'
                            self.pairing_phase = -1
                        #if 'Traceback' in line:
                        #    self.pairing_failed = True
                        #    self.busy_pairing = False
                        #    self.send_pairing_prompt("Error, Matter server crashed")
                        #    self.pairing_phase_message = 'Matter crashed!'
                        #    self.pairing_phase = -1
                        if 'Commissionable node discovery over BLE failed' in line: # Commissionable node discovery over BLE failed
                            self.pairing_failed = True
                            #self.busy_pairing = False
                            self.send_pairing_prompt("Bluetooth commissioning failed")
                            self.pairing_phase_message = 'Bluetooth scan did not find the device'
                            self.pairing_phase = -1
                        elif 'over BLE failed' in line: # Commissionable node discovery over BLE failed
                            self.pairing_failed = True
                            #self.busy_pairing = False
                            self.send_pairing_prompt("Bluetooth commissioning failed")
                            self.pairing_phase_message = 'Bluetooth connection could not be established'
                            self.pairing_phase = -1
                        if 'Found unconnected device, removing' in line:
                            self.pairing_phase_message = 'Removing unconnected device, likely from a previous failed pairing attempt'
                        if "Error on commissioning step 'WiFiNetworkEnable'" in line:
                            self.pairing_phase_message = 'Pairing failed because the WiFi network could not be enabled'
                        if 'error.NodeInterviewFailed' in line:
                            if self.busy_pairing:
                                self.pairing_failed = True
                                #self.busy_pairing = False
                                self.send_pairing_prompt("Interviewing Matter device failed")
                                self.pairing_phase = -1
                                self.pairing_phase_message = 'Interviewing the Matter device failed'
                        if 'Commission with code failed for node' in line:
                            if self.DEBUG:
                                self.s_print("\nPairing attempt: ", self.pairing_attempt, " failed:\n", line,"\n")
                            if self.pairing_attempt < 5:
                                if self.DEBUG:
                                    self.s_print("Pairing failed, but will try again")
                                self.send_pairing_prompt("Pairing failed.. Trying again..")
                                self.pairing_phase_message = 'Pairing failed.. Trying again..'
                                self.start_matter_pairing()
                            else:
                                self.pairing_failed = True
                                self.busy_pairing = False
                                self.send_pairing_prompt("Interviewing Matter device officially failed")
                                self.pairing_phase_message = 'Pairing attempts failed'
                                self.pairing_phase = -1
                        if 'Established secure session with Device' in line:
                            self.send_pairing_prompt("Connected to new device...")
                            self.pairing_phase_message = 'Secure connection to Matter device established'
                            self.pairing_phase = 50
                            self.last_pairing_update_time = int(time.time())
                        if 'Setting up attributes and events subscription' in line:
                            #if time.time() - self.addon_start_time > 60:
                            if self.busy_pairing:
                                self.send_pairing_prompt("Setting up device...")
                                self.pairing_phase_message = 'Setting up Matter device'
                                self.pairing_phase = 70
                                self.last_pairing_update_time = int(time.time())
                        if 'Discovery timed out' in line:
                            if self.busy_pairing:
                                self.pairing_failed = True
                                #self.busy_pairing = False
                                self.send_pairing_prompt("No new Matter device detected")
                                self.pairing_phase_message = 'No new Matter device detected'
                                self.pairing_phase = -1
                        if 'Failed to establish secure session to device' in line:
                            self.pairing_failed = True
                            #self.busy_pairing = False
                            self.send_pairing_prompt("Creating secure connection to new Matter device failed")
                            self.pairing_phase_message = 'Creating secure connection to new Matter device failed'
                            self.pairing_phase = -1
                        if 'le-connection-abort-by-local' in line:
                            self.pairing_failed = True
                            #self.busy_pairing = False
                            self.send_pairing_prompt("Bluetooth got wireless interference.")
                            self.pairing_phase_message = 'Could not connect to new device via Bluetooth. Possibly because of wireless interference'
                            self.pairing_phase = -1


                        if 'Discovered on mDNS' in line:
                            if self.DEBUG:
                                self.s_print("A device was dicovered on mDNS")
                            # <Node:20>
                            if '<Node:' in line:
                                device_index = line.split('<Node:')[1]
                                if '>' in device_index:
                                    device_index = device_index.split('>')[0]
                                    if device_index.isdigit():
                                        if self.DEBUG:
                                            self.s_print("Node ID of device discovered on mDNS: ", device_index)

                                        thing_id = 'matter-' + str(device_index)
                                        if str(device_index) in self.node_thing_id_lookup:
                                            thing_id = 'matter-' + self.node_thing_id_lookup[str(device_index)]
                                            if self.DEBUG:
                                                print("Discovered on mDNS: found thing_id in node_thing_id_lookup: ", device_index ," -> ", thing_id)
                                        else:
                                            if self.DEBUG:
                                                print("Discovered on mDNS: ERROR, ABORTING: node_id not found in node_thing_id_lookup: ", device_index, self.node_thing_id_lookup)
                                            continue

                                        target_device = self.get_device(thing_id)
                                        if target_device:
                                            target_device.connected = True
                                            target_device.connected_notify(True)
                                            

                        if 'Subscription succeeded with report interval' in line or 'Re-Subscription succeeded' in line:
                            if self.DEBUG:
                                self.s_print("A device re-connected")
                            if '<Node:' in line:
                                device_index = line.split('<Node:')[1]
                                if '>' in device_index:
                                    device_index = device_index.split('>')[0]
                                    if device_index.isdigit():

                                        thing_id = 'matter-' + str(device_index)
                                        if str(device_index) in self.node_thing_id_lookup:
                                            thing_id = 'matter-' + self.node_thing_id_lookup[str(device_index)]
                                            if self.DEBUG:
                                                print("Subscription succeeded with report interval: found thing_id in node_thing_id_lookup: ", device_index ," -> ", thing_id)
                                        else:
                                            if self.DEBUG:
                                                print("Subscription succeeded with report interval: ERROR, ABORTING: node_id not found in node_thing_id_lookup: ", device_index, self.node_thing_id_lookup)
                                            continue

                                        target_device = self.get_device(thing_id)
                                        if target_device:
                                            target_device.connected = True
                                            target_device.connected_notify(True)

                            if self.thread_running and self.informed_matter_server_about_thread == False:
                                self.informed_matter_server_about_thread = self.tell_matter_about_thread_dataset()
                                if self.DEBUG:
                                    self.s_print("A device re-connected -> self.informed_matter_server_about_thread: ", self.informed_matter_server_about_thread)


                        if 'Subscription failed' in line and 'Timeout, resubscription attempt 3' in line:
                            if self.DEBUG:
                                self.s_print("A device seems to have become unavailable")
                            # <Node:20>
                            if '<Node:' in line:
                                device_index = line.split('<Node:')[1]
                                if '>' in device_index:
                                    device_index = device_index.split('>')[0]
                                    if self.DEBUG:
                                        self.s_print("device seems to have become unavailable: ", device_index)
                                    if device_index.isdigit():

                                        thing_id = 'matter-' + str(device_index)
                                        if str(device_index) in self.node_thing_id_lookup:
                                            thing_id = 'matter-' + self.node_thing_id_lookup[str(device_index)]
                                            if self.DEBUG:
                                                print("Subscription failed: found thing_id in node_thing_id_lookup: ", device_index ," -> ", thing_id)
                                        else:
                                            if self.DEBUG:
                                                print("Subscription failed: ERROR, ABORTING: node_id not found in node_thing_id_lookup: ", device_index, self.node_thing_id_lookup)
                                            continue

                                        target_device = self.get_device(thing_id)
                                        if target_device:
                                            target_device.connected = False
                                            target_device.connected_notify(False)
                                            try:
                                                for dev in self.devices:
                                                    if self.DEBUG:
                                                        print("checking is device is connected ", dev)
                                                    if 'id' in dev and 'connected' in dev:
                                                        if self.DEBUG:
                                                            print("device.connected: ", device.id, device.connected)
                                            except Exception as ex:
                                                if self.DEBUG:
                                                    print("caught error checking which devices are connected: ", ex)

                        


                        if 'is not (yet) available' in line:
                            self.send_pairing_prompt("Device not available (yet)")
                            if ' Node ' in line:
                                device_index = line.split(' Node ')[1]
                                device_index = device_index.split('is not (yet) available')[0]
                                if self.DEBUG:
                                    self.s_print("Device not available (yet): ", device_index)
                                if device_index.isdigit():

                                    thing_id = 'matter-' + str(device_index)
                                    if str(device_index) in self.node_thing_id_lookup:
                                        thing_id = 'matter-' + self.node_thing_id_lookup[str(device_index)]
                                        if self.DEBUG:
                                            print("is not (yet) available: found thing_id in node_thing_id_lookup: ", device_index ," -> ", thing_id)
                                    else:
                                        if self.DEBUG:
                                            print("is not (yet) available: ERROR, ABORTING: node_id not found in node_thing_id_lookup: ", device_index, self.node_thing_id_lookup)
                                        continue

                                    target_device = self.get_device(thing_id)
                                    if target_device:
                                        target_device.connected = False
                                        target_device.connected_notify(False)

                        #output = self.server_process.stdout.readline()
                        #error_line = self.server_process.stderr.readline()


                #for x in range(60):
                #    self.s_print(x)

                #if self.DEBUG:
                #    self.s_print("clock run_process: beyond the for loop")
            except Exception as ex:
                self.s_print("caught error in clock message parsing: " + str(ex))
            #else:
            #    self.s_print("self.server_process is None")

            # Save persistent data
            if self.should_save:
                if self.DEBUG:
                    self.s_print("clock: should save persistent was True. Saving data to persistent file.")
                self.should_save = False
                self.save_persistent_data()

            # Synchronize time
            now_stamp = time.time()
            if self.matter_client_connected and self.matter_running and now_stamp - self.last_time_sync_time > self.time_sync_interval:
                if self.DEBUG:
                    self.s_print("CLOCK: time to sync time")
                self.last_time_sync_time = now_stamp

                self.timezone_name = str(run_command('date +%Z')).strip().rstrip()
                #self.timezone_offset = str(run_command('date +%z')).strip().rstrip()
                #self.timestamp = int(str(run_command('date +%s')).strip().rstrip())

                for device_index in self.matter_devices_with_time_sync:
                    thing_id = device_index
                    if not str(thing_id).startswith('matter-'):

                        if str(device_index) in self.node_thing_id_lookup:
                            thing_id = 'matter-' + self.node_thing_id_lookup[str(device_index)]
                            if self.DEBUG:
                                print("is not (yet) available: found thing_id in node_thing_id_lookup: ", device_index ," -> ", thing_id)
                        else:
                            if self.DEBUG:
                                print("is not (yet) available: ERROR, ABORTING: node_id not found in node_thing_id_lookup: ", device_index, self.node_thing_id_lookup)
                            continue

                    target_device = self.get_device(thing_id)
                    if target_device:
                        target_device.sync_time()

        if self.DEBUG:
            self.s_print("\nCLOCK EXITED\n")


    #def something_happened(self, message):
    #    self.s_print("\n\nBINGO\nin something_happened. Message: " + str(message))

    #def client_unsubscribe(self, message):
    #    self.s_print("\n\nBINGO\n client_unsubscribe happened. Message: " + str(message))


    # NOT USED?
    async def run_matter(self):
        """Run the Matter server."""
        if self.DEBUG:
            self.s_print("\nin run_matter")

        # Start Matter Server
        await self.server.start()
        # print("------------------when do I run?--------------------------------------------------")
        # loop.stop()




    async def handle_stop(self, loop: asyncio.AbstractEventLoop):
        if self.DEBUG:
            self.s_print("\nin handle_stop for matter.server")
        """Handle server stop."""
        await self.server.stop()



    def ensure_bridge(self):
        bridge_check = str(run_command('ip link show'))
        # Bridge interfaces if uap0 and wpan0 both exist

        """
        1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
            link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
        2: eth0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc mq state DOWN mode DEFAULT group default qlen 1000
            link/ether e4:5f:01:b7:XX:XX brd ff:ff:ff:ff:ff:ff
        3: wlan0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP mode DORMANT group default qlen 1000
            link/ether e4:5f:01:b7:XX:XX brd ff:ff:ff:ff:ff:ff
        4: uap0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel master virbr state UP mode DEFAULT group default qlen 1000
            link/ether e4:5f:01:b7:XX:XX brd ff:ff:ff:ff:ff:ff permaddr e6:5f:01:17:XX:XX
        12: virbr: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default qlen 1000
            link/ether e4:5f:01:b7:XX:XX brd ff:ff:ff:ff:ff:ff
        """


        # It seems brctl is deprecated
        # sudo ip address add 0.0.0.0/24 dev virbr

        # TODO: check if 192.168.13.1 isn't already used (edge case)
        if 'uap0' in bridge_check and 'wpan0' in bridge_check:

            nmcli_bridge_is_up = False
            nmcli_bridge_state_check = str(run_command('nmcli -f GENERAL.STATE con show CandleBridge'))
            if 'no such connection profile' in nmcli_bridge_state_check:
                create_bridge_check = run_command('nmcli connection add type bridge ifname virbr con-name CandleBridge -- ipv4.method disabled ipv6.method disabled connection.autoconnect yes stp no')
            elif 'activated' in nmcli_bridge_state_check:
                if self.DEBUG:
                    print("nmcli: bridge is in activated state")
                nmcli_bridge_is_up = True

            stp_command = ''
            nmcli_bridge_stp_check = str(run_command('nmcli -f bridge.stp con show CandleBridge'))
            if 'yes' in nmcli_bridge_stp_check:
                stp_command = 'nmcli con modify CandleBridge bridge.stp no'

            #if not 'virbr:' in bridge_check:
            #    if self.DEBUG:
            #        self.s_print("\nCreating brand new bridge")
            #
            #    bridge_command = 'sudo ifconfig uap0 down;sudo ifconfig wpan0 down;sudo brctl addif virbr wpan0;sudo brctl addif virbr uap0;sudo ip addr add 192.168.11.1 dev virbr;sudo ifconfig virbr up;sudo ifconfig wpan0 up;sudo ifconfig uap0 up'
            #    run_command(bridge_command)
            #else:

            #brctl_check = str(run_command('sudo brctl show'))
            """
            bridge name	bridge id		STP enabled	interfaces
            virbr		8000.e45f01b72b30	no		uap0
            """

            if not 'virdummy0' in bridge_check:
                run_command("nmcli con add type dummy ifname virdummy0 con-name 'CandleDummy0';nmcli con add type dummy ifname virdummy0 master CandleBridge connection.autoconnect yes;")
            if not 'virdummy1' in bridge_check:
                run_command("nmcli con add type dummy ifname virdummy1 con-name 'CandleDummy1';nmcli con add type dummy ifname virdummy0 master CandleBridge connection.autoconnect yes;")

            add_to_bridge_command = ''
            add_to_bridge_command_tail = ''
            if not 'uap0' in brctl_check:
                add_to_bridge_command += 'sudo ip link set uap0 down;nmcli con add type wifi ifname uap0 master CandleBridge connection.autoconnect yes;'
                add_to_bridge_command_tail += 'sudo ip link set uap0 up;'
                if self.DEBUG:
                    self.s_print("\n + Adding uap0 interface to bridge (again)")
            if not 'wpan0' in brctl_check:
                #add_to_bridge_command += 'sudo ip link set wpan0 down;nmcli con add type bridge-slave ifname wpan0 master CandleBridge connection.autoconnect yes;'
                add_to_bridge_command += 'sudo ip link set wpan0 down;nmcli con add type wpan ifname wpan0 master CandleBridge connection.autoconnect yes;'
                add_to_bridge_command_tail += 'sudo ip link set wpan0 up;'
                if self.DEBUG:
                    self.s_print("\n + Adding wpan0 interface to bridge (again)")

            if add_to_bridge_command != '':
                add_to_bridge_command = 'nmcli connection down CandleBridge;' + str(stp_command) + str(add_to_bridge_command) + 'nmcli connection up CandleBridge;' + str(add_to_bridge_command_tail)
                if self.DEBUG:
                    print("\nadd_to_bridge_command: \n", add_to_bridge_command, "\n")
                run_command(add_to_bridge_command)

            if nmcli_bridge_is_up == False:
                if self.DEBUG:
                    print("\nbringing CandleBridge back up")
                run_command('nmcli connection up CandleBridge')


    # handles events. In theory events tell you states from the past? But in practise there is some data in there.. which is not in attributes themselves for some reason.
    def handle_event(self,message):

        if not 'data' in message or not 'event' in message:
            if self.DEBUG:
                self.s_print("handle_event: error, no data or event type in provided message")
            return

        event = message['event']
        data = message['data']
        if self.DEBUG:
            self.s_print("in handle_event.  event,data: ", event,"\n", data)

        try:

            node_id = None
            thing_id = None
            endpoint = None
            endpoint_name = None
            value = None
            cluster_id = None
            cluster_name = None
            attribute_name = None
            attribute_code = None
            #attribute_id = None # not used for anything at the moment

            if isinstance(data, list) and len(data) == 3 and isinstance(data[0],int) and isinstance(data[1],str) and '/' in data[1]:
                #print("event = attribute_updated? ", event)
                node_id = data[0]

                #thing_id = 'matter-' + node_id
                if str(node_id) in self.node_thing_id_lookup:
                    thing_id = 'matter-' + self.node_thing_id_lookup[str(node_id)]
                    if self.DEBUG:
                        print("handle_event: found thing_id in node_thing_id_lookup: ", node_id ," -> ", thing_id)
                else:
                    if self.DEBUG:
                        print("\n\nhandle_event: ERROR, ABORTING: node_id not found in node_thing_id_lookup: ", node_id, self.node_thing_id_lookup, "\n\n")
                    self.get_nodes()
                    return
                    #thing_id = 'matter-' + md5_hash(str(node_id))

                value = data[2]
                # three values: node ID, cluster and attribute, and the new value
                endpoint = int(data[1].split('/')[0])
                endpoint_name = 'Endpoint' + str(endpoint)
                cluster_id = int(data[1].split('/')[1])
                #attribute_id = int(data[1].split('/')[2]) # not used for anything at the moment
                attribute_code = humanize(data[1])
                if self.DEBUG:
                    self.s_print("attribute_code from humanize: ", attribute_code)
                cluster_name = attribute_code.split('.Attributes.')[0]
                attribute_name = attribute_code.split('.Attributes.')[1]

                if cluster_name == 'ThreadNetworkDiagnostics':
                    if not thing_id in self.thread_diagnostics:
                        self.thread_diagnostics[thing_id] = {}
                    self.thread_diagnostics[thing_id][attribute_name] = value
                    if self.DEBUG:
                        print("handle_event: self.thread_diagnostics is now: ", self.thread_diagnostics)
                    return

                """

__NeighborTableStruct__

ExtAddress: 11678088788494768592
Age: 5
Rloc16: 3072
LinkFrameCounter: 54603
MleFrameCounter: 7119
Lqi: 3
AverageRssi: -52
LastRssi: -53
FrameErrorRate: 0
MessageErrorRate: 0
RxOnWhenIdle: TRUE
FullThreadDevice: TRUE
FullNetworkData: TRUE
IsChild: FALSE

# https://community.silabs.com/s/question/0D5Vm000006yjdHKAQ/how-to-map-extaddress-to-matter-node-id?language=en_US

# https://github.com/SiliconLabsSoftware/matter_sdk/blob/11813660464759af3765790d21b95953e9b21797/src/app/clusters/thread-network-diagnostics-server/ThreadNetworkDiagnosticsProvider.cpp#L217





__RouteTableStruct__

routeTable.extAddress      = Encoding::BigEndian::Get64(routerInfo.mExtAddress.m8);
routeTable.rloc16          = routerInfo.mRloc16;
routeTable.routerId        = routerInfo.mRouterId;
routeTable.nextHop         = routerInfo.mNextHop;
routeTable.pathCost        = routerInfo.mPathCost;
routeTable.LQIIn           = routerInfo.mLinkQualityIn;
routeTable.LQIOut          = routerInfo.mLinkQualityOut;
routeTable.age             = routerInfo.mAge;
routeTable.allocated       = routerInfo.mAllocated;
routeTable.linkEstablished = routerInfo.mLinkEstablished;

# https://github.com/SiliconLabsSoftware/matter_sdk/blob/11813660464759af3765790d21b95953e9b21797/src/app/clusters/thread-network-diagnostics-server/ThreadNetworkDiagnosticsProvider.cpp#L254-L263



                """


                if clusters_to_ignore and cluster_name in clusters_to_ignore:
                    if self.DEBUG:
                        self.s_print("handle_event: skipping because cluster_name was in list of clusters_to_ignore: ", cluster_name)
                    return
                #if 'Diagnostics' in cluster_name:
                #    if self.DEBUG:
                #        self.s_print("handle_event: skipping diagnostics cluster")
                #    return

                if attribute_name.isdigit():
                    if self.DEBUG:
                        self.s_print("ERROR: handle_event: attribute_name is digit: ", attribute_name)
                    attribute_name = None

            elif 'node_id' in data and 'value' in data and 'attribute_id' in data and 'endpoint_id' in data:
                node_id = data['node_id']
                #thing_id = 'matter-' + node_id
                if str(node_id) in self.node_thing_id_lookup:
                    thing_id = 'matter-' + self.node_thing_id_lookup[str(node_id)]
                    if self.DEBUG:
                        print("handle_event: found thing_id in node_thing_id_lookup: ", node_id ," -> ", thing_id)
                else:
                    if self.DEBUG:
                        print("handle_event: ERROR, ABORTING: node_id not found in node_thing_id_lookup: ", node_id, self.node_thing_id_lookup)
                    self.get_nodes()
                    return
                    #thing_id = 'matter-' + md5_hash(str(node_id))
                value = data['value']
                attribute_name = data['attribute_id']
                endpoint = data['endpoint_id']
                endpoint_name = 'Endpoint' + str(endpoint)

            # handling data['data'] data, like 'totalNumberOfPressesCounted''
            elif self.add_hacky_properties and 'node_id' in data and 'endpoint_id' in data and 'cluster_id' in data and 'data' in data:
                for data_attribute in data['data']:
                    if not 'previous' in data_attribute.lower() and isinstance(data['data'][data_attribute],(str,int,float,bool)):
                        if self.DEBUG:
                            self.s_print("handle_event: found something potentually useful in data['data']: ", data_attribute, data['data'][data_attribute])

                        # "Events are records of past state transitions such as a light device's on-off attribute changing from on to off."
                        # - source: https://docs.silabs.com/matter/latest/matter-api-reference/event

                        node_id = data['node_id']
                        if str(node_id) in self.node_thing_id_lookup:
                            thing_id = 'matter-' + self.node_thing_id_lookup[str(node_id)]
                            if self.DEBUG:
                                print("handle_event: found thing_id in node_thing_id_lookup: ", node_id ," -> ", thing_id)
                        else:
                            if self.DEBUG:
                                print("handle_event: ERROR, ABORTING: hacky node_id not found in node_thing_id_lookup: ", node_id, self.node_thing_id_lookup)
                            self.get_nodes()
                            return
                        #device_id = 'matter-' + str(node_id)
                        endpoint = data['endpoint_id']
                        endpoint_name = 'Endpoint' + str(endpoint)
                        value = data['data'][data_attribute]
                        cluster_name = humanize_cluster_id(data['cluster_id'])

                        if clusters_to_ignore and cluster_name in clusters_to_ignore:
                            if self.DEBUG:
                                self.s_print("handle_event: skipping because cluster_name was in list of clusters_to_ignore: ", cluster_name)

                        hacky_attribute_code = str(cluster_name) + '.Attributes.' + str(data_attribute)
                        attribute_name = str(data_attribute)

                        if self.DEBUG:
                            self.s_print("handle_event: hacky device_id: ", device_id)
                            self.s_print("handle_event: hacky endpoint_name: ", endpoint_name)

                        if not thing_id in self.persistent_data['nodez']:
                            if self.DEBUG:
                                self.s_print("handle_event: unexpectedly, missing thing_id in persistent data? ", thing_id)
                        else:
                            if not endpoint_name in self.persistent_data['nodez'][thing_id]['attributes']:
                                if self.DEBUG:
                                    self.s_print("handle_event: unexpectedly, missing endpoint_name in persistent data? ", endpoint_name)

                            else:
                                if hacky_attribute_code in self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name]:
                                    if self.DEBUG:
                                        self.s_print("handle_event: surprisingly, there is already an attribute with this hacky code: ", self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][hacky_attribute_code])
                                else:
                                    hacky_attribute_code = str(cluster_name) + 'Candle.Attributes.' + str(data_attribute)

                                    if hacky_attribute_code in self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name]:
                                        if self.DEBUG:
                                            self.s_print("handle_event: this hacky property has already been created in persistent data: ", self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][hacky_attribute_code])

                                        #device_id = 'matter-' + str(node_id)
                                        target_device = self.get_device(thing_id)
                                        if target_device:
                                            hacky_property_id = 'property-' + str(endpoint_name) + '-'+ str(cluster_name) + 'Candle-' + str(data_attribute)
                                            if self.DEBUG:
                                                self.s_print("handle_event: hacky_property_id: ", hacky_property_id)
                                            hacky_target_property = target_device.find_property(hacky_property_id)
                                            if hacky_target_property:
                                                if self.DEBUG:
                                                    self.s_print("handle_event: OK, found hacky property. Will update it to: ", value)
                                                hacky_target_property.update( value )

                                    else:
                                        attribute_code = hacky_attribute_code
                                        if self.DEBUG:
                                            self.s_print("\nhandle_event: creating new hacky property\n")
                                        self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][hacky_attribute_code] = {'enabled':True,'property':{'description':{'title':uncamel(data_attribute).replace('_',' ') + ' ' + str(endpoint),'readOnly':True}},'hacky':True,'value': value, 'received_values':[value]}
                                        if isinstance(value,int):
                                            self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][hacky_attribute_code]['property']['description']['type'] = 'number'
                                        elif isinstance(value,str):
                                            self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][hacky_attribute_code]['property']['description']['type'] = 'string'
                                        elif isinstance(value,bool):
                                            self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][hacky_attribute_code]['property']['description']['type'] = 'boolean'

                                        self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][hacky_attribute_code]['property']['attribute_code'] = attribute_code

                                        #device_id = 'matter-' + str(node_id)
                                        target_device = self.get_device(thing_id)
                                        if target_device:
                                            if self.DEBUG:
                                                self.s_print("handle_event: calling reparse_node so that the new hacky property will immediately be created")
                                            target_device.reparse_node()



            else:
                if self.DEBUG:
                    self.s_print("\nWARNING: handle_event: getting parameters fell through")

            if self.DEBUG:
                self.s_print("handle_event: node_id, attribute_name, value: ", node_id, attribute_name, value)

            if node_id and endpoint_name and attribute_name: # should value be allowed to be None?
                #thing_id = 'matter-' + str(node_id)

                if str(node_id) in self.node_thing_id_lookup:
                    thing_id = 'matter-' + self.node_thing_id_lookup[str(node_id)]
                    if self.DEBUG:
                        print("handle_event: part 2: found thing_id in node_thing_id_lookup: ", node_id ," -> ", thing_id)
                else:
                    if self.DEBUG:
                        print("handle_event: part 2: ERROR, ABORTING: hacky node_id not found in node_thing_id_lookup: ", node_id, self.node_thing_id_lookup)
                    return

                target_device = self.get_device(thing_id)

                if endpoint and attribute_code:
                    endpoint_name = 'Endpoint' + str(endpoint)
                    if str(thing_id) in self.persistent_data['nodez']:
                        if 'attributes' in self.persistent_data['nodez'][thing_id] and endpoint_name in self.persistent_data['nodez'][thing_id]['attributes']:

                            if attribute_code == None:
                                if self.DEBUG:
                                    self.s_print("handle_event: attribute_code was None")

                            elif str(attribute_code) in self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name]:
                                if self.auto_enable_properties == True:
                                    if 'enabled' in self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][str(attribute_code)] and self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][str(attribute_code)]['enabled'] == False:
                                        if self.DEBUG:
                                            self.s_print("handle_event: auto-enabling a property: ", attribute_code)
                                        self.should_save = True
                                    self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][str(attribute_code)]['enabled'] = True

                                # Keep track of the different type of variables that can be expected to be received
                                if not 'received_values' in self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][str(attribute_code)]:
                                    self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][str(attribute_code)]['received_values'] = []
                                elif len(self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][str(attribute_code)]['received_values']) > 10:
                                    if self.DEBUG:
                                        self.s_print("handle_event: trimming received values list back to 10 items")
                                    self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][str(attribute_code)]['received_values'] = self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][str(attribute_code)]['received_values'][-9:]

                                # Keep track of how many decimal points any numbers being sent will have, at maximum
                                # Also keep track of the smallest and largest number ever received. Useful to find out of percentages need to be scaled from 255, for example
                                # It is a privacy risk, so these values should not be exposed to the user, through it may be temping to use such values when displaying graph axis
                                if value != None and isinstance(value,(int,float)):
                                    if not 'max_decimals_received' in self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][str(attribute_code)]:
                                        self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][str(attribute_code)]['max_decimals_received'] = -1
                                    if not 'max_value_received' in self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][str(attribute_code)]:
                                        self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][str(attribute_code)]['max_value_received'] = value
                                    elif value > self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][str(attribute_code)]['max_value_received']:
                                        self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][str(attribute_code)]['max_value_received'] = value
                                    if not 'min_value_received' in self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][str(attribute_code)]:
                                        self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][str(attribute_code)]['min_value_received'] = value
                                    elif value < self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][str(attribute_code)]['min_value_received']:
                                        self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][str(attribute_code)]['min_value_received'] = value
                                    decimals = None
                                    if '.' in str(value):
                                        parts = str(value).split('.')
                                        if len(parts) == 2:
                                            parts[1] = str(parts[1])[:3]
                                            if str(parts[0]).isdigit() and str(parts[1]).isdigit():
                                                parts[1] = str(parts[1]).rstrip('0')
                                                decimals = len(parts[1])

                                    elif str(value).isdigit():
                                        decimals = 0
                                    #decimals = str(number)[::-1].find('.')
                                    if self.DEBUG:
                                        self.s_print("handle_event: max decimals spotted: ", decimals)

                                    if decimals != None and decimals > self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][str(attribute_code)]['max_decimals_received']:
                                        self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][str(attribute_code)]['max_decimals_received'] = decimals


                                if value != None and isinstance(value,(str,int,float,bool)):
                                    if not value in self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][str(attribute_code)]['received_values']:
                                        if self.DEBUG:
                                            self.s_print("handle_event: appending not seen before value to received_values: ", value)
                                        self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][str(attribute_code)]['received_values'].append(value)
                                    else:
                                        if self.DEBUG:
                                            self.s_print("handle_event: that value has been received before: ", value)

                                    # Privacy risk to update the actual value
                                    #self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][attribute_code]['value'] = value

                                if self.DEBUG:
                                    self.s_print("handle_event: received values:  thing_id,endpoint_name,attribute_code,values: ", thing_id, endpoint_name, attribute_code, self.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][str(attribute_code)]['received_values'])


                if target_device == None:
                    if self.DEBUG:
                        self.s_print("\nERROR: handle_event: missing device: ", thing_id)
                    if not thing_id in self.missing_devices:
                        self.missing_devices.append(thing_id)
                        if self.DEBUG:
                            print("self.missing_devices is now: ", self.missing_devices)

                else:
                    property_id = 'property-' + str(endpoint_name) + '-'+ str(cluster_name) + '-' + str(attribute_name)
                    if self.DEBUG:
                        self.s_print("looking for property with property_id: ", property_id)
                    target_property = target_device.find_property(property_id)

                    if target_property == None:
                        if self.DEBUG:
                            self.s_print("handle_event: found thing, but missing property: ", property_id)
                        if 'attributes' in data and len(data['attributes'].keys()) > 2 and 'Endpoint' in str(list(data['attributes'].keys())): # TODO: Very hacky, should check these assumptions too
                            if self.DEBUG:
                                self.s_print("handle_event: attempting update_from_node... with potential node data: ", data)
                            target_device.update_from_node(data)
                        else:
                            if self.DEBUG:
                                self.s_print("\nWARNING, there is no way to add the missing property now\ndata: ", data)
                            self.should_save = True
                    else:
                        if self.DEBUG:
                            self.s_print("handle_event: found existing property. calling property.update with value: ", value)
                        target_property.update( value )


                    # Also create and/or update event property if it exists
                    if isinstance(cluster_name,str) and cluster_name in self.events_lookup:

                        event_property_id = 'property-' + str(endpoint_name) + '-'+ str(cluster_name) + '-RecentEvent'
                        if self.DEBUG:
                            self.s_print("handle_event: event_property_id: ", event_property_id)

                        target_event_property = target_device.find_property(event_property_id)
                        if target_event_property:
                            if self.DEBUG:
                                self.s_print("handle_event: found event property")
                                self.s_print("possible events for cluster: ", cluster_name, self.events_lookup[cluster_name])

                            if 'event_id' in data and isinstance(data['event_id'],int) and data['event_id'] >= 0 and data['event_id'] < len(self.events_lookup[cluster_name]):
                                target_event_property.update( self.events_lookup[cluster_name][data['event_id']] )


                                #'Switch.Attributes.CurrentPosition':
                                """
                                0x00 SwitchLatched INFO V LS
                                0x01 InitialPress INFO V MS
                                0x02 LongPress INFO V MSL
                                0x03 ShortRelease INFO V MSR
                                0x04 LongRelease INFO V MSL
                                0x05 MultiPressOngoing
                                0x06 MultiPressComplete
                                """

                                #if attribute_code == 'Switch.Attributes.CurrentPosition' and data['event_id'] < len(self.switch_events):
                                #    target_event_property.update( self.switch_events[data['event_id']] )



                            #else:
                            #    target_event_property.update( 'None' )
                            #    if self.DEBUG:
                            #        self.s_print("handle_event: no event id, so setting event property to None")
                        else:
                            if self.DEBUG:
                                self.s_print("handle_event: did not find RecentEvent property")




        except Exception as ex:
            if self.DEBUG:
                self.s_print("caught error in handle_event: " + str(ex))
                self.s_print(traceback.print_exc())

        """
        OLD:
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



    # Create new devices from Matter nodes
    def parse_nodes(self,new_nodes):
        if self.DEBUG:
            self.s_print("in parse_nodes. new_nodes length: " + str(len(new_nodes)))
            #self.s_print("parse_nodes. self.nodes keys: ", self.nodes.keys())
            #self.s_print("in parse_nodes. self.nodes: \n\n", json.dumps(self.nodes,indent=4), "\n\n")
        self.nodes = []
        for node in list(new_nodes):
            try:
                improved_node = self.parse_node(node)
                self.nodes.append(improved_node)
            except Exception as ex:
                print("caught error in parse_nodes while looping over a node: ", ex)
            
        if os.path.isdir('/home/pi'):
            with open("/home/pi/matter_nodes.json", "w") as json_file:
                if self.DEBUG:
                    self.s_print("parse_nodes: saving self nodes, which now has length: " + str(len(self.nodes)))
                json.dump(self.nodes, json_file, indent=4)


    def parse_node(self,node):

        try:
            #if self.DEBUG:
            #    self.s_print("parse nodes: number: " + str(node_number))
            #node = self.nodes[node_number]


            """
            # Example get_nodes response, where each item in the 'result' array is fed into this function

            "message_id": "get_nodes",
            "result": [
            {
                "node_id": 7,
                "date_commissioned": "2026-05-24T22:47:15.368546",
                "last_interview": "2026-05-24T22:47:15.368551",
                "interview_version": 6,
                "available": false,
                "is_bridge": false,
                "attributes": {
                    "0/29/0": [
                        {
                        "0": 18,
                        "1": 1
                        },
                        {
                        "0": 22,
                        "1": 1
                        }
                    ],
                    "0/29/1": [
                        29,
                        31,
                        40,
                        42,
                    etc
            """


            event = None
            if 'event' in node:
                event = node['event']

            node_id = None
            if 'node_id' in node:
                node_id = node['node_id']
            elif 'data' in node and 'node_id' in node['data']:
                node_id = node['data']['node_id']


            if node_id == None:
                if self.DEBUG:
                    self.s_print("\nERROR: parse_node: no node_id in node or node['data']: ", node)
                return


            



            

            


            if not 'attributes' in node and 'data' in node and 'attributes' in node['data']:
                if self.DEBUG:
                    self.s_print("pulling a switch to make node['data'] the new node")
                node = node['data']

            available = False
            if 'available' in node and isinstance(node['available'],bool):
                available = node['available']

            is_bridge = False
            if 'is_bridge' in node and isinstance(node['is_bridge'],bool):
                is_bridge = node['is_bridge']

            
            if 'attributes' in node:
                #if self.DEBUG:
                    #print("parse_node: node before: \n", json.dumps(node,indent=2))
                    #print('parse_node: NODE BEFORE...')
                    #print("\nparse_node: end of node before\n\n\n\n\n\n\n\n")

                try:
                    for attr_path, value in node["attributes"].items():
                        endpoint_id, cluster_id, attr_id = attr_path.split("/")
                        cluster_id = int(cluster_id)
                        endpoint_id = int(endpoint_id)
                        attr_id = int(attr_id)
                        if not cluster_id in self.completed_command_clusters:
                            command_lookup_table = get_commands_for_cluster_id(cluster_id)
                            if command_lookup_table and len(list(command_lookup_table.keys())):
                                self.commands_lookup = self.commands_lookup | command_lookup_table
                                self.completed_command_clusters.append(cluster_id)
                                if self.DEBUG:
                                    self.s_print("self.completed_command_clusters is now: ", self.completed_command_clusters)
                            #else:
                            #    if self.DEBUG:
                            #        self.s_print("\nERROR, get_commands_for_cluster_id did not return a valid dict")
                except Exception as ex:
                    if self.DEBUG:
                        self.s_print("caught error looping over node in order to get all commands: ", ex)


                #
                #  PROCESS NODE
                #  This util function add human-readable attribute codes
                #

                if self.DEBUG:
                    self.s_print("parse_node: node before: \n", json.dumps(node,indent=2))
                    print("\n\n-------------------\n\n")

                process_node(node) # util function that adds human readable attributes

                if self.DEBUG:
                    self.s_print("parse_node: node after: \n", json.dumps(node,indent=2))

                


            else:
                if self.DEBUG:
                    self.s_print("\nERROR: parse_node: aborting, no attributes in node data?: ", node)
                return node


            # already handled by device
            # TODO: COMMENT THIS OUT AGAIN, AS THE DEVICE SHOULD HANDLE ADDING ITSELF TO THIS LIST
            #if not device_id in self.persistent_data['nodez']:
            #    self.persistent_data['nodez'][device_id] = {'device_id':device_id,'node_id':node_id,'attributes':{}}
            #    self.should_save = True


            if not 'node_id' in node:
                if self.DEBUG:
                    self.s_print("\nERROR: parse_node: node_id is missing from node data after process_node: ", node)
                return node


            thing_id = 'matter-' + str(node_id)
            if not str(node_id) in self.node_thing_id_lookup:
                if self.DEBUG:
                    print("parse_node: this node is not in self.node_thing_id_lookup yet")

                unique_id = str(node_id)
                if 'attributes' in node and 'Endpoint0' in node['attributes'] and 'BasicInformation' in node['attributes']['Endpoint0'] and 'UniqueID' in node['attributes']['Endpoint0']['BasicInformation']:
                    unique_id = md5_hash(node['attributes']['Endpoint0']['BasicInformation']['UniqueID'])
                else:
                    unique_id = md5_hash(str(node_id))
                
                self.node_thing_id_lookup[str(node_id)] = str(unique_id)
                thing_id = 'matter-' + str(unique_id)
            else:
                if 'attributes' in node and 'Endpoint0' in node['attributes'] and 'BasicInformation' in node['attributes']['Endpoint0'] and 'UniqueID' in node['attributes']['Endpoint0']['BasicInformation']:
                    unique_id = md5_hash(str(node['attributes']['Endpoint0']['BasicInformation']['UniqueID']))
                    if unique_id == self.node_thing_id_lookup[str(node_id)]:
                        if self.DEBUG:
                            print("OK, unique_id is still the same for node_id: ", node_id, " --> ", unique_id)
                    else:
                        if self.DEBUG:
                            print("\n\nERROR, clashing unique_ID's!! UPDATING node_thing_id_lookup!\n", node_id, " --> ", unique_id , "\n\n")
                        self.node_thing_id_lookup[str(node_id)] = str(unique_id)
                    thing_id = 'matter-' + str(unique_id)
                else:
                    if self.DEBUG:
                        print("\n\nERROR, no longer a UniqueID attribute found in parse_node for  node_id, node: ", node_id, node)
                    if str(node_id) in self.node_thing_id_lookup:
                        if self.DEBUG:
                            print("FALLING BACK TO LOOKUP TABLE IN PARSE_NODE\n\n")
                        thing_id = 'matter-' + self.node_thing_id_lookup[str(node_id)]
                    else:
                        if self.DEBUG:
                            print("\n\nERROR!\n\nERROR: parse_node: there is no way to get the thing_id: no UniqueID and node_id was not found in self.node_thing_id_lookup: ", node_id, "\n", json.dumps(self.node_thing_id_lookup,indent=2), "\n\n")
                        return


            if self.DEBUG:
                print("\nself.node_thing_id_lookup: \n", json.dumps(self.node_thing_id_lookup,indent=2))
                print("\nparse_node:  node_id,thing_id: \n", node_id, " --> ", thing_id, "\n")


            if available and 'attributes' in node and 'Endpoint0' in node['attributes']:
                print("ThreadNetworkDiagnostics:  well, attributes exists..")
                print("node['attributes'] keys: ", node['attributes']['Endpoint0'].keys())
            if available and 'attributes' in node and 'Endpoint0' in node['attributes'] and 'ThreadNetworkDiagnostics' in node['attributes']['Endpoint0']:
                if self.DEBUG:
                    print("parse_node: spotted ThreadNetworkDiagnostics, adding it to self.thread_diagnostics for thing_id: ", thing_id)
                self.thread_diagnostics[thing_id] = node['attributes']['Endpoint0']['ThreadNetworkDiagnostics']
                self.thread_diagnostics[thing_id]['is_bridge'] = is_bridge
                if 'GeneralDiagnostics' in node['attributes']['Endpoint0'] and 'NetworkInterfaces' in node['attributes']['Endpoint0']['GeneralDiagnostics']:
                    if self.DEBUG:
                        print("parse_node: spotted GeneralDiagnostics, adding it to self.general_diagnostics for thing_id: ", thing_id)
                    self.thread_diagnostics[thing_id]['NetworkInterfaces'] = node['attributes']['Endpoint0']['GeneralDiagnostics']['NetworkInterfaces']
            
            
            if available and thing_id not in self.reconnected_devices:
                self.reconnected_devices[thing_id] = {'node_id': int(node_id), 'thing_id':thing_id, 'reconnected_timestamp':int(time.time()), 'available':available}
                if self.DEBUG:
                    print("self.reconnected_devices is now: ", json.dumps(self.reconnected_devices,indent=2))
                self.get_node_ip(node_id)

            if self.DEBUG:
                self.s_print("\n\nparse_node: thing_id: " + str(thing_id))
                #print("node: \n", json.dumps(dataclass_to_dict(node),indent=2))


            
            if available:
                target_device = self.get_device(thing_id)
                if target_device == None:
                    if self.DEBUG:
                        self.s_print("parse_node: this device does not exist yet. Creating it now.")

                    # pass along the pairing code so that it will be stored in the pairing codes library
                    # TODO: there is room for error here. What if self.last_found_pairing_code doesn't actually match the device being created?
                    pairing_code = None
                    if isinstance(self.last_found_pairing_code,str) and self.last_found_pairing_code not in self.persistent_data['pairing_codes'] and self.last_pairing_start_time > time.time() - 120:
                        pairing_code = "" + str(self.last_found_pairing_code)

                    new_device = MatterDevice(self, thing_id, node, pairing_code)
                    self.handle_device_added(new_device)
                    
                else:
                    if self.DEBUG:
                        self.s_print("parse_node: target_device has already been created. Attempting to call it's update_from_node method.")
                    target_device.update_from_node(node)
                    self.handle_device_added(target_device)

            else:
                print("Not creating thing because matter node says it's not actually available yet")
            
            if 'available' in node and isinstance(node['available'],bool):
                target_device = self.get_device(thing_id)
                if target_device:
                    if self.DEBUG:
                        self.s_print("parse_node: OK, calling connected_notify on device with state: ", node['available'])
                    target_device.connected_notify(node['available'])
                else:
                    if self.DEBUG:
                        self.s_print("\nWARNING: parse_node: unexpectedly device was still not created.  thing_id: ", thing_id)


        except Exception as ex:
            if self.DEBUG:
                self.s_print("error in parse_node: " + str(ex))



        return node

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



    def get_matter_fabrics(self):
        if self.DEBUG:
            self.s_print("in get_matter_fabrics")

        try:
            if self.matter_client_connected and self.matter_running:

                message = {
                            "message_id": "get_matter_fabrics",
                            "command": "get_matter_fabrics",
                            "args": {}
                        }

                if self.DEBUG:
                    self.s_print("\nget_matter_fabrics: sending message to Matter.server: \n", json.dumps(message,indent=4))

                json_message = json.dumps(message)
                self.ws.send(json_message)

        except Exception as ex:
            if self.DEBUG:
                print("caught error in get_matter_fabrics: ", ex)



    def get_diagnostics(self):
        if self.DEBUG:
            self.s_print("in get_diagnostics")

        try:
            if self.matter_client_connected and self.matter_running:

                message = {
                            "message_id": "get_diagnostics",
                            "command": "diagnostics",
                            "args": {}
                        }

                if self.DEBUG:
                    self.s_print("\nget_diagnostics: sending message to Matter.server: \n", json.dumps(message,indent=4))

                json_message = json.dumps(message)
                self.ws.send(json_message)

        except Exception as ex:
            if self.DEBUG:
                print("caught error in get_diagnostics: ", ex)




    #GET_NODE_IP_ADDRESSES

    def get_node_ips(self):
        if self.DEBUG:
            self.s_print("in get_node_ips")

        try:
            
            if self.matter_client_connected and self.matter_running and 'nodez' in self.persistent_data:
                for thing_id in self.persistent_data['nodez']:
                    if 'node_id' in self.persistent_data['nodez'][str(thing_id)] and isinstance(self.persistent_data['nodez'][str(thing_id)]['node_id'],int):
                        
                        message_id = "get_node_ip_addresses_" + str(self.persistent_data['nodez'][str(thing_id)]['node_id'])
                        
                        message = {
                                    "message_id": message_id,
                                    "command": "get_node_ip_addresses",
                                    "args": {
                                        "node_id": int(self.persistent_data['nodez'][str(thing_id)]['node_id'])
                                    }
                                }

                        if self.DEBUG:
                            self.s_print("\nget_node_ips: sending message to Matter.server: \n", json.dumps(message,indent=4))

                        json_message = json.dumps(message)
                        self.ws.send(json_message)
                        time.sleep(0.1)
                    else:
                        if self.DEBUG:
                            self.s_print("\nERROR: get_node_ips: invalid node_id for thing_id: ", thing_id)
                
        except Exception as ex:
            if self.DEBUG:
                print("caught error in get_node_ips: ", ex)


    def get_node_ip(self, node_id):
        if self.DEBUG:
            self.s_print("in get_node_ip.  node_id: ", node_id)
        try:
            
            if str(node_id).isdigit() and self.matter_client_connected and self.matter_running and 'nodez' in self.persistent_data:
                for thing_id in self.persistent_data['nodez']:
                    if 'node_id' in self.persistent_data['nodez'][str(thing_id)] and isinstance(self.persistent_data['nodez'][str(thing_id)]['node_id'],int) and str(self.persistent_data['nodez'][str(thing_id)]['node_id']) == str(node_id):
                        
                        message_id = "get_node_ip_addresses_" + str(self.persistent_data['nodez'][str(thing_id)]['node_id'])
                        
                        message = {
                                    "message_id": message_id,
                                    "command": "get_node_ip_addresses",
                                    "args": {
                                        "node_id": int(self.persistent_data['nodez'][str(thing_id)]['node_id'])
                                    }
                                }

                        if self.DEBUG:
                            self.s_print("\nget_node_ip: sending message to Matter.server: \n", json.dumps(message,indent=4))

                        json_message = json.dumps(message)
                        self.ws.send(json_message)

                        break
        except Exception as ex:
            if self.DEBUG:
                print("caught error in get_node_ip: ", ex)





    #last_update_check
    def check_for_node_updates(self):
        if self.DEBUG:
            self.s_print("in check_for_node_updates")

        try:
            
            if self.matter_client_connected and self.matter_running and 'nodez' in self.persistent_data:
                for thing_id in self.persistent_data['nodez']:
                    if 'node_id' in self.persistent_data['nodez'][str(thing_id)] and isinstance(self.persistent_data['nodez'][str(thing_id)]['node_id'],int):
                        
                        message_id = "check_node_update_" + str(self.persistent_data['nodez'][str(thing_id)]['node_id'])
                        
                        message = {
                                    "message_id": message_id,
                                    "command": "check_node_update",
                                    "args": {
                                        "node_id": int(self.persistent_data['nodez'][str(thing_id)]['node_id'])
                                    }
                                }

                        if self.DEBUG:
                            self.s_print("\ncheck_for_node_updates: sending message to Matter.server: \n", json.dumps(message,indent=4))

                        json_message = json.dumps(message)
                        self.ws.send(json_message)
                        time.sleep(2)
                    else:
                        if self.DEBUG:
                            self.s_print("\nERROR: check_for_node_updates: invalid node_id for thing_id: ", thing_id)
                
        except Exception as ex:
            print("caught error in check_for_node_updates: ", ex)
        

    def update_node(self,node_id):
        if self.DEBUG:
            print("\nin UPDATE_NODE:  node_id: ", node_id, "\n")
        
        try:
            if isinstance(node_id,(str,int)):
                if self.matter_client_connected and self.matter_running and 'nodez' in self.persistent_data:
                    message = {
                                "message_id": "update_node_" + str(node_id),
                                "command": "update_node",
                                "args": {
                                    "node_id": int(node_id)
                                }
                            }

                    if self.DEBUG:
                        self.s_print("update_node: sending message to Matter.server: \n", json.dumps(message,indent=4))

                    json_message = json.dumps(message)
                    self.ws.send(json_message)

        except Exception as ex:
            self.s_print("caught error in update_node: " + str(ex))
        

    
    def check_onboarding_state(self):
        if isinstance(self.persistent_data['vendor_id'],str) and len(self.persistent_data['vendor_id']) == 4:
            self.missing_vendor_id = False
            if isinstance(self.persistent_data['matter_network_interface'],str) and len(self.persistent_data['matter_network_interface']) > 1:
                if self.persistent_data['onboarding_complete'] == False:
                    self.should_save_persistent = True
                self.persistent_data['onboarding_complete'] = True
            else:
                self.persistent_data['onboarding_complete'] = False
        else:
            self.persistent_data['onboarding_complete'] = False
            self.missing_vendor_id = True


            
              



    # Reset Thread
    def reset_thread(self):
        if self.thread_running:
            self.run_ot_ctl_command('thread stop')
            self.run_ot_ctl_command('ifconfig down')
        self.run_ot_ctl_command('factoryreset')
        
        self.really_stop_otbr()
        self.thread_dataset_loaded = False
        
        self.persistent_data['thread_dataset'] = ''
        os.system('rm -rf ' + str(self.data_thread_dir_path) + '/*')
        self.find_thread_radio()
        self.should_create_thread_mesh = True

        


    # Reset Matter
    def reset_matter(self):
        if self.DEBUG:
            self.s_print("in reset_matter")

        if self.server_process and self.server_process.poll() == None:
            if self.DEBUG:
                self.s_print("reset_matter: doing .terminate() of matter_server")
            self.server_process.terminate()
            time.sleep(.5)
        if self.server_process and self.server_process.poll() == None:
            if self.DEBUG:
                self.s_print("reset_matter: resorting to .kill() of matter_server")
            self.server_process.kill()
            time.sleep(.2)
        if self.server_process and self.server_process.poll() == None:
            if self.DEBUG:
                self.s_print("reset_matter: doing pkill of matter_server")
            os.system('sudo pkill -f matter_server.server')

        try:
            run_loop = asyncio.get_running_loop()
            run_loop.stop()
        except Exception as ex:
            self.s_print("reset_matter: error getting asyncio loop: " + str(ex))

        self.really_stop_otbr()

        #self.do_not_save_persistent_data = True

        if os.path.isdir(self.hasdata_backup_dir_path):
            if self.DEBUG:
                print("deleting a previous matter reset backup first")
            os.system('rm -rf ' + str(self.hasdata_backup_dir_path))
        os.system('mkdir -p ' + str(self.hasdata_backup_dir_path))
        #os.system('mv ' + str() + '/* /home/pi/.webthings/hasdata_backup/')
        os.system('mv ' + str(os.path.join(self.data_dir_path,"*")) + ' ' + str(self.hasdata_backup_dir_path) + '/') # TODO: is the slash necessary?
        #os.system('rm -rf ' + str(os.path.join(self.data_dir_path,"*")))
        os.system("find " + str(self.data_dir_path) + " -not -name " + str(self.hasdata_backup_dir_path) + " -delete") # -type f -not -name 'persistence.json'
        self.persistent_data['nodez'] = {}
        #self.persistent_data['thread_dataset'] = ''
        self.persistent_data['last_certificates_download_time'] = 0
        self.save_persistent_data()

        if self.DEBUG:
            print("\nreset_matter: ls /data/: \n", run_command('ls ' + str(self.data_dir_path)))
            self.s_print("\nreset_matter: done\n")

        #time.sleep(1)

        #try:
        #    self.close_proxy()
        #except Exception as ex:
        #    self.s_print("reset_matter: caught error calling self.close_proxy(): " + str(ex))
        

        """
        ota_dir = os.path.join(self.hasdata_dir_path,"ota")
        if os.path.isdir(ota_dir):
            if self.DEBUG:
                self.s_print("reset_matter: deleting ota dir")
            os.system('rm -rf ' + str(ota_dir))

        credentials_dir = os.path.join(self.hasdata_dir_path,"credentials")
        if os.path.isdir(credentials_dir):
            if self.DEBUG:
                self.s_print("reset_matter: deleting credential dir")
            os.system('rm -rf ' + str(credentials_dir))

        certificates_dir = os.path.join(self.hasdata_dir_path,"certificates")
        if os.path.isdir(certificates_dir):
            if self.DEBUG:
                self.s_print("reset_matter: deleting certificates dir")
            os.system('rm -rf ' + str(certificates_dir))

        fff1_dir = os.path.join(self.hasdata_dir_path,"server-1-fff1")
        if os.path.isdir(fff1_dir):
            if self.DEBUG:
                self.s_print("reset_matter: deleting server-1-fff1 dir")
            os.system('rm -rf ' + str(fff1_dir))

        vendors_dir = os.path.join(self.hasdata_dir_path,"vendors")
        if os.path.isdir(vendors_dir):
            if self.DEBUG:
                self.s_print("reset_matter: deleting vendors dir")
            os.system('rm -rf ' + str(vendors_dir))
        """





    #
    # The methods below are called by the controller
    #

    def start_pairing(self, timeout):
        """
        Start the pairing process. This starts when the user presses the + button on the things page.

        timeout -- Timeout in seconds at which to quit pairing
        """
        pass
        #if self.DEBUG:
        #    self.s_print("in start_pairing. Timeout: " + str(timeout))


    def cancel_pairing(self):
        """ Happens when the user cancels the pairing process."""
        # This happens when the user cancels the pairing process, or if it times out.
        pass
        #if self.DEBUG:
        #    self.s_print("in cancel_pairing")


    def unload(self):
        """ Shuts down the addon """
        if self.DEBUG:
            self.s_print("Stopping matter addon")

        self.running = False

        if self.server_process and self.server_process.poll() == None:
            if self.DEBUG:
                self.s_print("doing .terminate() of matter_server")
            self.server_process.terminate()
            time.sleep(.5)
        if self.server_process and self.server_process.poll() == None:
            if self.DEBUG:
                self.s_print("unload: resorting to .kill() of matter_server")
            self.server_process.kill()
            time.sleep(.2)
        if self.server_process and self.server_process.poll() == None:
            if self.DEBUG:
                self.s_print("unload: doing pkill of matter_server")
            os.system('sudo pkill -f matter_server.server')

        try:
            run_loop = asyncio.get_running_loop()
            run_loop.stop()
        except Exception as ex:
            self.s_print("Error getting asyncio loop: " + str(ex))

        self.really_stop_otbr()

        #if self.client != None:
        #    self.client.stop()



        # loop = asyncio.get_event_loop()
        # loop.stop()


        #try:
        #    self.devices['matter-thing'].properties['status'].update( "Bye")
        #except Exception as ex:
        #    self.s_print("Error setting status on thing: " + str(ex))

        # Tell the controller to show the device as disconnected. This isn't really necessary, as the controller will do this automatically.
        #self.devices['matter-thing'].connected_notify(False)

        # A final chance to save the data.
        self.save_persistent_data()

        #time.sleep(.1)
        #if self.server_process != None:
            #self.server.stop()
        #    time.sleep(1)
        #    os.system("pkill -f 'matter_server.server' --signal SIGKILL")
        #    os.system("pkill -f 'matter_server.server' --signal SIGKILL")

        # does it reach this?
        if self.DEBUG:
            self.s_print("matter adapter: goodbye\n\n")
        return True



    def remove_thing(self, device_id):
        """ Happens when the user deletes the thing."""
        if self.DEBUG:
            self.s_print("user deleted the thing")
        try:
            # We don't have to delete the thing in the addon, but we can.
            obj = self.get_device(device_id)
            if obj:
                self.handle_device_removed(obj) # Remove from device dictionary
                if self.DEBUG:
                    self.s_print("User removed thing")
            else:
                if self.DEBUG:
                    self.s_print("could not find thing to remove")

            if 'nodez' in self.persistent_data and device_id in self.persistent_data['nodez']:
                del self.persistent_data['nodez'][device_id]
                self.should_save = True

            self.remove_node(device_id.replace('matter-',''))

        except Exception as ex:
            if self.DEBUG:
                self.s_print("caught error in remove thing: " + str(ex))




    #
    # This saves the persistent_data dictionary to a file
    #

    def save_persistent_data(self):
        #if self.do_not_save_persistent_data == True:
        #    if self.DEBUG:
        #        self.s_print("SKIPPING Saving to persistence data store")
        #    return

        if self.DEBUG:
            self.s_print("Saving to persistence data store")

        try:
            if not os.path.isfile(self.persistence_file_path):
                open(self.persistence_file_path, 'a').close()
                if self.DEBUG:
                    self.s_print("Created an empty persistence file")
            else:
                if self.DEBUG:
                    self.s_print("Persistence file existed. Will try to save to it.")

            out_file = open(str(self.persistence_file_path), "w")
            json.dump(self.persistent_data, out_file, indent = 4)
            out_file.close()
            if self.DEBUG:
                self.s_print("persistent data saved to: " + str(self.persistence_file_path))
            return True

        except Exception as ex:
            if self.DEBUG:
                self.s_print("Error: could not store data in persistent store: " + str(ex) )

        return False



    def remove_node(self, node_id):
        if self.DEBUG:
            self.s_print("in remove_node. node_id: " + str(node_id))

        if self.matter_client_connected and self.matter_running == False:
            if self.DEBUG:
                self.s_print("remove_node: ERROR, client is not connected") 
            return False

        self.get_nodes(True)
        time.sleep(3)
        thing_id = 'matter-' + str(node_id)

        if self.DEBUG:
            self.s_print("remove_node: Node seems to exist, will delete it")
            
        message = {
                "message_id": "remove_node_" + str(node_id),
                "command": "remove_node",
                "args": {
                        "node_id": int(node_id)
                        }
                }
        json_message = json.dumps(message)
        self.ws.send(json_message)

        #if thing_id in self.nodes:
            

        #else:
        #    if self.DEBUG:
        #        self.s_print("\nERROR, remove_node: node doesn't seem to exist (already deleted?). Skipping delete")
        #    self.device_was_deleted = True # pretend it was just deleted


        # TODO: Also remove thing? Though in theory this is already being done
        # TODO: Remove logs?
        # TODO: Assuming that the matter server can also remove devices from thread



        return True


    def run_chip_tool_command(self, cmd, timeout_seconds=10):
        try:
            if not os.path.isfile(self.chip_tool_path):
                self.s_print("\nERROR, run_chip_tool_command: chip_tool is missing: ", self.chip_tool_path)
                return None
            my_env = get_env()

            my_env["LD_LIBRARY_PATH"] = '{}'.format(self.addon_thread_dir_path)

            #data_path = '/data'
            #my_env["TMPDIR"] = '{}'.format(self.data_dir_path)
            #my_env["TMPDIR"] = '{}'.format(data_path)
            my_env["TMPDIR"] = '{}'.format(self.hasdata_dir_path)


            command = str(self.chip_tool_path) + ' ' + str(cmd) # export LD_LIBRARY_PATH=' + str(self.addon_thread_dir_path) + ' ' +
            if self.DEBUG:
                self.s_print("run_chip_tool_command: \n" + str(command))
            #op = subprocess.run('sudo ' + str(self.ot_ctl_path) + ' ' + str(cmd) + ' --storage-directory ' + str(self.data_thread_dir_path), timeout=timeout_seconds, env=my_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
            op = subprocess.run(command, timeout=timeout_seconds, env=my_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)

            if op.returncode == 0:
                return str(op.stdout).rstrip()
            else:
                if op.stderr:
                    return str(op.stderr).rstrip()

        except Exception as ex:
            self.s_print("caught error in run_chip_tool_command: "  + str(ex))
            return None


    def run_ot_ctl_command(self, cmd, timeout_seconds=30):
        try:
            if not os.path.isfile(self.ot_ctl_path):
                self.s_print("\nERROR, run_ot_ctl_command: ot-ctl is missing: ", self.ot_ctl_path)
                return None
            my_env = get_env()

            my_env["LD_LIBRARY_PATH"] = '{}'.format(self.addon_thread_dir_path)

            data_path = '/data'
            my_env["TMPDIR"] = '{}'.format(self.data_thread_dir_path)
            #my_env["TMPDIR"] = '{}'.format(data_path)

            command = 'sudo ' + str(self.ot_ctl_path) + ' ' + str(cmd)
            if ('dataset' in cmd or cmd == 'factoryreset') and cmd != 'dataset': # and not 'dataset set active' in cmd:
                #command = command + ' --storage-directory ' + str(data_path)
                command = command + ' --storage-directory ' + str(self.data_thread_dir_path)

            if self.DEBUG:
                self.s_print("run_ot_ctl_command: \n" + str(command))
            #op = subprocess.run('sudo ' + str(self.ot_ctl_path) + ' ' + str(cmd) + ' --storage-directory ' + str(self.data_thread_dir_path), timeout=timeout_seconds, env=my_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
            op = subprocess.run(command, timeout=timeout_seconds, env=my_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)

            if op.returncode == 0:
                return str(op.stdout).rstrip()
            else:
                if op.stderr:
                    return str(op.stderr).rstrip()

        except Exception as ex:
            self.s_print("caught error in run_ot_ctl_command: " + str(ex))
            return None

    # Loop over all the items in the list, which is stored inside the adapter instance.
    """
    def delete_item(self,name):
        self.s_print("in delete_item. Name: " + str(name))
        for i in range(len(self.items_list)):
            if self.items_list[i]['name'] == name:
                # Found it
                del self.items_list[i]
                self.s_print("deleted item from list")
                return True

        # If we end up there, the name wasn't found in the list
        return False
    """


"""
def run_command(cmd, timeout_seconds=30):
    try:
        p = subprocess.run(cmd, timeout=timeout_seconds, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)

        if p.returncode == 0:
            return str(p.stdout).rstrip()
        else:
            if p.stderr:
                return str(p.stderr).rstrip()

    except Exception as ex:
        print("caught error in run_command: "  + str(ex))
        return None
"""
