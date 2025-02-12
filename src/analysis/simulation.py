"""
Module for simulating NBA games and outcomes.
"""

from typing import Any, Dict, Union

import numpy as np
import pandas as pd


def simulate_game(
    team1_stats: pd.Series,
    team2_stats: pd.Series,
    n_simulations: int = 10000
) -> Dict[str, Union[float, Dict[str, float]]]:
    """
    Simulate a game between two teams using Monte Carlo simulation.
    
    Args:
        team1_stats: Series containing team 1's statistics
        team2_stats: Series containing team 2's statistics
        n_simulations: Number of simulations to run
        
    Returns:
        Dictionary containing win probabilities and projected scores
    """
    # Calculate average pace for the game
    pace = np.mean([team1_stats['PACE'], team2_stats['PACE']])
    
    # Run Monte Carlo simulation
    team1_scores = []
    team2_scores = []
    
    for _ in range(n_simulations):
        # Simulate scores based on offensive and defensive ratings
        team1_score = np.random.normal(
            team1_stats['OFF_RATING'] * pace / 100,
            team1_stats['NET_RATING'].std()
        )
        team2_score = np.random.normal(
            team2_stats['OFF_RATING'] * pace / 100,
            team2_stats['NET_RATING'].std()
        )
        
        team1_scores.append(team1_score)
        team2_scores.append(team2_score)
    
    # Calculate win probabilities
    team1_wins = sum(t1 > t2 for t1, t2 in zip(team1_scores, team2_scores))
    
    return {
        "team1_win_prob": team1_wins / n_simulations,
        "team2_win_prob": 1 - (team1_wins / n_simulations),
        "average_score": {
            "team1": float(np.mean(team1_scores)),
            "team2": float(np.mean(team2_scores))
        },
        "score_std": {
            "team1": float(np.std(team1_scores)),
            "team2": float(np.std(team2_scores))
        }
    }

def simulate_season(
    team_stats: pd.DataFrame,
    n_simulations: int = 1000
) -> pd.DataFrame:
    """
    Simulate an entire season of games between all teams.
    
    Args:
        team_stats: DataFrame containing team statistics
        n_simulations: Number of simulations per matchup
        
    Returns:
        DataFrame containing projected win totals and probabilities
    """
    teams = team_stats['team'].unique()
    n_teams = len(teams)
    
    # Initialize results DataFrame with zeros
    results = pd.DataFrame(0.0, index=teams, columns=['projected_wins', 'win_pct'])
    
    # Simulate each matchup
    for i in range(n_teams):
        for j in range(i + 1, n_teams):
            team1 = teams[i]
            team2 = teams[j]
            
            # Get team stats
            team1_stats = team_stats[team_stats['team'] == team1].iloc[0]
            team2_stats = team_stats[team_stats['team'] == team2].iloc[0]
            
            # Simulate matchup
            sim_result = simulate_game(team1_stats, team2_stats, n_simulations)
            
            # Update win totals
            results.loc[team1, 'projected_wins'] += sim_result['team1_win_prob']
            results.loc[team2, 'projected_wins'] += sim_result['team2_win_prob']
    
    # Calculate win percentages
    total_games = n_teams - 1  # Each team plays every other team once
    results['win_pct'] = results['projected_wins'] / total_games
    
    return results 