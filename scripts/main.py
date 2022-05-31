
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
    constellation = config['constellation']

    tle_file_path = Path("../tmp")/(constellation['name']+".txt")
    args2tles(
        filename_out=tle_file_path,
        constellation_name=constellation['name'],
        num_orbits=constellation['num_orbits'],
        num_sats_per_orbit=constellation['num_sats_per_orbit'],
        phase_diff=constellation['phase_diff'],
        inclination_degree=constellation['inclination_degree'],
        eccentricity=constellation['eccentricity'],
        arg_of_perigee_degree=constellation['arg_of_perigee_degree'],
        mean_motion_rev_per_day=constellation['mean_motion_rev_per_day']
    )

    lines = readtles(tle_file_path)

    container = SatelliteCzml(tle_list=lines,
                              orb_num=constellation['num_orbits'],
                              sat_num=constellation['num_sats_per_orbit'])




    czmls = container.get_czml()
    with open("../tmp/{}.czml".format(constellation['name']), "w") as f:
        f.write(czmls)
    print('ok')




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="constellation-information")
    if os.path.exists('../configs/config.yaml'):
        parser.add_argument("--settings", default='../configs/config.yaml')
    else:
        parser.add_argument("--settings", default='./configs/config.yaml')

    args = parser.parse_args()
    main(args)