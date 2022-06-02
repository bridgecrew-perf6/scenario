
import json
import time
import numpy as np
import random
import pandas as pd
def time_stat(last_end):
    end = time.time()
    running_time = end - last_end
    # print('--> time cost : %.5f sec' % running_time)
    return running_time

def get_now():
    return time.time()



def json2dict(file):
    with open(file, 'r') as f:
        dict = json.load(fp=f)
        return dict
def dict2json(file,dict):
    with open(file, 'w') as f:
        json.dump(dict, f)


def to_csv(file,series):
    series.to_csv(file)
def read_csv(file):
    return pd.read_csv(file,index_col=0)

def readlines(filename):
    """Read all the lines in a text file and return as a list
    """
    with open(filename, 'r') as f:
        lines = f.read().splitlines()
    return lines

def readtles(filename):
    lines = readlines(filename)
    length = len(lines)
    assert(length%3==1,"err")


    reformat_lines=[]
    cnt = 1
    while cnt+3<= length:
        satname,line1,line2 = lines[cnt],lines[cnt+1],lines[cnt+2]
        cnt+=3
        reformat_lines.append([satname,line1,line2])

    return reformat_lines


def list_filter(lines,perc=0.1):
    random.shuffle(lines)
    length = len(lines)
    length = int(length*perc)
    return lines[:length]
