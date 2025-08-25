import logging

import structlog

from aws_utils.log_utils import get_cloudwatch_handler


def setup_logging():
    """
    Configure Python logging and structlog for console and optional CloudWatch.
    """
    handlers = [logging.StreamHandler()]

    # Add optional CloudWatch handler
    cloudwatch_handler = get_cloudwatch_handler()
    if cloudwatch_handler:
        handlers.append(cloudwatch_handler)

    logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=handlers)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "fruitstore"):
    """
    Get a structlog logger with the given name.
    """
    return structlog.get_logger(name)
