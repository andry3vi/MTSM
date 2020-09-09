import os
from mdutils.mdutils import MdUtils
import argparse
import matplotlib.pyplot as plt
from nudel import Nuclide
from mendeleev import element
from termcolor import colored



def get_parser():

    parser = argparse.ArgumentParser(description = 'Plotting script')

    parser.add_argument('-o',
                        dest='Outfolder',
                        type=str,
                        help='output folder')

    parser.add_argument('-e',
                        dest='Energy',
                        type=str,
                        help='Production Energy')

    parser.add_argument('-i',
                        dest='Infile',
                        type=str,
                        help='input file')


    args = parser.parse_args()

    return args, parser


def level_scheme(nuc=None, nucleons=None, protons=None, filename=None):
    decays = []
    if not nuc:
        nuc = Nuclide(nucleons, protons)
    for level in nuc.adopted_levels.levels:
        decays.extend(level.decays)

    i = 0.5
    for level in nuc.adopted_levels.levels:
        plt.axhline(level.energy.val, color='k')
        for decay in level.decays:
            plt.plot(
                [i, i],
                [decay.orig_level.energy.val, decay.dest_level.energy.val]
            )
            i += 1
    plt.xlim(0, i - 0.5)
    plt.ylim(0, nuc.adopted_levels.levels[-1].energy.val)
    plt.savefig(filename,dpi = 300)
    plt.close()


def list_levels(nuc=None, nucleons=None, protons=None):
    E = []
    M = []
    Lambda = []
    if not nuc:
        nuc = Nuclide(nucleons, protons)
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

def main():

        #-----Getting parser-----#
        args, parser = get_parser()
        cutoff = 1 #mb
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

        mdFile = MdUtils(file_name=args.Outfolder+'/Resume', title='ENSDF Resume')

        for Isotope in ProducedIsotopes :
            if float(Isotope[0]) > cutoff :
                proton = int(Isotope[1][0:3])
                nucleon = int(Isotope[1][3:6])
                level_scheme(nucleons=nucleon, protons=proton, filename=args.Outfolder+'/Images/'+Isotope[1]+'.png')

                El = element(proton)
                title = str(nucleon)+El.symbol
                mdFile.new_header(3, title)
                mdFile.new_line("Element "+title+" production cross section -> "+Isotope[0]+" mb")
                E, M, HL= list_levels(nucleons=nucleon, protons=proton)
                list_of_levels = ["Energy", "Jπ", "λ"]
                for index in range(len(E)):
                    list_of_levels.extend([f"{E[index]}", f"{M[index]}", HL[index]])

                mdFile.new_line()
                mdFile.new_table(columns=3, rows=len(E)+1, text=list_of_levels, text_align='left')
                mdFile.new_line(mdFile.new_inline_image(text=title, path='Images/'+Isotope[1]+'.png'))



        mdFile.create_md_file()





if __name__ == '__main__':
    main()
