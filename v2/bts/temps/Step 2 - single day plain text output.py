from astropy.time import Time
from astropy.coordinates import get_sun
import math
from datetime import datetime, timedelta

# Function to calculate declination and equation of time using Astropy
def calculate_declination_eq_time(date_str, time_str="00:00:00"):
    # Parse the input date and time
    dt_str = f"{date_str} {time_str}"
    dt = datetime.strptime(dt_str, '%d-%m-%Y %H:%M:%S')
    
    # Create an Astropy Time object from the datetime
    t = Time(dt)

    # Get the Sun's position in the sky at this time
    sun = get_sun(t)

    # The declination is simply the Sun's declination at this time
    declination = sun.dec.deg
    
    # Mean anomaly of the Sun (in radians)
    D = (t.jd - 2451545.0)
    g = math.radians(357.529 + 0.98560028 * D)  # mean anomaly

    # Mean longitude of the Sun (in degrees)
    L0 = (280.459 + 0.98564736 * D) % 360

    # Apparent longitude of the Sun (L) in degrees (with aberration correction)
    L = (L0 + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)) % 360

    # Right ascension (RA) of the Sun
    e = math.radians(23.439 - 0.00000036 * D)  # obliquity of the ecliptic
    sin_L = math.sin(math.radians(L))
    cos_L = math.cos(math.radians(L))
    RA = math.degrees(math.atan2(math.cos(e) * sin_L, cos_L)) % 360  # Right Ascension in degrees

    # Calculate the Equation of Time in minutes
    EqT = 4 * (L0 - RA)  # EqT in minutes

    # Normalize EqT to stay within -20 to +20 minutes
    if EqT > 20:
        EqT -= 360
    elif EqT < -20:
        EqT += 360

    return declination, EqT

# Helper function to calculate time difference using T(x)
def T(x, latitude, declination):
    cos_T = (-math.sin(math.radians(x)) - math.sin(math.radians(latitude)) * math.sin(math.radians(declination))) / (math.cos(math.radians(latitude)) * math.cos(math.radians(declination)))
    return math.degrees(math.acos(cos_T)) / 15.0

# Helper function to convert decimal hours to hh:mm:ss
def decimal_to_hms(decimal_hours):
    hours = int(decimal_hours)
    minutes = int((decimal_hours - hours) * 60)
    seconds = int(((decimal_hours - hours) * 60 - minutes) * 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# Function to calculate all prayer times
def calculate_prayer_times(date_str, latitude, longitude, timezone, elevation=0):
    declination, EqT = calculate_declination_eq_time(date_str)
    
    # Calculate Dhuhr (midday)
    Dhuhr = 12 + timezone - (longitude / 15.0) - (EqT / 60.0)

    # Calculate Sunrise and Sunset
    sunrise = Dhuhr - T((0.833 + (0.0347 * math.sqrt(elevation))), latitude, declination)
    sunset = Dhuhr + T((0.833 + (0.0347 * math.sqrt(elevation))), latitude, declination)

    # Calculate Fajr and Isha
    fajr = Dhuhr - T(16, latitude, declination)
    isha = Dhuhr + T(14, latitude, declination)

    # Calculate Asr
    cos_A = (-math.sin((math.atan(1 + math.tan(math.radians(abs(latitude - declination)))))) - math.sin(math.radians(latitude)) * math.sin(math.radians(declination))) / (math.cos(math.radians(latitude)) * math.cos(math.radians(declination)))
    print(cos_A)
    #asr_A = math.degrees(math.acos(cos_A)) / 15.0
    
    #Asr = Dhuhr + asr_A

    # Calculate Maghrib
    maghrib = Dhuhr + T(4, latitude, declination)

    # Calculate Midnight
    midnight = (fajr + sunset) / 2

    # Convert all times to hh:mm:ss format
    prayer_times = {
        "Fajr": decimal_to_hms(fajr),
        "Sunrise": decimal_to_hms(sunrise),
        "Dhuhr": decimal_to_hms(Dhuhr),
        #"Asr": decimal_to_hms(Asr),
        "Sunset": decimal_to_hms(sunset),
        "Maghrib": decimal_to_hms(maghrib),
        "Isha": decimal_to_hms(isha),
        "Midnight": decimal_to_hms(midnight)
    }

    return prayer_times

# Example usage:
latitude = 51.5074  # London's latitude
longitude = -0.1278  # London's longitude
timezone = 0  # UTC timezone

date_str = "10-01-2025"  # Date in "dd-mm-yyyy" format
time_str = "12:00:00"     # Enter your time here "hh:mm:ss"

prayer_times = calculate_prayer_times(date_str, latitude, longitude, timezone)

for prayer, time in prayer_times.items():
    print(f"{prayer}: {time}")
