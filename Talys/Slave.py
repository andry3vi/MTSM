import os
import zmq
import json
import time
import argparse


def get_parser():

    parser = argparse.ArgumentParser(description = 'Slave unit')

    parser.add_argument('-id',
                        dest='slavename',
                        type=str,
                        nargs=1,
                        help='id of the unit')

    args = parser.parse_args()

    return args, parser


def main():

    # Getting parser
    args, parser = get_parser()

    MainFolder = ''
    TalysCMD = '~/bin/talys'
    # Creating zmq context
    ctx = zmq.Context()

    id = args.slavename[0]
    print('slave id -> ', id)

    # Socket to receive messages on
    slave = ctx.socket(zmq.REQ)
    slave.connect("tcp://localhost:8000")

    #send connection check
    slave.send_json({'ID' : id})
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
        slave.send_json({"status" : "available", 'ID' : id})

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

        os.chdir(directory_name)
        
        with open('../input','r') as original_input:
            with open('input', 'w') as new_input:
                for line in original_input:
                    new_input.write('energy '+jobs['status'] if 'energy' in line else line)
        original_input.close()
        new_input.close()
        

        os.system(TalysCMD+' < input > output')

        os.chdir('../')
        time.sleep(10)



if __name__ == '__main__':
    main()
