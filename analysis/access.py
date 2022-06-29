'''
Author: Wang Xt
implement association between satellite and ground-station/aerocraft.
The code is a little bit of shit mountain, but works fine. Hope improve it later.
'''


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d as interp
from tqdm import tqdm

import datetime

class Access:
    def __init__(self,borderDistance=None,timeStamps=None):
        if timeStamps:
            self.timeStamps= timeStamps
        else:
            self.timeStamps = np.linspace(start=0,stop=87600,num=293)

        if borderDistance:
            self.borderDistance = borderDistance
        else:
            self.borderDistance = 500000/np.cos(np.deg2rad(50))# 500km high, 40d evelation of sat



        self.df = pd.DataFrame(index=self.timeStamps)
        self.ranges={}
        self.sat_funcs={}
        self.gs_funcs={}
        self.access_stamp={}
    def load_sat(self,sat):
        position = sat['position']['cartesian']
        sat_position = np.array(position).reshape([293,4])#292 x 300 = 87600


        self.sat_fx = interp(self.timeStamps, sat_position[:,1], 'cubic')
        self.sat_fy = interp(self.timeStamps, sat_position[:,2], 'cubic')
        self.sat_fz = interp(self.timeStamps, sat_position[:,3], 'cubic')
            # self.sat_funcs[sat['id']] = (fx,fy,fz)


        self.sat_id = sat['id']

        pass
    def load_gs(self,gs):
        self.gs_position = np.array(gs['position']['cartesian'])

        # self.gs_position_homo = [self.gs_position] * 293
        # self.gs_position_homo = np.array(self.gs_position_homo)
        self.gs_id = gs['id']

    def load_ac(self,ac):
        start,end = ac['availability'].split('/')
        start =  datetime.datetime.strptime(start,'%Y-%m-%dT%H:%M:%SZ')
        end =  datetime.datetime.strptime(end,'%Y-%m-%dT%H:%M:%SZ')

        duration_sec = (end-start).seconds
        self.duration_sec = duration_sec
        length = int(len( np.array(ac['position']['cartesian']))/4)
        ac_positions = np.array(ac['position']['cartesian']).reshape([length,4])
        time_stamp = ac_positions[:,0]
        pass
        ac_fx = interp(time_stamp, ac_positions[:, 1], 'cubic')
        ac_fy = interp(time_stamp, ac_positions[:, 2], 'cubic')
        ac_fz = interp(time_stamp, ac_positions[:, 3], 'cubic')

        self.full_time = np.linspace(start=0,stop=duration_sec,num=duration_sec+1)

        fullx = ac_fx(self.full_time)
        fully = ac_fy(self.full_time)
        fullz = ac_fz(self.full_time)
        fullx = np.expand_dims(fullx,0)
        fully = np.expand_dims(fully,0)
        fullz = np.expand_dims(fullz,0)
        self.ac_pos = np.concatenate([fullx,fully,fullz],0).T

        
        self.ac_id = ac['id']
    def range_log_ac(self):

        fullx = self.sat_fx(self.full_time)
        fully = self.sat_fy(self.full_time)
        fullz = self.sat_fz(self.full_time)
        sat_position = np.concatenate([np.expand_dims(fullx,1),np.expand_dims(fully,1),np.expand_dims(fullz,1)],1)


        ref = sat_position - self.ac_pos
        dis = ref ** 2
        dis = np.sum(dis, axis=1)
        dis = dis ** 0.5
        # tmp/=1000
        mask = dis < self.borderDistance
        if np.sum(mask) > 0:  # range in
            range_name = (self.ac_id, self.sat_id)
            # self.ranges[range_name] = tmp

            # caculate in out instant
            mask = np.int8(mask)
            mask = mask[:-1] - mask[1:]
            start_mask = mask == -1
            end_mask = mask == 1
            starts = list(self.full_time[:-1][start_mask])
            ends = list(self.full_time[:-1][end_mask])

            if len(starts) < len(ends):  # 开始即接入
                starts.insert(0, 0)
            elif len(starts) > len(ends):  # 结束还在接入
                ends.append(86400)

            starts = np.expand_dims(np.array(starts), 0)
            ends = np.expand_dims(np.array(ends), 0)

            self.access_stamp[range_name] = np.concatenate([starts, ends], 0).T



    def range_log(self):


        full_time = np.linspace(start=0, stop=86400, num=86401)

        fullx = self.sat_fx(full_time)
        fully = self.sat_fy(full_time)
        fullz = self.sat_fz(full_time)

        sat_position = np.concatenate([np.expand_dims(fullx,1),np.expand_dims(fully,1),np.expand_dims(fullz,1)],1)

        gs_homo = np.ones_like(sat_position) * self.gs_position

        # distance between sat and gs
        ref = sat_position - gs_homo
        dis = ref**2
        dis = np.sum(dis,axis=1)
        dis = dis**0.5
        # tmp/=1000
        mask = dis<self.borderDistance
        if np.sum(mask)>0:# range in
            range_name = (self.gs_id,self.sat_id)
            # self.ranges[range_name] = tmp

            #caculate in out instant
            mask = np.int8(mask)
            mask = mask[:-1] - mask[1:]
            start_mask = mask == -1
            end_mask = mask == 1
            starts = list(full_time[:-1][start_mask])
            ends = list(full_time[:-1][end_mask])

            if len(starts) < len(ends):  # 开始即接入
                starts.insert(0, 0)
            elif len(starts) > len(ends):  # 结束还在接入
                ends.append(86400)

            starts = np.expand_dims(np.array(starts), 0)
            ends = np.expand_dims(np.array(ends), 0)

            self.access_stamp[range_name] = np.concatenate([starts, ends], 0).T



    def sat_with_gss(self,sat,gss):
        self.load_sat(sat)
        for gs in gss:
            self.load_gs(gs)

            # caculate range between sat,gs
            self.range_log()

    def sat_with_acs(self,sat,acs):
        self.load_sat(sat)
        for ac in acs:
            self.load_ac(ac)
            self.range_log_ac()



    def get_access_stamp(self):
        return self.access_stamp