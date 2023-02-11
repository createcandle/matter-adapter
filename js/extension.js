(function() {
	class MatterAdapter extends window.Extension {
	    constructor() {
	      	super('matter-adapter');
      		
            this.debug = false; // if enabled, show more output in the console
            
            this.id = 'matter-adapter';
            
			console.log("Adding matter-adapter addon to main menu");
			this.addMenuEntry('Matter');
        
            this.discovered = null;
            this.nodes = null;
            
            this.all_things = {};
            this.title_lookup_table = {};
            this.nodez = {};
            this.updating_firmware = false;
            
            this.busy_discovering = false;
            this.busy_pairing = false;
            this.busy_polling_counter = 0;
            this.device_to_pair = null;
            this.pairing_code = "";
            
            this.hotspot_addon_installed = false;
            this.use_hotspot = false;
            this.wifi_credentials_available = false;
            
            this.uuid == null; // used with qr scanner
            
            window.matter_adapter_poll_interval = null;
            // We'll try and get this data from the addon backend
            //this.items = [];
            
            
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
			console.log("matter-adapter show called");
            
            try{
				clearInterval(window.matter_adapter_poll_interval);
                window.matter_adapter_poll_interval = null;
			}
			catch(e){
				//console.log("no interval to clear? ", e);
			} 
            
			const main_view = document.getElementById('extension-matter-adapter-view');
			
			if(this.content == ''){
                console.log("content has not loaded yet");
				return;
			}
			else{
				main_view.innerHTML = this.content;
			}
			
            try{
                
                
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
                
                // commission_with_code
                // Start pairing button press
                document.getElementById('extension-matter-adapter-start-normal-pairing-button').addEventListener('click', (event) => {
                	console.log("Start commission_with_code button clicked. this.busy_pairing: ", this.busy_pairing);
                    
                    const wifi_ssid = document.getElementById('extension-matter-adapter-wifi-ssid').value;
                    const wifi_password = document.getElementById('extension-matter-adapter-wifi-password').value;
                    const wifi_remember = document.getElementById('extension-matter-adapter-wifi-remember-checkbox').value;
                    
                    if(wifi_ssid.length < 2){
                        console.log("Wifi name is too short");
                        alert("That wifi name is too short");
                        return;
                    }
                    if(wifi_password.length < 8){
                        console.log("Wifi password is too short");
                        alert("That wifi password is too short");
                        return;
                    }
                    
                    
                    const code = this.pairing_code;
                    console.log("Pairing code: ", code);
                    if(code.length < 5){
                        console.log("pairing code was too short");
                        alert("That pairing code is too short");
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
                    
					
                    this.busy_pairing = true;
                    document.getElementById('extension-matter-adapter-second-page').classList.add('extension-matter-adapter-busy-pairing');
					
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
						console.log("pair device via commission_with_code response: ", body);
                        
                        
                        
					}).catch((e) => {
                        this.busy_pairing = false;
						console.error("matter-adapter: error making commission_with_code pairing request: ", e);
                        //document.getElementById('extension-matter-adapter-start-normal-pairing-button').classList.remove('extension-matter-adapter-hidden');
					});
                });
                
                
                // commission_on_network
                // Start pairing via commission_on_network button press
                document.getElementById('extension-matter-adapter-start-network-pairing-button').addEventListener('click', (event) => {
                	console.log("Start network pairing button clicked");
                    
                    const code = this.pairing_code;//document.getElementById('extension-matter-adapter-pairing-code').value;
                    
                    if(code.length < 5){
                        console.log("code was too short");
                        alert("That code is too short");
                        return;
                    }
                    
                    //document.getElementById('extension-matter-adapter-start-normal-pairing-button').classList.add('extension-matter-adapter-hidden');
                    //document.getElementById('extension-matter-adapter-busy-pairing-indicator').classList.remove('extension-matter-adapter-hidden');
                    
					// Inform backend
                    this.busy_pairing = true;
                    document.getElementById('extension-matter-adapter-second-page').classList.add('extension-matter-adapter-busy-pairing');
                    
                    console.log("Pairing code: ", code);
					window.API.postJson(
						`/extensions/${this.id}/api/ajax`,
						{'action':'start_pairing',
                        'pairing_type':'commission_on_network',
                        'code':code}
					).then((body) => { 
						console.log("pair device via commission_on_network response: ", body);
					}).catch((e) => {
                        this.busy_pairing = false;
						console.error("matter-adapter: error making commission_on_network pairing request: ", e);
                        //document.getElementById('extension-matter-adapter-start-network-pairing-button').classList.remove('extension-matter-adapter-hidden');
					});
                });


                // reveal wifi change button
    			document.getElementById('extension-matter-adapter-reveal-wifi-setup-button').addEventListener('click', (event) => {
                    document.getElementById('extension-matter-adapter-current-wifi-ssid-container').classList.add('extension-matter-adapter-hidden');
                    document.getElementById('extension-matter-adapter-provide-wifi-container').classList.remove('extension-matter-adapter-hidden');
    			});
                
                // Pairing failed, try again button
                /*
    			document.getElementById('extension-matter-adapter-pairing-failed-try-again-button').addEventListener('click', (event) => {
    				this.start_discovery();
    			});
                */
            
                // DEV
    			document.getElementById('extension-matter-adapter-stop-poll-button').addEventListener('click', (event) => {
                    console.log("stopping poll?");
                    try{
        				clearInterval(window.matter_adapter_poll_interval);
                        window.matter_adapter_poll_interval = null;
                        console.log("cleared interval");
        			}
        			catch(e){
        				console.log("no interval to clear? ", e);
        			} 
    			});
                
                
                // Show more pairing options button
    			document.getElementById('extension-matter-adapter-show-more-pairing-options-button').addEventListener('click', (event) => {
    				document.getElementById('extension-matter-adapter-other-pairing-options-container').classList.remove('extension-matter-adapter-hidden');
                    document.getElementById('extension-matter-adapter-show-more-pairing-options-button').classList.add('extension-matter-adapter-hidden');
    			});
                
                
                // Manually entered pairing code button
    			document.getElementById('extension-matter-adapter-save-manual-input-pairing-code-button').addEventListener('click', (event) => {
                    document.getElementById('extension-matter-adapter-save-manual-input-pairing-code-button').classList.add('extension-matter-adapter-hidden');
                    
                    const input_code = document.getElementById('extension-matter-adapter-pairing-code-input').value;
                    if(input_code.startsWith('MT:') && input_code.length > 6){
                        this.pairing_code = input_code;
                        setTimeout(function(){
                            document.getElementById('extension-matter-adapter-save-manual-input-pairing-code-button').classList.remove('extension-matter-adapter-hidden');
                        }, 4000);
                        this.show_pairing_start_area();
                    }
                    
    				//document.getElementById('extension-matter-adapter-other-pairing-options-container').classList.remove('extension-matter-adapter-hidden');
    			});
                
    			document.getElementById('extension-matter-adapter-pairing-network-question-normal-button').addEventListener('click', (event) => {
    				document.getElementById('extension-matter-adapter-second-page').classList.remove('extension-matter-adapter-pairing-questioning');
                    document.getElementById('extension-matter-adapter-second-page').classList.add('extension-matter-adapter-pairing-normal');
    			});
                
    			document.getElementById('extension-matter-adapter-pairing-network-question-network-button').addEventListener('click', (event) => {
    				document.getElementById('extension-matter-adapter-second-page').classList.remove('extension-matter-adapter-pairing-questioning');
                    document.getElementById('extension-matter-adapter-second-page').classList.add('extension-matter-adapter-pairing-network');
    			});
                
                
                
            
                // Easter egg when clicking on the title
    			document.getElementById('extension-matter-adapter-title').addEventListener('click', (event) => {
    				this.show();
    			});
            
            
                // ADD DEVICES PLUS BUTTON
                document.getElementById('extension-matter-adapter-show-second-page-button').addEventListener('click', (event) => {
                    console.log("clicked on (+) button");
                    
                    // iPhones need this fix to make the back button lay on top of the main menu button
                    document.getElementById('extension-matter-adapter-view').style.zIndex = '3';
                    document.getElementById('extension-matter-adapter-content-container').classList.add('extension-matter-adapter-showing-second-page');
                    
                    this.generate_qr();
                    //this.start_discovery();
                    
                    // start polling for data
                    if(window.matter_adapter_poll_interval == null){
                        window.matter_adapter_poll_interval = setInterval(() =>{
                            this.pairing_poll();
                        },5000);
                    }
                    
                    document.getElementById('extension-matter-adapter-pairing-start-area').classList.add('extension-matter-adapter-hidden');
    				document.getElementById('extension-matter-adapter-second-page').classList.add('extension-matter-adapter-pairing-questioning');
                    document.getElementById('extension-matter-adapter-second-page').classList.remove('extension-matter-adapter-pairing-normal');
					document.getElementById('extension-matter-adapter-second-page').classList.remove('extension-matter-adapter-pairing-network');
    			    document.getElementById('extension-matter-adapter-pairing-step-qr').classList.remove('extension-matter-adapter-hidden');
    			});
            
                
                // Back button, shows main page
                document.getElementById('extension-matter-adapter-back-button-container').addEventListener('click', (event) => {
                    console.log("clicked on back button");
                    this.busy_discovering = false;
                    this.busy_pairing = false;
                    
                    try{
        				clearInterval(window.matter_adapter_poll_interval);
                        window.matter_adapter_poll_interval = null;
        			}
        			catch(e){
        				//console.log("no interval to clear? ", e);
        			} 
                    
                    document.getElementById('extension-matter-adapter-content-container').classList.remove('extension-matter-adapter-showing-second-page');
                
                    // Undo the iphone fix, so that the main menu button is clickable again
                    document.getElementById('extension-matter-adapter-view').style.zIndex = 'auto';
                
                    this.get_init_data(); // repopulate the main page
                
    			});
            
            
                // Scroll the content container to the top
                document.getElementById('extension-matter-adapter-view').scrollTop = 0;
            
            

                // Finally, request the first data from the addon's API
                this.get_init_data();
                
            }
            catch(e){
                console.error("Matter: Show Error: ", e);
            }
            
		}
		
	
		// This is called then the user navigates away from the addon. It's an opportunity to do some cleanup. To remove the HTML, for example, or stop running intervals.
		hide() {
			console.log("matter-adapter hide called");
            
            try{
				clearInterval(window.matter_adapter_poll_interval);
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
                				console.error("error looping over all things" , e);
                			}
                        }
                    
                        console.log("this.all_things: ", this.all_things);
                        console.log("this.title_lookup_table: ", this.title_lookup_table);
                        
                        this.get_init_data2();
                    });
                }
    			catch(e){
    				console.log("Error calling API.getThings(): " , e);
                    this.request_devices_list();
    			}
                
			}
			catch(e){
				console.log("Error in API call to init: ", e);
			}
        }
        
        
        
        get_init_data2(){
            
	  		// Init
	        window.API.postJson(
	          `/extensions/${this.id}/api/ajax`,
                {'action':'init'}

	        ).then((body) => {
                
                try{
                    if(this.debug){
                        console.log("Matter adapter debug: init2 response: ", body);
                    }
                    
                    // We have now received initial data from the addon, so we can hide the loading spinner by adding the extension-matter-adapter-hidden class to it.
                    document.getElementById('extension-matter-adapter-loading').classList.add('extension-matter-adapter-hidden');
                
                    // If debug is available in the init data, set the debug value and output the init data to the console
                    if(typeof body.debug != 'undefined'){
                        this.debug = body.debug;
                        if(this.debug){
                            console.log("Matter adapter debugging: Init2 response: ", body);
                        
                            if(document.getElementById('extension-matter-adapter-debug-warning') != null){
                                document.getElementById('extension-matter-adapter-debug-warning').style.display = 'block';
                            }
                        }
                    }
                
                    if(typeof body.use_hotspot != 'undefined' && typeof body.hotspot_addon_installed != 'undefined' && typeof body.wifi_credentials_available != 'undefined'){
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
                    
                    /*
                    if(typeof body.nodes != 'undefined'){
                        console.log("nodes: ", body.nodes);
                        const nodes_string = JSON.stringify(body.nodes, null, 4)
                        document.getElementById('extension-matter-adapter-paired-devices-list-pre').innerHTML = nodes_string;
                        if(body.nodes.length > 0){
                            
                        }
                    }
                    */
                    if(typeof body.nodez != 'undefined'){
                        console.log("nodez: ", body.nodez);
                        this.nodez = body.nodez;
                        const nodes_string = JSON.stringify(body.nodez, null, 4)
                        document.getElementById('extension-matter-adapter-paired-devices-list-pre').innerHTML = nodes_string;
                        this.regenerate_items();
                        if(body.nodez.length > 0){
                            
                        }
                    }
                    
                    if(typeof body.wifi_credentials_available != 'undefined' && typeof body.wifi_ssid != 'undefined'){
                        if(body.wifi_credentials_available && body.wifi_ssid != ""){
                            document.getElementById('extension-matter-adapter-current-wifi-ssid').innerText = body.wifi_ssid;
                            document.getElementById('extension-matter-adapter-current-wifi-ssid-container').classList.remove('extension-matter-adapter-hidden');
                            document.getElementById('extension-matter-adapter-provide-wifi-container').classList.add('extension-matter-adapter-hidden');
                        }
                    }
                    
                    
                    /*
                    // Generate the list of items
                    if(typeof body.items_list != 'undefined'){
                        this.items = body['items_list'];
                        this.regenerate_items(body['items_list']);
                    }
                    */
                }
                catch(e){
                    console.log("Error parsing matter init response: ", e);
                }
			
	        }).catch((e) => {
	  			console.log("Error getting MatterAdapter init data: ", e);
	        });	
        }
    
    
    
    
    

        // is called once every few seconds by poll_interval
        pairing_poll(){
            console.log("in pairing_poll");
            
            if(this.busy_polling == true){
                console.warn("still busy polling, not doing a new poll request");
                this.busy_polling_counter++;
                if(this.busy_polling_counter > 5){
                    this.busy_polling_counter = 0;
                    console.log("letting a new polling attempt through")
                }
                else{
                    return;
                }
                
            }
            this.busy_polling = true;
            
            
			window.API.postJson(
				`/extensions/${this.id}/api/ajax`,
				{'action':'poll','uuid':this.uuid}
            
			).then((body) => {
                console.log("matter adapter: poll response: ", body);
                this.busy_polling = false;
                
                if(typeof body.busy_discovering != 'undefined'){
                    this.busy_discovering = body.busy_discovering;
                    if(this.busy_discovering){
                        document.getElementById('extension-matter-adapter-second-page').classList.add('extension-matter-adapter-busy-discovering');
                    }
                    else{
                        document.getElementById('extension-matter-adapter-second-page').classList.remove('extension-matter-adapter-busy-discovering');
                    }
                }
                if(typeof body.busy_pairing != 'undefined'){
                    this.busy_pairing = body.busy_pairing;
                    if(this.busy_pairing){
                        document.getElementById('extension-matter-adapter-second-page').classList.add('extension-matter-adapter-busy-pairing');
                    }
                    else{
                        document.getElementById('extension-matter-adapter-second-page').classList.remove('extension-matter-adapter-busy-pairing');
                    }
                }
                
                if(typeof body.certificates_updated != 'undefined'){
                    if(body.certificates_updated){
                        document.getElementById('extension-matter-adapter-busy-updating-certificates').classList.add('extension-matter-adapter-hidden');
                    }
                    else{
                        document.getElementById('extension-matter-adapter-busy-updating-certificates').classList.remove('extension-matter-adapter-hidden');
                        if(this.debug){
                            console.log("matter adapter: busy updating certificates");
                        }
                    }
                
                }
                /*
                if(typeof body.discovered != 'undefined' && this.busy_discovering == false){
                    this.discovered = body.discovered;
                    this.list_discovered_devices();
                }
                */
                if(typeof body.nodes != 'undefined'){
                    this.nodes = body.nodes;
                    //this.regenenerate_items();
                }
                if(typeof body.pairing_code != 'undefined'){
                    if(body.pairing_code.startsWith('MT:')){
                        console.log("GOT A GOOD PAIRING CODE: ", body.pairing_code);
                        this.pairing_code = body.pairing_code;
                        
                        document.getElementById('extension-matter-adapter-pairing-code-input').value = this.pairing_code;
                        
                        this.show_pairing_start_area();
                    }
                    else{
                        console.log("pairing code did not start with MT: yet: ", body.pairing_code)
                    }
                    //this.regenenerate_items();
                }   
                
			}).catch((e) => {
                this.busy_polling = false;
				console.log("matter-adapter: poll error: ", e);
                document.getElementById('extension-matter-adapter-start-normal-pairing-button').classList.remove('extension-matter-adapter-hidden');
			});
            
            
            // Check if the QR code scanner was used
            /*
            fetch('https://www.candlesmarthome.com/qr/ajax.php', {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ "uuid": this.uuid })
            })
            .then(response => response.json())
            .then(response => console.log("Ajax read response: ", JSON.stringify(response)))
            */
        }
        
        show_pairing_start_area(){
            console.log("in show_pairing_start_area");
            if(this.pairing_code != ""){
                console.log("WiFi credentials and pairing code are available. Showing pairing start area.");
                document.getElementById('extension-matter-adapter-pairing-start-area').classList.remove('extension-matter-adapter-hidden');
                document.getElementById('extension-matter-adapter-pairing-step-qr').classList.add('extension-matter-adapter-hidden');
                document.getElementById('extension-matter-adapter-pairing-start-area-pairing-code').innerText = this.pairing_code;
            }
            else{
                console.log("WiFi credentials and pairing code are NOT both available yet. Not revealing pairing start area.");
            }
            
        }
        
        
        
        // Called whenever the addon should start discovering devices
        /*
        start_discovery(){
            
            this.busy_discovering = true;
            this.busy_pairing = false;
            this.device_to_pair = null;
            
            document.getElementById('extension-matter-adapter-second-page').classList.add('extension-matter-adapter-busy-discovering');
            document.getElementById('extension-matter-adapter-second-page').classList.remove('extension-matter-adapter-busy-pairing');
            document.getElementById('extension-matter-adapter-discovered-devices-list').innerHTML = '<div class="extension-matter-adapter-spinner"><div></div><div></div><div></div><div></div></div>';
            document.getElementById('extension-matter-adapter-pairing-step1').classList.remove(extension-matter-adapter-hidden);
            document.getElementById('extension-matter-adapter-pairing-step2').classList.add(extension-matter-adapter-hidden);
            document.getElementById('extension-matter-adapter-pairing-step3').classList.add(extension-matter-adapter-hidden);
            
            document.getElementById('extension-matter-adapter-busy-pairing-indicator').classList.add('extension-matter-adapter-hidden');
            
			window.API.postJson(
				`/extensions/${this.id}/api/ajax`,
				{'action':'discover'}
                //{'action':'start_pairing', 'name':new_name  ,'value':new_value}
            
			).then((body) => {
                console.log("discover response: ", body);
                if(body.state == true){
                    console.log("discover response was OK");
                    //document.getElementById('extension-matter-adapter-add-item-name').value = "";
                    //document.getElementById('extension-matter-adapter-add-item-value').value = null;
                    //console.log("new item was saved");
                    //document.getElementById('extension-matter-adapter-pairing-step2').style.display = 'block';
                    
                }
                else{
                    console.log("discover failed?");
                    //document.getElementById('extension-matter-adapter-start-normal-pairing-button').classList.remove('extension-matter-adapter-hidden');
                }
            
			}).catch((e) => {
				console.log("matter-adapter: connnection error after discover button press: ", e);
                //document.getElementById('extension-matter-adapter-start-normal-pairing-button').classList.remove('extension-matter-adapter-hidden');
			});
        }
        */
        
        
        
        //
        //  GENERATE DISCOVERED DEVICES LIST
        //
        
        old_list_discovered_devices(){
            
            let list_el = document.getElementById('extension-matter-adapter-discovered-devices-list');
            if(list_el == null){
                console.error("Error, the discovered devices list container did not exist yet");
                return;
            }
            
            // If the items list does not contain actual items, then stop
            if(this.discovered.length == 0){
                list_el.innerHTML = "No devices found";
                return;
            }
            else{
                list_el.innerHTML = "";
            }
            
			for( var index in this.discovered ){
                
                const item = this.discovered[index];
				console.log("creating discovered devices list. Item: ", item);
                
				let div_el = document.createElement('div');
                div_el.classList.add('extension-matter-adapter-discovered-item');
                
                // add discovered device title
				let title_el = document.createElement('h3');
                title_el.classList.add('extension-matter-adapter-discovered-item-device-name');
                title_el.innerText = item.deviceName;
                div_el.appendChild(title_el);
                
                /*
                let pair_button_el = document.createElement('button');
                pair_button_el.classList.add('extension-matter-adapter-discovered-item-pair-button');
                pair_button_el.classList.add('text-button');
                pair_button_el.innerText = "Pair";
                
				pair_button_el.addEventListener('click', (event) => {
                    console.log("Pair button click. event: ", event);
                    
                    document.getElementById('extension-matter-adapter-pairing-step1').classList.add('extension-matter-adapter-hidden');
                    document.getElementById('extension-matter-adapter-pairing-step2').classList.remove('extension-matter-adapter-hidden');
                    document.getElementById('extension-matter-adapter-busy-pairing-indicator').classList.add('extension-matter-adapter-hidden');
                    //document.getElementById('extension-matter-adapter-start-normal-pairing-button').classList.remove('extension-matter-adapter-hidden');
                    
                    document.getElementById('extension-matter-adapter-pairing-step2-device-title').innerText = item.deviceName;
                    this.device_to_pair = item;
                    
                    event.target.closest(".extension-matter-adapter-discovered-item").classList.add('extension-matter-adapter-discovered-item-being-paired');
                    
			  	});
                */
                
                div_el.appendChild(pair_button_el);
                
                // Add the clone to the list container
				list_el.append(div_el);
                
			} // end of for loop
            
            
            
        }
        
        
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
		//
		//  REGENERATE ITEMS
		//
	
		regenerate_items(){
			try {
				console.log("regenerating list");
				//console.log(items);
		
				//const pre = document.getElementById('extension-matter-adapter-response-data');
				const list = document.getElementById('extension-matter-adapter-paired-devices-list');
			
				const original = document.getElementById('extension-matter-adapter-original-item');
			    //console.log("original: ", original);
                
			    // Since each item has a name, here we're sorting the list based on that name first
				//this.all_things.sort((a, b) => (a.title.toLowerCase() > b.title.toLowerCase()) ? 1 : -1)
                //this.title_lookup_table.sort((a, b) => (a.toLowerCase() > b.toLowerCase()) ? 1 : -1)
                
                console.log("sorted title_lookup_table: ", this.title_lookup_table);
				if(typeof list == 'undefined'){
                    console.error('Error, target list element does not exist');
				    return;
				}
				list.innerHTML = "";
		        
				// Loop over all things
				for( let thing_id in this.title_lookup_table ){
					console.log("thing_id = ", thing_id );
                    console.log(this.title_lookup_table[thing_id]);
    				try{
                        let title = this.title_lookup_table[thing_id];
    					console.log("thing_title = ", title);
				
    					//let thing_id = things[key]['href'].substr(things[key]['href'].lastIndexOf('/') + 1);
                        //console.log("thing_id: ", thing_id);
                        //this.title_lookup_table[thing_id] = thing_title;
                        
                        
                        if(typeof this.nodez[thing_id] == 'undefined'){
                            console.error("ERROR, THING ID NOT PRESENT IN NODEZ: ", thing_id)
                            continue;
                        }
                        else{
                            console.log("OK, thing_id is in nodez");
                        }
                        let qitremz = this.nodez[thing_id];
                        
                        console.log("qitremz: ", qitremz); // device_id
                        //console.log("qitremz: ", qitremz);
                    
    					var clone = original.cloneNode(true);
    					clone.removeAttribute('id');
    					console.log("clone: ", clone);
                    
                        /*
    					try{
    						//console.log("qitremz['model_id'] = " + qitremz['model_id']);
    						if(typeof qitremz['vendor_name'] != "undefined"){
    							var icon_name = qitremz['vendor_name'].toLowerCase();
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
					
                    
    					try{
                            // Create big title
    						var a = document.createElement("a");
    						//s.classList.add('extension-matter-adapter-description'); 
    						a.setAttribute("href", "/things/matter-" + qitremz['node_id']);
                        
                            // Add title if it could be found
                            try{
                                if( typeof this.title_lookup_table[ 'matter-' + qitremz['node_id'] ] != 'undefined' ){
                                    var title_span = document.createElement("span");
                                    title_span.classList.add('extension-matter-adapter-item-title');
                            
                                    var title_text = document.createTextNode(this.title_lookup_table[ 'matter-' + qitremz['node_id'] ]);
                                    title_span.appendChild(title_text);
                                    a.appendChild(title_span);
                                    clone.querySelector('.extension-matter-adapter-item-title').appendChild(a);
                                }
                                else{
                                    console.warn("not in lookup table: ", qitremz['node_id']);
                                }
                            }
                            catch(e){
                                console.error("Error getting thing title: ", e);
                            }
                        
                            //var desc_span = document.createElement("span");
                            //desc_span.classList.add('extension-matter-adapter-item-description');
                    
                            //var desc_text = document.createTextNode( qitremz['product_name'] );
                            //desc_span.appendChild(desc_text);
                            //clone.querySelectorAll('.extension-matter-adapter-description' )[0].appendChild(title_span);
                            //a.appendChild(desc_span);
    						try{
                                clone.querySelector('.extension-matter-adapter-item-vendor-name').innerText = qitremz['vendor_name']
                                clone.querySelector('.extension-matter-adapter-item-product-name').innerText = qitremz['product_name']
                            }
                            catch(e){
                                console.log("Error setting vendor or product name: ", e);
                            }
                            
                            /*
                            // Add MAC address link
    						var s = document.createElement("a");
    						//s.classList.add('extension-matter-adapter-matter-id');  
    						s.setAttribute("href", "/things/matter-" + qitremz['node_id']);              
    						var t = document.createTextNode( qitremz['node_id'] );
    						s.appendChild(t);                                   
    						clone.querySelectorAll('.extension-matter-adapter-matter-id' )[0].appendChild(s);
						    */
                            
                            // Add firmware version
    						if(typeof qitremz['software_version'] != "undefined"){
                                console.log("software version: ", qitremz['software_version']);
                                //alert(qitremz['software_version']);
    							var s = document.createElement("span");
    							//s.classList.add('extension-matter-adapter-matter-id');             
    							var t = document.createTextNode( qitremz['software_version'] );
    							s.appendChild(t);                                   
    							clone.querySelector('.extension-matter-adapter-item-software-version' ).appendChild(s);
    						}
    						if(typeof qitremz['hardware_version'] != "undefined"){
    							var s = document.createElement("span");
    							//s.classList.add('extension-matter-adapter-matter-id');             
    							var t = document.createTextNode( qitremz['hardware_version'] );
    							s.appendChild(t);                                   
    							clone.querySelector('.extension-matter-adapter-item-hardware-version' ).appendChild(s);
    						}
						
						
    					}
    					catch(e){
    						console.log("error handling Matter device data: " , e);
    					}
						
    					// Click on first firmware update button
    					const show_update_button = clone.querySelector('.extension-matter-adapter-item-update-button');
    					//console.log("show_update_button = ");
    					//console.log(show_update_button);
    					
                        //if(qitremz['update']['state'] == 'available'){
    					//	show_update_button.disabled = false;
    					//}
    					show_update_button.addEventListener('click', (event) => {
    						//console.log("clicked on show update button. node_id:" + qitremz['node_id']);
    						var target = event.currentTarget;
    						var parent3 = target.closest("extension-matter-adapter-item");
    						//console.log(parent3);
    						parent3.classList.add("extension-matter-adapter-update");
    					});
					    
					    /*
    					const read_about_risks_button = clone.querySelectorAll('.extension-matter-adapter-read-about-risks')[0];
    					read_about_risks_button.addEventListener('click', (event) => {
    						document.getElementById('extension-matter-adapter-content').classList = ['extension-matter-adapter-show-tab-tutorial'];
    					});
					    */
					
    					const cancel_update_button = clone.querySelector('.extension-matter-adapter-overlay-cancel-update-button');
    					cancel_update_button.addEventListener('click', (event) => {
    						//console.log("cancel update button has been clicked");
    						var target = event.currentTarget;
    						var parent3 = target.closest("extension-matter-adapter-item");
    						parent3.classList.remove("extension-matter-adapter-update");
    					});
					
					
					
					
					
    					// Click on start firmware update button
    					const start_update_button = clone.querySelectorAll('.extension-matter-adapter-overlay-start-update-button')[0];
                        start_update_button.dataset.node_id = qitremz['node_id'];
    					start_update_button.addEventListener('click', (event) => {
    						//console.log("clicked on start update button. Event:", event);
    						//console.log("- node_id:" + qitremz['node_id']);
                            //console.log("data attribute: ", event.target.dataset);
                            //console.log("data attribute: ", event.target.dataset.node_id);
                        
    						var target = event.currentTarget;
    						var parent3 = target.target.closest("extension-matter-adapter-item");
    						parent3.classList.remove("extension-matter-adapter-update");
    						parent3.classList.add("extension-matter-adapter-updating");
						
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
                                    console.log("matter: postJson error while requesting update start");
                                }
    						});
					
    				  	});
					
					
    					// Force-delete device from matter network feature. Unfinished, may just be confusing.
    					// Add delete button click event
    					const delete_button = clone.querySelector('.extension-matter-adapter-item-delete-button');
    					delete_button.addEventListener('click', (event) => {
                            if(this.debug){
                                //console.log("delete button clicked");
                            }
                            if(confirm("Are you sure you want to remove this device?")){
        						var target = event.currentTarget;
        						var parent3 = target.closest("extension-matter-adapter-item");
        						parent3.classList.add("delete");
        						var parent4 = parent3.parentElement;
        						parent4.removeChild(parent3);
					
        						// Send new values to backend
        						window.API.postJson(
        							`/extensions/${this.id}/api/ajax`,
        							{'action':'delete','node_id':qitremz['node_id']}
        						).then((body) => { 
        							if(this.debug){
                                        console.log("delete matter item reaction: ", body);
        							    //console.log(body); 
        							    //if( body['state'] != true ){
        							    //pre.innerText = body['message'];
                                    }
                                    if(body['status'] == 'ok'){
                                        parent3.classList.add(".extension-matter-adapter-hidden");
                                    }
                                
        							//}

        						}).catch((e) => {
        							//console.log("matter2mqt error in delete items handler: " , e);
        							if(this.debug){
                                        console.error('delete connection error', e);
                                    }
        						});
                            }
					
    				  	});
					
					
                        // makes it easier to target each item in the list by giving it a unique class
                        clone.classList.add('extension-matter-adapter-item-' + qitremz['node_id']);
                    
                        // show firmware update status
                        if( typeof qitremz['update'] != 'undefined' ){
                            if(qitremz['update']['state'] == "updating"){
                                clone.classList.add('extension-matter-adapter-updating');
                                const clone_progress_bar = clone.querySelectorAll('.extension-matter-adapter-update-progress-bar')[0];
                                clone_progress_bar.style.width = qitremz['update']['progress'] + "%";
                                const clone_progress_bar_percentage = clone.querySelectorAll('.extension-matter-adapter-update-progress-bar-percentage')[0];
                                clone_progress_bar_percentage.innerText = qitremz['update']['progress'] + "%";
                                this.updating_firmware = true;
        					}
                        }
				
    					list.append(clone);
                        
                        
                        
                    }
        			catch(e){
        				console.log("general error while looping over nodez: ", e);
        			}
                    
                    
                    
				} // end of for loop
			
                if(list.innerHTML == ""){
                    list.innerHTML = '<div style="margin:10rem auto;padding:2rem;max-width:40rem;text-align:center; background-color:rgba(0,0,0,.1);border-radius:10px"><h2>No Matter devices paired yet</h2><p>Click on the (+) button in the bottom right corner if you want to connect a new Matter device.</p></div>';
                }
                
                if(this.updating_firmware){
					// Disable all update buttons an update is in progress
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
				// statements to handle any exceptions
				//console.log("error while generating items: " , e); // pass exception object to error handler
			}
			

			
		}    
	
		//
		//  REGENERATE ITEMS LIST ON MAIN PAGE
		//
	    /*
		regenerate_items(items){
            // This funcion takes a list of items and generates HTML from that, and places it in the list container on the main page
			try {
				console.log("regenerating. items: ", items);
		        if(this.debug){
		            console.log("I am only here because debugging is enabled");
		        }
                
                let list_el = document.getElementById('extension-matter-adapter-paired-devices-list'); // list element
                if(list_el == null){
                    console.log("Error, the main list container did not exist yet");
                    return;
                }
                
                // If the items list does not contain actual items, then stop
                if(items.length == 0){
                    list_el.innerHTML = "No items";
                    return
                }
                else{
                    list_el.innerHTML = "";
                }
                
                // The original item which we'll clone  for each item that is needed in the list.  This makes it easier to design each item.
				const original = document.getElementById('extension-matter-adapter-original-item');
			    //console.log("original: ", original);
                
			    // Since each item has a name, here we're sorting the list based on that name first
				items.sort((a, b) => (a.name.toLowerCase() > b.name.toLowerCase()) ? 1 : -1)
				
                
				for( var item in items ){
					
					var clone = original.cloneNode(true); // Clone the original item
					clone.removeAttribute('id'); // Remove the ID from the clone
                    
                    // Place the name in the clone
                    clone.querySelector(".extension-matter-adapter-item-name").innerText = qitremz.name; 
                    clone.getElementsByClassName("extension-matter-adapter-item-value")[0].innerText = qitremz.value;
                     
                    
                    // You could add a specific CSS class to an element depending, for example depending on some value
                    //clone.classList.add('extension-matter-adapter-item-highlighted');   
                    

					// ADD DELETE BUTTON
					const delete_button = clone.querySelectorAll('.extension-matter-adapter-item-delete-button')[0];
                    //console.log("delete button element: ", delete_button);
                    delete_button.setAttribute('data-name', qitremz.name);
                    
					delete_button.addEventListener('click', (event) => {
                        console.log("delete button click. event: ", event);
                        if(confirm("Are you sure you want to delete this item?")){
    						
    						// Inform backend
    						window.API.postJson(
    							`/extensions/${this.id}/api/ajax`,
    							{'action':'delete','name': event.target.dataset.name}
    						).then((body) => { 
    							console.log("delete item response: ", body);
                                if(body.state == true){
                                    console.log('the item was deleted on the backend');
                                    
                                    event.target.closest(".extension-matter-adapter-item").style.display = 'none'; // find the parent item
                                    // Remove the item form the list, or regenerate the entire list instead
                                    // parent4.removeChild(parent3);
                                }

    						}).catch((e) => {
    							console.log("matter-adapter: error in delete items handler: ", e);
    						});
                        }
				  	});

                    // Add the clone to the list container
					list_el.append(clone);
                    
				} // end of for loop
                
                // Hide the loading spinner and show the paired devices list
                document.getElementById('extension-matter-adapter-loading').classList.add('extension-matter-adapter-hidden');
                list_el.classList.remove('extension-matter-adapter-hidden');
            
            
			}
			catch (e) {
				console.log("Error in regenerate_items: ", e);
			}
		}
	
        */
 
 
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
            
            document.getElementById('extension-matter-adapter-short-qr-scan-url').innerText = short_url;
            document.getElementById('extension-matter-adapter-qr-scan-link').href = long_url;
            
            const target_element = document.getElementById('extension-matter-adapter-qr-code');
	
    	    var qrcode = new QRCode(target_element, {
    		    width : 300,
    		    height : 300
    	    });
    	    qrcode.makeCode(long_url);
        }
    
    }

	new MatterAdapter();
	
})();


