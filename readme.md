Bittorrent Games
----------------

Create trackers, peers, and run your own bittorrent client on an Amazon EC2 instance.

You'll need your AWS credentials in environmental variables
`AMAZON_ACCESS_KEY` and `AMAZON_SECRET_KEY`
to run the fabric scripts.

If you don't have such a pair yet, you'll need to create one on the AWS Security Credentials page.

You also need to

`pip install fabric boto`

Remember to turn off your instances when you're done!


Contest Rules
-------------

* Use the "real" output time for the unix `time` command, or the larger fabric time, output when the fab command finishes.
* Run your bittorrent client at least twice, and as many times more as you want.

Instructions
------------

It's your job to write a python module provides three functions: install, torrentfile, and download. See tom.py as an example, and add your to the repository for more examples, and so others can test your client on their own scenario.

To debug your install script, try:

`fab use_new_instance:testing ssh`

and try to install your bittorrent client on that machine.
Keep track of all the commands you use, and write a script similar to tom.py. Terminate that instance,

`fab instance:testing terminate`

then try out your install script for real:

`fab use_new_instance:client install:tom` but replace "tom" with your custom module

Once you've got a working install script, spin up a tracker and a peer:

`fab use_new_instance:tracker install_tracker & fab use_new_instance:peer install_deluge`

Next you should start the tracker,

`fab instance:tracker start_tracker`

take a moment to reflect on the three instances you're running,

`fab list`

and seed a file:

`wget https://dl.dropboxusercontent.com/u/42074050/1999-12-31%2018.20.09.jpg cabin.jpg`

`fab instance:peer seed_file:cabin.jpg`

That command should leave a torrent file called `test.torrent` on your local computer;
you can test it by running your bittorrent client there if you want, or go straight to
running it on the instance you installed it on:

`fab instance:client download:tom,test.torrent`

Try it a few times, add your time to this readme, and try some larger files!

Notes
-----

You can still use these `fab` commands with a `-H ubuntu@hostname -i keyname`,
you just don't have to if you include `instance:instanceName` before the command you want.


Results:
========

Tom's bittorrent client: https://github.com/thomasballinger/bittorrent

One Tracker, One Peer, Default Deluge Upload Limit
--------------------------------------------------

Small File (2MB, https://dl.dropboxusercontent.com/u/42074050/1999-12-31%2018.20.09.jpg)

* Tom: 4.8, 2.2, 2.4, 2.15, 2.18
* Stacey (Non-Twisted): 0.71 0.63 0.735 0.63  avg: 0.68
* Stacey (Twisted): 0.95 1.07 1.02 0.98 avg: 1.01
* Jeff: 0.94, 0.95, 1.04
* Steve: 0.75, 0.78, 0.76
* Brian and Jari: 0.11, 0.11, 0.11, 0.11, 0.11

Medium File (28 MB, http://www.gutenberg.org/cache/epub/29765/pg29765.txt)

* Tom: 14.8, 14.9, 15.7
* Stacey (Non-Twisted: 6.08 5.69 7.36 5.77 avg: 6.22
* Stacey (Twisted): 6.77 8.53 9.0 6.60 avg: 7.73
* Jeff: 4.40, 4.20, 4.50
* Steve: 3.41, 3.37, 3.35
* Brian and Jari: 0.91, 0.91, 0.88, 0.91, 0.94

Large File (200MB, http://05d2db1380b6504cc981-8cbed8cf7e3a131cd8f1c3e383d10041.r93.cf2.rackcdn.com/pycon-us-2010/276_the-mighty-dictionary-55.m4v)

* Tom: 529 seconds
* Stacey (Non-Twisted): 56.0 57.01 58.16 59.62 avg: 57.7
* Stacey (Twisted): 64.69 67.02 66.31 65.08 avg: 65.53
* Jeff: 68.27, 68.40, 66.15
* Steve: 23.35, 23.26, 23.863
* Brian and Jari: 7.83, 7.03

Other Scenario Ideas:

* Multiple peers, one tracker, peers have limited upload bandwidth
* Multiple peers, one tracker, peers have different portions of the file
