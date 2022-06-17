import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d as interp
from tqdm import tqdm



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
    def load_sat(self,sat):
        positions = sat['position']['cartesian']
        self.sat_positions = np.array(positions).reshape([293,4])
        self.sat_id = sat['id']

        pass
    def load_gs(self,gs):
        self.gs_position = gs['position']['cartesian']
        self.gs_position_homo = [self.gs_position] * 293
        self.gs_position_homo = np.array(self.gs_position_homo)
        self.gs_id = gs['id']
    def range_log(self):
        if self.sat_id=='00200' and self.gs_id=='London':
            print('ok')

        ref = self.sat_positions[:,1:] - self.gs_position_homo
        tmp = ref**2
        tmp = np.sum(tmp,axis=1)
        tmp = tmp**0.5
        # tmp/=1000
        if np.sum(tmp<self.borderDistance)>0:# range in
            range_name = (self.gs_id,self.sat_id)
            self.ranges[range_name] = tmp


    def eva_log(self):
        pass
        #TODO

    def run(self):
        x = np.linspace(start=0, stop=86400, num=86401)
        # y = np.interp(x, self.df.index, self.ranges[('00903', 'London')])
        self.access_stamp={}
        for k,v in self.ranges.items():
            f = interp(self.timeStamps,v,'cubic')
            y = f(x)

            mask = np.int8(y < self.borderDistance)
            mask = mask[:-1] - mask[1:]
            start_mask = mask==-1
            end_mask = mask ==1
            starts = list(x[:-1][start_mask])
            ends = list(x[:-1][end_mask])

            if len(starts) < len(ends):#开始即接入
                starts.insert(0,0)
            elif len(starts)>len(ends):#结束还在接入
                ends.append(86400)

            starts= np.expand_dims(np.array(starts), 0)
            ends = np.expand_dims(np.array(ends), 0)

            self.access_stamp[k] = np.concatenate([starts,ends],0).T

    def get_access_stamp(self):
        return self.access_stamp