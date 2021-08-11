from django.db import models
from datetime import timedelta
from kafka_example.utils import create_data_identifier, random_message
from es_common.data_id import create_data_id
from appconf import AppConf
from django.dispatch import receiver
from django.conf import settings
from django.db.models.signals import post_save
from logging import getLogger

LOGGER = getLogger(__name__)


class ExampleAppConf(AppConf):
    """
    Defaults for settings that can be overridden in settings.py
    The real setting has the app prefix, eg. TOPIC overrides EXAMPLE_TOPIC
    """
    TOPIC = "example"


class ExampleValue(models.Model):
    """
    Simple model corresponding to the example avro value
    """
    data_id = models.CharField(
        max_length=1024,
        blank=True,
    )
    data_provenance = models.JSONField(default=list)
    timestamp = models.DateTimeField()
    value = models.CharField(
        max_length=250,
        blank=True,
    )
    created_date = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if not self.data_id:
            self.data_id = create_data_id('example', add_datetime=True)
        if not self.value:
            self.value = random_message()

    def add_provenance(self, provenance_id):
        """
        Add an element to the provenance list
        """
        if provenance_id not in self.data_provenance:
            self.data_provenance.append(provenance_id)
            return True
        return False
    
    def get_archive_id(self):
        """
        Get the id of the archive in the object's provenance
        """
        return create_data_id(
            'db.example', 
            paths=[self._meta.db_table, self.pk],
            add_uuid=False,
        )

    def delay(self):
        """
        Calculate the delay from when the message was sent to when
        it was saved to the db
        """
        if self.timestamp and self.created_date:
            return self.created_date - self.timestamp

    def delay_ms(self):
        """
        Get the delay in ms
        """
        return self.delay() / timedelta(milliseconds=1)


@receiver(post_save, sender=ExampleValue)
def add_archive_provenance(instance=None, created=False, **kwargs):
    if instance and created:
        if instance.add_provenance(instance.get_archive_id()):
            instance.save()
