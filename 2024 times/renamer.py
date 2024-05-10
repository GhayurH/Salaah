import os
import re
from datetime import datetime

# Define the folder path
folder_path = r'C:\Users\Muntazireen\Documents\Tech Drive\Salaah\2024 times\a'

# Define the mapping of strings to be replaced with corresponding month names
string_to_month = {
    "Jan": "January",
    "Feb": "February",
    "Mar": "March",
    "Apr": "April",
    "May": "May",
    "Jun": "June",
    "Jul": "July",
    "Aug": "August",
    "Sep": "September",
    "Oct": "October",
    "Nov": "November",
    "Dec": "December",
    # Add more mappings as needed
}

# Define the pattern for matching the file names
pattern = re.compile(r'(\d{4}) times_page-\d{4}\.jpg')

# Function to rename files
def rename_files(folder_path):
    for filename in os.listdir(folder_path):
        match = pattern.match(filename)
        if match:
            year = match.group(1)
            month_num = int(filename.split('_page-')[1][:2])
            month_name = string_to_month[datetime.strptime(str(month_num), '%m').strftime('%b')]
            new_filename = f"{month_name} {year}.jpg"
            os.rename(os.path.join(folder_path, filename), os.path.join(folder_path, new_filename))
            print(f"Renamed {filename} to {new_filename}")

# Call the function to rename files in the folder
rename_files(folder_path)
