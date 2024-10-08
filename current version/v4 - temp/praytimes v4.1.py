'''
----------------------------------------------------------
Shia Ithana Ashari Prayer Times Calculator
Version 4.1
Date: 30-09-2024
----------------------------------------------------------
Inputs: a start year, end year, and latitude/longitude coordinates
Outputs: an .xlsx file of prayer times from 01-Jan-StartYear to 31-Dec-EndYear, and images of the prayer times table for each calendar month    

Uses CSV data generated by the United States Naval Observatory (exact data, no approximate calculations).
- Source: https://aa.usno.navy.mil/data/geocentric

----------------------------------------------------------
IMPORTANT: Angle Values:
1. Fajr Angle:      16° (per Leva Research Institute, Qum)
2. Maghrib Angle:   4° (best guess from praytimes.org)
3. Isha Angle:      14° (per Leva Research Institute, Qum)
4. Midnight:        Calculated as the midpoint of Sunset and Fajr (This is hardcoded)

----------------------------------------------------------

License: GNU GPL v3.0

TERMS OF USE:
Permission is granted to use this code, with or without modification, in any website or application, as long as credit is given to the original work with a link back to https://github.com/GhayurH/Salaah. The use of this code cannot be for monetary profit, except if the website or application hosting the code also displays advertisements, provided that it is not solely dedicated to running this code.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY.

PLEASE DO NOT REMOVE THIS COPYRIGHT BLOCK.

---------------------Acknowledgement-------------------------
Code inspired by praytimes.org.
'''

import math
from datetime import datetime, timedelta
import pandas as pd
from timezonefinder import TimezoneFinder
import pytz
import matplotlib.pyplot as plt
#from matplotlib import font_manager

# Define constants to be used
start_year, end_year = 2024, 2024
coordinates          = [43.429516, -80.484115]  # format: [lat, long]
elev                 = 0  # elevation, only necessary for high altitudes
input_file_path      = r'C:\Users\Ghayur Haider\Desktop\AZ\Git\Salaah\current version\EqT and D.csv'
df = pd.read_csv(input_file_path)
output_xlsx_path     = r'C:\Users\Ghayur Haider\Desktop\AZ\Git\Salaah\current version\praytimes.xlsx'
output_image_directory = r'C:\Users\Ghayur Haider\Desktop\AZ\Git\Salaah\current version\images'

# Prayer time calculation constants
Fajr_Angle    = 16
Maghrib_Angle = 4
Isha_Angle    = 14


# Set Aptos as the font family
plt.rcParams['font.family'] = 'Calibri'
plt.rcParams['font.size'] = 12  # Set font size if needed


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

    date_obj = datetime(year, month, day)

    prayer_times = {
        "Date": date_obj,  # Store as datetime object
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
    
    # Convert Date column to datetime format
    df['Date'] = pd.to_datetime(df['Date'])
    
    df.to_excel(output_file, index=False)

def save_monthly_prayer_times_images(prayer_times_list, output_directory):
    # Convert list of dictionaries to DataFrame for easier manipulation
    df = pd.DataFrame(prayer_times_list)

    # Group by year and month
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y')  # Convert Date column to datetime
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month_name()  # Get full month name
    grouped = df.groupby(['Year', 'Month'])

    # Iterate through each month and create an image
    for (year, month), group in grouped:
        # Create table with selected columns
        table_data = group[['Date', 'Fajr', 'Sunrise', 'Dhuhr', 'Sunset', 'Maghrib', 'Midnight']]

        # Dynamically calculate the width of the image based on the table content
        num_columns = len(table_data.columns)
        num_rows = len(table_data)
        fig_width = num_columns * .8  # Adjust this multiplier to set the desired width per column
        fig_height = num_rows * 0.2  # Adjust this multiplier to set the desired row height

        fig, ax = plt.subplots(figsize=(fig_width, fig_height))

        # Hide axes
        ax.axis('tight')
        ax.axis('off')

        # Explicitly cast to string to avoid FutureWarning
        table_data['Date'] = table_data['Date'].dt.strftime('%b %d')  # Format date to "Jan 1"

        # Create the table
        table = ax.table(cellText=table_data.values,
                         colLabels=table_data.columns,
                         cellLoc='center',
                         loc='center')

        # Adjust column width to fit content
        table.auto_set_column_width([0, 1, 2, 3, 4, 5, 6])

        # Style the table (font, color)
        for (i, j), cell in table.get_celld().items():
            # Set vertical alignment to center for all cells
            cell.set_text_props(va='center')  # Vertically center the text

            if i == 0:  # Header row
                cell.set_text_props(weight='bold', fontsize=12)
                cell.set_facecolor('#D9D9D9')  # Light gray for header
            else:
                # Alternate row colors for banding
                if i % 2 == 0:  # Even rows
                    cell.set_facecolor('#D9D9D9')  # Light gray
                else:  # Odd rows
                    cell.set_facecolor('#ffffff')  # White

                # Additional styling for specific columns
                if j == 0:  # Date column
                    cell.set_text_props(weight='bold', color='#000000')  # Black for the date
                elif j in [1, 2]:  # Fajr and Sunrise columns
                    cell.set_text_props(color='#00B24E')  # Green for Fajr and Sunrise
                elif j in [3, 4]:  # Dhuhr and Sunset columns
                    cell.set_text_props(color='#BD5113')  # Brown for Dhuhr and Sunset
                elif j in [5, 6]:  # Maghrib and Midnight columns
                    cell.set_text_props(color='#0170BF')  # Blue for Maghrib and Midnight


        # Set title with full month name and year, ensuring it is above the table
        plt.suptitle(f'{month} {year}', fontsize=16, ha='center', va='top', y=1.05)

        # Remove extra whitespace by tightening layout
        plt.subplots_adjust(top=0.75)  # Adjust space between title and table
        plt.tight_layout(pad=0.0)  # Remove extra padding

        # Save the figure as an image, using bbox_inches='tight' to remove extra whitespace
        image_path = f'{output_directory}/{month} {year}.png'
        plt.savefig(image_path, bbox_inches='tight', dpi=300)
        plt.close(fig)  # Close the figure to free memory


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
save_prayer_times_to_xlsx(all_prayer_times, output_xlsx_path)

# Save monthly images of prayer times
save_monthly_prayer_times_images(all_prayer_times, output_image_directory)

print(f'Prayer times saved to {output_xlsx_path}')
print(f'Monthly images saved to {output_image_directory}')