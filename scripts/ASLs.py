
from utils.yaml_wrapper import YamlHandler
import argparse
import datetime
import matplotlib.pyplot as plt
from tqdm import tqdm
import os
from path import Path
from satgen import generate_tles_from_scratch_manual as args2tles
from utils.tool import json2dict,dict2json,to_csv,read_csv
from satellite_czml import SatelliteCzml
from utils.tool import readtles,list_filter
from analysis.access import Access
import threading
from threading import Condition
import numpy as np
import time
document_template ={
        "id": "document",
        "version": "1.0"
    }
ASLs_template = {
        "id":"ASLs",
        "name":"ASLs",
        "description":"collection of ASLs",
        "parent": "root"

}


class ASL:
    def __init__(self,id=None,description=None,ref=None):
        self.template = {
            "id": "none",
            "name": "none",
            "parent": "ASLs",
            "availability": [],
            "description": None,
            "polyline": {
                "show": [
                    {
                        "interval": None,
                        "boolean": True
                    }
                ],
                "width": 2,
                "material": {
                    "polylineDash": {
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
                "positions": {
                    "references": [
                        None,
                        None

                    ]
                }
            }
        }
        self.template['polyline']['show']=[]
        self.template['id']=id
        self.template['description']=description
        self.template["polyline"]["positions"]["references"] = ref

    def add_interval(self,str,tf=True):
        self.template['polyline']['show'].append(
            {
                "interval": str,
                "boolean":tf
            }
        )
    def get_item(self):
        return self.template
    def add_availability(self,interval):
        self.template['availability'].append(interval)

task_over_cnt=0
def sub_task(sats,gss,acc_stamps):
    global task_over_cnt
    acc = Access()

    for sat in sats:
        acc.sat_with_gss(sat,gss)
    acc_stamps.update(acc.get_access_stamp())
    task_over_cnt+=1



def input_split(sats,sub_sats_len):
    nums_sub = int(len(sats) / sub_sats_len)
    i = 0
    split_sats = []
    start = 0
    while i <= nums_sub:
        split_sats.append(sats[start:start+sub_sats_len])
        start+=sub_sats_len
        i+=1
    return split_sats

def main(args):
    global task_over_cnt
    yml = YamlHandler(args.settings)
    config = yml.read_yaml()
    dump_path = Path(config["dump_path"])
    SATs_path = dump_path/"lite_const.czml"
    ACs_path = dump_path/"lite_acs.czml"
    multiThreading=config['GSL']['multiThreading']
    print("\nGENERATING ASLs...")

    # get sats and acs from czml

    sats = json2dict(SATs_path)
    acs = json2dict(ACs_path)
    for i in range(len(sats)):
        if 'parent' in sats[i].keys() and sats[i]['parent']=='SATs':
            pass
        else:
            sats[i] = -1
    for i in range(len(acs)):
        if 'parent' in acs[i].keys() and acs[i]['parent'] == 'ACs':
            pass
        else:
            acs[i]=-1
    while -1 in sats:
        sats.remove(-1)
    while -1 in acs:
        acs.remove(-1)

    print("--> sats:{}, acs:{}".format(len(sats),len(acs)))

    print("-> stamps loging")
    access_stamps={}

    t1 = time.perf_counter()
    borderDistance = 400000/np.cos(np.deg2rad(50)) #sat 500- ac 100 = 400
    acc = Access(borderDistance=borderDistance)
    for sat in sats:
        acc.sat_with_acs(sat,acs)

    access_stamps = acc.get_access_stamp()
    t2 = time.perf_counter()


    print('\n-> log over,{:.2f} sec'.format(t2 - t1))

    # print("-> total {} stamp pair".format(len(access_stamps)))

    # write
    print("-> stamps writing...")


    ASLs=[]
    ASLs.append(document_template)
    ASLs.append(ASLs_template)

    start_stamp = datetime.datetime.strptime(config['start_time'], '%Y-%m-%dT%H:%M:%SZ').timestamp()
    end_stamp = datetime.datetime.strptime(config['end_time'], '%Y-%m-%dT%H:%M:%SZ').timestamp()

    for k,v in access_stamps.items():
        ac,sat = k
        ref = ["{}#position".format(sat), "{}#position".format(ac)]
        name = "ASL-{}-{}".format(sat,ac)
        asl = ASL(id =name,description=name,ref=ref)

        pre_stamp = start_stamp

        for start,end in v:
            pre_stamp_utc = datetime.datetime.fromtimestamp(pre_stamp)
            start_utc = datetime.datetime.fromtimestamp(start_stamp+start)
            inteval = "{}T{}Z/{}T{}Z".format(pre_stamp_utc.date(),pre_stamp_utc.time(),start_utc.date(),start_utc.time())
            asl.add_interval(inteval,False)

            end_utc = datetime.datetime.fromtimestamp(start_stamp+end)
            inteval = "{}T{}Z/{}T{}Z".format(start_utc.date(),start_utc.time(),end_utc.date(),end_utc.time())
            asl.add_interval(inteval,True)
            # gsl.add_availability(inteval)

            pre_stamp = start_stamp+end
        # add last false
        start_utc = datetime.datetime.fromtimestamp(pre_stamp)
        end_utc = datetime.datetime.fromtimestamp(end_stamp)
        inteval = "{}T{}Z/{}T{}Z".format(start_utc.date(), start_utc.time(), end_utc.date(), end_utc.time())
        asl.add_interval(inteval, False)


        ASLs.append(asl.get_item())

    print("-> total {} visible arc segment".format(len(access_stamps)))
    dump_file = "{}_asl.czml".format(config["constellation"]["name"])
    dict2json(dump_path / dump_file, ASLs)
    print("-> at {}/{}".format(dump_path, dump_file))

    # build gsls


    print('ok')









if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="constellation-information")
    if os.path.exists('../configs/config.yaml'):
        parser.add_argument("--settings", default='../configs/config.yaml')
    else:
        parser.add_argument("--settings", default='./configs/config.yaml')

    args = parser.parse_args()
    main(args)