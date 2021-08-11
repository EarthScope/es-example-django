from django.views.generic.edit import FormView
from django.views.generic.base import RedirectView
from django import forms
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from kafka_example.kafka.producer import produce_example_message
from kafka_example.models import ExampleValue
from django.contrib.auth import logout
from es_common.data_id import create_data_id
import gzip
import base64
import jwt
import requests
import logging
import json

LOGGER = logging.getLogger(__name__)


class TestForm(forms.ModelForm):
    """
    Form for the ExampleValue
    """

    class Meta:
        model = ExampleValue
        fields = ['value']
        widgets = {
            'value': forms.TextInput(
                attrs={'class': "form-control", 'placeholder': 'Optional message'}
            ),
        }


class IndexView(FormView):
    """
    It's a form with one field, the value to send
    """

    template_name = 'kafka_example/index.html'
    form_class = TestForm
    # When done, redirect back to this page
    success_url = reverse_lazy('example-home')

    def form_valid(self, form):
        """
        The form itself is good, try sending it as a message
        """
        try:
            value = form.cleaned_data.get('value')
            sent = produce_example_message(value)
            messages.add_message(
                self.request,
                messages.SUCCESS,
                "Added to queue: %s" % json.dumps(sent),
            )
            LOGGER.debug("Added to queue: %s", sent)
        except Exception as e:
            LOGGER.error(e, exc_info=True)
            messages.add_message(
                self.request,
                messages.ERROR,
                "Uh oh! %s" % e,
            )
        # Those operations set a message in the response
        # but the response itself is always the form looking ok
        return super().form_valid(form)

    def get_page_id(self):
        """
        """
        return create_data_id('web', paths=[self.request.path.strip('/')], add_datetime=True)

    def get_context_data(self, **kwargs):
        """
        Add data to the template context
        """
        context = super().get_context_data(**kwargs)
        # Include the last few processed items
        recent = ExampleValue.objects.order_by('-created_date')[:20]
        # Add this page to their provenance
        page_id = self.get_page_id()
        for r in recent:
            r.data_provenance.append(page_id)
        context['recent'] = recent
        return context
