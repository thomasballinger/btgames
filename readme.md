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


To Run:


Write a python module that provies three functions: install, torretfile, and download. See tom.py as an example, and add your to the resitory for more examples.

To debug your install script, try:

`fab newInstance`

`fab install:yourModuleNameHere -H hostname from prev command -i key filename from prev command`

You can poke around your instance with

`ssh hostname from prev command -i key filename from prev command`



To set up a scenario:

`fab installScenario1:tom,big datafile to download`

Then run it with

`fab runScenario1:username,test.torrent -H hostname from prev command -i key filename from prev command

Change the datafile without reinstalling:

`fab seedFile:big datafile,announce url (printed at some point) -H seeding server hostname (printed at some point)`

Download one of the test files (see results section), upload it, and add your times!

If setting up an Amazon account is a burden, let me know and we can write your script together on my account.

Results:
========

Tom's bittorrent client: https://github.com/thomasballinger/bittorrent

One Tracker, One Peer, Default Deluge Upload Limit
--------------------------------------------------

Small File (2MB, https://dl.dropboxusercontent.com/u/42074050/1999-12-31%2018.20.09.jpg)

* Tom: 4.8, 2.2, 2.4, 2.15, 2.18

Medium File (28 MB, http://www.gutenberg.org/cache/epub/29765/pg29765.txt)

* Tom: 14.8, 14.9, 15.7

Large File (200MB, http://05d2db1380b6504cc981-8cbed8cf7e3a131cd8f1c3e383d10041.r93.cf2.rackcdn.com/pycon-us-2010/276_the-mighty-dictionary-55.m4v)

* Tom: 529 seconds

