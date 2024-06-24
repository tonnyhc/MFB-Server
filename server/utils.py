from contextlib import contextmanager
from datetime import datetime
from distutils.util import strtobool


def transform_timestamp(input_timestamp):
    # Convert the input timestamp to a datetime object
    dt_object = datetime.fromisoformat(input_timestamp)
    # Format the datetime object as desired
    formatted_timestamp = dt_object.strftime("%d %b %Y %H:%M")
    return formatted_timestamp


def transform_timestamp_without_hour(input_timestamp):
    # Convert the input timestamp to a datetime object
    dt_object = datetime.fromisoformat(input_timestamp)
    # Format the datetime object as desired
    formatted_timestamp = dt_object.strftime("%d %b %Y")
    return formatted_timestamp


def string_to_bool(value):
    """
    Convert a string representation of boolean ('true' or 'false') to a boolean value.
    """
    return bool(strtobool(str(value)))