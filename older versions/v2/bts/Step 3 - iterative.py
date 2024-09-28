from astropy.time import Time
from astropy.coordinates import get_sun
import math
from datetime import datetime
import pandas as pd
import xlwings as xw



# Function to calculate declination and equation of time using Astropy
def calculate_declination_eq_time(date_str, time_str="00:00:00"):
    dt_str = f"{date_str} {time_str}"
    dt = datetime.strptime(dt_str, '%d-%m-%Y %H:%M:%S')
    t = Time(dt)

    sun = get_sun(t)
    declination = sun.dec.deg
    D = (t.jd - 2451545.0)
    g = math.radians(357.529 + 0.98560028 * D)

    L0 = (280.459 + 0.98564736 * D) % 360
    L = (L0 + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)) % 360
    e = math.radians(23.439 - 0.00000036 * D)
    sin_L = math.sin(math.radians(L))
    cos_L = math.cos(math.radians(L))
    RA = math.degrees(math.atan2(math.cos(e) * sin_L, cos_L)) % 360

    EqT = 4 * (L0 - RA)

    if EqT > 20:
        EqT -= 360
    elif EqT < -20:
        EqT += 360

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

def calculate_prayer_times(date_str, latitude, longitude, timezone, elevation=0):
    declination, EqT = calculate_declination_eq_time(date_str)

    Dhuhr = 12 + timezone - longitude / 15.0 - EqT / 60.0
    sunrise = Dhuhr - T(0.833 + (0.0347 * math.sqrt(elevation)), latitude, declination)
    sunset = Dhuhr + T(0.833 + (0.0347 * math.sqrt(elevation)), latitude, declination)

    fajr = Dhuhr - T(16, latitude, declination)
    isha = Dhuhr + T(14, latitude, declination)

    num1 = math.sin(math.atan2(1, 1 + math.tan(math.radians(abs(latitude - declination)))))
    num2 = math.sin(math.radians(latitude)) * math.sin(math.radians(declination))
    deno = (math.cos(math.radians(latitude)) * math.cos(math.radians(declination)))
    cos_A = (num1 - num2) / deno
    asr_A = math.degrees(math.acos(cos_A)) / 15.0
    Asr = Dhuhr + asr_A

    maghrib = Dhuhr + T(4, latitude, declination)
    midnight = sunset + ((fajr + 24 - sunset) / 2)

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

    # Define the column order and renaming if needed
    new_column_order = ['Date', 'Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Sunset', 'Maghrib', 'Isha', 'Midnight']
    rename_columns = {
        'Date': 'Date',
        'Fajr': 'Fajr',
        'Sunrise': 'Sunrise',
        'Dhuhr': 'Dhuhr',
        'Asr': 'Asr',
        'Sunset': 'Sunset',
        'Maghrib': 'Maghrib',
        'Isha': 'Isha',
        'Midnight': 'Midnight'
    }

    df = df[new_column_order]
    df.rename(columns=rename_columns, inplace=True)

    # Save DataFrame to Excel
    df.to_excel(output_file, index=False)


# Function to calculate prayer times for a specific date and coordinates
def calculate_prayer_times_with_dst(year, month, day, coordinates):
    dst_start = datetime(year, 3, (6 - datetime(year, 3, 1).weekday() + 8))  # Second Sunday of March
    dst_end = datetime(year, 11, (6 - datetime(year, 11, 1).weekday() + 1))  # First Sunday of November
    
    dst = dst_start <= datetime(year, month, day) < dst_end
    timezone = -4 if dst else -5  # UTC-4 with DST, UTC-5 without

    date_str = f'{day:02d}-{month:02d}-{year}'
    prayer_times = calculate_prayer_times(date_str, coordinates[0], coordinates[1], timezone)

    return prayer_times

# Iterate over all valid days in the year 2024 and calculate prayer times
start_year, end_year = 2024, 2024
coordinates = [43.493056, -80.501111]

all_prayer_times = []

for year in range(start_year, end_year + 1):
    for month in range(1, 13):
        days_in_month = 31 if month in [1, 3, 5, 7, 8, 10, 12] else 30 if month in [4, 6, 9, 11] else 29 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 28

        for day in range(1, days_in_month + 1):
            try:
                prayer_times = calculate_prayer_times_with_dst(year, month, day, coordinates)
                all_prayer_times.append(prayer_times)
            except ValueError:
                pass  # Ignore invalid dates


# Save the prayer times to an Excel file
output_file_path = r'C:\Users\Ghayur Haider\Desktop\prayer_times.xlsx'
save_prayer_times_to_xlsx(all_prayer_times, output_file_path)

print(f'Prayer times saved to {output_file_path}')
