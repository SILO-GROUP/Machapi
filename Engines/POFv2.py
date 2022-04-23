import requests
import configparser
from collections import OrderedDict
import json
# import pprint


class User():
    def __init__( self, obj, session ):
        self.details = obj
        self.session = session

    def send_message( self, message ):
        self.session.send_message( self.details, message )


class Session:
    # Exception type for various session errors.
    class POFSessionError(Exception):
        def __init__(self, value):
            self.value = value

    # Initializer for the POFSession class
    def __init__(self, config):
        self.my_user = None

        self.config = config

        # handle to use for getting new pages with existing POF session
        self.client = requests.Session()

        # Use the user-configured useragent string
        self.client.headers.update(
            {
                'User-Agent': self.config.useragent
            }
        )

        # rudimentary proxy support:
        if self.config.proxy_enabled:
            proxies = { 'http', self.config.proxy }
            self.client.proxies.update( proxies )

    class Config():
        def __init__( self, config_file ):
            settings = configparser.ConfigParser( allow_no_value=True )
            settings.read( config_file )

            self.useragent = settings.get( "general-client", "user_agent" )

            self.username = settings.get("pof-session", "username")
            self.password = settings.get("pof-session", "password")

            self.gender = settings.get("pof-search", "gender")
            self.min_age = settings.get("pof-search", "min_age")
            self.max_age = settings.get("pof-search", "max_age")
            self.zipcode = settings.get("pof-search", "zipcode")
            self.interests = settings.get("pof-search", "interests")
            self.target_gender= settings.get("pof-search", "target_gender")
            self.country = settings.get("pof-search", "country")
            self.min_height = settings.get("pof-search", "min_height")
            self.max_height = settings.get("pof-search", "max_height")
            self.maritalstatus = settings.get("pof-search", "marital_status")
            self.relationshipage_id = settings.get("pof-search", "relationshipage_id")
            self.wants_children = settings.get("pof-search", "wants_children")
            self.smokes = settings.get("pof-search", "smokes")
            self.drugs = settings.get("pof-search", "does_drugs")
            self.body_type = settings.get("pof-search", "body_type")
            self.smarts = settings.get("pof-search", "smarts")
            self.has_pets = settings.get("pof-search", "has_pets")
            self.eye_color = settings.get("pof-search", "eye_color")
            self.income = settings.get("pof-search", "income")
            self.profession = settings.get("pof-search", "profession")
            self.hair_color = settings.get("pof-search", "hair_color")
            self.religion = settings.get("pof-search", "religion")
            self.drinks = settings.get("pof-search", "drinks")
            self.has_children = settings.get("pof-search", "has_children")
            self.max_distance = settings.get("pof-search", "max_distance")

            self.proxy_enabled = settings.getboolean("proxy", "enabled")

            if self.proxy_enabled:
                self.proxy = settings.get("proxy", "proxy")

    # Log in to POF.com
    def login(self):
        # Can also get this from the response Set-Cookie header as
        form_url = 'https://www.pof.com/login/'
        session_endpoint = 'https://login.pof.com/'

        self.client.headers.update(
            {
                'Host': 'www.pof.com',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': 'https://www.pof.com/',
            }
        )
        try:
            url_form_get_response = self.client.get( form_url )

        except requests.exceptions.ConnectionError:
            raise Session.POFSessionError( "Could not reach %s" % form_url )

        # installID for session stuff
        installid = self.client.cookies.get_dict()['installid']

        # not needed, handled by requests client
        # exp = self.client.cookies.get_dict()['exp']

        session_endpoint_data = OrderedDict( {
            'installId': installid,
            'password': self.config.password,
            'rememberMe': 'false',
            'useTokenPair': 'true',
            'username': self.config.username
        } )

        try:
            self.client.headers = {}
            self.client.headers.update(
                {
                    'Host': 'login.pof.com',
                    'User-Agent': self.config.useragent,
                    'Accept': 'application/json',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Origin': 'https://www.pof.com',
                    'Connection': 'keep-alive',
                    'Referer': 'https://www.pof.com'
                }
            )
            session_endpoint_post_response = self.client.post(
                session_endpoint,
                data=session_endpoint_data,
                allow_redirects=True
            )

        except requests.exceptions.ConnectionError:
            raise Session.POFSessionError( "Could not reach %s" % session_endpoint )

        if session_endpoint_post_response.status_code != 200:
            raise Session.POFSessionError( "Failed to establish a session." )

        print("Established a session.  Getting user info...")

        try:
            my_user_info_url = 'https://www.pof.com/apiv1/Account/Me'
            self.client.headers = {}
            self.client.headers.update(
                {
                    'Host': 'www.pof.com',
                    'User-Agent': self.config.useragent,
                    'Accept': 'application/json',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Content-Type': 'application/json',
                    'Origin': 'https://www.pof.com',
                    'Connection': 'keep-alive',
                    'Referer': 'https://www.pof.com/login'
                }
            )

            my_user_info_post_data = {
                'FetchHighlight': True
            }
            my_user_info_payload_obj = json.dumps( my_user_info_post_data )

            my_user_info_url_response = self.client.post(
                my_user_info_url,
                data=my_user_info_payload_obj,
                allow_redirects=True
            )

        except requests.exceptions.ConnectionError:
            raise Session.POFSessionError( "Could not reach %s" % my_user_info_url )

        if my_user_info_url_response.status_code != 200:
            raise Session.POFSessionError( "{0} response calling {1}.".format(
                my_user_info_url_response.status_code,
                my_user_info_url
            ) )

        parsed = json.loads( my_user_info_url_response.text )
        self.my_user = parsed

        # pretty print cookies and response headers for debug
        # pprint.pprint( self.client.cookies.get_dict() )
        # pprint.pprint( session_endpoint_post_response.headers )

        # auth token grab for debug
        # auth = self.client.cookies.get_dict()['access']
        # refresh = self.client.cookies.get_dict()['refresh']
        # access value in cookies here becomes Access header value

    # retrieves the sent messages
    def get_sent_messages(self):
        try:
            history_url = 'https://www.pof.com/apiv1/Conversations/SentMessages?messageId=-1&pageSize=10'
            self.client.headers = {}
            self.client.headers.update(
                {
                    'Host': 'www.pof.com',
                    'User-Agent': self.config.useragent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            )

            sent_messages_result = self.client.get( history_url, allow_redirects=True )

        except requests.exceptions.ConnectionError:
            raise Session.POFSessionError("Could not reach %s" % form_url)

        if sent_messages_result.status_code != 200:
            raise Session.POFSessionError("Failed to fetch sent messages")

        parsed = json.loads( sent_messages_result.text )
        print( json.dumps( parsed, indent=4, sort_keys=True ))

    def search(self):
        try:
            search_url = 'https://www.pof.com/apiv1/ProfileList/AdvancedSearch'
            self.client.headers = {}
            self.client.headers.update(
                {
                    'Host': 'www.pof.com',
                    'User-Agent': self.config.useragent,
                    'Accept': 'application/json',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Content-Type': 'application/json',
                    'Origin': 'https://www.pof.com',
                    'Referer': 'https://www.pof.com/search'
                }
            )

            if self.config.target_gender == 'm':
                target_gender = 0
            else:
                target_gender = 1

            search_criteria = OrderedDict( {
                "useSavedSearch": False,
                "country": self.config.country,
                "imageSetting": 1,
                "maxAge": self.config.max_age,
                "maxHeight": self.config.max_height,
                "minAge": self.config.min_age,
                "searchDistance": self.config.max_distance,
                "seekingGender": target_gender,
                "seekingGenders": [
                    target_gender
                ],
                "sortOrder": 0,
                "zipCode": self.config.zipcode,
                "minHeight": self.config.min_height,
                "pageId": 0,
                "pageSize": 500,
                "pageSource": "https://www.pof.com/search",
                "deviceLocale": "en-US",
                "topSize": 500
            } )

            search_criteria_obj = json.dumps( search_criteria )
            search_submit_result = self.client.post( search_url, allow_redirects=True, data=search_criteria_obj )

        except requests.exceptions.ConnectionError:
            raise Session.POFSessionError("Could not reach %s" % form_url)

        if search_submit_result.status_code != 200:
            raise Session.POFSessionError("Failed to fetch sent messages")

        search_criteria_obj = json.loads( search_submit_result.text )

        # since they don't use a consistent user object model, in order
        # to simplify how we work with the data, we need to use the search results
        # to repopulate a user object list in a unified format.

        for user in search_criteria_obj['users']:
            print("Fetching details on user '{0}'".format( user['profileId']))
            user_obj = self.get_user(user['profileId'])
            yield user_obj



    def get_user( self, profile_id ):
        try:
            profile_api_url = 'https://www.pof.com/apiv1/Profile/{0}'.format( profile_id )
            self.client.headers = {}
            self.client.headers.update(
                {
                    'Host': 'www.pof.com',
                    'User-Agent': self.config.useragent,
                    'Accept': 'application/json',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Referer': 'Referer: https://www.pof.com/viewprofile?profileId={0}'.format( profile_id )
                }
            )

            sent_messages_result = self.client.get( profile_api_url, allow_redirects=True )

        except requests.exceptions.ConnectionError:
            raise Session.POFSessionError( "Could not reach %s" % profile_api_url )

        if sent_messages_result.status_code != 200:
            raise Session.POFSessionError( "Failed to fetch user." )

        parsed = json.loads( sent_messages_result.text )

        # hehe fixing their broken object model
        parsed['profileId'] = profile_id

        return User( parsed, self )

    # meant to be used internally
    # gets the `userId_enc` field from a user object
    def send_message( self, details, message ):
        profile_id = details['profileId']
        user_id_enc = details['userId_enc']
        username = details['username']

        try:
            send_message_api_url = 'https://www.pof.com/apiv1/Conversations/SendMessage'
            self.client.headers = {}
            self.client.headers.update(
                {
                    'Host': 'www.pof.com',
                    'User-Agent': self.config.useragent,
                    'Accept': 'application/json',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Content-Type': 'application/json',
                    'Referer': 'https://www.pof.com/viewprofile?profileId={0}'.format( profile_id )
                }
            )

            # introduces requirement to check username from session
            payload = OrderedDict(
                {
                    'IsPriority': False,
                    'MyUserName': self.my_user['user']['username'],
                    'SourceString': 'https://www.pof.com/abandon',
                    'Text': message,
                    'UnlockMediaSupported': True,
                    'UserId_enc': user_id_enc,
                    'UserName': username
                }
            )
            obj_payload = json.dumps( payload )
            sent_messages_result = self.client.post( send_message_api_url, data=obj_payload, allow_redirects=True )

        except requests.exceptions.ConnectionError:
            raise Session.POFSessionError( "Could not reach %s" % send_message_api_url )

        if sent_messages_result.status_code == 429:
            raise Session.POFSessionError("Hit the rate limit.  Slow down.")

        if sent_messages_result.status_code != 200:
            raise Session.POFSessionError( "{0} response calling {1}".format(
                sent_messages_result.status_code,
                send_message_api_url
            ) )

        response_obj = json.loads( sent_messages_result.text )

        if response_obj['success'] != True:
            raise Session.POFSessionError( "Could not send message." )

        print( "Message sent to user '{0}'.  {1} messages remaining in quota.".format(
            profile_id,
            response_obj['userFirstContactsCapStatus']['remainingAllowedCount']
        ) )

        parsed = json.loads( sent_messages_result.text )
        return User( parsed, self )
