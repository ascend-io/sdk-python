"""
Ascend Session module

The Session module encapsulates an HTTP session, and adds authentication.
All API requests pass through the Session.
"""

from ascend.auth import AwsV4Auth, BearerAuth, RefreshAuth
import ascend.cli.sh as sh

import json
import requests
import urllib3


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
        if not verify:
            requests.packages.urllib3.disable_warnings(
                category=urllib3.exceptions.InsecureRequestWarning)

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

    def request_with_bearer(self, *args, **kwargs):
        sh.debug(" ".join(args))
        response = self.bearer_session.request(*args, **kwargs)
        if response.status_code == 401:
            self.exchange_tokens()
            return self.bearer_session.request(*args, **kwargs)
        return response

    def delete(self, endpoint, service='api'):
        """
        Make a DELETE request

        # Parameters
        endpoint (str):
            the partial URL of the request (does not include hostname or API prefix)

        # Returns
        int: the HTTP response code status
        """
        def delete_with_bearer():
            resp = self.bearer_session.delete(self.make_url(endpoint, service), verify=self.verify)
            resp.raise_for_status()
            return resp.status_code

        return delete_with_bearer()

    def get(self, endpoint, query=None, service='api'):
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
        def get_with_bearer():
            resp = self.request_with_bearer(
                'GET', self.make_url(endpoint, service), params=query, verify=self.verify)
            if resp.status_code == 404:
                raise KeyError(resp.reason)
            else:
                resp.raise_for_status()
                return resp.json()

        return get_with_bearer()

    def patch(self, endpoint, data=None, service='api'):
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
        def patch_with_bearer():
            resp = self.request_with_bearer(
                'PATCH', self.make_url(endpoint, service),
                data=json.dumps(data), verify=self.verify)
            resp.raise_for_status()
            return resp.status_code

        return patch_with_bearer()

    def post(self, endpoint, data=None, service='api'):
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
        def post_with_bearer():
            resp = self.request_with_bearer(
                'POST', self.make_url(endpoint, service), data=json.dumps(data), verify=self.verify)
            resp.raise_for_status()
            return resp.status_code

        return post_with_bearer()

    def make_url(self, endpoint, service):
        return f'{self.base_uri}{service}/v1/{endpoint}'

    def stream(self, endpoint, query=None, service='api'):
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

        def stream_with_bearer():
            with self.request_with_bearer(
                    'GET', self.make_url(endpoint, service), params=query, verify=self.verify, stream=True) as resp:
                resp.raise_for_status()
                for row in resp.iter_lines():
                    yield json.loads(row)

        return stream_with_bearer()
