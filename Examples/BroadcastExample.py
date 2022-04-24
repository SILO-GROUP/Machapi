#!/usr/bin/env python3

# ---------------
# Sample Script
# ---------------
# Do not run this.  This is an example script of what you can do with Machapi.
# This example connects, runs a search based on your config.ini settings, and then
# sends a message asking the list of people returned if they were born in the city they
# indicate is the city they are in.

import sys, json
# import pprint
sys.path.insert( 0, '..' )

# this will later be a session multiplexer object in a module abstraction library
from Engines.POFv2 import Session as POFSession


def Main():
    config = POFSession.Config( "config.ini" )

    session_controller = POFSession( config )
    session_controller.login()
    for returned_user in session_controller.search():
        # Send the user a message.
        returned_user.send_message(
            "so are you from {0} originally or did you move there?".format( returned_user.details['city'] )
        )

    # this call will fetch a user object in json format
    # user = testSession.get_user( profile_id )

    # this call will tell you about your own user.
    # pprint.pprint( testSession.my_user )


if __name__ == '__main__':
    Main()
