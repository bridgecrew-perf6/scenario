
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


def main(args):
    yml = YamlHandler(args.settings)
    config = yml.read_yaml()
    dump_path = Path(config["dump_path"])
    name = config["constellation"]["name"]

    print("\nSUMMARIZING...")

    const = json2dict(dump_path/"{}_const.czml".format(name))
    isl = json2dict(dump_path/"{}_isl.czml".format(name))
    fwd = json2dict(dump_path/"{}_fwd.czml".format(name))

    sum = const+isl+fwd
    dict2json(dump_path/"{}.czml".format(name),sum)
    print("--> at {}/{}.czml".format(dump_path,name))








if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="constellation-information")
    if os.path.exists('../configs/config.yaml'):
        parser.add_argument("--settings", default='../configs/config.yaml')
    else:
        parser.add_argument("--settings", default='./configs/config.yaml')

    args = parser.parse_args()
    main(args)