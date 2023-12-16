from datetime import datetime


def transform_timestamp(input_timestamp):
    # Convert the input timestamp to a datetime object
    dt_object = datetime.fromisoformat(input_timestamp)

    # Format the datetime object as desired
    formatted_timestamp = dt_object.strftime("%d %b %Y %H:%M")

    return formatted_timestamp
