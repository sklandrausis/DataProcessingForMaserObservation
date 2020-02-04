import sys
import numpy as np
import matplotlib.pyplot as plt
from astropy.modeling import models, fitting
from astropy.modeling.fitting import LevMarLSQFitter
from functools import reduce
import random
import pandas as pd


def compute_gauss(velocity, y_data, gauss_lines):
    indexes = [(np.abs(velocity - float(line))).argmin() for line in gauss_lines]
    mons = [max(y_data[index - 5:index + 5]) for index in indexes]
    gaussian = [models.Gaussian1D(mons[index], gauss_lines[index], 0.05, bounds={'stddev': (None, 0.15)}) for index in range(0, len(mons))]

    gg_init = reduce(lambda a, b: a+b, gaussian)
    fitting.SLSQPLSQFitter()
    fit = LevMarLSQFitter()
    gg_fit = fit(gg_init, velocity, y_data)

    return gg_fit


def generate_initial_populations(population_size):
    cepa_velocity = [-1.77, -2.41, -3.66, -4.01, -4.67]

    populations = []
    for i in range(0, population_size):
        population = []
        cepa_velocity = [-1.77, -2.41, -3.66, -4.01, -4.67]
        tmp = np.random.random()

        if tmp < 0.4:
            initial_population_size = len(cepa_velocity)

        elif 0.4 < tmp < 0.6:
            initial_population_size = len(cepa_velocity) + 2

        elif 0.6 < tmp < 0.9:
            initial_population_size = len(cepa_velocity)

        else:
            initial_population_size = len(cepa_velocity) + 1

        if initial_population_size == len(cepa_velocity):
            population = cepa_velocity

        elif initial_population_size == len(cepa_velocity) + 2:
            population = cepa_velocity
            population.append(population[-1] - tmp)
            population.append(population[-1] - tmp)

        elif initial_population_size == len(cepa_velocity) + 1:
            population = cepa_velocity
            population.append(population[-1] - tmp)

        populations.append(population)

    return populations


def fitness_evaluation(populations):
    test_data_file = "/home/janis/Documents/maser/output/NotSmooht/cepa/6668/cepa_00_01_03_15_Nov_2019_IRBENE_418.dat"
    velocity = np.loadtxt(test_data_file, usecols=(0,), unpack=True)
    y_data = np.loadtxt(test_data_file, usecols=(3,), unpack=True)
    fitness = np.zeros((len(populations)))

    i = 0
    for population in populations:
        gg_fit = compute_gauss(velocity, y_data, population)
        fitness[i] = np.sqrt(np.sum(np.abs(y_data**2 - gg_fit(velocity)**2)))
        i += 1

    return fitness


def select_elite(populations, fitness):
    selected_individuals_count = len(populations)//2
    if selected_individuals_count % 2 != 0:
        selected_individuals_count += 1

    df = pd.DataFrame({'fitness': fitness})
    fitness_of_selected_individuals = df.nsmallest(selected_individuals_count, 'fitness')
    selected_individuals_indexes = list(fitness_of_selected_individuals.to_dict()["fitness"].keys())
    tmp_p = np.array(populations)
    selected_individuals_indexes = sorted(selected_individuals_indexes)
    selected_individuals = tmp_p[selected_individuals_indexes]
    return selected_individuals


def pairing (elite):
    parents = []

    i = 0
    j = 1

    while j < len(elite):
        parents.append([elite[i], elite[j]])
        i += 1
        j += 1

    return parents


def mutations(parents):
    new_generations = []
    cepa_velocity = [-1.77, -2.41, -3.66, -4.01, -4.67]
    min_velocity_count = len(cepa_velocity)

    for parent in parents:
        if len(parent[0]) < min_velocity_count and len(parent[1]) < min_velocity_count:
            new_generation = parent[0]
            new_generations.append(new_generation)

        elif len(parent[0]) > min_velocity_count > len(parent[1]):
            new_generation = parent[0]
            new_generations.append(new_generation)

        elif len(parent[0]) < min_velocity_count < len(parent[1]):
            new_generation = parent[1]
            new_generations.append(new_generation)

        else:
            new_generation = cepa_velocity
            new_generation.extend(parent[0][len(cepa_velocity):len(parent[0])])
            new_generation.extend(parent[1][len(cepa_velocity):len(parent[1])])
            new_generation = list(set(new_generation))
            new_generation = sorted(new_generation, reverse=True)
            new_generations.append(new_generation)

    return new_generations


def plot_best_individual(populations):
    best_gauss_lines = populations[0]
    test_data_file = "/home/janis/Documents/maser/output/NotSmooht/cepa/6668/cepa_00_01_03_15_Nov_2019_IRBENE_418.dat"
    velocity = np.loadtxt(test_data_file, usecols=(0,), unpack=True)
    y_data = np.loadtxt(test_data_file, usecols=(3,), unpack=True)
    gg_fit = compute_gauss(velocity, y_data, best_gauss_lines)

    plt.plot(velocity, y_data, "r-", label="original data")
    plt.plot(velocity, gg_fit(velocity), "g*", label="modulate data")
    plt.show()


def main():
    generations = 1000
    population_size = 300

    populations = generate_initial_populations(population_size)
    fitness = fitness_evaluation(populations)
    selected_elite = select_elite(populations, fitness)
    parents = pairing(selected_elite)

    i = 0
    for gen in range(0, generations):
        print("i", i)
        if len(populations) < 2:
            break

        if min(fitness) < 0.0000001:
            break

        populations = mutations(parents)
        fitness = fitness_evaluation(populations)
        selected_elite = select_elite(populations, fitness)
        parents = pairing(selected_elite)

        i += 1

    print(populations, fitness)

    plot_best_individual(populations)
    sys.exit(0)


if __name__ == "__main__":
    main()