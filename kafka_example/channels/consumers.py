from channels.generic.websocket import JsonWebsocketConsumer, SyncConsumer
from kafka_example.models import ExampleValue
from logging import getLogger
from kafka_example.kafka.producer import produce_example_message
from es_common.utils import parse_iso8601, safe_json, parse_json

LOGGER = getLogger(__name__)


def clean_json(data):
    """
    JSON can be picky, so serialize safely then deserialize to get
    something safe for a picky parser
    """
    return parse_json(safe_json(data))


class ExampleConsumer(JsonWebsocketConsumer):
    """
    A websocket consumer for operations on the example topic
    """
    def connect(self):
        LOGGER.info("Connected: %s", self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive_json(self, request):
        """
        Handle a message from the client
        """
        action = request.get('action')
        try:
            response = {}
            if action == 'send':
                # Send message
                response['result'] = self.action_send(request)
            elif action == 'list':
                # Updates since
                response['items'] = self.action_list(request)
            else:
                raise NotImplementedError("No action %s" % action)
            response['status'] = 'ok'
            self.send_json(response)
        except Exception as e:
            self.send_json({
                'status': 'error',
                'error': str(e),
            })

    def action_send(self, request):
        """
        Send a message on the kafka topic
        """
        value = request.get('value')
        produce_example_message(value)
        return value
    
    def action_list(self, request):
        """
        Return a list of items from the archive
        """
        qs = ExampleValue.objects.order_by('-created_date')
        since = request.get('since')
        if since:
            qs = qs.filter(created_date__gte=since)
        return clean_json(list(qs.values()[:20]))


class ExampleArchivedConsumer(SyncConsumer):
    """
    Listens for Channel notifications that an item has been saved
    """
    def example_archived(self, ctx):
        obj = ExampleValue.objects.get(pk=ctx.get('pk'))
        LOGGER.info("example_archived: %s", obj)

