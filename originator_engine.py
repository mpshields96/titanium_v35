import numpy as np
from scipy.stats import poisson, norm

class TitaniumOriginator:
    """
    TITANIUM V32: THE ORIGINATOR ENGINE
    "Bottom-Up" Probability Generation.
    """
    def __init__(self):
        pass

    def run_trinity_simulation(self, mean, std_dev, line, iterations=10000):
        # 1. Define Scenarios (Ceiling/Floor/Median)
        ceiling_val = norm.ppf(0.90, loc=mean, scale=std_dev)
        floor_val = norm.ppf(0.10, loc=mean, scale=std_dev)

        # 2. Run Simulations
        sim_ceiling = np.random.normal(ceiling_val, std_dev * 0.8, iterations)
        sim_floor = np.random.normal(floor_val, std_dev * 0.8, iterations)
        sim_median = np.random.normal(mean, std_dev, iterations)

        # 3. Calculate Win Probs
        prob_ceiling = np.sum(sim_ceiling > float(line)) / iterations
        prob_floor = np.sum(sim_floor > float(line)) / iterations
        prob_median = np.sum(sim_median > float(line)) / iterations

        # 4. Trinity Weighting (20/20/60)
        return (prob_ceiling * 0.20) + (prob_floor * 0.20) + (prob_median * 0.60)

    def run_poisson_matrix(self, home_xg, away_xg):
        # Atomic Goal Protocol (10x10 Matrix)
        max_goals = 10
        home_probs = [poisson.pmf(i, home_xg) for i in range(max_goals)]
        away_probs = [poisson.pmf(i, away_xg) for i in range(max_goals)]

        home_win, draw, away_win = 0.0, 0.0, 0.0

        for h in range(max_goals):
            for a in range(max_goals):
                prob = home_probs[h] * away_probs[a]
                if h > a: home_win += prob
                elif h == a: draw += prob
                else: away_win += prob

        return home_win, draw, away_win