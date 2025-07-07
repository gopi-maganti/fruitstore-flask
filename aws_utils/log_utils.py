import os
import watchtower


def get_cloudwatch_handler():
    """
    Create and return a CloudWatch log handler if configuration allows.

    Returns
    -------
    watchtower.CloudWatchLogHandler or None
    """
    try:
        return watchtower.CloudWatchLogHandler(
            log_group=os.getenv("CLOUDWATCH_LOG_GROUP", "fruitstore-logs"),
            stream_name=os.getenv("HOSTNAME", "fruitstore-instance"),
        )
    except Exception as e:
        print(f"[AWS Logging] CloudWatchLogHandler failed to initialize: {e}")
        return None
