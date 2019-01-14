from colicoords import SynthCellList, save, load, CellPlot
from colicoords.models import PSF, RDistModel, Memory
from colicoords.synthetic_data import draw_poisson, add_readout_noise
import matplotlib.pyplot as plt
import numpy as np
import mahotas as mh
from tqdm import tqdm
import time

def gen_synthcells(num):
    """Generates a list of synthetic cells"""
    #todo check numbers on l, r, curvature from real data
    lengths = np.random.normal(40, 7.5, num)
    bf_r = 6.245765530522576 # radius measured from brightfield r_dist
    r_factor = 1.5554007217841803  # Conversion from brightfield radius to binary radius (2018101)
    inner_membrane_factor = 1.314602664567288 # Conversion from brightfield radius to inner membrane radius (20181204)
    radii = np.random.normal(bf_r, 0.4, num) * r_factor
    curvatures = np.random.normal(0, 0.0075, num)

    st_num = list(np.random.normal(500, 50, size=2*num))  # Number of STORM localizations (membrane distributed) per cell
    st_ints = list(np.random.normal(200, 25, size=2*num))  # Fluorescence intensity of STORM localizations

    # Radial model for generating cytosolic background
    psf = PSF(sigma=1.54)
    rm = RDistModel(psf, r='equal', mem=Memory(verbose=0))

    cell_list = SynthCellList(lengths, radii, curvatures, pad_width=20)
#    bf_rdist = np.loadtxt('brightfield_r_dist.txt')
    x_out = np.genfromtxt('r_dist_cells_xvals_final.txt')
    # y_out[122:] = y_out[121]
    # y_out -= y_out[121]
    # y_out /= y_out.max()

    for cell, y_out in tqdm(zip(cell_list, yield_bf()), total=len(cell_list)):
        st_int = st_ints.pop()

        inner_radius = cell.coords.r / (r_factor * inner_membrane_factor)
        try:
            storm_table = cell.gen_storm_membrane(int(st_num.pop()), inner_radius, r_std=0.25, intensity_mean=st_int,
                                                  intensity_std=5 * np.sqrt(st_int))
        except ValueError:
            continue

        cell.data.add_data(storm_table, 'storm', 'storm_inner')
        storm_img = cell.gen_flu_from_storm('storm_inner', sigma_std=0.3)
        cell.data.add_data(storm_img, 'fluorescence', 'foci_inner')

        try:
            storm_table = cell.gen_storm_membrane(int(st_num.pop()), inner_radius + 100 / 80, r_std=0.25, intensity_mean=st_int,
                                                  intensity_std=5 * np.sqrt(st_int))
        except ValueError:
            continue

        cell.data.add_data(storm_table, 'storm', 'storm_outer')
        storm_img = cell.gen_flu_from_storm('storm_outer', sigma_std=0.3)
        cell.data.add_data(storm_img, 'fluorescence', 'foci_outer')

        r_scf = cell.coords.r / r_factor  # Scaling factor equal to one when cell radius equal to standard brightfield
        bf_img = np.interp(cell.coords.rc, r_scf*x_out, y_out)
        cell.data.add_data(bf_img, 'brightfield')

    return cell_list


def yield_bf():
    y_arr = np.loadtxt('r_dist_cells_yvals_final.txt')

    while True:
        idx = np.arange(len(y_arr))
        np.random.shuffle(idx)
        for i in idx:
            yield y_arr[i]


def measure_r(file_path):
    bf_rdist = np.loadtxt(file_path)
    x, y = bf_rdist.T

    mid_val = (np.min(y) + np.max(y)) / 2
    imin = np.argmin(y)
    imax = np.argmax(y)
    y_select = y[imin:imax] if imax > imin else y[imax:imin][::-1]
    x_select = x[imin:imax] if imax > imin else x[imax:imin][::-1]

    try:
        assert np.all(np.diff(y_select) > 0)
    except AssertionError:
        print('Radial distribution not monotonically increasing')

    r = np.interp(mid_val, y_select, x_select)
    return r


def test_bf():
    bf_rdist = np.loadtxt('brightfield_r_dist.txt')
    x_out, y_out = bf_rdist.T
    y_out -= y_out[-5:].mean()
    y_out /= y_out.max()
    cell_list = load('temp_cells.hdf5')
    cell = cell_list[0]

    plt.plot(y_out)
    plt.show()

    y_out[122:] = y_out[121]
    y_out -= y_out[121]
    y_out /= y_out.max()
    plt.plot(y_out)
    plt.show()
    bf_img = np.interp(cell.coords.rc, x_out, y_out)

    fig, axes = plt.subplots(1, 2)
    axes[0].imshow(cell.coords.rc)
    axes[1].imshow(bf_img)
    plt.show()


if __name__ == '__main__':

    #test_bf()
    #cell_list = gen_synthcells(25000)
    #save('cells_final.hdf5', cell_list)
    cell_list = load('cells_final_selected.hdf5')
    # print(cell_list[0].data.names)
    # b = np.array([len(cell.data.names) == 6 for cell in cell_list])
    # print(np.sum(b))
    #
    # save('cells_final_selected.hdf5', cell_list[b])




    #
    # olay = mh.overlay(cell_list[0].data.data_dict['brightfield'], red = cell_list[0].data.data_dict['binary'])
    # plt.imshow(olay)
    # plt.show()

    fig, axes = plt.subplots(1, 3)
    cp = CellPlot(cell_list[3])
    cp.imshow('binary', ax=axes[0])
    cp.imshow('brightfield', ax=axes[1], alpha=0.9, cmap='gray')
    cp.plot_storm(ax=axes[2], method='gauss')
    cp.plot_outline()
    plt.show()
    #


    fig, axes = plt.subplots(1, 3)
    cp = CellPlot(cell_list[3000])
    cp.imshow('binary', ax=axes[0])
    cp.imshow('brightfield', ax=axes[1], alpha=0.9, cmap='gray')
    cp.plot_storm(ax=axes[2], method='gauss')
    cp.plot_outline()
    plt.show()
    # cell_list[0].measure_r('brightfield', mode='mid')
    # print(cell_list[0].radius)
    # cp = CellPlot(cell_list[0])
    # #cp.imshow('binary', cmap='OrRd')
    # cp.imshow('foci_inner', alpha=0.9, cmap='gray')
    # cp.plot_storm(data_name='storm_inner')
    #
    #
    # cp.plot_outline()
    #
    # plt.show()
    #
    # cp.imshow('foci_outer', alpha=0.9, cmap='gray')
    # cp.plot_storm(data_name='storm_outer')
    # cp.plot_outline()
    #
    # plt.show()
    #
    # cp.plot_storm(method='gauss', data_name='storm_inner')
    # cp.plot_storm(method='gauss', data_name='storm_outer', alpha_cutoff=0.5)
    # plt.show()