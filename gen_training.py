import h5py
import argparse
from glob import glob
import os

def read_xrf(h5name):
    counts = None
    channel_names = None
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

def scan_dir(indir, outfile, depth=1):
    dir_list = glob(indir+"/*/", recursive = False)
    if depth > 1:
        scan_dir(indir, outfile, depth-1)
    print (dir_list)


def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-id', type=str,  help='Input directory to iterate over')
    parser.add_argument('-of', type=str,  help='Output filename, hdf5 ')
    args = parser.parse_args()

    if args.id == None or args.of == None:
        print("Please use -id for input directory and -of for output filename")
        return -1

    outfile = h5py.File(args.of, 'w')
    if outfile == None:
        print('Error opening ',args.of, 'for writing to.')
        return -2
    
    print(args.id)

    scan_dir(args.id, outfile)
    
    outfile.close()
    return 0

if __name__ == '__main__':
    main()