import h5py
import pyxrfmaps as px 
import numpy as np
import matplotlib.pyplot as plt
import argparse

element_csv_filename = "../reference/xrf_library.csv"
element_henke_filename = "../reference/henke.xdr"

def plot_results(name, idx, int_spec, fit_spec):
    i_ax = np.linspace(0,int_spec.size-1, int_spec.size)
    f_ax = np.linspace(0,fit_spec.size-1, fit_spec.size)
    fig, axs = plt.subplots(2,1)
    axs[0].plot(i_ax, int_spec)
    #axs[1,0].plot(i_ax, int_spec)
    axs[0].set_yscale('log')
    '''
    fft_spec = np.fft.fft(int_spec)
    freq = np.fft.fftfreq(fft_spec.size)
    axs[0,2].plot(freq, fft_spec.real**2 + fft_spec.imag**2)
    '''
    axs[0].plot(f_ax, fit_spec)
    axs[0].plot(f_ax, fit_spec)
    #axs[0,1].set_yscale('log')
    #
    #fft_fit_spec = np.fft.fft(fit_spec)
    #axs[0,2].plot(freq, fft_fit_spec.real**2 + fft_fit_spec.imag**2)
    
    diff_spec = np.abs(int_spec - fit_spec)
    axs[1].plot(i_ax, diff_spec)
    axs[1].plot(i_ax, diff_spec)
    #axs[1].set_yscale('log')
    #print(fft_fit_spec.imag)
    '''
    ffdiff = fft_spec - fft_fit_spec
    axs[1,2].plot(freq, ffdiff.real**2+ ffdiff.imag**2)
    '''
    print(f"/gen_training_xrf/output/{name}_{idx}.png")
    plt.savefig(f"/gen_training_xrf/output/{name}_{idx}.png", dpi=300)

def fit_spec(fit_rout, model, grp):
    print(grp.name)
    # Load fit parameters 
    po = px.ParamsOverride()
    trans = px.io.file.get_FILE_TAGS_TRANSLATION()
    s = grp['elements'][()]
    s = s.decode()
    el_list = [i.strip() for i in s.split(',')]
    el_list += ['COMPTON_AMPLITUDE', 'COHERENT_SCT_AMPLITUDE']
    po.fill_elements_from_dict(el_list, 'Si')
    param_names = grp['fit_param_names'][...]
    param_values = grp['fit_param_values'][...]
    for name, value in zip(param_names, param_values):
        if name.decode() in trans:
            name = trans[name.decode()]
        po.fit_params.add_parameter(px.Fit_Param(name, value))
    # Load dataset
    int_specs = grp['int_spectra']
    idx = 0
    po.fit_params.print()
    # Initialize model and fit routine with fit parameters
    model.update_fit_params_values(po.fit_params)
    for spectra in int_specs:
        #spectra = np.array(spectra)
        energy_range = px.get_energy_range(spectra.size, po.fit_params)
        fit_rout.initialize(model, po.elements_to_fit, energy_range)
        # Fit element counts
        #counts = fit_rout.fit_counts(model, spectra, po.elements_to_fit)
        #print(counts)
        # Get Fit Spectra 
        fit_spec = fit_rout.fit_spectra(model, spectra, po.elements_to_fit)
        max_val = np.amax(fit_spec)
        fit_spec = np.clip(fit_spec, 0.1, max_val)
        # Resize int_spec to match fit_spec
        spectra = spectra[energy_range.min:energy_range.max+1]
        max_val = np.amax(spectra)
        spectra = np.clip(spectra, 0.1, max_val) 
        # Plot both
        plot_results(grp.name, idx, spectra, fit_spec)
        idx += 1

def main():
    parser = argparse.ArgumentParser(description='Process some spectra.')
    parser.add_argument('-f', type=str,  help='input Filenae.')
    args = parser.parse_args()
    # initialize element info
    px.load_element_info(element_henke_filename, element_csv_filename)
    # Select fitting routine
    fit_rout = px.fitting.routines.nnls()
    # Use Gausian Model
    model = px.fitting.models.GaussModel()

    with h5py.File(args.f, 'r') as infile:
        if infile == None:
            print('Error opening ',args.f, 'for reading.')
            return -2
        for name, h5obj in infile.items():
            fit_spec(fit_rout, model, h5obj)
    return 0
    

if __name__ == '__main__':
    main()