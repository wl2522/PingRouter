# PingRouter

## Problem

I created this script in order to detect if and when a wireless router on my local network (an old Linksys E3200 router) goes down. This router currently serves as a wireless repeater bridge (running on DD-WRT firmware using this [setup](https://www.youtube.com/watch?v=oJaYE9Yk7gc&list=WL&index=3)) for a PlayStation 3 that's no longer able to connect to a wireless network on its own (presumably due to a malfunctioning wireless card) and which is too far away to be directly plugged into my main router.

Despite daily scheduled reboots, the E3200 router occasionally becomes unreachable, preventing the PS3 from connecting to my home wireless network. Correcting this issue usually involves power cycling the router. However,  sometimes this is not enough and I must perform a factory reset on the router followed by reconfiguring the settings in DD-WRT.

Even though I currently don't know of a way to prevent this issue from happening, it would be better if I knew if the router went offline ahead of time rather than when I turn on my PS3.

In addition, I would also like to detect if and when my main network router (a Synology RT2600ac router, which the Linksys E3200 is connected to) reboots on its own or becomes otherwise unreachable.

## Solution

To accomplish these goals, I've scheduled this script to run every 5 minutes, performing the following steps for both routers:

1. Read the last recorded line in an existing log file (or create a new log file if one doesn't exist)
2. Parse the previous outcome (if available) and calculate the time that has passed since that previous outcome was recorded
3. Ping the router and log the outcome (either the HTTP status code that was returned or the fact that the router was offline)
4. Either update the total time that the router has maintained the same status (a particular HTTP status code or being offline) or reset the the total time if the router's status has now changed
5. Send a notification through a Slack API webhook if the router status has changed or if the router has continued to be offline (limited to one notification per day)

## Routers with Self-Signed Certificates and HTTPS Requests

If the script is pinging a router that only accepts HTTPS connections and uses a self-signed certificate (such as with my Synology RT2600ac), then a `[SSL: CERTIFICATE_VERIFY_FAILED]` error may be raised.

One way to avoid this is to ping the router using `requests.get(verify=False)`. However, this is not recommended since it introduces security risks (see https://requests.readthedocs.io/en/stable/user/advanced/#ssl-cert-verification).

The safe way to resolve this issue is to [set up a DDNS hostname for the router](https://kb.synology.com/en-nz/SRM/help/SRM/NetworkCenter/internet_quickconnect_ddns?version=1_2#t2a) and [obtain a free third-party authorized certificate](https://kb.synology.com/en-us/SRM/help/SRM/ControlPanel/service_certificate?version=1_2#t2d) from [Let's Encrypt](https://letsencrypt.org/).  Then, the script should work when pinging the DDNS hostname rather than the router's local IP address.
