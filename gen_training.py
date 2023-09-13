import h5py
import argparse
from glob import glob
import traceback
import numpy as np

group_start_id = 0

skippable_tags = ['SRCURRENT', 'US_IC', 'DS_IC', 'ELT1', 'ELT2', 'ELT3', 'ELT4', 
                  'ERT1', 'ERT2', 'ERT3', 'ERT4', 'ICR1', 'ICR2', 'ICR3', 'ICR4',
                  'OCR1', 'OCR2', 'OCR3', 'OCR4', 'US_AMP_SENS_NUM', 'US_AMP_SENS_UNIT', 
                  'DS_AMP_SENS_NUM', 'DS_AMP_SENS_UNIT', 'BRANCHING_FAMILY_ADJUSTMENT_L', 
                  'BRANCHING_RATIO_ADJUSTMENT_L', 'BRANCHING_RATIO_ADJUSTMENT_K', 
                  'IDENTIFYING_NAME_[WHATEVERE_YOU_LIKE]', 'DATE', 'CAL_OFFSET_[E_OFFSET]_MAX',
                  'CAL_OFFSET_[E_OFFSET]_MIN', 'CAL_SLOPE_[E_LINEAR]_MAX', 'CAL_SLOPE_[E_LINEAR]_MIN',
                  'CAL_QUAD_[E_QUADRATIC]_MAX', 'CAL_QUAD_[E_QUADRATIC]_MIN', 'COHERENT_SCT_ENERGY_MAX',
                  'COHERENT_SCT_ENERGY_MIN', 'COMPTON_ANGLE_MAX', 'COMPTON_ANGLE_MIN', 'DETECTOR_MATERIAL',
                  'FIT_SNIP_WIDTH', 'BE_WINDOW_THICKNESS', 'DET_CHIP_THICKNESS', 'GE_DEAD_LAYER',  
                  'GE_ESCAPE_FACTOR', 'GE_ESCAPE_ENABLE', 'DPC1_IC', 'DPC2_IC',
                   'CFG_1', 'CFG_2', 'CFG_3', 'CFG_4', 'CFG_5', 'CFG_6', 'CFG_7', 'CFG_8', 'CFG_9', 'THETA_PV',
                    'TIME_SCALER_PV', 'TIME_SCALER_CLOCK', 'TIME_NORMALIZED_SCALER' ]

good_tags = ['VERSION', 'ELEMENTS_TO_FIT', 'ELEMENTS_WITH_PILEUP', 'DETECTOR_ELEMENTS', 'CAL_OFFSET_[E_OFFSET]', 'CAL_SLOPE_[E_LINEAR]', 'CAL_QUAD_[E_QUADRATIC]', 'FWHM_OFFSET', 'FWHM_FANOPRIME',
         'COHERENT_SCT_ENERGY', 'COMPTON_ANGLE', 'COMPTON_FWHM_CORR', 'COMPTON_STEP', 'COMPTON_F_TAIL', 'COMPTON_GAMMA', 'COMPTON_HI_F_TAIL',
        'COMPTON_HI_GAMMA', 'STEP_OFFSET', 'STEP_LINEAR', 'STEP_QUADRATIC', 'F_TAIL_OFFSET', 'F_TAIL_LINEAR', 'F_TAIL_QUADRATIC', 'KB_F_TAIL_OFFSET',
          'KB_F_TAIL_LINEAR', 'KB_F_TAIL_QUADRATIC', 'GAMMA_OFFSET', 'GAMMA_LINEAR', 'GAMMA_QUADRATIC', 'SNIP_WIDTH', 'SI_ESCAPE_FACTOR',
        'LINEAR_ESCAPE_FACTOR', 'SI_ESCAPE_ENABLE', 'MAX_ENERGY_TO_FIT', 'MIN_ENERGY_TO_FIT']

def read_fit_params(fname):
    global good_tags
    params = dict()
    with open(fname, 'r') as f:
        lines = f.readlines()
    for i in lines:
        tags = i.split(':')
        if len(tags) > 1:
            if tags[0] in good_tags:
                if tags[0] == 'ELEMENTS_TO_FIT' or tags[0] == 'ELEMENTS_WITH_PILEUP':
                    params[tags[0]] = tags[1].strip('\n')
                else:
                    params[tags[0]] = float(tags[1].strip('\n'))
    if 'ELEMENTS_TO_FIT' not in params:
        params = None
    return params

def read_int_spec(h5name):
    int_spec = None
    with h5py.File(h5name, 'r') as f:
        # try to see if v10 layout, Non Negative Lease squares fitting tech was used
        if '/MAPS/int_spec' in f:
            int_spec = f['/MAPS/int_spec'][...]
        elif '/MAPS/Spectra/Integrated_Spectra/Spectra' in f:
            int_spec = f['/MAPS/Spectra/Integrated_Spectra/Spectra'][...]
    if int_spec is not None:
        # don't use spec that are all 0's
        if int_spec.sum() == 0:
            return None
        # don't support spec > 2048
        spec_len = len(int_spec)
        if spec_len > 2048:
            return None
        if spec_len < 2048:
            amt = 2048 - spec_len
            int_spec = np.append(int_spec, np.zeros(amt))
    return int_spec

def write_fit_params(h5_f, fp):
    '''
    Writes fit parameters (fp) to an hdf5 group and returns group id
    '''
    global group_start_id
    grp = h5_f.create_group(f'entry_{group_start_id:06}')
    group_start_id += 1
    # create  datawset for fit parameters
    grp.create_dataset("elements", data=fp['ELEMENTS_TO_FIT'])
    if 'ELEMENTS_WITH_PILEUP' in fp:
        grp.create_dataset("pileups", data=fp['ELEMENTS_WITH_PILEUP'])
    # remove elements and pileups
    del fp['ELEMENTS_TO_FIT']
    del fp['ELEMENTS_WITH_PILEUP']
    grp.create_dataset("fit_param_names", data=list(fp.keys()))
    grp.create_dataset("fit_param_values", data=list(fp.values()))
    return grp

def proc_dir(indir, outfile, ignore_avg):
    try:
        # process directory
        print (f'Processing: {indir}')
        override_files = glob(indir+"/maps_fit_parameters_override.txt*", recursive = False)
        for over in override_files:
            last = over[len(over)-1]
            detector = ''
            try:
                if last == 't':
                    # avg file or detector 0 for single element detectors
                    detector = ''
                else:
                    detector = last
            except:
                print('Failed to parse detector for override file '+over)
            if ignore_avg and detector == '':
                continue
            fit_params = read_fit_params(over)
            if fit_params is not None:
                # write fit params to group
                int_specs = []
                h5_files = glob(indir + '/img.dat/*.h5'+detector)
                for h5 in h5_files:
                    int_spec = read_int_spec(h5)
                    if int_spec is not None:
                        int_specs += [int_spec]
                if len(int_specs) > 0:
                    grp = write_fit_params(outfile, fit_params)
                    grp.create_dataset('int_spectra', data=int_specs, compression="gzip", compression_opts=9)
    except Exception as e:
        traceback.print_exc()
        print (e)

def recur_scan_dir(indir, outfile, ignore_avg):
    dir_list = glob(indir+"/**/", recursive = False)
    #print (dir_list)
    # search 
    img_dat_dir = list(i for i in dir_list if i.find('img.dat') > 1)
    if len(img_dat_dir) > 0:
        proc_dir(indir, outfile, ignore_avg)
    else:
        for i in dir_list:
            recur_scan_dir(i, outfile, ignore_avg)

def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-i', type=str,  help='Input directory to iterate over.')
    parser.add_argument('-o', type=str,  help='Output filename, hdf5.')
    parser.add_argument('--ignore_avg', action=argparse.BooleanOptionalAction,  help='Ignore Avg h5 and only parse detector.')
    args = parser.parse_args()
    print(args.i, args.o, args.ignore_avg)
    if args.i == None or args.o == None:
        print("Please use -i for input directory and -o for output filename")
        return -1
    # open out file and scan in dir
    with h5py.File(args.o, 'w') as outfile:
        if outfile == None:
            print('Error opening ',args.o, 'for writing to.')
            return -2
        recur_scan_dir(args.i, outfile, args.ignore_avg)
    return 0

if __name__ == '__main__':
    main()