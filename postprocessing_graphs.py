# pylint: disable=line-too-long

"""
    Convenience module to produce vaguely equivalent tables and graphs as present in
    Fieldsend et al (2014)
"""

import pickle

import pandas as pd  # pandas is a bit overkill, but it formats everything nicely!
from matplotlib import pyplot as plt


def main():

    """
    Generate the DataFrames, graphs, and stats

    :return: None
    """

    convergence_rates_e1 = pd.DataFrame(index=['Mean', 'St.D'])
    convergence_rates_e4 = pd.DataFrame(index=['Mean', 'St.D'])
    success_rates = pd.DataFrame(index=['1e-1', '1e-2', '1e-3', '1e-4', '1e-5'])
    peak_ratios = pd.DataFrame(index=['1e-1', '1e-2', '1e-3', '1e-4', '1e-5'])

    for function in range(1, 21):
        results = pickle.load(open('results/benchmarking_result_{}.pkl'.format(function), 'rb'))

        col_name = 'F{}'.format(function)
        index = function-1

        convergence_rates_e1.insert(index, col_name, results.ConvergenceRates[0])
        convergence_rates_e4.insert(index, col_name, results.ConvergenceRates[3])

        success_rates.insert(index, col_name, results.SuccessRate)
        peak_ratios.insert(index, col_name, results.PeakRatio)

        for i in results.SimulationSwarms:

            x_axis = [k for k, _ in i.items()]
            y_axis = [v for _, v in i.items()]

            plt.subplot(4, 5, function)  # subplot indexes from 1
            plt.plot(x_axis, y_axis, 'k-')

    plt.savefig('results/nmmso_benchmark.png')
    plt.show()

    pd.set_option('display.max_columns', None)  # make sure all columns are printed below
    print(convergence_rates_e1)
    print(convergence_rates_e4)
    print(success_rates)
    print(peak_ratios)

    # Table V from Fieldsend et al.
    table4 = pd.Series([
        peak_ratios.stack().median(),
        peak_ratios.stack().mean(),
        peak_ratios.stack().std()
    ])
    print(table4)

    # do we want to reproduce Fig. 3


if __name__ == '__main__':
    main()
