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
            
            this.busy_discovering = false;
            this.busy_pairing = false;
            this.device_to_pair = null;
            
            this.hotspot_addon_installed = false;
            this.use_hotspot = false;
            this.wifi_credentials_available = false;
            
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
				clearInterval(this.poll_interval);
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
                
                
                // Start pairing button press
                document.getElementById('extension-matter-adapter-start-pairing-button').addEventListener('click', (event) => {
                	console.log("Start pairing button clicked");
                    
                    
                    const code = document.getElementById('extension-matter-adapter-manual-pairing-code').value;
                    
                    if(code.length < 5){
                        console.log("code was too short");
                        alert("That code is too short");
                        return;
                    }
                    if(this.device_to_pair == null){
                        return // shouldn't be possible, but just to be safe
                    }
                    
                    //document.getElementById('extension-matter-adapter-start-pairing-button').classList.add('extension-matter-adapter-hidden');
                    //document.getElementById('extension-matter-adapter-busy-pairing-hint').classList.remove('extension-matter-adapter-hidden');
                    
					// Inform backend
                    this.busy_pairing = true;
                    
                    console.log("Manual pairing code: ", code);
					window.API.postJson(
						`/extensions/${this.id}/api/ajax`,
						{'action':'start_pairing',
                        'pairing_type':'commission_with_code',
                        'code':code,
                        'device': this.device_to_pair}
					).then((body) => { 
						console.log("pair device response: ", body);
					}).catch((e) => {
                        this.busy_pairing = false;
						console.error("matter-adapter: error making pairing request: ", e);
                        document.getElementById('extension-matter-adapter-start-pairing-button').classList.remove('extension-matter-adapter-hidden');
					});
                });
                
                
                // Pairing failed, try again button
    			document.getElementById('extension-matter-adapter-pairing-failed-try-again-button').addEventListener('click', (event) => {
    				this.start_discovery();
    			});
            
                // Easter egg when clicking on the title
    			document.getElementById('extension-matter-adapter-title').addEventListener('click', (event) => {
    				this.show();
    			});
            
            
                // ADD DEVICES BUTTON
                document.getElementById('extension-matter-adapter-show-second-page-button').addEventListener('click', (event) => {
                    console.log("clicked on + button");
                    
                    // iPhones need this fix to make the back button lay on top of the main menu button
                    document.getElementById('extension-matter-adapter-view').style.zIndex = '3';
                    document.getElementById('extension-matter-adapter-content-container').classList.add('extension-matter-adapter-showing-second-page');
                    
                    this.start_discovery();
                    
                    // start polling for data
                    this.poll_interval = setInterval(() =>{
                        this.pairing_poll();
                    },5000);
                    
    			});
            
                // Back button, shows main page
                document.getElementById('extension-matter-adapter-back-button-container').addEventListener('click', (event) => {
                    console.log("clicked on back button");
                    this.busy_discovering = false;
                    this.busy_pairing = false;
                    
                    try{
        				clearInterval(this.poll_interval);
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
				clearInterval(this.poll_interval);
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
				
		  		// Init
		        window.API.postJson(
		          `/extensions/${this.id}/api/ajax`,
                    {'action':'init'}

		        ).then((body) => {
                    
                    try{
                        if(this.debug){
                            console.log("Matter adapter debug: init response: ", body);
                        }
                    
                        // We have now received initial data from the addon, so we can hide the loading spinner by adding the 'hidden' class to it.
                        document.getElementById('extension-matter-adapter-loading').classList.add('extension-matter-adapter-hidden');
                    
                        // If debug is available in the init data, set the debug value and output the init data to the console
                        if(typeof body.debug != 'undefined'){
                            this.debug = body.debug;
                            if(this.debug){
                                console.log("Matter adapter debugging: Init response: ", body);
                            
                                if(document.getElementById('extension-matter-adapter-debug-warning') != null){
                                    document.getElementById('extension-matter-adapter-debug-warning').style.display = 'block';
                                }
                            }
                        }
                    
                        if(typeof body.use_hotspot != 'undefined' && typeof body.hotspot_addon_installed != 'undefined' && typeof body.wifi_credentials_available != 'undefined'){
                            this.hotspot_addon_installed = body.hotspot_addon_installed;
                            this.use_hotspot = body.use_hotspot;
                            this.wifi_credentials_available = body.wifi_credentials_available;
                            if(this.use_hotspot && !this.hotspot_addon_installed){
                                document.getElementById('extension-matter-adapter-install-hotspot-hint').classList.remove('extension-matter-adapter-hidden');
                            }
                            else if(!this.wifi_credentials_available){
                                document.getElementById('extension-matter-adapter-missing-wifi-credentials-hint').classList.remove('extension-matter-adapter-hidden');
                            }
                        }
                    
                        if(typeof body.nodes != 'undefined'){
                            console.log("nodes: ", body.nodes);
                            const nodes_string = JSON.stringify(body.nodes, null, 4)
                            document.getElementById('extension-matter-adapter-paired-devices-list-pre').innerHTML = nodes_string;
                            if(body.nodes.length > 0){
                                alert("MATTER DEVICE PAIRED!");
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
			catch(e){
				console.log("Error in API call to init: ", e);
			}
        }
    

        // is called once every few seconds by poll_interval
        pairing_poll(){
            
            if(this.busy_polling == true){
                console.warn("still busy polling, not doing a new poll request");
                return;
            }
            this.busy_polling = true;
            
			window.API.postJson(
				`/extensions/${this.id}/api/ajax`,
				{'action':'poll'}
            
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
                
                
                if(typeof body.discovered != 'undefined' && this.busy_discovering == false){
                    this.discovered = body.discovered;
                    this.list_discovered_devices();
                }
                if(typeof body.nodes != 'undefined'){
                    this.nodes = body.nodes;
                    //this.regenenerate_items();
                }
                
                
                
                
                
			}).catch((e) => {
                this.busy_polling = false;
				console.log("matter-adapter: connnection error after start pairing button press: ", e);
                document.getElementById('extension-matter-adapter-start-pairing-button').classList.remove('extension-matter-adapter-hidden');
			});
            
        }
        
        
        // Called whenever the addon should start discovering devices
        start_discovery(){
            
            this.busy_discovering = true;
            this.busy_pairing = false;
            this.device_to_pair = null;
            
            document.getElementById('extension-matter-adapter-second-page').classList.add('extension-matter-adapter-busy-discovering');
            document.getElementById('extension-matter-adapter-second-page').classList.remove('extension-matter-adapter-busy-pairing');
            document.getElementById('extension-matter-adapter-discovered-devices-list').innerHTML = '<div class="extension-matter-adapter-spinner"><div></div><div></div><div></div><div></div></div>';
            document.getElementById('extension-matter-adapter-pairing-step1').classList.remove('hidden');
            document.getElementById('extension-matter-adapter-pairing-step2').classList.add('hidden');
            document.getElementById('extension-matter-adapter-pairing-step3').classList.add('hidden');
            
            document.getElementById('extension-matter-adapter-busy-pairing-hint').classList.add('extension-matter-adapter-hidden');
            
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
                    //document.getElementById('extension-matter-adapter-start-pairing-button').classList.remove('extension-matter-adapter-hidden');
                }
            
			}).catch((e) => {
				console.log("matter-adapter: connnection error after disover button press: ", e);
                //document.getElementById('extension-matter-adapter-start-pairing-button').classList.remove('extension-matter-adapter-hidden');
			});
        }
        
        
        
        
        //
        //  GENERATE DISCOVERED DEVICES LIST
        //
        
        list_discovered_devices(){
            
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
                
                let pair_button_el = document.createElement('button');
                pair_button_el.classList.add('extension-matter-adapter-discovered-item-pair-button');
                pair_button_el.classList.add('text-button');
                pair_button_el.innerText = "Pair";
                
				pair_button_el.addEventListener('click', (event) => {
                    console.log("Pair button click. event: ", event);
                    
                    document.getElementById('extension-matter-adapter-pairing-step1').classList.add('extension-matter-adapter-hidden');
                    document.getElementById('extension-matter-adapter-pairing-step2').classList.remove('extension-matter-adapter-hidden');
                    document.getElementById('extension-matter-adapter-busy-pairing-hint').classList.add('extension-matter-adapter-hidden');
                    document.getElementById('extension-matter-adapter-start-pairing-button').classList.remove('extension-matter-adapter-hidden');
                    
                    document.getElementById('extension-matter-adapter-pairing-step2-device-title').innerText = item.deviceName;
                    this.device_to_pair = item;
                    
                    event.target.closest(".extension-matter-adapter-discovered-item").classList.add('extension-matter-adapter-discovered-item-being-paired');
                    
			  	});
                
                
                div_el.appendChild(pair_button_el);
                
                // Add the clone to the list container
				list_el.append(div_el);
                
			} // end of for loop
            
            
            
        }
        
        
    
	
		//
		//  REGENERATE ITEMS LIST ON MAIN PAGE
		//
	
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
                    clone.querySelector(".extension-matter-adapter-item-name").innerText = items[item].name; 
                    clone.getElementsByClassName("extension-matter-adapter-item-value")[0].innerText = items[item].value;
                     
                    
                    // You could add a specific CSS class to an element depending, for example depending on some value
                    //clone.classList.add('extension-matter-adapter-item-highlighted');   
                    

					// ADD DELETE BUTTON
					const delete_button = clone.querySelectorAll('.extension-matter-adapter-item-delete-button')[0];
                    //console.log("delete button element: ", delete_button);
                    delete_button.setAttribute('data-name', items[item].name);
                    
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
	
 
    
    }

	new MatterAdapter();
	
})();


