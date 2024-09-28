from skyfield.api import load
from skyfield.almanac import equation_of_time
from datetime import datetime

# Function to calculate EoT and declination using Skyfield
def calculate_declination_eq_time(date_str, time_str="00:00:00"):
    # Parse the input date and time
    dt_str = f"{date_str} {time_str}"
    dt = datetime.strptime(dt_str, '%d-%m-%Y %H:%M:%S')
    
    # Load ephemeris data
    # eph = load('de421.bsp')  # or use 'de430.bsp' for even more precision
    eph = load('de430.bsp')
    earth = eph['earth']
    ts = load.timescale()

    # Create Skyfield time object
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

    # Calculate the Sun's position as seen from Earth (geocentric position)
    sun = earth.at(t).observe(eph['sun']).apparent()
    declination = sun.dec().degrees  # Declination in degrees

    # Calculate the Equation of Time (in minutes)
    eot = equation_of_time(ts)(t)  # EoT from Skyfield in radians

    # Convert EoT from radians to minutes
    eot_minutes = eot * (180 / 3.1415926535) * 4  # 4 minutes per degree

    return declination, eot_minutes

# Example usage:
date_str = "28-09-2024"  # Enter your date here
time_str = "12:00:00"     # Enter your time here
declination, eq_time = calculate_declination_eq_time(date_str, time_str)

print(f"Declination: {declination} degrees")
print(f"Equation of Time: {eq_time} minutes")
