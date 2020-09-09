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

    parser.add_argument('-i',
                        dest='Infile',
                        type=str,
                        help='input file')


    args = parser.parse_args()

    return args


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


def main():

        #-----Getting parser-----#
        args = get_parser()

        try:
            os.mkdir(args.Outfolder)
        except:
            print(colored('WARNING :', 'yellow')," Output folder already exist. All content will be replaced")
        finally:
            os.system('rm -r '+args.Outfolder)
            os.mkdir(args.Outfolder)
            os.mkdir(args.Outfolder+'/Images')

        mdFile = MdUtils(file_name=args.Outfolder+'/Resume', title='ENSDF Resume')



        level_scheme(nucleons=214, protons=83, filename=args.Outfolder+'/Images/083214.png')

        mdFile.new_header(3, "Inline Images")

        mdFile.new_line(mdFile.new_inline_image(text='test', path='Images/083214.png'))

        E, M, HL= list_levels(nucleons=214, protons=83)
        list_of_levels = ["Energy", "Jπ", "λ"]
        for index in range(len(E)):
            list_of_levels.extend([f"{E[index]}", f"{M[index]}", HL[index]])

        mdFile.new_line()
        mdFile.new_table(columns=3, rows=len(E)+1, text=list_of_levels, text_align='left')

        mdFile.create_md_file()





if __name__ == '__main__':
    main()
