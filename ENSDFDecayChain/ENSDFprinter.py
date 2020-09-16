import os
from mdutils.mdutils import MdUtils
import argparse
import matplotlib.pyplot as plt
from nudel import Nuclide as nucl
from mendeleev import element
from termcolor import colored
from tqdm import tqdm
import sys
import re
import xml.dom.minidom
from Nuclide import *



def get_parser():

    parser = argparse.ArgumentParser(description = 'Plotting script')

    parser.add_argument('-o',
                        dest='Outfolder',
                        type=str,
                        help='output folder')

    parser.add_argument('-e',
                        dest='Energy',
                        type=str,
                        default='065',
                        help='Production Energy [MeV]')

    parser.add_argument('-xs',
                        dest='XsecTh',
                        type=str,
                        default='10',
                        help='Xsection threshold [mb]')

    parser.add_argument('-i',
                        dest='Infile',
                        type=str,
                        help='input file')
    
    parser.add_argument('-level',
                        dest='Levels',
                        type=bool,
                        default=False,
                        help='Activate decay level summary')


    args = parser.parse_args()

    return args

def load_xml_nuclear_table(datafile, n_range, z_range,
                           n_limits = [None, None], z_limits = [None, None]):
    """Loads data from nuclear table in xml format. Returns list of
    Nuclide objects
    """
    # Make high and low limit oposite
    # Later each point is checked against:
    # n_limits[0] = N if N < n_limits[0]
    # n_limits[1] = N if N > n_limits[1]
    # (Z likewise)
    # So oposite limit here forces first point to set 
    # reasonable limits without loosing any data point
    n_limits[0] = n_range[1]
    n_limits[1] = n_range[0]

    z_limits[0] = z_range[1]
    z_limits[1] = z_range[0]

    try:
        dom = xml.dom.minidom.parse(datafile)
    except (EnvironmentError, xml.parsers.expat.ExpatError) as err:
        print("{0}: import error: {1}".format(datafile, err))
        return None

    data = []
    for nuclide in dom.getElementsByTagName("nuclide"):
        try:
            A = int(nuclide.getAttribute('A'))
            Z = int(nuclide.getAttribute('Z'))
            N = A - Z

            if not(n_range[0] <= N <= n_range[1] and 
                z_range[0] <= Z <= z_range[1]):
                continue
            elif N > n_range[1] and Z > z_range[1]:
                break

            if N < n_limits[0]:
                n_limits[0] = N
            if N > n_limits[1]:
                n_limits[1] = N
            if Z < z_limits[0]:
                z_limits[0] = Z
            if Z > z_limits[1]:
                z_limits[1] = Z

            isotope = NuclideXml(Z, A, nuclide)
            data.append(isotope)
        except (ValueError, LookupError) as err:
            print("{0}: import error: {1}".format(datafile, err))
            return False
    return data

data = load_xml_nuclear_table("nubase16.xml", [120,150] ,[80, 95])

def level_scheme(nuc=None, nucleons=None, protons=None, filename=None):
    decays = []
    if not nuc:
        nuc = nucl(nucleons, protons)
    for level in nuc.adopted_levels.levels:
        decays.extend(level.decays)
    success = False
    i = 0.5
    for level in nuc.adopted_levels.levels:
        plt.axhline(level.energy.val, color='k')
        for decay in level.decays:
            success = False
            plt.plot(
                [i, i],
                [decay.orig_level.energy.val, decay.dest_level.energy.val]
            )
            i += 1
    plt.xlim(0, i - 0.5)
    plt.ylim(0, nuc.adopted_levels.levels[-1].energy.val)
    plt.savefig(filename,dpi = 300)
    plt.close()

    return success


def list_levels(nuc=None, nucleons=None, protons=None):
    E = []
    M = []
    Lambda = []
    if not nuc:
        nuc = nucl(nucleons, protons)
    for l in nuc.adopted_levels.levels:
        hl = str(l.half_life)

        E.append(l.energy)
        M.append(l.ang_mom)
        Lambda.append(hl)

    return  E, M, Lambda

def data_extractor(folder, energy):

    data = []
    with open(folder) as infile:

        cycleflag = False
        for line in infile:
            if (cycleflag and ('#' in line) ): break
            if cycleflag :
                 linesplit = line.split()
                 data.append([linesplit[0],linesplit[1]])
            if '# Energy -> {:03d} \n'.format(int(energy)) == line : cycleflag = True

    return data

def PrimaryProduction(XsecTh, ProducedIsotopes):
    Primary = []
    for Isotope in ProducedIsotopes :
        if float(Isotope[0]) > float(XsecTh) :
            protons = int(Isotope[1][0:3])
            nucleons = int(Isotope[1][3:6])
            for nuclide in data:
                if (nuclide.Z == protons) and (nuclide.A == nucleons) :
                    Primary.append({'Z': protons, 
                                    'A': nucleons, 
                                    'Xsec': float(Isotope[0]), 
                                    'Br': nuclide.decay_modes[0]['value'],
                                    'Dmode': nuclide.decay_modes[0]['mode'],
                                    'T': nuclide.half_life_in_seconds()[0]})
                    
    
    return Primary

def decaydirect(Z,A,mode):
    nextZ = 0
    nextA = 0

    if mode == 'b-':
        nextZ = Z+1
        nextA = A
    elif mode == 'b+':
        nextZ = Z-1
        nextA = A
    elif mode == 'ec':
        nextZ = Z-1
        nextA = A
    elif mode == 'a' :
        nextZ = Z-2
        nextA = A-4
    return nextZ, nextA

def decayreverse(Z,A,mode):
    nextZ = 0
    nextA = 0

    if mode == 'b-':
        nextZ = Z-1
        nextA = A
    elif mode == 'b+':
        nextZ = Z+1
        nextA = A
    elif mode == 'ec':
        nextZ = Z+1
        nextA = A
    elif mode == 'a' :
        nextZ = Z+2
        nextA = A+4
    return nextZ, nextA

def NextProduction(Primary):
    
    Secondary = []
    longlivedth = 1800 # seconds
    for iso in Primary:
        nextZ, nextA = decaydirect(iso['Z'],iso['A'],iso['Dmode'])
        
        if float(iso['T']) <= longlivedth:
            for nuclide in data:
                if (nuclide.Z == nextZ) and (nuclide.A == nextA) :
                    Xsec = 0
                    if iso['Br'] != '?' : Xsec = iso['Xsec']*float(iso['Br'])/100.0
                    else : Xsec = iso['Xsec']
                    Secondary.append({'Z': nextZ, 
                                      'A': nextA, 
                                      'Xsec': Xsec , 
                                      'Br': nuclide.decay_modes[0]['value'],
                                      'Dmode': nuclide.decay_modes[0]['mode'],
                                      'T': nuclide.half_life_in_seconds()[0],
                                      'Prev': iso['Dmode']})
    return Secondary

def checkisopresence(Z, A, List):
    
    for i in range(len(List)):
        if  List[i]['Z'] == Z and List[i]['A'] == A :
            return i
    return -1
        
        

def main():

    #-----Getting parser-----#
    args = get_parser()
    
    ProducedIsotopes = []

    if args.Energy is not None:
        ProducedIsotopes = data_extractor(args.Infile,args.Energy)
    else:
        print(colored('ERROR :', 'red'), ' Energy not provided')
        raise SystemExit

    try:
        os.mkdir(args.Outfolder)
    except:
        print(colored('WARNING :', 'yellow')," Output folder already exist. All content will be replaced")
    finally:
        os.system('rm -r '+args.Outfolder)
        os.mkdir(args.Outfolder)
        os.mkdir(args.Outfolder+'/Images')

    
    

    Primary = PrimaryProduction( args.XsecTh , ProducedIsotopes)

    Second = NextProduction(Primary)
    Third = NextProduction(Second)

    # print(Primary)
    # print(Second)
    # print(Third)
    
    mdFile = MdUtils(file_name=args.Outfolder+'/Resume', title='ENSDF Resume')
    blacklist = []
    for iso in Primary:
                
        E = []
        M = []
        HL = []
        flag = args.Levels
        levelflag = True
        nucleon = iso['A']
        proton = iso['Z']
        try:
            E, M, HL= list_levels(nucleons=nucleon, protons=proton)
            levelflag = level_scheme(nucleons=nucleon, protons=proton, filename=args.Outfolder+'/Images/'+str(proton)+str(nucleon)+'.png')
        except:
            flag = False
        
        El = element(proton)
        title = str(nucleon)+El.symbol
        blacklist.append(title)
        mdFile.new_header(3, title)
        mdFile.new_line("Element "+title+" direct production cross section -> "+str(iso['Xsec'])+" mb")
        x = checkisopresence(iso['Z'], iso['A'], Second)
        y = checkisopresence(iso['Z'], iso['A'], Third)
                   
        if x != -1:
            Z, A = decayreverse(Second[x]['Z'],Second[x]['A'],Second[x]['Prev'])
            El2 = element(Z)
            title2 = str(A)+El2.symbol
            mdFile.new_line("Second generation production cross section -> "+str(Second[x]['Xsec'])+" mb")
            mdFile.new_line("Coming from "+Second[x]['Prev']+" decay of "+title2)

        if y != -1:
            Z, A = decayreverse(Third[y]['Z'],Third[y]['A'],Third[y]['Prev'])
            El2 = element(Z)
            title2 = str(A)+El2.symbol
            mdFile.new_line("Third generation production cross section -> "+str(Third[y]['Xsec'])+" mb")
            mdFile.new_line("Coming from "+Third[y]['Prev']+" decay of "+title2)
        
                        
        if flag :
            list_of_levels = ["Energy", "Jπ", "λ"]
            for index in range(len(E)):
                list_of_levels.extend([f"{E[index]}", f"{M[index]}", HL[index]])

            mdFile.new_line()
            mdFile.new_table(columns=3, rows=len(E)+1, text=list_of_levels, text_align='left')
                # if levelflag :
                #     mdFile.new_line(mdFile.new_inline_image(text=title, path='Images/'+Isotope[1]+'.png'))

    for iso in Second:
                
        E = []
        M = []
        HL = []
        flag = args.Levels
        levelflag = True
        nucleon = iso['A']
        proton = iso['Z']
        El = element(proton)
        title = str(nucleon)+El.symbol
        if title not in blacklist:
            blacklist.append(title)
            try:
                E, M, HL= list_levels(nucleons=nucleon, protons=proton)
                levelflag = level_scheme(nucleons=nucleon, protons=proton, filename=args.Outfolder+'/Images/'+str(proton)+str(nucleon)+'.png')
            except:
                flag = False
            
            
            mdFile.new_header(3, title)
            Z, A = decayreverse(iso['Z'],iso['A'],iso['Prev'])
            El2 = element(Z)
            title2 = str(A)+El2.symbol
            mdFile.new_line("Second generation production cross section -> "+str(iso['Xsec'])+" mb")
            mdFile.new_line("Coming from "+iso['Prev']+" decay of "+title2)
            

            if flag :
                list_of_levels = ["Energy", "Jπ", "λ"]
                for index in range(len(E)):
                    list_of_levels.extend([f"{E[index]}", f"{M[index]}", HL[index]])

                mdFile.new_line()
                mdFile.new_table(columns=3, rows=len(E)+1, text=list_of_levels, text_align='left')
                    # if levelflag :
                    #     mdFile.new_line(mdFile.new_inline_image(text=title, path='Images/'+Isotope[1]+'.png'))
    
    for iso in Third:
                
        E = []
        M = []
        HL = []
        flag = args.Levels
        levelflag = True
        nucleon = iso['A']
        proton = iso['Z']
        El = element(proton)
        title = str(nucleon)+El.symbol
        if title not in blacklist:
            blacklist.append(title)
            try:
                E, M, HL= list_levels(nucleons=nucleon, protons=proton)
                levelflag = level_scheme(nucleons=nucleon, protons=proton, filename=args.Outfolder+'/Images/'+str(proton)+str(nucleon)+'.png')
            except:
                flag = False
            
            
            mdFile.new_header(3, title)
            Z, A = decayreverse(iso['Z'],iso['A'],iso['Prev'])
            El2 = element(Z)
            title2 = str(A)+El2.symbol
            mdFile.new_line("Third generation production cross section -> "+str(iso['Xsec'])+" mb")
            mdFile.new_line("Coming from "+iso['Prev']+" decay of "+title2)
            

            if flag :
                list_of_levels = ["Energy", "Jπ", "λ"]
                for index in range(len(E)):
                    list_of_levels.extend([f"{E[index]}", f"{M[index]}", HL[index]])

                mdFile.new_line()
                mdFile.new_table(columns=3, rows=len(E)+1, text=list_of_levels, text_align='left')
                    # if levelflag :
                    #     mdFile.new_line(mdFile.new_inline_image(text=title, path='Images/'+Isotope[1]+'.png'))

    
    
    cmdstr = ''
    for el in blacklist:
        cmdstr += ' --Produced '+el
    os.system('python ChartDrawer.py --n 129 148 --z 85 97 nubase16.xml '+args.Outfolder+'/chart.svg '+cmdstr)
    os.system('inkscape '+args.Outfolder+'/chart.svg --export-filename '+args.Outfolder+'/chart.pdf')
    mdFile.new_line(mdFile.new_inline_image(text="Production Nuclide Chart", path=args.Outfolder+'/chart.png'))
    mdFile.create_md_file()
    os.system('grip -b '+args.Outfolder+'/Resume.md')
    os.system('xdg-open '+args.Outfolder+'/chart.pdf')





if __name__ == '__main__':
    main()
