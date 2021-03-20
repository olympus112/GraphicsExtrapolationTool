import math
import numpy as np
from scipy.optimize import leastsq
import pylab as plt

if __name__ == '__main__':
    N = 5  # number of data points
    t = np.linspace(0, 4 * np.pi, N)
    f = 1.15247  # Optional!! Advised not to use
    data = 3.0 * np.sin(f * t + 0.001) + 0.5 #+ np.random.randn(N)  # create artificial data with noise
    # data = [2*math.sin(3*1+0.1)+0.5, 2*math.sin(3*2+0.1)+0.5, 2*math.sin(3*3+0.1)+0.5]

    guess_mean = np.mean(data)
    guess_std = 3 * np.std(data) / (2 ** 0.5) / (2 ** 0.5)
    guess_phase = 0
    guess_freq = 1
    guess_amp = 1

    # we'll use this to plot our first estimate. This might already be good enough for you
    data_first_guess = guess_std * np.sin(t + guess_phase) + guess_mean

    # Define the function to optimize, in this case, we want to minimize the difference
    # between the actual data and our "guessed" parameters
    # optimize_func = lambda x: x[0] * np.sin(x[1] * t + x[2]) + x[3] - data
    optimize_func = lambda x: x[0] * np.sin(x[1] * t + x[2]) + x[3] - data
    est_amp, est_freq, est_phase, est_mean = leastsq(optimize_func, [guess_amp, guess_freq, guess_phase, guess_mean])[0]

    # recreate the fitted curve using the optimized parameters
    data_fit = est_amp * np.sin(est_freq * t + est_phase) + est_mean

    # recreate the fitted curve using the optimized parameters

    fine_t = np.arange(0, max(t), 0.1)
    data_fit = est_amp * np.sin(est_freq * fine_t + est_phase) + est_mean

    plt.plot(t, data, '.')
    plt.plot(t, data_first_guess, label='first guess')
    plt.plot(fine_t, data_fit, label='after fitting')
    plt.legend()
    plt.show()