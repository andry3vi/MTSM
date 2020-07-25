import os
import zmq
import json
import time
import argparse
import subprocess
import numpy as np

def get_parser():

    parser = argparse.ArgumentParser(description = 'Slave unit')

    parser.add_argument('-id',
                        dest='slavename',
                        type=str,
                        nargs=1,
                        help='id of the unit')

    args = parser.parse_args()

    return args, parser

def free_format_file(filename):

    with open(filename, 'r') as input_file:

        lines = input_file.readlines()
        beam_index = 0

        for idx,line in enumerate(lines):

            if('BEAM ' in line):

                beam_index = idx

        lines = lines[:beam_index] + ['FREE\n','BEAMLINE\n','FIXED\n'] + lines[beam_index+1:]


    with open(filename[:-4] + '_fixed.inp','w') as outfile:

        outfile.writelines(lines)
        outfile.close()

        return

def change_energy(filename, par):

    with open(filename,'r') as input_file:

        lines = input_file.readlines()

        for idx,line in enumerate(lines):

            if('BEAMLINE' in line):

                lines[idx] = 'BEAM,-' + str(par) + ',,,,,,PROTON\n'

    with open(filename, 'w') as input_fluka:

        input_fluka.writelines(lines)
        input_fluka.close()

    return

def create_cmd_buffer(channel):

    filelist = []

    for file in os.listdir():

        if('fort.'+str(channel) in file):

            filelist.append(file)


    with open('buffer.txt','w') as buffer:

        for file in filelist:
            buffer.write(file + '\n')

        buffer.write('\n')
        buffer.write('output.rnc\n')

        buffer.close()

    return

def main():

    # Getting parser
    args, parser = get_parser()

    # Setting up fluka Environment
    fluka_environment = os.environ.copy()
    fluka_environment["FLUFOR"] = "gfortran"
    fluka_environment["FLUPRO"] = "/home/andrea/Simu/fluka"

    MainFolder = ''

    # Creating zmq context
    ctx = zmq.Context()

    id = args.slavename[0]
    print('slave id -> ', id)

    # Socket to receive messages on
    slave = ctx.socket(zmq.REQ)
    slave.connect("tcp://localhost:8000")

    #send connection check
    slave.send_json({'name' : args.slavename})
    msg = slave.recv_json()
    if (msg['status'] == 'connected'):
        print('------------------------------------')
        print('Unit --',id,'-- connected')
        print('------------------------------------')
        os.chdir(msg['folder'])
        MainFolder = msg['folder']

    #waiting time to allow every unit to link up
    time.sleep(5)

    while True:

        #unit declared as available
        slave.send_json({"status" : "available"})

        # Retrieve a task from the manager
        jobs = slave.recv_json()

        if jobs == {} : continue

        if (jobs['status'] == 'kill') : os.system('screen -XS '+ id +' quit')

        print('--------------------------')
        print('processing energy ->',jobs['status'])
        print('--------------------------')

        print("creating simulation energy folder ->", jobs['status'])

        directory_name = 'Energy_'+jobs['status']

        try:
            os.mkdir(directory_name)
        except:
            print("Warning:",directory_name,"Already exist. All content will be deleted.")
            print()
        finally:
            os.system('rm -r '+directory_name)
            os.mkdir(directory_name)

        os.system('cp simu.inp '+directory_name+'/simu.inp')
        os.chdir(directory_name)

        free_format_file('simu.inp')
        change_energy('simu_fixed.inp',np.round(int(jobs['status'])/1000.0,6))

        # Run the new simulation
        os.system('$FLUPRO/flutil/rfluka  simu_fixed.inp')



        create_cmd_buffer(22)

        os.system('$FLUPRO/flutil/usrsuw < buffer.txt')

        os.system('rm -v *.err *.out')
        os.chdir('../')
        time.sleep(5)



if __name__ == '__main__':
    main()
