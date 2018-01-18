from oct2py import octave
import timeit
octave.addpath('/home/alexander/Documents/MATLAB/matpower6.0')
octave.addpath('/home/alexander/Documents/MATLAB/matpower6.0/@opf_model')
octave.addpath('/home/alexander/Documents/MATLAB/opf_solvers/minopf5.1_linux')
octave.addpath('/home/alexander/Documents/MATLAB/opf_solvers/tspopf5.1_linux64')


def test_solver(solver, case):

    options = octave.mpoption('opf.ac.solver', solver)
    base_case = octave.loadcase(case)

    start = timeit.default_timer()
    base_result = octave.runopf(base_case, options)
    stop = timeit.default_timer()

    return stop - start

