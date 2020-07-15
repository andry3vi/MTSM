import os
import zmq
import json
import time
import argparse
from datetime import datetime
from tqdm import tqdm

def get_parser():

    parser = argparse.ArgumentParser(description = 'Master process to handle the single threads')

    parser.add_argument('-j',
                        dest='slaves',
                        type=int,
                        help='Number of working units')

    parser.add_argument('-input',
                        dest='basicinput',
                        type=str,
                        help='basicinput filename')

    parser.add_argument('-energies',
                        dest='Elist',
                        type=int,
                        action = 'store',
                        nargs=3,
                        help='Emin Emax Steps')

    args = parser.parse_args()

    return args, parser


def main():

    # Getting parser
    args, parser = get_parser()


    # datetime object containing current date and time
    now = datetime.now()

    # dd_mm_YY_HMS
    dt_string = now.strftime("%d_%m_%Y_%H%M%S")
    print("creating simulation folder ->", dt_string)

    directory_name = dt_string+"_SIMU"

    try:
        os.mkdir(directory_name)
    except:
        print("Warning:",directory_name,"Already exist. All content will be deleted.")
        print()
    finally:
        os.system('rm -r '+directory_name)
        os.mkdir(directory_name)


    os.system('cp '+args.basicinput+' '+directory_name+'/simu.inp')
    os.chdir(directory_name)

    # Creating zmq context
    ctx = zmq.Context()

    # Define the port on which worker units should ask for tasks
    master = ctx.socket(zmq.REP)
    master.bind("tcp://*:8000")


    #check unit connection
    for j in range(args.slaves):
        unit = master.recv_json()

        print('------------------------------------')
        print('Unit --', unit['name'],'-- connected')
        print('------------------------------------')

        master.send_json({'status' : 'connected', 'folder' : directory_name})







    for e in  tqdm(range(args.Elist[0],args.Elist[1],args.Elist[2])):
        msg = master.recv_json()
        if( msg['status'] == 'available'):
            master.send_json({'status':str(e)})


    time.sleep(10)

    for j in range(args.slaves):
        msg = master.recv_json()
        if( msg['status'] == 'available'):
            master.send_json({'status':'kill'})


    os.system('echo exiting')
    os.system('screen -XS Master quit')



if __name__ == '__main__':
    main()
