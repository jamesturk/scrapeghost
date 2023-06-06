import logging
import structlog

# turn off non-warnings and disable timestamps
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.WARNING),
    processors=[
        structlog.processors.KeyValueRenderer(
            key_order=["event", "level", "logger", "timestamp", "exception"]
        )
    ],
)
