"""Ping the Linksys E3200 router to determine if it's still accessible."""
import logging
import sys
import json
import pandas as pd
import requests
from yaml import load, SafeLoader


with open('config.yml', 'r') as f:
    config = load(f, Loader=SafeLoader)

IP_ADDRESS = config['router_ip']
SLACK_URL = 'https://hooks.slack.com/services/' + config['slack_webhook']

DATE = pd.to_datetime('now', utc=True).tz_convert(config['time_zone'])
DATESTAMP = DATE.strftime('%Y-%m-%d %I:%M%p')

logger = logging.getLogger(name=__name__)
logger.setLevel(logging.DEBUG)

print_handler = logging.StreamHandler(stream=sys.stdout)
file_handler = logging.FileHandler(config['log_fname'],
                                   mode='a')

formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
print_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(print_handler)
logger.addHandler(file_handler)


def get_previous_state(log_fname):
    """Read a log file to get the last recorded status of the router."""
    logger = logging.getLogger(__name__ + '.get_previous_state')

    # Attempt to read the last line of an existing log file
    with open(log_fname, 'r') as log_file:
        try:
            last_log = log_file.readlines()[-1]
            timestamp, log_level, _, uptime = last_log.split(' | ')

            timestamp = pd.to_datetime(timestamp
                                       ).tz_localize(config['time_zone'])
            uptime = pd.Timedelta(uptime)

        # Create a new file if it doesn't already exist and return default data
        except IndexError:
            uptime = pd.Timedelta(0, 'm')
            timestamp = None
            log_level = 'INFO'

            logger.debug("Creating new log file named %s! | %s",
                         log_fname,
                         uptime)

    return timestamp, log_level, uptime


def update_elapsed_time(uptime, time_difference=None):
    """Update the estimated elapsed time after attempting to ping the router.

    Take the estimated time since the router status last changed and either
    add the time that has passed since then.

    The cumulative time is reset to 0 if no time difference is provided,
    which would be the case if the router status has changed since the last
    time the router was pinged.

    Note that the calculated elapsed time is based on the assumption that
    the router status did not temporarily change (and then change back) in
    between pings.

    Parameters
    ----------
    uptime : pandas Timedelta object
        The cumulative time that has passed since the log status last changed
    time_difference : pandas Timedelta object, default=None
        The time duration to add to the cumulative uptime

    Returns
    -------
    pandas Timedelta object

    """
    if time_diff is None:
        updated_time = pd.Timedelta(0, 'm')
    else:
        # Round the difference between the two timestamps to the nearest second
        updated_time = pd.Timedelta((time_difference).seconds, 's') + uptime

    return updated_time


if __name__ == '__main__':
    (last_timestamp, last_status, elapsed_time
     ) = get_previous_state(config['log_fname'])

    # Define the default settings when the router is online
    time_diff = DATE - last_timestamp
    notify = False

    try:
        ping = requests.get('http://' + IP_ADDRESS,
                            timeout=config['ping_timeout'])

        if ping.status_code == 200:
            if last_status != 'INFO':
                elapsed_time = update_elapsed_time(elapsed_time, time_diff)
                notify = True

                msg = (f'Status code {ping.status_code}: '
                       f'Router address {IP_ADDRESS} is now reachable! | '
                       f'{elapsed_time}')

            else:
                elapsed_time = update_elapsed_time(elapsed_time, time_diff)

                msg = f'Status code {ping.status_code} | {elapsed_time}'

            logger.info(msg)

        else:
            if last_status != 'WARNING':
                time_diff = None

            elapsed_time = update_elapsed_time(elapsed_time, time_diff)
            msg = f'Status code {ping.status_code} | {elapsed_time}'
            notify = True

            logger.warn(msg)

    except requests.exceptions.Timeout:
        if last_status != 'ERROR':
            time_diff = None

        elapsed_time = update_elapsed_time(elapsed_time, time_diff)
        msg = f'Router address {IP_ADDRESS} is unreachable! | {elapsed_time}'

        logger.error(msg)

        # Notify via Slack if the router became unreachable after the last ping
        if last_timestamp is None or last_status == 'INFO':
            notify = True

        # Send a reminder each day the router is still unreachable
        elif last_status != 'INFO' and last_timestamp.date() != DATE.date():
            notify = True

    if notify:
        requests.post(url=SLACK_URL,
                      data=json.dumps({'text': f'"{DATESTAMP}": `{msg}`'}),
                      headers={"Content-type": "application/json",
                               "Accept": "text/plain"})
