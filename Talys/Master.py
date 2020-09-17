import os
import zmq
import json
import time
import argparse
from datetime import datetime
from tqdm import tqdm
import itertools  

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

marker = itertools.cycle(('|','/', '-', '\\'))
def clear(): 
    _ = os.system('clear') 

def status_print(slave_list):
    print('\033[H\033[J') #clear()
    load = next(marker)
    for slaveID in slave_list.keys():
        print('------------------------------------')
        print('Unit ID     -- ', slaveID)
        print('Unit Status -- ', slave_list[slaveID][0])
        print('Unit job    -- ', slave_list[slaveID][1])
        if slave_list[slaveID][1] != '---' : 
            print('Computing '+load)
        print('------------------------------------')
    
def main():

    # Getting parser
    args, parser = get_parser()


    # datetime object containing current date and time
    now = datetime.now()
    El = ''
    A  = ''

    with open(args.basicinput,'r') as original_input:
        for line in original_input:
            parameter = line.strip().split(' ')
            try:
                if parameter[0] == 'element' : El = parameter[1]
                if parameter[0] == 'mass'    : A  = parameter[1]
            except:
                continue

      
    
    original_input.close()
    # dd_mm_YY_HMS
    
    dt_string = now.strftime("%d_%m_%Y_%H%M%S")
    

    directory_name = El+A+'_p'+str(args.Elist[0])+'min_'+str(args.Elist[1])+'max_'+str(args.Elist[2])+'step_'+dt_string+"_SIMU"
    print("creating simulation folder ->", directory_name)

    try:
        os.mkdir(directory_name)
    except:
        print("Warning:",directory_name,"Already exist. All content will be deleted.")
        print()
    finally:
        os.system('rm -r '+directory_name)
        os.mkdir(directory_name)


    os.system('cp '+args.basicinput+' '+directory_name+'/input')
    os.chdir(directory_name)

    # Creating zmq context
    ctx = zmq.Context()

    # Define the port on which worker units should ask for tasks
    master = ctx.socket(zmq.REP)
    master.bind("tcp://*:8000")
    
    slave_list = dict()

    for j in range(args.slaves):
        slave_list['Slave'+str(j+1)] = ['not connected','---']

    #check unit connection
    for j in range(args.slaves):
        unit = master.recv_json()
        slave_list[unit['ID']] = ['connected', '---']
        status_print(slave_list)
        master.send_json({'status' : 'connected', 'folder' : directory_name})






    

    for e in range(args.Elist[0],args.Elist[1],args.Elist[2]):
        while True:
            try:
                msg = master.recv_json(flags=zmq.NOBLOCK)
                if( msg['status'] == 'available'):
                    master.send_json({'status':str(e)})
                    slave_list[msg['ID']] = ['connected', 'Energy '+str(e)]
                    status_print(slave_list)
                    break
            except :
                status_print(slave_list)
            
            time.sleep(1)
      
    

    for j in range(args.slaves):
        while True:
            try:
                msg = master.recv_json(flags=zmq.NOBLOCK)
                if( msg['status'] == 'available'):
                    master.send_json({'status':'kill'})
                    slave_list.pop(msg['ID'])
                    break
            except :
                status_print(slave_list)
            time.sleep(0.1)


    os.system('echo exiting')
    os.system('screen -XS Master quit')



if __name__ == '__main__':
    main()
