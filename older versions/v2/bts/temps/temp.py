from astropy.coordinates import EarthLocation
from astropy.time import Time
from astropy import units as u
import datetime

observing_location = EarthLocation(lat=46.57*u.deg, lon=7.65*u.deg)
observing_time = Time(datetime.datetime.now(), scale='utc', location=observing_location)

LST = observing_time.sidereal_time('mean')
print(LST)

LaT = observing_time.sidereal_time('apparent')
print(LaT)
