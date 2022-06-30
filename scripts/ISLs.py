
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

ISLs_template = {
        "id":"ISLs",
        "name":"ISLs",
        "description":"collection of ISL",
        "parent":"root"
      }
InterOrbitLinks_template = {
    "id": "InterOrbitLinks",
    "name": "InterOrbitLinks",
    "description": "collection of InterOrbitLinks",
    "parent": "ISLs"

}
IntraOrbitLinks_template={
    "parent": "ISLs",
    "id": "IntraOrbitLinks",
    "name": "IntraOrbitLinks",
    "description": "collection of IntraOrbitLinks",
}

class ISL:
    def __init__(self,id,name,description,ref):

        self.template = {
        "id":"none",
        "name":"none",
        "parent":"IntraOrbitLinks",
        "availability":None,
        "description":None,
        "polyline":{
          "show":[

            {
              "interval":None,
              "boolean":True
            }

          ],
          "width":2,
          "material":{
              "polylineGlow": {
                  " glowPower": 0.2,
                  "taperPower": 1,
                  "color": {
                      "rgba": [
                          0,
                          255,
                          255,
                          255
                      ]
                  }
              }
          },
          "arcType":"NONE",
          "positions":{
            "references":[
              "none","none"
            ]
          }
        }
      }

        self.template["id"] = id
        self.template["name"] = name
        self.template["description"] = description
        self.template["polyline"]["positions"]["references"] = ref
    def setParent(self):
        self.template["parent"] = "InterOrbitLinks"
    def setLine(self,rgba=None):
        if not rgba:
            # self.template["polyline"]["material"]["polylineGlow"]["color"]["rgba"] = [255,0,0,255]
            self.template["polyline"]["material"]["solidColor"]={}
            self.template["polyline"]["material"]["solidColor"]["color"]={}
            self.template["polyline"]["material"]["solidColor"]["color"]["rgba"] = [0,255,0,255]
            self.template["polyline"]["width"] = 1

        else:
            self.template["polyline"]["material"]["polylineGlow"]["color"]["rgba"] = rgba

    def setTime(self,start_time,end_time):
        interval = start_time.isoformat()+"Z" + "/" + end_time.isoformat()+"Z"

        self.template["availability"]=[interval]
        self.template["polyline"]["show"][0]["interval"] = interval
    def get_item(self):
        return self.template





def adjacent_sats(sat,num_orbit,num_sat,inter_link_deltas,intral_link_deltas):
    intral_link_deltas = intral_link_deltas
    shell_no = int(sat[0])
    this_orbit_no = int(sat[1:3])
    this_sat_no = int(sat[3:5])


    adj_intral_orbit_sat_no = []
    adj_inter_orbit_sat_no = []
    for delta in intral_link_deltas:
        adj_intral_orbit_sat_no.append((delta+this_sat_no)%num_sat)
    for delta in inter_link_deltas:
        adj_inter_orbit_sat_no.append((delta + this_sat_no)%num_sat)

    next_orbit_no = (this_orbit_no+1)%num_orbit
    adj_sats = []
    for no in adj_intral_orbit_sat_no:
        adj_sats.append("{:01d}{:02d}{:02d}".format(shell_no,this_orbit_no,no))
    
    for no in adj_inter_orbit_sat_no:
        adj_sats.append("{:01d}{:02d}{:02d}".format(shell_no,next_orbit_no,no))
    return adj_sats


def main(args):
    global positions
    yml = YamlHandler(args.settings)
    config = yml.read_yaml()
    dump_path = Path(config["dump_path"])
    constellation = config['constellation']
    num_orbit= constellation['num_orbits']
    num_sat = constellation['num_sats_per_orbit']

    intral_link_deltas = config['ISL']['intral_link_deltas']
    inter_link_deltas = config['ISL']['inter_link_deltas']


    start_time = datetime.datetime.strptime(config['start_time'], '%Y-%m-%dT%H:%M:%SZ')
    end_time = datetime.datetime.strptime(config['end_time'], '%Y-%m-%dT%H:%M:%SZ')

    print("\nGENERATES ISLs...")
    inFile = Path(dump_path)/"{}_const.czml".format(constellation['name'])

    side_link = [0]
    czml = json2dict(inFile)
    czml_dict={}
    for item in czml:
        if 'parent' in item.keys() and item['parent'] == 'SATs':
            czml_dict[item['id']] = item
    positions = getCoord(czml_dict)

    sats = list(positions.keys())

    adj_mat=set()
    for sat in sats:
        adj_sats = adjacent_sats(sat,num_orbit,num_sat,inter_link_deltas=inter_link_deltas,intral_link_deltas=intral_link_deltas)
        for adj_sat in adj_sats:
            if (sat,adj_sat) in adj_mat or (adj_sat,sat) in adj_mat:
                continue
            adj_mat.add((sat, adj_sat))

    ISLs_list=[]
    ISLs_list.append(document_template)
    ISLs_list.append(ISLs_template)
    ISLs_list.append(IntraOrbitLinks_template)
    ISLs_list.append(InterOrbitLinks_template)


# construct ISLs file
    intralCnt=0
    for (sati,satj) in adj_mat:
        name = "ISL-{}-{}".format(sati,satj)
        id = "ISL-{}-{}".format(sati,satj)
        description = "ISL-{}-{}".format(sati,satj)
        ref = ["{}#position".format(sati),"{}#position".format(satj)]

        isl = ISL(name=name,id=id,description=description,ref=ref)
        if sati[1:3] != satj[1:3]:# not in same orbit
            isl.setLine()
            isl.setParent()
            intralCnt+=1
        isl.setTime(start_time,end_time)
        ISLs_list.append(isl.get_item())
    print("number of ISLs, intral:{}, inter:{}, total:{}".format(intralCnt,len(ISLs_list)-intralCnt,len(ISLs_list)))
    dump_file = "{}_isl.czml".format(constellation["name"])
    dict2json(dump_path/dump_file,ISLs_list)
    print("--> at {}/{}".format(dump_path,dump_file))





if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="constellation-information")
    if os.path.exists('../configs/config.yaml'):
        parser.add_argument("--settings", default='../configs/config.yaml')
    else:
        parser.add_argument("--settings", default='./configs/config.yaml')

    args = parser.parse_args()
    main(args)