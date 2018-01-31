import numpy as np


def crossover(pairs, population):

    n, m = population.shape

    children = np.empty((len(pairs), m))
    for i, pair in enumerate(pairs):
        genes = population[pair, :]
        avg_genes = np.mean(genes, axis=0)
        temp = avg_genes.argsort(kind='heapsort')
        ranks = np.empty_like(temp)
        ranks[temp] = np.arange(m)
        children[i, :] = ranks

    return children
