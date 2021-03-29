import math
import numpy as np
from sklearn.metrics import r2_score
from scipy.optimize import leastsq
import pylab as plt

if __name__ == '__main__':
    N = 5  # number of data points
    t = np.linspace(0, N-1, N)
    # data = 3.0 * np.sin(0.5 * t + 0.2) + 0.5
    data = np.array([0.5, 1, 1.8, 1, 0.5])

    guess_mean = np.mean(data)
    guess_std = 3 * np.std(data) / (2 ** 0.5) / (2 ** 0.5)
    guess_phase = 0
    guess_freq = 1
    guess_amp = 1

    # we'll use this to plot our first estimate. This might already be good enough for you
    data_first_guess = guess_std * np.sin(guess_freq * t + guess_phase) + guess_mean

    optimize_func = lambda x: x[0] * np.sin(x[1] * t + x[2]) + x[3] - data
    est_amp, est_freq, est_phase, est_mean = leastsq(optimize_func, np.array([guess_amp, guess_freq, guess_phase, guess_mean]))[0]

    print(t)
    print(est_amp, est_freq, est_phase, est_mean)
    inverse_t = (np.arcsin((data - est_mean) / est_amp) - est_phase) / est_freq
    print(3-inverse_t[3], 4-inverse_t[4])
    print(inverse_t)

    # recreate the fitted curve using the optimized parameters
    data_fit = est_amp * np.sin(est_freq * t + est_phase) + est_mean
    print(r2_score(data, data_fit))

    # recreate the fitted curve using the optimized parameters
    fine_t = np.arange(0, max(t), 0.1)
    data_fine_fit = est_amp * np.sin(est_freq * np.arange(0, max(t), 0.1) + est_phase) + est_mean


    plt.plot(t, data, '.')
    plt.scatter(inverse_t, np.zeros(inverse_t.shape[0]))
    # plt.plot(t, data_first_guess, label='first guess')
    plt.plot(t, data_fit, label='after fitting')
    plt.plot(fine_t, data_fine_fit, label='after fine fitting')
    plt.legend()
    plt.show()