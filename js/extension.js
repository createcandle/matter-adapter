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
			this.total_busy_polling_counter = 0;
            this.device_to_pair = null;
            this.pairing_code = "";
            
            this.hotspot_addon_installed = false;
            this.use_hotspot = false;
            this.wifi_credentials_available = false;
            
            this.uuid == null; // used with qr scanner
            
            this.retried_init = false;
			
			this.scan_window = null;
			this.matter_qr_scanner_url = null;
			this.barcode_detector_supported = false;
			
			if (window.location.protocol.startsWith('https') && navigator.mediaDevices && navigator.mediaDevices.getUserMedia && 'BarcodeDetector' in window) {
			
				BarcodeDetector.getSupportedFormats()
				.then((formats) => {
					//console.log("supported formats: ", formats);
					if(formats.includes('qr_code')){
						this.barcode_detector_supported = true;
						//console.log('BarcodeDetector is supported');
					}
				})
				.catch((err) => {
					//console.error("BarcodeDetector is not supported");
				})
			}
            
			this.second_page_el = null;
            window.matter_adapter_poll_interval = null;
            // We'll try and get this data from the addon backend
            //this.items = [];
            
			//console.log("QrScanner: ", QrScanner);
			
			document.body.classList.add(location.protocol.replace(':',''));
			
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
					this.total_busy_polling_counter = 0;
				}
                window.matter_adapter_poll_interval = null;
			}
			catch(e){
				//console.log("no interval to clear? ", e);
			} 
            
			//const main_view = document.getElementById('extension-matter-adapter-view');
			
			if(this.content == ''){
                if(this.debug){
					console.log("matter adapter debug: content has not loaded yet");
				}
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
                        console.log("matter adapter debug: start commission_with_code button clicked. this.busy_pairing: ", this.busy_pairing);
                    }
                    this.start_pairing();
                    
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
                        if(this.debug){
							console.error("matter adapter debug: code was too short");
						}
                        this.flash_message("That code is too short");
                        return;
                    }
                    this.pairing_code = code;
                    if(this.debug){
                        console.log("matter adapter debug: network pairing code: ", code);
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
                            console.log("matter adapter debug: pair device via commission_on_network response: ", body);
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
                                this.flash_message("Error, could not start the pairing process");
                            }
                        }
                        
					}).catch((e) => {
                        this.busy_pairing = false;
						console.error("matter-adapter: error making commission_on_network pairing request: ", e);
                        //document.getElementById('extension-matter-adapter-start-network-pairing-button').classList.remove('extension-matter-adapter-hidden');
					});
                });


                // Reveal wifi change button
    			this.view.querySelector('#extension-matter-adapter-reveal-wifi-setup-button').addEventListener('click', () => {
                    this.view.querySelector('#extension-matter-adapter-current-wifi-ssid-container').classList.add('extension-matter-adapter-hidden');
                    this.view.querySelector('#extension-matter-adapter-provide-wifi-container').classList.remove('extension-matter-adapter-hidden');
    			});
                
				this.view.querySelector('#extension-matter-adapter-pairing-qr-choose-scanner-camera').addEventListener('click', (event) => {
					//event.preventDefault();
					
					if(this.barcode_detector_supported && window.location.protocol.startsWith('https')){
						this.start_local_qr_scanner();
					}
					else if(typeof this.matter_qr_scanner_url == 'string'){
						console.log("matter adapter: opening in new window: event.target: ",  event.target);
						console.log("matter adapter: opening in new window: url:", event.target.href);
						this.scan_window = window.open(this.matter_qr_scanner_url,'_blank');
						
						// start polling for data
			            if(window.matter_adapter_poll_interval == null){
			                window.matter_adapter_poll_interval = setInterval(() =>{
			                    this.pairing_poll();
			                },5000);
							
			            }
						this.busy_polling_counter = 0;
						this.total_busy_polling_counter = 0;
					}
					
					document.getElementById('extension-matter-adapter-pairing-qr-choose-scanner-area').classList.add('extension-matter-adapter-hidden');
					
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
    			this.view.querySelector('#extension-matter-adapter-pairing-qr-choose-scanner-phone').addEventListener('click', () => {
					console.log("matter adapter: clicked on big phone button");
    				document.getElementById('extension-matter-adapter-pairing-qr-choose-scanner-area').classList.add('extension-matter-adapter-hidden');
    			});
				
				// Use previously scanned code
    			this.view.querySelector('#extension-matter-adapter-pairing-use-previously-scanned-code').addEventListener('click', () => {
					console.log("matter adapter: clicked on use-previously-scanned-code");
    				
					this.pairing_code = this.view.querySelector('#extension-matter-adapter-pairing-code-input').value;
					console.log("this.pairing_code is now: ", this.pairing_code);
					if(this.pairing_code.startsWith('MT:')){
						document.getElementById('extension-matter-adapter-pairing-qr-choose-scanner-area').classList.add('extension-matter-adapter-hidden');
						this.show_pairing_start_area();
					}
					else{
						this.pairing_code = '';
						this.view.querySelector('#extension-matter-adapter-pairing-use-previously-scanned-code').classList.add('extension-matter-adapter-hidden');
					}
					
    			});
				
				
				
                // Pairing failed, try again button
    			this.view.querySelector('#extension-matter-adapter-pairing-failed-back-to-the-start-button').addEventListener('click', () => {
    				this.show_pairing_page();
    			});
				
                // Pairing failed, try again button
    			this.view.querySelector('#extension-matter-adapter-pairing-failed-try-again-button').addEventListener('click', () => {
    				this.start_pairing();
    			});
                
    			this.view.querySelector('#extension-matter-adapter-update-certificates-button').addEventListener('click', () => {
    				this.view.querySelector('#extension-matter-adapter-certificates-need-update').classList.add('extension-matter-adapter-hidden');
					this.view.querySelector('#extension-matter-adapter-busy-updating-certificates').classList.remove('extension-matter-adapter-hidden');
    			});
				
            	
			
			
                // DEV
    			this.view.querySelector('#extension-matter-adapter-stop-poll-button').addEventListener('click', () => {
                    console.log("matter adapter: stopping poll?");
                    try{
        				clearInterval(window.matter_adapter_poll_interval);
						this.total_busy_polling_counter = 0;
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
    			this.view.querySelector('#extension-matter-adapter-show-more-pairing-options-button').addEventListener('click', () => {
    				this.view.querySelector('#extension-matter-adapter-other-pairing-options-container').classList.remove('extension-matter-adapter-hidden');
                    this.view.querySelector('#extension-matter-adapter-show-more-pairing-options-button').classList.add('extension-matter-adapter-hidden');
    			});
                
                
                // Manually entered pairing code button
    			this.view.querySelector('#extension-matter-adapter-save-manual-input-pairing-code-button').addEventListener('click', () => {
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
				
                
    			this.view.querySelector('#extension-matter-adapter-pairing-network-question-normal-button').addEventListener('click', () => {
    				this.second_page_el.classList.remove('extension-matter-adapter-pairing-questioning');
                    this.second_page_el.classList.add('extension-matter-adapter-pairing-normal');
    			});
                
    			this.view.querySelector('#extension-matter-adapter-pairing-network-question-network-button').addEventListener('click', () => {
    				this.second_page_el.classList.remove('extension-matter-adapter-pairing-questioning');
                    this.second_page_el.classList.add('extension-matter-adapter-pairing-network');
    			});
                
                
                
            
                // Easter egg when clicking on the title
    			this.view.querySelector('#extension-matter-adapter-title').addEventListener('click', () => {
    				this.show();
    			});
                
    			this.view.querySelector('#extension-matter-adapter-refresh-paired-list-button').addEventListener('click', () => {
    				this.view.querySelector('#extension-matter-adapter-refresh-paired-list-button').classList.add('extension-matter-adapter-hidden');
                    this.view.querySelector('#extension-matter-adapter-paired-devices-list').innerHTML = '<div class="extension-matter-adapter-spinner"><div></div><div></div><div></div><div></div></div>';
                    this.get_init_data();
    			});
    			
				this.view.querySelector('#extension-matter-adapter-stop-refreshing-list-button').addEventListener('click', () => {
					this.stop_regenerating = true;
				});
				
				this.view.querySelector('#extension-matter-adapter-reset-customizations-button').addEventListener('click', () => {
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
                this.view.querySelector('#extension-matter-adapter-show-second-page-button').addEventListener('click', () => {
                    if(this.debug){
                        console.log("matter adapter debug: clicked on (+) button");
                    }
                    
                    // iPhones need this fix to make the back button lay on top of the main menu button
                    this.view.style.zIndex = '3';
                    this.view.querySelector('#extension-matter-adapter-content-container').classList.add('extension-matter-adapter-showing-second-page');
                    
                    this.show_pairing_page();
    			});
				
				this.view.querySelector('#extension-matter-adapter-pairing-accept-thing-button').addEventListener('click', () => {
					document.getElementById('add-button').click();
				});
                
                // SHOW WIFI PASSWORD CHECKBOX
                this.view.querySelector('#extension-matter-adapter-wifi-show-password-checkbox').addEventListener('change', () => {
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
				
				
				
				//
				// FIND THREAD RADIO
				//
				
				
                this.view.querySelector('#extension-matter-adapter-find-thread-radio-button').addEventListener('click', (event) => {
                    if(this.debug){
                        console.log("matter adapter debug: clicked on add a Thread radio button");
                    }
					
					this.view.querySelector('#extension-matter-adapter-find-thread-radio-button').classList.add('extension-matter-adapter-hidden');
					this.view.querySelector('#extension-matter-adapter-find-thread-radio-container').classList.remove('extension-matter-adapter-hidden');
					
    			});
				
				
                this.view.querySelector('#extension-matter-adapter-find-thread-radio-unplugged-button').addEventListener('click', (event) => {
                    if(this.debug){
                        console.log("matter adapter debug: clicked on find thread radio UNPLUGGED button");
                    }
					window.API.postJson(
						`/extensions/${this.id}/api/ajax`,
						{'action':'find_thread_radio_before'}
					).then((body) => { 
						
						this.view.querySelector('#extension-matter-adapter-find-thread-radio-step2').classList.remove('extension-matter-adapter-hidden');
						
					}).catch((err) => {
						console.error("matter-adapter: error calling find_thread_radio_before: ", err);
					});
					
    			});
				
                this.view.querySelector('#extension-matter-adapter-find-thread-radio-plugged-in-button').addEventListener('click', (event) => {
                    if(this.debug){
                        console.log("matter adapter debug: clicked on find thread radio PLUGGED IN button");
                    }
					window.API.postJson(
						`/extensions/${this.id}/api/ajax`,
						{'action':'find_thread_radio'}
					).then((body) => { 
						
						if(body.state === true){
							this.view.querySelector('#extension-matter-adapter-find-thread-radio-step1').classList.add('extension-matter-adapter-hidden');
							this.view.querySelector('#extension-matter-adapter-find-thread-radio-step2').classList.add('extension-matter-adapter-hidden');
							this.view.querySelector('#extension-matter-adapter-find-thread-radio-success').classList.remove('extension-matter-adapter-hidden');
							this.view.querySelector('#extension-matter-adapter-find-thread-radio-failed').classList.add('extension-matter-adapter-hidden');
						}
						else{
							this.view.querySelector('#extension-matter-adapter-find-thread-radio-success').classList.add('extension-matter-adapter-hidden');
							this.view.querySelector('#extension-matter-adapter-find-thread-radio-failed').classList.remove('extension-matter-adapter-hidden');
						}
						
					}).catch((err) => {
						console.error("matter-adapter: error calling find_thread_radio_before: ", err);
					});
					
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
							this.total_busy_polling_counter = 0;
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
					this.total_busy_polling_counter = 0;
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
							thread_details_el.innerHTML += '<span>No Thread radio detected</span><span style="font-style:italic">Only WiFi Matter devices can be paired</span>';
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
							console.warn("matter adapter: debug: thread_radio_is_alive_seconds_ago: ", body.thread_radio_is_alive_seconds_ago);
						}
						else{
							console.warn("matter adapter: debug: thread_radio_is_alive_seconds_ago was not a number: ", typeof body.thread_radio_is_alive_seconds_ago);
						}
					}
					
					if(typeof body.thread_radio_is_alive_seconds_ago == 'number'){
						if(body.thread_radio_is_alive_seconds_ago <= 60){
							thread_details_el.classList.remove('extension-matter-adapter-thread-radio-is-not-responding');
						}
						else{
							if(body.thread_radio_is_alive_seconds_ago > 60){
								if(body.thread_radio_is_alive_seconds_ago < 181){
									thread_details_el.innerHTML += '<span class="extension-matter-adapter-thread-radio-seems-down-warning">Thread radio last responded ' + body.thread_radio_is_alive_seconds_ago  + ' seconds ago</span>';
								}
								else if(body.thread_radio_is_alive_seconds_ago < 600){
									thread_details_el.innerHTML += '<span class="extension-matter-adapter-thread-radio-seems-down-warning">Thread radio last responded ' + Math.round(body.thread_radio_is_alive_seconds_ago/60)  + ' minutes ago</span>';
								}
								else{
									thread_details_el.innerHTML += '<span class="extension-matter-adapter-thread-radio-seems-down-warning">Thread will restart once the radio is plugged in again.</span>';
								}
							}
							thread_details_el.classList.add('extension-matter-adapter-thread-radio-is-not-responding');
						}
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
							pairing_progress_bar_container_el.style.background = 'rgba(0,0,0,.3)';
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
				
				if(typeof body.pairing_phase_message == 'string'){
					const pairing_progress_message_el = this.view.querySelector('#extension-matter-adapter-pairing-progress-message');
					if(pairing_progress_message_el){
						pairing_progress_message_el.textContent = body.pairing_phase_message;
					}
				}
				
				if(typeof body.pairing_attempt == 'number'){
					const pairing_attempt_el = this.view.querySelector('#extension-matter-adapter-pairing-attempt');
					if(pairing_attempt_el){
						pairing_attempt_el.textContent = "Pairing attempt " + body.pairing_attempt + " of 3";
					}
				}
				
				if(typeof body.extension_cable_recommended == 'boolean' && body.extension_cable_recommended == true){
					this.view.querySelector('#extension-matter-adapter-extension-cable-hint').classList.remove('extension-matter-adapter-hidden');
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
									this.total_busy_polling_counter = 0;
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
			this.total_busy_polling_counter = 0;
            
            if(this.debug){
                console.log("matter adapter debug: in show_pairing_page");
            }
            
            if (this.current_stream) {
              this.current_stream.getTracks().forEach(track => track.stop());
              this.current_stream = null;
            }
			
			if(this.scan_window){
				console.log("matter adapter: closing previously opened scan window");
				this.scan_window.close();
				this.scan_window = null;
			}
            
            window.API.postJson(
				`/extensions/${this.id}/api/ajax`,
				{'action':'reset_pairing'}
			).then((body) => { 
				if(this.debug){
                    console.log("reset pairing done");
                }
                this.busy_pairing = false;
			}).catch((err) => {
                this.busy_pairing = false;
				console.error("matter-adapter: error making reset pairing request: ", err);
			});
            
			
			this.generate_qr();
			
			
			if(window.matter_adapter_poll_interval){
				clearInterval(window.matter_adapter_poll_interval);
			}
			
			if(!this.second_page_el){
				this.second_page_el = this.view.querySelector('#extension-matter-adapter-second-page');
			}
			
            // Reset elements to start position
            
			this.second_page_el.classList.add('extension-matter-adapter-pairing-questioning');
            this.second_page_el.classList.remove('extension-matter-adapter-pairing-normal');
			this.second_page_el.classList.remove('extension-matter-adapter-pairing-network');
            this.second_page_el.classList.remove('extension-matter-adapter-busy-pairing');
			this.view.querySelector('#extension-matter-adapter-pairing-qr-choose-scanner-area').classList.remove('extension-matter-adapter-hidden');
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
					console.log("old_code_storage_time: ", old_code_storage_time);
					
					const two_hours_ago = Date.now() - 7200000;
					console.log("two hours ago: ", two_hours_ago);
					
					if(old_code_storage_time > two_hours_ago){
						this.view.querySelector('#extension-matter-adapter-pairing-code-input').value = old_pairing_code.split('----|----')[0];
						this.view.querySelector('#extension-matter-adapter-pairing-use-previously-scanned-code').classList.remove('extension-matter-adapter-hidden');
						if(this.debug){
							console.log("restored recent pairing code: ", this.view.querySelector('#extension-matter-adapter-pairing-code-input').value);
						}
					}
					else{
						if(this.debug){
							console.log("matter adapter debug: pairing code in local storage was too old, deleting it");
						}
						this.view.querySelector('#extension-matter-adapter-pairing-use-previously-scanned-code').classList.add('extension-matter-adapter-hidden');
						localStorage.removeItem('extension-matter-adapter-last-pairing-code');
					}
				}
			}
			
        }
    
    

        // is called once every few seconds by poll_interval
        pairing_poll(){
            if(this.debug){
                console.log("matter adapter debug: in pairing_poll.  this.busy_pairing, this.busy_polling_counter, this.total_busy_polling_counter: ", this.busy_pairing, this.busy_polling_counter, this.total_busy_polling_counter);
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
						if(this.debug){
                            console.log("matter adapter debug: pairing_poll: this.busy_pairing is now: ", this.busy_pairing);
						}
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
	                            console.log("matter adapter debug: busy updating certificates");
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
						if(this.debug){
                            console.log("matter adapter debug: body.decoded_pairing_code: ", body.decoded_pairing_code);
						}
						if(Array.isArray(body.decoded_pairing_code)){
							for(let l = 0; l < body.decoded_pairing_code.length; l++){
    							if(this.debug){
                                    console.log("matter adapter debug: decoded pairing code line: ", body.decoded_pairing_code[l]);
								}
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
										this.total_busy_polling_counter = 0;
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
					if(this.debug){
                        console.error("matter adapter debug: caught pairing poll error: ", err);
					}
	                this.view.querySelector('#extension-matter-adapter-start-normal-pairing-button').classList.remove('extension-matter-adapter-hidden');
				});
                
				
				this.busy_polling_counter++;
				
            }
            
			this.total_busy_polling_counter++;
			if(this.total_busy_polling_counter > 120){ // 10 minutes
				this.flash_message("Getting the QR code took too long");
				this.show_pairing_page();
			}
        }
        
        
        
        // Reveal the div with the actual normal pairing button
        show_pairing_start_area(){
            if(this.debug){
                console.log("matter adapter debug: in show_pairing_start_area");
            }
            if(this.pairing_code != ""){
                if(this.debug){
                    console.log("matter adapter debug: pairing code is available. Showing pairing start area.");
                }
				
	            if (this.current_stream) {
	              this.current_stream.getTracks().forEach(track => track.stop());
	              this.current_stream = null;
	            }
				
				this.view.querySelector('#extension-matter-adapter-pairing-start-area-vendor-name').textContent = this.get_vendor_from_mt_code(this.pairing_code);
				
                this.view.querySelector('#extension-matter-adapter-pairing-start-area').classList.remove('extension-matter-adapter-hidden');
                this.view.querySelector('#extension-matter-adapter-pairing-step-qr').classList.add('extension-matter-adapter-hidden');
                this.view.querySelector('#extension-matter-adapter-pairing-start-area-pairing-code').innerText = this.pairing_code;
            
				if(window.matter_adapter_poll_interval){
					clearInterval(window.matter_adapter_poll_interval);
					this.total_busy_polling_counter = 0;
				}
	            window.matter_adapter_poll_interval = null;
			}
            else{
                if(this.debug){
                    console.warn("matter adapter debug: WiFi credentials and pairing code are NOT both available yet. Not revealing pairing start area.");
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
                    if(this.debug){
						console.error('matter adapter: Error, target list element does not exist');
					}
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
                            console.log("matter adapter debug:  thing_id,item_data: ", thing_id, item_data); // device_id
                        }
                        //console.log("item_data: ", item_data);
						if(typeof item_data['node_id'] == 'undefined'){
							if(typeof thing_id == 'string' && thing_id.indexOf('matter-') != -1){
								item_data['node_id'] = parseInt(thing_id.replace('matter-'));
							}
							else{
								if(this.debug){
									console.error("matter adapter debug: regenerate_items: skipping, missing node_id in item data: ", item_data);
								}
								continue
							}
						}
                    	const my_node_id = item_data['node_id']
					
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
	                                //this.flash_message(item_data['software_version']);
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
						
                        
                        
                        
    					
    					const show_delete_button = clone.querySelector('.extension-matter-adapter-item-delete-button');
                        if(show_delete_button != null){
							if(!show_delete_button.classList.contains('extension-matter-adapter-listener-added')){
								show_delete_button.classList.add('extension-matter-adapter-listener-added');
								
        						if(this.debug){
									console.log("matter adapter debug: adding listeners to buttons for thing_id: ", thing_id);
								}
								
								
								// DELETE
								
		    					show_delete_button.addEventListener('click', (event) => {
									console.warn("CLICKED");
		                            if(this.debug){
		                                console.log("matter adapter debug: show delete overlay button clicked");
		                            }
		    						let item_el = event.currentTarget.closest(".extension-matter-adapter-item");
									if(item_el){
										item_el.classList.add("extension-matter-adapter-delete");
									}
									else{
										console.error("could not find closest parent item");
									}
	    						
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
		                                    console.log("matter adapter debug:Do event and item exist here?: ", event);
		                                }
		                                if(body.state == true){
		                                    this.nodez = body.nodez;
		                                    //let item_el = local_event.currentTarget.closest(".extension-matter-adapter-item");
		                                    if(typeof event.target != 'undefined'){
		                                        //console.log("in delete response, event.target exists");
		                                        let item_el = event.target.closest('extension-matter-adapter-item');
		                                        //console.log('item_el ', item_el);
		                                        item_el.classList.add("extension-matter-adapter-hidden");
		                                        //console.log("item_el.classList: ", item_el.classList);
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
		                                        this.flash_message(body.message);
		                                    }
		                                }

		    						}).catch((e) => {
		    							if(this.debug){
		                                    console.error('matter adapter debug: delete: connection error', e);
		                                    this.flash_message("An error occured during the delete process. Try reloading the page.");
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
								
								
								
								
								
								
								
								// UPATE
								
								const show_update_button = clone.querySelector('.extension-matter-adapter-item-update-button');
								if(show_update_button){
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
								}
	        					
                        
                    
							    
								
								
								
								
								
		                        // SHARE
                        
		                        // Share Matter device buttons
                        
		                        // Reveal share overlay
		    					const reveal_share_button = clone.querySelector('.extension-matter-adapter-item-reveal-share-button');
								if(reveal_share_button){
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
			    							{'action':'share_node','node_id':my_node_id}
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
                        
								}
		    					
                        
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
										
										const cluster_name = short_type.split('.Attributes.')[0];
										const attribute_name = short_type.split('.Attributes.')[1];
										
										let attribute_header_el = null;
										let attribute_el = endpoint_el.querySelector("." + attribute_class_name);
										if(!attribute_el){
											attribute_el = document.createElement('li');
											attribute_el.classList.add(attribute_class_name);
											
											
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
												//console.log("unique_id: ", unique_id);
												
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
															if(this.debug){
										                        console.log("matter adapter debug: change_attribute response was OK");
															}
								                        }
								                        else{
															if(this.debug){
										                        console.error("matter adapter debug: change_attribute failed?");
															}
								                        }
                    
								    				}).catch((err) => {
														if(this.debug){
									                        console.error("matter adapter debug: caught error calling change_attribute: ", err);
														}
								    				});
												});
												
												attribute_header_el.appendChild(enabled_checkbox_el);
												
												const enabled_checkbox_label_el = document.createElement('label');
												enabled_checkbox_label_el.setAttribute('for', unique_id);
												attribute_header_el.appendChild(enabled_checkbox_label_el);
												
												
											}
											if(typeof attribute['enabled'] == 'boolean'){
												enabled_checkbox_el.checked = attribute['enabled'];
											}
											else{
												enabled_checkbox_el.checked = false;
											}
											
										}
										
										if(!attribute_el){
											if(this.debug){
						                        console.error("matter adapter debug: no attribute_el?");
											}
											continue
										}
										
										if(attribute_name == 'AcceptedCommandList'){
											console.log("spotted AcceptedCommandList, does it have accepted_commands? ");
											console.log("typeof attribute['accepted_commands']: ", attribute['accepted_commands']);
										}
										
										// Add list of accepted commands
										if(typeof attribute['accepted_commands'] != 'undefined' && attribute['accepted_commands'] != null && Array.isArray(attribute['accepted_commands'])){
											console.warn("FOUND ACCEPTED COMMANDS: ", attribute['accepted_commands']);
											let accepted_commands_el = attribute_el.querySelector('.extension-matter-adapter-item-details-accepted-commands');
											if(!accepted_commands_el){
												accepted_commands_el = document.createElement('div');
												accepted_commands_el.classList.add('extension-matter-adapter-item-details-accepted-commands');
												accepted_commands_el.classList.add('extension-matter-adapter-area');
												accepted_commands_el.classList.add('extension-matter-adapter-show-if-developer');
												
												for(let ac = 0; ac < attribute['accepted_commands'].length; ac++){
													const accepted_command_el = document.createElement('span');
													accepted_command_el.textContent = attribute['accepted_commands'][ac];
													accepted_commands_el.appendChild(accepted_command_el);
												}
											}
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
																	if(this.debug){
												                        console.log("matter adapter debug: change_attribute response: ", body);
																	}
											                        if(body.state == true){
											                            console.log("change_attribute response was OK");
																		value_input_el.classList.add('extension-matter-adapter-green-bg');
																		setTimeout(() => {
																			value_input_el.classList.remove('extension-matter-adapter-green-bg');
																		},1000)
																		
											                        }
											                        else{
																		if(this.debug){
													                        console.error("matter adapter debug: change_attribute failed?");
																		}
											                        }
                    
											    				}).catch((err) => {
																	if(this.debug){
												                        console.error("matter adapter debug: caught error calling change_attribute: ", err);
																	}
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
 
 
		start_pairing(){
            const wifi_ssid = this.view.querySelector('#extension-matter-adapter-wifi-ssid').value;
            const wifi_password = this.view.querySelector('#extension-matter-adapter-wifi-password').value;
            const wifi_remember = this.view.querySelector('#extension-matter-adapter-wifi-remember-checkbox').value;
            
            this.view.querySelector('#extension-matter-adapter-pairing-failed-hint').classList.add('extension-matter-adapter-hidden');
            
            if(this.wifi_credentials_available == false){
                if(wifi_ssid.length < 2){
                    console.log("matter adapter: Wifi name is too short");
                    this.flash_message("That wifi name is too short");
                    return;
                }
                if(wifi_password.length < 8){
                    console.log("matter adapter: Wifi password is too short");
                    this.flash_message("That wifi password is too short");
                    return;
                }
            }
            
            const code = this.pairing_code;
            if(this.debug){
                console.log("matter adapter: Pairing code: ", code);
            }
            if(code.length < 5){
                console.log("matter adapter: pairing code was too short");
                this.flash_message("That pairing code is too short");
                return;
            }
            if(!code.startsWith('MT:')){
                console.log("matter adapter: pairing code did not start with MT:");
                this.flash_message("The pairing code should start with 'MT:'");
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
                        console.log("matter adapter debug: pair device via commission_with_code response: ", body);
                    }
					if(typeof body.state != 'undefined'){
						if(body.state == false){
							this.view.querySelector('#extension-matter-adapter-pairing-failed-hint').classList.remove('extension-matter-adapter-hidden');
							this.second_page_el.classList.remove('extension-matter-adapter-busy-pairing');
						}
						else if(body.state == true){
							if(this.debug){
		                        console.log("matter adapter debug: Matter server pairing process seems to have started succesfully");
							}
						}
					}
                
                
				}).catch((err) => {
                    this.busy_pairing = false;
					if(this.debug){
                        console.error("matter adapter debug: error making commission_with_code pairing request: ", err);
					}
                    //document.getElementById('extension-matter-adapter-start-normal-pairing-button').classList.remove('extension-matter-adapter-hidden');
				});
				
			}
		}
		
		
		/*
		scan_qr_code(){
			
			if (('BarcodeDetector' in window) && ((await BarcodeDetector.getSupportedFormats()).includes('qr_code'))) {
				console.log('BarcodeDetector is supported');
			
				// Get video element 
				const video_el = document.getElementById('qr-video');

				if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
					const constraints = {
						video: true,
						audio: false
					};
  
					navigator.mediaDevices.getUserMedia(constraints).then(stream => video_el.srcObject = stream);
				}
			
				// Detect code function 
				const detectCode = () => {
				  barcodeDetector.detect(video).then(codes => {
				    for (const barcode of codes)  {
						console.log("Found QR code: ", barcode);
					
						setResult('Matter',{'data':barcode.rawValue});
			      
				    }
				  }).catch(err => {
				    console.error("CAught error using barcodeDetector: ", err);
				  })
				}

		        document.getElementById('start-button').addEventListener('click', () => {
				
					if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
						const constraints = {
							video: true,
							audio: false
						};
  
						navigator.mediaDevices.getUserMedia(constraints).then(stream => video_el.srcObject = stream);
					
			            window.detecting_interval = setInterval(detectCode, 100);
			            document.getElementById('scanner-container').style.display = 'block';
			            document.getElementById('intro').style.display = 'none';
					
					}
		        });
			
			
			
			}
			
		}
		
		*/
		
		
		
		start_local_qr_scanner(){
			if(this.debug){
                console.log("matter adapter debug: in start_local_qr_scanner");
			}
			
			this.current_stream = null;
			
			const scanner_container_el = this.view.querySelector('#extension-matter-adapter-pairing-scanner-container');
			if(scanner_container_el){
				//scanner_container_el.innerHTML = '<div style="height:40rem;" class="extension-matter-adapter-flex-center extension-matter-adapter-area"><button>Scan QR code</button><span class="extension-matter-adapter-pairing-qr-choose-scanner-icon extension-matter-adapter-pairing-qr-choose-scanner-icon-camera"></span></div>';
				scanner_container_el.innerHTML = '';
			
				const create_qr_scanner = () => {
					if(this.debug){
                        console.log("matter adapter debug: in create_qr_scanner");
					}
					scanner_container_el.innerHTML = '';
					
					const extra_video_wrapper_el = document.createElement('div');
					extra_video_wrapper_el.setAttribute('id','extension-matter-adapter-pairing-scanner-extra-wrapper');
					
					const video_el = document.createElement('video');
					video_el.setAttribute('id','extension-matter-adapter-qr-scanner-video');
					extra_video_wrapper_el.appendChild(video_el);
				
					const canvas_el = document.createElement('canvas');
					canvas_el.setAttribute('id','extension-matter-adapter-qr-scanner-canvas');
					extra_video_wrapper_el.appendChild(canvas_el);
				
					const context = canvas_el.getContext('2d', { willReadFrequently: true });
				
					const screenshot_el = document.createElement('img');
					//screenshot_el.setAttribute('id','extension-matter-adapter-qr-scanner-screenshot');
					screenshot_el.setAttribute('id','extension-matter-adapter-qr-scanner-guide-lines');
					extra_video_wrapper_el.appendChild(screenshot_el);
					
					scanner_container_el.appendChild(extra_video_wrapper_el);
					
					
					const stop_qr_scanning_button_el = document.createElement('button');
					stop_qr_scanning_button_el.setAttribute('id','extension-matter-adapter-qr-scanner-stop-button');
					stop_qr_scanning_button_el.classList.add('text-button');
					stop_qr_scanning_button_el.textContent = 'Stop scanning';
					stop_qr_scanning_button_el.addEventListener('click', () => {
						turn_off_qr_scanner();
					});
					scanner_container_el.appendChild(stop_qr_scanning_button_el);
					
					/*
					const guide_lines_el = document.createElement('div');
					guide_lines_el.setAttribute('id','extension-matter-adapter-qr-scanner-guide-lines');
					scanner_container_el.appendChild(guide_lines_el);
					*/
					const guide_lines_el = screenshot_el;
				
					const constraints = {
						video: {
							width: { min: 1080, ideal: 4096 },
							height: { min: 1080, ideal: 2160 },
							facingMode: 'environment'
						},
						audio: false
					};
					//navigator.mediaDevices.getUserMedia(constraints).then(stream => video.srcObject = stream);
					//navigator.mediaDevices.getUserMedia(constraints).then(stream => video.srcObject = stream);
	
	
	
	
					const detectCode = () => {
						//console.log("detectCode:  barcodeDetector: ", typeof barcodeDetector, barcodeDetector);
						//console.log("in detectCode");
						if(video_el.videoWidth){
							//console.log("video_el.videoWidth: ", video_el.videoWidth);
							//console.log("video_el.videoHeight: ", video_el.videoHeight);
							//console.log("video.width: ", video_el.offsetWidth);
							//console.log("video.height: ", video_el.offsetHeight);
							//guide_canvas.width = video_el.videoWidth;
							//guide_canvas.height = video_el.videHeight;
							//guide_context.clearRect(0, 0, canvas.width, canvas.height);



							let x_offset = 0;
							let y_offset = 0;
							if(video_el.videoWidth > 640){
							  x_offset = (video_el.videoWidth - 640) / 2;
							}
							if(video_el.videoHeight > 640){
							  y_offset = (video_el.videoHeight - 640) / 2;
							}
							//console.log("x_offset: ", x_offset);
							//console.log("y_offset: ", y_offset);

							canvas_el.width = 640; //video_el.videoWidth;
							canvas_el.height = 640; //video_el.videoHeight;

							let x_factor = video_el.offsetWidth / video_el.videoWidth;
							let y_factor = video_el.offsetHeight / video_el.videoHeight;
							//console.log("x_factor: ", x_factor);
							let guide_x_offset = x_offset * x_factor;
							let guide_y_offset = y_offset * y_factor;
							//console.log("guide_x_offset: ", guide_x_offset);
							guide_lines_el.style.left = Math.round(guide_x_offset) + 'px';
							guide_lines_el.style.width = Math.round(640 * x_factor) + 'px';

							guide_lines_el.style.top = Math.round(guide_y_offset) + 'px';
							guide_lines_el.style.height = Math.round(640 * y_factor) + 'px';



							// Draw the center of the current video frame to the canvas
							context.drawImage(video_el, x_offset, y_offset, canvas_el.width, canvas_el.height, 0, 0, canvas_el.width, canvas_el.height);

							const clamp = (num) => Math.min(Math.max(num, 0), 254)
							
							function contrastImage(imgData, contrast, brightness=0){  //input range [-100..100]
								var d = imgData.data;
								contrast = (contrast/100) + 1;  //convert to decimal & shift range: [0..2]
								var intercept = 128 * (1 - contrast) + brightness;
								for(var i=0;i<d.length;i+=4){   //r,g,b,a
									d[i] = clamp(d[i]*contrast + intercept);
									d[i+1] = clamp(d[i+1]*contrast + intercept);
									d[i+2] = clamp(d[i+2]*contrast + intercept);
								}
								return imgData;
							}

							if(contrast_factor){
								let image_data = context.getImageData(0, 0, canvas_el.width, canvas_el.height);
								image_data = contrastImage(image_data, contrast_factor * 15, contrast_factor * 15);
								context.putImageData(image_data,0,0);
							}
							contrast_factor++;
							if(contrast_factor > 4){
								contrast_factor = 0;
							}

							// Convert canvas to image data URL
							const dataURL = canvas_el.toDataURL('image/png');
							//console.log("imageData: ", typeof imageData, imageData);

							screenshot_el.src = dataURL;
						}
						else{
							if(this.debug){
								console.error("matter adapter debug: video.videoWidth was zero");
							}
						}
					}
	
	
	
	
				    navigator.mediaDevices
				    .getUserMedia(constraints)
				    .then((stream) => {
						if(this.debug){
	                        console.log("matter adapter debug: GOT VIDEO STREAM.  video_el: ", video_el, stream);
						}
						this.current_stream = stream;
						video_el.srcObject = stream;
						video_el.play();
					
						video_el.detecting_interval = setInterval(detectCode, 250);
				    })
				    .catch((err) => {
						if(this.debug){
							console.error("matter adapter debug: caught error getting video stream: ", err);
						}
						turn_off_qr_scanner();
						
				    });
				
				
				
				
				
				
					let contrast_factor = 0;

					const barcodeDetector = new BarcodeDetector({ formats: ['qr_code'] });
					//console.log("barcodeDetector: ", barcodeDetector);
					// Detect code function 

					screenshot_el.addEventListener('load', () => {
						//console.log("screenshot loaded");
						barcodeDetector.detect(screenshot_el)
						.then(codes => {
							//console.log("barcode codes: ", codes);
	  
							for (const barcode of codes)  {
								if(this.debug){
			                        console.log("matter adapter debug: Found QR code: ", barcode);
								}
							
								if(typeof barcode.rawValue == 'string'){
									
									const raw_code = "" + barcode.rawValue;
									if(this.debug){
				                        console.log("matter adapter debug: raw_code: ", raw_code);
									}
									let matter_code = '';
									//let codes = raw_code.match(/(MT:[A-Z0-9]{5}[^a-zA-Z\d\s][A-Z0-9]{13})/g);
									let codes = raw_code.match(/(MT:[A-Z0-9-.]{19})/g);
									
	
									if(codes && codes.length){
										matter_code = codes[0];
									}
									else{
										//codes = decodeURIComponent(raw_code).match(/(MT:[A-Z0-9]{5}-[A-Z0-9]{13})/g);
										codes = decodeURIComponent(raw_code).match(/(MT:[A-Z0-9-.]{19})/g);
										if(codes && codes.length){
											matter_code = codes[0];
										}
									}
									if(this.debug){
				                        console.log("matter adapter debug: matter-code?: ", matter_code);
									}
						            if(typeof matter_code == 'string' && matter_code.startsWith("MT:")){
										
										if(this.debug){
					                        console.log("matter adapter debug: FOUND A VALID MATTER CODE");
										}
										
										if(video_el && video_el.detecting_interval){
											clearInterval(video_el.detecting_interval);
										}
										
										//setResult('Matter',{'data':barcode.rawValue});
										scanner_container_el.innerHTML = '<p>Got it!</p><p>' + matter_code + '</p>';
										//turn_off_qr_scanner();
								
				                        this.pairing_code = barcode.rawValue;
            							
				                        this.view.querySelector('#extension-matter-adapter-pairing-code-input').value = this.pairing_code;
            							
				                        this.show_pairing_start_area();
										
										localStorage.setItem('extension-matter-adapter-last-pairing-code', this.pairing_code + '----|----' + Date.now() );
										
										
										
									}
									
									
								}
								
							}
						})
						.catch(err => {
							if(this.debug){
		                        console.error("matter adapter debug: Caught error using barcodeDetector: ", err);
							}
							if(video_el.detecting_interval){
								clearInterval(video_el.detecting_interval);
							}
							//test_el.innerHTML = '<h1>' + err + '</h1>';
							//start_scan_fallback();
							turn_off_qr_scanner();
							this.generate_qr();
						})
					});
				}
			
			
				const turn_off_qr_scanner = () => {
					
		            if (this.current_stream) {
		              this.current_stream.getTracks().forEach(track => track.stop());
		              this.current_stream = null;
		            }

					//const current_video_stream_el = this.view.querySelector('#extension-matter-adapter-qr-scanner-video');
		            //if (current_video_stream_el) {
					//	current_video_stream_el.srcObject = null;
					//}
					
					scanner_container_el.innerHTML = '';
					
					const start_qr_scanner_button_el = document.createElement('div');
					start_qr_scanner_button_el.setAttribute('id','extension-matter-adapter-pairing-start-qr-scanner-button');
					
					const start_qr_scanner_title_el = document.createElement('h3');
					start_qr_scanner_title_el.textContent = 'Start QR code scanner';
					start_qr_scanner_button_el.appendChild(start_qr_scanner_title_el);
					
					const start_qr_scanner_icon_el = document.createElement('span');
					start_qr_scanner_icon_el.classList.add('extension-matter-adapter-pairing-qr-choose-scanner-icon');
					start_qr_scanner_icon_el.classList.add('extension-matter-adapter-pairing-qr-choose-scanner-icon-camera');
					start_qr_scanner_button_el.appendChild(start_qr_scanner_icon_el);
					
					start_qr_scanner_button_el.addEventListener('click', () => {
						create_qr_scanner();
					})
					scanner_container_el.appendChild(start_qr_scanner_button_el);
				}
			
				create_qr_scanner();
				//turn_off_qr_scanner();

				/*
				const constraints = {
					video: true,
					audio: false
				};

				navigator.mediaDevices.getUserMedia(constraints).
				then((stream) => {
					video.srcObject = stream;
	
	
				});
				*/
			

		        //document.getElementById('start-button').addEventListener('click', () => {

	
				
	
					/*
    
	

		
	
	
    
					*/
				
	
					/*
					navigator.mediaDevices.getUserMedia(constraints).then(stream => video.srcObject = stream);
	
					navigator.mediaDevices.getUserMedia(constraints)
					.then((stream) => {
						video_el.srcObject = stream;
		
			            window.detecting_interval = setInterval(detectCode, 1000);
        
	
					});
					*/
		            //document.getElementById('scanner-container').style.display = 'block';
		           	//document.getElementById('intro').style.display = 'none';

    

	
				//});
		
			}
			else{
				if(this.debug){
                    console.error("matter adapter debug: missing qr scanner container");
				}
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
            
			this.matter_qr_scanner_url = long_url;
			this.view.querySelector('#extension-matter-adapter-qr-scan-link').href = long_url;
            //this.view.querySelector('#extension-matter-adapter-pairing-qr-choose-scanner-camera').href = long_url;
            this.view.querySelector('#extension-matter-adapter-mobile-qr-scan-link').href = long_url;
            
            const target_element = this.view.querySelector('#extension-matter-adapter-qr-code');
	        target_element.innerHTML = "";
    		
    	    var qrcode = new QRCode(target_element, {
    		    width : 300,
    		    height : 300
    	    });
    	    qrcode.makeCode(long_url);
        }
		
		
		
		flash_message(message){
			if(typeof message == 'string' && message.length){
				const flash_message_el = document.getElementById('extension-candleappstore-flash-message-container');
				if(flash_message_el){
					flash_message_el.innerHTML = '<h3>' + message + '</h3>';
					setTimeout(() => {
						flash_message_el.innerHTML = '';
					},3000);
				}
				else{
					alert(message);
				}
			}
		}
		
		
		
		
		get_vendor_from_mt_code(mt_code){
			
			if(typeof mt_code != 'string'){
				console.error("get_vendor_from_mt_code: provided mt_code was not a string: ", mt_code);
				return ''
			}
			
            if (!mt_code.startsWith('MT:')) {
             	console.error("mt_code did not start with MT:");
				return ''
            }

            
            if (mt_code.length < 20) {
				console.error("mt_code was too short");
				return ''
            }
			
			const encoded_part = mt_code.substring(3);
			
			function decode_base_38(encoded_part){
				const char_array = encoded_part.split("").map(char => char.charCodeAt(0) - 48);
				console.log("get_vendor_from_mt_code: char_array: ", char_array);
				let total_decimal = 0;
				for (let ca = 0; ca < char_array.length; ca++) {
					total_decimal += char_array[ca] * Math.pow(38, (char_array.length - ca) - 1);
				}
				console.log("get_vendor_from_mt_code: total_decimal: ", total_decimal);
				return total_decimal.toString();
			}
			
			
			
	        const BASE38_CHARS = [
	          '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I',
	          'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '-', '.'
	        ];

	        function base38Decode(str) {
	          const result = [];

	          for (let i = 0; i < str.length; ) {
	            let chunkSize, byteCount;

	            if (i + 5 <= str.length) {
	              chunkSize = 5;
	              byteCount = 3;
	            } else if (i + 4 <= str.length) {
	              chunkSize = 4;
	              byteCount = 2;
	            } else if (i + 2 <= str.length) {
	              chunkSize = 2;
	              byteCount = 1;
	            } else {
	              throw new Error('Invalid base38 string length');
	            }

	            let value = 0;
	            for (let j = 0; j < chunkSize; j++) {
	              const char = str[i + j];
	              const index = BASE38_CHARS.indexOf(char);
	              if (index === -1) {
	                throw new Error(`Invalid character: ${char}`);
	              }
	              value += index * Math.pow(38, j);
	            }

	            for (let j = 0; j < byteCount; j++) {
	              result.push(value & 0xFF);
	              value >>= 8;
	            }

	            i += chunkSize;
	          }

	          return new Uint8Array(result);
	        }
			
			const decoded_mt_code = base38Decode(encoded_part)
			
			
			console.log("get_vendor_from_mt_code: decoded_mt_code: ", decoded_mt_code);

	        function get_bits(encoded_part, starting_position=3, desired_length=16) {
				let output = 0;

				for (let i = 0; i < desired_length; i++) {
		            const bit_index = starting_position + i;
		            const byte_index = Math.floor(bit_index / 8);
		            const bit_offset = bit_index % 8;

		            if (byte_index >= encoded_part.length){
						break
					}

		            const bit = (encoded_part[byte_index] >> bit_offset) & 1;
		            output |= (bit << i);
				}

				return output;
	        }
			
            const raw_vendor_id = get_bits(decoded_mt_code);
			console.log("get_vendor_from_mt_code: raw vendor_id: ", raw_vendor_id);
            return this.vendor_id_lookup(raw_vendor_id);
			
		}
		
		
		
		
		
		vendor_id_lookup(vendor_id){
			const matter_vendors_lookup = {
    "1": {
        "legal": "Panasonic Holdings Corporation",
        "url": "https://holdings.panasonic/global/",
        "vendor": "Panasonic"
    },
    "2": {
        "vendor": "Sony"
    },
    "3": {
        "vendor": "Samsung"
    },
    "4": {
        "vendor": "Philips"
    },
    "5": {
        "vendor": "Freescale"
    },
    "6": {
        "vendor": "Oki Semiconductors"
    },
    "7": {
        "vendor": "Texas Instruments"
    },
    "4096": {
        "vendor": "Cirronet"
    },
    "4097": {
        "vendor": "Chipcon"
    },
    "4098": {
        "vendor": "Ember"
    },
    "4099": {
        "vendor": "NTS"
    },
    "4100": {
        "vendor": "Freescale"
    },
    "4101": {
        "vendor": "IP Com"
    },
    "4102": {
        "vendor": "San Juan Software"
    },
    "4103": {
        "vendor": "TUV"
    },
    "4104": {
        "vendor": "Integration"
    },
    "4105": {
        "vendor": "BM SpA"
    },
    "4106": {
        "vendor": "AwarePoint"
    },
    "4107": {
        "legal": "Signify Netherlands B.V.",
        "url": "https://www.signify.com/",
        "vendor": "Signify"
    },
    "4108": {
        "vendor": "Luxoft"
    },
    "4109": {
        "vendor": "Korwin"
    },
    "4110": {
        "vendor": "One RF Technology"
    },
    "4111": {
        "vendor": "Software Technologies Group"
    },
    "4112": {
        "vendor": "Telegesis"
    },
    "4113": {
        "vendor": "Visonic"
    },
    "4114": {
        "vendor": "Insta"
    },
    "4115": {
        "vendor": "Atalum"
    },
    "4116": {
        "vendor": "Atmel"
    },
    "4117": {
        "vendor": "Develco"
    },
    "4118": {
        "vendor": "Honeywell"
    },
    "4119": {
        "vendor": "RadioPulse"
    },
    "4120": {
        "vendor": "Renesas"
    },
    "4121": {
        "vendor": "Xanadu Wireless"
    },
    "4122": {
        "vendor": "NEC Engineering"
    },
    "4123": {
        "vendor": "Yamatake Corporation"
    },
    "4124": {
        "vendor": "Tendril Networks"
    },
    "4125": {
        "legal": "Fortune Brands Innovation Inc",
        "url": "https://www.fbin.com/",
        "vendor": "Fortune Brands"
    },
    "4126": {
        "vendor": "MaxStream"
    },
    "4127": {
        "vendor": "Neurocom"
    },
    "4128": {
        "vendor": "Institute for Information Industry"
    },
    "4129": {
        "legal": "Legrand",
        "url": "https://www.legrand.com",
        "vendor": "Legrand Group"
    },
    "4130": {
        "vendor": "iControl"
    },
    "4131": {
        "vendor": "Raymarine"
    },
    "4132": {
        "vendor": "LS Research"
    },
    "4133": {
        "vendor": "Onity Inc."
    },
    "4134": {
        "vendor": "Mono Products"
    },
    "4135": {
        "vendor": "RF Technologies"
    },
    "4136": {
        "vendor": "Itron"
    },
    "4137": {
        "vendor": "Tritech"
    },
    "4138": {
        "vendor": "Embedit A/S"
    },
    "4139": {
        "vendor": "S3C"
    },
    "4140": {
        "vendor": "Siemens"
    },
    "4141": {
        "vendor": "Mindtech"
    },
    "4142": {
        "legal": "LG Electronics, Inc.",
        "vendor": "LG Electronics"
    },
    "4143": {
        "vendor": "Mitsubishi Electric Corp."
    },
    "4144": {
        "vendor": "Johnson Controls"
    },
    "4145": {
        "vendor": "Secure Meters (UK) Ltd"
    },
    "4146": {
        "vendor": "Knick"
    },
    "4147": {
        "vendor": "Viconics"
    },
    "4148": {
        "vendor": "Flexipanel"
    },
    "4149": {
        "vendor": "Piasim Corporation Pte., Ltd."
    },
    "4150": {
        "vendor": "Trane"
    },
    "4151": {
        "legal": "NXP Semiconductors N.V.",
        "url": "https://www.nxp.com",
        "vendor": "NXP Semiconductors"
    },
    "4152": {
        "vendor": "Living Independently Group"
    },
    "4153": {
        "vendor": "AlertMe.com"
    },
    "4154": {
        "vendor": "Daintree"
    },
    "4155": {
        "vendor": "Aiji System"
    },
    "4156": {
        "vendor": "Telecom Italia"
    },
    "4157": {
        "vendor": "Mikrokrets AS"
    },
    "4158": {
        "vendor": "Oki Semiconductor"
    },
    "4159": {
        "vendor": "Newport Electonics"
    },
    "4160": {
        "vendor": "Control 4"
    },
    "4161": {
        "legal": "STMicroelectronics"
    },
    "4162": {
        "vendor": "Ad-Sol Nissin Corp"
    },
    "4163": {
        "vendor": "DCSI"
    },
    "4164": {
        "vendor": "France Telecom"
    },
    "4165": {
        "vendor": "muNet"
    },
    "4166": {
        "vendor": "Autani Corporation"
    },
    "4167": {
        "vendor": "Colorado vNet"
    },
    "4168": {
        "vendor": "Aerocomm, Inc."
    },
    "4169": {
        "legal": "Silicon Laboratories Inc NASDAQ: SLAB",
        "url": "https://www.silabs.com/",
        "vendor": "Silicon Labs"
    },
    "4170": {
        "vendor": "Inncom International Inc."
    },
    "4171": {
        "vendor": "Cooper Power Systems"
    },
    "4172": {
        "vendor": "Synapse"
    },
    "4173": {
        "vendor": "Fisher Pierce/Sunrise"
    },
    "4174": {
        "vendor": "CentraLite Systems, Inc."
    },
    "4175": {
        "vendor": "Crane Wireless Monitoring Solutions"
    },
    "4176": {
        "vendor": "Mobilarm Limited"
    },
    "4177": {
        "vendor": "iMonitor Research Ltd."
    },
    "4178": {
        "vendor": "Bartech"
    },
    "4179": {
        "vendor": "MeshNetics"
    },
    "4180": {
        "vendor": "LS Industrial Systems Co. Ltd."
    },
    "4181": {
        "vendor": "Cason Engineering plc"
    },
    "4182": {
        "vendor": "Wireless Glue Networks Inc."
    },
    "4183": {
        "vendor": "Elster"
    },
    "4184": {
        "vendor": "SMS Tecnologia Eletro;nica"
    },
    "4185": {
        "vendor": "Onset Computer Corporation"
    },
    "4186": {
        "vendor": "Riga Development"
    },
    "4187": {
        "vendor": "Energate"
    },
    "4188": {
        "vendor": "ConMed Linvatec"
    },
    "4189": {
        "vendor": "PowerMand"
    },
    "4190": {
        "legal": "Schneider Electric"
    },
    "4191": {
        "vendor": "Eaton Corporation"
    },
    "4192": {
        "vendor": "Telular Corporation"
    },
    "4193": {
        "vendor": "Delphi Medical Systems"
    },
    "4194": {
        "vendor": "EpiSensor Limited"
    },
    "4195": {
        "vendor": "Landis+Gyr"
    },
    "4196": {
        "vendor": "Kaba Group"
    },
    "4197": {
        "vendor": "Shure Incorporated"
    },
    "4198": {
        "vendor": "Comverge, Inc."
    },
    "4199": {
        "vendor": "DBS Lodging Technologies, LLC."
    },
    "4200": {
        "vendor": "Energy Aware Technology Inc."
    },
    "4201": {
        "vendor": "Hidalgo Limited"
    },
    "4202": {
        "vendor": "Air2App"
    },
    "4203": {
        "vendor": "AMX"
    },
    "4204": {
        "vendor": "EDMI Pty Ltd"
    },
    "4205": {
        "vendor": "Cyan Ltd"
    },
    "4206": {
        "vendor": "System SPA"
    },
    "4207": {
        "vendor": "Telit"
    },
    "4208": {
        "vendor": "Kaga Electronics"
    },
    "4209": {
        "vendor": "Astrel Group SRL"
    },
    "4210": {
        "vendor": "Certicom"
    },
    "4211": {
        "vendor": "Gridpoint"
    },
    "4212": {
        "vendor": "Profile Systems LLC"
    },
    "4213": {
        "vendor": "Compacta International Ltd"
    },
    "4214": {
        "vendor": "Freestyle Technology Pty Ltd."
    },
    "4215": {
        "vendor": "Alektrona"
    },
    "4216": {
        "legal": "Computime Limited",
        "vendor": "ntve home"
    },
    "4217": {
        "vendor": "Remote Technologies, Inc."
    },
    "4218": {
        "vendor": "Wavecom S.A."
    },
    "4219": {
        "vendor": "Energy Optimizers Ltd."
    },
    "4220": {
        "vendor": "GE"
    },
    "4221": {
        "vendor": "Jetlun"
    },
    "4222": {
        "vendor": "Cipher Systems"
    },
    "4223": {
        "vendor": "Corporate Systems Engineering"
    },
    "4224": {
        "vendor": "ecobee"
    },
    "4225": {
        "vendor": "SMK"
    },
    "4226": {
        "vendor": "Meshworks Wireless Oy"
    },
    "4227": {
        "vendor": "Ellips B.V."
    },
    "4228": {
        "vendor": "Secure electrans"
    },
    "4229": {
        "vendor": "CEDO"
    },
    "4230": {
        "vendor": "Toshiba"
    },
    "4231": {
        "vendor": "Digi International"
    },
    "4232": {
        "vendor": "Ubilogix"
    },
    "4233": {
        "vendor": "Echelon"
    },
    "4240": {
        "legal": "Green Energy Options Ltd",
        "url": "https://www.geotogether.com/",
        "vendor": "Green Energy Options"
    },
    "4241": {
        "vendor": "Silver Spring Networks"
    },
    "4242": {
        "vendor": "Black  and  Decker"
    },
    "4243": {
        "vendor": "Aztech Associates Inc."
    },
    "4244": {
        "vendor": "A and D Co., Ltd."
    },
    "4245": {
        "vendor": "Rainforest Automation"
    },
    "4246": {
        "vendor": "Carrier Electronics"
    },
    "4247": {
        "vendor": "SyChip/Murata"
    },
    "4248": {
        "vendor": "OpenPeak"
    },
    "4249": {
        "vendor": "PassiveSystems"
    },
    "4250": {
        "vendor": "MMB Research"
    },
    "4251": {
        "legal": "Leviton Manufacturing Company",
        "url": "https://www.leviton.com",
        "vendor": "Leviton"
    },
    "4252": {
        "vendor": "Korea Electric Power Data Network Co., Ltd."
    },
    "4253": {
        "vendor": "Comcast"
    },
    "4254": {
        "vendor": "NEC Electronics"
    },
    "4255": {
        "vendor": "Netvox"
    },
    "4256": {
        "vendor": "U-Control"
    },
    "4257": {
        "vendor": "Embedia Technologies Corp"
    },
    "4258": {
        "vendor": "Sensus"
    },
    "4259": {
        "vendor": "Sunrise Technologies"
    },
    "4260": {
        "vendor": "Memtech Corp"
    },
    "4261": {
        "vendor": "Freebox"
    },
    "4262": {
        "vendor": "M2 Labs Ltd."
    },
    "4263": {
        "vendor": "British Gas"
    },
    "4264": {
        "vendor": "Sentec Ltd."
    },
    "4265": {
        "vendor": "Navetas"
    },
    "4266": {
        "vendor": "Lightspeed Technologies"
    },
    "4267": {
        "vendor": "Oki Electric Industry Co., Ltd."
    },
    "4268": {
        "vendor": "S I - Sistemas Inteligentes Eletro;nicos Ltda"
    },
    "4269": {
        "vendor": "Dometic"
    },
    "4270": {
        "vendor": "Alps"
    },
    "4271": {
        "vendor": "EnergyHub"
    },
    "4272": {
        "vendor": "Kamstrup"
    },
    "4273": {
        "vendor": "EchoStar"
    },
    "4274": {
        "vendor": "EnerNOC"
    },
    "4275": {
        "vendor": "Eltav"
    },
    "4276": {
        "vendor": "Belkin"
    },
    "4277": {
        "vendor": "XStreamHD - Wireless Ventures"
    },
    "4278": {
        "vendor": "Saturn South Pty Ltd"
    },
    "4279": {
        "vendor": "GreenTrapOnline A/S"
    },
    "4280": {
        "vendor": "SmartSynch, Inc."
    },
    "4281": {
        "vendor": "Nyce Control, Inc."
    },
    "4282": {
        "vendor": "ICM Controls Corp"
    },
    "4283": {
        "vendor": "Millennium Electronics, PTY Ltd."
    },
    "4284": {
        "vendor": "Motorola, Inc"
    },
    "4285": {
        "vendor": "Emerson White-Rodgers"
    },
    "4286": {
        "vendor": "Radio Thermostat Company of America"
    },
    "4287": {
        "vendor": "OMRON Corporation"
    },
    "4288": {
        "vendor": "GiiNii Global Limited"
    },
    "4289": {
        "vendor": "Fujitsu General Limited"
    },
    "4290": {
        "vendor": "Peel Technologies, Inc."
    },
    "4291": {
        "vendor": "Accent S.p.A."
    },
    "4292": {
        "vendor": "ByteSnap Design Ltd."
    },
    "4293": {
        "vendor": "NEC TOKIN Corporation"
    },
    "4294": {
        "vendor": "G4S Justice Services"
    },
    "4295": {
        "vendor": "Trilliant Networks, Inc."
    },
    "4296": {
        "vendor": "Electrolux Italia S.p.A"
    },
    "4297": {
        "vendor": "Onzo Ltd"
    },
    "4298": {
        "vendor": "EnTek Systems"
    },
    "4299": {
        "vendor": "Philips"
    },
    "4300": {
        "vendor": "Mainstream Engineering"
    },
    "4301": {
        "vendor": "Indesit Company"
    },
    "4302": {
        "vendor": "THINKECO, INC."
    },
    "4303": {
        "vendor": "2D2C, Inc."
    },
    "4304": {
        "legal": "Qorvo, Inc.",
        "url": "https://www.qorvo.com/",
        "vendor": "Qorvo"
    },
    "4305": {
        "vendor": "InterCEL"
    },
    "4306": {
        "vendor": "LG Electronics"
    },
    "4307": {
        "vendor": "Mitsumi Electric Co.,Ltd."
    },
    "4308": {
        "vendor": "Mitsumi Electric Co.,Ltd."
    },
    "4309": {
        "vendor": "Zentrum Mikroelektronik Dresden AG (ZMDI)"
    },
    "4310": {
        "vendor": "Nest Labs, Inc."
    },
    "4311": {
        "vendor": "Exegin Technologies, Ltd."
    },
    "4312": {
        "vendor": "Honeywell"
    },
    "4313": {
        "vendor": "Takahata Precision Co. Ltd."
    },
    "4314": {
        "vendor": "SUMITOMO ELECTRIC NETWORKS, INC."
    },
    "4315": {
        "vendor": "GE Energy"
    },
    "4316": {
        "vendor": "GE Appliances"
    },
    "4317": {
        "vendor": "Radiocrafts AS"
    },
    "4318": {
        "vendor": "Ceiva"
    },
    "4319": {
        "vendor": "TEC and CO Co., Ltd"
    },
    "4320": {
        "vendor": "Chameleon Technology (UK) Ltd"
    },
    "4321": {
        "vendor": "Samsung"
    },
    "4322": {
        "vendor": "ruwido austria gmbh"
    },
    "4323": {
        "vendor": "Huawei Technologies Co., Ltd."
    },
    "4324": {
        "vendor": "Huawei Technologies Co., Ltd."
    },
    "4325": {
        "vendor": "Greenwave Reality"
    },
    "4326": {
        "vendor": "BGlobal Metering Ltd"
    },
    "4327": {
        "vendor": "Mindteck"
    },
    "4328": {
        "vendor": "Ingersoll-Rand"
    },
    "4329": {
        "vendor": "Dius Computing Pty Ltd"
    },
    "4330": {
        "vendor": "Embedded Automation, Inc."
    },
    "4331": {
        "vendor": "ABB"
    },
    "4332": {
        "vendor": "Sony"
    },
    "4333": {
        "vendor": "Genus Power Infrastructures Limited"
    },
    "4334": {
        "legal": "Universal Electronics Inc",
        "url": "https://www.uei.com/",
        "vendor": "UEI"
    },
    "4335": {
        "vendor": "Universal Electronics, Inc."
    },
    "4336": {
        "vendor": "Metrum Technologies, LLC"
    },
    "4337": {
        "vendor": "Cisco"
    },
    "4338": {
        "legal": "ubisys technologies GmbH",
        "url": "https://www.ubisys.de",
        "vendor": "ubisys"
    },
    "4339": {
        "vendor": "Consert"
    },
    "4340": {
        "vendor": "Crestron Electronics"
    },
    "4341": {
        "vendor": "Enphase Energy"
    },
    "4342": {
        "vendor": "Invensys Controls"
    },
    "4343": {
        "vendor": "Mueller Systems, LLC"
    },
    "4344": {
        "vendor": "AAC Technologies Holding"
    },
    "4345": {
        "vendor": "U-NEXT Co., Ltd"
    },
    "4346": {
        "vendor": "Steelcase Inc."
    },
    "4347": {
        "vendor": "Telematics Wireless"
    },
    "4348": {
        "vendor": "Samil Power Co., Ltd"
    },
    "4349": {
        "vendor": "Pace Plc"
    },
    "4350": {
        "vendor": "Osborne Coinage Co."
    },
    "4351": {
        "vendor": "Powerwatch"
    },
    "4352": {
        "vendor": "CANDELED GmbH"
    },
    "4353": {
        "vendor": "FlexGrid S.R.L"
    },
    "4354": {
        "vendor": "Humax"
    },
    "4355": {
        "vendor": "Universal Devices"
    },
    "4356": {
        "vendor": "Advanced Energy"
    },
    "4357": {
        "vendor": "BEGA Gantenbrink-Leuchten"
    },
    "4358": {
        "vendor": "Brunel University"
    },
    "4359": {
        "vendor": "Panasonic R and D Center Singapore"
    },
    "4360": {
        "vendor": "eSystems Research"
    },
    "4361": {
        "vendor": "Panamax"
    },
    "4362": {
        "legal": "Samsung SmartThings"
    },
    "4363": {
        "vendor": "EM-Lite Ltd."
    },
    "4364": {
        "vendor": "Osram Sylvania"
    },
    "4365": {
        "vendor": "2 Save Energy Ltd."
    },
    "4366": {
        "vendor": "Planet Innovation Products Pty Ltd"
    },
    "4367": {
        "vendor": "Ambient Devices, Inc."
    },
    "4368": {
        "vendor": "Profalux"
    },
    "4369": {
        "vendor": "Billion Electric Company (BEC)"
    },
    "4370": {
        "vendor": "Embertec Pty Ltd"
    },
    "4371": {
        "vendor": "IT Watchdogs"
    },
    "4372": {
        "vendor": "Reloc"
    },
    "4373": {
        "vendor": "Intel Corporation"
    },
    "4374": {
        "vendor": "Trend Electronics Limited"
    },
    "4375": {
        "vendor": "Moxa"
    },
    "4376": {
        "vendor": "QEES"
    },
    "4377": {
        "vendor": "SAYME Wireless Sensor Networks"
    },
    "4378": {
        "vendor": "Pentair Aquatic Systems"
    },
    "4379": {
        "vendor": "Orbit Irrigation"
    },
    "4380": {
        "vendor": "California Eastern Laboratories"
    },
    "4381": {
        "legal": "Comcast",
        "url": "https://www.xfinity.com/",
        "vendor": "Comcast Communications"
    },
    "4382": {
        "vendor": "IDT Technology Limited"
    },
    "4383": {
        "vendor": "Pixela Corporation"
    },
    "4384": {
        "vendor": "TiVo, Inc."
    },
    "4385": {
        "vendor": "Fidure Corp."
    },
    "4386": {
        "vendor": "Marvell Semiconductor, Inc."
    },
    "4387": {
        "vendor": "Wasion Group Limited"
    },
    "4388": {
        "legal": "Jasco Products Company LLC"
    },
    "4389": {
        "vendor": "Shenzhen Kaifa Technology (Chengdu) Co., Ltd."
    },
    "4390": {
        "vendor": "Netcomm Wireless Limited"
    },
    "4391": {
        "vendor": "Define Instruments Limited"
    },
    "4392": {
        "vendor": "In Home Displays Ltd."
    },
    "4393": {
        "vendor": "Miele  and  Cie. KG"
    },
    "4394": {
        "vendor": "Televes S.A."
    },
    "4395": {
        "vendor": "Labelec"
    },
    "4396": {
        "vendor": "China Electronics Standardization Institute"
    },
    "4397": {
        "vendor": "Vectorform, LLC"
    },
    "4398": {
        "vendor": "Busch-Jaeger Elektro"
    },
    "4399": {
        "vendor": "Redpine Signals, Inc."
    },
    "4400": {
        "vendor": "Bridges Electronic Technology Pty Ltd."
    },
    "4401": {
        "vendor": "Sercomm"
    },
    "4402": {
        "vendor": "WSH GmbH wirsindheller"
    },
    "4403": {
        "vendor": "Bosch Security Systems, Inc."
    },
    "4404": {
        "vendor": "eZEX Corporation"
    },
    "4405": {
        "legal": "dresden elektronik ingenieurtechnik gmbh",
        "url": "https://www.dresden-elektronik.de",
        "vendor": "dresden elektronik"
    },
    "4406": {
        "vendor": "MEAZON S.A."
    },
    "4407": {
        "vendor": "Crow Electronic Engineering Ltd."
    },
    "4408": {
        "vendor": "Harvard Engineering Plc"
    },
    "4409": {
        "vendor": "Andson(Beijing) Technology CO.,Ltd"
    },
    "4410": {
        "vendor": "Adhoco AG"
    },
    "4411": {
        "vendor": "Waxman Consumer Products Group, Inc."
    },
    "4412": {
        "vendor": "Owon Technology, Inc."
    },
    "4413": {
        "vendor": "Hitron Technologies, Inc."
    },
    "4414": {
        "vendor": "Scemtec Hard - und Software fur Mess - und Steuerungstechnik GmbH"
    },
    "4415": {
        "vendor": "Webee LLC"
    },
    "4416": {
        "vendor": "Grid2Home Inc"
    },
    "4417": {
        "vendor": "Telink Micro"
    },
    "4418": {
        "vendor": "Jasmine Systems, Inc."
    },
    "4419": {
        "vendor": "Bidgely"
    },
    "4420": {
        "vendor": "Lutron"
    },
    "4421": {
        "vendor": "IJENKO"
    },
    "4422": {
        "vendor": "Starfield Electronic Ltd."
    },
    "4423": {
        "vendor": "TCP, Inc."
    },
    "4424": {
        "vendor": "Rogers Communications Partnership"
    },
    "4425": {
        "vendor": "Cree, Inc."
    },
    "4426": {
        "vendor": "Robert Bosch LLC"
    },
    "4427": {
        "vendor": "Ibis Networks, Inc."
    },
    "4428": {
        "vendor": "Quirky, Inc."
    },
    "4429": {
        "vendor": "Efergy Technologies Limited"
    },
    "4430": {
        "vendor": "SmartLabs, Inc."
    },
    "4431": {
        "vendor": "Everspring Industry Co., Ltd."
    },
    "4432": {
        "vendor": "Swann Communications Ptl Ltd."
    },
    "4433": {
        "vendor": "Soneter"
    },
    "4434": {
        "vendor": "Samsung SDS"
    },
    "4435": {
        "vendor": "Uniband Electronic Corporation"
    },
    "4436": {
        "vendor": "Accton Technology Corporation"
    },
    "4437": {
        "vendor": "Bosch Thermotechnik GmbH"
    },
    "4438": {
        "vendor": "Wincor Nixdorf Inc."
    },
    "4439": {
        "vendor": "Ohsung Electronics"
    },
    "4440": {
        "vendor": "Zen Within, Inc."
    },
    "4441": {
        "vendor": "Tech4home, Lda."
    },
    "4442": {
        "legal": "Nanoleaf Ltd.",
        "url": "https://nanoleaf.me",
        "vendor": "Nanoleaf"
    },
    "4443": {
        "vendor": "Keen Home, Inc."
    },
    "4444": {
        "vendor": "Poly-Control APS"
    },
    "4445": {
        "vendor": "Eastfield Lighting Co., Ltd Shenzhen"
    },
    "4446": {
        "vendor": "IP Datatel, Inc."
    },
    "4447": {
        "legal": "Lumi United Technology Co., Ltd.",
        "url": "https://www.aqara.com/",
        "vendor": "Aqara"
    },
    "4448": {
        "legal": "Sengled Co., Ltd.",
        "vendor": "Sengled"
    },
    "4449": {
        "vendor": "Remote Solution Co., Ltd."
    },
    "4450": {
        "vendor": "ABB Genway Xiamen Electrical Equipment Co., Ltd."
    },
    "4451": {
        "vendor": "Zhejiang Rexense Tech"
    },
    "4452": {
        "vendor": "ForEE Technology"
    },
    "4453": {
        "vendor": "Open Access Technology International."
    },
    "4454": {
        "legal": "Innr Lighting B.V.",
        "url": "https://www.innr.com",
        "vendor": "Innr"
    },
    "4455": {
        "vendor": "Techworld Industries"
    },
    "4456": {
        "legal": "Leedarson IoT Technology Inc.",
        "vendor": "Leedarson"
    },
    "4457": {
        "vendor": "Arzel Zoning"
    },
    "4458": {
        "vendor": "Holley Technology"
    },
    "4459": {
        "vendor": "Beldon Technologies"
    },
    "4460": {
        "vendor": "Flextronics"
    },
    "4461": {
        "vendor": "Shenzhen Meian"
    },
    "4462": {
        "vendor": "Lowes"
    },
    "4463": {
        "vendor": "Sigma Connectivity"
    },
    "4465": {
        "vendor": "Wulian"
    },
    "4466": {
        "vendor": "Plugwise B.V."
    },
    "4467": {
        "vendor": "Titan Products"
    },
    "4468": {
        "vendor": "Ecospectral"
    },
    "4469": {
        "legal": "D-Link Corporation",
        "vendor": "D-Link"
    },
    "4470": {
        "vendor": "Technicolor Home USA"
    },
    "4471": {
        "vendor": "Opple Lighting"
    },
    "4472": {
        "legal": "WNC Corporation"
    },
    "4473": {
        "vendor": "QMotion Shades"
    },
    "4474": {
        "legal": "Insta GmbH",
        "url": "https://www.insta.de"
    },
    "4475": {
        "vendor": "Shanghai Vancount"
    },
    "4476": {
        "legal": "IKEA of Sweden AB",
        "url": "https://www.ikea.com/",
        "vendor": "IKEA of Sweden"
    },
    "4477": {
        "vendor": "RT-RK"
    },
    "4478": {
        "legal": "Shenzhen Feibit Electronic Technology Co.,Ltd",
        "url": "http://www.feibit.com",
        "vendor": "Feibit"
    },
    "4479": {
        "vendor": "EuControls"
    },
    "4480": {
        "vendor": "Telkonet"
    },
    "4481": {
        "vendor": "Thermal Solution Resources"
    },
    "4482": {
        "vendor": "PomCube"
    },
    "4483": {
        "vendor": "Ei Electronics"
    },
    "4484": {
        "vendor": "Optoga"
    },
    "4485": {
        "vendor": "Stelpro"
    },
    "4486": {
        "vendor": "Lynxus Technologies Corp."
    },
    "4487": {
        "vendor": "Semiconductor Components"
    },
    "4488": {
        "legal": "TP-Link Systems Inc.",
        "url": "https://www.tp-link.com",
        "vendor": "TP-Link"
    },
    "4489": {
        "legal": "Ledvance GmbH",
        "vendor": "LEDVANCE"
    },
    "4490": {
        "vendor": "Nortek"
    },
    "4491": {
        "vendor": "iRevo/Assa Abbloy Korea"
    },
    "4492": {
        "legal": "Midea Group"
    },
    "4493": {
        "vendor": "ZF Friedrichshafen"
    },
    "4494": {
        "vendor": "Checkit"
    },
    "4495": {
        "vendor": "Aclara"
    },
    "4496": {
        "vendor": "Nokia"
    },
    "4497": {
        "vendor": "Goldcard High-tech Co., Ltd."
    },
    "4498": {
        "vendor": "George Wilson Industries Ltd."
    },
    "4499": {
        "vendor": "EASY SAVER CO.,INC"
    },
    "4500": {
        "vendor": "ZTE Corporation"
    },
    "4501": {
        "legal": "CommScope",
        "url": "https://www.pki-center.com/"
    },
    "4502": {
        "vendor": "Reliance BIG TV"
    },
    "4503": {
        "vendor": "Insight Energy Ventures/Powerley"
    },
    "4504": {
        "vendor": "Thomas Research Products (Hubbell Lighting Inc.)"
    },
    "4505": {
        "vendor": "Li Seng Technology"
    },
    "4506": {
        "vendor": "System Level Solutions Inc."
    },
    "4507": {
        "vendor": "Matrix Labs"
    },
    "4508": {
        "vendor": "Sinope Technologies"
    },
    "4509": {
        "vendor": "Jiuzhou Greeble"
    },
    "4510": {
        "vendor": "Guangzhou Lanvee Tech. Co. Ltd."
    },
    "4511": {
        "vendor": "Venstar"
    },
    "4608": {
        "vendor": "SLV"
    },
    "4609": {
        "vendor": "Halo Smart Labs"
    },
    "4610": {
        "vendor": "Scout Security Inc."
    },
    "4611": {
        "vendor": "Alibaba China Inc."
    },
    "4612": {
        "vendor": "Resolution Products, Inc."
    },
    "4613": {
        "vendor": "Smartlok Inc."
    },
    "4614": {
        "legal": "EME Delaware Inc.",
        "vendor": "EME Americas"
    },
    "4615": {
        "vendor": "Vimar SpA"
    },
    "4616": {
        "vendor": "Universal Lighting Technologies"
    },
    "4617": {
        "legal": "Robert Bosch GmbH",
        "url": "https://www.bosch.com",
        "vendor": "Bosch"
    },
    "4618": {
        "vendor": "Accenture"
    },
    "4619": {
        "legal": "Shenzhen Heiman Technology Co., Ltd.",
        "vendor": "HEIMAN"
    },
    "4620": {
        "vendor": "Shenzhen HOMA Technology Co., Ltd."
    },
    "4621": {
        "vendor": "Vision-Electronics Technology"
    },
    "4622": {
        "vendor": "Lenovo"
    },
    "4623": {
        "vendor": "Presciense R and D"
    },
    "4624": {
        "vendor": "Shenzhen Seastar Intelligence Co., Ltd."
    },
    "4625": {
        "vendor": "Sensative AB"
    },
    "4626": {
        "vendor": "SolarEdge"
    },
    "4627": {
        "vendor": "Zipato"
    },
    "4628": {
        "vendor": "China Fire  and  Security Sensing Manufacturing (iHorn)"
    },
    "4629": {
        "vendor": "Quby BV"
    },
    "4630": {
        "vendor": "Hangzhou Roombanker Technology Co., Ltd."
    },
    "4631": {
        "legal": "Amazon.com, Inc.",
        "url": "https://www.amazon.com",
        "vendor": "Amazon Alexa"
    },
    "4632": {
        "vendor": "Paulmann Licht GmbH"
    },
    "4633": {
        "legal": "Shenzhen ORVIBO Technology Co.,  Ltd.",
        "url": "https://www.orvibo.com",
        "vendor": "ORVIBO"
    },
    "4634": {
        "vendor": "TCI Telecommunications"
    },
    "4635": {
        "vendor": "Mueller-Licht International Inc."
    },
    "4636": {
        "vendor": "Aurora Limited"
    },
    "4637": {
        "vendor": "SmartDCC"
    },
    "4638": {
        "vendor": "Shanghai UMEinfo Co. Ltd."
    },
    "4639": {
        "vendor": "carbonTRACK"
    },
    "4640": {
        "vendor": "Somfy"
    },
    "4641": {
        "vendor": "Viessmann Elektronik GmbH"
    },
    "4642": {
        "vendor": "Hildebrand Technology Ltd"
    },
    "4643": {
        "vendor": "Onkyo Technology Corporation"
    },
    "4644": {
        "legal": "Shenzhen Sunricher Technology Ltd.",
        "vendor": "Sunricher"
    },
    "4645": {
        "vendor": "Xiu Xiu Technology Co., Ltd"
    },
    "4646": {
        "vendor": "Zumtobel Group"
    },
    "4647": {
        "vendor": "Shenzhen Kaadas Intelligent Technology Co. Ltd"
    },
    "4648": {
        "vendor": "Shanghai Xiaoyan Technology Co. Ltd"
    },
    "4649": {
        "vendor": "Cypress Semiconductor"
    },
    "4650": {
        "vendor": "XAL GmbH"
    },
    "4651": {
        "vendor": "Inergy Systems LLC"
    },
    "4652": {
        "vendor": "Alfred Karcher GmbH  and  Co KG"
    },
    "4653": {
        "legal": "Aduro Technologies LLC",
        "vendor": "AduroSmart"
    },
    "4654": {
        "vendor": "Groupe Muller"
    },
    "4655": {
        "vendor": "V-Mark Enterprises Inc."
    },
    "4656": {
        "vendor": "Lead Energy AG"
    },
    "4657": {
        "vendor": "Ultimate IOT (Henan) Technology Ltd."
    },
    "4658": {
        "vendor": "Axxess Industries Inc."
    },
    "4659": {
        "vendor": "Third Reality Inc."
    },
    "4660": {
        "vendor": "DSR Corporation"
    },
    "4661": {
        "vendor": "Guangzhou Vensi Intelligent Technology Co. Ltd."
    },
    "4662": {
        "legal": "Schlage Lock Company LLC",
        "vendor": "Allegion"
    },
    "4663": {
        "vendor": "Net2Grid"
    },
    "4664": {
        "vendor": "Airam Electric Oy Ab"
    },
    "4665": {
        "legal": "Immax WPB CZ, s.r.o.",
        "vendor": "Immax"
    },
    "4666": {
        "vendor": "ZIV Automation"
    },
    "4667": {
        "vendor": "HangZhou iMagicTechnology Co., Ltd"
    },
    "4668": {
        "vendor": "Xiamen Leelen Technology Co. Ltd."
    },
    "4669": {
        "vendor": "Overkiz SAS"
    },
    "4670": {
        "vendor": "Flonidan A/S"
    },
    "4671": {
        "vendor": "HDL Automation Co., Ltd."
    },
    "4672": {
        "vendor": "Ardomus Networks Corporation"
    },
    "4673": {
        "legal": "Samjin Co.,Ltd",
        "vendor": "Samjin"
    },
    "4674": {
        "vendor": "FireAngel Safety Technology plc"
    },
    "4675": {
        "vendor": "Indra Sistemas, S.A."
    },
    "4676": {
        "vendor": "Shenzhen JBT Smart Lighting Co., Ltd."
    },
    "4677": {
        "vendor": "GE Lighting  and  Current"
    },
    "4678": {
        "vendor": "Danfoss A/S"
    },
    "4679": {
        "vendor": "NIVISS PHP Sp. z o.o. Sp.k."
    },
    "4680": {
        "vendor": "Shenzhen Fengliyuan Energy Conservating Technology Co. Ltd"
    },
    "4681": {
        "vendor": "NEXELEC"
    },
    "4682": {
        "vendor": "Sichuan Behome Prominent Technology Co., Ltd"
    },
    "4683": {
        "vendor": "Fujian Star-net Communication Co., Ltd."
    },
    "4684": {
        "vendor": "Toshiba Visual Solutions Corporation"
    },
    "4685": {
        "vendor": "Latchable, Inc."
    },
    "4686": {
        "vendor": "L and S Deutschland GmbH"
    },
    "4687": {
        "vendor": "Gledopto Co., Ltd."
    },
    "4688": {
        "vendor": "The Home Depot"
    },
    "4689": {
        "legal": "Neonlite",
        "vendor": "Neonlite Distribution Ltd."
    },
    "4690": {
        "vendor": "Arlo Technologies, Inc."
    },
    "4691": {
        "vendor": "Xingluo Technology Co., Ltd."
    },
    "4692": {
        "vendor": "Simon Electric (China) Co., Ltd."
    },
    "4693": {
        "vendor": "Hangzhou Greatstar Industrial Co., Ltd."
    },
    "4694": {
        "vendor": "Sequentric Energy Systems, LLC"
    },
    "4695": {
        "vendor": "Solum Co., Ltd."
    },
    "4696": {
        "vendor": "Eaglerise Electric  and  Electronic (China) Co., Ltd."
    },
    "4697": {
        "vendor": "Fantem Technologies (Shenzhen) Co., Ltd."
    },
    "4698": {
        "vendor": "Yunding Network Technology (Beijing) Co., Ltd."
    },
    "4699": {
        "vendor": "Atlantic Group"
    },
    "4700": {
        "vendor": "Xiamen Intretech, Inc."
    },
    "4701": {
        "legal": "Tuya Global Inc.",
        "vendor": "Tuya"
    },
    "4702": {
        "vendor": "Dnake (Xiamen) Intelligent Technology Co., Ltd."
    },
    "4703": {
        "vendor": "Niko nv"
    },
    "4704": {
        "vendor": "Emporia Energy"
    },
    "4705": {
        "vendor": "Sikom AS"
    },
    "4706": {
        "vendor": "AXIS Labs, Inc."
    },
    "4707": {
        "vendor": "Current Products Corporation"
    },
    "4708": {
        "vendor": "MeteRSit SRL"
    },
    "4709": {
        "vendor": "HORNBACH Baumarkt AG"
    },
    "4710": {
        "vendor": "DiCEworld s.r.l. a socio unico"
    },
    "4711": {
        "legal": "ARC Technology Co., Ltd. "
    },
    "4712": {
        "vendor": "Hangzhou Konke Information Technology Co., Ltd."
    },
    "4713": {
        "vendor": "SALTO Systems S.L."
    },
    "4714": {
        "vendor": "Shenzhen Shyugj Technology Co., Ltd"
    },
    "4715": {
        "vendor": "Brayden Automation Corporation"
    },
    "4716": {
        "vendor": "Environexus Pty. Ltd."
    },
    "4717": {
        "vendor": "Eltra nv/sa"
    },
    "4718": {
        "legal": "Xiaomi Communications Co., Ltd.",
        "url": "https://iot.mi.com",
        "vendor": "Xiaomi"
    },
    "4719": {
        "vendor": "Shanghai Shuncom Electronic Technology Co., Ltd."
    },
    "4720": {
        "vendor": "Voltalis S.A"
    },
    "4721": {
        "vendor": "FEELUX Co., Ltd."
    },
    "4722": {
        "vendor": "SmartPlus Inc."
    },
    "4723": {
        "vendor": "Halemeier GmbH"
    },
    "4724": {
        "legal": "Trust International BV"
    },
    "4725": {
        "vendor": "Duke Energy Business Services LLC"
    },
    "4726": {
        "vendor": "Calix, Inc."
    },
    "4727": {
        "vendor": "ADEO"
    },
    "4728": {
        "vendor": "Connected Response Limited"
    },
    "4729": {
        "vendor": "StroyEnergoKom, Ltd."
    },
    "4730": {
        "vendor": "Lumitech Lighting Solution GmbH"
    },
    "4731": {
        "vendor": "Verdant Environmental Technologies"
    },
    "4732": {
        "vendor": "Alfred International Inc."
    },
    "4733": {
        "vendor": "Sansi LED Lighting co., LTD."
    },
    "4734": {
        "vendor": "Mindtree Limited"
    },
    "4735": {
        "legal": "Nordic Semiconductor ASA",
        "url": "https://www.nordicsemi.com"
    },
    "4736": {
        "legal": "Siterwell Electronics Co., Limited",
        "vendor": "Siterwell"
    },
    "4737": {
        "vendor": "Briloner Leuchten GmbH  and  Co. KG"
    },
    "4738": {
        "legal": "Shenzhen SEI Technology Co., Ltd.",
        "url": "https://seirobotics.net/",
        "vendor": "SEI"
    },
    "4739": {
        "vendor": "Copper Labs, Inc."
    },
    "4740": {
        "vendor": "Delta Dore"
    },
    "4741": {
        "legal": "Hager Controls SAS",
        "vendor": "Hager Group"
    },
    "4742": {
        "legal": "SHENZHEN Coolkit Technology CO.,LTD.",
        "url": "https://www.coolkit.cn/",
        "vendor": "CoolKit"
    },
    "4743": {
        "vendor": "Hangzhou Sky-Lighting Co., Ltd."
    },
    "4744": {
        "vendor": "E.ON SE"
    },
    "4745": {
        "legal": "Lidl Stiftung & Co. KG"
    },
    "4746": {
        "legal": "Sichuan Changhong Neonet Technologies Co.,Ltd. ",
        "url": "https://www.neo-net.com/",
        "vendor": "Changhong Network"
    },
    "4747": {
        "vendor": "NodOn"
    },
    "4748": {
        "vendor": "Jiangxi Innotech Technology Co., Ltd."
    },
    "4749": {
        "vendor": "Mercator Pty Ltd"
    },
    "4750": {
        "vendor": "Beijing Ruying Tech Limited"
    },
    "4751": {
        "legal": "EGLO Leuchten GmbH",
        "url": "https://www.eglo.com/en/",
        "vendor": "EGLO"
    },
    "4752": {
        "vendor": "Pietro Fiorentini S.p.A"
    },
    "4753": {
        "vendor": "Zehnder Group Vaux-Andigny"
    },
    "4754": {
        "vendor": "BRK Brands, Inc."
    },
    "4755": {
        "vendor": "Askey Computer Corp."
    },
    "4756": {
        "vendor": "PassiveBolt, Inc."
    },
    "4757": {
        "legal": "FRITZ! GmbH",
        "url": "https://fritz.com",
        "vendor": "FRITZ!"
    },
    "4758": {
        "vendor": "Ningbo Suntech Lighting Technology Co., Ltd"
    },
    "4759": {
        "vendor": "Société en Commandite Stello"
    },
    "4760": {
        "vendor": "Vivint Smart Home"
    },
    "4761": {
        "vendor": "Namron AS"
    },
    "4762": {
        "legal": "DeltaDore Rademacher GmbH",
        "url": "https://www.rademacher.de/",
        "vendor": "Delta Dore Rademacher"
    },
    "4763": {
        "vendor": "OMO Systems LTD"
    },
    "4764": {
        "vendor": "Siglis AG"
    },
    "4765": {
        "vendor": "IMHOTEP CREATION"
    },
    "4766": {
        "vendor": "icasa"
    },
    "4767": {
        "legal": "Assa Abloy Level LLC",
        "url": "https://level.co",
        "vendor": "Level Home"
    },
    "4864": {
        "vendor": "TIS Control Limited"
    },
    "4865": {
        "vendor": "Radisys India Pvt. Ltd."
    },
    "4866": {
        "vendor": "Veea Inc."
    },
    "4867": {
        "vendor": "FELL Technology AS"
    },
    "4868": {
        "vendor": "Sowilo Design Services, Ltd."
    },
    "4869": {
        "vendor": "Lexi Devices, Inc."
    },
    "4870": {
        "vendor": "Lifi Labs INC. dba LIFX"
    },
    "4871": {
        "vendor": "GRUNDFOS Holding A/S"
    },
    "4872": {
        "vendor": "SOURCING  and  CREATION"
    },
    "4873": {
        "vendor": "Kraken Technologies Ltd"
    },
    "4874": {
        "legal": "Eve Systems GmbH",
        "url": "https://www.evehome.com",
        "vendor": "Eve"
    },
    "4875": {
        "vendor": "LITE-ON TECHNOLOGY CORPORATION"
    },
    "4876": {
        "legal": "EVVR ApS",
        "url": "https://evvr.io",
        "vendor": "EVVR"
    },
    "4877": {
        "legal": "Bouffalo Lab (Nanjing) Co., Ltd.",
        "url": "https://www.bouffalolab.com/",
        "vendor": "BouffaloLab"
    },
    "4878": {
        "vendor": "Wyze Labs, Inc."
    },
    "4879": {
        "vendor": "Z-Wave Europe GmbH"
    },
    "4880": {
        "vendor": "AEOTEC LIMITED"
    },
    "4881": {
        "vendor": "NGSTB Company Limited"
    },
    "4882": {
        "legal": "Qingdao Yeelink Information Technology Co., Ltd.",
        "url": "https://en.yeelight.com/#",
        "vendor": "Yeelight"
    },
    "4883": {
        "vendor": "E-Smart Home Automation Systems Limited"
    },
    "4884": {
        "vendor": "Fibar Group S.A."
    },
    "4885": {
        "vendor": "Prolitech GmbH"
    },
    "4886": {
        "legal": "Realtek Semiconductor Corp.",
        "url": "https://www.realtek.com/",
        "vendor": "Realtek"
    },
    "4887": {
        "vendor": "Logitech"
    },
    "4888": {
        "vendor": "Piaro, Inc."
    },
    "4889": {
        "legal": "Mitsubishi Electric US, Inc.",
        "vendor": "Mitsubishi Electric US"
    },
    "4890": {
        "legal": "Resideo Technologies, Inc.",
        "url": "https://www.resideo.com/",
        "vendor": "Resideo"
    },
    "4891": {
        "legal": "Espressif Systems (Shanghai) Co. Ltd.",
        "url": "https://www.espressif.com",
        "vendor": "Espressif Systems"
    },
    "4892": {
        "legal": "HELLA Sonnen- und Wetterschutztechnik GmbH",
        "url": "https://www.hella.info",
        "vendor": "HELLA"
    },
    "4893": {
        "vendor": "Geberit International AG"
    },
    "4894": {
        "legal": "CAME S.p.A.",
        "url": "https://www.came.com/"
    },
    "4895": {
        "legal": "Longan Link Tech Co.,LTD",
        "url": "https://longan.link/",
        "vendor": "Longan.link"
    },
    "4896": {
        "vendor": "Phyplus Microelectronics Limited"
    },
    "4897": {
        "legal": "Shenzhen Sonoff Technologies Co.,Ltd.",
        "url": "https://sonoff.tech/",
        "vendor": "SONOFF"
    },
    "4898": {
        "vendor": "Safe4 Security Group"
    },
    "4899": {
        "vendor": "Shanghai MXCHIP Information Technology Co., Ltd."
    },
    "4900": {
        "vendor": "HDC I-Controls"
    },
    "4901": {
        "vendor": "Zuma Array Limited"
    },
    "4902": {
        "vendor": "DECELECT"
    },
    "4903": {
        "legal": "Mill International AS"
    },
    "4904": {
        "vendor": "HomeWizard BV"
    },
    "4905": {
        "vendor": "Shenzhen Topband Co., Ltd"
    },
    "4906": {
        "vendor": "Pressac Communications Ltd"
    },
    "4907": {
        "vendor": "Origin Wireless, Inc."
    },
    "4908": {
        "vendor": "Connecte AS"
    },
    "4909": {
        "vendor": "YOKIS"
    },
    "4910": {
        "legal": "Xiamen Yankon Energetic Lighting Co., Ltd.",
        "vendor": "Energetic"
    },
    "4911": {
        "legal": "Yandex LLC",
        "vendor": "Yandex"
    },
    "4912": {
        "vendor": "Critical Software S.A."
    },
    "4913": {
        "vendor": "Nortek Control"
    },
    "4914": {
        "vendor": "BrightAI"
    },
    "4915": {
        "legal": "Becker Antriebe GmbH",
        "url": "https://www.becker-antriebe.com/",
        "vendor": "Becker Antriebe"
    },
    "4916": {
        "legal": "Shenzhen TCL New Technology Co.,LTD.",
        "vendor": "tcl-vendor"
    },
    "4917": {
        "legal": "Dexatek Technology Ltd",
        "vendor": "Dexatek Technology"
    },
    "4918": {
        "vendor": "Elelabs International Limited"
    },
    "4919": {
        "vendor": "Datek Wireless AS"
    },
    "4920": {
        "vendor": "ALDES"
    },
    "4921": {
        "legal": "GE Lighting, a Savant company",
        "url": "https://www.gelighting.com/"
    },
    "4922": {
        "vendor": "Ariston Thermo Group"
    },
    "4923": {
        "legal": "WAREMA Renkhoff SE",
        "url": "https://www.warema.com"
    },
    "4924": {
        "vendor": "VTech Holdings Limited"
    },
    "4925": {
        "vendor": "Futurehome AS"
    },
    "4926": {
        "vendor": "Cognitive Systems Corp."
    },
    "4927": {
        "legal": "ASR Microelectronics(ShenZhen)Co., Ltd.",
        "vendor": "ASR"
    },
    "4928": {
        "vendor": "Airios"
    },
    "4929": {
        "vendor": "Guangdong OPPO Mobile Telecommunications Corp., Ltd."
    },
    "4930": {
        "legal": "beken",
        "url": "http://www.bekencorp.com/",
        "vendor": "Beken Corporation"
    },
    "4931": {
        "vendor": "Corsair"
    },
    "4932": {
        "legal": "Eltako GmbH",
        "url": "https://www.eltako.com",
        "vendor": "Eltako"
    },
    "4933": {
        "legal": "Chengdu Meross Technology Co., Ltd.",
        "url": "https://www.meross.com",
        "vendor": "Meross"
    },
    "4934": {
        "legal": "Rafael Microelectronics, Inc.",
        "vendor": "Rafael"
    },
    "4935": {
        "vendor": "Aug. Winkhuas GmbH  and  Co. KG"
    },
    "4936": {
        "vendor": "Qingdao Haier Technology Co., Ltd."
    },
    "4937": {
        "legal": "Apple Inc.",
        "url": "https://www.apple.com/home-app",
        "vendor": "Apple Home"
    },
    "4938": {
        "legal": "Rollease Acmeda Inc.",
        "url": "https://www.rolleaseacmeda.com/",
        "vendor": "Rollease Acmeda"
    },
    "4939": {
        "legal": "Open Home Foundation",
        "url": "https://www.openhomefoundation.org/",
        "vendor": "Home Assistant (Open Home Foundation)"
    },
    "4940": {
        "legal": "Simon Holding"
    },
    "4941": {
        "vendor": "KD Navien"
    },
    "4942": {
        "legal": "tado GmbH",
        "url": "https://www.tado.com/",
        "vendor": "tado"
    },
    "4943": {
        "legal": "mediola - connected living AG",
        "url": "https://www.mediola.com",
        "vendor": "mediola"
    },
    "4944": {
        "vendor": "Polynhome"
    },
    "4945": {
        "legal": "HooRii Technology CO., LTD",
        "url": "https://www.hoorii.io/",
        "vendor": "HooRii Technology"
    },
    "4946": {
        "legal": "Häfele SE & Co. KG",
        "url": "https://www.hafele.com",
        "vendor": "Hafele"
    },
    "4947": {
        "vendor": "KIMIN Electronics Co., Ltd."
    },
    "4948": {
        "vendor": "Zyax AB"
    },
    "4949": {
        "vendor": "Baracoda SA"
    },
    "4950": {
        "legal": "Lennox International, Inc",
        "url": "https://www.lennox.com",
        "vendor": "Lennox"
    },
    "4951": {
        "vendor": "Teledatics Incorporated"
    },
    "4952": {
        "legal": "Top Victory Investments Limited",
        "url": "https://www.tpv-tech.com/"
    },
    "4953": {
        "legal": "GOQUAL Inc."
    },
    "4954": {
        "legal": "SIEGENIA-AUBI KG",
        "url": "https://www.siegenia.com",
        "vendor": "Siegenia Aubi KG"
    },
    "4955": {
        "vendor": "Virtual Connected Controlling System (Singapore) Pte. Ltd."
    },
    "4956": {
        "vendor": "Gigaset Communications GmbH"
    },
    "4957": {
        "legal": "Nuki Home Solutions GmbH",
        "url": "https://nuki.io",
        "vendor": "Nuki"
    },
    "4958": {
        "vendor": "Devicebook, Inc."
    },
    "4959": {
        "vendor": "Consumer 2.0 Inc. (Rently)"
    },
    "4960": {
        "vendor": "Edison Labs, Inc. (dba Orro)"
    },
    "4961": {
        "legal": "Inovelli Labs Corporation",
        "url": "https://www.inovelli.com",
        "vendor": "Inovelli"
    },
    "4962": {
        "legal": "deveritec GmbH",
        "url": "https://deveritec.de"
    },
    "4963": {
        "vendor": "Charter Communications"
    },
    "4964": {
        "vendor": "Monolithic Power Systems, Inc."
    },
    "4965": {
        "legal": "Ningbo Dooya Mechanic & Electronic Technology Co.,Ltd",
        "vendor": "Connector"
    },
    "4966": {
        "vendor": "Shenzhen SDMC Technology Co., Ltd."
    },
    "4967": {
        "vendor": "HP Inc."
    },
    "4968": {
        "vendor": "mui Lab, Inc."
    },
    "4969": {
        "vendor": "BHtronics S.r.l."
    },
    "4970": {
        "vendor": "Akuvox (Xiamen) Networks Co., Ltd."
    },
    "4971": {
        "vendor": "nami"
    },
    "4972": {
        "vendor": "Kee Tat Manufactory Holdings Limited"
    },
    "4973": {
        "vendor": "Iton Technology Corp."
    },
    "4974": {
        "vendor": "Ambi Labs Limited"
    },
    "4975": {
        "vendor": "Corporación Empresarial Altra S.L."
    },
    "4976": {
        "vendor": "Coway Co., Ltd."
    },
    "4977": {
        "vendor": "Tridonic GmbH  and  Co KG"
    },
    "4978": {
        "vendor": "innovation matters iot GmbH"
    },
    "4979": {
        "vendor": "MediaTek Inc."
    },
    "4980": {
        "vendor": "Fresco"
    },
    "4981": {
        "vendor": "Hangzhou Yaguan Technology Co., Ltd."
    },
    "4982": {
        "vendor": "Guardian Glass, LLC"
    },
    "4983": {
        "vendor": "Night Owl SP, LLC"
    },
    "4984": {
        "vendor": "Je Woo Corporation Ltd."
    },
    "4985": {
        "vendor": "Earda Technologies Co., Ltd."
    },
    "4986": {
        "vendor": "Alexa Connect Kit (ACK)"
    },
    "4987": {
        "vendor": "Amazon Basics"
    },
    "4988": {
        "vendor": "Morse Micro Inc."
    },
    "4989": {
        "vendor": "Shanghai Xiaodu Technology Limited"
    },
    "4990": {
        "vendor": "Nubert electronic GmbH"
    },
    "4991": {
        "vendor": "Shenzhen NEO Electronics Co. Ltd."
    },
    "4992": {
        "vendor": "Grimsholm Products AB"
    },
    "4993": {
        "vendor": "Amazon Prime Video"
    },
    "4994": {
        "vendor": "ION INDUSTRIES B.V."
    },
    "4995": {
        "vendor": "Ayla Networks"
    },
    "4996": {
        "vendor": "Apple Keychain"
    },
    "4997": {
        "vendor": "Lightning Semiconductor"
    },
    "4998": {
        "vendor": "Skylux NV"
    },
    "4999": {
        "vendor": "Shenzhen Qianyan Technology Ltd."
    },
    "5000": {
        "vendor": "Infineon Technologies AG"
    },
    "5001": {
        "vendor": "Shenzhen Jingxun Technology Co., Ltd."
    },
    "5002": {
        "vendor": "Nature Inc."
    },
    "5003": {
        "vendor": "WiFigarden Inc."
    },
    "5004": {
        "vendor": "Hisense Group Co. Ltd., USA"
    },
    "5005": {
        "vendor": "Nanjing Easthouse Electrical Co., Ltd."
    },
    "5006": {
        "vendor": "Ledworks SRL"
    },
    "5007": {
        "vendor": "Shina System Co., Ltd."
    },
    "5008": {
        "vendor": "Qualcomm Technologies Inc."
    },
    "5009": {
        "vendor": "Kasa (Big Field Global PTE. Ltd.)"
    },
    "5010": {
        "vendor": "Tapo (Big Field Global PTE. Ltd.)"
    },
    "5011": {
        "vendor": "Shanghai High-Flying Electronics Technology Co., Ltd."
    },
    "5012": {
        "vendor": "SigmaStar Technology Ltd."
    },
    "5013": {
        "vendor": "HOOBS Inc."
    },
    "5014": {
        "vendor": "AiDot Inc."
    },
    "5015": {
        "vendor": "Woan Technology (Shenzhen) Co., Ltd."
    },
    "5016": {
        "vendor": "Meizu Technology Co., Ltd."
    },
    "5017": {
        "vendor": "Yukai Engineering Inc."
    },
    "5018": {
        "vendor": "Qrio, Inc."
    },
    "5019": {
        "vendor": "ITIUS GmbH"
    },
    "5020": {
        "vendor": "Zemismart Technology Limited"
    },
    "5021": {
        "vendor": "LED Linear GmbH"
    },
    "5022": {
        "vendor": "Dyson Technology Limited"
    },
    "5023": {
        "vendor": "Razer Inc."
    },
    "5120": {
        "vendor": "Uascent Technology Company Limited"
    },
    "5121": {
        "vendor": "Bose Corporation"
    },
    "5122": {
        "vendor": "GOLDTek Technology Co., Ltd."
    },
    "5123": {
        "vendor": "Arlec Australia Pty. Ltd."
    },
    "5124": {
        "vendor": "Shenzhen Phaten Technology Co., Ltd."
    },
    "5125": {
        "vendor": "Ecovacs Robotics Co., Ltd."
    },
    "5126": {
        "vendor": "Luxshare-ICT Co., Ltd."
    },
    "5127": {
        "vendor": "Jiangshu Shushi Technology Co., Ltd."
    },
    "5128": {
        "vendor": "Velux A/S"
    },
    "5129": {
        "vendor": "Shenzhen Hidin Technology Co., Ltd."
    },
    "5130": {
        "vendor": "Intertech Services AG"
    },
    "5131": {
        "vendor": "70mai Co., Ltd."
    },
    "5132": {
        "vendor": "Beijing ESWIN Computing Technology CO.,Ltd."
    },
    "5133": {
        "vendor": "Photon Sail Technologies Pte. Ltd."
    },
    "5134": {
        "vendor": "WiDom SRL"
    },
    "5135": {
        "vendor": "Sagemcom SAS"
    },
    "5136": {
        "vendor": "Quectel Wireless Solutions Co., Ltd."
    },
    "5137": {
        "vendor": "Freedompro S.r.l."
    },
    "5138": {
        "vendor": "Disign Incorporated"
    },
    "5139": {
        "vendor": "1Home Solutions GmbH"
    },
    "5140": {
        "vendor": "StreamUnlimited Engineering GmbH"
    },
    "5141": {
        "vendor": "Caveman (Nanoleaf)"
    },
    "5142": {
        "vendor": "Umbra (Nanoleaf)"
    },
    "5143": {
        "vendor": "Konnected Inc."
    },
    "5144": {
        "vendor": "KLite (Signify)"
    },
    "5145": {
        "vendor": "Lorex Technology Inc."
    },
    "5146": {
        "vendor": "RATOC Systems, Inc"
    },
    "5147": {
        "vendor": "Rang Dong Light Source  and  VacuumFlask Joint Stock Company"
    },
    "5148": {
        "vendor": "Shenzhen Sibo Zhilian Technology Co., Ltd."
    },
    "5149": {
        "vendor": "Secuyou APS"
    },
    "5150": {
        "vendor": "TUO Accessories LLC"
    },
    "5151": {
        "vendor": "DUCTECH Co., Ltd"
    },
    "5152": {
        "vendor": "EcoFlow Inc."
    },
    "5153": {
        "vendor": "Kwikset"
    },
    "5154": {
        "vendor": "Zhuhai HiVi Technology Co., Ltd."
    },
    "5155": {
        "vendor": "Feit Electric Company, Inc."
    },
    "5156": {
        "vendor": "Alarm.com Incorporated"
    },
    "5157": {
        "vendor": "Hangzhou BroadLink Technology Co., Ltd."
    },
    "5158": {
        "vendor": "ELE (Group) Co., Ltd."
    },
    "5159": {
        "vendor": "Hama GmbH  and  Co. KG"
    },
    "5160": {
        "vendor": "Shenzhen Aimore .Co .,Ltd"
    },
    "5161": {
        "vendor": "Albrecht Jung GmbH  and  Co. KG"
    },
    "5162": {
        "vendor": "Hitachi Global Life Solutions, Inc."
    },
    "5163": {
        "vendor": "Beijing Renhejia Technology Co., Ltd"
    },
    "5164": {
        "vendor": "vivo Mobile Communication Co., Ltd."
    },
    "5165": {
        "vendor": "Zhongshan QIHANG Electronic Technology Co."
    },
    "5166": {
        "vendor": "Shenzhen Sowye Technology CO.,Ltd"
    },
    "5167": {
        "vendor": "Shenzhen QIACHIP Wireless Ecommerce Co."
    },
    "5168": {
        "vendor": "L-TRADE GROUP SP z.o.o."
    },
    "5169": {
        "vendor": "Daikin Industries, Ltd."
    },
    "5170": {
        "vendor": "ELKO EP, s.r.o."
    },
    "5171": {
        "vendor": "MOMAX Technology (Hong Kong) Limited"
    },
    "5172": {
        "vendor": "Hangzhou Ezviz Network Co., Ltd."
    },
    "5173": {
        "vendor": "Granite River Labs"
    },
    "5174": {
        "vendor": "SinuxSoft Inc."
    },
    "5175": {
        "vendor": "ACCEL LAB Ltd."
    },
    "5176": {
        "vendor": "Xiamen Topstar Lighting Co.,Ltd"
    },
    "5177": {
        "vendor": "Vaillant Group"
    },
    "5178": {
        "vendor": "YoSmart Inc."
    },
    "5179": {
        "vendor": "Amina Charging AS"
    },
    "5180": {
        "vendor": "Athom B.V."
    },
    "5181": {
        "vendor": "Shenzhen Champon Technology Co., Ltd"
    },
    "5182": {
        "vendor": "Acer Inc."
    },
    "5183": {
        "vendor": "Vestel Elektronik Sanayi ve Ticaret A.S."
    },
    "5184": {
        "vendor": "VerLuce"
    },
    "5185": {
        "vendor": "Shenzhen Snowball Technology Co., Ltd."
    },
    "5186": {
        "vendor": "REHAU Group"
    },
    "5187": {
        "vendor": "GoodsiQ"
    },
    "5188": {
        "vendor": "Last lock Inc."
    },
    "5189": {
        "vendor": "Finesse Decor"
    },
    "5190": {
        "vendor": "Take As Global, SL"
    },
    "5191": {
        "vendor": "Honor Device Co., Ltd."
    },
    "5192": {
        "vendor": "LivingStyle Enterprises Limited"
    },
    "5193": {
        "vendor": "ZUTTO TECHNOLOGIES"
    },
    "5194": {
        "vendor": "Sensibo Ltd."
    },
    "5195": {
        "vendor": "Kohler Company"
    },
    "5196": {
        "vendor": "TrustAsia Technologies, Inc."
    },
    "5197": {
        "vendor": "Atios AG"
    },
    "5198": {
        "vendor": "Sense Labs, Inc."
    },
    "5199": {
        "vendor": "Assa Abloy AB"
    },
    "5200": {
        "vendor": "GM Global Technology Operations LLC"
    },
    "5201": {
        "vendor": "JetHome"
    },
    "5202": {
        "vendor": "Big Ass Fans"
    },
    "5203": {
        "vendor": "Gumax BV"
    },
    "5204": {
        "vendor": "Yardi Systems Inc."
    },
    "5205": {
        "vendor": "Deutsche Telekom AG"
    },
    "5206": {
        "vendor": "Sensirion AG"
    },
    "5207": {
        "vendor": "Hangzhou Wistar Mechanical  and  Electric Technology Co., Ltd"
    },
    "5208": {
        "vendor": "Wilhelm Koch GmbH "
    },
    "5209": {
        "vendor": "Shenzhen iComm Semiconductor Co., Ltd."
    },
    "5210": {
        "vendor": "British Telecommunications plc"
    },
    "5211": {
        "vendor": "Remotec Technology Ltd."
    },
    "5212": {
        "vendor": "Pin Genie, Inc. DBA Lockly"
    },
    "5213": {
        "vendor": "Hosiden Corporation"
    },
    "5214": {
        "vendor": "Deako, Inc."
    },
    "5215": {
        "vendor": "Good Way Technology Co., Ltd."
    },
    "5216": {
        "vendor": "Zhuhai Ruran Intelligent Technology Co., LTD (Meizu)"
    },
    "5217": {
        "vendor": "Xinda Asset Management (Shenzhen) Co.,Ltd."
    },
    "5218": {
        "vendor": "Chengdu Energy Magic Cube Technology Co., Ltd"
    },
    "5219": {
        "vendor": "Eberle Controls GmbH"
    },
    "5220": {
        "vendor": "Opulinks Technology"
    },
    "5221": {
        "vendor": "Hunter Douglas Group"
    },
    "5222": {
        "vendor": "Hangzhou Hemos Lighting Company Limited"
    },
    "5223": {
        "vendor": "OTODO SAS"
    },
    "5224": {
        "vendor": "Anona Security Technology Limited"
    },
    "5225": {
        "vendor": "Loxone Electronics GmbH"
    },
    "5226": {
        "vendor": "Intecular LLC"
    },
    "5227": {
        "vendor": "Aixlink Ltd."
    },
    "5228": {
        "vendor": "Shenzhen Jinjie Technology Co.,Ltd."
    },
    "5229": {
        "vendor": "Polyaire Pty Ltd"
    },
    "5230": {
        "vendor": "Shenzhen PINXUAN Trading Co."
    },
    "5231": {
        "vendor": "SmartWing Home LLC"
    },
    "5232": {
        "vendor": "Shenzhen Hope Microelectronics Co., Ltd."
    },
    "5233": {
        "vendor": "Commax"
    },
    "5234": {
        "vendor": "Zhejiang Jiecang Linear Motion Technology Co.,Ltd"
    },
    "5235": {
        "vendor": "Shenzhen Lelight technology Co.lt"
    },
    "5236": {
        "vendor": "Shenzhen Ruomu Zhilian Technology Co., Ltd."
    },
    "5237": {
        "vendor": "Cable Television Laboratories, Inc. dba CableLabs"
    },
    "5238": {
        "vendor": "Harman International"
    },
    "5239": {
        "vendor": "Shenzhen Multi IR Technology Co.,Ltd"
    },
    "5240": {
        "vendor": "APYNOV"
    },
    "5241": {
        "vendor": "Browan Communications Inc."
    },
    "5242": {
        "vendor": "Shenzhen Realwe Innovation Technology Co., Ltd."
    },
    "5243": {
        "vendor": "Lumiflow INC"
    },
    "5244": {
        "vendor": "SHENZHEN SHENAN YANGGUANG ELECTRONICS CO., LTD."
    },
    "5245": {
        "vendor": "Wenzhou Morning Electronics Co., Ltd."
    },
    "5246": {
        "vendor": "MIWA Lock Co., Ltd."
    },
    "5247": {
        "vendor": "U-tec Group Inc."
    },
    "5248": {
        "vendor": "Beijing Roborock Technology Co., Ltd."
    },
    "5249": {
        "vendor": "Shenzhen Xenon Industrial Ltd"
    },
    "5250": {
        "vendor": "Guangzhou Lingqu Electronic Technology Co., Ltd"
    },
    "5251": {
        "vendor": "Shenzhen Jijia Intelligent Technology Co., Ltd."
    },
    "5252": {
        "vendor": "CANDY HOUSE, Inc."
    },
    "5253": {
        "vendor": "ELIT Scandinavia ApS"
    },
    "5254": {
        "vendor": "Infibrite Inc"
    },
    "5255": {
        "vendor": "Whirlpool Corp."
    },
    "5256": {
        "vendor": "Shortcut Labs (Flic)"
    },
    "5257": {
        "vendor": "INTEREL BUILDING AUTOMATION"
    },
    "5258": {
        "vendor": "Occhio GmbH"
    },
    "5259": {
        "vendor": "Samraj Technologies Limited"
    },
    "6548": {
        "vendor": "Gewiss S.p.A."
    },
    "10132": {
        "vendor": "Climax Technology Co., Ltd."
    },
    "24582": {
        "vendor": "Google LLC"
    }
}

			let vendor_name = ''
			vendor_id = '' + vendor_id;
			if(vendor_id.length && typeof matter_vendors_lookup[vendor_id] != 'undefined'){
				
				if(typeof matter_vendors_lookup[vendor_id]['vendor'] == 'string'){
					vendor_name = matter_vendors_lookup[vendor_id]['vendor'];
				}
				if(typeof matter_vendors_lookup[vendor_id]['legal'] == 'string'){
					if(vendor_name != ''){
						vendor_name = vendor_name + ' a.k.a. ';
					}
					vendor_name = vendor_name + matter_vendors_lookup[vendor_id]['legal'];
				}
				if(vendor_name == '' && typeof matter_vendors_lookup[vendor_id]['url'] == 'string'){
					vendor_name = matter_vendors_lookup[vendor_id]['url'];
				}
			}
			return vendor_name;
		}
		
    
    }

	new MatterAdapter();
	
})();


