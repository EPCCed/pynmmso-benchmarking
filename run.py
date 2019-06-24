import multiprocessing

import numpy as np

from cec2013.cec2013 import CEC2013
from pynmmso import Nmmso

import benchmarking as benchmarks


class CECFunction:
    def __init__(self, i):

        self.f = CEC2013(i)
        dim = self.f.get_dimension()

        self.mn = np.zeros(dim)
        self.mx = np.zeros(dim)

        # Get lower, upper bounds
        for k in range(dim):
            self.mn[k] = self.f.get_lbound(k)
            self.mx[k] = self.f.get_ubound(k)

    def fitness(self, x):
        res = self.f.evaluate(x)

        # 1D problems return an array but other problems return a scalar - so we need to handle this
        if type(res) in [np.float64, float]:
            return res
        return res[0]

    def get_bounds(self):
        return self.mn, self.mx


def nmmso_runner(func_num, benchmarking=False):

    # Simplest way of running a multiprocessing job is to have the process as a single function,
    # rather than try and shoehorn it into a class

    #
    # for benchmarking we set up some loops to run all needed:
    #  - 20 problems
    #  - PR and SR for all accuracy levels (doesn't need a rerun of the simulations)
    #  - CR for accuracy level 1e-4
    #

    simulation_runs = 2
    max_evals = CEC2013(func_num).get_maxfes()
    problem = CECFunction(func_num)
    nmmso = Nmmso(problem)

    if benchmarking:
        bm = benchmarks.Benchmarking()

        for i in range(simulation_runs):

            print('simulation run {} of function {}'.format(i, func_num))

            bm.run_info(problem, nmmso, simulation_runs, func_num)

            while nmmso.evaluations < max_evals:
                nmmso.iterate()

                if not all(bm.all_found):
                    bm.total_swarms[nmmso.evaluations] = bm.check_convergence()

            bm.benchmarking_result.SimulationSwarms.append(bm.total_swarms)
            bm.add_convergence()
            bm.all_found = [False for _ in range(len(bm.accuracies))]

        bm.calculate_stats(export_data=True)

    else:
        for i in range(simulation_runs):

            print('simulation run {} of function {}'.format(i, func_num))

            while nmmso.evaluations < max_evals:
                nmmso.iterate()


def main():

    jobs = []
    for j in range(1, 12):

        process = multiprocessing.Process(target=nmmso_runner, args=(j, True))
        jobs.append(process)
        process.start()


if __name__ == "__main__":
    main()
