""" Simple Python class to access the Tesla JSON API
https://github.com/gglockner/teslajson

The Tesla JSON API is described at:
http://docs.timdorr.apiary.io/

Example:

import teslajson
c = teslajson.Connection('youremail', 'yourpassword')
v = c.vehicles[0]
v.wake_up()
v.data_request('charge_state')
v.command('charge_start')
"""

try:  # Python 3
    from urllib.parse import urlencode
    from urllib.request import Request, urlopen
except:  # Python 2
    from urllib import urlencode
    from urllib2 import Request, urlopen
import json
from retrying import retry

client_id = '81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384'
client_secret = 'c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3'
tesla_base_url = 'https://owner-api.teslamotors.com'


# returns a dict containing: access_token, refresh_token, tesla_token_grant_date, tesla_token_expiration_date
# make sure to save those values because the old tokens, etc become invalid after we succeed at this call!!!
@retry(stop_max_attempt_number=4, wait_exponential_multiplier=1000, wait_exponential_max=20000)
def rotate_tesla_token(email, refresh_token):
    data = {'refresh_token': refresh_token, 'client_secret': client_secret, 'grant_type': 'refresh_token',
            'email': email, 'client_id': client_id}
    return open(tesla_base_url, '/oauth/token', data=data)


def open(base_url, url, headers={}, data=None):
    """Raw urlopen command"""
    req = Request('%s%s' % (base_url, url), headers=headers)
    try:
        req.data = urlencode(data).encode('utf-8')  # Python 3
    except:
        try:
            req.add_data(urlencode(data))  # Python 2
        except:
            pass

    resp = urlopen(req)
    charset = resp.info().get('charset', 'utf-8')
    return json.loads(resp.read().decode(charset))


class Connection(object):
    """Connection to Tesla Motors API"""
    def __init__(self,
                    email='',
                    password='',
                    access_token='',
                    url=tesla_base_url,
                    api="/api/1/",
                    client_id=client_id,
                    client_secret=client_secret,
                    verbose_logging=False,
                    load_vehicles=True,
                    auth_dict=None):
        """Initialize connection object

        Sets the vehicles field, a list of Vehicle objects
        associated with your account

        Required parameters:
        email: your login for teslamotors.com
        password: your password for teslamotors.com

        Optional parameters:
        access_token: API access token
        url: base URL for the API
        api: API string
        client_id: API identifier
        client_secret: Secret API identifier
        verbose_logging
        """
        self.verbose_logging = verbose_logging
        self.base_url = url
        self.api = api
        self.auth_dict = auth_dict
        self.access_token = access_token

        # could have been passed a token as a part of an authorization dictionary
        if not self.access_token and self.auth_dict:
            self.access_token = self.auth_dict.get('access_token')

        # if at this point we still don't have an access token, we assume we've got a password
        if not self.access_token:
            oauth = {
                "grant_type": "password",
                "client_id": client_id,
                "client_secret": client_secret,
                "email": email,
                "password": password}
            self.auth_dict = open(self.base_url, "/oauth/token", data=oauth)
            self.access_token = self.auth_dict.get('access_token')

        self.head = {"Authorization": "Bearer %s" % self.access_token}
        if load_vehicles:
            self.load_vehicles()
        else:
            self.vehicles = []

    def load_vehicles(self):
        self.vehicles = [Vehicle(v, self) for v in self.get('vehicles')['response']]

    def authorization_dictionary(self):
        return self.auth_dict

    def get(self, command):
        """Utility command to get data from API"""
        return open(self.base_url, '%s%s' % (self.api, command), headers=self.head)

    def post(self, command, data={}):
        """Utility command to post data to API"""
        return open(self.base_url, '%s%s' % (self.api, command), headers=self.head, data=data)

    def open(self, url, headers={}, data=None):
        """Raw urlopen command"""
        req = Request('%s%s' % (self.base_url, url), headers=headers)
        # req.add_unredirected_header('User-Agent', 'This is a test.')

        if self.verbose_logging:
            print("Requesting: %s%s with headers %s" % (self.base_url, url, headers))

        try:
            req.data = urlencode(data).encode('utf-8')  # Python 3
        except:
            try:
                req.add_data(urlencode(data))  # Python 2
            except:
                pass
        resp = urlopen(req)
        charset = resp.info().get('charset', 'utf-8')
        return json.loads(resp.read().decode(charset))


class Vehicle(dict):
    """Vehicle class, subclassed from dictionary.

    There are 3 primary methods: wake_up, data_request and command.
    data_request and command both require a name to specify the data
    or command, respectively. These names can be found in the
    Tesla JSON API."""
    def __init__(self, data, connection):
        """Initialize vehicle class

        Called automatically by the Connection class
        """
        super(Vehicle, self).__init__(data)
        self.connection = connection

    def data_request(self, name):
        """Get vehicle data"""
        result = self.get('data_request/%s' % name)
        return result['response']

    def wake_up(self):
        """Wake the vehicle"""
        return self.post('wake_up')

    def command(self, name, data={}):
        """Run the command for the vehicle"""
        return self.post('command/%s' % name, data)

    def get(self, command):
        """Utility command to get data from API"""
        return self.connection.get('vehicles/%i/%s' % (self['id'], command))

    def post(self, command, data={}):
        """Utility command to post data to API"""
        return self.connection.post('vehicles/%i/%s' % (self['id'], command), data)

    # update the vehicle data. Largely used to get new tokens
    def update_vehicle_metadata(self):
        new_values = self.connection.get('vehicles/%i/' % self['id'])['response']
        self.update(new_values)
        return new_values
