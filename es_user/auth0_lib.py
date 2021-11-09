import requests
from typing import Tuple, Any, List
from requests.auth import HTTPBasicAuth
import re
import os
from auth0.v3.authentication import GetToken
from auth0.v3.management import Auth0
from django.conf import settings
import yaml
import logging

LOGGER = logging.getLogger(__name__)


def get_domain(host):
    return re.sub(r'^(?:https?://)?(.+?)/?$', r'\1', host)


class Auth0ManagementAPI(object):
    """
    """
    client_id = settings.AUTH0_MGMT_CLIENT_ID
    client_secret = settings.AUTH0_MGMT_CLIENT_SECRET
    domain = get_domain(settings.AUTH0_MGMT_TENANT_HOST)
    mgmt_api_token = None
    auth0 = None

    def get_mgmt_token(self):
        get_token = GetToken(self.domain)
        token = get_token.client_credentials(
            self.client_id,
            self.client_secret,
            f'https://{self.domain}/api/v2/',
        )
        return token['access_token']

    def get_api(self):
        if not self.auth0:
            self.mgmt_api_token = self.get_mgmt_token()
            self.auth0 = Auth0(self.domain, self.mgmt_api_token)
        return self.auth0
    
    def get_connections(self):
        return self.get_api().connections.all()

    def as_yaml(self):
        return yaml.dump(self)


if __name__ == "__main__":
    api = Auth0ManagementAPI().get_api()
    print(api.connections.all())
