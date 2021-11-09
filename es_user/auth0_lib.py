import requests
from typing import Tuple, Any, List
from requests.auth import HTTPBasicAuth
import re
import os
from auth0.v3.authentication import GetToken
from auth0.v3.management import Auth0
from django.conf import settings
import logging

LOGGER = logging.getLogger(__name__)

AUTH0_CLIENT_ID = settings.AUTH0_MGMT_CLIENT_ID
AUTH0_CLIENT_SECRET = settings.AUTH0_MGMT_CLIENT_SECRET
AUTH0_TENANT_HOST = settings.AUTH0_MGMT_TENANT_HOST


class Auth0ManagementAPI(object):
    """
    """
    client_id = settings.AUTH0_MGMT_CLIENT_SECRET
    client_secret = settings.AUTH0_MGMT_CLIENT_SECRET
    domain = settings.AUTH0_MGMT_TENANT_HOST
    mgmt_api_token = None

    def get_mgmt_token(self):
        get_token = GetToken(self.domain)
        token = get_token.client_credentials(
            self.client_id,
            self.client_secret,
            f'https://{self.domain}/api/v2/',
        )
        return token['access_token']

    def get_api(self):
        if not self.mgmt_api_token:
            self.mgmt_api_token = self.get_mgmt_token()
        return Auth0(self.domain, self.mgmt_api_token)
    
    def get_connections(self):
        return self.get_api().connections.all()


if __name__ == "__main__":
    api = Auth0ManagementAPI().get_api()
    print(api.connections.all())
