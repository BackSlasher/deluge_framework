#!/usr/bin/python

###############
# By: Nitzan (http://OneBoredAdmin.com)
# The interesting code is at the bottom
# call filter_torrents from your code like this:
## from deluge_framework import filter_torrents
## filter_torrents(connection_data,torrent_info_wanted,action,interactive)
# see bottom of script for details

from deluge.log import LOG as log
from deluge.ui.client import client
import deluge.component as component
from twisted.internet import reactor, defer
import time

def printSuccess(dresult, is_success, smsg):
    global is_interactive
    if is_interactive:
        if is_success:
            print "[+]", smsg
        else:
            print "[i]", smsg

def printError(emsg):
    global is_interactive
    if is_interactive:
        print "[e]", emsg

def endSession(esresult):
    if esresult:
        print esresult
        reactor.stop()
    else:
        client.disconnect()
        printSuccess(None, False, "Client disconnected.")
        reactor.stop()

def printReport(rresult):
    
    printSuccess(None, True, "Finished")
    endSession(None)

def on_torrents_status(torrents):
    tlist=[]
    for torrent_id,torrent_info in torrents.items():
        try:
            res = torrentAction(torrent_id,torrent_info)
            if res == 'd':
                successmsg = "%s [%s]: Deleted without data" % (torrent_id, torrent_info['name'])
                errormsg = "%s [%s]: Error deleting without data" % (torrent_id, torrent_info["name"])
                tlist.append(client.core.remove_torrent(torrent_id, False).addCallbacks(printSuccess, printError, callbackArgs = (True, successmsg), errbackArgs = (errormsg)))
            elif res == 'D':
                successmsg = "%s [%s]: Deleted WITH DATA" % (torrent_id, torrent_info['name'])
                errormsg = "%s [%s]: Error deleting WITH DATA" % (torrent_id, torrent_info["name"])
                tlist.append(client.core.remove_torrent(torrent_id, True).addCallbacks(printSuccess, printError, callbackArgs = (True, successmsg), errbackArgs = (errormsg)))
            elif res == 'l':
                printSuccess(None, False, "%s [%s]: Listing (doing nothing)" % (torrent_id, torrent_info["name"]))
            elif res == '':
                pass
            else:
                printError("%s [%s]: Unknown function response '%s'" % (torrent_id, torrent_info["name"],res))
        except Exception as inst:
            printError("%s [%s]: Exception %s" % (torrent_id, torrent_info["name"], inst))
    defer.DeferredList(tlist).addCallback(printReport)

def on_session_state(result):
    client.core.get_torrents_status({"id": result}, torrent_info_wanted).addCallback(on_torrents_status)

def on_connect_success(result):
    printSuccess(None, True, "Connection was successful!")
    client.core.get_session_state().addCallback(on_session_state)

def filter_torrents(connection_data={},info_wanted=[],action=(lambda tid,tinfo: 'l'),interactive=True):
    """ Get all torrents and filter them
    Arguments:
    connection_data -- How to connect to the deluged daemon. Specify a dictionary of host, port(integer), username, password
    info_wanted -- A list of fields to be retrived for each torrent. You'll get it as a populated dictionary when action is called
    action -- function called for each torrent. Will get two variables - the torrent id and a populated dictionary of the torrent data. Should return a string indicating what to do with the torrent. Possible values:
        '':  Do nothing
        'd': Delete torrent (without deleting data)
        'D': Delete torrent WITH data
        'l': List torrent (display id and name)
        (Anything else): Causes an error.
        More things to come!
    interactive -- whether to write information / errors to output. Send False for cron jobs
    """
    # ensure 'name' is in torrent_info_wanted
    if 'name' not in info_wanted: info_wanted.append('name')
    # set parameters
    global cliconnect
    cliconnect = client.connect(**connection_data)
    global torrent_info_wanted
    torrent_info_wanted = info_wanted
    global torrentAction
    torrentAction = action
    global is_interactive
    is_interactive = interactive
    # start the show
    cliconnect.addCallbacks(on_connect_success, endSession, errbackArgs=("Connection failed: check settings and try again."))
    reactor.run()
