from skyfield.api import load
from skyfield.almanac import find_discrete
from datetime import datetime

# Function to calculate EoT and declination using Skyfield
def calculate_declination_eq_time(date_str, time_str="00:00:00"):
    # Parse the input date and time
    dt_str = f"{date_str} {time_str}"
    dt = datetime.strptime(dt_str, '%d-%m-%Y %H:%M:%S')
    
    # Load ephemeris data
    ts = load.timescale()
    # Create Skyfield time object
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    eph = load('de421.bsp')  # or use 'de430.bsp' for even more precision
    earth = eph['earth']
    sunmetric = earth.at(t).observe(eph['sun'])

    # Calculate the Sun's position as seen from Earth (geocentric position)
    sun_ra, sun_dec, sun_dist = sunmetric.apparent().radec()
    dec_wip = sun_dec  # Declination in degree,min,sec
    declination = dec_wip.degrees # Declination in degrees

    # Use the Sun's hour angle to compute the Equation of Time manually
    # Mean solar time and apparent solar time difference
    apparent_sidereal_time = earth.at(t).apparent().sidereal_time()
    mean_sidereal_time = earth.at(t).mean_sidereal_time()

    # Equation of Time in degrees
    eot_degrees = apparent_sidereal_time.degrees - mean_sidereal_time.degrees

    # Convert EoT from degrees to minutes
    eot_minutes = eot_degrees * 4  # 4 minutes per degree

    return declination, eot_minutes

# Example usage:
date_str = "28-09-2024"  # Enter your date here
time_str = "12:00:00"     # Enter your time here
declination, eq_time = calculate_declination_eq_time(date_str, time_str)

print(f"Declination: {declination} degrees")
print(f"Equation of Time: {eq_time} minutes")