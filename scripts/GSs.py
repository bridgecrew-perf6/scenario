
from utils.yaml_wrapper import YamlHandler
import argparse
import datetime
import matplotlib.pyplot as plt
import os
from path import Path
from utils.tool import readlines,dict2json
import math

document_template ={
        "id": "document",
        "version": "1.0"
    }
GSs_template = {
        "id":"GSs",
        "name":"GSs",
        "description":"collection of GSs",
        "parent": "root"

}
class GroundStation:
    def __init__(self,id,name,description):


        self.template = {
            "id": None,
            "name": None,
            "parent":"GSs",
            "availability": None,
            "description": None,
            "label": {
                "fillColor": {
                    "rgba": [
                        0, 255, 255, 255
                    ]
                },
                "font": "11pt Lucida Console",
                "horizontalOrigin": "LEFT",
                "outlineColor": {
                    "rgba": [
                        0, 0, 0, 255
                    ]
                },
                "outlineWidth": 2,
                "pixelOffset": {
                    "cartesian2": [
                        12, 0
                    ]
                },
                "show": True,
                "style": "FILL_AND_OUTLINE",
                "text": "AGI",
                "verticalOrigin": "CENTER"
            },
            "position":{
                "cartesian": None
            }
            ,
            "cylinder":{
                "length": 400000.0,
                "topRadius": 0.0,
                "bottomRadius": 100000.0,
                "material": {

                    "solidColor": {
                        "color": {
                            "rgba": [255, 0, 0, 255],
                        },

                    }
                }
            }

        }

        self.template["id"] = id
        self.template["name"] = name
        self.template["description"] = description

    def setPos(self,cartesian):
        self.template['position']['cartesian'] = cartesian
    def setLabel(self,text):
        self.template['label']['text'] = text
    def setTime(self,start_time,end_time):
        interval = start_time.isoformat() + "/" + end_time.isoformat()

        self.template["availability"]=[interval]
        self.template["polyline"]["show"][0]["interval"] = interval
    def get_item(self):
        return self.template



def main(args):
    global positions
    yml = YamlHandler(args.settings)
    config = yml.read_yaml()
    dump_path = Path(config["dump_path"])

    GSs_in = Path(config["GSs"]["path"])

    print("\nGENERATES GSs...")

    lines = readlines(GSs_in)
    GSs=[]
    GSs.append(document_template)
    GSs.append(GSs_template)
    for line in lines:
        name,location = line.split('\t')
        latitude ,longitude= location.split(',')
        if longitude[-1]=='E':
            longitude = float(longitude[:-1])
        elif longitude[-1]=='W':
            longitude = -float(longitude[:-1])

        if latitude[-1]=='N':
            latitude = float(latitude[:-1])
        elif latitude[-1]=='S':
            latitude = -float(latitude[:-1])


        pos= cartesian3(longitude, latitude)
        # print(name,cartesian3(longitude, latitude))

        gs = GroundStation(id = name,name=name,description=location)
        gs.setPos(list(pos))
        gs.setLabel(name)
        GSs.append(gs.get_item())

    dump_file = "{}_gss.czml".format(config['constellation']['name'])
    dict2json(dump_path / dump_file, GSs)
    print("--> at {}/{}".format(dump_path, dump_file))


def cartesian3(longitude,latitude):
    longitude = math.radians(longitude)
    latitude = math.radians(latitude)


    R = 6378137.0   # relative to centre of the earth
    X = R * math.cos(latitude) * math.cos(longitude)
    Y = R * math.cos(latitude) * math.sin(longitude)
    Z = R * math.sin(latitude)
    return  [X,Y,Z]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="constellation-information")
    if os.path.exists('../configs/config.yaml'):
        parser.add_argument("--settings", default='../configs/config.yaml')
    else:
        parser.add_argument("--settings", default='./configs/config.yaml')

    args = parser.parse_args()
    main(args)