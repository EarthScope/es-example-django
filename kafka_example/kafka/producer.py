import kafka_interface as kafka
import uuid
import datetime
import logging
from django.conf import settings
from es_common.utils import get_instance_data, safe_json
from es_common.data_id import create_data_id
from kafka_example.models import ExampleValue

LOGGER = logging.getLogger(__name__)


class ProducerSingleton:
    """
    Create just one producer
    """

    instance = None

    @classmethod
    def singleton(cls, *args, **kwargs):
        if not cls.instance:
            cls.instance = cls.create(*args, **kwargs)
        return cls.instance

    @classmethod
    def create(cls, topic):
        return kafka.kafka_producer(topic)


def produce_example_message(value):
    """
    Produce one message
    """
    topic = settings.KAFKA_EXAMPLE_TOPIC
    producer = ProducerSingleton.singleton(topic)

    # Create an id for this processing step
    process_id = create_data_id("produce.example", paths=(topic, __name__), add_date=True)

    # We use a model instance to create the message for convenience
    # but it does *NOT* get saved here -- we only save the one we
    # read from kafka in the consumer
    model = ExampleValue(
        value=value,
        timestamp=datetime.datetime.utcnow(),
        data_provenance=[process_id],
    )
    model.clean()
    # instance_data = get_instance_data(model)
    message = {
        'data_id': model.data_id,
        'timestamp': model.timestamp.isoformat(),
        'data_provenance': model.data_provenance,
        'value': model.value,
    }
    LOGGER.info(safe_json(message))
    key = {
        'key': process_id,
    }
    producer.produce(key, message)
    producer.flush()
    return message
