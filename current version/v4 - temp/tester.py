from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz

def get_timezone_info(lat, lon):
    # Initialize TimezoneFinder
    tf = TimezoneFinder()
    print(tf)
    # Get the timezone name based on lat and long
    timezone_str = tf.timezone_at(lng=lon, lat=lat)
    (print(timezone_str))
    if timezone_str is None:
        return "Timezone could not be determined."
    
    # Get the timezone object
    timezone = pytz.timezone(timezone_str)
    print(timezone)
    # Get the current time in UTC
    utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
    print(utc_now)
    # Get the current time in the determined timezone
    local_time = utc_now.astimezone(timezone)
    print(local_time)
    # Get the UTC offset in hours (e.g., -7 for UTC-7)
    utc_offset = local_time.utcoffset().total_seconds() / 3600
    print(utc_offset)
    # Check if DST is in effect
    print(local_time.dst())
    is_dst = bool(local_time.dst())

    # Make utc_now naive for comparison with naive transition times
    utc_now_naive = utc_now.replace(tzinfo=None)

    # Get DST start and end dates (if applicable)
    try:
        # Find the next DST transition
        dst_transitions = timezone._utc_transition_times
        dst_start = dst_end = None
        for transition in dst_transitions:
            if transition > utc_now_naive:
                # Transition is the start of DST if it has a DST offset
                dst_start = transition if timezone.localize(transition).dst() else dst_start
                # Transition is the end of DST if it does not have a DST offset
                dst_end = transition if not timezone.localize(transition).dst() else dst_end
                if dst_start and dst_end:
                    break
    except AttributeError:
        # Handle timezones that do not have DST
        dst_start, dst_end = None, None

    return {
        "timezone_utc_offset": utc_offset,  # Return the numeric UTC offset
        "is_dst": is_dst,
        "dst_start": dst_start,
        "dst_end": dst_end
    }
#970188, 3695128

# Example usage
lat = 24.913283
lon = 67.0359856
timezone_info = get_timezone_info(lat, lon)

print(timezone_info)
