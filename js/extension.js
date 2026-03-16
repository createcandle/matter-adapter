(function() {
	class MatterAdapter extends window.Extension {
	    constructor() {
	      	super('matter-adapter');
      		
            this.debug = false; // if enabled, show more output in the console
            this.stop_regenerating = false;
			
            this.id = 'matter-adapter';
            
			//console.log("Adding matter-adapter addon to main menu");
			this.addMenuEntry('Matter');
        
            this.discovered = null;
            this.nodez = null;
            
            this.all_things = {};
            this.title_lookup_table = {};
            this.nodez = {};
            this.initial_nodez_count = 0;
            this.updating_firmware = false;
            
            this.busy_discovering = false;
            this.busy_pairing = false;
			//this.busy_polling = false;
            this.busy_polling_counter = 0;
            this.device_to_pair = null;
            this.pairing_code = "";
            
            this.hotspot_addon_installed = false;
            this.use_hotspot = false;
            this.wifi_credentials_available = false;
            
            this.uuid == null; // used with qr scanner
            
            this.retried_init = false;
			
			this.scan_window = null;
            
			this.second_page_el = null;
            window.matter_adapter_poll_interval = null;
            // We'll try and get this data from the addon backend
            //this.items = [];
            
			//console.log("QrScanner: ", QrScanner);
			
			
            this.is_narrow = window.matchMedia("only screen and (max-width: 760px)").matches;
            this.is_touch = ('ontouchstart' in document.documentElement && navigator.userAgent.match(/Mobi/));
            
            this.is_mobile = false;
            if(this.is_narrow && this.is_touch){
                this.is_mobile = true
            }
            
            // Load the html
            this.content = ''; // The html from the view will be loaded into this variable
			fetch(`/extensions/${this.id}/views/content.html`)
	        .then((res) => res.text())
	        .then((text) => {
	         	this.content = text;
                
                // This is needed because the user might already be on the addon page and click on the menu item again. This helps to reload it.
	  		 	if( document.location.href.endsWith("extensions/matter-adapter") ){
	  		  		this.show();
	  		  	}
	        })
	        .catch((e) => console.error('Failed to fetch content:', e));
            
            
            // This is not needed, but might be interesting to see. It will show you the API that the controller has available. For example, you can get a list of all the things this way.
            //console.log("window API: ", window.API);
            
	    }






		//
        //  SHOW
        //
        // This is called then the user clicks on the addon in the main menu, or when the page loads and is already on this addon's location.
	    show() {
			//console.log("matter-adapter show called");
            
            try{
				if(window.matter_adapter_poll_interval){
					clearInterval(window.matter_adapter_poll_interval);
				}
                window.matter_adapter_poll_interval = null;
			}
			catch(e){
				//console.log("no interval to clear? ", e);
			} 
            
			//const main_view = document.getElementById('extension-matter-adapter-view');
			
			if(this.content == ''){
                console.log("matter adapter: content has not loaded yet");
				return;
			}
			else{
				this.view.innerHTML = this.content;
			}
			
            try{
                
				this.second_page_el = this.view.querySelector('#extension-matter-adapter-second-page');
				
				
                if(this.is_mobile && this.second_page_el){
                    this.second_page_el.classList.add('extension-matter-adapter-is-mobile');
                }
                
                // Discover button
                /*
                document.getElementById('extension-matter-adapter-discover-button').addEventListener('click', (event) => {
                	console.log("discover button clicked");
                    document.getElementById('extension-matter-adapter-second-page').classList.add('extension-matter-adapter-busy-discovering');
                    document.getElementById('extension-matter-adapter-discovered-devices-list').innerHTML = '<div class="extension-matter-adapter-spinner"><div></div><div></div><div></div><div></div></div>';
                    
    				window.API.postJson(
    					`/extensions/${this.id}/api/ajax`,
    					{'action':'discover'}
                    
    				).then((body) => {
                        console.log("discover response: ", body);
                        if(body.state == true){
                            console.log("discover response was OK");
                        }
                        else{
                            console.log("discover failed?");
                        }
                    
    				}).catch((e) => {
    					console.log("matter-adapter: connnection error after discover button press: ", e);
    				});
            
                });
                */
                
                
                // Commission_with_code
                // Start pairing button press
                this.view.querySelector('#extension-matter-adapter-start-normal-pairing-button').addEventListener('click', (event) => {
                	if(this.debug){
                        console.log("matter adapter: Start commission_with_code button clicked. this.busy_pairing: ", this.busy_pairing);
                    }
                    const wifi_ssid = document.getElementById('extension-matter-adapter-wifi-ssid').value;
                    const wifi_password = document.getElementById('extension-matter-adapter-wifi-password').value;
                    const wifi_remember = document.getElementById('extension-matter-adapter-wifi-remember-checkbox').value;
                    
                    this.view.querySelector('#extension-matter-adapter-pairing-failed-hint').classList.add('extension-matter-adapter-hidden');
                    
                    if(this.wifi_credentials_available == false){
                        if(wifi_ssid.length < 2){
                            console.log("matter adapter: Wifi name is too short");
                            alert("That wifi name is too short");
                            return;
                        }
                        if(wifi_password.length < 8){
                            console.log("matter adapter: Wifi password is too short");
                            alert("That wifi password is too short");
                            return;
                        }
                    }
                    
                    const code = this.pairing_code;
                    if(this.debug){
                        console.log("matter adapter: Pairing code: ", code);
                    }
                    if(code.length < 5){
                        console.log("matter adapter: pairing code was too short");
                        alert("That pairing code is too short");
                        return;
                    }
                    if(!code.startsWith('MT:')){
                        console.log("matter adapter: pairing code did not start with MT:");
                        alert("The pairing code should start with 'MT:'");
                        return;
                    }
                    //this.device_to_pair = {"not":"needed"}
                    /*
                    if(this.device_to_pair == null){
                        console.log("device_to_pair was null");
                        return // shouldn't be possible, but just to be safe
                    }
                    */
                    
                    //document.getElementById('extension-matter-adapter-start-normal-pairing-button').classList.add('extension-matter-adapter-hidden');
                    //document.getElementById('extension-matter-adapter-busy-pairing-indicator').classList.remove('extension-matter-adapter-hidden');
                    
                    this.initial_nodez_count = this.nodez.length; // if this increases, then a new device has been paired.
					
                    this.busy_pairing = true;
					if(!this.second_page_el){
						this.second_page_el = this.view.querySelector('#extension-matter-adapter-second-page');
					}
					if(this.second_page_el){
                    	this.second_page_el.classList.add('extension-matter-adapter-busy-pairing');
						
	                    // Inform backend
	                    window.API.postJson(
							`/extensions/${this.id}/api/ajax`,
							{'action':'start_pairing',
	                        'wifi_ssid':wifi_ssid,
	                        'wifi_password':wifi_password,
	                        'wifi_remember':wifi_remember,
	                        'pairing_type':'commission_with_code',
	                        'code':code}
						).then((body) => { 
							if(this.debug){
	                            console.log("pair device via commission_with_code response: ", body);
	                        }
							if(typeof body.state != 'undefined'){
								if(body.state == false){
									this.view.querySelector('#extension-matter-adapter-pairing-failed-hint').classList.remove('extension-matter-adapter-hidden');
									this.second_page_el.classList.remove('extension-matter-adapter-busy-pairing');
								}
								else if(body.state == true){
									console.log("Matter server pairing process seems to have started succesfully");
								}
							}
                        
                        
						}).catch((e) => {
	                        this.busy_pairing = false;
							console.error("matter-adapter: error making commission_with_code pairing request: ", e);
	                        //document.getElementById('extension-matter-adapter-start-normal-pairing-button').classList.remove('extension-matter-adapter-hidden');
						});
						
					}
                    
                });
                
                
                // Commission_on_network
                // Start pairing via commission_on_network button press
                this.view.querySelector('#extension-matter-adapter-start-network-pairing-button').addEventListener('click', (event) => {
                	if(this.debug){
                        console.log("matter adapter debug: Start network pairing button clicked");
                    }
                    const code = this.view.querySelector('#extension-matter-adapter-network-pairing-code-input').value; //this.pairing_code;//document.getElementById('extension-matter-adapter-pairing-code').value;
                    
                    this.view.querySelector('#extension-matter-adapter-pairing-failed-hint').classList.add('extension-matter-adapter-hidden');
                    
                    if(code.length < 4){
                        console.error("matter adapter: code was too short");
                        alert("That code is too short");
                        return;
                    }
                    this.pairing_code = code;
                    if(this.debug){
                        console.log("Network pairing code: ", code);
                    }
                    //document.getElementById('extension-matter-adapter-start-normal-pairing-button').classList.add('extension-matter-adapter-hidden');
                    //document.getElementById('extension-matter-adapter-busy-pairing-indicator').classList.remove('extension-matter-adapter-hidden');
                    
                    this.initial_nodez_count = this.nodez.length;
                    
					// Inform backend
                    this.busy_pairing = true;
					
					if(!this.second_page_el){
						this.second_page_el = this.view.querySelector('#extension-matter-adapter-second-page');
					}
					if(this.second_page_el){
                    	this.view.querySelector('#extension-matter-adapter-second-page').classList.add('extension-matter-adapter-busy-pairing');
                    }
                    
					window.API.postJson(
						`/extensions/${this.id}/api/ajax`,
						{'action':'start_pairing',
                        'pairing_type':'commission_on_network',
                        'code':code}
					).then((body) => { 
						if(this.debug){
                            console.log("pair device via commission_on_network response: ", body);
                        }
                        if(typeof body.state != 'undefined'){
                            if(body.state == true){
                                if(this.debug){
                                    console.log('matter adapter debug: start commission on network response: state was good');
                                }
                            }
                            else{
                                if(this.debug){
                                    console.error('matter adapter debug: error, start commission on network failed');
                                }
                                alert("Error, could not start the pairing process");
                            }
                        }
                        
					}).catch((e) => {
                        this.busy_pairing = false;
						console.error("matter-adapter: error making commission_on_network pairing request: ", e);
                        //document.getElementById('extension-matter-adapter-start-network-pairing-button').classList.remove('extension-matter-adapter-hidden');
					});
                });


                // Reveal wifi change button
    			this.view.querySelector('#extension-matter-adapter-reveal-wifi-setup-button').addEventListener('click', (event) => {
                    this.view.querySelector('#extension-matter-adapter-current-wifi-ssid-container').classList.add('extension-matter-adapter-hidden');
                    this.view.querySelector('#extension-matter-adapter-provide-wifi-container').classList.remove('extension-matter-adapter-hidden');
    			});
                
				this.view.querySelector('#extension-matter-adapter-pairing-qr-choose-scanner-camera').addEventListener('click', (event) => {
					event.preventDefault();
					console.log("matter adapter: opening in new window: event.target: ",  event.target);
					console.log("matter adapter: opening in new window: url:", event.target.href);
					this.scan_window = window.open(event.target.href,'_blank');
				});
				
				
				// Choose to scan with camera
				/*
    			document.getElementById('extension-matter-adapter-pairing-qr-choose-scanner-camera').addEventListener('click', (event) => {
					console.log("clicked on big camera button");
    				document.getElementById('extension-matter-adapter-pairing-qr-choose-scanner-area').classList.add('extension-matter-adapter-hidden');
					document.getElementById('extension-matter-adapter-pairing-qr-camera-area').classList.remove('extension-matter-adapter-hidden');
					
					const qr_scan_video_el = document.getElementById('extension-matter-adapter-qr-video');
					
			        //const videoContainer = document.getElementById('extension-matter-adapter-video-container');
			        //const camHasCamera = document.getElementById('extension-matter-adapter-cam-has-camera');
			        const camList = document.getElementById('extension-matter-adapter-cam-list');
			        const camHasFlash = document.getElementById('extension-matter-adapter-cam-has-flash');
			        const flashToggle = document.getElementById('extension-matter-adapter-flash-toggle');
			        
					const flashState = document.getElementById('extension-matter-adapter-flash-state');
			        const camQrResult = document.getElementById('extension-matter-adapter-cam-qr-result');
					
					
					const scanner = new QrScanner(
					    qr_scan_video_el,
					    result => {
					    	console.log('decoded qr code:', result);
							scanner.stop();
					    },
						{
							onDecodeError: error => {
								//console.error("There was a decode error?: ", error);
								//camQrResult.textContent = error;
								//camQrResult.style.color = 'inherit';
							},
							highlightScanRegion: true,
							highlightCodeOutline: true,
						},
					);
					console.log("\n\nscanner: ", scanner);
					scanner.setInversionMode('both');
					
			        // for debugging
			        window.scanner = scanner;
					
			        camList.addEventListener('change', event => {
			            scanner.setCamera(event.target.value).then(updateFlashAvailability);
			        });
					
			        flashToggle.addEventListener('click', () => {
			            scanner.toggleFlash() //.then(() => {
			                //flashState.textContent = scanner.isFlashOn() ? 'Flash on' : 'Flash off');
			        });
					
			        const updateFlashAvailability = () => {
			            scanner.hasFlash().then(hasFlash => {
			                console.log("does the selected camera have a flash?", hasFlash);
			                //camHasFlash.textContent = hasFlash;
			                flashToggle.style.display = hasFlash ? 'inline-block' : 'none';
			            });
			        };
					
			        scanner.start().then(() => {
						//console.log("scnr: ", scnr);
			            updateFlashAvailability();
			            // List cameras after the scanner started to avoid listCamera's stream and the scanner's stream being requested
			            // at the same time which can result in listCamera's unconstrained stream also being offered to the scanner.
			            // Note that we can also start the scanner after listCameras, we just have it this way around in the demo to
			            // start the scanner earlier.
			            QrScanner.listCameras(true).then(cameras => cameras.forEach(camera => {
			                const option = document.createElement('option');
			                option.value = camera.id;
			                option.text = camera.label;
			                camList.add(option);
			            }));
			        });
					
			        QrScanner.hasCamera().then(hasCamera => {
			            console.log("camera exists? ", hasCamera);
			            //camHasCamera.textContent = hasCamera
			        });
					
    			});
				
				*/
				
				// Choose to scan with phone
    			this.view.querySelector('#extension-matter-adapter-pairing-qr-choose-scanner-phone').addEventListener('click', (event) => {
					console.log("matter adapter: clicked on big phone button");
    				document.getElementById('extension-matter-adapter-pairing-qr-choose-scanner-area').classList.add('extension-matter-adapter-hidden');
    			});
				
				
				
                // Pairing failed, try again button
    			this.view.querySelector('#extension-matter-adapter-pairing-failed-try-again-button').addEventListener('click', (event) => {
    				this.show_pairing_page();
    			});
                
    			this.view.querySelector('#extension-matter-adapter-update-certificates-button').addEventListener('click', (event) => {
    				this.view.querySelector('#extension-matter-adapter-certificates-need-update').classList.add('extension-matter-adapter-hidden');
					this.view.querySelector('#extension-matter-adapter-busy-updating-certificates').classList.remove('extension-matter-adapter-hidden');
    			});
				
            	
			
			
                // DEV
    			this.view.querySelector('#extension-matter-adapter-stop-poll-button').addEventListener('click', (event) => {
                    console.log("matter adapter: stopping poll?");
                    try{
        				clearInterval(window.matter_adapter_poll_interval);
                        window.matter_adapter_poll_interval = null;
                        console.log("matter adapter: cleared interval");
						
						if(!this.second_page_el){
							this.second_page_el = this.view.querySelector('#extension-matter-adapter-second-page');
						}
						if(this.second_page_el){
	                    	this.second_page_el.classList.remove('extension-matter-adapter-busy-pairing');
						}
						
        			}
        			catch(e){
        				console.log("matter adapter: no interval to clear? ", e);
        			} 
    			});
                
                
                // Show more pairing options button
    			this.view.querySelector('#extension-matter-adapter-show-more-pairing-options-button').addEventListener('click', (event) => {
    				this.view.querySelector('#extension-matter-adapter-other-pairing-options-container').classList.remove('extension-matter-adapter-hidden');
                    this.view.querySelector('#extension-matter-adapter-show-more-pairing-options-button').classList.add('extension-matter-adapter-hidden');
    			});
                
                
                // Manually entered pairing code button
    			this.view.querySelector('#extension-matter-adapter-save-manual-input-pairing-code-button').addEventListener('click', (event) => {
                    this.view.querySelector('#extension-matter-adapter-save-manual-input-pairing-code-button').classList.add('extension-matter-adapter-hidden');
                    
                    const input_code = this.view.querySelector('#extension-matter-adapter-pairing-code-input').value;
                    if(input_code.startsWith('MT:') && input_code.length > 6){
                        this.pairing_code = input_code;
                        setTimeout(function(){
                            document.getElementById('extension-matter-adapter-save-manual-input-pairing-code-button').classList.remove('extension-matter-adapter-hidden');
                        }, 4000);
                        this.show_pairing_start_area();
						
						if(this.scan_window){
							console.log("matter adapter: closing previously opened scan window");
							this.scan_window.close();
							this.scan_window = null;
						}
						
                    }
                    
    				//document.getElementById('extension-matter-adapter-other-pairing-options-container').classList.remove('extension-matter-adapter-hidden');
    			});
                
                
                // Save network pairing pin code button
                /*
    			document.getElementById('extension-matter-adapter-save-network-pairing-code-button').addEventListener('click', (event) => {
                    document.getElementById('extension-matter-adapter-save-network-pairing-code-button').classList.add('extension-matter-adapter-hidden');
                    
                    const input_code = document.getElementById('extension-matter-adapter-network-pairing-code-input').value;
                    if(input_code.length > 3){
                        this.pairing_code = input_code;
                        setTimeout(function(){
                            document.getElementById('extension-matter-adapter-save-network-pairing-code-button').classList.remove('extension-matter-adapter-hidden');
                        }, 4000);
                        this.show_pairing_start_area();
                    }
                    
    				//document.getElementById('extension-matter-adapter-other-pairing-options-container').classList.remove('extension-matter-adapter-hidden');
    			});
                */
                
				if(!this.second_page_el){
					this.second_page_el = this.view.querySelector('#extension-matter-adapter-second-page');
				}
				
                
    			this.view.querySelector('#extension-matter-adapter-pairing-network-question-normal-button').addEventListener('click', (event) => {
    				this.second_page_el.classList.remove('extension-matter-adapter-pairing-questioning');
                    this.second_page_el.classList.add('extension-matter-adapter-pairing-normal');
    			});
                
    			this.view.querySelector('#extension-matter-adapter-pairing-network-question-network-button').addEventListener('click', (event) => {
    				this.second_page_el.classList.remove('extension-matter-adapter-pairing-questioning');
                    this.second_page_el.classList.add('extension-matter-adapter-pairing-network');
    			});
                
                
                
            
                // Easter egg when clicking on the title
    			this.view.querySelector('#extension-matter-adapter-title').addEventListener('click', (event) => {
    				this.show();
    			});
                
    			this.view.querySelector('#extension-matter-adapter-refresh-paired-list-button').addEventListener('click', (event) => {
    				this.view.querySelector('#extension-matter-adapter-refresh-paired-list-button').classList.add('extension-matter-adapter-hidden');
                    this.view.querySelector('#extension-matter-adapter-paired-devices-list').innerHTML = '<div class="extension-matter-adapter-spinner"><div></div><div></div><div></div><div></div></div>';
                    this.get_init_data();
    			});
    			
				this.view.querySelector('#extension-matter-adapter-stop-refreshing-list-button').addEventListener('click', (event) => {
					this.stop_regenerating = true;
				});
				
				this.view.querySelector('#extension-matter-adapter-reset-customizations-button').addEventListener('click', (event) => {
					if(confirm("Are you sure you want to forget all device customizations?")){
			            window.API.postJson(
							`/extensions/${this.id}/api/ajax`,
							{'action':'reset_customizations'}
						).then((body) => { 
							if(this.debug){
			                    console.log("reset reset_customizations done");
			                }
							this.nodez = {};
							this.regenerate_items();
						}).catch((err) => {
							console.error("matter-adapter: caught error calling reset_customizations: ", err);
						});
					}
					
				});
				
            
            
                // ADD DEVICES PLUS BUTTON
                this.view.querySelector('#extension-matter-adapter-show-second-page-button').addEventListener('click', (event) => {
                    if(this.debug){
                        console.log("matter adapter debug: clicked on (+) button");
                    }
                    
                    // iPhones need this fix to make the back button lay on top of the main menu button
                    this.view.style.zIndex = '3';
                    this.view.querySelector('#extension-matter-adapter-content-container').classList.add('extension-matter-adapter-showing-second-page');
                    
                    this.show_pairing_page();
    			});
                
                // SHOW WIFI PASSWORD CHECKBOX
                this.view.querySelector('#extension-matter-adapter-wifi-show-password-checkbox').addEventListener('change', (event) => {
                    if(this.debug){
                        console.log("matter adapter debug: clicked on wifi password reveal checkbox");
                    }
                    const checked = this.view.querySelector('#extension-matter-adapter-wifi-show-password-checkbox').checked;
                    if(checked){
                        this.view.querySelector('#extension-matter-adapter-wifi-password').type = 'text';
                    }
                    else{
                        this.view.querySelector('#extension-matter-adapter-wifi-password').type = 'password';
                    }
    			});
                
            
                
                // Back button, shows main page
                this.view.querySelector('#extension-matter-adapter-back-button-container').addEventListener('click', (event) => {
                    if(this.debug){
                        console.log("matter adapter debug: clicked on back button");
                    }
                    this.busy_discovering = false;
                    this.busy_pairing = false;
					this.busy_polling_counter = 0;
                    
                    try{
						if(window.matter_adapter_poll_interval){
							clearInterval(window.matter_adapter_poll_interval);
						}
        				
                        window.matter_adapter_poll_interval = null;
        			}
        			catch(e){
        				//console.log("no interval to clear? ", e);
        			} 
                    
                    this.view.querySelector('#extension-matter-adapter-content-container').classList.remove('extension-matter-adapter-showing-second-page');
                
                    // Undo the iphone fix, so that the main menu button is clickable again
                    this.view.style.zIndex = 'auto';
                
                    this.get_init_data(); // repopulate the main page
                
    			});
            
            
                // Scroll the content container to the top
                this.view.scrollTop = 0;
            
            

                // Finally, request the first data from the addon's API
                //console.log("Matter adapter: making init data request");
                this.get_init_data();
                
				
            }
            catch(err){
                console.error("Matter adapter: caught error in show(): ", err);
            }
			
			
			
			
			
			
			
			this.waiting_for_main_poll = 0;
			
			this.view.main_poll_interval = setInterval(() => {
				
				if(this.waiting_for_main_poll > 65){
					this.waiting_for_main_poll = 0;
				}
				
				if(this.waiting_for_main_poll == 0){
		            window.API.postJson(
						`/extensions/${this.id}/api/ajax`,
						{'action':'get_main_poll'}
					).then((body) => { 
						if(this.debug){
		                    console.log("matter adapter: debug: get_main_poll: response body: ", body);
		                }
						
						this.parse_body(body);
						
						this.waiting_for_main_poll = 0
					}).catch((err) => {
						console.error("matter-adapter: caught error calling get_main_poll: ", err);
						this.waiting_for_main_poll = 0
					});
				}
				this.waiting_for_main_poll++;
				
			},3000);
            
		}
		
	
		// This is called then the user navigates away from the addon. It's an opportunity to do some cleanup. To remove the HTML, for example, or stop running intervals.
		hide() {
			if(this.debug){
                console.log("matter adapter debug: hide called");
            }
            
            try{
				if(window.matter_adapter_poll_interval){
					clearInterval(window.matter_adapter_poll_interval);
				}
                window.matter_adapter_poll_interval = null;
			}
			catch(e){
				//console.log("no interval to clear? ", e);
			} 
		}
    
    
    
        //
        //  INIT
        //
        // This gets the first data from the addon API
        
        get_init_data(){
			try{
                
                // Load all things, in order to integrate that data with the init data
                try{
            	    API.getThings().then((things) => {
			
            			this.all_things = things;
            			for (let key in things){
                        
            				try{
					
            					var thing_title = 'unknown';
            					if( things[key].hasOwnProperty('title') ){
            						thing_title = things[key]['title'];
            					}
            					else if( things[key].hasOwnProperty('label') ){
            						thing_title = things[key]['label'];
            					}
					
            					//console.log("thing_title = " + thing_title);
					
            					var thing_id = things[key]['href'].substr(things[key]['href'].lastIndexOf('/') + 1);
                                if(thing_id.startsWith('matter-')){
                                    this.title_lookup_table[thing_id] = thing_title;
                                }
                            
                            }
                			catch(e){
                				console.error("Matter adapter: error looping over all things: ", e);
                			}
                        }
                        if(this.debug){
                            console.log("matter adapter debug: this.all_things: ", this.all_things);
                            console.log("matter adapter debug: this.title_lookup_table: ", this.title_lookup_table);
                        }
                        
                        this.get_init_data2();
                        
                    });
                }
    			catch(e){
    				console.log("matter adapter debug: Error calling API.getThings(): " , e);
                    this.request_devices_list();
    			}
                
			}
			catch(e){
				console.log("matter adapter debug: Error in API call to init: ", e);
			}
        }
        
        
        // Gets called after the things have first been requested from the webthings API. Which is needed to get the thing title.
        get_init_data2(){
            if(this.debug){
                console.log("matter adapter debug: in get_init_data2 (getting init from addon api)");
            }
            
	  		// Init
	        window.API.postJson(
	          `/extensions/${this.id}/api/ajax`,
                {'action':'init'}

	        ).then((body) => {
                
                this.parse_body(body);
			
	        }).catch((err) => {
	  			console.log("Error getting MatterAdapter init2 data: ", err);
                setTimeout(() => {
                    if(this.retried_init == false){
                        this.retried_init = true;
                        if(this.debug){
							console.warn("matter adapter debug: restaring get_init_data after earlier attempt failed");
						}
                        this.get_init_data();
                    }
                    
                },15000);
	        });	
        }
    
    	parse_body(body){
            try{
                // We have now received initial data from the addon, so we can hide the loading spinner by adding the extension-matter-adapter-hidden class to it.
                
				if(this.debug){
					console.log("matter adapter debug: in parse_body.  body: ", body);
				}
				
				if(!this.second_page_el){
					this.second_page_el = this.view.querySelector('#extension-matter-adapter-second-page');
				}
				
				const spinner_el = this.view.querySelector('#extension-matter-adapter-loading');
				if(spinner_el){
					spinner_el.classList.add('extension-matter-adapter-hidden');
				}
				
            
                // If debug is available in the init data, set the debug value and output the init data to the console
                if(typeof body.debug != 'undefined'){
                    this.debug = body.debug;
                    if(this.debug){
                        // Show big red debug warning
                        if(this.view.querySelector('#extension-matter-adapter-debug-warning')){
                            this.view.querySelector('#extension-matter-adapter-debug-warning').style.display = 'block';
                        }
                    }
                }
            
                //if(this.debug){
                //    console.log("matter adapter debug: parse_body: is_mobile? ", this.is_mobile);
                //}
            
				
                if(typeof body.use_hotspot == 'boolean' && typeof body.hotspot_addon_installed == 'boolean' && typeof body.wifi_credentials_available != 'undefined'){
                    this.hotspot_addon_installed = body.hotspot_addon_installed;
                    this.use_hotspot = body.use_hotspot;
                    this.wifi_credentials_available = body.wifi_credentials_available;
                    /*
                    if(this.use_hotspot && !this.hotspot_addon_installed){
                        document.getElementById('extension-matter-adapter-install-hotspot-hint').classList.remove('extension-matter-adapter-hidden');
                    }
                    else if(!this.wifi_credentials_available){
                        document.getElementById('extension-matter-adapter-missing-wifi-credentials-hint').classList.remove('extension-matter-adapter-hidden');
                    }
                    */
                }
				
				if(typeof body.use_hotspot == 'boolean'){
					this.use_hotspot = body.use_hotspot;
					const hotspot_hint_el = this.view.querySelector('#extension-matter-adapter-install-hotspot-hint');
					if(hotspot_hint_el){
						if(body.use_hotspot == false){
							hotspot_hint_el.classList.remove('extension-matter-adapter-hidden');
						}
						else{
							hotspot_hint_el.classList.add('extension-matter-adapter-hidden');
						}
						
					}
				}
                
                if(typeof body.nodez != 'undefined'){
                    //if(this.debug){
                    //    console.log("matter adapter debug: parse_body: received nodez: ", body.nodez);
                    //}
                    this.nodez = body.nodez;
                    const nodes_string = JSON.stringify(body.nodez, null, 4);
					const devices_list_pre_el = this.view.querySelector('#extension-matter-adapter-paired-devices-list-pre')
                    if(devices_list_pre_el){
                    	devices_list_pre_el.innerHTML = nodes_string;
                    }
					
					this.regenerate_items();
					
                    
                    //if(body.nodez.length > 0){
                        
					//}
                }
                
                if(typeof body.wifi_credentials_available == 'boolean' && typeof body.wifi_ssid == 'string'){
                    if(body.wifi_credentials_available && body.wifi_ssid != ""){
						const wifi_ssid_el = this.view.querySelector('#extension-matter-adapter-current-wifi-ssid');
						if(wifi_ssid_el){
                            wifi_ssid_el.innerText = body.wifi_ssid;
                            this.view.querySelector('#extension-matter-adapter-current-wifi-ssid-container').classList.remove('extension-matter-adapter-hidden');
                            this.view.querySelector('#extension-matter-adapter-provide-wifi-container').classList.add('extension-matter-adapter-hidden');
							this.view.querySelector('#extension-matter-adapter-pairing-step-wifi-explanation').classList.add('extension-matter-adapter-hidden');
						}
                        
                    }
                }
                
                
                /*
                // Generate the list of items
                if(typeof body.items_list != 'undefined'){
                    this.items = body['items_list'];
                    this.regenerate_items(body['items_list']);
                }
                */
				
				
				
				// MAIN POLL
				if(typeof body.client_connected == 'boolean'){
					const still_starting_el = this.view.querySelector('#extension-matter-adapter-still-starting-hint');
					if(still_starting_el){
						if(body.client_connected == false){
							still_starting_el.classList.remove('extension-matter-adapter-hidden');
						}
						else{
							still_starting_el.classList.add('extension-matter-adapter-hidden');
						}
					}
				}
				
				const thread_details_el = this.view.querySelector('#extension-matter-adapter-thread-radio-details');
				if(thread_details_el){
					thread_details_el.innerHTML = '';
					
					if(typeof body.found_thread_radio_again == 'boolean' && typeof body.found_new_thread_radio == 'boolean'){
						if(body.found_new_thread_radio){
							thread_details_el.innerHTML += '<span>NEW Thread radio detected</span>';
						}
						else if(body.found_thread_radio_again){
							thread_details_el.innerHTML += '<span>Thread radio detected</span>';
						}
						else{
							thread_details_el.innerHTML += '<span>No Thread radio detected; you can only pair Matter WiFi devices.</span>';
							if(this.debug){
								console.warn("matter adapter: debug: No Thread radio detected (yet)");
							}
						}
					}
					
					
					if(typeof body.thread_error == 'string' && body.thread_error.length > 1){
						thread_details_el.innerHTML += '<span class="extension-matter-adapter-error">' + body.thread_error + '</span>';
					}
					else if(typeof body.thread_running == 'boolean' && typeof body.otbr_started == 'boolean'){
						if(body.thread_running){
							thread_details_el.innerHTML += '<span>Thread network is ready</span>';
						}
						else if(body.otbr_started){
							thread_details_el.innerHTML += '<span>Thread network is starting...</span>';
						}
						else{
							if(this.debug){
								console.warn("matter adapter: debug: otbr not started (yet)");
							}
						}
					}
					
					if(this.debug){
						if(typeof body.thread_radio_is_alive_seconds_ago == 'number'){
							console.warn("matter adapter: debug: thread_radio_is_alive_seconds_ago: ", typeof body.thread_radio_is_alive_seconds_ago);
						}
						else{
							console.warn("matter adapter: debug: thread_radio_is_alive_seconds_ago was not a number: ", typeof body.thread_radio_is_alive_seconds_ago);
						}
					}
					
					if(typeof body.thread_radio_is_alive_seconds_ago == 'number' && body.thread_radio_is_alive_seconds_ago <= 60){
						thread_details_el.classList.remove('extension-matter-adapter-thread-radio-is-not-responding');
					}
					else{
						if(typeof body.thread_radio_is_alive_seconds_ago == 'number' && body.thread_radio_is_alive_seconds_ago > 60){
							if(body.thread_radio_is_alive_seconds_ago < 181){
								thread_details_el.innerHTML += '<span>Thread radio last responded ' + body.thread_radio_is_alive_seconds_ago  + ' seconds ago</span>';
							}
							else if(body.thread_radio_is_alive_seconds_ago < 3600){
								thread_details_el.innerHTML += '<span>Thread radio last responded ' + Math.round(body.thread_radio_is_alive_seconds_ago/60)  + ' minutes ago</span>';
							}
						}
						thread_details_el.classList.add('extension-matter-adapter-thread-radio-is-not-responding');
					}
					
				}
				
				if(typeof body.wifi_restore_countdown == 'number'){
					const restore_countdown_el = this.view.querySelector('#extension-matter-adapter-wifi-restore-countdown');
					if(restore_countdown_el){
						if(body.wifi_restore_countdown > 0){
							restore_countdown_el.innerHTML = '<p>Pairing in progress</p><h3>Turning WiFi back on in ' + Math.round(body.wifi_restore_countdown) + ' seconds...</h3>';
						}
						else{
							restore_countdown_el.innerHTML = '';
						}
					}
					
				}
				
				
				if(typeof body.pairing_phase == 'number'){
					const pairing_progress_bar_el = this.view.querySelector('#extension-matter-adapter-pairing-progress-bar');
					if(pairing_progress_bar_el){
						const pairing_progress_bar_container_el = this.view.querySelector('#extension-matter-adapter-pairing-progress-bar-container');
						
						let progress_bar_width = body.pairing_phase;
						if(progress_bar_width < 0){
							progress_bar_width = 0;
							pairing_progress_bar_container_el.style.background = 'red';
						}
						else{
							if(progress_bar_width >= 100){
								progress_bar_width = 100;
								pairing_progress_bar_container_el.style.background = 'green';
							}
							else{
								pairing_progress_bar_container_el.style.background = 'rgba(0,0,0,.3)';
							}
						}
						pairing_progress_bar_el.style.width = progress_bar_width + '%';
					}
					
				}
				
				
                // PAIRING FAILED?
                if(typeof body.pairing_failed == 'boolean'){
					
					if(body.pairing_failed == true){
						
						if(this.second_page_el){
							if(this.second_page_el.classList.contains('extension-matter-adapter-busy-pairing')){
	                            this.second_page_el.classList.remove('extension-matter-adapter-busy-pairing');
								this.view.querySelector('#extension-matter-adapter-pairing-failed-hint').classList.remove('extension-matter-adapter-hidden');
							}
						}
						
						if(this.busy_pairing){
                            if(this.debug){
                                console.log("matter adapter debug: MATTER PAIRING FAILED");
                            }
                            try{
								if(window.matter_adapter_poll_interval){
									clearInterval(window.matter_adapter_poll_interval);
								}
                                window.matter_adapter_poll_interval = null;
                			}
                			catch(e){
                				//console.log("no interval to clear? ", e);
                			}
                            this.busy_pairing = false;
						}
					}
                    
                    //this.regenenerate_items();
                }
				
				if(typeof body.decoded_pairing_code != 'undefined'){
					console.warn("decoded_pairing_code: ", body.decoded_pairing_code);
				}
				
				
            }
            catch(err){
                console.error("matter adapter: parse_body: caught error parsing matter response: ", err);
            }
    	}
	
	
    
        // Show pairing page, triggered by opening the pairing page, or pressing the retry button if pairing failed
        show_pairing_page(){
            this.busy_pairing = false;
			this.busy_polling_counter = 0;
            
            if(this.debug){
                console.log("matter adapter debug: in show_pairing_page");
            }
            
            
            window.API.postJson(
				`/extensions/${this.id}/api/ajax`,
				{'action':'reset_pairing'}
			).then((body) => { 
				if(this.debug){
                    console.log("reset pairing done");
                }
                this.busy_pairing = false;
			}).catch((e) => {
                this.busy_pairing = false;
				console.error("matter-adapter: error making reset pairing request: ", e);
			});
            
            
            this.generate_qr();
            
            // start polling for data
            if(window.matter_adapter_poll_interval == null){
                window.matter_adapter_poll_interval = setInterval(() =>{
                    this.pairing_poll();
                },5000);
            }
			
			if(!this.second_page_el){
				this.second_page_el = this.view.querySelector('#extension-matter-adapter-second-page');
			}
            
            // Reset elements to start position
            
			this.second_page_el.classList.add('extension-matter-adapter-pairing-questioning');
            this.second_page_el.classList.remove('extension-matter-adapter-pairing-normal');
			this.second_page_el.classList.remove('extension-matter-adapter-pairing-network');
            this.second_page_el.classList.remove('extension-matter-adapter-busy-pairing');
			this.view.querySelector('#extension-matter-adapter-pairing-start-area').classList.add('extension-matter-adapter-hidden');
		    this.view.querySelector('#extension-matter-adapter-pairing-step-qr').classList.remove('extension-matter-adapter-hidden');
            this.view.querySelector('#extension-matter-adapter-save-manual-input-pairing-code-button').classList.remove('extension-matter-adapter-hidden');
            this.view.querySelector('#extension-matter-adapter-pairing-failed-hint').classList.add('extension-matter-adapter-hidden');
            this.view.querySelector('#extension-matter-adapter-pairing-success-hint').classList.add('extension-matter-adapter-hidden');
			
			let old_pairing_code = localStorage.getItem('extension-matter-adapter-last-pairing-code');
			if(typeof old_pairing_code == 'string' && old_pairing_code.startsWith('MT')){
				if(this.debug){
					console.log("matter adapter debug: spotted pairing code in local storage: ", old_pairing_code);
				}
				if(old_pairing_code.indexOf('----|----') != -1){
					let old_code_storage_time = old_pairing_code.split('----|----')[1];
					old_code_storage_time = parseInt(old_code_storage_time);
					if(old_code_storage_time < Date.now() - 3600000){
						this.view.querySelector('#extension-matter-adapter-pairing-code-input').value = old_pairing_code.split('----|----')[0];
					}
					else{
						if(this.debug){
							console.log("matter adapter debug: pairing code in local storage was too old, deleting it");
						}
						localStorage.removeItem('extension-matter-adapter-last-pairing-code');
					}
				}
			}
			
        }
    
    

        // is called once every few seconds by poll_interval
        pairing_poll(){
            if(this.debug){
                console.log("matter adapter debug: in pairing_poll.  this.busy_pairing, this.busy_polling_counter: ", this.busy_pairing, this.busy_polling_counter);
            }
			
            if(this.busy_polling_counter > 13){
                this.busy_polling_counter = 0;
                if(this.debug){
                    console.log("matter adapter debug: letting a new polling attempt through");
                }
            }
			
            if(this.busy_pairing == false){
                
				window.API.postJson(
					`/extensions/${this.id}/api/ajax`,
					{'action':'poll','uuid':this.uuid}
            
				).then((body) => {
	                if(this.debug){
	                    console.log("matter adapter debug: poll response: ", body);
	                }
	                this.busy_pairing = false;
					this.busy_polling_counter = 0;
                
	                /*
	                if(typeof body.busy_discovering != 'undefined'){
	                    this.busy_discovering = body.busy_discovering;
	                    if(this.busy_discovering){
	                        document.getElementById('extension-matter-adapter-second-page').classList.add('extension-matter-adapter-busy-discovering');
	                    }
	                    else{
	                        document.getElementById('extension-matter-adapter-second-page').classList.remove('extension-matter-adapter-busy-discovering');
	                    }
	                }
	                */
					if(!this.second_page_el){
						this.second_page_el = this.view.querySelector('#extension-matter-adapter-second-page');
					}
					
	                if(typeof body.busy_pairing == 'boolean'){
						if(body.busy_pairing != this.busy_pairing){
							console.warn("PAIRING STATE CHANGED from,to:", this.busy_pairing, body.busy_pairing);
						}
	                    this.busy_pairing = body.busy_pairing;
						console.log("pairing_poll: this.busy_pairing is now: ", this.busy_pairing);
						if(this.second_page_el){
		                    if(this.busy_pairing){
		                        this.second_page_el.classList.add('extension-matter-adapter-busy-pairing');
		                    }
		                    else{
		                        this.second_page_el.classList.remove('extension-matter-adapter-busy-pairing');
		                    }
						}
						else{
							console.error("matter adapter: could not find #extension-matter-adapter-second-page");
						}
	                    
	                }
                
				
	                if(typeof body.busy_updating_certificates != 'undefined'){
	                    if(body.busy_updating_certificates){
	                        this.view.querySelector('#extension-matter-adapter-busy-updating-certificates').classList.remove('extension-matter-adapter-hidden');
							this.view.querySelector('#extension-matter-adapter-certificates-need-update').classList.add('extension-matter-adapter-hidden');
	                        if(this.debug){
	                            console.log("matter adapter: busy updating certificates");
	                        }
						}
	                    else{
	                        this.view.querySelector('#extension-matter-adapter-busy-updating-certificates').classList.add('extension-matter-adapter-hidden');
		                
							if(typeof body.certificates_updated != 'undefined'){
			                    if(body.certificates_updated){
			                        this.view.querySelector('#extension-matter-adapter-certificates-need-update').classList.add('extension-matter-adapter-hidden');
			                    }
			                    else{
			                        this.view.querySelector('#extension-matter-adapter-certificates-need-update').classList.remove('extension-matter-adapter-hidden');
			                    }
                
			                }
	                    }
                
	                }
				
					if(typeof body.decoded_pairing_code != 'undefined'){
						console.warn("body.decoded_pairing_code: ", body.decoded_pairing_code);
						if(Array.isArray(body.decoded_pairing_code)){
							for(let l = 0; l < body.decoded_pairing_code.length; l++){
								console.log("decoded pairing code line: ", body.decoded_pairing_code[l]);
							}
						}
						
					}
				
                
	                /*
	                if(typeof body.discovered != 'undefined' && this.busy_discovering == false){
	                    this.discovered = body.discovered;
	                    this.list_discovered_devices();
	                }
	                */
                
	                if(typeof body.nodez != 'undefined'){
	                    if(body.nodez.length > this.initial_nodez_count){
	                        if(this.debug){
								console.log("matter adapter debug: THE DEVICE LIST IS LONGER NOW, PAIRING MUST HAVE SUCCEEDED");
							}
	                        this.view.querySelector('#extension-matter-adapter-second-page').classList.remove('extension-matter-adapter-busy-pairing');
	                        this.view.querySelector('#extension-matter-adapter-pairing-success-hint').classList.remove('extension-matter-adapter-hidden');
	                    }
	                    this.nodez = body.nodez;
	                    //this.regenenerate_items();
	                }
                
	                if(typeof body.nodes != 'undefined'){
	                    this.nodez = body.nodes;
	                    //this.regenenerate_items();
	                }
	                if(typeof body.pairing_code != 'undefined'){
	                    if(body.pairing_code.startsWith('MT:')){
	                        if(this.debug){
	                            console.log("matter adapter debug: GOT A GOOD PAIRING CODE: ", body.pairing_code);
	                        }
	                        this.pairing_code = body.pairing_code;
                        
	                        this.view.querySelector('#extension-matter-adapter-pairing-code-input').value = this.pairing_code;
                        	
							if(this.scan_window){
								if(this.debug){
									console.log("matter adapter debug: closing previously opened scan window");
								}
								this.scan_window.close();
								this.scan_window = null;
							}
						
	                        this.show_pairing_start_area();
							
							localStorage.setItem('extension-matter-adapter-last-pairing-code', this.pairing_code + '----|----' + Date.now() );
	                    
						}
	                    else{
	                        if(this.debug){
	                            //console.log("pairing code did not start with MT: yet: ", this.pairing_code);
	                        }
	                    }
                    
	                    //this.regenenerate_items();
	                }
                
	                // PAIRING FAILED?
	                if(typeof body.pairing_failed == 'boolean'){
						
						if(body.pairing_failed == true){
							
							if(this.second_page_el){
								if(this.second_page_el.classList.contains('extension-matter-adapter-busy-pairing')){
		                            this.second_page_el.classList.remove('extension-matter-adapter-busy-pairing');
									this.view.querySelector('#extension-matter-adapter-pairing-failed-hint').classList.remove('extension-matter-adapter-hidden');
								}
							}
							
							if(this.busy_pairing){
	                            if(this.debug){
	                                console.log("matter adapter debug: MATTER PAIRING FAILED");
	                            }
								
								
	                            try{
									if(window.matter_adapter_poll_interval){
										clearInterval(window.matter_adapter_poll_interval);
									}
	                                window.matter_adapter_poll_interval = null;
	                			}
	                			catch(e){
	                				//console.log("no interval to clear? ", e);
	                			}
	                            this.busy_pairing = false;
							}
						}
	                    
	                    //this.regenenerate_items();
	                }
					
					
					
                
				}).catch((err) => {
	                this.busy_pairing = false;
					this.busy_polling_counter = 0;
	                console.error("matter-adapter: caught pairing poll error: ", err);
	                this.view.querySelector('#extension-matter-adapter-start-normal-pairing-button').classList.remove('extension-matter-adapter-hidden');
				});
                
				
				this.busy_polling_counter++;
            }
            
			
			
            
        }
        
        
        
        // Reveal the Div with the actual normal pairing button
        show_pairing_start_area(){
            if(this.debug){
                console.log("matter adapter debug: in show_pairing_start_area");
            }
            if(this.pairing_code != ""){
                if(this.debug){
                    console.log("pairing code is available. Showing pairing start area.");
                }
                this.view.querySelector('#extension-matter-adapter-pairing-start-area').classList.remove('extension-matter-adapter-hidden');
                this.view.querySelector('#extension-matter-adapter-pairing-step-qr').classList.add('extension-matter-adapter-hidden');
                this.view.querySelector('#extension-matter-adapter-pairing-start-area-pairing-code').innerText = this.pairing_code;
            }
            else{
                if(this.debug){
                    console.log("matter adapter debug: WiFi credentials and pairing code are NOT both available yet. Not revealing pairing start area.");
                }
            }
            
        }
        
        
    
    
    
		//
		//  REGENERATE ITEMS
		//
	
		regenerate_items(){
			try {
				
				// Used for debugging
				if(this.stop_regenerating){
					return
				}
				
				if(this.debug){
                    console.log("matter adapter debug: in regenerating_items.  this.nodez: ", this.nodez);
                }
				
				const list = this.view.querySelector('#extension-matter-adapter-paired-devices-list');
				if(!list){
                    console.error('matter adapter: Error, target list element does not exist');
				    return;
				}
				
				
				const original = this.view.querySelector('#extension-matter-adapter-original-item');
			    //console.log("original: ", original);
                
			    // Since each item has a name, here we're sorting the list based on that name first
				//this.all_things.sort((a, b) => (a.title.toLowerCase() > b.title.toLowerCase()) ? 1 : -1)
                //this.title_lookup_table.sort((a, b) => (a.toLowerCase() > b.toLowerCase()) ? 1 : -1)
                
                
				
				//list.innerHTML = "";
		        
				
				if(Object.keys(this.nodez).length){
					const no_devices_hint_el = this.view.querySelector('#extension-matter-adapter-no-devices-yet-hint');
					if(no_devices_hint_el){
						no_devices_hint_el.remove();
					}
				}
				
				// Loop over all things
				for( let thing_id in this.nodez ){
					
    				try{
                        let title = 'New device';
                        if(typeof this.title_lookup_table[thing_id] != 'undefined'){
                            title = this.title_lookup_table[thing_id];
                        }
						
						let brand_new_item = false;
    					//let thing_id = things[key]['href'].substr(things[key]['href'].lastIndexOf('/') + 1);
                        //console.log("thing_id: ", thing_id);
                        //this.title_lookup_table[thing_id] = thing_title;
                        
                        
                        let item_data = this.nodez[thing_id];
                        if(this.debug){
                            console.log("matter adapter debug: item_data: ", item_data); // device_id
                        }
                        //console.log("item_data: ", item_data);
                    
					
						let clone = list.querySelector('#extension-matter-adapter-item-' + thing_id);
						
						if(!clone){
							if(this.debug){
		                        console.log("matter adapter debug: creating new item for thing_id: ", thing_id );
			                    console.log("matter adapter debug: sorted title_lookup_table: ", this.title_lookup_table);
			                }
							clone = original.cloneNode(true);
							clone.setAttribute('id','extension-matter-adapter-item-' + thing_id);
							brand_new_item = true;
						}
						
					
    					//var clone = original.cloneNode(true);
    					//clone.removeAttribute('id');
    					//if(this.debug){
                            //console.log("clone: ", clone);
						//}
                    
                        
                        /*
    					// Generate a somewhat fancy icon
                        try{
    						//console.log("item_data['model_id'] = " + item_data['model_id']);
    						if(typeof item_data['vendor_name'] != "undefined"){
    							var icon_name = item_data['vendor_name'].toLowerCase();
                                //console.log("vendor name: " + icon_name);
    							if(icon_name.toLowerCase() == "ikea"){
    								icon_name = "IKEA";
    							}
    							else if(icon_name.toLowerCase() == "ge"){
    								icon_name = "GE";
    							}
    							else if(icon_name.toLowerCase().includes("xiaomi")){
    								icon_name = "MI";
    							}
    							else if(icon_name.toLowerCase().includes("bitron")){
    								icon_name = "Bitron";
    							}
    							else if(icon_name.toLowerCase().includes("tuya")){
    								icon_name = "tuya";
    							}
    							else if(icon_name.toLowerCase().includes("yale")){
    								icon_name = "Yale";
    							}
    							else if(icon_name.toLowerCase().includes("gledopto")){
    								icon_name = "GLEDOPTO";
    							}
    							else if(icon_name.toLowerCase().includes("philips")){
    								icon_name = "PHILIPS";
    							}
    							else if(icon_name.toLowerCase().includes("osram")){
    								icon_name = "OSRAM";
    							}
    							else if(icon_name.toLowerCase().includes("lidl")){
    								icon_name = "LIDL";
    							}
    							else if(icon_name.toLowerCase().includes("legrand")){
    								icon_name = "legrand";
    							}
    							else if(icon_name.toLowerCase().includes("innr")){
    								icon_name = "innr";
    							}
    							else if(icon_name.toLowerCase().includes("immax")){
    								icon_name = "Immax";
    							}
    							else if(icon_name.toLowerCase().includes("hornbach")){
    								icon_name = "HORNBACH";
    							}
    							else if(icon_name.toLowerCase().includes("smart") && icon_name.toLowerCase().includes("smart")){
    								icon_name = "ECOSMART";
    							}
    							else if(icon_name.toLowerCase().includes("develco")){
    								icon_name = "DEVELCO";
    							}
    							else if(icon_name.toLowerCase().includes("centralite")){
    								icon_name = "Centralite";
    							}
    							else if(icon_name.toLowerCase().includes("aurora")){
    								icon_name = "AURORA";
    							}
    							else{
                                    //console.log("No nice icon for this brand yet");
    								//icon_name = 'Unknown';
    							}
						
    							var s = document.createElement("div");
    							var t = document.createTextNode( icon_name );
    							icon_name = icon_name.toLowerCase().replace(/ /g, '-');
    							const class_name = 'extension-matter-adapter-icon-' + icon_name;
							
    							s.appendChild(t);
    							s.classList.add(class_name);                   
    							clone.querySelector('.extension-matter-adapter-item-icon').appendChild(s);
    						}

    					}
    					catch(e){
    						console.error("error adding icon: ", e);
    					}	
					    */
					    
                        
                        // Insert data into item
                    
    					try{
                            // Create big title
							
							let link_title_span_el = clone.querySelector('.extension-matter-adapter-item-title');
							
							if(!link_title_span_el){
	    						
                        
	                            // Add title if it could be found
	                            try{
		    						var a_el = document.createElement("a");
		    						a_el.setAttribute("href", "/things/" + thing_id);
									
	                                let title_span = document.createElement("span");
	                                title_span.classList.add('extension-matter-adapter-item-title');
                            		title_span.textContent = title;
	                                a_el.appendChild(title_span);
	                                clone.querySelector('.extension-matter-adapter-item-title-wrapper').appendChild(a_el);
                                
	                            }
	                            catch(e){
	                                if(this.debug){
										console.error("matter adapter debug: caught error adding thing title to clone: ", e);
									}
	                            }
							}
							else if(link_title_span_el.textContent != title){
								link_title_span_el.textContent = title;
							}
								
							
    						
                        
                            //var desc_span = document.createElement("span");
                            //desc_span.classList.add('extension-matter-adapter-item-description');
                    
                            //var desc_text = document.createTextNode( item_data['product_name'] );
                            //desc_span.appendChild(desc_text);
                            //clone.querySelectorAll('.extension-matter-adapter-description' )[0].appendChild(title_span);
                            //a.appendChild(desc_span);
    						try{
								if(typeof item_data['vendor_name'] == 'string'){
									const vendor_name_el = clone.querySelector('.extension-matter-adapter-item-vendor-name');
									if(vendor_name_el && vendor_name_el.textContent != item_data['vendor_name']){
										vendor_name_el.textContent = item_data['vendor_name'];
									}
								}
                                if(typeof item_data['product_name'] == 'string'){
									const product_name_el = clone.querySelector('.extension-matter-adapter-item-product-name');
									if(product_name_el && product_name_el.textContent != item_data['product_name']){
										product_name_el.textContent = item_data['product_name'];
									}
								}
                            }
                            catch(err){
								if(this.debug){
	                                console.error("matter adapter debug: Error setting vendor or product name: ", err);
									console.log("matter adapter debug: item_data: ", item_data);
								}
                                
                            }
                            
                            /*
                            // Add MAC address link
    						var s = document.createElement("a");
    						//s.classList.add('extension-matter-adapter-matter-id');  
    						s.setAttribute("href", "/things/matter-" + item_data['node_id']);              
    						var t = document.createTextNode( item_data['node_id'] );
    						s.appendChild(t);                                   
    						clone.querySelectorAll('.extension-matter-adapter-matter-id' )[0].appendChild(s);
						    */
                            
                            // Add firmware version
    						if(typeof item_data['software_version'] != "undefined"){
                                if(clone.querySelector('.extension-matter-adapter-item-software-version' ).innerHTML == ''){
									if(this.debug){
	                                    console.log("matter adapter debug: software version: ", item_data['software_version']);
	                                }
	                                //alert(item_data['software_version']);
	    							const s = document.createElement("span");
									s.textContent = item_data['software_version'];
	    							clone.querySelector('.extension-matter-adapter-item-software-version' ).appendChild(s);
                                }
								
    						}
    						if(typeof item_data['hardware_version'] != "undefined"){
    							if(clone.querySelector('.extension-matter-adapter-item-hardware-version' ).innerHTML == ''){
									const s = document.createElement("span");
									s.textContent = item_data['hardware_version'];                   
	    							clone.querySelector('.extension-matter-adapter-item-hardware-version' ).appendChild(s);
								}
    						}
						
						
    					}
    					catch(e){
    						console.log("matter adapter debug: error handling Matter device data: " , e);
    					}
						
                        
                        // UPDATE
                        
    					// Click on first firmware update button
    					const show_update_button = clone.querySelector('.extension-matter-adapter-item-update-button');
                        //if(item_data['update']['state'] == 'available'){
    					//	show_update_button.disabled = false;
    					//}
                        if(show_update_button != null){
							if(!show_update_button.classList.contains('extension-matter-adapter-listener-added')){
								show_update_button.classList.add('extension-matter-adapter-listener-added');
								
        						if(this.debug){
									console.log("matter adapter debug: adding listeners to buttons for thing_id: ", thing_id);
								}
								
	        					show_update_button.addEventListener('click', () => {
	        						if(this.debug){
										console.log("matter adapter debug: clicked on show update button. thing_id: ", thing_id);
									}
	        						let item_el = event.currentTarget.closest(".extension-matter-adapter-item");
	        						item_el.classList.add("extension-matter-adapter-update");
	        					});
							
        					
                        
							    /*
		    					const read_about_risks_button = clone.querySelectorAll('.extension-matter-adapter-read-about-risks')[0];
		    					read_about_risks_button.addEventListener('click', (event) => {
		    						document.getElementById('extension-matter-adapter-content').classList = ['extension-matter-adapter-show-tab-tutorial'];
		    					});
							    */
					
		    					const cancel_update_button = clone.querySelector('.extension-matter-adapter-overlay-cancel-update-button');
		    					cancel_update_button.addEventListener('click', (event) => {
		    						if(this.debug){
										console.log("matter adapter debug: cancel update button has been clicked.  thing_id: ", thing_id);
									}
		    						let item_el = event.currentTarget.closest(".extension-matter-adapter-item");
		    						item_el.classList.remove("extension-matter-adapter-update");
		    					});
					
					
					
							    // UPDATE
					
		    					// Click on start firmware update button
		                        /*
		    					const start_update_button = clone.querySelectorAll('.extension-matter-adapter-overlay-start-update-button')[0];
		                        start_update_button.dataset.node_id = item_data['node_id'];
		    					start_update_button.addEventListener('click', (event) => {
		    						//console.log("clicked on start update button. Event:", event);
		    						//console.log("- node_id:" + item_data['node_id']);
		                            //console.log("data attribute: ", event.target.dataset);
		                            //console.log("data attribute: ", event.target.dataset.node_id);
                        
		    						let item_el = event.currentTarget.closest(".extension-matter-adapter-item");
		    						item_el.classList.remove("extension-matter-adapter-update");
		    						item_el.classList.add("extension-matter-adapter-updating");
						
		    						//setTimeout(() => hideBtn(0), 1000);
						
		    						//setTimeout(function(){ 
		    						//	parent3.classList.remove("updating");
		    						//}, 600000); // after 10 minutes, remove updating styling no matter what
						
						
		    						// Disable all update buttons if one has been clicked
		    						var update_buttons = document.getElementsByClassName("extension-matter-adapter-item-update-button");
		    						for(var i = 0; i < update_buttons.length; i++)
		    						{
		    							update_buttons[i].disabled = true;
		    						}
		    						//pre.innerText = "Please wait 10 minutes before you start another update!";
						
						
		    						// Send update request to backend
		    						window.API.postJson(
		    							`/extensions/${this.id}/api/ajax`,
		    							{'action':'update-device','node_id':event.target.dataset.node_id}
		    						).then((body) => { 
		                                if(this.debug){
		    							    //console.log("Update item reaction: ");
		    							    //console.log(body);
		    							    pre.innerText = "update firmware response: " + body['update'];
		                                }
		    							this.updating_firmware = true;

		    						}).catch((e) => {
		    							if(this.debug){
		                                    console.log("matter adapter debug: postJson error while requesting update start");
		                                }
		    						});
					
		    				  	});
							    */
                        
                    
							    // DELETE
                        
		    					// Show delete overlay button
		    					const delete_button = clone.querySelector('.extension-matter-adapter-item-delete-button');
		    					delete_button.addEventListener('click', (event) => {
		                            if(this.debug){
		                                console.log("matter adapter debug: show delete overlay button clicked");
		                            }
		    						let item_el = event.currentTarget.closest(".extension-matter-adapter-item");
		    						item_el.classList.add("extension-matter-adapter-delete");
		    				  	});
					    
		                        // Delete confirm button
		                        const delete_confirm_button = clone.querySelector('.extension-matter-adapter-item-delete-confirm-button');
		    					delete_confirm_button.addEventListener('click', (event) => {
		                            if(this.debug){
		                                console.log("matter adapter debug: delete confirm button clicked. event: ", event);
		                            }
                            
		                            delete_confirm_button.classList.add('extension-matter-adapter-hidden');
                            
		    						let item_el = event.currentTarget.closest(".extension-matter-adapter-item");
		    						item_el.classList.add("extension-matter-adapter-delete");
		                            item_el.querySelector('.extension-matter-adapter-overlay-delete-text').innerText = "Deleting...";
                            
		                            const local_event = event;
                            
		    						// Ask backend to delete device from Matter fabric
		    						window.API.postJson(
		    							`/extensions/${this.id}/api/ajax`,
		    							{'action':'delete','node_id':item_data['node_id']}
		    						).then((body) => { 
		    							if(this.debug){
		                                    console.log("matter adapter debug: delete matter item reaction: ", body);
		                                    console.log("Do event and item exist here?: ", event);
		                                }
		                                if(body.state == true){
		                                    this.nodez = body.nodez;
		                                    //let item_el = local_event.currentTarget.closest(".extension-matter-adapter-item");
		                                    if(typeof event.target != 'undefined'){
		                                        console.log("in delete response, event.target exists");
		                                        let item_el = event.target.closest('extension-matter-adapter-item');
		                                        console.log('item_el ', item_el);
		                                        item_el.classList.add("extension-matter-adapter-hidden");
		                                        console.log("item_el.classList: ", item_el.classList);
		                                    }
                                    
		                                    if(this.debug){
		                                        console.log("matter adapter debug: Delete succeeded. Message: ", body.message);
		                                    }
                                    
		            						//let item_el_parent = item_el.parentElement;
		            						//item_el_parent.removeChild(item_el);
		                                }
		                                else{
		                                    if(this.debug){
		                                        console.error("matter adapter debug: Delete failed. Message: ", body.message);
		                                        alert(body.message);
		                                    }
		                                }

		    						}).catch((e) => {
		    							if(this.debug){
		                                    console.error('matter adapter debug: delete: connection error', e);
		                                    alert("An error occured during the delete process. Try reloading the page.");
		                                }
		    						});
                            
		    				  	});
                        
		                        // Delete cancel button
		                        const delete_cancel_button = clone.querySelector('.extension-matter-adapter-item-delete-cancel-button');
		    					delete_cancel_button.addEventListener('click', (event) => {
		                            if(this.debug){
		                                console.log("matter adapter debug: delete cancel button clicked");
		                            }
		    						let item_el = event.currentTarget.closest(".extension-matter-adapter-item");
		    						item_el.classList.remove("extension-matter-adapter-delete");
		                        });
								
								
								
								
								
								
		                        // SHARE
                        
		                        // Share Matter device buttons
                        
		                        // Reveal share overlay
		    					const reveal_share_button = clone.querySelector('.extension-matter-adapter-item-reveal-share-button');
		    					reveal_share_button.addEventListener('click', (event) => {
		    						let item_el = event.currentTarget.closest(".extension-matter-adapter-item");
		    						//console.log("item_el: ", item_el);
		                            //console.log(parent3);
		                            item_el.querySelector('.extension-matter-adapter-rule-share-confirm-button').classList.remove('extension-matter-adapter-hidden');
		                            item_el.querySelector('.extension-matter-adapter-share-code').innerText = "Would you like to share this device with another Matter controller?";
		                            item_el.querySelector('.extension-matter-adapter-rule-share-cancel-button').value = 'Cancel'; 
		    						item_el.classList.add("extension-matter-adapter-share");
		    					});
                        
		                        // Cancel share
		    					const cancel_share_button = clone.querySelector('.extension-matter-adapter-rule-share-cancel-button');
		    					cancel_share_button.addEventListener('click', (event) => {
		    						//console.log("cancel share button has been clicked");
		    						let item_el = event.currentTarget.closest(".extension-matter-adapter-item");
		    						item_el.classList.remove("extension-matter-adapter-share");
		    					});
                        
		                        // Confirm share
		    					const confirm_share_button = clone.querySelector('.extension-matter-adapter-rule-share-confirm-button');
		    					confirm_share_button.addEventListener('click', (event) => {
		    						if(this.debug){
		                                console.log("matter adapter debug: confirm share button has been clicked");
		                            }
		                            confirm_share_button.classList.add('extension-matter-adapter-hidden');
                            
		                            let item_el = event.currentTarget.closest(".extension-matter-adapter-item");
		                            item_el.querySelector('.extension-matter-adapter-rule-share-cancel-button').value = 'Close'; 
		                            item_el.querySelector('.extension-matter-adapter-share-code').innerText = "One moment... ";
		    						//let item_el = event.currentTarget.closest(".extension-matter-adapter-item");
		    						//item_el.classList.remove("extension-matter-adapter-update");
                            
		    						// Send new values to backend
		    						window.API.postJson(
		    							`/extensions/${this.id}/api/ajax`,
		    							{'action':'share_node','node_id':item_data['node_id']}
		    						).then((body) => {
		    							if(this.debug){
		                                    console.log("matter adapter debug: share_node reaction: ", body);
		                                    console.log("matter adapter debug: item_el in response: ", item_el);
		                                }
		                                if(typeof body.state != 'undefined'){
		                                    if(body['state'] == true){
		                                        if(typeof body.pairing_code != 'undefined'){
		                                            item_el.querySelector('.extension-matter-adapter-share-code').innerText = "Enter this code in the other controller: " + body.pairing_code;
		                                            //item_el.querySelector('.extension-matter-adapter-share-question').classList.add('extension-matter-adapter-hidden');
		                                        }
		                                        //parent3.classList.add(".extension-matter-adapter-hidden");
		                                    }
		                                    else{
		                                        if(this.debug){
		                                            console.error('matter adapter debug: share failed: ', body.message);
		                                        }
		                                        item_el.querySelector('.extension-matter-adapter-share-code').innerText = body.message;
		                                    }
		                                }
                            
		    						}).catch((err) => {
		    							if(this.debug){
		                                    console.error('matter adapter debug: caught delete connection error', err);
		                                }
		    						});
                            
		    					});
                        
                        
		                        // Makes it easier to target each item in the list by giving it a unique class
								// now using ID instead
		                        //clone.classList.add('extension-matter-adapter-item-' + item_data['node_id']);
								
								
								
								
								
							}
						    
                        
						}
					    
                        
                        
                        
                        
                    
                        // Show firmware update status
                        if( typeof item_data['update'] != 'undefined' ){
                            if(item_data['update']['state'] == "updating"){
                                clone.classList.add('extension-matter-adapter-updating');
                                const clone_progress_bar = clone.querySelectorAll('.extension-matter-adapter-update-progress-bar')[0];
                                clone_progress_bar.style.width = item_data['update']['progress'] + "%";
                                const clone_progress_bar_percentage = clone.querySelectorAll('.extension-matter-adapter-update-progress-bar-percentage')[0];
                                clone_progress_bar_percentage.innerText = item_data['update']['progress'] + "%";
                                this.updating_firmware = true;
        					}
							else{
								clone.classList.remove('extension-matter-adapter-updating');
							}
                        }
						else{
							clone.classList.remove('extension-matter-adapter-updating');
						}
				
				
				
						// GENERATE LIST OF ATTRIBUTES
				
						
						if(typeof item_data['attributes'] != 'undefined'){
							const details_list_el = clone.querySelector('.extension-matter-adapter-item-details-list');
							if(details_list_el){
								for (const [endpoint_name, attributes_list] of Object.entries(item_data['attributes'])) {
									//console.log("endpoint_name: ", endpoint_name);
									let endpoint_el = details_list_el.querySelector('.extension-matter-adapter-item-details-list-' + endpoint_name);
									if(!endpoint_el){
										endpoint_el = document.createElement('ul');
										endpoint_el.classList.add('extension-matter-adapter-item-details-list-' + endpoint_name);
										details_list_el.appendChild(endpoint_el);
									}
									
									
									for (const [short_type, attribute] of Object.entries(attributes_list)) {
										const attribute_class_name = 'extension-matter-adapter-item-attribute-' + short_type.replaceAll('.Attributes.','-');
										//console.log("attribute_class_name: ", attribute_class_name);
										let attribute_header_el = null;
										let attribute_el = endpoint_el.querySelector("." + attribute_class_name);
										if(!attribute_el){
											attribute_el = document.createElement('li');
											attribute_el.classList.add(attribute_class_name);
											
											const cluster_name = short_type.split('.Attributes.')[0];
											attribute_el.classList.add('extension-matter-adapter-item-details-cluster-name-' + cluster_name);
											endpoint_el.classList.add('extension-matter-adapter-item-details-cluster-name-' + cluster_name);
											
											attribute_header_el = document.createElement('div');
											attribute_header_el.classList.add('extension-matter-adapter-item-details-header');
											attribute_header_el.classList.add('extension-matter-adapter-flex-between');
											
											const attribute_title_el = document.createElement('span');
											attribute_title_el.classList.add('extension-matter-adapter-item-details-attribute-title');
											
											if(typeof attribute['value'] == 'undefined'){
												attribute['value'] = '?';
											}
											
											attribute_title_el.innerHTML = '<span class="extension-matter-adapter-item-details-attribute-title-cluster">' + short_type.replace('.Attributes.',' - </span><span>') + '</span><span class="extension-matter-adapter-item-details-attribute-value">' + attribute['value'] + '</span>';
											attribute_header_el.appendChild(attribute_title_el);
											
											attribute_el.appendChild(attribute_header_el);
											
											endpoint_el.appendChild(attribute_el);
										}
										
										if(typeof attribute['enabled'] == 'boolean'){
											let enabled_checkbox_el = attribute_el.querySelector('.extension-matter-adapter-item-details-attribute-enabled-checkbox');
											if(!enabled_checkbox_el && attribute_header_el){
												
												const unique_id = 'extension-matter-adapter-unique-' + thing_id + '-' + endpoint_name + '-' + short_type.replace('.Attributes.','-');
												console.log("unique_id: ", unique_id);
												
												enabled_checkbox_el = document.createElement('input');
												enabled_checkbox_el.setAttribute('type','checkbox');
												enabled_checkbox_el.setAttribute('id',unique_id);
												enabled_checkbox_el.setAttribute('name',unique_id);
												
												enabled_checkbox_el.classList.add('extension-matter-adapter-item-details-attribute-enabled-checkbox');
												enabled_checkbox_el.addEventListener('change', () => {
								    				window.API.postJson(
								    					`/extensions/${this.id}/api/ajax`,
								    					{
															'action':'change_attribute',
															'thing_id':thing_id, 
															'endpoint_name':endpoint_name, 
															'short_type':short_type, 
															'attribute':'enabled', 
															'value':enabled_checkbox_el.checked
														}
                    
								    				).then((body) => {
								                        console.log("change_attribute response: ", body);
								                        if(body.state == true){
								                            console.log("change_attribute response was OK");
								                        }
								                        else{
								                            console.error("change_attribute failed?");
								                        }
                    
								    				}).catch((err) => {
								    					console.log("matter-adapter: caught error calling change_attribute: ", err);
								    				});
												});
												
												attribute_header_el.appendChild(enabled_checkbox_el);
												
												const enabled_checkbox_label_el = document.createElement('label');
												enabled_checkbox_label_el.setAttribute('for', unique_id);
												attribute_header_el.appendChild(enabled_checkbox_label_el);
												
												
											}
											enabled_checkbox_el.checked = attribute['enabled'];
										}
										
										if(!attribute_el){
											console.error("matter adapter: no attribute_el?");
											continue
										}
										
										
										if(typeof attribute['property'] != 'undefined' && attribute['property'] != null && typeof attribute['property']['description'] == 'object' && attribute['property']['description'] != null){
											let property_container_el = attribute_el.querySelector('.extension-matter-adapter-item-details-property');
											if(!property_container_el){
												property_container_el = document.createElement('div');
												property_container_el.classList.add('extension-matter-adapter-item-details-property');
												property_container_el.classList.add('extension-matter-adapter-area');
												
												for (const [property_at, property_details] of Object.entries(attribute['property']['description'])) {
													let property_at_el = document.createElement('div');
													property_at_el.classList.add('extension-matter-adapter-flex-between');
													property_at_el.classList.add('extension-matter-adapter-flex-align-center');
													
													
													const label_el = document.createElement('span');
													label_el.textContent = property_at;
													property_at_el.appendChild(label_el);
													
													if(property_at == 'title' && typeof property_details == 'string'){
														const value_input_el = document.createElement('input');
														let current_value = property_details;
														value_input_el.setAttribute('type','text');
														value_input_el.setAttribute('value', property_details);
														value_input_el.addEventListener('blur', () => {
															let new_title = value_input_el.value.trim()
															new_title = new_title.replace(/[^a-zA-Z0-9\- ]/g, '');
															value_input_el.value = new_title;
															if(new_title.length > 0 && new_title.length < 30 && new_title != current_value){
																current_value = new_title;
											    				window.API.postJson(
											    					`/extensions/${this.id}/api/ajax`,
											    					{
																		'action':'change_attribute',
																		'thing_id':thing_id, 
																		'endpoint_name':endpoint_name, 
																		'short_type':short_type, 
																		'path':'description',
																		'attribute':'title', 
																		'value':value_input_el.value
																	}
                    
											    				).then((body) => {
											                        console.log("change_attribute response: ", body);
											                        if(body.state == true){
											                            console.log("change_attribute response was OK");
																		value_input_el.classList.add('extension-matter-adapter-green-bg');
																		setTimeout(() => {
																			value_input_el.classList.remove('extension-matter-adapter-green-bg');
																		},1000)
																		
											                        }
											                        else{
											                            console.error("change_attribute failed?");
											                        }
                    
											    				}).catch((err) => {
											    					console.log("matter-adapter: caught error calling change_attribute: ", err);
											    				});
															}
										    				
														})
														property_at_el.appendChild(value_input_el);
													}
													else{
														const value_el = document.createElement('span');
														value_el.textContent = property_details;
														property_at_el.appendChild(value_el);
													}
													
													property_container_el.appendChild(property_at_el);
												}
												
												attribute_el.appendChild(property_container_el);
											}
											
										}
										
										if(typeof attribute['received_values'] != 'undefined'){
											let received_values_container_el = attribute_el.querySelector('.extension-matter-adapter-item-details-received-values');
											if(!received_values_container_el){
												received_values_container_el = document.createElement('div');
												received_values_container_el.classList.add('extension-matter-adapter-item-details-received-values');
												received_values_container_el.classList.add('extension-matter-adapter-area');
												attribute_el.appendChild(received_values_container_el);
											}
											const received_values_text = 'Received values: ' + attribute['received_values'];
											if(received_values_container_el.textContent != received_values_text){
												received_values_container_el.textContent = received_values_text;
											}
										}
										
										
										
										
									}
									
									
								}
							}
							
						}
						
				
				
				
				
				
				
				
				
				
				
				
						if(brand_new_item){
							list.append(clone);
						}
    					
                        
                        
                    }
        			catch(err){
        				console.error("matter adapter: caught general error while looping over nodez: ", err);
        			}
                    
                    
				} // end of for loop
			
                if(list.innerHTML == ""){
                    list.innerHTML = '<div id="extension-matter-adapter-no-devices-yet-hint"><h2>No Matter devices paired yet</h2><p>Click on the (+) button in the bottom right corner if you want to connect a new Matter device.</p></div>';
                }
                else{
                    // Show refresh button
        			//this.view.querySelector('#extension-matter-adapter-refresh-paired-list-button').classList.remove('extension-matter-adapter-hidden');
                }
                
                if(this.updating_firmware){
					// Disable all update buttons if an update is in progress
					var update_buttons = document.getElementsByClassName("extension-matter-adapter-item-update-button");
					for(var i = 0; i < update_buttons.length; i++)
					{
						update_buttons[i].disabled = true;
					}
                }
				else{
					var update_buttons = document.getElementsByClassName("extension-matter-adapter-item-update-button");
					for(var i = 0; i < update_buttons.length; i++)
					{
						update_buttons[i].disabled = true;
					}
				}
				/*
				try{
					const reading_list = document.getElementsByClassName('extension-matter-adapter-read-about-risks');
					for( var link in reading_list ){
						const element = reading_list[link]
						element.addEventListener('click', (event) => {
							//console.log(event);
							document.getElementById('extension-matter-adapter-content').classList = ['extension-matter-adapter-show-tab-tutorial'];
						});
					}
				}
				catch (e) {
					// statements to handle any exceptions
					//console.log("error creating reading list items: " , e); // pass exception object to error handler
				}
				*/
			
			}
			catch (e) {
				console.log("Matter adapter: general error while generating items: ", e);
			}
			
		}
 
        // Generate QR code to go to QR code scanner (feels weird, but it works)
        generate_qr(){
            
            function make_id(length) {
               var result           = '';
               var characters       = 'ABCDEFGHIJKLMNPQRSTUVWXYZabcdefghijklmnpqrstuvwxyz123456789';
               var charactersLength = characters.length;
               for ( var i = 0; i < length; i++ ) {
                  result += characters.charAt(Math.floor(Math.random() * charactersLength));
               }
               return result;
            }
			
            
            // This ID is used only once, here, to exchange the matter pairing code via the Candle web server.
            this.uuid = make_id(8); //Math.round(Math.random() * 10000000);
            const short_url = 'candlesmarthome.com/qr?' + this.uuid;
            const long_url = 'https://www.' + short_url;
            
            this.view.querySelector('#extension-matter-adapter-short-qr-scan-url').innerText = short_url;
            this.view.querySelector('#extension-matter-adapter-mobile-short-qr-scan-url').innerText = short_url;
            
			this.view.querySelector('#extension-matter-adapter-qr-scan-link').href = long_url;
            this.view.querySelector('#extension-matter-adapter-pairing-qr-choose-scanner-camera').href = long_url;
            this.view.querySelector('#extension-matter-adapter-mobile-qr-scan-link').href = long_url;
            
            const target_element = this.view.querySelector('#extension-matter-adapter-qr-code');
	        target_element.innerHTML = "";
    		
    	    var qrcode = new QRCode(target_element, {
    		    width : 300,
    		    height : 300
    	    });
    	    qrcode.makeCode(long_url);
        }
    
    }

	new MatterAdapter();
	
})();


