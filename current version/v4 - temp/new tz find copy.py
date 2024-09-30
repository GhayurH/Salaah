from timezonefinder import TimezoneFinder
from datetime import datetime, timedelta
import pytz

def get_timezone_and_dst_info(lat, lon, start_year=None, end_year=None):
    # Initialize TimezoneFinder
    tf = TimezoneFinder()

    # Get the timezone name based on lat and long
    timezone_str = tf.timezone_at(lng=lon, lat=lat)
    
    if timezone_str is None:
        return "Timezone could not be determined."
    
    # Get the timezone object
    timezone = pytz.timezone(timezone_str)

    # Get a fixed point in time to determine the non-DST offset (January 1st when DST is usually not in effect)
    non_dst_time = timezone.localize(datetime(datetime.now().year, 1, 1))

    # Get the non-DST UTC offset in hours
    utc_offset = non_dst_time.utcoffset().total_seconds() / 3600

    # Limit transitions to a reasonable time range (from 1900 to prevent OverflowError)
    min_year = 1900
    max_year = 2100  # Keep a future bound as well
    valid_transitions = [t for t in timezone._utc_transition_times if min_year <= t.year <= max_year]

    # Check if the location ever uses DST
    is_dst = any(timezone.localize(transition).dst() != timedelta(0) for transition in valid_transitions)

    # If a range of years is provided, gather DST start/end dates for that range
    dst_start_dates = []
    dst_end_dates = []
    if start_year and end_year:
        for year in range(start_year, end_year + 1):
            jan_1 = datetime(year, 1, 1, tzinfo=pytz.utc)
            dec_31 = datetime(year, 12, 31, tzinfo=pytz.utc)

            # Get all transitions within the year
            for transition_time in valid_transitions:
                transition_aware = pytz.utc.localize(transition_time)
                if jan_1 <= transition_aware <= dec_31:
                    if timezone.localize(transition_time).dst():
                        dst_start_dates.append(transition_time.date())
                    else:
                        dst_end_dates.append(transition_time)

    return {
        "timezone_utc_offset": utc_offset,  # Numeric UTC offset (non-DST)
        "is_dst": is_dst,                   # Whether the location ever uses DST
        "dst_start_dates": dst_start_dates if start_year and end_year else None,  # DST start dates for range
        "dst_end_dates": dst_end_dates if start_year and end_year else None       # DST end dates for range
    }

# Example usage
lat = 43.493056
lon = -80.501111
start_year = 2025
end_year = 2030
timezone_info = get_timezone_and_dst_info(lat, lon, start_year, end_year)

print(timezone_info)
