import math
from datetime import datetime, timedelta

# Helper function to compute Julian Date
def julian_date(day, month, year):
    if month <= 2:
        year -= 1
        month += 12
    A = math.floor(year / 100)
    B = 2 - A + math.floor(A / 4)
    JD = math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + B - 1524.5
    return JD

# Function to calculate declination and equation of time
def calculate_declination_eq_time(date_str):
    # Parse the input date
    day, month, year = map(int, date_str.split('-'))
    
    # Compute Julian Date and D (days since J2000.0)
    JD = julian_date(day, month, year)
    D = JD - 2451545.0

    # Compute g, q, and L (mean anomaly, mean longitude, and ecliptic longitude)
    g = 357.529 + 0.98560028 * D
    g = math.radians(g % 360)  # Convert g to radians and ensure it is within 0-360 degrees
    q = 280.459 + 0.98564736 * D
    q = q % 360  # Reduce q to the range 0° to 360°
    L = q + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)
    L = math.radians(L % 360)  # Convert L to radians and ensure it is within 0-360 degrees
    
    # Approximate Sun's ecliptic latitude and distance (not used in calculation)
    # b = 0  # b can be approximated as 0
    # R = 1.00014 - 0.01671 * math.cos(g) - 0.00014 * math.cos(2 * g)
    
    # Compute the mean obliquity of the ecliptic
    e = math.radians(23.439 - 0.00000036 * D)
    
    # Compute Sun's right ascension (RA) and declination (d)
    sin_L = math.sin(L)
    cos_L = math.cos(L)
    # tan_RA = math.cos(e) * sin_L / cos_L
    RA = math.degrees(math.atan2(math.cos(e) * sin_L, cos_L))  # atan2 ensures the proper quadrant
    RA = RA % 360  # Reduce RA to the range 0° to 360°
    RA_hours = RA / 15  # Convert RA to hours (0h to 24h range)
    
    sin_d = math.sin(e) * sin_L
    d = math.degrees(math.asin(sin_d))  # Declination in degrees
    
    # Compute the Equation of Time (EqT)
    EqT = (q / 15) - RA_hours  # Equation of Time in hours
    
    return d, EqT

# Example usage:
date_str = "28-09-2024"  # Enter your date here
declination, eq_time = calculate_declination_eq_time(date_str)

print(f"Declination: {declination:.4f} degrees")
print(f"Equation of Time: {eq_time:.4f} hours")
