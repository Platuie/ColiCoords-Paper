import matplotlib.pyplot as plt
import numpy as np
from colicoords import Cell, load, save, CellPlot, Data
from colicoords.support import running_sum
import matplotlib.gridspec as gridspec
from pycorrelate import ucorrelate
from scipy.ndimage.filters import uniform_filter1d
from brokenaxes import brokenaxes
import os



upscale = 1
cell_storm = load(r'D:\_processed_data\2018\20181204_lacy_sr\20181204_cell_10.hdf5')

save('storm_cell.cc', cell_storm)

fig_width = 8.53534 / 2.54

fig = plt.figure(figsize=(fig_width, 1.25*2*0.84*3.209210481625255))
frac_bot = 0.61

zx_min = 10
zx_max = 20
w_r = zx_max - zx_min

zy_max = 23
zy_min = 11
h_r = zy_max - zy_min

shape_l = cell_storm.data.binary_img.shape
rl = shape_l[1] / shape_l[0]
rr = w_r / h_r

top_grid = gridspec.GridSpec(2, 2, width_ratios=[rl, rr])
top_grid.update(bottom=frac_bot)

bot_grid = gridspec.GridSpec(3, 1)
bot_grid.update(top=frac_bot)


axes = np.empty((2,2), dtype=object)
for index, x in np.ndenumerate(axes):
    axes[index] = plt.subplot(top_grid[index])

for ax in axes.flatten():
    ax.tick_params(axis='x', labelbottom=False)
    ax.tick_params(axis='y', labelleft=False)

cp = CellPlot(cell_storm)
cp.imshow('binary', ax=axes[0, 0], cmap='gray_r', alpha=0.3)
cp.plot_storm(method='gauss', alpha_cutoff=0.3, ax=axes[0, 0], upscale=upscale, interpolation='spline16')
#cp.plot_storm(method='plot', ax=axes[0, 0], color='b', alpha=0.5, markersize=1)
cp.plot_outline(ax=axes[0, 0], alpha=0.5)
cp.plot_midline(ax=axes[0, 0], alpha=0.5)
axes[0, 0].plot([zx_min, zx_min, zx_max, zx_max, zx_min], [zy_min, zy_max, zy_max, zy_min, zy_min], color='k', linestyle='--')

cp.plot_storm(method='gauss', alpha_cutoff=0.3, ax=axes[0, 1], upscale=upscale, interpolation='spline16')
#cp.plot_storm(method='plot', ax=axes[0, 1], color='y', alpha=1, markersize=1.5)
cp.plot_outline(ax=axes[0, 1], alpha=0.5)
cp.plot_midline(ax=axes[0, 1], alpha=0.5)

axes[0, 1].set_xlim(zx_min, zx_max)
axes[0, 1].set_ylim(zy_max, zy_min)

cell_storm_opt = cell_storm.copy()
cell_storm_opt.optimize('storm')

cp = CellPlot(cell_storm_opt)
cp.imshow('binary', ax=axes[1, 0], cmap='gray_r', alpha=0.3)
cp.plot_storm(method='gauss', alpha_cutoff=0.3, ax=axes[1, 0], upscale=upscale, interpolation='spline16')
cp.plot_outline(ax=axes[1, 0], alpha=0.5)
cp.plot_midline(ax=axes[1, 0], alpha=0.5)
axes[1, 0].plot([zx_min, zx_min, zx_max, zx_max, zx_min], [zy_min, zy_max, zy_max, zy_min, zy_min], color='k', linestyle='--')


cp.plot_storm(method='gauss', alpha_cutoff=0.3, ax=axes[1, 1], upscale=upscale, interpolation='spline16')
cp.plot_outline(ax=axes[1, 1], alpha=0.5)
cp.plot_midline(ax=axes[1, 1], alpha=0.5)


axes[1, 1].set_xlim(zx_min, zx_max)
axes[1, 1].set_ylim(zy_max, zy_min)

axes[0, 0].set_ylabel("Initial")
axes[1, 0].set_ylabel("Final")

top_grid.tight_layout(fig, rect=[0.05, frac_bot, 1, 1], h_pad=0, w_pad=0)

p0 = axes[0, 0].get_position()
fig.text(0.0, p0.y0 + p0.height, 'A', fontsize=15)

x, y = cell_storm.data.data_dict['storm']['x'], cell_storm.data.data_dict['storm']['y']
perimeter = cell_storm.coords.calc_perimeter(x, y)

# Sampling points
x_out = np.linspace(0, cell_storm.circumference, num=20000, endpoint=True)
dx = np.diff(x_out)[0]
# Sum convolution with gaussian
y_out = running_sum(np.sort(perimeter), np.ones_like(perimeter), x_out, sigma=0.075)

# Autocorrelation
G = ucorrelate(y_out, y_out)

# Remove low-frequency component
G_m = uniform_filter1d(G, size=200)
acf = G - G_m


#https://stackoverflow.com/questions/11205037/detect-period-of-unknown-source
fourier = np.fft.fft(acf)/len(acf)
n = acf.size
freq = np.fft.fftfreq(n, d=dx)

#axes_bot = [plt.subplot(bot_grid[i]) for i in range(3)]

ax_loc = plt.subplot(bot_grid[0])
ax_loc.plot(x_out*(80/1000), y_out)
ax_loc.set_xlim(0, np.max(x_out)*(80/1000))
ax_loc.set_ylabel('Localizations')
ax_loc.set_xlabel('Distance ($\mu$m)', labelpad=0)
#axes_bot[0].set_title('Localizations along perimeter')
ax_loc.set_ylim(0)


bax_acf = plt.subplot(bot_grid[1])
bax_acf.plot(x_out*(80/1000), acf / acf.max())
#axes_bot[1].set_yticks([0, 1])
bax_acf.set_xlim(0, np.max(x_out)*(80/1000))
bax_acf.set_ylabel('Amplitude')

#axes_bot[1].set_title('Autocorrelation')
bax_acf.set_xlabel('Lag distance ($\mu$m)', labelpad=0)


#axes_bot[2].set_title('Fourier Transform')
ax_fft = plt.subplot(bot_grid[2])
ax_fft.set_yticks([0, 1])
ft = np.abs(fourier)[:n//2]
ft /= ft.max()
ax_fft.plot(80/freq[:n//2], ft)
ax_fft.set_xlim(0, 750)
ax_fft.set_ylim(0, 1)
ax_fft.set_xlabel('Period (nm)', labelpad=0)
ax_fft.set_ylabel('Ampltidute')
ax_fft.text(200, 0.65, '$\lambda_{max}$ = 56 nm')

bot_grid.tight_layout(fig, rect=[0.05, 0, 1, frac_bot], h_pad=0.5, w_pad=0)

p0 = ax_loc.get_position()
fig.text(0.0, p0.y0 + p0.height, 'B', fontsize=15)

p0 = bax_acf.get_position()
fig.text(0.0, p0.y0 + p0.height, 'C', fontsize=15)

p0 = ax_fft.get_position()
fig.text(0.0, p0.y0 + p0.height, 'D', fontsize=15)

plt.show()

output_folder = r'C:\Users\Smit\MM\Projects\05_Live_cells\manuscripts\ColiCoords\tex\Figures'
plt.savefig(os.path.join(output_folder, 'Figure4_test.pdf'), bbox_inches='tight', dpi=1000)
#