from screenutils import list_screens, Screen
import argparse
import time
import zmq


def get_parser():

    parser = argparse.ArgumentParser(description = 'Multithread simulation manager')

    parser.add_argument('-j',
                        dest='threads',
                        type=int,
                        default = 2,
                        help='Number of working units')

    parser.add_argument('-input',
                        dest='basicinput',
                        type=str,
                        default = 'testinputfile',
                        help='basicinput filename')

    parser.add_argument('-energies',
                        dest='Elist',
                        type=int,
                        nargs=3,
                        default = [10,100,10],
                        help='Emin Emax Steps')

    args = parser.parse_args()

    return args, parser


def main():

    FolderCMD = '/home/andrea/Repository/233Usimulation/Multi_Thread_Simulation_Manager'
    # Getting parser
    args, parser = get_parser()

    # Create screen session for Master
    MasterShell = Screen("Master",True)
    #MasterShell.enable_logs()

    MasterShell.send_commands('cd '+ FolderCMD + ' ; python Master.py -j '+str(args.threads)+ ' -input ' + args.basicinput + ' -energies ' + str(args.Elist[0]) + " " + str(args.Elist[1]) + " " +str(args.Elist[2]) )
    # Create screen sessions for Slaves
    SlaveShell = []

    for j in range(args.threads):
        name = 'Slave' + str(j+1)
        SlaveShell.append(Screen(name,True))
        #SlaveShell[j].enable_logs()
        SlaveShell[j].send_commands('cd '+ FolderCMD + ' ; python Slave.py -id '+ name)


if __name__ == '__main__':
    main()
