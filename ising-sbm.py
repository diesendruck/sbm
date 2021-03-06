# coding: utf-8

import numpy as np
import matplotlib.pyplot as plt
import os
import time
from datetime import datetime

def main(verbose=False):
    # Use same adjacency matrix for all iterations of other variables.
    n = 50
    runs_per_theta = 5
    num_unique_thetas = 6
    p1 = 0.9
    p2 = 0.7
    px = 0.01

    # Create variable set for trial runs.
    var_set = [[n, p1, p2, px, 10],
               [n, p1, p2, px, 5],
               [n, p1, p2, px, 1],
               [n, p1, p2, px, -1],
               [n, p1, p2, px, -5],
               [n, p1, p2, px, -10]]

    # Set up storage for sampled plots of each theta value.
    plot_dict = {i:[] for i in range(num_unique_thetas)}

    # Sample several plots for each theta value.
    for i, v in enumerate(var_set):
        print("sampling "+str(i))
        n, p_pos, p_neg, p_btwn, theta_fill_value = v
        for _ in xrange(runs_per_theta):
            a = sample_a(n, p_pos, p_neg, p_btwn, theta_fill_value, verbose)
            plot_dict[i].append(a)

    print("visualizing...")
    # Generate image with results and store to directory.
    visualize(plot_dict, var_set, runs_per_theta, num_unique_thetas)
    return a

def visualize(plot_dict, var_set, runs_per_theta, num_unique_thetas):
    """Plot test figures."""
    # Create plot with subplots.
    fig, axes = plt.subplots(runs_per_theta, num_unique_thetas, figsize=(8,8))
    axes = axes.ravel()

    # Make title using the fixed parameters of the test.
    # This is correct, only if all cases in var_set use same p1, p2, q.
    vars1 = var_set[0]
    plt.suptitle((r'$A$-Matrix: '+r'$p_1={}$, '+r'$p_2={}$, '+r'$q={}$').format(
                  vars1[1], vars1[2], vars1[3]))

    # Create subplots with several trials per unique theta.
    for i in xrange(num_unique_thetas):
        for j in xrange(runs_per_theta):
            start_index = i
            plot_index = start_index+j*num_unique_thetas
            # For mixed_theta, don't show theta titles.
            #axes[start_index].set_title(r'$\theta={}$'.format(var_set[i][4]))
            axes[plot_index].imshow(plot_dict[i][j],interpolation='none', cmap='GnBu')
            axes[plot_index].tick_params(labelsize=6)

    # Save figures to directory.
    path = '/Users/mauricediesendruck/Google Drive/0-LIZHEN RESEARCH/sbm/'
    os.chdir(path)
    plt.savefig('fig-'+time.strftime('%Y%m%d_%H:%M:%S')+'.png', format='png',
                dpi=1200)

def sample_a(n, p_pos, p_neg, p_btwn, theta_fill_value, verbose):
    theta = np.empty([n, n]); theta.fill(theta_fill_value)
    mixed_theta = True
    if mixed_theta:
        # Make arbitrary theta matrix to see effect on sampled A-matrices.
        theta = make_mixed_theta(theta)
    z = sample_ising(theta)
    q = build_q_matrix(z, p_pos, p_neg, p_btwn)
    a = sample_sbm(q, n)
    a = a[:, np.argsort(z)][np.argsort(z), :]

    if verbose==True:
        summarize(n, p_pos, p_neg, p_btwn, theta_fill_value, z, q, a)
    return a

def make_mixed_theta(theta):
    """ Define mixed theta matrix."""
    n = len(theta)
    theta.fill(0)
    if False:
        np.fill_diagonal(theta, 5)
        rng = np.arange(n-1); theta[rng, rng+1] = 5
        rng = np.arange(n-2); theta[rng, rng+2] = 5
        rng = np.arange(n-3); theta[rng, rng+3] = 5
    if True:
        theta[:, [0, 1, 2, 3, 4]] = 5
    theta = sym_matrix(theta)
    return theta

def summarize(n, p_pos, p_neg, p_btwn, theta_fill_value, z, q, a):
    print('N: ', n)
    print('Pr(1): ', p_pos)
    print('Pr(-1): ', p_neg)
    print('Pr(between): ', p_btwn)
    print('Theta fill value: ', theta_fill_value)
    print
    print("Z vector: ")
    print(z)
    print("q matrix:")
    print(q)
    print("For q: ", check_symmetry(q))
    print("a matrix:")
    print(a)
    print("For a: ", check_symmetry(a))

def sample_adj_matrix(n, p):
    """Builds random adjacency matrix.

    Creates nxn adjacency matrix (1s and 0s) representing edges between nodes.
    Each edge is sampled as an independent Bernoulli random variable with
    probability p.

    Args:
        n: Number of nodes, and size of matrix adjacency matrix.
        p: Bernoulli probabiity for each edge.

    Returns:
        adj: Adjacency matrix.
    """
    adj = np.asarray([[rbern(p) for j in range(n)] for i in range(n)])
    adj = sym_matrix(adj)
    np.fill_diagonal(adj, 0)
    return adj

def set_mixed_theta():
    pass
def build_q_matrix(z, p_pos, p_neg, p_btwn):
    """Builds q matrix from stochastic block model.

    Compares each element in z to every other element in z, assigning link
    probabilities according to the agreement between pairs of elements.

    Args:
        z: Vector of ising assignments.
        p_pos: Link probability for pair of elements in cluster +1.
        p_neg: Link probability for pair of elements in cluster -1.
        p_btwn: Link probability for pair of elements in opposite clusters.

    Returns:
        q: Q matrix of pairwise link probabilities, given the stochastic block
            model.
    """

    def cond(i, j):
        """Determines which probability value applies for a given pair.

        Args:
            i: Reference index of z vector.
            j: Comparison index of z vector.

        Returns:
            p: Probability value.
        """
        # Probability to return, which gets reassigned given conditions.
        p = 0

        # A point and itself gets a zero, so q has zeros on diagonal.
        if i == j:
            p = 0
        else:
            # When reference element is 1, return within-cluster-1 probability
            # or cross prob.
            if z[i] == 1:
                if z[i] == z[j]:  # if pair is equal, give cluster 1 probabiity
                    p = p_pos
                else:
                    p = p_btwn
            # When reference element is -1, return within-cluster-(-1)
            # probability or cross prob.
            elif z[i] == -1:
                if z[i] == z[j]:
                    p = p_neg
                else:
                    p = p_btwn
            else:
                p = "z[i] not in [1, -1]"
        return p

    n = len(z)
    # Evaluate over all z indices; here, indices are the range 0 to n-1.
    q = np.asarray([[cond(i, j) for j in range(n)] for i in range(n)])
    return q

def check_symmetry(q): return("Symmetry: ", (q.transpose() == q).all())

def sample_sbm(q, n):
    """Samples from the Stochastic Block Model (SBM) link probability matrix.

    Args:
        q: The link probability matrix.
        n: The number of rows (and equivalently, columns) of the matrix q.

    Returns:
        a: An instance of the link matrix, based on SBM probability matrix.
    """
    a = np.asarray([[rbern(q[i, j]) for j in range(n)] for i in range(n)])
    a = sym_matrix(a)
    return a

def rbern(p):
    r = np.random.binomial(1, p)
    return r

def sym_matrix(matrix, part="upper"):
    """Makes square, symmetric matrix, from matrix and upper/lower flag.

    Requires: import numpy as np

    Supply a square matrix and a flag like "upper" or "lower", and copy the
    chosen matrix part, symmetrically, to the other part. Diagonals are left
    alone. For example:
    matrix <- [[8, 1, 2],
               [0, 8, 4],
               [0, 0, 8]]
    sym_matrix(matrix, "upper") -> [[8, 1, 2],
                                    [1, 8, 4],
                                    [2, 4, 8]]

    Args:
        matrix: Square matrix.
        part: String indicating "upper" or "lower".

    Returns:
        m: Symmetric matrix, with either upper or lower copied across the
            diagonal.
    """
    n = matrix.shape[0]
    upper_indices = np.triu_indices(n, k=1)
    lower_indices = upper_indices[1], upper_indices[0]
    m = np.copy(matrix)
    if part=="upper":
        m[lower_indices] = m[upper_indices]
    elif part=="lower":
        m[upper_indices] = m[lower_indices]
    else:
        print("Give a good 'part' definition, e.g. 'upper' or 'lower'.")

    return m

def sample_ising(theta):
    """Given a matrix of agreement parameters, samples binary ising vector.

    Samples vector of 1's and -1's from a Gibbs sampled Ising Distribution.

    Args:
        theta: Agreement parameter matrix; one agreement coefficient for each
            pair of nodes.

    Returns:
        z_sample: Vector of n values, each either 1 or -1.
    """
    # Set up parameters and variable storage.
    n = len(theta)  # Number of nodes in graph.
    num_trials = 500  # Number of times to run the Gibbs sampler.
    burn_in = 300  # Number of Gibbs samples to discard; must be < num_trials.
    z_chain = np.zeros([num_trials, n])  # Storage for Gibbs samples, by row.

    # Initialize and store first configuration of z's.
    z0 = np.random.choice([-1, 1], n)  # Initialize z's.
    z_chain[0,:] = z0  # Store initial values as first row of z_chain.

    # Run Gibbs.
    for t in range(1, num_trials):
        z = z_chain[t-1,:]
        for i in range(n):
            # Sample each z from its full Ising model conditional.
            # pi(z_i|z_not_i) = (1/C)*exp(sum(theta*z_i*z_j)), for j's with
            #     edges to i [...actually, edge condition irrelevant here].
            # Evaluate for z_i=-1 and z_i=1, normalize, then sample.
            summation_terms_neg1 = [theta[i, j]*(-1)*z[j] if j!=i else 0 for j in range(n)]
            summation_terms_pos1 = [theta[i, j]*(1)*z[j] if j!=i else 0 for j in range(n)]
            pn = unnorm_prob_neg1 = np.exp(sum(summation_terms_neg1))
            pp = unnorm_prob_pos1 = np.exp(sum(summation_terms_pos1))
            # Normalize probabilities.
            pr_neg1 = pn/(pn+pp)
            pr_pos1 = pp/(pn+pp)
            # Sample z_i
            z_i_value = np.random.choice([-1, 1], p=[pr_neg1, pr_pos1])
            # Store z_i value in z_chain.
            z_chain[t, i] = z_i_value

    # Sample a z from the z_chain.
    sample_index = np.random.randint(burn_in, len(z_chain))
    z_sample = z_chain[sample_index,:]

    return z_sample


start_time = datetime.now()
a = main(verbose=False)
print datetime.now() - start_time


