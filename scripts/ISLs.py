
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



def sameOrbitSats(sat_id,num_orbit,num_sat):
    same_orbit_sats=[]
    sat = int(sat_id[3:5])
    orbit= int(sat_id[1:3])
    shell=0

    sats = [(sat - 1) % num_sat, (sat + 1) % num_sat]
    orbits = [orbit]

    for orb in orbits:
        for sat in sats:
            tmp = "{}{:02d}{:02d}".format(shell, orb, sat)
            same_orbit_sats.append(tmp)


    return same_orbit_sats


def sideSats(sat_id,num_orbit,num_sat):
    side_sats=[]
    orbit = int(sat_id[1:3])
    shell = 0
    sats = list(range(0, num_sat))
    # sats = [(sat-1)%num_sat,sat,(sat+1)%num_sat]

    orbits = [(orbit - 1) % num_orbit,  (orbit + 1) % num_orbit]
    for orb in orbits:
        for sat in sats:
            tmp = "{}{:02d}{:02d}".format(shell, orb, sat)
            side_sats.append(tmp)

    return side_sats


def cadidate_sats(sat_id,num_orbit,num_sat):
    "based on name search, only works for 0 phase factor constellation"
    los =[]
    shell = sat_id[0]
    orbit= int(sat_id[1:3])
    sat = int(sat_id[3:5])

    # sats = [(sat-1)%num_sat,sat,(sat+1)%num_sat]
    sats = list(range(0,num_sat))
    orbits = [(orbit-1)%num_orbit,orbit,(orbit+1)%num_orbit]
    for orb in orbits:
        for sat in sats:
            tmp = "{}{:02d}{:02d}".format(shell,orb,sat)
            if tmp !=sat_id:
                los.append(tmp)

    return  los

def LoS_rel(sat_id):
    pass

def last_duration():

    return  [20,50]

positions={}
def distance(sat1,sat2,duration):
    sat1_position = positions[sat1][duration[0]:duration[1]][:,1:]
    sat2_position = positions[sat2][duration[0]:duration[1]][:,1:]
    avg_dis = np.abs(sat1_position-sat2_position)**2
    avg_dis = avg_dis.sum(1).mean()
    return avg_dis


def makeISLs(sat,num_orbit,num_sat,num_ISLs):
    duration = last_duration()


    same_orbit_sats = sameOrbitSats(sat,num_orbit,num_sat)
    side_sats = sideSats(sat,num_orbit,num_sat)


    dises ={}
    for adj in side_sats:
        dises[adj] = distance(sat,adj,duration)
    adjs = sorted(dises, key=lambda k: dises[k])

    if num_ISLs ==4:
        return same_orbit_sats+adjs[:2]
    elif num_ISLs ==6:
        return same_orbit_sats+adjs[:4]

def crossed(sat,adjs):
    "based on name search, only works for 0 phase factor constellation"
    mask =[]

    for item in adjs:
        # same orbit
        if sat[1:3] == item[1:3]:
            mask.append(True)
        #nearly side link
        elif sat[-2:] ==item[-2:]:
            mask.append(True)
        else:
            mask.append(False)


    return list(np.array(adjs)[np.array(mask)])

def isIntraOrbit(sati,satj):
    if sati[1:3] == satj[1:3]:
        return True
    else:
        return False
def isInterSide(sati,satj):
    if sati[-2:] == satj[-2:]:
        return True
    else:
        return False
def notInterSide(sati,satj):
    if sati[-2:] != satj[-2:] and  sati[1:3] != satj[1:3]:
        return True
    else:
        return False


def main(args):
    global positions
    yml = YamlHandler(args.settings)
    config = yml.read_yaml()
    dump_path = Path(config["dump_path"])
    constellation = config['constellation']
    num_orbit= constellation['num_orbits']
    num_sat = constellation['num_sats_per_orbit']
    num_ISLs = config['num_ISLs']

    start_time = datetime.datetime.strptime(config['start_time'], '%Y-%m-%dT%H:%M:%SZ')
    end_time = datetime.datetime.strptime(config['end_time'], '%Y-%m-%dT%H:%M:%SZ')

    print("\nGENERATES ISLs...")
    inFile = Path(dump_path)/"{}_const.czml".format(constellation['name'])


    czml = json2dict(inFile)
    czml_dict={}
    for item in czml:
        if 'parent' in item.keys() and item['parent'] == 'SATs':
            czml_dict[item['id']] = item
    positions = getCoord(czml_dict)

    sats = list(positions.keys())

    adj_mat=set()
    for sat in sats:
        ISLs = makeISLs(sat,num_orbit,num_sat,num_ISLs)
        for adj_sat in ISLs:
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
        if not isIntraOrbit(sati,satj):
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