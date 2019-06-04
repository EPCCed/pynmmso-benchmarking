import numpy as np
from cec2013.cec2013 import CEC2013
from nmmso import Nmmso


import benchmarking as bm


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

        # If seems that 1D problems return an array but other problems return a scalar -
        # so we need to handle this
        # CW: added float too (and the list) - but don't understand why it's needed
        if type(res) in [np.float64, float]:
            return res
        return res[0]

    def get_bounds(self):
        return self.mn, self.mx


class NmmsoRunner:

    #
    # for benchmarking stuff ideally we'd set up some loops to run all needed:
    #  - 20 problems
    #  - PR and SR for all accuracy levels (doesn't need a rerun of the simulations)
    #  - CR for accuracy level 1e-4
    #

    def __init__(self, func_num, benchmarking=False):

        self.func_num = func_num
        self.simulation_runs = 50

        max_evals = CEC2013(self.func_num).get_maxfes()

        if benchmarking:
            self.bm = bm.Benchmarking()

        for i in range(self.simulation_runs):

            print('simulation run {} of function {}'.format(i, func_num))

            self.problem = CECFunction(self.func_num)
            self.nmmso = Nmmso(self.problem)

            if benchmarking:
                self.bm.run_info(self.problem, self.nmmso, self.simulation_runs, self.func_num)

            while self.nmmso.evaluations < max_evals:
                self.nmmso.iterate()

                if benchmarking and not all(self.bm.all_found):
                    self.bm.total_swarms[self.nmmso.evaluations] = self.bm.check_convergence()

            # we should be able to move this to end of check_convergence,
            # but nmmso.iterative doesn't give any indication when it has finished
            if benchmarking:
                self.bm.benchmarking_result.SimulationSwarms.append(self.bm.total_swarms)
                self.bm.add_convergence()
                self.bm.all_found = [False for _ in range(len(self.bm.accuracies))]

        if benchmarking:
            self.bm.calculate_stats(export_data=True)
