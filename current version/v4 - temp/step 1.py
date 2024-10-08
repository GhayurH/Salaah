import math
from datetime import datetime, timedelta
import pandas as pd
from timezonefinder import TimezoneFinder
import pytz

# Define constants to be used
start_year, end_year = 2024, 2025
coordinates = [43.493056, -80.501111]  # format: [lat, long]
elev = 0  # elevation, only necessary for high altitudes
input_file_path = r'C:\Users\Ghayur Haider\Desktop\AZ\Git\Salaah\current version\EqT and D.csv'
df = pd.read_csv(input_file_path)
output_file_path = r'C:\Users\Ghayur Haider\Desktop\AZ\Git\Salaah\current version\pray.xlsx'

# Prayer time calculation constants
Fajr_Angle = 16
Maghrib_Angle = 4
Isha_Angle = 14


# Function to get timezone and DST information dynamically
def get_timezone_and_dst_info(lat, lon, start_year=None, end_year=None):
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lng=lon, lat=lat)

    if timezone_str is None:
        return "Timezone could not be determined."

    timezone = pytz.timezone(timezone_str)
    non_dst_time = timezone.localize(datetime(datetime.now().year, 1, 1))
    utc_offset = non_dst_time.utcoffset().total_seconds() / 3600

    min_year = 1900
    max_year = 2100
    valid_transitions = [t for t in timezone._utc_transition_times if min_year <= t.year <= max_year]

    is_loc_dst = any(timezone.localize(transition).dst() != timedelta(0) for transition in valid_transitions)
    
    dst_start_dates = []
    dst_end_dates = []
    if start_year and end_year:
        for year in range(start_year, end_year + 1):
            jan_1 = datetime(year, 1, 1, tzinfo=pytz.utc)
            dec_31 = datetime(year, 12, 31, tzinfo=pytz.utc)

            for transition_time in valid_transitions:
                transition_aware = pytz.utc.localize(transition_time)
                if jan_1 <= transition_aware <= dec_31:
                    if timezone.localize(transition_time).dst():
                        dst_start_dates.append(transition_time.date())
                    else:
                        dst_end_dates.append(transition_time.date())

    return {
        "timezone_utc_offset": utc_offset,
        "is_loc_dst": is_loc_dst,
        "dst_start_dates": dst_start_dates if start_year and end_year else None,
        "dst_end_dates": dst_end_dates if start_year and end_year else None
    }


# Function to pull declination and equation of time from .csv
def calculate_declination_eqt(year, month, day):
    filtered_row = df[(df['date_y'] == year) & (df['date_m'] == month) & (df['date_d'] == day)]
    declination = filtered_row['D_sign'].values[0] * (filtered_row['D_deg'].values[0] + (filtered_row['D_min'].values[0] / 60) + (filtered_row['D_sec'].values[0] / 3600))
    EqT = filtered_row['EqT_sign'].values[0] * (filtered_row['EqT_m'].values[0] + (filtered_row['EqT_s'].values[0] / 60))
    return declination, EqT


def T(x, latitude, declination):
    numerator = (-math.sin(math.radians(x)) - math.sin(math.radians(latitude)) * math.sin(math.radians(declination)))
    denominator = (math.cos(math.radians(latitude)) * math.cos(math.radians(declination)))
    cos_T = numerator / denominator
    return math.degrees(math.acos(cos_T)) / 15.0


def decimal_to_hms(decimal_hours):
    hours = int(decimal_hours)
    minutes = int((decimal_hours - hours) * 60)
    seconds = int(((decimal_hours - hours) * 60 - minutes) * 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def calculate_prayer_times(year, month, day, latitude, longitude, timezone, elevation):
    declination, EqT = calculate_declination_eqt(year, month, day)

    Dhuhr = 12 + timezone - longitude / 15.0 - EqT / 60.0
    sunrise = Dhuhr - T(0.833 + (0.0347 * math.sqrt(elevation)), latitude, declination)
    sunset = Dhuhr + T(0.833 + (0.0347 * math.sqrt(elevation)), latitude, declination)

    fajr = Dhuhr - T(Fajr_Angle, latitude, declination)
    isha = Dhuhr + T(Isha_Angle, latitude, declination)

    num1 = math.sin(math.atan2(1, 1 + math.tan(math.radians(abs(latitude - declination)))))
    num2 = math.sin(math.radians(latitude)) * math.sin(math.radians(declination))
    deno = (math.cos(math.radians(latitude)) * math.cos(math.radians(declination)))
    cos_A = (num1 - num2) / deno
    asr_A = math.degrees(math.acos(cos_A)) / 15.0
    Asr = Dhuhr + asr_A

    maghrib = Dhuhr + T(Maghrib_Angle, latitude, declination)
    midnight = sunset + ((fajr + 24 - sunset) / 2)

    date_str = f'{day:02d}-{month:02d}-{year}'

    prayer_times = {
        "Date": date_str,
        "Fajr": decimal_to_hms(fajr),
        "Sunrise": decimal_to_hms(sunrise),
        "Dhuhr": decimal_to_hms(Dhuhr),
        "Asr": decimal_to_hms(Asr),
        "Sunset": decimal_to_hms(sunset),
        "Maghrib": decimal_to_hms(maghrib),
        "Isha": decimal_to_hms(isha),
        "Midnight": decimal_to_hms(midnight)
    }

    return prayer_times


def save_prayer_times_to_xlsx(prayer_times_list, output_file):
    df = pd.DataFrame(prayer_times_list)
    new_column_order = ['Date', 'Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Sunset', 'Maghrib', 'Isha', 'Midnight']
    df = df[new_column_order]
    df.to_excel(output_file, index=False)


# Main Loop to calculate prayer times for the year range
all_prayer_times = []
lat, lon = coordinates
tz_info = get_timezone_and_dst_info(lat, lon, start_year, end_year)

# Get base timezone offset
base_timezone = tz_info['timezone_utc_offset']

for year in range(start_year, end_year + 1):
    for month in range(1, 13):
        days_in_month = 31 if month in [1, 3, 5, 7, 8, 10, 12] else 30 if month in [4, 6, 9, 11] else 29 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 28
        for day in range(1, days_in_month + 1):
            try:
                current_date = datetime(year, month, day).date()

                # Check if the current date is within the DST period
                is_dst = any(start <= current_date < end for start, end in zip(tz_info['dst_start_dates'], tz_info['dst_end_dates'])) if tz_info['dst_start_dates'] and tz_info['dst_end_dates'] else False
                timezone = base_timezone + 1 if is_dst else base_timezone  # Adjust for DST

                prayer_times = calculate_prayer_times(year, month, day, lat, lon, timezone, elev)
                all_prayer_times.append(prayer_times)
            except ValueError:
                pass  # Ignore invalid dates

# Save the prayer times to an Excel file
save_prayer_times_to_xlsx(all_prayer_times, output_file_path)

print(f'Prayer times saved to {output_file_path}')
