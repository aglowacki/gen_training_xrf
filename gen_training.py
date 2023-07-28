import h5py
import argparse
from glob import glob
import os

detector_list = range(7)

skippable_tags = ['SRCURRENT', 'US_IC', 'DS_IC', 'ELT1', 'ELT2', 'ELT3', 'ELT4', 
                  'ERT1', 'ERT2', 'ERT3', 'ERT4', 'ICR1', 'ICR2', 'ICR3', 'ICR4',
                  'OCR1', 'OCR2', 'OCR3', 'OCR4', 'US_AMP_SENS_NUM', 'US_AMP_SENS_UNIT', 
                  'DS_AMP_SENS_NUM', 'DS_AMP_SENS_UNIT', 'BRANCHING_FAMILY_ADJUSTMENT_L', 
                  'BRANCHING_RATIO_ADJUSTMENT_L', 'BRANCHING_RATIO_ADJUSTMENT_K', 
                  'IDENTIFYING_NAME_[WHATEVERE_YOU_LIKE]', 'DATE', 'CAL_OFFSET_[E_OFFSET]_MAX',
                  'CAL_OFFSET_[E_OFFSET]_MIN', 'CAL_SLOPE_[E_LINEAR]_MAX', 'CAL_SLOPE_[E_LINEAR]_MIN',
                  'CAL_QUAD_[E_QUADRATIC]_MAX', 'CAL_QUAD_[E_QUADRATIC]_MIN', 'COHERENT_SCT_ENERGY_MAX',
                  'COHERENT_SCT_ENERGY_MIN', 'COMPTON_ANGLE_MAX', 'COMPTON_ANGLE_MIN', 'DETECTOR_MATERIAL',
                  'FIT_SNIP_WIDTH', 'BE_WINDOW_THICKNESS', 'DET_CHIP_THICKNESS', 'GE_DEAD_LAYER',  'MAX_ENERGY_TO_FIT',
                  'MIN_ENERGY_TO_FIT', 'GE_ESCAPE_FACTOR', 'GE_ESCAPE_ENABLE', 'DPC1_IC', 'DPC2_IC',
                   'CFG_1', 'CFG_2', 'CFG_3', 'CFG_4', 'CFG_5', 'CFG_6', 'CFG_7', 'CFG_8', 'CFG_9' ]

def read_fit_params(fname):
    params = dict()
    with open(fname, 'r') as f:
        lines = f.readlines()
    for i in lines:
        tags = i.split(':')
        if len(tags) > 1:
            is_comment = tags[0][0] == ' ' or tags[0][0] == '\t'
            if False == is_comment:
                if tags[0] in skippable_tags:
                    continue
                elif tags[0] == 'ELEMENTS_TO_FIT' or tags[0] == 'ELEMENTS_WITH_PILEUP':
                    params[tags[0]] = tags[1].strip('\n')
                else:
                    params[tags[0]] = float(tags[1].strip('\n'))
    return params

def read_int_spec(h5name):
    int_spec = None
    with h5py.File(h5name, 'r') as f:
        # try to see if v10 layout, Non Negative Lease squares fitting tech was used
        h5_counts = f['/MAPS/XRF_Analyzed/NNLS/Counts_Per_Sec']
        h5_channel_names = f['/MAPS/XRF_Analyzed/NNLS/Channel_Names']
        if h5_counts is None:
            # try to see if v10 layout, iterative matrix fitting tech was used
            h5_counts = f['/MAPS/XRF_Analyzed/Fitted/Counts_Per_Sec']
            h5_channel_names = f['/MAPS/XRF_Analyzed/Fitted/Channel_Names']
            if h5_counts is None:
                # try to see if was saved in v9 layout
                h5_counts = f['/MAPS/XRF_fits']
                h5_channel_names = f['/MAPS/channel_names']
        if h5_counts != None:
            counts = h5_counts[...]
            channel_names = h5_channel_names[...]
    return (counts, channel_names)

def write_int_spec_and_fp(h5_f, int_spec, fp):
    pass

def proc_dir(indir, outfile):
    try:
        # process directory
        override_files = glob(indir+"/maps_fit_parameters_override.txt*", recursive = False)
        for over in override_files:
            last = over[len(over-1)]
            detector = ''
            try:
                if last == 't':
                    # avg file or detector 0 for single element detectors
                    detector = ''
                else:
                    detector = last
            except:
                print('Failed to parse detector for override file '+over)
            fit_params = read_fit_params(over)
            h5_files = glob(indir + '/img.dat/*.h5'+detector)
            for h5 in h5_files:
                int_spec = read_int_spec(h5)
    except Exception as e:
        print (e)

def recur_scan_dir(indir, outfile):
    dir_list = glob(indir+"/**/", recursive = False)
    print (dir_list)
    # search 
    img_dat_dir = list(i for i in dir_list if i.find('img.dat') > 1)
    if len(img_dat_dir > 0):
        proc_dir(indir, outfile)
    else:
        for i in dir_list:
            recur_scan_dir(i, outfile)

def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-i', type=str,  help='Input directory to iterate over')
    parser.add_argument('-o', type=str,  help='Output filename, hdf5 ')
    args = parser.parse_args()
    print(args.i, args.o)
    if args.i == None or args.o == None:
        print("Please use -i for input directory and -o for output filename")
        return -1
    '''
    with h5py.File(args.of, 'w') as outfile:
        if outfile == None:
            print('Error opening ',args.of, 'for writing to.')
            return -2
   
        recur_scan_dir(args.i, outfile)
    '''
    return 0

if __name__ == '__main__':
    main()