import numpy as np
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


