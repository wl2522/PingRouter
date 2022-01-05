
# PingRouter

I created this script in order to detect if and when a wireless router on my local network (an old Linksys E3200 router) goes down. This router currently serves as a wireless repeater bridge (running on DD-WRT firmware using this [setup](https://www.youtube.com/watch?v=oJaYE9Yk7gc&list=WL&index=3)) for a PlayStation 3 that's no longer able to connect to a wireless network on its own (presumably due to a malfunctioning wireless card) and which is too far away to be directly plugged into my main router.

Despite daily scheduled reboots, the E3200 router occasionally becomes unreachable, preventing the PS3 from connecting to my home wireless network. Correcting this issue usually involves power cycling the router. However,  sometimes this is not enough and I must perform a factory reset on the router followed by reconfiguring the settings in DD-WRT.

Even though I currently don't know of a way to prevent this issue from happening, it would be better if I knew if the router went offline ahead of time rather than when I turn on my PS3. Therefore, I've scheduled this script to run every 5 minutes, performing the following steps:

1. Read the last recorded line in an existing log file (or create a new log file if one doesn't exist)
2. Parse the previous outcome (if available) and calculate the time that has passed since that previous outcome was recorded
3. Ping the router and log the outcome (either the HTTP status code that was returned or the fact that the router was offline)
4. Either update the total time that the router has maintained the same status (a particular HTTP status code or being offline) or reset the the total time if the router's status has now changed
5. Send a notification through a Slack API webhook if the router status has changed or if the router has continued to be offline (limited to one notification per day)
