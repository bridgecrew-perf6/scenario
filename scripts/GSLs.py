
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
import time
document_template ={
        "id": "document",
        "version": "1.0"
    }
GSLs_template = {
        "id":"GSLs",
        "name":"GSLs",
        "description":"collection of GSs",
        "parent": "root"

}


class GSL:
    def __init__(self,id=None,description=None,ref=None):
        self.template = {
            "id": "none",
            "name": "none",
            "parent": "GSLs",
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
                                0,
                                0,
                                255,
                                255
                            ]
                        },
                        "gapColor":{
                            "rgba":[
                                255,
                                0,
                                0,
                                0
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
    GSs_path = dump_path/"lite_gss.czml"
    multiThreading=config['GSL']['multiThreading']
    print("\nGENERATING GSLs...")
    sats = json2dict(SATs_path)
    gss = json2dict(GSs_path)

    # get sats and gss
    for i in range(len(sats)):
        if 'parent' in sats[i].keys() and sats[i]['parent']=='SATs':
            pass
        else:
            sats[i] = -1
    for i in range(len(gss)):
        if 'parent' in gss[i].keys() and gss[i]['parent'] == 'GSs':
            pass
        else:
            gss[i]=-1
    while -1 in sats:
        sats.remove(-1)
    while -1 in gss:
        gss.remove(-1)

    print("-> sats:{}, gss:{}".format(len(sats),len(gss)))

    print("-> stamps loging")
    access_stamps={}
    if multiThreading:
        # multi-threading
        input_item_len = config['GSL']['input_item_len']

        ts=[]
        t1 = time.perf_counter()

        input_list = input_split(sats,input_item_len)
        num_sub_task = len(input_list)
        for input_item in input_list:
            # acc.sat_with_gss(sat,gss)
            ts.append( threading.Thread(target=sub_task,args=(input_item,gss,access_stamps)))

        for t in ts:
            t.start()

        # for t in tqdm(ts):
        print('-> waiting',end='')

        while task_over_cnt < num_sub_task:
            print('.',end='')

            time.sleep(3)
        t2=time.perf_counter()

    else:
        t1 = time.perf_counter()

        acc = Access()
        for sat in sats:
            acc.sat_with_gss(sat,gss)

        access_stamps = acc.get_access_stamp()

        t2 = time.perf_counter()


    print('\n-> log over,{:.2f} sec'.format(t2 - t1))

    # print("-> total {} stamp pair".format(len(access_stamps)))

    # write
    print("-> stamps writing...")


    GSLs=[]
    GSLs.append(document_template)
    GSLs.append(GSLs_template)

    start_stamp = datetime.datetime.strptime(config['start_time'], '%Y-%m-%dT%H:%M:%SZ').timestamp()
    end_stamp = datetime.datetime.strptime(config['end_time'], '%Y-%m-%dT%H:%M:%SZ').timestamp()

    for k,v in access_stamps.items():
        gs,sat = k
        ref = ["{}#position".format(sat), "{}#position".format(gs)]
        name = "GSL-{}-{}".format(sat,gs)
        gsl = GSL(id =name,description=name,ref=ref)
        if gs =='London' and sat =='00200':
            pass
            print('ok')
        pre_stamp = start_stamp

        for start,end in v:
            pre_stamp_utc = datetime.datetime.fromtimestamp(pre_stamp)
            start_utc = datetime.datetime.fromtimestamp(start_stamp+start)
            inteval = "{}T{}Z/{}T{}Z".format(pre_stamp_utc.date(),pre_stamp_utc.time(),start_utc.date(),start_utc.time())
            gsl.add_interval(inteval,False)

            end_utc = datetime.datetime.fromtimestamp(start_stamp+end)
            inteval = "{}T{}Z/{}T{}Z".format(start_utc.date(),start_utc.time(),end_utc.date(),end_utc.time())
            gsl.add_interval(inteval,True)
            # gsl.add_availability(inteval)

            pre_stamp = start_stamp+end
        # add last false
        start_utc = datetime.datetime.fromtimestamp(pre_stamp)
        end_utc = datetime.datetime.fromtimestamp(end_stamp)
        inteval = "{}T{}Z/{}T{}Z".format(start_utc.date(), start_utc.time(), end_utc.date(), end_utc.time())
        gsl.add_interval(inteval, False)


        GSLs.append(gsl.get_item())

    print("-> total {} visible arc segment".format(len(access_stamps)))
    dump_file = "{}_gsl.czml".format(config["constellation"]["name"])
    dict2json(dump_path / dump_file, GSLs)
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