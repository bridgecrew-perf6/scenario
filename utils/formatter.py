import numpy as np
import math
def getCoord(czml_dict):
    frame = {}
    for k,v in czml_dict.items():
        positions = v['position']['cartesian']
        if len(positions)%4 !=0:
            print('error in sat {}'.format(k))
            continue
        coor_len = int(len(positions)/4)


        positions= np.array(positions).reshape([coor_len,4])
        frame[k] = positions
    return frame


def tle2description(tle):
    temp = "<!--HTML--> <ul> <li>{}</li> <li>{}</li> </ul>".format(tle[0][1:],tle[1][1:])
    return temp
def cartesian3(longitude,latitude,h=0):
    longitude = math.radians(longitude)
    latitude = math.radians(latitude)


    R = 6378137.0 +h  # relative to centre of the earth
    X = R * math.cos(latitude) * math.cos(longitude)
    Y = R * math.cos(latitude) * math.sin(longitude)
    Z = R * math.sin(latitude)
    return  [X,Y,Z]

def lalong_str2num(lalong_str):
    la_str, long_str = lalong_str.split(',')
    longitude=None
    latitude=None
    if long_str[-1] == 'E':
        longitude = float(long_str[:-1])
    elif long_str[-1] == 'W':
        longitude = -float(long_str[:-1])

    if la_str[-1] == 'N':
        latitude = float(la_str[:-1])
    elif la_str[-1] == 'S':
        latitude = -float(la_str[:-1])

    return latitude,longitude

def mid_longlat(oneLon, oneLat, twoLon, twoLat):
    # oneLon：第一个点的经度；oneLat：第一个点的纬度；twoLon：第二个点的经度；twoLat：第二个点的纬度；
    bLon = float(oneLon) - float(twoLon)
    bLat = float(oneLat) - float(twoLat)
    # //Math.abs()绝对值
    if bLon > 0:
        aLon = float(oneLon) - abs(bLon) / 2
    else:
        aLon = float(twoLon) - abs(bLon) / 2

    if bLat > 0:
        aLat = float(oneLat) - abs(bLat) / 2
    else:
        aLat = float(twoLat) - abs(bLat) / 2

    return aLon, aLat