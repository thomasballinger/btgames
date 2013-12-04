Bittorrent Games
----------------

Create trackers, peers, and run your own bittorrent client on an Amazon EC2 instance.

You'll need your AWS credentials in environmental variables
`AMAZON_ACCESS_KEY` and `AMAZON_SECRET_KEY`
to run the fabric scripts.

Remember to turn off your instances when you're done!


To Run:


Write a python module that provies three functions: install, torretfile, and download. See tom.py as an example.

To debug your install script, try:

`fab newInstance`

`fab install:<yourModuleNameHere> -H <hostname from prev command> -i <key filename from prev command>

To set up a scenario:

`fab installScenario1:tom`

`fab runScenario1:<username>,test.torrent -H <hostname from prev command> -i <key filename from prev command>

Try fab install
