GingerBase Project - HostStats Configuration
============================================

One of the main features of GingerBase is the Host Statistics (HostStats)
visualization. This feature is responsible to collect and show on UI the data
for CPU, memory, network and disk usage on host system. A history of the last
60 seconds of statistics is cached and the UI is capable to show this
information when Dashboard screen of the Host tab is selected.

To create this history, it's possible that Wok consumes about 1% of host's CPU
when in idle mode, due the background task executed every second to collect and
cache the host statistics. This CPU consumption can be reduced by turning off
the host statistics history, making Wok only collect host's data when Dashboard
screen of the Host tab is accessed.

By default the cache of host statistics history is enabled. To disable it, do
the following:

 * Edit the /etc/wok/plugins.d/gingerbase.conf file and change the value of
**statshistory_on** to False:

```
   statshistory_on = False
```

  * Then (re)start Wok service:

```
   sudo systemctl start wokd.service
```

The Wok server will not cache host statistics history and the graphics of the
Dashboard screen will show data since the moment this screen is accessed.

Enjoy!
