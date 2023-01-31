"""
Matter addon for Candle Controller.
"""


import os
#os.path.insert(1, dirname(os.path.dirname(os.path.abspath(__file__))))
import sys
# This helps the addon find python libraries it comes with, which are stored in the "lib" folder. The "package.sh" file will download Python libraries that are mentioned in requirements.txt and place them there.
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')) 

import json
#import time

from gateway_addon import APIHandler, APIResponse



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
            print("IN HANDLE REQUEST")
            
            if request.method != 'POST':
                return APIResponse(status=404) # we only accept POST requests
            
            if request.path == '/ajax': # you could have all kinds of paths. In this example we only use this one, and use the 'action' variable to denote what we want to api handler to do

                try:
                    
                    action = str(request.body['action']) 
                    
                    if self.DEBUG:
                        print("API handler is being called. Action: " + str(action))
                        print("request.body: " + str(request.body))
                    
                    
                    # INIT
                    if action == 'init':
                        if self.DEBUG:
                            print("API: in init")
                        
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
                                      'wifi_credentials_available': wifi_credentials_available,
                                      'client_connected': self.adapter.client_connected,
                                      }),
                        )
                        
                    
                    # START PAIRING
                    elif action == 'start_pairing':
                        if self.DEBUG:
                            print("API: in start_pairing")
                        state = False
                        
                        try:
                            state = self.adapter.start_pairing()
                        except Exception as ex:
                            if self.DEBUG:
                                print("Error in start_pairing request: " + str(ex))
                        
                        
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state' : state}),
                        )
                    
                    
                    # DELETE
                    elif action == 'delete':
                        if self.DEBUG:
                            print("API: in delete")
                        
                        state = False
                        
                        try:
                            name = str(request.body['name'])
                            
                            #state = self.delete_item(name) # This method returns True if deletion was succesful
                            
                        except Exception as ex:
                            if self.DEBUG:
                                print("Error deleting: " + str(ex))
                        
                        return APIResponse(
                          status=200,
                          content_type='application/json',
                          content=json.dumps({'state' : state}),
                        )
                    
                    
                    else:
                        print("Error, that action is not possible")
                        return APIResponse(
                            status=404
                        )
                        
                        
                        
                except Exception as ex:
                    if self.DEBUG:
                        print("Ajax error: " + str(ex))
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

