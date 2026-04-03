"""
Matter addon for Candle Controller.
"""


import os
#os.path.insert(1, dirname(os.path.dirname(os.path.abspath(__file__))))
import sys
# This helps the addon find python libraries it comes with, which are stored in the "lib" folder. The "package.sh" file will download Python libraries that are mentioned in requirements.txt and place them there.
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')) 

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
        print("INSIDE API HANDLER INIT")
        
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
                            print("API: in init")
                        
                        self.adapter.get_nodes()
                        time.sleep(5)
                        
                        wifi_credentials_available = False
                        if self.adapter.wifi_ssid != "" and self.adapter.wifi_password != "":
                            wifi_credentials_available = True
                        
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({
                                      'debug': self.adapter.DEBUG,
                                      'use_hotspot': self.adapter.use_hotspot,
                                      'hotspot_addon_installed': self.adapter.hotspot_addon_installed,
                                      'wifi_ssid': self.adapter.wifi_ssid,
                                      'wifi_credentials_available': wifi_credentials_available,
                                      'client_connected': self.adapter.client_connected,
                                      #'nodes': self.adapter.nodes,
                                      'nodez': self.adapter.persistent_data['nodez']
                                      }),
                        )
                        
                        
                    
                    # MAIN POLL
                    elif action == 'get_main_poll':
                        
                        wifi_restore_countdown = 0;
                        if self.adapter.turn_wifi_back_on_at != 0:
                            if self.DEBUG:
                                print("get_main_poll: self.adapter.turn_wifi_back_on_at: ", self.adapter.turn_wifi_back_on_at)
                            wifi_restore_countdown = round(self.adapter.turn_wifi_back_on_at - time.time())
                            if self.DEBUG:
                                print("get_main_poll: wifi_restore_countdown: ", wifi_restore_countdown)
                            if wifi_restore_countdown < 0:
                                wifi_restore_countdown = 0
                        
                        
                        thread_radio_is_alive_seconds_ago = None
                        if isinstance(self.adapter.last_thread_radio_is_alive_timestamp,int) and self.adapter.last_thread_radio_is_alive_timestamp != 0:
                            thread_radio_is_alive_seconds_ago = int(time.time()) - self.adapter.last_thread_radio_is_alive_timestamp;
                        
                        if wifi_restore_countdown != 0:
                            if self.DEBUG:
                                print("API: debug: get_main_poll:  wifi_restore_countdown: ", wifi_restore_countdown)
                        
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({
                                      'debug': self.adapter.DEBUG,
                                      'certificates_updated': self.adapter.certificates_updated,
                                      'busy_updating_certificates': self.adapter.busy_updating_certificates,
                                      'client_connected': self.adapter.client_connected,
                                      'discovered': self.adapter.discovered, # deprecated, but might be interesting to see if it's ever populated
                                      'busy_discovering': self.adapter.busy_discovering,
                                      'busy_pairing': self.adapter.busy_pairing,
                                      'pairing_failed': self.adapter.pairing_failed,
                                      'nodez': self.adapter.persistent_data['nodez'],
                                      'found_thread_radio_again': self.adapter.found_thread_radio_again,
                                      'found_new_thread_radio': self.adapter.found_new_thread_radio,
                                      'found_a_thread_radio': self.adapter.found_a_thread_radio_once,
                                      'thread_radio_went_missing': self.adapter.thread_radio_went_missing,
                                      'otbr_started': self.adapter.otbr_started,
                                      'thread_running': self.adapter.thread_running,
                                      'thread_error': self.adapter.thread_error,
                                      'last_found_pairing_code': self.adapter.last_found_pairing_code,
                                      'client_connected': self.adapter.client_connected,
                                      'wifi_congestion_data': self.adapter.wifi_congestion_data,
                                      'wifi_restore_countdown': wifi_restore_countdown,
                                      'thread_radio_is_alive_seconds_ago': thread_radio_is_alive_seconds_ago,
                                      'pairing_phase': self.adapter.pairing_phase,
                                      'pairing_attempt': self.adapter.pairing_attempt,
                                      'pairing_phase_message':self.adapter.pairing_phase_message,
                                      'extension_cable_recommended': self.adapter.extension_cable_recommended,
                                      'last_received_server_info':self.adapter.last_received_server_info,
                                      'noise_delta':self.adapter.noise_delta,
                                      'thread_diagnostics':self.adapter.thread_diagnostics,
                                      'thread_radio_serial_port': self.adapter.persistent_data['thread_radio_serial_port']
                                      }),
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
                       
                            if self.adapter.DEBUG:
                                print("poll: doing request to candle webserver. parameters: " + str(parameters))
                            
                            q = requests.post( "https://www.candlesmarthome.com/qr/ajax.php", data = parameters )
                            #if self.adapter.DEBUG:
                            #    print("q.content = " + str(q.content))
                            #    print("q.json = " + str(q.json))
                            if len(str(q.content)) > 4:
                                qr_json = q.json()
                                if self.adapter.DEBUG:
                                    print("qr_json: ", qr_json)
                                
                                if 'code' in qr_json:
                                    code = qr_json['code']
                                    self.adapter.last_found_pairing_code = str(code)
                                    try:
                                        decoded_pairing_code = self.adapter.parse_mt_pairing_code(str(code))
                                        if self.adapter.DEBUG:
                                            print('decoded_pairing_code: ', decoded_pairing_code)
                                    except Exception as ex:
                                        print("caught error trying to unpack matter pairing code: ", ex)
                                        print(traceback.format_exc())
                                    
                                    
                                else:
                                    if self.adapter.DEBUG:
                                        print('no code in post json: ', q.content)
                            else: 
                                if self.adapter.DEBUG:
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
                                      'debug': self.adapter.DEBUG,
                                      'certificates_updated': self.adapter.certificates_updated,
                                      'busy_updating_certificates':self.adapter.busy_updating_certificates,
                                      'client_connected': self.adapter.client_connected,
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
                        
                        
                    # DISCOVER
                    # does a scan for pairable devices. Currently not used.
                    elif action == 'discover':
                        if self.DEBUG:
                            print("\n\nAPI: in discover")
                        state = False
                        
                        code = ""
                        
                        try:
                            state = self.adapter.discover()
                        except Exception as ex:
                            if self.DEBUG:
                                print("Error in discover request: " + str(ex))
                                print(traceback.format_exc())
                        
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state':state}),
                        )
                    
                    
                    elif action == 'find_thread_radio_before':
                        self.adapter.serial_before = str(run_command('ls /dev/serial/by-id'))
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state':True}),
                        )
                    
                    elif action == 'find_thread_radio':
                        self.adapter.find_thread_radio()
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state':self.adapter.found_new_thread_radio}),
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
                                                self.adapter.should_save_persistent = True
                                    
                                
                                if pairing_type == 'commission_with_code':
                                    
                                    if code and isinstance(code,str) and len(code) > 10 and code.startswith('MT:'):
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
                    
                    elif action == 'reset_matter':
                        if self.DEBUG:
                            print("\n\nAPI: in reset_matter")
                        
                        self.adapter.persistent_data['nodez'] = {}
                        self.adapter.get_nodes()
                        self.adapter.reset_matter()
                        self.adapter.should_save = True
                        
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
                    elif action == 'delete':
                        if self.DEBUG:
                            print("API: in delete")
                        
                        state = False
                        message = "An unknown error has occured."
                        self.adapter.device_was_deleted = False
                        try:
                            node_id = str(request.body['node_id'])
                            if node_id.startswith('matter-'):
                                node_id = node_id.replace('matter-','')
                            device_id = 'matter-' + str(node_id)
                            #state = self.delete_item(name) # This method returns True if deletion was succesful
                            
                            self.adapter.remove_thing(device_id)
                            
                            # Remove Device object from the adapter
                            #old_device = self.adapter.get_device(device_id)
                            #if old_device != None:
                            #    if self.DEBUG:
                            #        print("removing thing from adapter")
                            #    
                            #else:
                            #    if self.DEBUG:
                            #        print("Warning, thing was not present on adapter? Cannot delete thing.")
                            
                            # Remove the device from the nodez dictionary
                            """
                            if device_id in self.adapter.persistent_data['nodez']:
                                if self.DEBUG:
                                    print("removing thing from nodez")
                                del self.adapter.persistent_data['nodez'][device_id]
                                message += " Also deleted from persistent data"
                                #state = True
                            else:
                                if self.DEBUG:
                                    print("device_id was not found in nodez. Already deleted?: " + str(device_id))
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
                                time.sleep(3)
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
                                print("caught error deleting from Matter: " + str(ex))
                                print(traceback.format_exc())
                        
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state' : state, 
                                              'message':message, 
                                              'device_was_deleted':self.adapter.device_was_deleted,
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
                            #state = self.delete_item(name) # This method returns True if deletion was succesful
                            
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
                                print("Error in share_node: " + str(ex))
                                print(traceback.format_exc())
                        
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state':state, 
                                              'message':message, 
                                              'pairing_code':self.adapter.share_node_code
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

