(function() {
	class ExampleAddon1 extends window.Extension {
	    constructor() {
	      	super('example-addon1');
      		
            this.debug = false; // if enabled, show more output in the console
            
            // We'll try and get this data from the addon backend
            this.a_number_setting = null;
            this.items = [];
            
			console.log("Adding example-addon1 addon to main menu");
			this.addMenuEntry('Example addon 1');
            
            // Load the html
            this.content = ''; // The html from the view will be loaded into this variable
			fetch(`/extensions/${this.id}/views/content.html`)
	        .then((res) => res.text())
	        .then((text) => {
	         	this.content = text;
                
                // This is needed because the user might already be on the addon page and click on the menu item again. This helps to reload it.
	  		 	if( document.location.href.endsWith("extensions/example-addon1") ){
	  		  		this.show();
	  		  	}
	        })
	        .catch((e) => console.error('Failed to fetch content:', e));
            
            
            // This is not needed, but might be interesting to see. It will show you the API that the controller has available. For example, you can get a list of all the things this way.
            console.log("window API: ", window.API);
            
	    }






		//
        //  SHOW
        //
        // This is called then the user clicks on the addon in the main menu, or when the page loads and is already on this addon's location.
	    show() {
			console.log("example-addon1 show called");
			//console.log("this.content:");
			//console.log(this.content);
            
            
			const main_view = document.getElementById('extension-example-addon1-view');
			
			if(this.content == ''){
                console.log("content has not loaded yet");
				return;
			}
			else{
				main_view.innerHTML = this.content;
			}
			
            
            // ADD button press
            document.getElementById('extension-example-addon1-add-item-button').addEventListener('click', (event) => {
            	console.log("first button clicked. Event: ", event);
                
                const new_name = document.getElementById('extension-example-addon1-add-item-name').value;
                const new_value = document.getElementById('extension-example-addon1-add-item-value').value;
                
                if(new_name == ""){
                    alert("Please provide a name");
                    return;
                }
                    
                // isNaN is short for "is not a number"
                if(isNaN(new_value)){
                    alert("Please provide a valid number");
                    return;
                }
                
                // If we end up here, then a name and number were present in the input fields. We can now ask the backend to save the new item.
				window.API.postJson(
					`/extensions/${this.id}/api/ajax`,
					{'action':'add', 'name':new_name  ,'value':new_value}
                    
				).then((body) => {
                    console.log("add item response: ", body);
                    if(body.state == true){
                        console.log("adding a new item went ok");
                        document.getElementById('extension-example-addon1-add-item-name').value = "";
                        document.getElementById('extension-example-addon1-add-item-value').value = null;
                        console.log("new item was saved");
                    }
                    else{
                        console.log("saving new item failed!");
                        alert("sorry, saving new item failed.");
                    }
                    
				}).catch((e) => {
					console.log("example-addon1: connnection error after add new item button press: ", e);
                    alert("failed to add new item: connection error");
				});
            
            });
            
            
            
            
            
            // Easter egg when clicking on the title
			document.getElementById('extension-example-addon1-title').addEventListener('click', (event) => {
				alert("You found an easter egg!");
			});
            
            
            
            
            // Button to show the second page
            document.getElementById('extension-example-addon1-show-second-page-button').addEventListener('click', (event) => {
                console.log("clicked on + button");
                document.getElementById('extension-example-addon1-content-container').classList.add('extension-example-addon1-showing-second-page');
                
                // iPhones need this fix to make the back button lay on top of the main menu button
                document.getElementById('extension-example-addon1-view').style.zIndex = '3';
			});
            
            // Back button, shows main page
            document.getElementById('extension-example-addon1-back-button-container').addEventListener('click', (event) => {
                console.log("clicked on back button");
                document.getElementById('extension-example-addon1-content-container').classList.remove('extension-example-addon1-showing-second-page');
                
                // Undo the iphone fix, so that the main menu button is clickable again
                document.getElementById('extension-example-addon1-view').style.zIndex = 'auto';
                
                this.get_init_data(); // repopulate the main page
                
			});
            
            
            // Scroll the content container to the top
            document.getElementById('extension-example-addon1-view').scrollTop = 0;
            
            // Finally, request the first data from the addon's API
            this.get_init_data();
            
            
		}
		
	
		// This is called then the user navigates away from the addon. It's an opportunity to do some cleanup. To remove the HTML, for example, or stop running intervals.
		hide() {
			console.log("example-addon1 hide called");
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
                    console.log("init response: ", body);
                    
                    // We have now received initial data from the addon, so we can hide the loading spinner by adding the 'hidden' class to it.
                    document.getElementById('extension-example-addon1-loading').classList.add('extension-example-addon1-hidden');
                    
                    // If debug is available in the init data, set the debug value and output the init data to the console
                    if(typeof body.debug != 'undefined'){
                        this.debug = body.debug;
                        if(body.debug == true){
                            console.log("example addon 1: debugging enabled. Init API result: ", body);
                            
                            // If debugging is enabled, please show a big warning that this is the case. 
                            // Debugging can be a privacy risk, since lots of data will be stored in the internal logs. Showing this warning helps avoid abuse.
                            // Here we just manipulate the element style directly, instead of using the 'hidden' class.
                            if(document.getElementById('extension-example-addon1-debug-warning') != null){
                                document.getElementById('extension-example-addon1-debug-warning').style.display = 'block';
                            }
                        }
                    }
                    
                    // Show the value of the number from the addon's settings
                    if(typeof body.a_number_setting != 'undefined'){
                        this.a_number_setting = body['a_number_setting'];
                        console.log("this.a_number_setting: ", this.a_number_setting);
                        document.getElementById('extension-example-addon1-number-setting-output').innerText = body.a_number_setting; // body['a_number_setting'] and body.a_number_setting are two ways of writing the same thing 
                    }
                    
                    // Show the value of the slider
                    document.getElementById('extension-example-addon1-slider-value-output').innerText = body.slider_value;
                    
                    // Generate the list of items
                    if(typeof body.items_list != 'undefined'){
                        this.items = body['items_list'];
                        this.regenerate_items(body['items_list']);
                    }
                    
				
		        }).catch((e) => {
		  			console.log("Error getting ExampleAddon1 init data: ", e);
		        });	

			}
			catch(e){
				console.log("Error in API call to init: ", e);
			}
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
                
                let list_el = document.getElementById('extension-example-addon1-main-items-list'); // list element
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
				const original = document.getElementById('extension-example-addon1-original-item');
			    //console.log("original: ", original);
                
			    // Since each item has a name, here we're sorting the list based on that name first
				items.sort((a, b) => (a.name.toLowerCase() > b.name.toLowerCase()) ? 1 : -1)
				
                
				// Loop over all items in the list to create HTML for each item. 
                // This is done by cloning an existing hidden HTML element, updating some of its values, and then appending it to the list element
				for( var item in items ){
					
					var clone = original.cloneNode(true); // Clone the original item
					clone.removeAttribute('id'); // Remove the ID from the clone
                    
                    // Place the name in the clone
                    clone.querySelector(".extension-example-addon1-item-name").innerText = items[item].name; // The original and its clones use classnames to avoid having the same ID twice
                    clone.getElementsByClassName("extension-example-addon1-item-value")[0].innerText = items[item].value; // another way to do the exact same thing - select the element by its class name
                     
                    
                    // You could add a specific CSS class to an element depending, for example depending on some value
                    //clone.classList.add('extension-example-addon1-item-highlighted');   
                    

					// ADD DELETE BUTTON
					const delete_button = clone.querySelectorAll('.extension-example-addon1-item-delete-button')[0];
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
                                    
                                    event.target.closest(".extension-example-addon1-item").style.display = 'none'; // find the parent item
                                    // Remove the item form the list, or regenerate the entire list instead
                                    // parent4.removeChild(parent3);
                                }

    						}).catch((e) => {
    							console.log("example-addon1: error in delete items handler: ", e);
    						});
                        }
				  	});

                    // Add the clone to the list container
					list_el.append(clone);
                    
                    
                    
				} // end of for loop
                
            
            
			}
			catch (e) {
				console.log("Error in regenerate_items: ", e);
			}
		}
	
 
    
    }

	new ExampleAddon1();
	
})();


