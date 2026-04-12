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
"""



import os
import re
import sys
# This helps the addon find python libraries it comes with, which are stored in the "lib" folder. The "package.sh" file will download Python libraries that are mentioned in requirements.txt and place them there.
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

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
DEFAULT_STORAGE_PATH = '/home/pi/.webthings/hasdata' #os.path.join(Path.home(), ".matter_server")

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



        print(run_command('printenv'))

        self.s_print_lock = Lock()

        # set up some variables
        self.DEBUG = False
        self.DEBUG2 = False

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
        #self.client = None
        #self.unsubscribe = None

        self.port = 5580
        self.message_counter = 0
        self.client_connected = False

        self.vendor_id = ""

        self.discovered = []
        self.nodes = []

        self.raw_mdns = ''
        self.last_get_nodes_timestamp = 0

        #self.switch_events = ['Switch latched','Initial press','Long press','Short release','Long release','Multi press ongoing','Multi press complete']

        self.certificates_updated = False
        self.busy_updating_certificates = False
        self.last_certificates_download_time = 0
        self.time_between_certificate_downloads = 14 * 86400 # 14 days

        self.busy_discovering = False
        self.pairing_failed = False
        self.busy_pairing = False
        self.last_pairing_start_time = 0
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


        # THREAD / OTBR
        self.otbr_thread = None
        self.found_thread_radio_again = False
        self.found_new_thread_radio = False
        self.found_a_thread_radio_once = False
        self.thread_radio_went_missing = False
        self.thread_radio_is_alive_count = 0 # how many spinel messages have been received
        self.last_thread_radio_is_alive_timestamp = 0

        self.otbr_starting_timestamp = None
        self.otbr_stopping_timestamp = 0
        self.last_time_otbr_started = time.time()
        self.should_start_otbr = True
        self.otbr_started = False # This is the first stage, done by otbr-agent

        self.thread_set_active = False # This is the second stage, managed by ot-ctl
        self.informed_matter_server_about_thread = False
        self.thread_running = False # becomes true when Thread is completely up
        self.thread_error = ''
        self.otbr_agent_process = None
        self.otbr_stdout_messages = []
        self.thread_channel = 26
        self.thread_dataset = ''
        self.turn_wifi_back_on_at = 0
        self.extension_cable_recommended = False
        self.last_time_otbr_restarted = 0
        self.serial_before = '' # used to detect newly plugged in USB sticks by comparing before and after of lsusb
        self.last_received_server_info = None
        self.noise_counter = 0
        self.previous_noise_counter = 0 # used to count noise per time unit
        self.noise_delta = 0 # hot many instances of noise were counted during 5 seconds

        self.thread_diagnostics = {}

        self.enums_lookup = get_enums_lookup()
        self.events_lookup = get_events_lookup()

        self.completed_command_clusters = [] # Will be filled with cluster_id's that have already been lookup up through get_commands_for_cluster_id
        self.commands_lookup = {} # will be filled as needed by calling get_commands_for_cluster_id(). The first key is the cluster_name

        # Matter time sync
        self.matter_devices_with_time_sync = []
        self.time_sync_interval = 3600 # every hour sync the clocks
        self.last_time_sync_time = time.time() #int(str(run_command('date +%s')).strip().rstrip())
        self.timezone_name = str(run_command('date +%Z')).strip().rstrip()


        #print("self.user_profile: ", self.user_profile)
        #print("")
        #print("self.preferences: ", self.preferences)
        #print("")




        # Hotspot
        self.use_hotspot = True
        self.hotspot_ssid = ""
        self.hotspot_password = ""


        # WiFi
        self.wifi_ssid = ""
        self.wifi_password = ""
        self.wifi_set = False

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
        self.data_path = os.path.join(self.user_profile['dataDir'], self.addon_id)


        # Create the data directory if it doesn't exist yet
        if not os.path.isdir(self.data_path):
            #print("making missing data directory")
            os.system('mkdir -p ' + str(self.data_path))

        self.persistence_file_path = os.path.join(self.data_path, 'persistence.json') # dataDir points to the directory where the addons are allowed to store their data (/home/pi/.webthings/data)
        self.hasdata_dir_path = os.path.join(self.user_profile['baseDir'],'hasdata')
        self.chip_factory_ini_file_path = os.path.join(self.hasdata_dir_path,'chip_factory.ini')
        self.data_chip_factory_ini_file_path = os.path.join(self.data_path, 'chip_factory.ini')
        #self.certs_dir_path = os.path.join(self.data_path, 'paa-root-certs')

        self.matter_server_base_path = os.path.join(self.addon_path,'matterjs-server')
        #self.matter_serverjs_start_path = os.path.join(self.matter_server_base_path,'packages','matter-server','dist','esm','MatterServer.js') # node_modules/matter-server/dist/esm
        self.matter_serverjs_start_path = os.path.join(self.matter_server_base_path,'node_modules','matter-server','dist','esm','MatterServer.js')



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
        self.data_thread_dir_path = os.path.join(self.data_path,'thread')
        if not os.path.isdir(str(self.data_thread_dir_path)):
            #print("creating missing data/thread dir: ", self.data_thread_dir_path)
            os.system('mkdir -p ' + str(self.data_thread_dir_path))

        os.chdir(self.data_path)

        pwd = str(run_command('pwd'))
        pwd = pwd.rstrip()

        self.certs_dir_path = os.path.join(self.data_path,'credentials','development','paa-root-certs')
        self.certs_dir_path = pwd + '/credentials/development/paa-root-certs'
        #print("self.certs_dir_path: " + str(self.certs_dir_path))


        self.certs_downloader_path = os.path.join(self.addon_path, 'download_certificates.py')

        # deprecated, as Candle 3.0 has hotspot functionality built-in
        self.hotspot_addon_path = os.path.join(self.user_profile['addonsDir'], 'hotspot')
        self.hotspot_persistence_path = os.path.join(self.user_profile['dataDir'], 'hotspot', 'persistence.json')




        self.persistent_data = {}


        # Get persistent data
        try:
            with open(self.persistence_file_path) as f:
                self.persistent_data = json.load(f)
                if self.DEBUG:
                    self.s_print('self.persistent_data was loaded from file: ' + str(self.persistent_data))

        except:
            if self.DEBUG:
                self.s_print("Could not load persistent data (if you just installed the add-on then this is normal)")




        if 'thread_dataset' in self.persistent_data and isinstance(self.persistent_data['thread_dataset'], str) and len(self.persistent_data['thread_dataset']) > 10:
            self.thread_dataset = self.persistent_data['thread_dataset']

        if not 'thing_index' in self.persistent_data:
            self.persistent_data['thing_index'] = 50
            self.should_save = True


        # LOAD CONFIG
        try:
            self.add_from_config()
        except Exception as ex:
            self.s_print("Error loading config: " + str(ex))

        if self.DEBUG:
            self.s_print("PWD:" + str(pwd))
            self.s_print("initial self.thread_dataset: ", self.thread_dataset)
            self.s_print("\nself.enums_lookup: ", self.enums_lookup)
            self.s_print("\nself.events_lookup: ", self.events_lookup)

        # Override vendor ID
        if len(self.vendor_id) > 2 and len(self.vendor_id) < 7:
            if os.path.exists(self.chip_factory_ini_file_path):

                if os.path.exists(self.chip_factory_ini_file_path):
                    #if self.DEBUG:
                    #    self.s_print("\nWARNING, replacing vendor-id in chip_factory.ini with: " + str(self.vendor_id) + ", in: " + str(self.chip_factory_ini_file_path))
                    os.system("sed -i 's/.*vendor-id=*.*/vendor-id=" + str(self.vendor_id) + "/' " + str(self.chip_factory_ini_file_path))

                if os.path.isfile('/data/chip_factory.ini'):
                    #if self.DEBUG:
                    #    self.s_print("\nWARNING, replacing vendor-id in chip_factory.ini with: " + str(self.vendor_id) + ", in: /boot/chip_factory.ini")
                    os.system("sed -i 's/.*vendor-id=*.*/vendor-id=" + str(self.vendor_id) + "/' /data/chip_factory.ini")

                if os.path.exists(self.data_chip_factory_ini_file_path):
                    #if self.DEBUG:
                    #    self.s_print("\nWARNING, replacing vendor-id in chip_factory.ini with: " + str(self.vendor_id) + ", in: " + str(self.data_chip_factory_ini_file_path))
                    os.system("sed -i 's/.*vendor-id=*.*/vendor-id=" + str(self.vendor_id) + "/' " + str(self.data_chip_factory_ini_file_path))

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


        #print("PERSISTENT DATA")
        #print(json.dumps(self.persistent_data, None,4))
        #print(json.dumps(self.persistent_data))

        if self.persistent_data['wifi_ssid'] != "" and self.persistent_data['wifi_password'] != "":
            self.wifi_ssid = self.persistent_data['wifi_ssid']
            self.wifi_password = self.persistent_data['wifi_password']

        if 'last_certificates_download_time' not in self.persistent_data:
            self.persistent_data['last_certificates_download_time'] = 0
        elif self.persistent_data['last_certificates_download_time'] > time.time() - self.time_between_certificate_downloads:
            self.certificates_updated = True

        if 'thread_radio_serial_port' not in self.persistent_data:
            self.persistent_data['thread_radio_serial_port'] = None



        # Allow the use_hotspot setting to override the wifi credentials
        # TODO: check if the hotspot addon is actually running?
        self.hotspot_addon_installed = False
        if os.path.isdir(self.hotspot_addon_path):
            self.hotspot_addon_installed = True


        if not os.path.exists('/boot/firmware/candle_hotspot.txt'):
            self.use_hotspot = False

        #print("self.nmcli_installed: ", self.nmcli_installed)

        if self.use_hotspot and (self.nmcli_installed or self.hotspot_addon_installed):
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
        if not os.path.isdir(self.data_path):
            if self.DEBUG:
                self.s_print("creating matter_server storage path: " + str(self.data_path))
            os.mkdir(self.data_path)

        if not os.path.isdir(self.certs_dir_path):
            if self.DEBUG:
                self.s_print("making certificates directory")
            os.system('mkdir -p ' + self.certs_dir_path)

        # /data
        if not os.path.exists("/data"):
            if self.DEBUG:
                self.s_print("Error! Could not find /data, which the server will be looking for")
            #while self.running:
            #    time.sleep(1)


        # Start clock thread
        if self.DEBUG:
            self.s_print("Init: starting the clock thread")
        try:
            self.ct = threading.Thread(target=self.clock)
            self.ct.daemon = True
            self.ct.start()
        except Exception as ex:
            if self.DEBUG:
                self.s_print("Error starting the clock thread: " + str(ex))

        try:
            self.matter_servers_thread = threading.Thread(target=self.start_servers)
            self.matter_servers_thread.daemon = True
            self.matter_servers_thread.start()
        except Exception as ex:
            if self.DEBUG:
                self.s_print("Error starting the matter servers thread: " + str(ex))


        # Init matter server
        #self.server = MatterServer(
        #    self.data_path, DEFAULT_VENDOR_ID, DEFAULT_FABRIC_ID, int(self.port)
        #)

        #self.start_servers()

        pwd = run_command('pwd')
        if self.DEBUG:
            self.s_print("PWD after chdir: " + str(pwd))
            print("init done\n")

        #time.sleep(60)
        #self.ready = True

        #self.wifi_congestion_data = self.wifi_congestion_scan()






    def  start_servers(self):
        if self.running:
            # Download the latest Matter certificates
            #self.download_certs()


            # If a radio is found, then it also starts OTBR
            #if self.DEBUG:
            #    self.s_print("start_servers: calling find_thread_radio")
            #self.find_thread_radio()

            # Start matter.server client
            if self.DEBUG:
                self.s_print("\nstart_servers: starting the matter.server client thread")
            try:
                self.otbr_t = threading.Thread(target=self.otbr_loop)
                self.otbr_t.daemon = True
                self.otbr_t.start()
            except Exception as ex:
                if self.DEBUG:
                    self.s_print("Error starting the OTBR loop thread: " + str(ex))
                    self.s_print(traceback.format_exc())

            time.sleep(2)

            if self.DEBUG:
                print("is self.otbr_starting_timestamp None or a number?: ", self.otbr_starting_timestamp)


            # if it's starting, then wait until the thread network has fully started
            if self.otbr_starting_timestamp != None:
                while self.running and self.thread_running == False:
                    if self.DEBUG:
                        self.s_print("start_servers: waiting for self.thread_running to be True.  len(self.otbr_stdout_messages): ", len(self.otbr_stdout_messages))

                    time.sleep(1)
                    if self.otbr_starting_timestamp == None:
                        break
                    if self.otbr_starting_timestamp != None and time.time() - self.otbr_starting_timestamp > 90:
                        break


            # Ensure there's a bridge
            #self.ensure_bridge()




            # Start the Matter.server
            if self.DEBUG:
                self.s_print("\nstart_servers: calling start_matter_server")
            self.start_matter_server()
            if self.DEBUG:
                self.s_print("start_servers: beyond start_matter_server")


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


            while self.running:
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
                if self.DEBUG:
                    self.s_print("Debugging enabled")

            if self.DEBUG:
                self.s_print("matter adapter config: ", str(config)) # Print the entire config data

            if "Do not use Hotspot as WiFi network for devices" in config:
                self.use_hotspot = not bool(config["Do not use Hotspot as WiFi network for devices"])
                if self.DEBUG:
                    self.s_print("Use hotspot preference was in settings: " + str(self.use_hotspot))

            if "Vendor ID" in config:
                if len(config["Vendor ID"]) > 2:
                    self.vendor_id = str(config["Vendor ID"])
                    if self.DEBUG:
                        self.s_print("Vendor ID override was in settings: " + str(self.vendor_id))

            if 'Brightness transition duration' in config:
                self.brightness_transition_time = int(config["Brightness transition duration"])
                if self.DEBUG:
                    self.s_print("Brightness transition preference was in settings: " + str(self.brightness_transition_time))

            if 'Thread dataset' in config:
                raw_dataset = str(config["Thread dataset"]).strip().rstrip()
                if len(raw_dataset) > 10:
                    self.thread_dataset = raw_dataset
                    self.persistent_data['thread_dataset'] = raw_dataset
                    if self.DEBUG:
                        self.s_print("Thread dataset preference was in settings, and long enough.  self.thread_dataset is now: " + str(self.thread_dataset))
                else:
                    if self.DEBUG:
                        self.s_print("Thread dataset preference was in settings, but not long enough: -->" + str(raw_dataset) + "<--")

            if 'Thread channel' in config:
                self.thread_channel = int(config["Thread channel"])
                if self.DEBUG:
                    self.s_print("Thread channel preference was in settings: " + str(self.thread_channel))

            if 'Matter server type' in config:
                self.matter_server_type =  bool(config["Matter server type"])
                if self.DEBUG:
                    self.s_print("Matter server type preference was in settings: " + str(self.matter_server_type))

        except Exception as ex:
            self.s_print("caught error in add_from_config: " + str(ex))






    # If OTBR starts, then it (should) block this loop
    def otbr_loop(self):

        while self.running:
            #if self.DEBUG:
                #self.s_print("otbr_loop: loop start.  self.should_start_otbr, self.otbr_started, self.found_thread_radio_again: ", self.should_start_otbr,self.otbr_started, self.found_thread_radio_again)
            #    self.s_print("otbr_loop: loop start.")

            self.find_thread_radio()

            #if self.DEBUG:
            #    self.s_print("otbr_loop:")
            #    self.s_print("- self.otbr_started: ", self.otbr_started)
            #    self.s_print("- self.thread_radio_went_missing: ", self.thread_radio_went_missing)
            #    self.s_print("- self.found_thread_radio_again: ", self.found_thread_radio_again)
            #    self.s_print("- self.found_new_thread_radio: ", self.found_new_thread_radio)
            #    self.s_print("- self.thread_set_active: ", self.thread_set_active)
            #    self.s_print("- self.last_time_otbr_restarted: ", self.last_time_otbr_restarted)

            if self.should_start_otbr == True and self.otbr_started == False and self.otbr_starting_timestamp == None and self.last_time_otbr_restarted < time.time() - 60 and (self.found_thread_radio_again or self.found_new_thread_radio):
                if self.DEBUG:
                    self.s_print("otbr_loop: conditions are perfect. calling start_otbr")
                self.last_time_otbr_restarted = time.time()
                self.start_otbr()

            time.sleep(5)

        if self.DEBUG:
            self.s_print("otbr_loop: beyond while loop. self.running should be false: ", self.running)





    # Get real tty port from:
    # ls -la /dev/serial/by-id/usb-*

    def find_thread_radio(self):
        found_thread_radio_again = False
        found_new_thread_radio = False
        if os.path.isdir('/dev/serial/by-id'):
            serial_by_id_output = run_command('ls /dev/serial/by-id')
            if isinstance(serial_by_id_output,str) and len(str(serial_by_id_output)) > 5:

                if 'No such file or directory' in str(serial_by_id_output):
                    if self.DEBUG:
                        print("ERROR, find_thread_radio: no /dev/serial/by-id!")
                    return False
            
                if self.serial_before:
                    for line in str(serial_by_id_output).splitlines():
                        line = str(line).strip().rstrip()
                        if not line in self.serial_before:
                            self.persistent_data['thread_radio_serial_port'] = line
                            if self.DEBUG:
                                self.s_print("Found a new thread radio: ", line)
                            found_new_thread_radio = True
                            self.serial_before = ''
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

        self.found_thread_radio_again = found_thread_radio_again
        self.found_new_thread_radio = found_new_thread_radio

        if self.found_thread_radio_again or self.found_new_thread_radio:
            self.found_a_thread_radio_once = True
            if self.otbr_started == False and self.otbr_starting_timestamp == None:
                if self.DEBUG:
                    print("find_thread_radio: SUCCESS, setting should_start_otbr to True")
                self.should_start_otbr = True

        else:
            #if self.DEBUG:
            #    self.s_print("\nNO THREAD RADIO FOUND\n")
            if self.found_a_thread_radio_once:
                self.thread_radio_went_missing = True






    def add_otbr_iptables(self):

        current_iptables = run_command('sudo iptables -S')
        if isinstance(current_iptables,str):
            if not 'wpan0' in current_iptables:
                if self.DEBUG:
                    self.s_print("add_otbr_iptables: adding wpan0 masquerade iptables")

                # OpenThread NAT64
                os.system('sudo iptables -t mangle -A PREROUTING -i wpan0 -j MARK --set-mark 0x1001')
                os.system('sudo iptables -t nat -A POSTROUTING -m mark --mark 0x1001 -j MASQUERADE')
                os.system('sudo iptables -t filter -A FORWARD -o uap0 -j ACCEPT')
                os.system('sudo iptables -t filter -A FORWARD -i uap0 -j ACCEPT')









    #
    #  START OTBR
    #



    def start_otbr(self):
        if self.DEBUG:
            self.s_print("in start_otbr")
        self.otbr_starting_timestamp = time.time()
#       #self.otbr_thread = threading.Thread(target=self.really_start_otbr)
#       #self.otbr_thread.daemon = True
#       #self.otbr_thread.start()
#       self.really_start_otbr()
#
#   def really_start_otbr(self):
        if self.DEBUG:
            self.s_print("in really_start_otbr")
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


                self.thread_radio_url = thread_radio_url

                self.thread_backbone_interface = 'wlan0'
                if os.path.isfile('/boot/firmware/candle_hotspot.txt'):
                    self.thread_backbone_interface = 'uap0'

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
                os.system('sudo sysctl "net.ipv6.conf.all.disable_ipv6=0 net.ipv4.conf.all.forwarding=1 net.ipv6.conf.all.forwarding=1 net.ipv6.conf.all.accept_ra=2 net.ipv6.conf.all.accept_ra_rt_info_max_plen=64 net.ipv6.conf.uap0.accept_ra=2 net.ipv6.conf.wpan0.accept_ra=2"')

                os.system('sudo sysctl -w net.ipv6.conf.wlan0.accept_ra=2')
                os.system('sudo sysctl -w net.ipv6.conf.uap0.accept_ra=2')
                os.system('sudo sysctl -w net.ipv6.conf.eth0.accept_ra=2')

                # ,"--vendor-name","CandleSmartHome","--model-name","CandleController", # unrecognized option '--vendor-name'
                agent_command_array = ["sudo",str(self.otbr_agent_path),"--data-path",str(self.data_thread_dir_path),"--syslog-disable","--debug-level","7","--thread-ifname","wpan0","-B", str(self.thread_backbone_interface), str(self.thread_radio_url)]


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
                except Exception as ex:
                    if self.DEBUG:
                        self.s_print("caught error checking if otbr process is running: ", ex)


                # sudo tcpdump -i any 'udp port 5353 and (host 224.0.0.251 or host ff02::fb)'





                if self.otbr_agent_process:
                    if self.DEBUG:
                        self.s_print("self.otbr_agent_process has been created")

                    if self.otbr_agent_process.poll() == None:
                        if self.DEBUG:
                            print("otbr_agent_process is running OK")


                        while self.otbr_agent_process != None and self.otbr_agent_process.poll() == None:
                            time.sleep(1)
                            try:
                                for i in range(1000):
                                    msg = self.otbr_agent_process.stdout.readline()
                                    decoded_message = str(msg.decode()).strip().rstrip()
                                    # note to self: do not putf a print statement here
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
            print("in parse_otbr_messages.  len(self.otbr_stdout_messages): ", len(self.otbr_stdout_messages))
        if self.DEBUG and self.thread_radio_is_alive_count < 100:
            self.s_print("\nclock: total otbr_stdout_messages length: ", len(self.otbr_stdout_messages))

        wpan_check = str(run_command('ip link show | grep wpan0'))
        if 'state ' in wpan_check:
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
                    self.s_print("parse_otbr_messages: self.thread_radio_is_alive_count: ", self.thread_radio_is_alive_count)

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
                self.start_thread_mesh()

            elif '... noise:-128' in otbr_message:
                #if self.DEBUG:
                #    self.s_print("Thread radio is receiving a lot of noise?")
                self.noise_counter += 1
                #self.thread_error = 'The thread radio is receiving a lot of noise. You may need to use a USB extension cable for your Thread dongle'
                #self.extension_cable_recommended = True

            elif 'Wait for response timeout' in otbr_message:
                if self.DEBUG:
                    self.s_print("\nWARNING, otbr got timeout - usb stick not responding?")



    #
    #  START MATTER.SERVER
    #

    def start_matter_server_js(self):
        if self.DEBUG:
            print("in start_matter_server")

        if not os.path.exists(self.data_path):
            self.s_print("ERROR DATA PATH DOES NOT EXIST")
            os.system('mkdir -p ' + str(self.data_path))


        


        if self.DEBUG:
            print("Started Matter.server")









    def start_matter_server(self):
        if self.DEBUG:
            print("in start_matter_server.  version: ", version)

        if not os.path.exists(self.data_path):
            self.s_print("start_matter_server: data dir did not exist yet. Creating it now.")
            os.system('mkdir -p ' + str(self.data_path))



        #
        #  PYTHON VERSION
        #
        # This is the 'old' version, which will NOT get updates. 
        # It uses less memory and disk space than the new Node JS version (below)

        if self.matter_server_type == 'Python':
            
            python3_path = str(run_command('readlink $(which python3)'))
            python3_path = "/usr/bin/" + str(python3_path).rstrip()

            if self.DEBUG:
                print("start_matter_server:  python3_path: ", python3_path)

            if not os.path.exists(python3_path):
                if self.DEBUG:
                    print("start_matter_server: error, could not find python binary at path: ", python3_path)
                python3_path = 'python3'
            # /home/pi/.webthings/addons/matter-adapter/lib/
            #matter_server_command = str(python3_path) + ' -m matter_server.server --storage-path ' + str(self.data_path)
            matter_server_command = str(python3_path) + ' -m matter_server.server --storage-path ' + str(self.hasdata_dir_path)

            if self.vendor_id != "":
                decimal_vendor_id = int(self.vendor_id, 16)
                #matter_server_command = matter_server_command + " --vendorid " + str(self.vendor_id)
                matter_server_command = matter_server_command + " --vendorid " + str(decimal_vendor_id)

            if self.nmcli_installed == True:
                matter_server_command = matter_server_command + " --primary-interface uap0"


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


            if not os.path.exists(self.data_path):
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
            
            
            # ALL AVAILABLE FLAGS ARE DOCUMENTED HERE: https://github.com/matter-js/matterjs-server/blob/main/docs/cli.md
            #matter_server_command = 'npm run server --

            # node --enable-source-maps packages/matter-server/dist/esm/MatterServer.js

            # self.matter_server_start_path = os.path.join(self.matter_server_base_path,'packages','matter-server','dist','esm','MatterServer.js')

            matter_server_command = '/home/pi/node24 --enable-source-maps --disable-dashboard ' + self.matter_serverjs_start_path

            matter_server_command = matter_server_command + ' --storage-path ' + str(self.data_path)



            if self.DEBUG:
                matter_server_command += ' --log-level debug'
            else:
                matter_server_command += ' --log-level critical'


            if self.nmcli_installed == True:
                matter_server_command = matter_server_command + " --primary-interface uap0"

            # --listen-address 192.168.12.1  # REPEATABLE, so should then also bind to wpan0 if that has an IP address


            #matter_server_command = matter_server_command + " --ble"

            if self.vendor_id != "":
                decimal_vendor_id = int(self.vendor_id, 16)
                #matter_server_command = matter_server_command + " --vendorid " + str(self.vendor_id)
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
            self.server_process = subprocess.Popen(matter_server_command_array, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=my_env, cwd=self.matter_server_base_path)
            os.set_blocking(self.server_process.stdout.fileno(), False)
            os.set_blocking(self.server_process.stderr.fileno(), False)


        if self.DEBUG:
            print("Started Matter.server")




    # Currently unused, but could optimize which Thread channel to select. Apple always chooses 26 though, so that might not be a bad choice either.
    def wifi_congestion_scan(self):
        if self.DEBUG:
            print("in wifi_congestion_scan (BLOCKED)")

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



    # TODO: implement a feature to find all nearby Threat networks using otbr cli/agent



    def start_thread_mesh(self):
        if self.DEBUG:
            self.s_print("in start_thread_mesh")
        dataset_loaded = False

        ip_link_show_output = str(run_command('ip link show'))
        if self.DEBUG:
            self.s_print("start_thread_mesh:  ip_link_show_output: \n" + str(ip_link_show_output))

        if os.path.isfile(self.ot_ctl_path) and 'wpan0' in ip_link_show_output:

            if self.DEBUG:
                self.s_print("start_thread_mesh: calling add_otbr_iptables")
            self.add_otbr_iptables()

            if self.DEBUG:
                self.s_print("start_thread_mesh: setting txpower to 8")
            txpower_output = self.run_ot_ctl_command('txpower 8')
            if self.DEBUG:
                self.s_print("txpower_output: ", txpower_output)


            initial_thread_state = str(self.run_ot_ctl_command('state')).rstrip()
            if self.DEBUG:
                self.s_print("initial_thread_state: \n" + str(initial_thread_state))


            if 'leader' in initial_thread_state or 'router' in initial_thread_state:
                if self.DEBUG:
                    self.s_print("\nThread is already running?!\n" + str(initial_thread_state))

                if str(self.run_ot_ctl_command('thread stop')).rstrip() == 'Done':
                    if str(self.run_ot_ctl_command('ifconfig down')).rstrip() == 'Done':
                        # eh?
                        if self.DEBUG:
                            self.s_print("start_thread_mesh: brought down thread first")

            self.thread_running = False

            if 'thread_dataset' in self.persistent_data and isinstance(self.persistent_data['thread_dataset'],str) and len(self.persistent_data['thread_dataset']) > 40:
                if self.DEBUG:
                    print("OK, there is a thread dataset in persistent data. Will attempt to load it.")
                #dataset networkkey
                #if str(self.run_ot_ctl_command('dataset set active ' + str(self.persistent_data['thread_dataset']))).rstrip() == 'Done':
                load_dataset_check = str(self.run_ot_ctl_command('dataset init tlvs ' + str(self.persistent_data['thread_dataset']), 60)).rstrip()

                if load_dataset_check == 'Done':
                #if str(self.run_ot_ctl_command('dataset init active ' + str(self.persistent_data['thread_dataset']))).rstrip() == 'Done':
                    initial_dataset = str(self.run_ot_ctl_command('dataset')).rstrip()
                    self.s_print("loaded initial_dataset? ", initial_dataset)

                    if str(self.run_ot_ctl_command('dataset commit active')).rstrip() == 'Done':
                        if self.DEBUG:
                            self.s_print("start_thread_mesh: OK, loaded and comitted existing thread dataset")
                        dataset_loaded = True

                    #if str(self.run_ot_ctl_command('dataset networkname CandleThread')).rstrip() == 'Done':
                        #if str(self.run_ot_ctl_command('set channel ' + str(self.thread_channel))).rstrip() == 'Done':
                        #    if self.DEBUG:
                        #        self.s_print("channel set")
                elif 'timed out after' in load_dataset_check:
                    if self.DEBUG:
                            self.s_print("ERROR: start_thread_mesh: loading the datset timed out")

            else:
                if self.DEBUG:
                    print("warning, no thread dataset in persistent data")

            if dataset_loaded == False:

                if 'thread_dataset' in self.persistent_data and isinstance(self.persistent_data['thread_dataset'], str) and len(self.persistent_data['thread_dataset']) > 10:
                    if self.DEBUG:
                        print("\nERROR, dataset was not loaded, but there is a thread dataset in persistent data. Did loading the dataset time-out?")
                    self.thread_error = 'Error, failed to load Thread dataset'
                else:
                    if self.DEBUG:
                        print("\nWARNING, creating brand new thread dataset\n")
                    if self.run_ot_ctl_command('dataset init new'):
                        panid = '0x' + str(run_command('openssl rand -hex 1')).rstrip()
                        extpanid = str(run_command('openssl rand -hex 8')).rstrip()
                        networkkey = str(run_command('openssl rand -hex 16')).rstrip()
                        if len(extpanid) > 4 and len(networkkey) > 8:
                            if str(self.run_ot_ctl_command('dataset panid ' + str(panid))).rstrip() == 'Done': #0xdead
                                if str(self.run_ot_ctl_command('dataset extpanid ' + str(extpanid))).rstrip() == 'Done': # dead1111dead2222
                                    if str(self.run_ot_ctl_command('dataset networkname CandleThread')).rstrip() == 'Done':
                                        if str(self.run_ot_ctl_command('dataset networkkey ' + str(networkkey))).rstrip() == 'Done': #11112233445566778899DEAD1111DEAD
                                            #if str(self.run_ot_ctl_command('set channel ' + str(self.thread_channel))).rstrip() == 'Done':
                                            #    if self.DEBUG:
                                            #        self.s_print("channel set")
                                            if str(self.run_ot_ctl_command('dataset commit active')).rstrip() == 'Done':
                                                if self.DEBUG:
                                                    self.s_print("start_thread_mesh: OK, called dataset commit active on brand new thread dataset")
                                                dataset_loaded = True



            if dataset_loaded:
                #self.thread_running = True


                time.sleep(1)

                if self.DEBUG:
                    dataset_check = str(self.run_ot_ctl_command('dataset')).rstrip()
                    self.s_print("DATASET LOADED\ndataset_check: \n" + dataset_check)

                thread_state = str(self.run_ot_ctl_command('state')).rstrip()
                if self.DEBUG:
                    self.s_print("thread state: \n" + str(thread_state))


                if 'leader' in thread_state or 'router' in thread_state:
                    self.thread_running = True
                    if self.DEBUG:
                        self.s_print("\nOK - Thread is already up and running\n" + str(thread_state))

                elif 'child' in thread_state:
                    self.thread_running = True
                    if self.DEBUG:
                        self.s_print("\nERROR, Thread state is child")

                elif 'isabled' in thread_state or 'etached' in thread_state:
                    if self.DEBUG:
                        self.s_print("\nWARNING, dataset loaded, but thread started in disabled or detached state. Attempting to bring it up.")
                    if str(self.run_ot_ctl_command('ifconfig up')).rstrip() == 'Done':
                        if str(self.run_ot_ctl_command('thread start')).rstrip() == 'Done':
                            self.thread_running = True
                            if self.DEBUG:
                                self.s_print("\nOK, Thread has now fully started\n")
                else:
                    if self.DEBUG:
                        self.s_print("\nERROR, checking if thread has started fell through.  thread_state: \n" + str(thread_state))
                    time.sleep(1)
                    self.thread_set_active = False


                if self.thread_running:
                    active_dataset = self.run_ot_ctl_command('dataset active -x')
                    if self.DEBUG:
                        self.s_print("dataset loaded, in theory. dataset active -x: " + str(active_dataset))

                    if isinstance(active_dataset,str) and 'Done' in active_dataset and len(active_dataset) > 40:
                        self.thread_dataset = str(active_dataset).replace('Done','').strip().rstrip()

                        if len(self.thread_dataset) < 10:
                            self.thread_dataset = ''
                            time.sleep(1)
                            self.thread_set_active = False
                            if self.DEBUG:
                                self.s_print("\nERROR, thread_dataset from dataset active -x was too short to be valid: ", self.thread_dataset)
                            return

                        if self.DEBUG:
                            self.s_print("self.thread_dataset: -->" + str(self.thread_dataset) + "<--")
                        self.set_thread_dataset()

                        if not 'thread_dataset' in self.persistent_data:
                            self.persistent_data['thread_dataset'] = "" + str(self.thread_dataset)
                            self.should_save = True

                        elif 'thread_dataset' in self.persistent_data and isinstance(self.persistent_data['thread_dataset'],str) and len(self.persistent_data['thread_dataset']) > 10:
                            if str(self.thread_dataset) == str(self.persistent_data['thread_dataset']):
                                if self.DEBUG:
                                    self.s_print("OK, the thread dataset is still the same")
                            else:
                                if self.DEBUG:
                                    self.s_print("\nERROR, thread dataset is different from version in persistent data!")
                                    self.s_print(str(self.thread_dataset) + " != " + str(self.persistent_data['thread_dataset']) + "\n")
                                if len(self.thread_dataset) < len(self.persistent_data['thread_dataset']):
                                    self.thread_dataset = ''
                    else:
                        if self.DEBUG:
                            self.s_print("\nERROR, active thread dataset is way too short: " + str(active_dataset))

                else:
                    if self.DEBUG:
                        self.s_print("\nERROR, could not get thread to run!\n")
                    time.sleep(1)
                    self.thread_set_active = False
            else:
                if self.DEBUG:
                    self.s_print("\nERROR, no Thread dataset loaded!\n")
                time.sleep(1)
                self.thread_set_active = False

            if self.thread_running and self.DEBUG:
                self.s_print("__THREAD DETAILS__")
                self.s_print(str(self.run_ot_ctl_command('dataset active -x')))
                self.s_print(str(self.run_ot_ctl_command('netdata show')))
                self.s_print(str(self.run_ot_ctl_command('ipaddr')))
                self.s_print("")
                self.s_print(str(run_command('sudo sysctl -a | grep .wpan0.')))
                self.s_print("")


        else:
            self.s_print("\nERROR, start_thread_mesh: ot-ctl does not exist, or 'wpan0' not in ip link show\nself.ot_ctl_path: " + str(self.ot_ctl_path) + "\n" + str(ip_link_show_output) + "\n\n")
            time.sleep(1)
            self.thread_set_active = False



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
                self.s_print("Warning, really_stop_otbr was called while it was already busy stopping OTBR")
            return

        self.otbr_stopping_timestamp = time.time()
        if self.otbr_agent_process != None and self.otbr_agent_process.poll() == None:
            self.run_ot_ctl_command('thread stop')
            self.run_ot_ctl_command('ifconfig down')
            if self.DEBUG:
                self.s_print("really_stop_otbr: called ot-ctl thread stop and ot-ctl ifconfig down")
            if self.otbr_agent_process and self.otbr_agent_process != None:
                self.otbr_agent_process.terminate()
                time.sleep(0.3)
                if self.otbr_agent_process and self.otbr_agent_process.poll() == None:
                    if self.DEBUG:
                        self.s_print("warning, otbr_agent_process is still alive after .terminate()")
                    self.otbr_agent_process.kill()
                    time.sleep(0.2)
                    if self.otbr_agent_process and self.otbr_agent_process.poll() == None:
                        if self.DEBUG:
                            self.s_print("\nERROR, otbr_agent_process is still alive after .kill(). Calling pkill..")
                        os.system('sudo pkill -f otbr-agent')
        self.otbr_agent_process = None
        self.thread_radio_is_alive_count = 0
        self.thread_set_active = False
        self.thread_error = ''
        self.thread_running = False
        self.should_start_otbr = False
        self.otbr_started = False
        self.otbr_starting_timestamp = None
        self.otbr_stopping_timestamp == 0



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
            time.sleep(10)
            if self.DEBUG:
                self.s_print("client thread: zzz done, starting client")
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

                    if 'data' in message:
                        self.last_received_server_info = message['data']
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
                self.client_connected = True

                # Set the wifi credentials
                self.set_wifi_credentials()

                # Set the thread credentials
                self.set_thread_dataset()

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
                    self.client_connected = True


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

                    if message['message_id'] == "commission_with_code":
                        if self.DEBUG:
                            self.s_print("OK! Device was paired! result: ", message['result'])
                        self.discovered = message['result']
                        self.busy_discovering = False
                        self.busy_pairing = False
                        self.pairing_phase = 100
                        self.pairing_phase_message = 'Pairing completed succesfully'
                        self.get_nodes()

                    elif message['message_id'] == 'start_listening':
                        if self.DEBUG:
                            self.s_print("OK LISTENING")

                    elif message['message_id'] == 'set_wifi_credentials':
                        if self.DEBUG:
                            self.s_print("OK WIFI CREDENTIALS SET")

                    elif message['message_id'] == 'discover' and 'result' in message.keys():
                        if self.DEBUG:
                            self.s_print("OK DISCOVER RESPONSE")
                        self.discovered = message['result']
                        self.busy_discovering = False

                    elif message['message_id'] == 'commission_with_code':
                        if self.DEBUG:
                            self.s_print("\n\nNew device paired succesfully\n\n")
                        self.send_pairing_prompt("New device paired succesfully")
                        self.get_nodes()

                    elif message['message_id'] == 'node_added':
                        if self.DEBUG:
                            self.s_print("\n\nNew device paired succesfully\n\n")

                    elif message['message_id'] == 'get_nodes':
                        if 'result' in message:
                            if self.DEBUG:
                                self.s_print("\n\nGET NODES succesfull\n\n")
                            self.nodes = message['result']
                            self.parse_nodes()
                            self.ready = True # the addon should now have recreated the things

                    elif message['message_id'].startswith('get_node_'):
                        if self.DEBUG:
                            self.s_print("\n\nGET NODE succesfull\n\n")
                        device_info = message['result']
                        if self.DEBUG:
                            self.s_print("DEVICE INFO: " + str(json.dumps(device_info)))

                    elif message['message_id'] == 'remove_node':
                        if self.DEBUG:
                            self.s_print("\n\nremove_node was succesfull\n\n")
                        self.device_was_deleted = True
                        #self.nodes = message['result']
                        #self.parse_nodes()
                        self.get_nodes()

                    elif message['message_id'] == 'open_commissioning_window' or message['message_id'] == 'commission_on_network':

                        if 'result' in message and isinstance(message['result'],str):
                            self.share_node_code = message['result']
                            if self.DEBUG:
                                self.s_print("\n\nopen_commissioning_window or commission_on_network was succesfull?  self.share_node_code: ", self.share_node_code, "\n\n")


                    # Handle event messages
                    #elif ('_type' in message and message['_type'].endswith("message.EventMessage")) or 'message_id' in message:




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

                    if message['message_id'] == "device_command":
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

                    else:
                        if self.DEBUG:
                            self.s_print("interesting, an unanticipated error message. message_id: " + str(message['message_id']))





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


    def get_nodes(self):
        try:
            if self.client_connected and self.last_get_nodes_timestamp < time.time() - 30:
                self.last_get_nodes_timestamp = time.time()

                if self.DEBUG:
                    self.s_print("get_nodes: Client is connected, so asking for latest node list")

                message = {
                        "message_id": "get_nodes",
                        "command": "get_nodes"
                      }
                json_message = json.dumps(message)
                self.ws.send(json_message)

                return True
            else:
                if self.DEBUG:
                    self.s_print("Error in get_nodes: client was not connected yet, or already did get_nodes recently")

        except Exception as ex:
            if self.DEBUG:
                self.s_print("caught error in get_nodes: " + str(ex))

        return False


    def get_node(self, node_id):
        try:
            if self.client_connected:

                if self.DEBUG:
                    self.s_print("get-node: Client is connected, so asking for info on single node")

                message = {
                        "message_id": "get_node",
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
            if self.client_connected:

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
            if self.client_connected:

                self.busy_discovering = True

                if self.DEBUG:
                    self.s_print("discover: Client is connected, so sending discover command to Matter server")

                message = {
                        "message_id": "discover",
                        "command": "discover"
                      }

                json_message = json.dumps(message)
                self.ws.send(json_message)

                return True

        except Exception as ex:
            self.s_print("Error in discover: " + str(ex))

        return False



    # Download the latest certificates
    def download_certs(self):
        if self.DEBUG:
            self.s_print("in download_certs")
        if time.time() - self.time_between_certificate_downloads > self.persistent_data['last_certificates_download_time']:
            if self.DEBUG:
                self.s_print("downloading latest certificates")
            self.pairing_phase_message = 'Updating certificates'
            self.busy_updating_certificates = True
            self.certificates_updated = False
            certificates_download_command = "python3 " + str(self.certs_downloader_path) + " --use-main-net-http --paa-trust-store-path " + str(self.certs_dir_path)
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

                if len(str(download_certs_output)) > 5:
                    self.certificates_updated = True
                    #self.last_certificates_download_time = time.time()
                    self.persistent_data['last_certificates_download_time'] = int(time.time())
                    self.should_save = True
                    return True
                else:
                    if self.DEBUG:
                        self.s_print("Error, certificates didn't seem to download (output was None)")
                    self.send_pairing_prompt("failed to download certificates")
                    return False

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
            if self.client_connected == False:
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
    def set_thread_dataset(self):
        if self.DEBUG:
            self.s_print("in set_thread_dataset. self.thread_dataset: " + str(self.thread_dataset))
        try:
            if self.client_connected == False:
                if self.DEBUG:
                    self.s_print("Cannot set thread dataset, client is not connected to Matter server")

            elif isinstance(self.thread_dataset,str) and len(self.thread_dataset) > 10:
                if self.DEBUG:
                    self.s_print("Sharing thread dataset with Matter server")

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
                thread_message = {
                        "message_id": "set_thread_dataset",
                        "command": "set_thread_dataset",
                        "args": {
                            "dataset": str(self.thread_dataset)
                        }
                      }

                # send wifi credentials
                if self.DEBUG:
                    self.s_print("\n.\n) ) )\n.\nsending thread credentials: " + str(thread_message))
                json_thread_message = json.dumps(thread_message)

                self.ws.send(json_thread_message)
                return True

            else:
                if self.DEBUG:
                    self.s_print("Cannot set thread dataset, as there is no dataset to set yet.  self.thread_dataset: ", self.thread_dataset)

        except Exception as ex:
            if self.DEBUG:
                self.s_print("caught error in set thread dataset: " + str(ex))

        return False











    #
    #   START MATTER PAIRING
    #




    def start_matter_pairing(self,pairing_type=None):
        if self.DEBUG:
            self.s_print("\n\n\n\nin start_matter_pairing. Pairing type: " + str(pairing_type))
        try:
            self.last_pairing_start_time = time.time()
            if self.turn_wifi_back_on_at > self.last_pairing_start_time:
                self.turn_wifi_back_on_at = 0
                if self.DEBUG:
                    print("start_matter_pairing: turning WiFi back on first")
                run_command('nmcli radio wifi on')

            self.pairing_failed = False
            self.pairing_phase = 0
            self.busy_pairing = True
            # Download the latest certificates if they haven't been updated in a while
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

            if self.wireless_type == 'thread' and self.pairing_attempt < 5:
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

                        if len(discriminator) == 4 and len(passcode) == 8:

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



            #return



            try:
                if self.client_connected:
                    if self.DEBUG:
                        self.s_print("start_pairing: Client is connected, so sending commissioning code to Matter server.")

                    self.busy_pairing = True
                    self.pairing_phase_message = 'Setting credentials'


                    # Set the wifi credentials
                    if self.pairing_attempt == 0:
                        self.set_wifi_credentials()
                        self.pairing_phase = 2
                        self.set_thread_dataset()
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
                        self.pairing_phase_message = 'Pairing in progress'
                        return True

                else:
                    self.pairing_phase_message = 'Error, Matter is not running'
                    if self.DEBUG:
                         self.s_print("start_matter_pairing: error, client is not connected")
                         self.send_pairing_prompt("Error, Matter client is not connected")

            except Exception as ex:
                self.s_print("caught error in start_pairing: " + str(ex))
                self.pairing_phase_message = 'An unexpected error occured while trying to start pairing'

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

                if seconds_counter > 5:
                    seconds_counter = 0
                    self.noise_delta = self.noise_counter - self.previous_noise_counter
                    self.previous_noise_counter = self.noise_counter

                #self.s_print("tick tock")
                passed_time = time.time() - last_tick_tock_time

                #if self.DEBUG:
                #    self.s_print("clock: actual seconds that passed: ", passed_time)
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
                                            print("Thread radio was uplugged during pairing.")
                                        self.busy_pairing = False
                                        if self.turn_wifi_back_on_at > 0:
                                            self.turn_wifi_back_on_at = 0
                                            if self.DEBUG:
                                                print("Thread radio was uplugged during pairing -> Forcing WiFi back on.")
                                            run_command('nmcli radio wifi on')

                                        self.pairing_failed = True
                                        self.pairing_phase = -1
                                
                                self.thread_radio_went_missing = True

                        if self.thread_radio_went_missing == False:
                            wpan0_check = run_command('ip link show')
                            if isinstance(wpan0_check,str) and not 'wpan0' in wpan0_check:
                                if self.DEBUG:
                                    self.s_print("\nERROR: wpan0 no longer seems to exist even though in theory Thread is running")
                                self.really_stop_otbr()
                                self.should_start_otbr = True


                    #if self.thread_radio_went_missing == False:
                    #    self.ensure_bridge()

                #if self.found_a_thread_radio_once == True and self.thread_radio_went_missing == False:


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
                self.send_pairing_prompt("Turning on WiFi again")
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
                if self.server_process:
                    for line in iter(self.server_process.stdout.readline,b''):
                        if self.DEBUG:
                            self.s_print("CAPTURED STDOUT: " + str(line.decode().rstrip()))

                        # nothing is coming out of stdout


                    for line in iter(self.server_process.stderr.readline,b''):
                        line = line.decode()
                        if self.DEBUG:
                            self.s_print("CAPTURED STDERR: " + str(line.rstrip()))

                        if 'collides with an existing FabricAdmin instance' in line:
                            if self.DEBUG:
                                self.s_print("\n\nERROR: matter server fabric config issue\n\n")
                            self.reset_matter()

                        if 'address already in use' in line:
                            if self.DEBUG:
                                self.s_print("\n\nERROR: matter server running twice?\n\n")

                        #if 'Traceback' in line:
                        #    self.pairing_failed = True
                        #    self.busy_pairing = False
                        #    self.send_pairing_prompt("Error, Matter server crashed")
                        #    self.pairing_phase_message = 'Matter crashed!'
                        #    self.pairing_phase = -1
                        if 'over BLE failed' in line:
                            self.pairing_failed = True
                            self.busy_pairing = False
                            self.send_pairing_prompt("Bluetooth commissioning failed")
                            self.pairing_phase_message = 'Bluetooth connection to Matter device could not be established'
                            self.pairing_phase = -1

                        if 'Found unconnected device, removing' in line:
                            self.pairing_phase_message = 'Removing unconnected device, likely from a previous failed pairing attempt'

                        if "Error on commissioning step 'WiFiNetworkEnable'" in line:
                            self.pairing_phase_message = 'Pairing failed because the WiFi network could not be enabled'

                        if 'error.NodeInterviewFailed' in line:
                            if self.busy_pairing:
                                self.pairing_failed = True
                                self.busy_pairing = False
                                self.send_pairing_prompt("Interviewing Matter device failed")
                                self.pairing_phase = -1
                                self.pairing_phase_message = 'Interviewing the Matter device failed'
                        if 'Commission with code failed for node' in line:
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
                                self.pairing_phase_message = 'Pairing failed'
                                self.pairing_phase = -1


                        if 'Established secure session with Device' in line:
                            self.send_pairing_prompt("Connected to new device...")
                            self.pairing_phase_message = 'Secure connection to Matter device established'
                            self.pairing_phase = 50
                        if 'Setting up attributes and events subscription' in line:
                            #if time.time() - self.addon_start_time > 60:
                            if self.busy_pairing:
                                self.send_pairing_prompt("Setting up device...")
                                self.pairing_phase_message = 'Setting up Matter device'
                                self.pairing_phase = 70
                        if 'Discovery timed out' in line:
                            if self.busy_pairing:
                                self.pairing_failed = True
                                self.busy_pairing = False
                                self.send_pairing_prompt("No new Matter device detected")
                                self.pairing_phase_message = 'No new Matter device detected'
                                self.pairing_phase = -1
                        if 'Failed to establish secure session to device' in line:
                            self.pairing_failed = True
                            self.busy_pairing = False
                            self.send_pairing_prompt("Creating secure connection to new Matter device failed")
                            self.pairing_phase_message = 'Creating secure connection to new Matter device failed'
                            self.pairing_phase = -1
                        if 'le-connection-abort-by-local' in line:
                            self.pairing_failed = True
                            self.busy_pairing = False
                            self.send_pairing_prompt("Bluetooth got wireless interference.")
                            self.pairing_phase_message = 'Could not connect to new device via Bluetooth. Possibly because of wireless interference'
                            self.pairing_phase = -1
                        if 'address already in use' in line:
                            self.s_print("ERROR, THERE ALREADY IS A MATTER SERVER RUNNING")

                        if 'Subscription succeeded with report interval' in line or 'Re-Subscription succeeded' in line:
                            if self.DEBUG:
                                self.s_print("A device re-connected")
                            if '<Node:' in line:
                                device_index = line.split('<Node:')[1]
                                if '>' in device_index:
                                    device_index = device_index.split('>')[0]
                                    if device_index.isdigit():
                                        device_id = 'matter-' + str(device_index)
                                        target_device = self.get_device(device_id)
                                        if target_device:
                                            target_device.connected = True
                                            target_device.connected_notify(True)

                            if self.thread_running and self.informed_matter_server_about_thread == False:
                                self.informed_matter_server_about_thread = self.set_thread_dataset()
                                if self.DEBUG:
                                    print("A device re-connected -> self.informed_matter_server_about_thread: ", self.informed_matter_server_about_thread)


                        if 'Subscription failed' in line and 'Timeout, resubscription attempt 3' in line:
                            if self.DEBUG:
                                self.s_print("A device seems to have become unavailable")
                            # <Node:20>
                            if '<Node:' in line:
                                device_index = line.split('<Node:')[1]
                                if '>' in device_index:
                                    device_index = device_index.split('>')[0]
                                    if self.DEBUG:
                                        print("device seems to have become unavailable: ", device_index)
                                    if device_index.isdigit():
                                        device_id = 'matter-' + str(device_index)
                                        target_device = self.get_device(device_id)
                                        if target_device:
                                            target_device.connected = False
                                            target_device.connected_notify(False)
                                            try:
                                                for dev in self.devices:
                                                    if self.DEBUG:
                                                        print("checking is device is connedted ", dev)
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
                                    print("Device not available (yet): ", device_index)
                                if device_index.isdigit():
                                    device_id = 'matter-' + str(device_index)
                                    target_device = self.get_device(device_id)
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
                self.s_print("Error in clock try: " + str(ex))
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
            if now_stamp - self.last_time_sync_time > self.time_sync_interval:
                if self.DEBUG:
                    print("CLOCK: time to sync time")
                self.last_time_sync_time = now_stamp

                self.timezone_name = str(run_command('date +%Z')).strip().rstrip()
                #self.timezone_offset = str(run_command('date +%z')).strip().rstrip()
                #self.timestamp = int(str(run_command('date +%s')).strip().rstrip())

                for device_id in self.matter_devices_with_time_sync:
                    if not str(device_id).startswith('matter-'):
                        device_id = 'matter-' + str(device_id)
                    target_device = self.get_device(device_id)
                    if target_device:
                        target_device.sync_time()

        if self.DEBUG:
            print("CLOCK EXITED")


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
                    if not node_id in self.thread_diagnostics:
                        self.thread_diagnostics[node_id] = {}
                    self.thread_diagnostics[node_id][attribute_name] = value
                    if self.DEBUG:
                        print("self.thread_diagnostics is now: ", self.thread_diagnostics)

                if clusters_to_ignore and cluster_name in clusters_to_ignore:
                    if self.DEBUG:
                        self.s_print("handle_event: skipping because cluster_name was in list of clusters_to_ignore: ", cluster_name)

                #if 'Diagnostics' in cluster_name:
                #    if self.DEBUG:
                #        self.s_print("handle_event: skipping diagnostics cluster")
                #    return

                if attribute_name.isdigit():
                    if self.DEBUG:
                        self.s_print("ERROR: handle_event: attribute_name is digit")
                    attribute_name = None

            elif 'node_id' in data and 'value' in data and 'attribute_id' in data and 'endpoint_id' in data:
                node_id = data['node_id']
                value = data['value']
                attribute_name = data['attribute_id']
                endpoint = data['endpoint_id']
                endpoint_name = 'Endpoint' + str(endpoint)

            # handling data['data'] data, like 'totalNumberOfPressesCounted''
            elif self.add_hacky_properties and 'node_id' in data and 'endpoint_id' in data and 'cluster_id' in data and 'data' in data:
                for data_attribute in data['data']:
                    if not 'previous' in data_attribute.lower() and isinstance(data['data'][data_attribute],(str,int,float,bool)):
                        if self.DEBUG:
                            self.s_print("Found something potentually useful in data['data']: ", data_attribute, data['data'][data_attribute])

                        # "Events are records of past state transitions such as a light device's on-off attribute changing from on to off."
                        # - source: https://docs.silabs.com/matter/latest/matter-api-reference/event

                        node_id = data['node_id']
                        device_id = 'matter-' + str(node_id)
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
                            self.s_print("hacky device_id: ", device_id)
                            self.s_print("hacky endpoint_name: ", endpoint_name)

                        if not device_id in self.persistent_data['nodez']:
                            if self.DEBUG:
                                self.s_print("unexpectedly, missing device_id in persistent data? ", device_id)
                        else:
                            if not endpoint_name in self.persistent_data['nodez'][device_id]['attributes']:
                                if self.DEBUG:
                                    self.s_print("unexpectedly, missing endpoint_name in persistent data? ", endpoint_name)

                            else:
                                if hacky_attribute_code in self.persistent_data['nodez'][device_id]['attributes'][endpoint_name]:
                                    if self.DEBUG:
                                        self.s_print("surprisingly, there is already an attribute with this hacky code: ", self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][hacky_attribute_code])
                                else:
                                    hacky_attribute_code = str(cluster_name) + 'Candle.Attributes.' + str(data_attribute)

                                    if hacky_attribute_code in self.persistent_data['nodez'][device_id]['attributes'][endpoint_name]:
                                        if self.DEBUG:
                                            self.s_print("this hacky property has already been created in persistent data: ", self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][hacky_attribute_code])

                                        device_id = 'matter-' + str(node_id)
                                        target_device = self.get_device(device_id)
                                        if target_device:
                                            hacky_property_id = 'property-' + str(endpoint_name) + '-'+ str(cluster_name) + 'Candle-' + str(data_attribute)
                                            if self.DEBUG:
                                                self.s_print("hacky_property_id: ", hacky_property_id)
                                            hacky_target_property = target_device.find_property(hacky_property_id)
                                            if hacky_target_property:
                                                if self.DEBUG:
                                                    self.s_print("OK, found hacky property. Will update it to: ", value)
                                                hacky_target_property.update( value )

                                    else:
                                        attribute_code = hacky_attribute_code
                                        if self.DEBUG:
                                            self.s_print("\ncreating new hacky property\n")
                                        self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][hacky_attribute_code] = {'enabled':True,'property':{'description':{'title':uncamel(data_attribute).replace('_',' ') + ' ' + str(endpoint),'readOnly':True}},'hacky':True,'value': value, 'received_values':[value]}
                                        if isinstance(value,int):
                                            self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][hacky_attribute_code]['property']['description']['type'] = 'number'
                                        elif isinstance(value,str):
                                            self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][hacky_attribute_code]['property']['description']['type'] = 'string'
                                        elif isinstance(value,bool):
                                            self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][hacky_attribute_code]['property']['description']['type'] = 'boolean'

                                        self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][hacky_attribute_code]['property']['attribute_code'] = attribute_code


                                        device_id = 'matter-' + str(node_id)
                                        target_device = self.get_device(device_id)
                                        if target_device:
                                            if self.DEBUG:
                                                self.s_print("calling reparse_node so that the new hacky property will immediately be created")
                                            target_device.reparse_node()



            else:
                if self.DEBUG:
                    self.s_print("WARNING: handle_event: getting parameters fell through")

            if self.DEBUG:
                self.s_print("handle_event: node_id, attribute_name, value: ", node_id, attribute_name, value)

            if node_id and endpoint_name and attribute_name: # should value be allowed to be None?
                device_id = 'matter-' + str(node_id)
                target_device = self.get_device(device_id)

                if endpoint and attribute_code:
                    endpoint_name = 'Endpoint' + str(endpoint)
                    if str(device_id) in self.persistent_data['nodez']:
                        if 'attributes' in self.persistent_data['nodez'][device_id] and endpoint_name in self.persistent_data['nodez'][device_id]['attributes']:

                            if attribute_code == None:
                                if self.DEBUG:
                                    self.s_print("handle_event: attribute_code was None")

                            elif str(attribute_code) in self.persistent_data['nodez'][device_id]['attributes'][endpoint_name]:
                                if self.auto_enable_properties == True:
                                    if 'enabled' in self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][str(attribute_code)] and self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][str(attribute_code)]['enabled'] == False:
                                        if self.DEBUG:
                                            self.s_print("handle_event: auto-enabling a property: ", attribute_code)
                                        self.should_save = True
                                    self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][str(attribute_code)]['enabled'] = True

                                # Keep track of the different type of variables that can be expected to be received
                                if not 'received_values' in self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][str(attribute_code)]:
                                    self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][str(attribute_code)]['received_values'] = []
                                elif len(self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][str(attribute_code)]['received_values']) > 10:
                                    if self.DEBUG:
                                        self.s_print("handle_event: trimming received values list back to 10 items")
                                    self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][str(attribute_code)]['received_values'] = self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][str(attribute_code)]['received_values'][-9:]

                                # Keep track of how many decimal points any numbers being sent will have, at maximum
                                # Also keep track of the smallest and largest number ever received. Useful to find out of percentages need to be scaled from 255, for example
                                # It is a privacy risk, so these values should not be exposed to the user, through it may be temping to use such values when displaying graph axis
                                if value != None and isinstance(value,(int,float)):
                                    if not 'max_decimals_received' in self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][str(attribute_code)]:
                                        self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][str(attribute_code)]['max_decimals_received'] = -1
                                    if not 'max_value_received' in self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][str(attribute_code)]:
                                        self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][str(attribute_code)]['max_value_received'] = value
                                    elif value > self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][str(attribute_code)]['max_value_received']:
                                        self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][str(attribute_code)]['max_value_received'] = value
                                    if not 'min_value_received' in self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][str(attribute_code)]:
                                        self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][str(attribute_code)]['min_value_received'] = value
                                    elif value < self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][str(attribute_code)]['min_value_received']:
                                        self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][str(attribute_code)]['min_value_received'] = value
                                    decimals = None
                                    if '.' in str(value):
                                        parts = str(value).split('.')
                                        limited_string = original_string[:max_length]
                                        if len(parts) == 2:
                                            parts[1] = str(parts[1])[:3]
                                            if str(parts[0]).isdigit() and str(parts[1]).isdigit():
                                                parts[1] = str(parts[1]).rstrip('0')
                                                decimals = len(parts[1])

                                    elif str(value).isdigit():
                                        decimals = 0
                                    #decimals = str(number)[::-1].find('.')
                                    if self.DEBUG:
                                        self.s_print("decimals: ", decimals)

                                    if decimals != None and decimals > self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][str(attribute_code)]['max_decimals_received']:
                                        self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][str(attribute_code)]['max_decimals_received'] = decimals


                                if value != None and isinstance(value,(str,int,float,bool)):
                                    if not value in self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][str(attribute_code)]['received_values']:
                                        if self.DEBUG:
                                            self.s_print("handle_event: appending not seen before value to received_values: ", value)
                                        self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][str(attribute_code)]['received_values'].append(value)
                                    else:
                                        if self.DEBUG:
                                            self.s_print("handle_event: that value has been received before: ", value)

                                    # Privacy risk to update the actual value
                                    #self.adapter.persistent_data['nodez'][device_id]['attributes'][endpoint_name][attribute_code]['value'] = value

                                if self.DEBUG:
                                    self.s_print("handle_event: received values:  device_id,endpoint_name,attribute_code,values: ", device_id, endpoint_name, attribute_code, self.persistent_data['nodez'][device_id]['attributes'][endpoint_name][str(attribute_code)]['received_values'])





                if target_device == None:
                    if self.DEBUG:
                        self.s_print("\nERROR: handle_event: missing device: ", device_id)
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
    def parse_nodes(self):
        if self.DEBUG:
            self.s_print("in parse_nodes. self.nodes length: " + str(len(self.nodes)))
        for node in list(self.nodes):
            self.parse_node(node)


    def parse_node(self,node):

        try:
            #if self.DEBUG:
            #    self.s_print("parse nodes: number: " + str(node_number))
            #node = self.nodes[node_number]

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

            device_id = 'matter-' + str(node_id)

            if self.DEBUG:
                self.s_print("\n\nparse_node: device_id: " + str(device_id))
                #print("node: \n", json.dumps(dataclass_to_dict(node),indent=2))


            if not 'attributes' in node and 'data' in node and 'attributes' in node['data']:
                if self.DEBUG:
                    self.s_print("pulling a switch to make node['data'] the new node")
                node = node['data']


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


                process_node(node)

                #if self.DEBUG:
                #    self.s_print("parse_node: node after: \n", json.dumps(node,indent=2))

            else:
                if self.DEBUG:
                    self.s_print("\nERROR: parse_node: aborting, no attributes in node data?: ", node)
                return


            # already handled by device
            # TODO: COMMENT THIS OUT AGAIN, AS THE DEVICE SHOULD HANDLE ADDING ITSELF TO THIS LIST
            #if not device_id in self.persistent_data['nodez']:
            #    self.persistent_data['nodez'][device_id] = {'device_id':device_id,'node_id':node_id,'attributes':{}}
            #    self.should_save = True


            if not 'node_id' in node:
                if self.DEBUG:
                    self.s_print("\nERROR: parse_node: node_id is missing from node data after process_node: ", node)
                return

            target_device = self.get_device(device_id)
            if target_device == None:
                if self.DEBUG:
                    self.s_print("parse_node: this device does not exist yet. Creating it now.")

                pairing_code = None
                if isinstance(self.last_found_pairing_code,str) and self.last_found_pairing_code not in self.persistent_data['pairing_codes'] and self.last_pairing_start_time > time.time() - 120:
                    pairing_code = "" + str(self.last_found_pairing_code)

                new_device = MatterDevice(self, device_id, node, pairing_code)
                self.handle_device_added(new_device)

            else:
                if self.DEBUG:
                    self.s_print("parse_node: target_device has already been created. Attempting to call it's update_from_node method.")
                target_device.update_from_node(node)
                self.handle_device_added(target_device)

            if 'available' in node and isinstance(node['available'],bool):
                if self.DEBUG:
                    self.s_print("parse_node: node.available: ", node['available'])
                target_device = self.get_device(device_id)
                if target_device:
                    if self.DEBUG:
                        self.s_print("parse_node: OK, calling connected_notify on device with state: ", node['available'])
                    target_device.connected_notify(node['available'])
                else:
                    if self.DEBUG:
                        self.s_print("\nWARNING: parse_node: unexpectedly device was still not created.  device_id: ", device_id)

        except Exception as ex:
            if self.DEBUG:
                self.s_print("error in parse_node: " + str(ex))


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


    # Reset Matter
    def reset_matter(self):
        if self.DEBUG:
            self.s_print("in reset_matter")

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

        if os.path.isdir('/home/pi/.webthings/hasdata_backup'):
            os.system('rm -rf /home/pi/.webthings/hasdata_backup')
        os.system('mkdir -p /home/pi/.webthings/hasdata_backup')
        os.system('mv /home/pi/.webthings/hasdata/* /home/pi/.webthings/hasdata_backup/')




    #
    #  CHANGING THE PROPERTIES
    #

    # It's nice to have a central location where a change in a property is managed.

    def set_state(self,state):
        try:
            if self.DEBUG:
                self.s_print("in set_state with state: " + str(state))

            # saves the new state in the persistent data file, so that the addon can restore the correct state if it restarts
            self.persistent_data['state'] = state
            self.save_persistent_data()

            # A cool feature: you can create popups in the interface this way:
            if state == True:
                self.send_pairing_prompt("You switched on the thing") # please don't overdo it with the pairing prompts..

            # We tell the property to change its value. This is a very round-about way, and you could place all this logic inside the property instead. It's a matter of taste.
            try:
                self.devices['matter-thing'].properties['state'].update( state )
            except Exception as ex:
                self.s_print("error setting state on thing: " + str(ex))

        except Exception as ex:
            self.s_print("error in set_state: " + str(ex))



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

            if 'nodez' in self.persistent_data and matter_id in self.persistent_data['nodez']:
                del self.persistent_data['nodez'][matter_id]
                self.should_save = True

            self.remove_node(device_id)

        except Exception as ex:
            if self.DEBUG:
                self.s_print("caught error in remove thing: " + str(ex))




    #
    # This saves the persistent_data dictionary to a file
    #

    def save_persistent_data(self):
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

        if self.client_connected == False:
            if self.DEBUG:
                self.s_print("remove_node: ERROR, client is not connected") # TODO: assuming that the matter server can even remove devices from thread
            return False

        self.get_nodes()
        time.sleep(3)
        matter_id = 'matter-' + str(node_id)


        if matter_id in self.nodes:
            if self.DEBUG:
                self.s_print("remove_node: Node seems to exist, will delete it")
            message = {
                    "message_id": "remove_node",
                    "command": "remove_node",
                    "args": {
                        "node_id": node_id
                    }
                  }
            json_message = json.dumps(message)
            self.ws.send(json_message)

        else:
            if self.DEBUG:
                self.s_print("\nERROR, remove_node: node doesn't seem to exist (already deleted?). Skipping delete")
            self.device_was_deleted = True # pretend it was just deleted

        return True


    def run_chip_tool_command(self, cmd, timeout_seconds=10):
        try:
            if not os.path.isfile(self.chip_tool_path):
                self.s_print("\nERROR, run_chip_tool_command: chip_tool is missing: ", self.chip_tool_path)
                return None
            my_env = get_env()

            my_env["LD_LIBRARY_PATH"] = '{}'.format(self.addon_thread_dir_path)

            #data_path = '/data'
            #my_env["TMPDIR"] = '{}'.format(self.data_path)
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
            #my_env["TMPDIR"] = '{}'.format(self.data_thread_dir_path)
            my_env["TMPDIR"] = '{}'.format(data_path)

            command = 'sudo ' + str(self.ot_ctl_path) + ' ' + str(cmd)
            if 'dataset' in cmd and cmd != 'dataset':
                command = command + ' --storage-directory ' + str(data_path)

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
