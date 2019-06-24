import csv
import logging
import os

from dataclasses import dataclass
import statistics
import pickle

import numpy as np

from cec2013.cec2013 import CEC2013, how_many_goptima


@dataclass
class BenchmarkingResults:

    # all the raw data
    raw_data: list = None

    # number of simulation runs used
    SimulationRuns: int = None

    # list of Peak Ratios for all accuracy levels
    PeakRatio: list = None

    # list of Success Rates for all accuracy levels
    SuccessRate: list = None

    # ConvergenceEvals: number of function evaluations required to reach
    # convergence (at each accuracy rate)
    ConvergenceEvals: list = None

    # ConvergenceRates: average and std dev (over total number of simulation runs )
    # of number of function evaluations
    # required to reach convergence (per accuracy)
    ConvergenceRates: list = None

    # number of swarms in nmmso when convergence has been reached (at each accuracy rate)
    ConvergenceSwarms: list = None

    # number of successful simulations (at each accuracy rate)
    SuccessfulSimulations: list = None

    # number of swarms at each iteration
    SimulationSwarms: list = None


class Benchmarking:

    def __init__(self):

        logging.basicConfig(level=logging.WARNING)

        self.problem = None
        self.nmmso = None
        self.simulation_runs = None
        self.func_num = None
        self.locations = None
        self.c_found = None
        self.raw_data = None
        self.counts = None
        self.convergences = None
        self.successful_runs = None
        self.total_swarms = {}
        self.max_evals = None

        self.accuracies = [pow(10, -i) for i in range(1, 6)]

        self.all_found = [False for _ in range(len(self.accuracies))]

        self.convergence_evaluation = [None] * len(self.accuracies)
        self.convergence_swarms = [None] * len(self.accuracies)

        self.benchmarking_result = BenchmarkingResults()
        self.benchmarking_result.ConvergenceEvals = []
        self.benchmarking_result.ConvergenceSwarms = []

        self.benchmarking_result.raw_data = []
        self.benchmarking_result.SuccessfulSimulations = [0] * len(self.accuracies)

        self.benchmarking_result.SimulationSwarms = []

        if not os.path.exists("results"):
            os.makedirs("results")

    def __str__(self):
        return 'id: {}\nnmmso: {}'.format(id(self), self.nmmso)

    def run_info(self, problem, nmmso, simulation_runs, func_number):
        self.problem = problem
        self.nmmso = nmmso
        self.benchmarking_result.SimulationRuns = self.simulation_runs = simulation_runs
        self.func_num = func_number
        self.total_swarms = {}

        self.max_evals = CEC2013(self.func_num).get_maxfes()

    def _export_data(self):

        with open("results/{}.csv".format(self.func_num), 'w', newline='') as raw_data_csv:
            writer = csv.writer(raw_data_csv)
            writer.writerow(['0.1', '0.01', '0.001', '0.0001', '0.00001']*3)
            writer.writerows(self.benchmarking_result.raw_data)

        pickle.dump(self.benchmarking_result,
                    open('results/benchmarking_result_{}.pkl'.format(self.func_num),
                         'wb'))

    def check_convergence(self):

        #
        # this is to help find the convergence rate. We need to know how quickly the
        # global optima are found
        #  - this is different to just returning the swarms at the end because most of the work
        #    of the algorithm could just be finding a slightly more optimal solution from an
        #    already optimal solution!
        #
        #  - we want to know at which evaluation all global optima have been found:
        #       however, 'evaluation' refers to 'number of times the objective function is
        #       evaluated', rather than the actual iterations of the algorithm (and total
        #       evaluations made by the end of the final iteration) which is the only metric
        #       we can measure. Each iteration of the algorithm may evaluate the objective
        #       function many times, so, as with Jonathan's original code, there may be a very
        #       slight discrepancy between the absolute true number of evaluations, and the
        #       number of evaluations returned
        #

        global_optima_fitness = self.problem.f.get_fitness_goptima()
        n_global_optima = self.problem.f.get_no_goptima()

        # only count the number of swarms when the accuracy is less than 1e-5,
        # so we can generate Fig. 2 in Fieldsend et al.
        accuracy = 1e-5
        self.c_found = False
        n_fittest = sum([abs(swarm.mode_value - global_optima_fitness) <= accuracy
                         for swarm in self.nmmso.swarms])
        nswarms = None
        if n_fittest <= n_global_optima and self.c_found is False:
            nswarms = len(self.nmmso.swarms)
            self.c_found = True

        for accuracy_index, accuracy in enumerate(self.accuracies):

            if self.all_found[accuracy_index] is False:

                n_fittest = sum([abs(swarm.mode_value - global_optima_fitness) <= accuracy
                                 for swarm in self.nmmso.swarms])

                if n_fittest == n_global_optima:
                    self.all_found[accuracy_index] = True
                    self.convergence_evaluation[accuracy_index] = self.nmmso.evaluations
                    self.convergence_swarms[accuracy_index] = len(self.nmmso.swarms)

        return nswarms

    def add_convergence(self):

        self.locations = [s.mode_location for s in self.nmmso.swarms]
        convergence = [self.max_evals if c is None else c for c in self.convergence_evaluation]
        self.benchmarking_result.raw_data.append(self.find_noptima() +
                                                 convergence +
                                                 self.convergence_swarms)
        self.benchmarking_result.ConvergenceEvals.append(convergence)
        self.benchmarking_result.ConvergenceSwarms.append(self.convergence_swarms)

    def calculate_stats(self, export_data=False):

        # since we want to do things by accuracy, it's much easier if we
        # transpose the 2D array we have:
        self.raw_data = list(map(list, zip(*self.benchmarking_result.raw_data)))

        self.benchmarking_result.PeakRatio = []
        self.benchmarking_result.SuccessRate = []
        self.benchmarking_result.ConvergenceRates = []

        for accuracy_index in range(len(self.accuracies)):
            self.counts = self.raw_data[accuracy_index]
            self.successful_runs = self.benchmarking_result.SuccessfulSimulations[accuracy_index]
            self.convergences = self.raw_data[accuracy_index + len(self.accuracies)]
            self.convergence_swarms = self.raw_data[accuracy_index + 2 * len(self.accuracies)]

            cs_ave, cs_sd = self.find_convergence_speed()

            self.benchmarking_result.PeakRatio.append(self.find_peak_ratio())
            self.benchmarking_result.SuccessRate.append(self.find_success_rate())
            self.benchmarking_result.ConvergenceRates.append((cs_ave, cs_sd))

        print("=" * 70)
        print("Benchmarking result for the {} runs: "
              "peak ratio: {} "
              "success rate: {} "
              "convergence speed average / sd {}".format(
                  self.simulation_runs,
                  self.benchmarking_result.PeakRatio,
                  self.benchmarking_result.SuccessRate,
                  self.benchmarking_result.ConvergenceRates))

        if export_data:
            self._export_data()

        self.benchmarking_result.raw_data = self.raw_data

    def find_noptima(self):

        locations = np.array(self.locations)
        noptima = []

        for i, accuracy in enumerate(self.accuracies):

            count, _ = how_many_goptima(locations, CEC2013(self.func_num), accuracy)

            if count == CEC2013(self.func_num).get_no_goptima():
                self.benchmarking_result.SuccessfulSimulations[i] += 1

            noptima.append(count)

            logging.debug("~"*70)
            logging.debug("In the current population there exist {}"
                          "global optimizers (accuracy: {})".format(count, accuracy))
            # print("Global optimizers: {}".format(seeds))

        return noptima

    def find_peak_ratio(self):

        """
            From Eqtn 4 in Fieldsend / Eqtn 1 in Benchmarking paper

            we need number of runs, number of global peaks, and total number of global optima found
        """

        return sum(self.counts) / (self.simulation_runs * CEC2013(self.func_num).get_no_goptima())

    def find_success_rate(self):

        """
            From Eqtn 2 in Benchmarking paper

            we need Number of Successful Runs and Number of Runs
        """

        return self.successful_runs / self.simulation_runs

    def find_convergence_speed(self):

        """
            From Eqtn 3 in Benchmarking paper
              - for each of the 50 runs, we need to find the number of evaluations it takes
                to find all global optima

            I've added in appropriate code in nmmso.Nmmso.find_convergence() to calculate
            this for each run

        """

        # sanity check:
        if not len(self.convergences) == self.benchmarking_result.SimulationRuns:
            print("Check why length of self.convergence_evals isn't the correct length")
            return None, None

        average = sum(self.convergences) / self.benchmarking_result.SimulationRuns
        std_dev = statistics.stdev(self.convergences)
        return average, std_dev
