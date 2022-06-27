
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
root={
    "id":"root",
    "name":"root",
    "parent":None
}
SATs_template = {
        "id":"SATs",
        "name":"SATs",
        "description":"collection of SAT",
        "parent": "root"

}



def main(args):
    yml = YamlHandler(args.settings)
    config = yml.read_yaml()
    dump_path = Path(config["dump_path"])
    dump_path.mkdir_p()

    constellation = config['constellation']

    tle_file_path = dump_path/(constellation['name']+"_tle.txt")

    # phase_factor = constellation['phase_factor']
    # perigee_degree = constellation['perigee_degree']
    # orbit_shift= phase_factor*360/constellation['num_orbits']/constellation['num_sats_per_orbit']

    args2tles(
        filename_out=tle_file_path,
        constellation_name=constellation['name'],
        num_orbits=constellation['num_orbits'],
        num_sats_per_orbit=constellation['num_sats_per_orbit'],
        phase_factor=constellation['phase_factor'],

        eccentricity=constellation['eccentricity'],
        seed_satellite=config['satellite']
    )

    lines = readtles(tle_file_path)
    container = SatelliteCzml(tle_list=lines,
                              start_time= datetime.datetime.strptime(config['start_time'], '%Y-%m-%dT%H:%M:%SZ'),
                              end_time=datetime.datetime.strptime(config['end_time'], '%Y-%m-%dT%H:%M:%SZ'),
                              orb_num=constellation['num_orbits'],
                              sat_num=constellation['num_sats_per_orbit'])

    print("\nGENERATING CONSTELLATION...")
    print("--> duration:{} -> {}".format(config['start_time'],config['end_time']))
    print("--> constellation args:\n \t number of orbit:{}, sat_per_orb:{},phase factor:{}".format(
        constellation['num_orbits'],
        constellation['num_sats_per_orbit'],
        constellation['phase_factor']))

    print("--> dump path:\n \t{}\n\t{}/{}_const.czml".format(tle_file_path,dump_path,constellation['name']))
    czmls = container.get_czml()
    with open(dump_path/"{}_const.czml".format(constellation['name']), "w") as f:
        f.write(czmls)


    # add parent item for every sats to achive  better management
    const_list = json2dict(dump_path/"{}_const.czml".format(constellation['name']))
    for item in const_list:
        if item["id"]!="document":
            item["parent"] = SATs_template["id"]
        else:
            item["parent"] = None
    const_list.insert(1,root)
    const_list.insert(2,SATs_template)

    dict2json(dump_path/"{}_const.czml".format(constellation['name']),const_list)




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="constellation-information")
    if os.path.exists('../configs/config.yaml'):
        parser.add_argument("--settings", default='../configs/config.yaml')
    else:
        parser.add_argument("--settings", default='./configs/config.yaml')

    args = parser.parse_args()
    main(args)