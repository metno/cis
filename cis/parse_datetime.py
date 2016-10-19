from collections import namedtuple
import datetime
import re
from cis.time_util import cis_standard_time_unit
import argparse


def parse_datetimestr_to_std_time(s):
    import dateutil.parser as du
    return cis_standard_time_unit.date2num(du.parse(s))


def _parse_datetime(dt_string):
    """Parse a date/time string.

    The string should be in an ISO 8601 format except that the date and time
    parts may be separated by a space or colon instead of T.
    :param dt_string: String to parse
    :return: list of datetime components
    :raise ValueError: if the string cannot be parsed as a date/time
    """
    # Separate date and time at first character that is one of 'T', ' ' or ':'.
    match = re.match(r'(?P<date>[^T :]+)(?:[T :])(?P<time>.+)$', dt_string)
    if match is not None:
        date_str = match.group('date')
        time_components = [int(x) for x in match.group('time').split(':')]
    else:
        date_str = dt_string
        time_components = []

    date_components = [int(x) for x in date_str.split('-')]

    dt_components = list(date_components)
    if ((len(date_components) > 3) or (len(time_components) > 3) or
            (len(date_components) < 3) and (len(time_components) > 0)):
        raise ValueError()
    else:
        dt_components.extend(time_components)

    # Check that the components are valid (assuming month and/or date is 1 if missing).
    tmp_components = list(dt_components)
    if len(tmp_components) < 3:
        tmp_components.extend([1] * (3 - len(tmp_components)))
    datetime.datetime(*tmp_components)

    return dt_components


def date_delta_creator(year, month=0, day=0, hour=0, minute=0, second=0):
    date_delta_tuple = namedtuple('date_delta', ['year', 'month', 'day', 'hour', 'minute', 'second'])
    return date_delta_tuple(int(year), int(month), int(day), int(hour), int(minute), int(second))


def _parse_datetime_delta(dt_string):
    """Parse a date/time delta string into years, months, days, hours, minutes and seconds.

    :param dt_string: String to parse, for example 'PY2M3DT4H5M6S' (ISO 8061)
    :return: Named tuple 'date_delta' containing, 'year', 'month', 'day', 'hour', 'minute', 'second'
    :raise ValueError: if the string cannot be parsed as a date/time delta
    """

    dt_string = dt_string.upper()

    match = re.match(r'(?:[P])(?P<date>[^T :]+)?(?:[T :])?(?P<time>.+)?$', dt_string)

    if match is None:
        raise ValueError('Date/Time step must be in ISO 8061 format, for example PY2M3DT4H5M6S.')

    if match.group('date') is not None:
        date_string = match.group('date')
    else:
        date_string = ''

    if match.group('time') is not None:
        time_string = match.group('time')
    else:
        time_string = ''

    date_tokens = re.findall('[0-9]*[A-Z]', date_string)
    time_tokens = re.findall('[0-9]*[A-Z]', time_string)

    years = 0
    months = 0
    days = 0
    hours = 0
    minutes = 0
    seconds = 0

    for token in date_tokens:
        val = int(token[:-1])
        if token[-1:] == "Y":
            years = val
        elif token[-1:] == "M":
            months = val
        elif token[-1:] == "D":
            days = val
        else:
            raise ValueError("Date/Time step must be in ISO 8061 format, for example PY2M3DT4H5M6S")

    for token in time_tokens:
        val = int(token[:-1])
        if token[-1:] == "H":
            hours = val
        elif token[-1:] == "M":
            minutes = val
        elif token[-1:] == "S":
            seconds = val
        else:
            raise ValueError("Date/Time step must be in ISO 8061 format, for example PY2M3DT4H5M6S")

    times = [years, months, days, hours, minutes, seconds]

    return date_delta_creator(*times)


def _datetime_delta_to_float_days(delta):
    """
    Converts a datetime delta into a fractional day
    :param delta: the datetime delta to be converted
    :return: a float representation of a day
    """
    from datetime import timedelta

    sec = 1.0/(24.0*60.0*60.0)  # Conversion from sec to day

    days = delta.day + delta.month*365.2425/12.0 + delta.year*365.2425

    td = timedelta(days=days, hours=delta.hour, minutes=delta.minute, seconds=delta.second)

    return td.total_seconds()*sec


def parse_datetimestr_delta_to_float_days(string):
    """
    Parses "PY2M3DT4H5M6S" (ISO 8061) into a fractional day
    :param string: string to be parsed
    :return: a float representation of a day
    """

    date_delta = _parse_datetime_delta(string)
    return _datetime_delta_to_float_days(date_delta)


def parse_as_number_or_datetime(string):
    """Parse a string as a number from the command line, or if that fails, as a datetime, reporting parse errors.

    The string should be in an ISO 8601 format except that the date and time parts may be separated by a space or
     colon instead of T.

    :param in_string: String to parse
    :return: int, or float value (possibly converted to the standard time from a time string)
    """
    from datetime import datetime
    try:
        ret = int(string)
    except ValueError:
        try:
            ret = float(string)
        except ValueError:
            try:
                ret = cis_standard_time_unit.date2num(datetime(*_parse_datetime(string)))
            except ValueError:
                raise argparse.ArgumentTypeError("'{}' is not a valid value.".format(string))
    return ret


def parse_as_number_or_partial_datetime(string):
    """Parse a string as a number from the command line, or if that fails, as a datetime, reporting parse errors.

    The string should be in an ISO 8601 format except that the date and time
    parts may be separated by a space or colon instead of T.
    :param in_string: String to parse
    :return: int, float value, datetime component list or datetimedelta
    """
    try:
        ret = int(string)
    except ValueError:
        try:
            ret = float(string)
        except ValueError:
            try:
                ret = _parse_datetime(string)
            except ValueError:
                try:
                    ret = _parse_datetime_delta(string)
                except ValueError:
                    raise argparse.ArgumentTypeError("'{}' is not a valid value.".format(string))
    return ret


def convert_datetime_components_to_datetime(dt_components, is_lower_limit):
    """
    Converts date and time components: year, month, day, hours, minutes, seconds to a datetime object for use
    as a limit.

    Components beyond the year are defaulted if absent, taking minimum or maximum values if the value of
    is_lower_limit is True or False respectively.

    :param dt_components: list of date/time components as integers in the order:year, month, day, hours, minutes,
        seconds. At least the year must be specified. If only the year is specified it may be passed as an integer.
    :param is_lower_limit: If True, use minimum value for missing date/time components, otherwise use maximum.
    """
    YEAR_INDEX = 0
    DAY_INDEX = 2

    if isinstance(dt_components, list):
        all_components = list(dt_components)
    else:
        all_components = [dt_components]

    if is_lower_limit:
        default_limits = [None, 1, 1, 0, 0, 0]
    else:
        default_limits = [None, 12, None, 23, 59, 59]

    # Fill in the trailing fields with default values.
    for idx in range(len(all_components), len(default_limits)):
        if idx == YEAR_INDEX:
            # Don't default the year - this is the minimum that must be specified.
            pass
        elif idx == DAY_INDEX and not is_lower_limit:
            # Set day to last day of month.
            all_components.append(find_last_day_of_month(*all_components))
        else:
            all_components.append(default_limits[idx])
    return datetime.datetime(*all_components)


def find_last_day_of_month(year, month):
    """Finds the last day of a month.

    :param year: year as integer
    :param month: month as integer
    :return: last day of month as integer
    """
    next_month = datetime.datetime(year, month, 28) + datetime.timedelta(days=4)
    last_date = next_month - datetime.timedelta(days=next_month.day)
    return last_date.day
