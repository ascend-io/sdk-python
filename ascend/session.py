"""
Ascend Session module

The Session module encapsulates an HTTP session, and adds authentication.
All API requests pass through the Session.
"""

from ascend.auth import AwsV4Auth, BearerAuth, RefreshAuth

import json
import requests


class Session:
    """
    Session implements an authenticated HTTP session to an Ascend host,
    including handling token exchange.

    # Parameters
    environment_hostname (str):
        hostname on which the Ascend environment you wish connect to is deployed
    access_key (str):
        Access Key ID you wish to use to authenticate with Ascend
    secret_key (str):
        Secret Access Key to use to authenticate with Ascend
    verify (bool):
        verify the server's SSL certificate
        (default is `True`)
    """

    def __init__(self, environment_hostname, access_key, secret_key, verify=True):
        if not access_key:
            raise ValueError("Missing api access key")
        if not secret_key:
            raise ValueError("Missing api secret key")
        if not environment_hostname:
            raise ValueError("Missing environment hostname")

        self.verify = verify
        self.base_uri = "https://{}:443/".format(environment_hostname)
        self.signed_session = requests.session()
        self.signed_session.auth = AwsV4Auth(access_key, secret_key, environment_hostname, "POST")

        self.init_token_exchange()

        self.bearer_session = requests.session()
        self.bearer_session.headers["Ascend-Service-Name"] = "sdk"
        self.bearer_session.auth = BearerAuth(self.access_token)

        self.refresh_session = requests.session()
        self.refresh_session.auth = RefreshAuth(self.refresh_token)

    def init_token_exchange(self):
        resp = self.signed_session.post(self.base_uri + "authn/tokenExchange", verify=self.verify)
        resp.raise_for_status()
        respJson = resp.json()
        self.access_token, self.refresh_token = respJson["data"]["access_token"], respJson["data"]["refresh_token"]

    def refresh_token_exchange(self):
        resp = self.refresh_session.post(self.base_uri + "authn/tokenExchange", verify=self.verify)
        resp.raise_for_status()
        respJson = resp.json()
        self.access_token, self.refresh_token = respJson["data"]["access_token"], respJson["data"]["refresh_token"]
        self.bearer_session.auth = BearerAuth(self.access_token)
        self.refresh_session.auth = RefreshAuth(self.refresh_token)

    def exchange_tokens(self):
        if self.refresh_token:
            self.refresh_token_exchange()
        else:
            self.init_token_exchange()

    def delete(self, endpoint):
        """
        Make a DELETE request

        # Parameters
        endpoint (str):
            the partial URL of the request (does not include hostname or API prefix)

        # Returns
        int: the HTTP response code status
        """
        api_url = "{}api/v1/{}".format(self.base_uri, endpoint)

        def delete_with_bearer():
            resp = self.bearer_session.delete(api_url, verify=self.verify)
            resp.raise_for_status()
            return resp.status_code

        try:
            return delete_with_bearer()
        except:
            self.exchange_tokens()
            return delete_with_bearer()

    def get(self, endpoint, query=None):
        """
        Make a GET request.

        # Parameters
        endpoint (str):
            the partial URL of the request (does not include hostname or API prefix)
        query (dict):
            query parameters to send with the request

        # Returns
        dict: the parsed JSON response
        """
        api_url = "{}api/v1/{}".format(self.base_uri, endpoint)

        def get_with_bearer():
            resp = self.bearer_session.get(api_url, params=query, verify=self.verify)
            resp.raise_for_status()
            return resp.json()

        try:
            return get_with_bearer()
        except:
            self.exchange_tokens()
            return get_with_bearer()

    def patch(self, endpoint, data=None):
        """
        Make a PATCH request.

        # Parameters
        endpoint (str):
            the partial URL of the request (does not include hostname or API prefix)
        data (dict):
            JSON to send in the request body

        # Returns
        int: the HTTP response status code
        """
        api_url = "{}api/v1/{}".format(self.base_uri, endpoint)

        def patch_with_bearer():
            resp = self.bearer_session.patch(api_url, data=json.dumps(data), verify=self.verify)
            resp.raise_for_status()
            return resp.status_code

        try:
            return patch_with_bearer()
        except:
            self.exchange_tokens()
            return patch_with_bearer()

    def post(self, endpoint, data=None):
        """
        Make a POST request.

        # Parameters
        endpoint (str):
            the partial URL of the request (does not include hostname or API prefix)
        data (dict):
            JSON to send in the request body

        # Returns
        int: the HTTP response status code
        """
        api_url = "{}api/v1/{}".format(self.base_uri, endpoint)

        def post_with_bearer():
            resp = self.bearer_session.post(api_url, data=json.dumps(data), verify=self.verify)
            resp.raise_for_status()
            return resp.status_code

        try:
            return post_with_bearer()
        except:
            self.exchange_tokens()
            return post_with_bearer()

    def stream(self, endpoint, query=None):
        """
        Make a GET request and process the results as a stream of JSON lines

        # Parameters
        endpoint (str):
            the partial URL of the request (does not include hostname or API prefix)
        query (dict):
            query parameters to send with the request

        # Returns
        Iterator<dict>: an iterator over the parsed JSON lines
        """
        api_url = "{}api/v1/{}".format(self.base_uri, endpoint)

        def stream_with_bearer():
            with self.bearer_session.get(api_url, params=query, verify=self.verify, stream=True) as resp:
                resp.raise_for_status()
                for row in resp.iter_lines():
                    yield json.loads(row)

        try:
            return stream_with_bearer()
        except:
            self.exchange_tokens()
            return stream_with_bearer()
