# Example addon

An add-on example for the Candle Controller (and Webthings Gateway), intended to help people get started with addon development in Python. The idea is that you can see how everything works, and remove what you don't need.

The Controller normally starts by validating the manifest.json files. For example, the directory name and addon ID should be the same. It also makes sure that the checksums of all the files match. You can get the controller to skip this validation by creating a directory called ".git" in the addon's folder. This is useful for development.

If everything seems valid it will start the addon by calling the command mentioned in the manifest file, in this case "python3 main.py". Then main.py in turns loads in example-addon1.py from the pkg directory. The file(s) in pkg will have the real meat and potatoes of what your addon does.

There are a number of functionalities your addon can provide.

1.
If you want your addon to bring new things to the controller, then you will want to create an "adapter". This is the default in this example - example-addon1.py is an adapter.
Adapters create "things". Even if your addon won't connect to actual things, making things is still useful because it's the best way for making rules to control with your addon. Rules can manipulate things, and thus manipulate your addon.

2.
You may also want to add a new page to the controller's interface. That is done by creating an "extension". Extensions require you to have two parts:
- The part that loads in the UI: a HTML file (view), a javascript file, a CSS file, and an SVG icon.
- The backend part. This provides the addon's API which the javascript can then talk to. This is taken care of by an "API Handler", which in this example is loaded in

3.
There is a rare third type, the "notifier". This is used to create an addon that sends notifications from the rules interface. Take a look at the Voco addon, which also adds two notifiers.

This example is a hybrid of both an adapter and an API handler, with the adapter being the "primary" type. But an addon doesn't need to add things, it could just as well be a pure API handler, or a pure adapter. Most addons are currently pure adapters.



## What are all these files for?

- manifest.json describes the basic details of your addon to the controller. The controller also checks that things match. For example, the directory name and addon ID must be the same.
- package.sh will turn your code into a tar archive, which is what users download to their device when they installl an addon. The controller also detects any errors in the download process using the SHA checksum files.
- SHA256SUMS. These provides a checksum for each file in the addon. If the controller detects that the checksum for any file no longer match, the addon will not be started. Think of it as a security feature to avoid manipulation.
- LICENSE describes which (open source) license the addon is made available under.
- requirements.txt contains a list of Python dependencies for your addon. The package.sh script will download and place these dependencies in the lib directory.
- .github/workflows/release.yml is a file that can be used to automate creation of the addon by Github. If you upload your addon to github, whenever you create a new release, this will generate two new files: a .tar file and a checksum file. These are required to get your addon into the app store (details below).
- optional build.sh is a file that is part of the Github release process. It creates a virtual machine that emulates a Raspberry Pi, and in turns calls package.sh. This is needed if you are using python libraries that need this emulation. This simple example doesn't currently use this method.


## Getting started

First we'll have to get your Candle controller into a more developer friendly stance. Note that this will remove some security protections, so it's recommended to do development on a second device.

We'll need to disable the read only mode of the main partition first.
- Enable developer mode in the Candle store addon's settings.
- Go into settings -> developer, and enable SSH
- You can now log into the Candle controller with SSH: `ssh pi@candle.local`. The password is "smarthome".

We'll create a file on the SD card that will disable read-only mode:
```
sudo touch /boot/candle_rw_keep.txt`
```

Reboot:
```
sudo reboot
```

Now you'll have to go into settings again, enable SSH again, and log into SSH again. Since we disabled read-only mode, SSH will stay enabled from now on.

You can install Samba on Raspberry Pi to more easily work on the addon. That way the files of the controller will show up as a network drive. This command will do this automatically for you:
```
sudo chmod +x /home/pi/candle/install_samba.sh && sudo /home/pi/candle/install_samba.sh
```
(You can also use SFTP instead of Samba)

Next we'll download the example addon onto the system. Using SSH, navigate to the addons directory:
`cd /home/pi/.webthings/addons`

Clone the example addon into the addons directory:
`git clone https://github.com/createcandle/example-addon1.git`

We need to quickly restart the controller to get it to detect the new addon. A fast way to do this without rebooting is:
`sudo systemctl restart webthings-gateway.service`

The addon should now appear in the installed addons list. Enable it, and refresh the browser. You should now see the example addon in the main menu.


## Starting actual development.

After taking a look around and reading all the documentation, the first thing you'll want to do it change the addon's name. This has to be done in a number of places. A good name is short, lowercase and uses dashes between words. For example "internet-radio" is valid.
- change the directory name to the addon id
- change the addon ID and other details in the manifest.json file
- Do an exact search-and-replace "example-addon1" with your addon ID in the other files (python, javascript, CSS and html).
- Do an exact search-and-replace "example_addon1" with your addon ID in the other files (python, javascript, CSS and html), but with the same lower dash.
- Do an exact search-and-replace "ExampleAddon1" with your addon ID in camel case in the python and javascript files.
- Change the addon ID in the .github/workflows file, package.sh and (optional) build.sh
- If it doesn't exist yet: make a folder called ".git" inside the addon directory. Whenever the controller detects a .git folder inside the addon directory, it will skip the checksum security feature.

To test if everything went well, try running the addon manually with:

`python3 main.py`

If you are working on an addon with a UI, then you will want to start the addon through the controller's normal web interface. In that case you can check its debug output with this command:

`tail -f -n100 ~/.webthings/log/run-app.log`





## A closer look at manifest.json

- You can change "primary type" to "extension" or "notifier" if you prefer. It's used to show a different icon.
- The order of information in the manifest.json file matters. The order of the settings in the "properties" part of the "schema" part determines in which order the settings are displayed.
- Required settings must be filled by the user before then are allowed to save the settings. Some parameters such as checkbox or slider always have a value, so adding them to the list of required settings doesn't make much sense.
- The short name should be short yet unique. Preferably on word. This part isn't really used anywhere.. yet.



## A closer look at the python structure

The addon must follow a structure. Expecially adapters have multiple "layers":
- Adapter
- - Devices
- - - Properties

So an adapter can create multiple devices, which it then offers to the controller. Users can then accept these devices by clicking on (+) on the things overview page.
Each device can have one or more properties (booleans switches, values).

For example, the Network Presence Detection addon does a scan for devices on the network, and then create a new Device for each devices that it discovers. Each device has certain properties (IP address, etc).

You could say that the addon communicates with the controller through a hidden parent layer at the very top, the manager_proxy. This handles communication between the addon and the controller in the background. The Adapter, Devices and Property layer have methods to communicate with the Proxy when something (such as the value of a propery or the detection of a new device) has changed.
If you're curious about all the available methods, have a look here: https://github.com/WebThingsIO/gateway-addon-python

This layer also calls methods in the addon. For example:
- when the user click on the (+) on the things overview, it calls the "start pairing" method on the adapter. That way your adapter can react to this event, for example by doing a quick scan for devices. This pairing window lasts 60 seconds or until the user cancels it, at which point "cancle pairing" is called.
- when the addon is stopped ( on a reboot or shutdown, or manually or on an update) the "unload" method is called. This allows you to do some quick cleanup and maybe store some data. Please don't take longer than a second to do all this.

The addon is "the single point of truth" for its devices. After a reboot the controller will have forgetten the latest values of all devices and properties, so your addon should ideally keep track of the latest values of properties, and quickly recreate the devices and properties whenever the addon is started. That's what the "persistent data" parts are useful for.


## Giving an addon settings

There are two ways to give an addon settings. 

The basic one is to provide options in the manifest.json file. The controller will then create a basic settings interface for you. These values can be loaded by the addon whenever it starts. This does have some limitations. Firstly, from the perspective of your addon these are read-only; your addon is not supposed to change these settings, only let the user do this. And if the user changes these settings the addon is completely restarted. Also... in rare occasions loading these settings can fail. 

That's why its useful to also store settings in an addon's own persistent data store, and make that the main "point of truth" for your addon. What's more, you could offer a settings interface in the UI. That way the addon does not need to be restarted every time a setting changes, and you can offer more complex (and nicer looking) settings.

Addons have a "data" folder where they are allowed to store any data they want, so this is the best place to store the persistent data (json) file too.


## Getting your addon into the Candle app store

This part is still under construction and more will be added soon.

Generally there are two steps: 
1. get your addon onto Github and generate your first official release
2. get our first release accepted into an addons list. (There are two addons lists: Webthings and Candle)

Getting your addon onto Github will require a little knowledge of how Github works.
- Upload your code to Github. The `package.sh` and (optional) `build.sh` file will need to have execution permission.
- The github/workflow/release.yml file will need to reflect if you're using the simple package.sh only approach or the build.sh + package.sh approach.
- On Github create an initial release for your addon. This will start the Github action described in the workflow file. After waiting a minute or a few hours - depending on the complexity of your addon - you will have extra files on your release page.

These files will be something like you see here: https://github.com/createcandle/power-settings/releases (random example)

- your-addon-name-0.0.1.tgz
- your-addon-name-0.0.1.tgz.sha256sum
- Source code (zip)
- Source code (tar.gz)


Now you can propose your own entry in one of the addon lists. You might want to try and get your addon accepted by the Webthings Gateway project (which Candle builds on) first. That way more people will be able to enjoy your work, and if it gets accepted there it will also show up in the Candle app store.
https://github.com/WebThingsIO/addon-list

If your addon is "too wild" for the Webthings community, then you can try getting it into the Candle list:
https://github.com/createcandle/addons-list

Either way you'll need to provide:
- The download URL of your tgz file. The .tgz file is what gets downloaded onto a user's system and extracted into the addon directory.
- A checksum for that file. Download the .tgz.sha256sum file and you will find the checksum value inside - a long string of seemingly random letters and number.



## More examples

For a very simple real-world example or a pure extension, have a look at the Welcome addon. It communicates with the backend to store a single setting.

For a more complex addon, take a look at the Web Interface addon. It has tabs, and hooks into the javascript API inside the web browser.

For a complex kitchen-sink addon, have a look at Voco. It's an adapter, API handler and notifier, all in one.


## Troubleshooting

- The package.sh and build.sh file need to have an execute permission on github. Unfortunately giving them that permission cannot be done through the web interface, so if you want your addon available to other you will have to learn a little about github.
- Can't save a change in your file? It might be a permissions issue. A very bad way to fix this issue would be to use: `sudo chmod -R 777 ./` inside your addon's directory...
- Addding "developer.txt" to /boot might give you more debug output. Use this command to generate that file: `sudo touch /boot/developer.txt`


## Tips

- If you're working on an addon with a UI, it might get annoying to start and stop the addon each time you want to make a change to the backend. You can open the addon in one browser tab, then open another browser tab in which you disable the addon. Then start the addon from SSH with `python3 main.py`. The first tab's UI will be able to communicate with the backend that you just started.
- You may enjoy the Seashell addon, which lets you run shell commands from the user interface.


