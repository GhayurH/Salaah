#!/usr/bin/env python
# compatible with python 2.x and 3.x

import math
import re
import pandas as pd
from openpyxl import Workbook
from datetime import datetime, timedelta
import xlwings as xw

'''
--------------------- Copyright Block ----------------------

praytimes.py: Prayer Times Calculator (ver 2.3)
Copyright (C) 2007-2011 PrayTimes.org

Python Code: Saleem Shafi, Hamid Zarrabi-Zadeh
Original js Code: Hamid Zarrabi-Zadeh

License: GNU LGPL v3.0

TERMS OF USE:
	Permission is granted to use this code, with or
	without modification, in any website or application
	provided that credit is given to the original work
	with a link back to PrayTimes.org.

This program is distributed in the hope that it will
be useful, but WITHOUT ANY WARRANTY.

PLEASE DO NOT REMOVE THIS COPYRIGHT BLOCK.


--------------------- Help and Manual ----------------------

User's Manual:
http://praytimes.org/manual

Calculation Formulas:
http://praytimes.org/calculation
	
'''

#----------------------- PrayTimes Class ------------------------

class PrayTimes():


	#------------------------ Constants --------------------------

	# Time Names
	timeNames = {
		'imsak'    : 'Imsak',
		'fajr'     : 'Fajr',
		'sunrise'  : 'Sunrise',
		'dhuhr'    : 'Dhuhr',
		'asr'      : 'Asr',
		'sunset'   : 'Sunset',
		'maghrib'  : 'Maghrib',
		'isha'     : 'Isha',
		'midnight' : 'Midnight'
	}

	# Calculation Methods
	methods = {
		#'Tehran': {
		#	'name': 'Institute of Geophysics, University of Tehran',
		#	'params': { 'fajr': 17.7, 'isha': 14, 'maghrib': 4.5, 'midnight': 'Jafari' } },  # isha is not explicitly specified in this method
		'Jafari': {
			'name': 'Shia Ithna-Ashari, Leva Institute, Qum',
			'params': { 'fajr': 16, 'isha': 14, 'maghrib': 4, 'midnight': 'Jafari' } }
	}

	# Default Parameters in Calculation Methods
	defaultParams = {
		'maghrib': '0 min', 'midnight': 'Jafari'
	}

	
	#---------------------- Default Settings --------------------

	calcMethod = 'Jafari'
	
	# do not change anything here; use adjust method instead
	settings = {
		"imsak"    : '10 min',
		"dhuhr"    : '0 min',
		"asr"      : 'Standard',
		"highLats" : 'NightMiddle'
	}
	
	timeFormat = '24h'
	timeSuffixes = ['am', 'pm']
	invalidTime =  '-----'

	numIterations = 1
	offset = {}


	#---------------------- Initialization -----------------------

	def __init__(self, method = "Jafari") :

		# set methods defaults
		for method, config in self.methods.items():
			for name, value in self.defaultParams.items():
				if not name in config['params'] or config['params'][name] is None:
					config['params'][name] = value

		# initialize settings
		self.calcMethod = method if method in self.methods else 'Jafari'
		params = self.methods[self.calcMethod]['params']
		for name, value in params.items():
			self.settings[name] = value

		# init time offsets
		for name in self.timeNames:
			self.offset[name] = 0


	#-------------------- Interface Functions --------------------

	def setMethod(self, method):
		if method in self.methods:
			self.adjust(self.methods[method].params)
			self.calcMethod = method

	def adjust(self, params):
		self.settings.update(params)

	def tune(self, timeOffsets):
		self.offset.update(timeOffsets)
			
	def getMethod(self):
		return self.calcMethod

	def getSettings(self):
		return self.settings
		
	def getOffsets(self):
		return self.offset

	def getDefaults(self):
		return self.methods

	# return prayer times for a given date
	def getTimes(self, date, coords, timezone, dst = 0, format = None):
		self.lat = coords[0]
		self.lng = coords[1]
		self.elv = coords[2] if len(coords)>2 else 0
		if format != None:
			self.timeFormat = format
		if type(date).__name__ == 'date':
			date = (date.year, date.month, date.day)
		self.timeZone = timezone + (1 if dst else 0)
		self.jDate = self.julian(date[0], date[1], date[2]) - self.lng / (15 * 24.0)
		return self.computeTimes()
	
	# convert float time to the given format (see timeFormats)
	def getFormattedTime(self, time, format, suffixes = None):
		if math.isnan(time):
			return self.invalidTime
		if format == 'Float':
			return time
		if suffixes == None:
			suffixes = self.timeSuffixes

		time = self.fixhour(time+ 0.5/ 60)  # add 0.5 minutes to round
		hours = math.floor(time)
		
		minutes = math.floor((time- hours)* 60)
		suffix = suffixes[ 0 if hours < 12 else 1 ] if format == '12h' else ''
		formattedTime = "%02d:%02d" % (hours, minutes) if format == "24h" else "%d:%02d" % ((hours+11)%12+1, minutes)
		return formattedTime + suffix

	
	#---------------------- Calculation Functions -----------------------

	# compute mid-day time
	def midDay(self, time):
		eqt = self.sunPosition(self.jDate + time)[1]
		return self.fixhour(12 - eqt)

	# compute the time at which sun reaches a specific angle below horizon 
	def sunAngleTime(self, angle, time, direction = None):
		try:
			decl = self.sunPosition(self.jDate + time)[0]
			noon = self.midDay(time)
			t = 1/15.0* self.arccos((-self.sin(angle)- self.sin(decl)* self.sin(self.lat))/
					(self.cos(decl)* self.cos(self.lat)))
			return noon+ (-t if direction == 'ccw' else t)
		except ValueError:
			return float('nan')

	# compute asr time
	def asrTime(self, factor, time): 
		decl = self.sunPosition(self.jDate + time)[0]
		angle = -self.arccot(factor + self.tan(abs(self.lat - decl)))
		return self.sunAngleTime(angle, time)

	# compute declination angle of sun and equation of time
	# Ref: http://aa.usno.navy.mil/faq/docs/SunApprox.php
	def sunPosition(self, jd):
		D = jd - 2451545.0
		g = self.fixangle(357.529 + 0.98560028* D)
		q = self.fixangle(280.459 + 0.98564736* D)
		L = self.fixangle(q + 1.915* self.sin(g) + 0.020* self.sin(2*g))

		R = 1.00014 - 0.01671*self.cos(g) - 0.00014*self.cos(2*g)
		e = 23.439 - 0.00000036* D

		RA = self.arctan2(self.cos(e)* self.sin(L), self.cos(L))/ 15.0
		eqt = q/15.0 - self.fixhour(RA)
		decl = self.arcsin(self.sin(e)* self.sin(L))

		return (decl, eqt)
		
	# convert Gregorian date to Julian day
	# Ref: Astronomical Algorithms by Jean Meeus
	def julian(self, year, month, day):
		if month <= 2:
			year -= 1
			month += 12
		A = math.floor(year / 100)
		B = 2 - A + math.floor(A / 4)
		return math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + B - 1524.5



	#---------------------- Compute Prayer Times -----------------------

	# compute prayer times at given julian date
	def computePrayerTimes(self, times):
		times = self.dayPortion(times)
		params = self.settings
		
		imsak   = self.sunAngleTime(self.eval(params['imsak']), times['imsak'], 'ccw')
		fajr    = self.sunAngleTime(self.eval(params['fajr']), times['fajr'], 'ccw')
		sunrise = self.sunAngleTime(self.riseSetAngle(self.elv), times['sunrise'], 'ccw')
		dhuhr   = self.midDay(times['dhuhr'])
		asr     = self.asrTime(self.asrFactor(params['asr']), times['asr'])
		sunset  = self.sunAngleTime(self.riseSetAngle(self.elv), times['sunset'])
		maghrib = self.sunAngleTime(self.eval(params['maghrib']), times['maghrib'])
		isha    = self.sunAngleTime(self.eval(params['isha']), times['isha']) 
		return {
			'imsak': imsak, 'fajr': fajr, 'sunrise': sunrise, 'dhuhr': dhuhr,
			'asr': asr, 'sunset': sunset, 'maghrib': maghrib, 'isha': isha
		}

	# compute prayer times
	def computeTimes(self):
		times = {
			'imsak': 5, 'fajr': 5, 'sunrise': 6, 'dhuhr': 12,
			'asr': 13, 'sunset': 18, 'maghrib': 18, 'isha': 18
		}
		# main iterations
		for i in range(self.numIterations):
			times = self.computePrayerTimes(times)
		times = self.adjustTimes(times)
		# add midnight time
		times['midnight'] = times['sunset'] + self.timeDiff(times['sunset'], times['fajr']) / 2
		
		times = self.tuneTimes(times)
		return self.modifyFormats(times)
		
	# adjust times in a prayer time array
	def adjustTimes(self, times):
		params = self.settings
		tzAdjust = self.timeZone - self.lng / 15.0
		for t,v in times.items():
			times[t] += tzAdjust

		if params['highLats'] != 'None':
			times = self.adjustHighLats(times)

		if self.isMin(params['imsak']):
			times['imsak'] = times['fajr'] - self.eval(params['imsak']) / 60.0
		# need to ask about 'min' settings
		if self.isMin(params['maghrib']):
			times['maghrib'] = times['sunset'] - self.eval(params['maghrib']) / 60.0

		if self.isMin(params['isha']):
			times['isha'] = times['maghrib'] - self.eval(params['isha']) / 60.0
		times['dhuhr'] += self.eval(params['dhuhr']) / 60.0

		return times

	# get asr shadow factor
	def asrFactor(self, asrParam):
		methods = {'Standard': 1, 'Hanafi': 2}
		return methods[asrParam] if asrParam in methods else self.eval(asrParam)

	# return sun angle for sunset/sunrise
	def riseSetAngle(self, elevation = 0):
		elevation = 0 if elevation == None else elevation
		return 0.833 + 0.0347 * math.sqrt(elevation) # an approximation

	# apply offsets to the times
	def tuneTimes(self, times):
		for name, value in times.items():
			times[name] += self.offset[name] / 60.0
		return times

	# convert times to given time format
	def modifyFormats(self, times):
		for name, value in times.items():
			times[name] = self.getFormattedTime(times[name], self.timeFormat)
		return times
	
	# adjust times for locations in higher latitudes
	def adjustHighLats(self, times):
		params = self.settings
		nightTime = self.timeDiff(times['sunset'], times['sunrise']) # sunset to sunrise
		times['imsak'] = self.adjustHLTime(times['imsak'], times['sunrise'], self.eval(params['imsak']), nightTime, 'ccw')
		times['fajr']  = self.adjustHLTime(times['fajr'], times['sunrise'], self.eval(params['fajr']), nightTime, 'ccw')
		times['isha']  = self.adjustHLTime(times['isha'], times['sunset'], self.eval(params['isha']), nightTime)
		times['maghrib'] = self.adjustHLTime(times['maghrib'], times['sunset'], self.eval(params['maghrib']), nightTime)
		return times

	# adjust a time for higher latitudes
	def adjustHLTime(self, time, base, angle, night, direction = None):
		portion = self.nightPortion(angle, night)
		diff = self.timeDiff(time, base) if direction == 'ccw' else self.timeDiff(base, time)
		if math.isnan(time) or diff > portion:
			time = base + (-portion if direction == 'ccw' else portion)
		return time

	# the night portion used for adjusting times in higher latitudes
	def nightPortion(self, angle, night):
		method = self.settings['highLats']
		portion = 1/2.0  # midnight
		if method == 'AngleBased':
			portion = 1/60.0 * angle
		if method == 'OneSeventh':
			portion = 1/7.0
		return portion * night

	# convert hours to day portions
	def dayPortion(self, times):
		for i in times:
			times[i] /= 24.0
		return times

	
	#---------------------- Misc Functions -----------------------

	# compute the difference between two times
	def timeDiff(self, time1, time2):
		return self.fixhour(time2- time1)

	# convert given string into a number
	def eval(self, st):
		val = re.split('[^0-9.+-]', str(st), 1)[0]
		return float(val) if val else 0

	# detect if input contains 'min'
	def isMin(self, arg):
		return isinstance(arg, str) and arg.find('min') > -1


	#----------------- Degree-Based Math Functions -------------------

	def sin(self, d): return math.sin(math.radians(d))
	def cos(self, d): return math.cos(math.radians(d))
	def tan(self, d): return math.tan(math.radians(d))

	def arcsin(self, x): return math.degrees(math.asin(x))
	def arccos(self, x): return math.degrees(math.acos(x))
	def arctan(self, x): return math.degrees(math.atan(x))

	def arccot(self, x): return math.degrees(math.atan(1.0/x))
	def arctan2(self, y, x): return math.degrees(math.atan2(y, x))

	def fixangle(self, angle): return self.fix(angle, 360.0)
	def fixhour(self, hour): return self.fix(hour, 24.0)

	def fix(self, a, mode):
		if math.isnan(a):
			return a
		a = a - mode * (math.floor(a / mode))
		return a + mode if a < 0 else a

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
