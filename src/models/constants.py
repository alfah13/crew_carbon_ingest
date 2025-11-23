"""
Aspirational Improvement
"""

from enum import Enum
import pytz

# Get all valid IANA timezones
VALID_TIMEZONES = pytz.all_timezones


class TimezoneEnum(str, Enum):
    """Enum of common timezones"""

    UTC = "UTC"

    # US Timezones
    US_EASTERN = "America/New_York"
    US_CENTRAL = "America/Chicago"
    US_MOUNTAIN = "America/Denver"
    US_PACIFIC = "America/Los_Angeles"

    # European Timezones
    EUROPE_LONDON = "Europe/London"
    EUROPE_PARIS = "Europe/Paris"
    EUROPE_BERLIN = "Europe/Berlin"
    EUROPE_AMSTERDAM = "Europe/Amsterdam"
    EUROPE_ROME = "Europe/Rome"

    # Asian Timezones
    ASIA_TOKYO = "Asia/Tokyo"
    ASIA_SHANGHAI = "Asia/Shanghai"
    ASIA_SINGAPORE = "Asia/Singapore"

    # Australian Timezones
    AUSTRALIA_SYDNEY = "Australia/Sydney"
    AUSTRALIA_MELBOURNE = "Australia/Melbourne"

    @classmethod
    def is_valid(cls, value):
        """Check if timezone is valid"""
        return value in VALID_TIMEZONES

    @classmethod
    def get_all_timezones(cls):
        """Get all valid IANA timezones"""
        return VALID_TIMEZONES

    @classmethod
    def get_common_timezones(cls):
        """Get list of commonly used timezones"""
        return [tz.value for tz in cls]
