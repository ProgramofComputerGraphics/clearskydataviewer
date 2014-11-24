# angle_utilities.py
# Provides functionality to convert between UV coordinates and angles as well
#   as other useful angle utilities. 
#
#  Copyright 2014-2015 Program of Computer Graphics, Cornell University
#     580 Rhodes Hall
#     Cornell University
#     Ithaca NY 14853
#  Web: http://www.graphics.cornell.edu/
#
#  Not for commercial use. Do not redistribute without permission.
#

__all__ = ['GetUVFromAngles', 'CalculateSunAngles', 'FisheyeAngleWarp', 'GetAngleFromUV', 'PlotSamplePath']

import math
from datetime import time, timedelta, datetime

EARTH_MEAN_RADIUS = 6371.01 # In km
ASTRONOMICAL_UNIT = 149597890 # In km

def FisheyeAngleWarp(theta, phi, inRadians=True):
    """ Take in a pair of angles and return the corresponding angles on the 
          fisheye image taking into account the position of North, etc.
    """
    if inRadians:
        phi = phi * 180.0 / math.pi
        theta = theta * 180.0 / math.pi

    # Theta is azimuth, with north being directly down. 
    theta = 360 - ((theta + 270) % 360)
    phi = 90 - phi

    if inRadians:
        phi = phi * math.pi / 180.0
        theta = theta * math.pi / 180.0

    return (theta, phi)

def GetAngleFromUV(x, y):
    """ Given the x, y fractional coordinates of a point in an image, return the
          angles corresponding to this location in degrees. 
    """
    radius = math.sqrt((x-0.5) * (x - 0.5) + (y - 0.5) * (y-0.5))
    x = x - 0.5
    y = y - 0.5
    theta = math.atan2(x, y)
    phi = radius * math.pi / 2.0

    return (int((theta * 180.0 / math.pi + 360) % 360), int(90 - 2 * phi * 180.0 / math.pi))

def GetUVFromAngle(theta, phi, inRadians=True):
    """ Get the UV coordinates for a pair of angles representing position
          on a fisheye hemisphere image.
    """
    if not inRadians:
        phi = phi * math.pi / 180.0
        theta = theta * math.pi / 180.0

    radius = phi / (math.pi / 2.0)
    return (0.5 * (radius * math.cos(theta) + 1), 0.5 * (radius * math.sin(theta) + 1))

def CalculateSunAngles(time, coord):
    """ Calculate the angles representing the position of the sun based on a 
          provided time and coordinates. 
    """
    # Calculate difference in days of Julian Days
    decHours = time.hour + (time.minute + time.second / 60.0) / 60.0
    liAux1 = (time.month - 14) / 12
    liAux2 = (1461*(time.year + 4800 + liAux1)) / 4 + (367 * (time.month - 2 - 12 * liAux1)) / 12 - (3*((time.year + 4900 + liAux1) / 100)) / 4 + time.day - 32075
    julianDate = liAux2 - 0.5 + decHours / 24.0
    elapsedJulianDays =julianDate - 2451545.0

    # Calculate ecliptic coordinates 
    omega = 2.1429 - 0.0010394594 * elapsedJulianDays
    meanLongitude = 4.8950630 + 0.017202791698 * elapsedJulianDays
    anomaly = 6.2400600 + 0.0172019699 * elapsedJulianDays;
    eclipticLongitude = meanLongitude + 0.03341607 * math.sin(anomaly) + 0.00034894 * math.sin(2*anomaly) - 0.0001134 - 0.0000203 * math.sin(omega)
    eclipticObliquity = 0.4090928 - 6.2140e-9 * elapsedJulianDays + 0.0000396 * math.cos(omega);

    # Calculate celestial coordinates
    sinEclipticLongitude = math.sin(eclipticLongitude)
    dY = math.cos(eclipticObliquity) * sinEclipticLongitude;
    dX = math.cos(eclipticLongitude)
    rightAscension = math.atan2(dY, dX);
    declination = math.asin(math.sin(eclipticObliquity) * sinEclipticLongitude)

    # Calculate local coordinates
    greenwichMeanSiderealTime = 6.6974243242 + 0.0657098283 * elapsedJulianDays + decHours
    localMeanSiderealTime = (greenwichMeanSiderealTime * 15 + coord['longitude']) * math.pi / 180.0;

    latitudeInRadians = coord['latitude'] * math.pi / 180.0
    cosLatitude = math.cos(latitudeInRadians)
    sinLatitude = math.sin(latitudeInRadians)
    hourAngle = localMeanSiderealTime - rightAscension
    cosHourAngle = math.cos(hourAngle)
    elevation = math.acos(cosLatitude * cosHourAngle * math.cos(declination) + math.sin(declination) * sinLatitude)
    dY = -math.sin(hourAngle)
    dX = math.tan(declination) * cosLatitude - sinLatitude * cosHourAngle
    azimuth = math.atan2(dY, dX)
    if azimuth < 0.0:
        azimuth = azimuth + 2 * math.pi

    elevation = elevation + (EARTH_MEAN_RADIUS / ASTRONOMICAL_UNIT) * math.sin(elevation)

    return (azimuth, math.pi / 2.0 - elevation)

