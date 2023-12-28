import logging
from typing import Any
import pandas as pd


def format_and_log_data_for_debug(logger: logging.Logger, attributes: dict[str, Any]):
    log_messages = []
    for name, obj in attributes.items():
        if isinstance(obj, pd.DataFrame):
            log_message = f"{name} (head):\n{obj.head() if not obj.empty else 'Empty DataFrame'}\n"
        elif isinstance(obj, dict) and any(len(v) > 10 for v in obj.values()):
            # For dictionaries with values having more than 10 items, show keys and their counts
            summarized_dict = {k: len(v) for k, v in obj.items()}
            log_message = f"{name} (some keys have more than 10 items, showing keys and counts):\n{summarized_dict}\n"
        elif isinstance(obj, dict):
            # For other dictionaries, show the first few items
            limit = 5
            dict_head = dict(list(obj.items())[:limit])
            log_message = (
                f"{name} (first {limit}):\n{dict_head if dict_head else 'Empty Dictionary'}\n"
            )
        else:
            log_message = f"{name}:\n{obj}\n"

        log_messages.append(log_message)

    logger.debug("\n".join(log_messages))
