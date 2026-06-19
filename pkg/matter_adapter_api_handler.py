"""
Matter addon for Candle Controller.
"""


import os
#os.path.insert(1, dirname(os.path.dirname(os.path.abspath(__file__))))
import sys
# This helps the addon find python libraries it comes with, which are stored in the "lib" folder. The "package.sh" file will download Python libraries that are mentioned in requirements.txt and place them there.
lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')
if lib_path not in sys.path:
	sys.path.append(lib_path)

import json
import time
import requests
from gateway_addon import APIHandler, APIResponse

import traceback

from .matter_util import run_command

class MatterAPIHandler(APIHandler):
    """API handler."""

    def __init__(self, adapter, verbose=False):
        """Initialize the object."""
        #print("INSIDE API HANDLER INIT")
        
        self.adapter = adapter
        self.DEBUG = self.adapter.DEBUG


        # Intiate extension addon API handler
        try:
            manifest_fname = os.path.join(
                os.path.dirname(__file__),
                '..',
                'manifest.json'
            )

            with open(manifest_fname, 'rt') as f:
                manifest = json.load(f)

            APIHandler.__init__(self, manifest['id'])
            self.manager_proxy.add_api_handler(self)
            

            if self.DEBUG:
                print("self.manager_proxy = " + str(self.manager_proxy))
                print("Created new API HANDLER: " + str(manifest['id']))
        
        except Exception as e:
            print("Error: failed to init API handler: " + str(e))


        # Intiate extension addon API handler
        #try:
            
            #APIHandler.__init__(self, self.adapter.addon_id) # gives the api handler the same id as the adapter
            #self.adapter.manager_proxy.add_api_handler(self) # tell the controller that the api handler now exists
            #self.manager_proxy.add_api_handler(self) # tell the controller that the api handler now exists
            
        #except Exception as e:
        #    print("Error: failed to init API handler: " + str(e))
        
        
        
        
        
        
    #
    #  HANDLE REQUEST
    #

    def handle_request(self, request):
        """
        Handle a new API request for this handler.

        request -- APIRequest object
        """
        
        try:
            #print("IN HANDLE REQUEST")
            
            if request.method != 'POST':
                return APIResponse(status=404) # we only accept POST requests
            
            if request.path == '/ajax': # you could have all kinds of paths. In this example we only use this one, and use the 'action' variable to denote what we want to api handler to do

                try:
                    
                    action = str(request.body['action']) 
                    
                    #if self.DEBUG:
                    #    #print("API handler is being called. Action: " + str(action))
                    #    print("API: debug: request.body: " + str(request.body))
                    
                    
                    # INIT
                    if action == 'init':
                        if self.DEBUG:
                            print("API handler: in init")
                        
                        self.adapter.get_nodes()
                        time.sleep(5)
                        
                        wifi_credentials_available = False
                        if self.adapter.wifi_ssid != "" and self.adapter.wifi_password != "":
                            wifi_credentials_available = True

                        self.adapter.check_onboarding_state()

                        has_thread_dataset = False
                        if isinstance(self.adapter.persistent_data['thread_dataset'],str) and len(self.adapter.persistent_data['thread_dataset']) > 40:
                            has_thread_dataset = True
                            
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({
                                      'debug': self.DEBUG,
                                      'use_hotspot': self.adapter.use_hotspot,
                                      'hotspot_addon_installed': self.adapter.hotspot_addon_installed,
                                      'wifi_ssid': self.adapter.wifi_ssid,
                                      'wifi_credentials_available': wifi_credentials_available,
                                      'matter_client_connected': self.adapter.matter_client_connected,
                                      'nodez': self.adapter.persistent_data['nodez'],
                                      'disable_matter_dashboard':self.adapter.disable_matter_dashboard,
                                      'thread_channel':self.adapter.thread_channel,
                                      'matter_collision_detected':self.adapter.matter_collision_detected,
                                      'missing_vendor_id':self.adapter.missing_vendor_id,
                                      'thread_network_name':self.adapter.thread_network_name,
                                      'has_thread_dataset':has_thread_dataset
                                      }),
                        )
                        
                        
                    
                    # MAIN POLL
                    elif action == 'get_main_poll':
                        
                        wifi_restore_countdown = 0
                        if self.adapter.turn_wifi_back_on_at != 0:
                            if self.DEBUG:
                                print("get_main_poll: self.adapter.turn_wifi_back_on_at: ", self.adapter.turn_wifi_back_on_at)
                            wifi_restore_countdown = round(self.adapter.turn_wifi_back_on_at - time.time())
                            
                            if wifi_restore_countdown < 0:
                                wifi_restore_countdown = 0
                            else:
                                if self.DEBUG:
                                    print("get_main_poll: wifi_restore_countdown: ", wifi_restore_countdown)
                        
                        
                        thread_radio_is_alive_seconds_ago = None
                        if isinstance(self.adapter.last_thread_radio_is_alive_timestamp,int) and self.adapter.last_thread_radio_is_alive_timestamp != 0:
                            thread_radio_is_alive_seconds_ago = int(time.time()) - self.adapter.last_thread_radio_is_alive_timestamp;
                        
                        if wifi_restore_countdown != 0:
                            if self.DEBUG:
                                print("API: debug: get_main_poll:  wifi_restore_countdown: ", wifi_restore_countdown)
                        
                        last_update_check_seconds_ago = int(time.time()) - self.adapter.last_matter_update_check_timestamp
                        last_update_check_response_seconds_ago = int(time.time()) - self.adapter.last_matter_update_check_response_timestamp

                        if self.adapter.thread_running == True and self.adapter.busy_pairing == False:
                            if self.DEBUG:
                                print("api_handler: get_main_poll: calling update_thread_state_info")
                            self.adapter.update_thread_state_info()

                        has_thread_dataset = False
                        if isinstance(self.adapter.persistent_data['thread_dataset'],str) and len(self.adapter.persistent_data['thread_dataset']) > 40:
                            has_thread_dataset = True

                        pairing_activity_seconds_ago = 0
                        if self.adapter.last_pairing_update_time > 0:
                            pairing_activity_seconds_ago = int(time.time()) - self.adapter.last_pairing_update_time
                        
                        seconds_until_starting_matter = 0
                        if self.adapter.should_start_matter_time > 0:
                            seconds_until_starting_matter = self.adapter.should_start_matter_time - int(time.time())
                            if seconds_until_starting_matter < 0:
                                seconds_until_starting_matter = 0
                       

                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({
                                      'debug': self.DEBUG,
                                      'certificates_updated': self.adapter.certificates_updated,
                                      'busy_updating_certificates': self.adapter.busy_updating_certificates,
                                      'discovered': self.adapter.discovered, # deprecated, but might be interesting to see if it's ever populated
                                      'busy_discovering': self.adapter.busy_discovering,
                                      'busy_pairing': self.adapter.busy_pairing,
                                      'pairing_failed': self.adapter.pairing_failed,
                                      'nodez': self.adapter.persistent_data['nodez'],
                                      'actual_interfaces':self.adapter.actual_interfaces,
                                      'matter_network_interface':self.adapter.persistent_data['matter_network_interface'],
                                      'actual_matter_network_interface':self.adapter.persistent_data['actual_matter_network_interface'],
                                      'available_interfaces':self.adapter.available_interfaces,
                                      'found_thread_radio_again': self.adapter.found_thread_radio_again,
                                      'found_new_thread_radio': self.adapter.found_new_thread_radio,
                                      'found_a_thread_radio_once': self.adapter.found_a_thread_radio_once,
                                      'thread_radio_went_missing': self.adapter.thread_radio_went_missing,
                                      'matter_server_type': self.adapter.matter_server_type,
                                      
                                      'onboarding_complete':self.adapter.persistent_data['onboarding_complete'],
                                      'missing_vendor_id': self.adapter.missing_vendor_id,
                                      'thread_radio_serial_port': self.adapter.persistent_data['thread_radio_serial_port'],
                                      'thread_error': self.adapter.thread_error,
                                      'thread_channel': self.adapter.thread_channel,
                                      'should_start_otbr':self.adapter.should_start_otbr,
                                      'otbr_started': self.adapter.otbr_started,
                                      'should_create_thread_mesh': self.adapter.should_create_thread_mesh,
                                      'should_start_thread_mesh':self.adapter.should_start_thread_mesh,
                                      'thread_dataset_loaded': self.adapter.thread_dataset_loaded,
                                      'help_thread_devices_to_connect_to_the_internet':self.adapter.help_thread_devices_to_connect_to_the_internet,
                                      'thread_netdata_registered':self.adapter.thread_netdata_registered,
                                      'thread_running': self.adapter.thread_running,
                                      'seconds_until_starting_matter':seconds_until_starting_matter,
                                      'matter_network_interface_found':self.adapter.matter_network_interface_found,
                                      'should_start_matter':self.adapter.should_start_matter,
                                      'matter_server_running':self.adapter.matter_server_running,
                                      'matter_client_connected': self.adapter.matter_client_connected,
                                      'matter_running':self.adapter.matter_running,

                                      'last_found_pairing_code': self.adapter.last_found_pairing_code,
                                      'wifi_congestion_data': self.adapter.wifi_congestion_data,
                                      'wifi_restore_countdown': wifi_restore_countdown,
                                      'thread_radio_is_alive_seconds_ago': thread_radio_is_alive_seconds_ago,
                                      'pairing_phase': self.adapter.pairing_phase,
                                      'pairing_activity_seconds_ago': pairing_activity_seconds_ago,
                                      'pairing_attempt': self.adapter.pairing_attempt,
                                      'pairing_phase_message': self.adapter.pairing_phase_message,
                                      'extension_cable_recommended': self.adapter.extension_cable_recommended,
                                      'last_received_server_info': self.adapter.last_received_server_info,
                                      'noise_delta': self.adapter.noise_delta,
                                      'timeout_delta': self.adapter.timeout_delta,
                                      'old_pairing_codes_count': len(self.adapter.persistent_data['pairing_codes'].keys()),
                                      'last_update_check_seconds_ago': last_update_check_seconds_ago,
                                      'last_update_check_response_seconds_ago': last_update_check_response_seconds_ago,
                                      'matter_collision_detected': self.adapter.matter_collision_detected,
                                      'thread_state_info':self.adapter.thread_state_info,
                                      'thread_netdata_info':self.adapter.thread_netdata_info,
                                      'has_thread_dataset':has_thread_dataset,
                                      'reconnected_devices':self.adapter.reconnected_devices
                                      
                                      })
                        )
                    
                        
                    # POLL used when pairing a new Matter device
                    elif action == 'poll':
                        if self.DEBUG:
                            print("API: in poll")
                        
                        code = ""
                        qr_json = ""
                        decoded_pairing_code = ""
                        
                        try:
                            uuid = str(request.body['uuid'])
                            parameters = {
                                        "action": "load",
                                        "uuid": uuid 
                                    }
                       
                            if self.DEBUG:
                                print("poll: doing request to candle webserver. parameters: " + str(parameters))
                            
                            q = requests.post( "https://www.candlesmarthome.com/qr/ajax.php", data = parameters )
                            #if self.DEBUG:
                            #    print("q.content = " + str(q.content))
                            #    print("q.json = " + str(q.json))
                            if len(str(q.content)) > 4:
                                qr_json = q.json()
                                if self.DEBUG:
                                    print("qr_json: ", qr_json)
                                
                                if 'code' in qr_json:
                                    code = qr_json['code']
                                    self.adapter.last_found_pairing_code = str(code)
                                    try:
                                        decoded_pairing_code = self.adapter.parse_mt_pairing_code(str(code))
                                        if self.DEBUG:
                                            print('decoded_pairing_code: ', decoded_pairing_code)
                                    except Exception as ex:
                                        if self.DEBUG:
                                            print("caught error trying to unpack matter pairing code: ", ex)
                                            print(traceback.format_exc())
                                    
                                    
                                else:
                                    if self.DEBUG:
                                        print('no code in post json: ', q.content)
                            else: 
                                if self.DEBUG:
                                    print('Matter adapter debug: poll: response not long enough')
                            #if not self.adapter.busy_pairing:
                                
                        
                        except Exception as ex:
                            if self.DEBUG:
                                print("Error doing post request for pairing code from QR scanner: " + str(ex))
                            code = "error"
                        
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({
                                      'debug': self.DEBUG,
                                      'certificates_updated': self.adapter.certificates_updated,
                                      'busy_updating_certificates':self.adapter.busy_updating_certificates,
                                      'matter_client_connected': self.adapter.matter_client_connected,
                                      'discovered': self.adapter.discovered, # deprecated, but might be interesting to see if it's ever populated
                                      'busy_discovering':self.adapter.busy_discovering,
                                      'pairing_code': code,
                                      'decoded_pairing_code': str(decoded_pairing_code).splitlines(),
                                      'busy_pairing':self.adapter.busy_pairing,
                                      'pairing_failed':self.adapter.pairing_failed,
                                      'nodez': self.adapter.persistent_data['nodez'],
                                      'pairing_phase':self.adapter.pairing_phase,
                                      'pairing_attempt': self.adapter.pairing_attempt,
                                      'pairing_phase_message':self.adapter.pairing_phase_message,
                                      }),
                        )
                        
                    


                    elif action == 'get_map':
                        if self.DEBUG:
                            print("got request to get_map")
                        state = False
                        eid_cache = {}
                        my_rloc16 = None
                        my_extaddr = None
                        my_neighbortable = []

                        #self.adapter.get_diagnostics()
                        #time.sleep(1)
                        
                        try:
                            eid_cache_check = self.adapter.run_ot_ctl_command('eidcache')
                            rloc16_check = self.adapter.run_ot_ctl_command('rloc16')
                            extaddr_check = self.adapter.run_ot_ctl_command('extaddr')
                            neighbortable_check = self.adapter.run_ot_ctl_command('neighbor table')
                            if isinstance(eid_cache_check,str) and isinstance(rloc16_check,str) and isinstance(neighbortable_check,str) and isinstance(extaddr_check,str):
                                
                                for line in eid_cache_check.splitlines():
                                    line_parts = line.split(' ')
                                    if self.DEBUG:
                                        print("get_map: eid_cache line_parts: ", line_parts)
                                    if len(line_parts) > 2:
                                        eid_cache[line_parts[0]] = line_parts[1]
                                if self.DEBUG:
                                    print("eid_cache: ", eid_cache)

                                for line in neighbortable_check.splitlines():
                                    if '0x' in line:
                                        line_parts = line.split('|')
                                        if self.DEBUG:
                                            print("get_map: neighbortable line_parts: ", line_parts)
                                        if len(line_parts) > 6:
                                            if str(line_parts[6]).strip().isdigit():
                                                my_neighbortable.append({"rloc16":str(line_parts[2]).strip().replace('0x',''), "lqi":int(line_parts[6].strip())})
                                            else:
                                                if self.DEBUG:
                                                    print("get_map: neighbortable line_parts 6 (LQI) was not a digit: -->" + str(line_parts[6]).strip() + "<--")
                                if self.DEBUG:
                                    print("my_neighbortable: ", my_neighbortable)

                                my_rloc16 = str(rloc16_check).replace('Done','').rstrip().strip()
                                if self.DEBUG:
                                    print("my_rloc16: -->" + str(my_rloc16) + "<--")

                                my_extaddr = str(extaddr_check).replace('Done','').rstrip().strip()
                                my_extaddr = int(my_extaddr, 16) # hex to dec
                                if self.DEBUG:
                                    print("my_extaddr: -->" + str(my_extaddr) + "<--")

                                state = True

                        except Exception as ex:
                            print("caught error handling get_map request: ", ex)
                        

                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({
                            'state':state,
                            'thread_diagnostics': self.adapter.thread_diagnostics,
                            'general_diagnostics': self.adapter.general_diagnostics,
                            'eid_cache':eid_cache,
                            'my_rloc16':my_rloc16,
                            'my_extaddr':my_extaddr,
                            'my_neighbortable':my_neighbortable
                          }),
                        )

                    elif action == 'check_for_updates':
                        state = False
                        if self.DEBUG:
                            print("got request to check_for_updates")
                        try:
                            if self.adapter.matter_client_connected and (self.adapter.last_matter_update_check_timestamp < time.time() - 300 or (self.DEBUG and self.adapter.last_matter_update_check_timestamp < time.time() - 10)):
                                self.adapter.last_matter_update_check_timestamp = int(time.time())
                                self.adapter.check_for_node_updates()
                                state = True
                        except Exception as ex:
                            print("caught error handling check_for_updates request: ", ex)
                        

                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({
                            'state':state
                          }),
                        )

                    elif action == 'update_node':
                        state = False
                        
                        try:
                            if 'node_id' in request.body and str(request.body['node_id']) != '':
                                if self.DEBUG:
                                    print("got request to update_node: ", request.body['node_id'])
                                self.adapter.update_node(int(request.body['node_id']))
                                state = True
                        except Exception as ex:
                            print("caught error handling update_node request: ", ex)
                        

                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({
                            'state':state
                          }),
                        )


                    


                    # DISCOVER
                    # does a scan for pairable devices. Currently not used.
                    elif action == 'discover':
                        if self.DEBUG:
                            print("\n\nAPI: in discover")
                        state = False
                        
                        code = ""
                        
                        try:
                            state = self.adapter.discover()
                            if state == True:
                                time.sleep(5)
                        except Exception as ex:
                            if self.DEBUG:
                                print("Error in discover request: " + str(ex))
                                print(traceback.format_exc())
                        
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({
                            'state':state,
                            'discovering':self.adapter.busy_discovering,
                            'discovered':self.adapter.discovered
                          })
                        )
                    
                    
                    elif action == 'find_thread_radio_before':
                        state = True
                        if os.path.isdir('/dev/serial/by-id'):
                            self.adapter.serial_before = str(run_command('ls /dev/serial/by-id'))
                            #state = True
                        else:
                            self.adapter.serial_before = ''
                        if self.DEBUG:
                            print("find_thread_radio_before: self.adapter.serial_before: ", self.adapter.serial_before)
                            if self.adapter.persistent_data['thread_radio_serial_port'] != None:
                                print("find_thread_radio_before: WARNING, setting persistent_data['thread_radio_serial_port'] to None from: ", self.adapter.persistent_data['thread_radio_serial_port'])
                        self.adapter.persistent_data['thread_radio_serial_port'] = None

                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state':state,'serial_before':self.adapter.serial_before}),
                        )
                    
                    elif action == 'find_thread_radio':
                        self.adapter.find_thread_radio()
                        time.sleep(3)
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state':self.adapter.found_new_thread_radio,'thread_radio_serial_port':self.adapter.persistent_data['thread_radio_serial_port']}),
                        )


                    elif action == 'get_thread_network_code':
                        state = False
                        thread_dataset = ''
                        if 'thread_dataset' in self.adapter.persistent_data and isinstance(self.adapter.persistent_data['thread_dataset'],str) and len(self.adapter.persistent_data['thread_dataset']) > 40:
                            thread_dataset = self.adapter.persistent_data['thread_dataset']
                            state = True
                        
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({
                                'state':state,
                                'thread_network_code':thread_dataset
                                })
                        )
                    

                    elif action == 'save_thread_network_code':
                        state = False
                        if self.DEBUG:
                            print("handling requested action: save_thread_network_code")

                        try:
                            if 'code' in request.body:
                                provided_thread_network_code = str(request.body['code'])
                                if len(provided_thread_network_code) > 40:
                                    if self.DEBUG:
                                        print("save_thread_network_code: provided Thread network code is long enough")
                                    
                                    if 'thread_dataset' in self.adapter.persistent_data and str(provided_thread_network_code) == str(self.adapter.persistent_data['thread_dataset']):
                                        if self.DEBUG:
                                            print("save_thread_network_code: provided Thread network code is the same as the existing one")
                                        state = True
                                    
                                    else:
                                        if self.adapter.thread_running == True or self.adapter.otbr_started == True:
                                            print(str(self.adapter.run_ot_ctl_command('thread stop')))
                                            print(str(self.adapter.run_ot_ctl_command('ifconfig down')))
                                            """
                                            if self.DEBUG:
                                                print("save_thread_network_code: stopping OTBR first")
                                            if self.adapter.really_stop_otbr():
                                                if self.DEBUG:
                                                    print("save_thread_network_code: OTBR stopped succesfully")
                                                time.sleep(2)
                                                self.adapter.thread_dataset = provided_thread_network_code
                                                self.adapter.persistent_data['thread_dataset'] = provided_thread_network_code
                                                self.adapter.save_persistent_data()
                                                state = True
                                            else:
                                                if self.DEBUG:
                                                    print("\nERROR, save_thread_network_code:  calling save_thread_network_code returned false")
                                            """
                                        #else:

                                        
                                        self.adapter.import_thread_dataset(provided_thread_network_code)

                                        self.adapter.thread_dataset = str(provided_thread_network_code)
                                        self.adapter.persistent_data['thread_dataset'] = str(provided_thread_network_code)
                                        self.adapter.save_persistent_data()
                                        state = True

                                        if state == True:
                                            self.adapter.last_time_otbr_restarted = 0
                                            self.adapter.should_start_otbr = True
                                            self.adapter.otbr_starting_timestamp = None
                                            self.adapter.tell_matter_about_thread_dataset()


                        except Exception as ex:
                            print("caught error handling save_thread_network_code API request: ", ex)

                        
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state':state}),
                        )
                    

                    elif action == 'save_vendor_id':
                        if self.DEBUG:
                            print("got request to save_vendor_id")
                    
                        try:
                            if 'vendor_id' in request.body and isinstance(str(request.body['vendor_id']),str):
                                new_vendor_id = request.body['vendor_id']
                                if len(new_vendor_id) == 4:
                                    if isinstance(self.adapter.persistent_data['vendor_id'],str) and len(self.adapter.persistent_data['vendor_id']) == 4 and self.adapter.persistent_data['vendor_id'] != new_vendor_id:
                                        if self.DEBUG:
                                            print("WARNING, VENDOR ID IS BEING CHANGED FROM: ", self.adapter.persistent_data['vendor_id'], ", TO: ", new_vendor_id);
                                    self.adapter.persistent_data['vendor_id'] = new_vendor_id
                                    #self.adapter.vendor_id = new_vendor_id
                                    self.adapter.check_onboarding_state()
                                    self.adapter.should_save = True
                                    state = True

                        except Exception as ex:
                            print("caught error handling save_vendor_id API request: ", ex)

                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state':state}),
                        )

                    elif action == 'save_matter_network_interface':
                        if self.DEBUG:
                            print("got request to save_matter_network_interface")
                    
                        try:
                            if 'matter_network_interface' in request.body and isinstance(str(request.body['matter_network_interface']),str):
                                if self.DEBUG:
                                    print("matter_network_interface has been set to: ", self.adapter.persistent_data['matter_network_interface']);
                                self.adapter.persistent_data['matter_network_interface'] = request.body['matter_network_interface']
                                if request.body['matter_network_interface'] == 'Advanced' and 'actual_matter_network_interface' in request.body and isinstance(str(request.body['actual_matter_network_interface']),str):
                                    self.adapter.persistent_data['actual_matter_network_interface'] = request.body['actual_matter_network_interface']
                                self.adapter.update_network_interfaces()
                                self.adapter.check_onboarding_state()
                                self.adapter.should_save = True
                                state = True
                                    
                        except Exception as ex:
                            print("caught error handling save_matter_network_interface API request: ", ex)

                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state':state, 'onboarding_complete':self.adapter.persistent_data['onboarding_complete']}),
                        )


                    elif action == 'run_otbr_command':
                        output = ''
                        try:
                            if 'command' in request.body:
                                if self.DEBUG:
                                    print("debug: running OTBR command: ", str(request.body['command']))
                                output = str(self.adapter.run_ot_ctl_command(str(request.body['command'])))
                                if self.DEBUG:
                                    print("debug: OTBR command output: ", output)
                                if 'connect session failed: No such file or directory' in output:
                                    output = 'OTBR agent is not running'

                        except Exception as ex:
                            if self.DEBUG:
                                print("caught error running OTBR command: ", ex)
                            output = ''

                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'output':output}),
                        )


                    elif action == 'run_chip_command':
                        output = ''
                        try:
                            if 'command' in request.body:
                                if self.DEBUG:
                                    print("debug: running CHIP TOOL command: ", str(request.body['command']))
                                output = str(self.adapter.run_chip_tool_command(str(request.body['command'])))
                                if self.DEBUG:
                                    print("debug: CHIP TOOL command output: ", output)
                                #if 'connect session failed: No such file or directory' in output:
                                #    output = 'CHIP TOOL is not available'

                        except Exception as ex:
                            if self.DEBUG:
                                print("caught error running CHIP TOOL command: ", ex)
                            output = ''

                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'output':output}),
                        )


                    elif action == 'import_pairing_codes':
                        state = False
                        try:
                            if 'pairing_codes' in request.body:
                                if self.DEBUG:
                                    print("debug: importing pairing_codes: ", str(request.body['pairing_codes']))
                                self.adapter.persistent_data['pairing_codes'] = request.body['pairing_codes']
                                self.adapter.should_save = True
                                state = True

                        except Exception as ex:
                            if self.DEBUG:
                                print("caught error handling import_pairing_codes request: ", ex)
                            

                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state':state}),
                        )
                    
                    
                    
                    # START NORMAL PAIRING
                    elif action == 'start_pairing':
                        if self.DEBUG:
                            print("\n\nAPI: debug: in start_pairing. request.body: " + str(request.body))
                        state = False
                        self.adapter.pairing_failed = False
                        code = ""
                        
                        try:
                            if 'pairing_type' in request.body and 'code' in request.body and 'wireless_type' in request.body:
                                wireless_type = str(request.body['wireless_type'])
                                if self.DEBUG:
                                    print("raw wireless_type: ", wireless_type)
                                if wireless_type.lower() == 'thread':
                                    self.adapter.wireless_type = 'thread'
                                elif wireless_type.lower() == 'wifi':
                                    self.adapter.wireless_type = 'wifi'
                                else:
                                    self.adapter.wireless_type = 'unknown'
                                
                                pairing_type = str(request.body['pairing_type'])
                                code = request.body['code']
                                
                                
                                # commission_with_code
                                if pairing_type == 'commission_with_code' or pairing_type == 'commission_on_network':
                                    if 'wifi_ssid' in request.body and 'wifi_password' in request.body and 'wifi_remember' in request.body:
                                        if self.DEBUG:
                                            print("OK all required parameters were provided")
                                            
                                        if len(str(request.body['wifi_password'])) > 7:
                                            self.adapter.wifi_ssid = str(request.body['wifi_ssid']).rstrip()
                                            self.adapter.wifi_password = str(request.body['wifi_password']).rstrip()
                                            if self.DEBUG:
                                                print("self.adapter.wifi_ssid: " + str(self.adapter.wifi_ssid))
                                                print("self.adapter.wifi_password: " + str(self.adapter.wifi_password))
                                            if request.body['wifi_remember'] == True:
                                                if self.DEBUG:
                                                    print("Remembering wifi credentials")
                                                self.adapter.persistent_data['wifi_ssid'] = str(request.body['wifi_ssid'])
                                                self.adapter.persistent_data['wifi_password'] = str(request.body['wifi_password'])
                                                self.adapter.should_save = True
                                    
                                
                                if pairing_type == 'commission_with_code':
                                    
                                    if code and isinstance(code,str) and (len(code) > 10 and code.startswith('MT:') or (len(code) > 6 and code.isdigit())):
                                        if self.DEBUG:
                                            print("start_matter_pairing: setting last_found_pairing_code to: ", code)
                                        self.adapter.last_found_pairing_code = code
        
                                        self.adapter.last_decoded_pairing_code = self.adapter.parse_mt_pairing_code(str(self.adapter.last_found_pairing_code))
                                        if self.DEBUG:
                                            print('start_matter_pairing: setting self.last_decoded_pairing_code: \n\n', self.adapter.last_decoded_pairing_code, '\n\n')
                                    
                                    
                                        #device = request.body['device']
                                        self.adapter.pairing_attempt = -1
                                        self.adapter.pairing_phase = 0
                                        self.adapter.pairing_phase_message = 'Preparing..'
                                        state = self.adapter.start_matter_pairing(pairing_type) # device data isn't really needed, CHIP brute-force scans all devices on the network.
                                        if self.DEBUG:
                                            print("API handler got request to commission_with_code. self.adapter.start_matter_pairing returned this state: ", state)
                                # commission_on_network
                                elif pairing_type == 'commission_on_network':
                                     if code and isinstance(code,str):
                                         self.adapter.last_found_pin_code = code
                                         
                                         self.adapter.pairing_attempt = -1
                                         self.adapter.pairing_phase = 0
                                         self.adapter.pairing_phase_message = 'Preparing onboarding..'
                                         state = self.adapter.start_matter_pairing(pairing_type) # device data isn't really needed, CHIP brute-force scans all devices on the network.
                                
                                else:
                                    if self.DEBUG:
                                        print("unsupported pairing type")
                               
                                #else:
                                #    if self.DEBUG:
                                #        print("OK all required parameters were provided")
                                
                                
                            else:
                                if self.DEBUG:
                                    print("\n\n\nERROR, NOT ALL PARAMETERS FOR PAIRING WERE PROVIDED")
                        
                        except Exception as ex:
                            if self.DEBUG:
                                print("Error in start_pairing request: " + str(ex))
                                print(traceback.format_exc())
                        
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state':state}),
                        )
                    
                    

                    
                    
                    # Reset pairing
                    elif action == 'reset_pairing':
                        if self.DEBUG:
                            print("\n\nAPI: in reset_pairing")
                        
                        if self.adapter.busy_pairing and self.adapter.pairing_attempt != -1:
                            self.adapter.pairing_attempt = 100
                        else:
                            self.adapter.pairing_attempt = -1
                        self.adapter.busy_pairing = False
                        self.adapter.pairing_failed = False
                        #self.adapter.pairing_code = ""
                        self.adapter.pairing_phase = 0
                        
                        self.adapter.pairing_phase_message = 'Starting pairing process'
                        
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state':True}),
                        )
                    
                    
                    elif action == 'reset_customizations':
                        if self.DEBUG:
                            print("\n\nAPI: in reset_customizations")
                        
                        self.adapter.persistent_data['nodez'] = {}
                        self.adapter.get_nodes()
                        self.adapter.should_save = True
                        
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state':True}),
                        )
                    
                    elif action == 'reset_thread':
                        if self.DEBUG:
                            print("\n\nAPI: in reset_thread")
                        
                        #self.adapter.persistent_data['nodez'] = {}
                        #self.adapter.get_nodes()
                        self.adapter.reset_thread()
                        time.sleep(1)
                        #self.adapter.should_save = True
                        
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state':True}),
                        )

                    elif action == 'reset_matter':
                        if self.DEBUG:
                            print("\n\nAPI: in reset_matter")
                        
                        #self.adapter.persistent_data['nodez'] = {}
                        #self.adapter.get_nodes()
                        self.adapter.reset_matter()
                        time.sleep(1)
                        #self.adapter.should_save = True
                        
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state':True}),
                        )
                        
                    
                    elif action == 'change_attribute':
                        if self.DEBUG:
                            print("API: in change_attribute")
                        state = False
                        
                        try:
                            thing_id = str(request.body['thing_id'])
                            endpoint_name = str(request.body['endpoint_name'])
                            if not 'attribute_code' in request.body:
                                if self.DEBUG:
                                    print("ERROR: change_attribute: missing attribute_code")
                            attribute_code = str(request.body['attribute_code'])
                            attribute = str(request.body['attribute'])
                            value = request.body['value']
                            path = ''
                            if 'path' in request.body:
                                path = request.body['path']
                                
                            if self.DEBUG:
                                print("- thing_id: ", thing_id)
                                print("- endpoint_name: ", endpoint_name)
                                print("- attribute_code: ", attribute_code)
                                print("- path: ", path)
                                print("- attribute: ", attribute)
                                print("- value: ", value)
                                
                            if value != None and thing_id in self.adapter.persistent_data['nodez']:
                                if thing_id in self.adapter.persistent_data['nodez']:
                                    if 'attributes' in self.adapter.persistent_data['nodez'][thing_id]:
                                        if endpoint_name in self.adapter.persistent_data['nodez'][thing_id]['attributes']:
                                            if attribute_code in self.adapter.persistent_data['nodez'][thing_id]['attributes'][endpoint_name]:
                                                if path == '':
                                                    if not 'customizations' in self.adapter.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][attribute_code]:
                                                        self.adapter.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][attribute_code]['customizations'] = {}
                                                    self.adapter.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][attribute_code]['customizations'][attribute] = value
                                                    if self.DEBUG:
                                                        print("attribute set.\nAttempting to reparse thing..")
                                                    if attribute == 'enabled':
                                                        self.adapter.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][attribute_code]['enabled'] = bool(value)
                                                        target_device = self.adapter.get_device(thing_id)
                                                        if target_device:
                                                            state = target_device.reparse_node()
                                                        else:
                                                            if self.DEBUG:
                                                                print("change_attribute could not find the target_device from thing_id: ", thing_id)
                                                            state = False
                                                    else:
                                                        state = True
                                                    
                                                elif path == 'description' and 'property' in self.adapter.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][attribute_code]:
                                                    if not 'description_customizations' in self.adapter.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][attribute_code]['property']:
                                                        self.adapter.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][attribute_code]['property']['description_customizations'] = {}
                                                        
                                                    self.adapter.persistent_data['nodez'][thing_id]['attributes'][endpoint_name][attribute_code]['property']['description_customizations'][attribute] = value
                                                    if self.DEBUG:
                                                        print("attribute set.\nAttempting to reparse thing..")
                                                    target_device = self.adapter.get_device(thing_id)
                                                    if target_device:
                                                        state = target_device.reparse_node()
                                                    else:
                                                        if self.DEBUG:
                                                            print("change_attribute could not find the target_device from thing_id: ", thing_id)
                                                        state = False
                                                    
                                                    
                                                    
                                                    
                        except Exception as ex:
                            if self.DEBUG:
                                print("caught error in change_attibute: ", ex)
                                print(traceback.format_exc())
                        
                        if self.DEBUG:
                            print("change_attribute: final state: ", state)
                        
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state':state}),
                        )
                        
                        
                    
                    
                    
                    # DELETE
                    elif action == 'delete_node':
                        if self.DEBUG:
                            print("API: in delete_node")
                        
                        state = False
                        message = "An unknown error has occured."
                        thing_id = None
                        self.adapter.device_was_deleted = False
                        try:

                            # REMOVE THE THING
                            node_id = str(request.body['node_id'])

                            for existing_thing_id in self.adapter.persistent_data['nodez'].keys():
                                if 'node_id' in self.adapter.persistent_data['nodez'][existing_thing_id] and self.adapter.persistent_data['nodez'][existing_thing_id]['node_id'] == node_id:
                                    thing_id = existing_thing_id
                                    if self.DEBUG:
                                        print("API: delete_node: found existing thing_id with the node_id: ", thing_id)
                                    break
                            #if node_id.startswith('matter-'):
                            #    node_id = node_id.replace('matter-','')
                            #thing_id = 'matter-' + str(node_id)
                        
                            

                            #state = self.delete_item(name) # This method returns True if deletion was succesful
                            if isinstance(thing_id,str):
                                if self.DEBUG:
                                    print("API: delete_node: asking adapter to remove thing_id: ", thing_id)
                                self.adapter.remove_thing(thing_id)
                                
                                if thing_id in self.adapter.persistent_data['nodez']:
                                    if self.DEBUG:
                                        print("API: delete_node: removing thing from persistent_data with thing_id: ", thing_id)
                                    del self.adapter.persistent_data['nodez'][thing_id]
                                    self.adapter.should_save = True

                                # Remove Device object from the adapter
                                #old_device = self.adapter.get_device(thing_id)
                                #if old_device != None:
                                #    if self.DEBUG:
                                #        print("removing thing from adapter")
                                #    
                                #else:
                                #    if self.DEBUG:
                                #        print("Warning, thing was not present on adapter? Cannot delete thing.")
                                
                                # Remove the device from the nodez dictionary
                                """
                                if thing_id in self.adapter.persistent_data['nodez']:
                                    if self.DEBUG:
                                        print("removing thing from nodez")
                                    del self.adapter.persistent_data['nodez'][thing_id]
                                    message += " Also deleted from persistent data"
                                    #state = True
                                else:
                                    if self.DEBUG:
                                        print("thing_id was not found in nodez. Already deleted?: " + str(thing_id))
                                    message = "Device was not present in data - already deleted?"
                                    if self.DEBUG:
                                        print("Error: " + message)
                                """
                        except Exception as ex:
                            if self.DEBUG:
                                print("Error deleting from nodez of things: " + str(ex))
                                print(traceback.format_exc())
                            
                        try:
                            #if node_id in self.adapter.nodes:
                            state = self.adapter.remove_node(node_id)
                            
                            # TODO: check how long this actually takes
                            if self.adapter.device_was_deleted == False:
                                time.sleep(3) #Could this be blocking the web interface?
                            if self.adapter.device_was_deleted == False:
                                time.sleep(3)
                            if self.adapter.device_was_deleted == False:
                                time.sleep(3)
                                
                            if self.adapter.device_was_deleted == False:
                                message = "Deletion may have failed; it took longer than 9 seconds."
                            else:
                                message = "Device was succesfully removed."
                                state = True
                            if self.DEBUG:
                                print("delete action final message: " + str(message))
                                
                            
                        except Exception as ex:
                            if self.DEBUG:
                                print("caught error deleting node from Matter: " + str(ex))
                                print(traceback.format_exc())
                        
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state' : state, 
                                              'message':message, 
                                              'device_was_deleted':self.adapter.device_was_deleted, # TODO: hacky solution
                                              'nodez':self.adapter.persistent_data['nodez']
                                          }),
                        )
                    

                    
                    elif action == 'share_node':
                        if self.DEBUG:
                            print("API: in share_node")
                        
                        self.adapter.pairing_failed = False
                        self.adapter.share_node_code = ""
                        message = "Failed to share the device"
                        state = False
                        
                        try:
                            node_id = str(request.body['node_id'])
                            
                            state = self.adapter.share_node(node_id)
                            
                            time.sleep(4)
                            if self.adapter.share_node_code == "":
                                time.sleep(4)
                            if self.adapter.share_node_code == "":
                                time.sleep(4)
                            if self.adapter.share_node_code != "":
                                message = "You can now pair the device (for 60 seconds)"
                                state = True
                        except Exception as ex:
                            if self.DEBUG:
                                print("cacught error in share_node: " + str(ex))
                                print(traceback.format_exc())
                        
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state':state, 
                                              'message':message, 
                                              'pairing_code':self.adapter.share_node_code
                                          }),
                        )
                    

                    elif action == 'refresh_node':
                        if self.DEBUG:
                            print("API: in refresh_node")
                        
                        state = False
                        
                        try:
                            node_id = str(request.body['node_id'])
                            for existing_thing_id in self.adapter.persistent_data['nodez'].keys():
                                if 'node_id' in self.adapter.persistent_data['nodez'][existing_thing_id] and self.adapter.persistent_data['nodez'][existing_thing_id]['node_id'] == node_id:
                                    thing_id = existing_thing_id
                                    if self.DEBUG:
                                        print("API: refresh_node: found existing thing_id based on the node_id: ", node_id, " -> ", thing_id)
                                    
                                    if thing_id in self.adapter.persistent_data['nodez']:
                                        if self.DEBUG:
                                            print("API: refresh_node: removing thing from persistent_data with thing_id: ", thing_id)
                                        del self.adapter.persistent_data['nodez'][thing_id]
                                        self.adapter.should_save = True
                                        state = True

                                    break
                            
                        except Exception as ex:
                            if self.DEBUG:
                                print("caught error in refresh_node: " + str(ex))
                                print(traceback.format_exc())
                        
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state':state}),
                        )
                    







                    elif action == 'get_mdns':
                        self.adapter.raw_mdns = str(run_command('avahi-browse -rt _trel._udp'))
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state':state, 
                                              'raw_mdns':self.adapter.raw_mdns
                                          }),
                        )
                        
                    # To minimize security risks this data must be explicitly requested
                    elif action == 'get_old_pairing_codes':
                        if self.DEBUG:
                            print("handling request get_old_pairing_codes")
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state':True, 
                                              'old_pairing_codes':self.adapter.persistent_data['pairing_codes']
                                          }),
                        )
                    
                    
                    
                    else:
                        if self.DEBUG:
                            print("Error, that action is not possible")
                        return APIResponse(
                            status=404
                        )
                        
                        
                        
                except Exception as ex:
                    if self.DEBUG:
                        print("Ajax error: " + str(ex))
                        print(traceback.format_exc())
                    return APIResponse(
                        status=500,
                        content_type='application/json',
                        content=json.dumps({"error":"Error in API handler"}),
                    )
                    
            else:
                if self.DEBUG:
                    print("invalid path: " + str(request.path))
                return APIResponse(status=404)
                
        except Exception as e:
            if self.DEBUG:
                print("Failed to handle UX extension API request: " + str(e))
            return APIResponse(
                status=500,
                content_type='application/json',
                content=json.dumps({"error":"General API error"}),
            )

