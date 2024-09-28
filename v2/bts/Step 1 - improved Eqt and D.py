from astropy.time import Time
from astropy.coordinates import get_sun, AltAz, EarthLocation
import astropy.units as u
from datetime import datetime
import math

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
    # ra2 = sun.ra # alt method for RA but inaccurate
    
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

# Example usage:
date_str = "10-01-2025"  # Enter your date here "dd-mm-yyyy"
time_str = "12:00:00"     # Enter your time here "hh:mm:ss"
declination, eq_time = calculate_declination_eq_time(date_str, time_str)

print(f"Declination: {declination} degrees")
print(f"Equation of Time: {eq_time} minutes")