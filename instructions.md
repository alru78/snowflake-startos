# Snowflake

## Documentation

- [Snowflake](https://snowflake.torproject.org/) — the Tor Project's page on what Snowflake is and who it helps.
- [Running a Snowflake proxy](https://community.torproject.org/relay/setup/snowflake/) — the Tor Project's guide for proxy operators.

## What you get on StartOS

A Snowflake proxy that starts relaying for censored Tor users the moment the service is running, and a **Dashboard** interface showing what it has done: the NAT type it detected and how long the proxy has been up, bandwidth relayed in the last 24 hours, the last 7 days and all-time with the daily average (each split into down and up), an hour-by-hour chart of the last day, and a weekday-by-hour heatmap of when your proxy is busiest.

There is nothing to configure and no account to make. The proxy never learns what anyone is browsing, and the traffic it carries leaves the Tor network from a Tor bridge — not from your address. Forwarding a port range on your router (see NAT type below) is optional and only improves how many clients the proxy can help; the service runs and relays clients without it.

## Getting set up

1. Start the service.
2. Open the **Dashboard** from the Dashboard tab.

The NAT type appears a minute or so after each start. Bandwidth and connection figures are added once an hour, so the first ones show up after the first full hour; the page refreshes itself every five minutes.

## Using Snowflake

### NAT type

**unrestricted** means clients behind strict NATs can reach your proxy, which is the most useful kind of proxy to run. **restricted** means only clients with permissive NATs can; the proxy still helps, just fewer people.

To turn a restricted proxy into an unrestricted one, open this service's **Proxy Relay Ports** interface and enable the public IP address of the gateway this server's internet traffic leaves through. If that gateway is your router, forward UDP 30000–30249 to this server there. Then restart the service; the NAT Type tile should read **unrestricted** a minute or so later.

### Reading the figures

Everything on the dashboard comes from the proxy's own hourly summaries, so a figure is up to an hour behind and "0 connections" in the first hour is normal. The history lives on this server and survives restarts and updates.

The 24-hour and 7-day figures are rolling windows ending now, and the arrow next to each compares it with the window before; it appears once the history covers both. The heatmap shows the average traffic for each hour of each weekday, in UTC; empty cells are hours with no data yet. The status line at the top shows the NAT type and live uptime, and turns amber if no hourly summary has arrived for two hours.
