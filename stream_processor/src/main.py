from __future__ import annotations

import logging

from confluent_kafka import Consumer, KafkaError

from .clickhouse_writer import ClickHouseWriter
from .config import Settings, TOPICS
from .debezium import parse_message


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("cdc_processor")


def build_consumer(settings: Settings) -> Consumer:
    return Consumer(
        {
            "bootstrap.servers": settings.redpanda_brokers,
            "group.id": settings.consumer_group,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": "false",
        }
    )


def main() -> None:
    settings = Settings()
    writer = ClickHouseWriter(settings)
    consumer = build_consumer(settings)
    consumer.subscribe(TOPICS)
    logger.info("Subscribed to %s", ", ".join(TOPICS))

    try:
        while True:
            message = consumer.poll(settings.poll_timeout_seconds)
            if message is None:
                continue

            if message.error():
                if message.error().code() != KafkaError._PARTITION_EOF:
                    logger.error("Kafka error: %s", message.error())
                continue

            try:
                event = parse_message(
                    value=message.value(),
                    topic=message.topic(),
                    partition=message.partition(),
                    offset=message.offset(),
                )
                if event is None:
                    consumer.commit(message=message, asynchronous=False)
                    continue

                writer.write_event(event)
                consumer.commit(message=message, asynchronous=False)
                logger.info("Processed %s %s %s", event.op, event.table, event.primary_key)
            except Exception as exc:
                logger.exception("Failed to process message")
                writer.write_log(
                    level="ERROR",
                    component="stream_processor",
                    event_type="cdc_event_failed",
                    source_table=message.topic().split(".")[-1],
                    message=str(exc),
                    context={
                        "topic": message.topic(),
                        "partition": message.partition(),
                        "offset": message.offset(),
                    },
                )
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
