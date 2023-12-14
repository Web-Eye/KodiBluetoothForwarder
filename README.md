# Kodi Bluetooth Forwarder
## Overview
This little app receives bluetooth keystrokes from every bluetooth remote and send customate keys, actions to 
[Kodi](https://kodi.tv/).
## Intention
I loved to use Kodi with single board computers (like Raspberry Pi, or Odroid devices) for several years. From 
the very beginning via OpenElec, LibreElec and finally CoreElec. So, I used to control Kodi with an IR-Remote, 
also to power on/off these devices.   
  
My last device was an Odroid H3+, a little bit greater than a single board device, but sadly without the 
opportunity to power on/off this machine. I didn't want to miss this, especially with the properties of a Harmony 
remote, so the laziness wins and results in this little app....
## Method
Instead of sending the bluetooth signals directly the final device, they will be catched from another device any 
Linux-based 24/7 machine on which this app runs.  
This app catches these signals, mapped them to other commands like keystrokes or actions, which can be sent over 
local lan to Kodi's event server or maybe the JSONRPC API. Turning on the machine is solved via a WOL magic packet, 
turning off also via JSONRPC or even ssh login.
## Prerequisites
- A Linux machine which runs 24/7 or even during you run Kodi
- A Bluetooth adapter/dongle which is set up sucessfully on this machine with bluetooth daemon, BlueZ package.
- A Bluetooth remote/keyboard which is sucessful paired and trusted by this bluetooth adapter.
- The Kodi device must be prepared to handle WOL magic packets to power on this machine.
## Setup
...still to do
