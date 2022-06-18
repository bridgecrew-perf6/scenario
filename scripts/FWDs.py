
from utils.yaml_wrapper import YamlHandler
import argparse
import datetime
import matplotlib.pyplot as plt
import os
from path import Path
from satgen import generate_tles_from_scratch_manual as args2tles
from utils.tool import json2dict,dict2json,to_csv,read_csv
from satellite_czml import SatelliteCzml
from utils.tool import readtles,list_filter
from utils.formatter import getCoord
import numpy as np


document_template ={
        "id": "document",
        "version": "1.0"
    }
FWDs_template = {
        "id":"FWDs",
        "name":"FWDs",
        "description":"collection of FWD",
        "parent": "root"

}
class Forwarding:
    def __init__(self,id,name,description,ref):

        self.template = {
            "id": None,
            "name": None,
            "parent":"FWDs",
            "availability": None,
            "description": None,
            "polyline": {
                "show": [
                    {
                        "interval": None,
                        "boolean": True
                    }
                ],
                "width": 10,
                "material": {
                    "polylineArrow": {
                        "color": {
                            "rgba": [
                                255,
                                0,
                                0,
                                255
                            ]
                        }
                    }
                },
                "arcType": "LOXODROME",
                "positions": {
                    "references": [
                        None,
                        None

                    ]
                }
            }
        }

        self.template["id"] = id
        self.template["name"] = name
        self.template["description"] = description
        self.template["polyline"]["positions"]["references"] = ref
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
    constellation = config['constellation']

    start_time = datetime.datetime(*config["start_time"])
    end_time = datetime.datetime(*config["end_time"])

    print("\nGENERATING FWDs...")
    inFile = Path(dump_path)/"{}_isl.czml".format(constellation['name'])


    czml_list = json2dict(inFile)
    czml_dict={}
    for item in czml_list:
        if item['id'] == 'document':
            continue
        czml_dict[item['id']] = item
    FWDs =[]
    FWDs.append(document_template)
    FWDs.append(FWDs_template)
    id_set = set()
    for item in czml_list:

        if item['id'][0:3]=="ISL" and item['id'][0:4]!='ISLs':
            sati = item['id'][4:9]
            satj = item['id'][10:15]
            fwd_id = "FWD-{}-{}".format(sati,satj)
            if fwd_id not in id_set:
                ref = ["{}#position".format(sati), "{}#position".format(satj)]
                fwd = Forwarding(id=fwd_id, description= fwd_id,ref=ref,name=fwd_id)
                fwd.setTime(start_time,end_time)
                FWDs.append(fwd.get_item())


            fwd_id = "FWD-{}-{}".format(satj,sati)
            if fwd_id not in id_set:

                ref = ["{}#position".format(satj), "{}#position".format(sati)]
                fwd = Forwarding(id=fwd_id, description=fwd_id, ref=ref, name=fwd_id)
                fwd.setTime(start_time, end_time)
                FWDs.append(fwd.get_item())

    dump_file = "{}_fwd.czml".format(constellation["name"])
    dict2json(dump_path/dump_file,FWDs)
    print("--> at {}/{}".format(dump_path,dump_file))





if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="constellation-information")
    if os.path.exists('../configs/config.yaml'):
        parser.add_argument("--settings", default='../configs/config.yaml')
    else:
        parser.add_argument("--settings", default='./configs/config.yaml')

    args = parser.parse_args()
    main(args)