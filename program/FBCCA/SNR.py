import mne
from GetDataSSVEP import GetData
import numpy as np
import matplotlib.pyplot as plt

def snr_spectrum(psd, noise_n_neighbor_freqs=1, noise_skip_neighbor_freqs=1):
    """Compute SNR spectrum from PSD spectrum using convolution.

    Parameters
    ----------
    psd : ndarray, shape ([n_trials, n_channels,] n_frequency_bins)
        Data object containing PSD values. Works with arrays as produced by
        MNE's PSD functions or channel/trial subsets.
    noise_n_neighbor_freqs : int
        Number of neighboring frequencies used to compute noise level.
        increment by one to add one frequency bin ON BOTH SIDES
    noise_skip_neighbor_freqs : int
        set this >=1 if you want to exclude the immediately neighboring
        frequency bins in noise level calculation

    Returns
    -------
    snr : ndarray, shape ([n_trials, n_channels,] n_frequency_bins)
        Array containing SNR for all epochs, channels, frequency bins.
        NaN for frequencies on the edges, that do not have enough neighbors on
        one side to calculate SNR.
    """
    # Construct a kernel that calculates the mean of the neighboring
    # frequencies
    averaging_kernel = np.concatenate((
        np.ones(noise_n_neighbor_freqs),
        np.zeros(2 * noise_skip_neighbor_freqs + 1),
        np.ones(noise_n_neighbor_freqs)))
    averaging_kernel /= averaging_kernel.sum()

    # Calculate the mean of the neighboring frequencies by convolving with the
    # averaging kernel.
    mean_noise = np.apply_along_axis(
        lambda psd_: np.convolve(psd_, averaging_kernel, mode='valid'),
        axis=-1, arr=psd
    )

    # The mean is not defined on the edges so we will pad it with nas. The
    # padding needs to be done for the last dimension only so we set it to
    # (0, 0) for the other ones.
    edge_width = noise_n_neighbor_freqs + noise_skip_neighbor_freqs
    pad_width = [(0, 0)] * (mean_noise.ndim - 1) + [(edge_width, edge_width)]
    mean_noise = np.pad(
        mean_noise, pad_width=pad_width, constant_values=np.nan
    )

    return psd / mean_noise


if __name__=='__main__':

    path = 'C:/Program Files (x86)/Neuracle/Neusen W/Data/2022/10/221029-1/data.bdf'
    raw = mne.io.read_raw_bdf(path)

    picks = ['POz','Oz','PO3','PO4','O1','O2']
    raw.pick_channels(picks)
    
    trigger_time = [12.131, 16.146,
                    18.167, 22.177,
                    24.198, 28.209,
                    30.230, 34.240,
                    36.262, 40.272,
                    42.292, 46.303,
                    48.324, 52.335,
                    54.354, 58.366,
                    60.386, 64.397,
                    66.418, 70.428,
                    72.449, 76.460,
                    78.480, 82.491,
                    84.511, 88.524,
                    90.543, 94.555,
                    96.575, 100.586,
                    102.606, 106.617,
                    108.637, 112.648,
                    114.669, 118.680,
                    120.700, 124.711,
                    126.732, 130.743]
    
    raw = raw.copy().crop(trigger_time[0],trigger_time[1])

    dataset=GetData() 

    raw=dataset.preProcessing(raw)

    epochs = mne.make_fixed_length_epochs(raw, duration=raw.times[-1])
    epochs = epochs[0]

    data = raw.get_data()
    
    tmin = 0.
    tmax = raw.times[-1]
    fmin = 1.
    fmax = 80.
    sfreq = epochs.info['sfreq']

    psds, freqs = mne.time_frequency.psd_welch(
        epochs,
        n_fft=int(sfreq * (tmax - tmin)),
        n_overlap=0, n_per_seg=None,
        tmin=tmin, tmax=tmax,
        fmin=fmin, fmax=fmax,
        window='boxcar',
        verbose=False)

    snrs = snr_spectrum(psds, noise_n_neighbor_freqs=3,
                        noise_skip_neighbor_freqs=1)


    fig, axes = plt.subplots(2, 1, sharex='all', sharey='none', figsize=(8, 5))
    freq_range = range(np.where(np.floor(freqs) == 1.)[0][0],
                       np.where(np.ceil(freqs) == fmax - 1)[0][0])

    psds_plot = 10 * np.log10(psds)
    psds_mean = psds_plot.mean(axis=(0, 1))[freq_range]
    psds_std = psds_plot.std(axis=(0, 1))[freq_range]
    axes[0].plot(freqs[freq_range], psds_mean, color='b')
    axes[0].fill_between(
        freqs[freq_range], psds_mean - psds_std, psds_mean + psds_std,
        color='b', alpha=.2)
    axes[0].set(title="PSD spectrum", ylabel='Power Spectral Density [dB]')

    # SNR spectrum
    snr_mean = snrs.mean(axis=(0, 1))[freq_range]
    snr_std = snrs.std(axis=(0, 1))[freq_range]

    axes[1].plot(freqs[freq_range], snr_mean, color='r')
    axes[1].fill_between(
        freqs[freq_range], snr_mean - snr_std, snr_mean + snr_std,
        color='r', alpha=.2)
    axes[1].set(
        title="SNR spectrum", xlabel='Frequency [Hz]',
        ylabel='SNR', ylim=[-2, 30], xlim=[fmin, fmax])
    fig.show()
    plt.show()
