
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
from utils.formatter import dict2frame
import numpy as np

class ISL:
    def __init__(self,id,name,description,ref):

        self.template = {
        "id":"none",
        "name":"none",
        "availability":[
          "2022-05-27T10:14:19.663460+00:00/2022-05-28T10:14:19.663460+00:00"
        ],
        "description":"none",
        "polyline":{
          "show":[

            {
              "interval":"2022-05-27T10:14:19.663460+00:00/2022-05-28T10:14:19.663460+00:00",
              "boolean":True
            }

          ],
          "width":10,
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
    def get_item(self):
        return self.template

def LoS(sat_id,num_orbit,num_sat):
    los =[]
    shell = sat_id[0]
    orbit= int(sat_id[1:3])
    sat = int(sat_id[3:5])

    sats = [(sat-1)%num_sat,sat,(sat+1)%num_sat]
    orbits = [(orbit-1)%num_orbit,orbit,(orbit+1)%num_orbit]
    for orb in orbits:
        for sat in sats:
            tmp = "{}{:02d}{:02d}".format(shell,orb,sat)
            if tmp !=sat_id:
                los.append(tmp)



    return  los
def last_duration():

    return  [20,50]
def isSameV(sat1,sat2,duration):

    pass

positions={}
def distance(sat1,sat2,duration):
    sat1_position = positions[sat1][duration[0]:duration[1]][:,1:]
    sat2_position = positions[sat2][duration[0]:duration[1]][:,1:]
    avg_dis = np.abs(sat1_position-sat2_position)**2
    avg_dis = avg_dis.sum(1).mean()
    return avg_dis

def makeISLs(sat,num_orbit,num_sat):
    num_ISLs_per_sat=4
    duration = last_duration()
    satsInLoS = LoS(sat, num_orbit, num_sat)

    dises ={}
    for adj in satsInLoS:
        dises[adj] = distance(sat,adj,duration)
    ret = sorted(dises, key=lambda k: dises[k])
    return ret[:num_ISLs_per_sat]


def main(args):
    global positions
    yml = YamlHandler(args.settings)
    config = yml.read_yaml()
    constellation = config['constellation']
    num_orbit= constellation['num_orbits']
    num_sat = constellation['num_sats_per_orbit']
    file = "../tmp/{}.czml".format(constellation['name'])
    czml = json2dict(file)
    czml_dict={}
    for item in czml:
        if item['id'] == 'document':
            continue
        czml_dict[item['id']] = item
    positions = dict2frame(czml_dict)

    sats = list(positions.keys())

    adj_mat=set()
    for sat in sats:
        ISLs = makeISLs(sat,num_orbit,num_sat)
        for adj_sat in ISLs:
            if (sat,adj_sat) in adj_mat or (adj_sat,sat) in adj_mat:
                continue
            adj_mat.add((sat, adj_sat))

    czml_format=[]


    for (sati,satj) in adj_mat:
        name = "ISL-{}-{}".format(sati,satj)
        id = "ISL-{}-{}".format(sati,satj)
        description = "ISL-{}-{}".format(sati,satj)
        ref = ["{}#position".format(sati),"{}#position".format(satj)]

        isl = ISL(name=name,id=id,description=description,ref=ref)

        czml_format.append(isl.get_item())


    dict2json("../tmp/tmp.czml",czml_format)
    print('isl ok')




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="constellation-information")
    if os.path.exists('../configs/config.yaml'):
        parser.add_argument("--settings", default='../configs/config.yaml')
    else:
        parser.add_argument("--settings", default='./configs/config.yaml')

    args = parser.parse_args()
    main(args)