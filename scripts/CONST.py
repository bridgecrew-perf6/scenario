
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

parent = {
        "id":"SATs",
        "name":"SATs",
        "description":"collection of SAT"
}
parent_str = "SATs"


def main(args):
    yml = YamlHandler(args.settings)
    config = yml.read_yaml()
    dump_path = Path(config["dump_path"])
    constellation = config['constellation']

    tle_file_path = dump_path/(constellation['name']+"_tle.txt")
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
                              start_time= datetime.datetime(*config['start_time']),
                              end_time=datetime.datetime(*config['end_time']),
                              orb_num=constellation['num_orbits'],
                              sat_num=constellation['num_sats_per_orbit'])

    print("\nGENERATES CONSTELLATION...")
    print("--> duration:{} ->{}".format(datetime.datetime(*config['start_time']),datetime.datetime(*config['end_time'])))
    print("--> satellites number of orbit:{}, sat_per_orb:{}, inclination_degree:{}".format(
        constellation['num_orbits'],constellation['num_sats_per_orbit'],constellation['inclination_degree']))

    print("--> dump path:\n \t{}\n\t{}/{}_const.czml".format(tle_file_path,dump_path,constellation['name']))
    czmls = container.get_czml()
    with open(dump_path/"{}_const.czml".format(constellation['name']), "w") as f:
        f.write(czmls)


    # add parent item for better management
    const_list = json2dict(dump_path/"{}_const.czml".format(constellation['name']))
    for item in const_list:
        if item["id"]!="document":
            item["parent"] = parent_str
    const_list.insert(1,parent)
    dict2json(dump_path/"{}_const.czml".format(constellation['name']),const_list)




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="constellation-information")
    if os.path.exists('../configs/config.yaml'):
        parser.add_argument("--settings", default='../configs/config.yaml')
    else:
        parser.add_argument("--settings", default='./configs/config.yaml')

    args = parser.parse_args()
    main(args)