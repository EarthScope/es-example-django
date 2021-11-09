import json
from logging import getLogger

from django.contrib.auth import logout
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from es_user.vouch_proxy import VouchProxyJWT
from es_user.models import UserJWT
from es_user import auth0_lib
from es_common.utils import safe_json

LOGGER = getLogger(__name__)


class UserView(TemplateView):
    """
    Show information about the user
    """

    template_name = 'es_user/user.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # JWT from the user account
        user = self.request.user
        if user.is_authenticated:
            user_jwt = UserJWT.objects.filter(user=user).first()
            if user_jwt:
                context['user_jwt'] = user_jwt.jwt
            else:
                context['user_jwt'] = "not saved"
        # JWT from the request cookie
        context['cookie_jwt'] = VouchProxyJWT(self.request)
        try:
            context['user_claims'] = UserJWT.get_all_user_claims(user)
            LOGGER.info(context['user_claims'])
        except Exception as e:
            LOGGER.warning(e)
        
        try:
            api = auth0_lib.Auth0ManagementAPI()
            context['auth0_connections'] = api.get_connections()
        except Exception as e:
            LOGGER.warning(e)
            context['auth0_connections'] = e

        return context


class LoginView(RedirectView):
    """
    Handle login
    """
    def get_redirect_url(self, *args, **kwargs):
        next_page = self.request.GET.get('next_page') or reverse_lazy('user-home')
        if self.request.user.is_authenticated:
            return next_page
        else:
            next_url = self.request.build_absolute_uri(next_page)
            return '/login?url=%s' % next_url


class LogoutView(RedirectView):
    """
    Handle logout, which has a couple components :P
    """

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            logout(self.request)
        next_page = self.request.GET.get('next_page') or reverse_lazy('user-home')
        next_url = self.request.build_absolute_uri(next_page)
        return '/logout?url=%s' % next_url
