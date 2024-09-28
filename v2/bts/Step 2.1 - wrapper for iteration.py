

import math
import re
import pandas as pd
from openpyxl import Workbook
from datetime import datetime, timedelta
import xlwings as xw



#----------------------- PrayTimes Class ------------------------

class PrayTimes():


	#---------------------- Initialization -----------------------

	

	
	#---------------------- Calculation Functions -----------------------




	#---------------------- Compute Prayer Times -----------------------

	


	#---------------------- Misc Functions -----------------------



	#----------------- Degree-Based Math Functions -------------------



#---------------------- prayTimes Object -----------------------

prayTimes = PrayTimes()

##############################################################################
# Tune prayer times to round up for prayer times and round down for qaza times
prayTimes.tune({'fajr': 0.5, 'dhuhr': 0.5, 'maghrib': 0.5, 'sunrise': -0.5, 'sunset': -0.5, 'midnight': -0.5})
                
# Write a script to run the code iteratively for all days from 1-Jan-2024 to 31-Dec-2024 and the coordinates (43.493056, -80.501111)
# Function to calculate prayer times for a specific date and coordinates
def calculate_prayer_times(year, month, day, coordinates):
    # Set the desired calculation method
    # prayTimes.setMethod('Jafari')  - not needed - jafari hardcoded earlier

    # Calculate the start and end dates for DST based on the year
    dst_start = datetime(year, 3, (6 - datetime(year, 3, 1).weekday() + 8))  # Second Sunday of March
    dst_end = datetime(year, 11, (6 - datetime(year, 11, 1).weekday() + 1))  # First Sunday of November
    
    # Determine if the current date is within the DST period
    dst = dst_start <= datetime(year, month, day) < dst_end

    # Specify timezone with DST adjustment
    timezone = -4 if dst else -5

    # Get prayer times for the specified date and coordinates
    prayer_times = prayTimes.getTimes((year, month, day), coordinates, timezone)

    return prayer_times

# New function to run VBA macro using xlwings
def add_vba_macro(wb, macro_code):
    """
    Embeds a VBA macro in the Excel workbook.

    Args:
    wb: The xlwings Workbook object.
    macro_code: The VBA macro code as a string.
    """
    xlmodule = wb.api.VBProject.VBComponents.Add(1)  # 1 = vbext_ct_StdModule
    xlmodule.CodeModule.AddFromString(macro_code)

    
# Define your VBA macro code as a string
vba_macro_code = """
Sub ConvertFormats()
    Dim cell As Range
    Dim ws As Worksheet

    For Each ws In ThisWorkbook.Sheets
        For Each cell In ws.UsedRange
            If IsNumeric(Mid(cell.Value, 1, 2)) And Mid(cell.Value, 3, 1) = ":" And IsNumeric(Mid(cell.Value, 4, 2)) Then
                cell.Value = TimeValue(cell.Value)
            End If
            If IsDate(cell.Value) Then
                cell.Value = CDate(cell.Value)
            End If
        Next cell
    Next ws
End Sub
"""


# Function to create a DataFrame from the prayer times and save it to an xlsx file
def save_prayer_times_to_xlsx_with_macro(prayer_times_list, output_file):
    # Convert the list of dictionaries to a DataFrame and filter/rename columns
    df = pd.DataFrame(prayer_times_list)
    
    # Specify the new order, renaming for the columns, and filtering out unwanted keys
    new_column_order = ['Date', 'fajr', 'sunrise', 'dhuhr', 'sunset', 'maghrib', 'midnight']
    rename_columns = {
        'Date': 'Date',
        'fajr': 'Fajr',
        'sunrise': 'Sunrise',
        'dhuhr': 'Zuhr',
        'sunset': 'Sunset',
        'maghrib': 'Maghrib',
        'midnight': 'Midnight'
    }
    
    # Filter out the columns we want to keep, rename them, and reorder them
    df = df[new_column_order]
    df.rename(columns=rename_columns, inplace=True)
    
    # Use xlwings to create and manipulate the Excel workbook
    with xw.App(visible=False) as app:
        wb = xw.Book()
        sheet = wb.sheets[0]
        # Write DataFrame to Excel without index
        sheet.range('A1').options(index=False).value = df
        # Embed and run the macro
        add_vba_macro(wb, vba_macro_code)
        app.api.Run('ConvertFormats')
        # Save the workbook
        wb.save(output_file)
        wb.close()


# Iterate over all valid days in the year 2024 and calculate prayer times
start_year, end_year = 2024, 2024
coordinates = [43.493056, -80.501111]

all_prayer_times = []

for year in range(start_year, end_year + 1):
    for month in range(1, 13):
        # Determine the number of days in the month
        days_in_month = 31 if month in [1, 3, 5, 7, 8, 10, 12] else 30 if month in [4, 6, 9, 11] else 29 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 28

        for day in range(1, days_in_month + 1):
            try:
                prayer_times = calculate_prayer_times(year, month, day, coordinates)
                prayer_times['Date'] = f'{year}-{month:02d}-{day:02d}'

                all_prayer_times.append(prayer_times)
            except ValueError:
                pass  # Ignore invalid dates (e.g., Feb 30)

# Save the prayer times to an Excel file
output_file_path = "prayer_times_2024.xlsx"
save_prayer_times_to_xlsx_with_macro(all_prayer_times, output_file_path)

print(f'Prayer times saved to {output_file_path}')
