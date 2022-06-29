
from utils.yaml_wrapper import YamlHandler
import argparse
import datetime
import matplotlib.pyplot as plt
import os
from path import Path
from satgen import generate_tles_from_scratch_manual as args2tles
from utils.tool import json2dict,dict2json,to_csv,read_csv
from utils.formatter import cartesian3,lalong_str2num,mid_longlat

document_template ={
        "id": "document",
        "version": "1.0"
    }

ACs_template = {
        "id":"ACs",
        "name":"ACs",
        "description":"collection of AC",
        "parent":"root"
      }

class Aerocraft:
    def __init__(self,id,name,description):

        self.template =   {
        "id": "00000",
        "description": "okk",
        "availability": "2000-01-01T00:00:00+00:00/2000-01-02T00:00:00+00:00",
        "position": {
            "epoch": "2000-01-01T00:00:00+00:00",
            "cartesian":[],
            "interpolationAlgorithm": "LAGRANGE",
            "interpolationDegree": 20,
            "referenceFrame": "FIXED"
        },
        "label": {
            "show": True,
            "text": "00000",
            "horizontalOrigin": "LEFT",
            "pixelOffset": {
                "cartesian2": [
                    12,
                    0
                ]
            },
            "fillColor": {
                "rgba": [
                    197,
                    215,
                    20,
                    255
                ]
            },
            "font": "11pt Lucida Console",
            "outlineColor": {
                "rgba": [
                    0,
                    0,
                    0,
                    255
                ]
            },
            "outlineWidth": 2
        },
        "orientation" : {
            "velocityReference": "#position"
        },
        "model": {
            "gltf":
              "../launchvehicle.glb",
            "scale": 2.0,
            "minimumPixelSize": 128,
            "runAnimations": False
        },
        "path": {
            "show": [
                {
                    "interval": "2000-01-01T00:00:00+00:00/2000-01-02T00:00:00+00:00",
                    "boolean": True
                }
            ],
            "width": 5,
            "resolution": 120,
            "material": {
                 "polylineOutline": {
          "color": {
            "rgba": [255, 0, 255, 255],
          },
          "outlineColor": {
            "rgba": [0, 255, 255, 255],
          },
          "outlineWidth": 5,
            },
        },
        },
        "parent": "ACs"
    }

        self.template["id"] = id
        self.template["name"] = name
        self.template["description"] = description
    def set_position(self,position):
        self.template["position"]["cartesian"] = position
    def set_start_end(self,start_time,end_time):
        self.template['availability']=start_time.isoformat()+"Z"+"/"+end_time.isoformat()+"Z"
        self.template['path']['show'][0]['interval']=start_time.isoformat()+"Z"+"/"+end_time.isoformat()+"Z"
        pass
    def get_item(self):
        return self.template



import numpy as np
def main(args):
    yml = YamlHandler(args.settings)
    config = yml.read_yaml()
    dump_path = Path(config["dump_path"])

    ACs_path = Path(config["root"]) / config['ACs_path']
    print("\nGENERATING ACs...")
    ACs_in = json2dict(ACs_path)

    start_time =datetime.datetime.strptime(config['start_time'], '%Y-%m-%dT%H:%M:%SZ')
    # end_time = datetime.timedelta(seconds=config['duration_sec'])



    ACs = []
    ACs.append(document_template)
    ACs.append(ACs_template)
    for ac in ACs_in:
        duration_sec = ac['duration_sec']
        time_delta = datetime.timedelta(seconds=duration_sec)
        end_time = start_time+time_delta
        time_stamps = np.linspace(start=0,stop=duration_sec,num=len(ac['path']))
        time_pose =[]
        for longlat ,stamp in zip(ac['path'],time_stamps):
            latitude, longitude = lalong_str2num(longlat)
            if stamp==0 or stamp ==duration_sec:
                pos = cartesian3(longitude, latitude,h=0)
            else:
                pos = cartesian3(longitude, latitude,h=100000)

            time_pose.append(stamp)
            time_pose.append(pos[0])
            time_pose.append(pos[1])
            time_pose.append(pos[2])






        name = ac['name']
        description = ac['path'][0]+' -> ' +ac['path'][-1]
        # print(name,cartesian3(longitude, latitude))

        ac = Aerocraft(id=name, name=name, description=description)

        ac.set_position(time_pose)
        ac.set_start_end(start_time,end_time)
        ACs.append(ac.get_item())

    dump_file = "{}_acs.czml".format(config['constellation']['name'])
    dict2json(dump_path / dump_file, ACs)
    print("-> at {}/{}".format(dump_path, dump_file))




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="constellation-information")
    if os.path.exists('../configs/config.yaml'):
        parser.add_argument("--settings", default='../configs/config.yaml')
    else:
        parser.add_argument("--settings", default='./configs/config.yaml')

    args = parser.parse_args()
    main(args)