#!/usr/bin/env python3
"""
Script to create a Jupyter notebook for NBA data analysis.
"""

import json
import sys
from pathlib import Path

import nbformat as nbf


def create_analysis_notebook(output_path: Path) -> None:
    """
    Create a Jupyter notebook for NBA data analysis.
    
    Args:
        output_path: Path where the notebook should be saved
    """
    # Create a new notebook
    nb = nbf.v4.new_notebook()
    
    # Add markdown cell - Introduction
    nb.cells.append(nbf.v4.new_markdown_cell("""# NBA Stats Data Analysis

This notebook provides analysis and visualization of NBA statistics collected by our data collection pipeline.

## Data Sources
- Basketball Reference
- NBA API
- The Odds API

## Analysis Sections
1. Team Performance Analysis
2. Player Efficiency Analysis
3. Game Predictions
4. Betting Analysis
"""))
    
    # Add code cell - Setup and Imports
    nb.cells.append(nbf.v4.new_code_cell("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from pathlib import Path

# Import our analysis modules
from src.analysis.efficiency import (
    calculate_team_efficiency,
    calculate_player_efficiency,
    calculate_pace_factors
)
from src.analysis.simulation import simulate_game, simulate_season

# Set up visualization
plt.style.use('default')
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = [12, 8]

# Configure pandas display options
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 50)

# Enable inline plotting
%matplotlib inline"""))
    
    # Add markdown cell - Data Loading
    nb.cells.append(nbf.v4.new_markdown_cell("""## Data Loading

Load the most recent NBA statistics from our data collection pipeline."""))
    
    # Add code cell - Load Data
    nb.cells.append(nbf.v4.new_code_cell("""# Find most recent data file
data_dir = Path("data")
data_files = sorted(data_dir.glob("nba_stats_*.xlsx"), reverse=True)
if not data_files:
    raise FileNotFoundError("No data files found in data directory")
    
latest_file = data_files[0]
print(f"Loading data from {latest_file.name}")

# Load all sheets into a dictionary of dataframes
data = pd.read_excel(latest_file, sheet_name=None)

# Extract individual dataframes
team_stats = data['team_stats']
player_stats = data['player_stats']
team_efficiency = data['team_efficiency']
player_efficiency = data['player_efficiency']
pace_factors = data['pace_factors']

print("\\nAvailable data sheets:")
for sheet in data.keys():
    print(f"- {sheet}")"""))
    
    # Add markdown cell - Team Analysis
    nb.cells.append(nbf.v4.new_markdown_cell("""## Team Performance Analysis

Analyze team performance metrics including:
- Offensive and defensive ratings
- Pace factors
- Win percentages
- Scoring distributions"""))
    
    # Add code cell - Team Analysis
    nb.cells.append(nbf.v4.new_code_cell("""# Display basic team statistics
print("Team Stats Shape:", team_stats.shape)
print("\\nTeam Stats Summary:")
team_stats.describe()"""))
    
    # Add markdown cell - Visualizations
    nb.cells.append(nbf.v4.new_markdown_cell("""### Team Performance Visualizations

Create visualizations to better understand team performance metrics."""))
    
    # Add code cell - Create Visualizations
    nb.cells.append(nbf.v4.new_code_cell("""# Offensive vs Defensive Rating
plt.figure(figsize=(12, 8))
plt.scatter(team_stats['OFF_RATING'], team_stats['DEF_RATING'], alpha=0.6)

# Add team labels
for i, txt in enumerate(team_stats['team']):
    plt.annotate(str(txt), (team_stats['OFF_RATING'].iloc[i], team_stats['DEF_RATING'].iloc[i]))

plt.xlabel('Offensive Rating')
plt.ylabel('Defensive Rating')
plt.title('Team Offensive vs Defensive Ratings')

# Add quadrant lines at median values
plt.axvline(team_stats['OFF_RATING'].median(), color='gray', linestyle='--', alpha=0.3)
plt.axhline(team_stats['DEF_RATING'].median(), color='gray', linestyle='--', alpha=0.3)

plt.show()"""))
    
    # Add markdown cell - Game Simulation
    nb.cells.append(nbf.v4.new_markdown_cell("""## Game Simulation

Simulate matchups between teams using Monte Carlo simulation."""))
    
    # Add code cell - Simulation Example
    nb.cells.append(nbf.v4.new_code_cell("""# Example: Simulate a game between two teams
team1 = "LAL"  # Los Angeles Lakers
team2 = "BOS"  # Boston Celtics

# Get team stats
team1_stats = team_stats[team_stats['team'] == team1].iloc[0]
team2_stats = team_stats[team_stats['team'] == team2].iloc[0]

# Run simulation
result = simulate_game(team1_stats, team2_stats, n_simulations=10000)

print(f"{team1} vs {team2} Simulation Results:")
print(f"{team1} win probability: {result['team1_win_prob']:.1%}")
print(f"{team2} win probability: {result['team2_win_prob']:.1%}")
print(f"\\nProjected Scores:")
print(f"{team1}: {result['average_score']['team1']:.1f} ± {result['score_std']['team1']:.1f}")
print(f"{team2}: {result['average_score']['team2']:.1f} ± {result['score_std']['team2']:.1f}")"""))
    
    # Save the notebook
    with open(output_path, 'w', encoding='utf-8') as f:
        nbf.write(nb, f)

def main():
    """Main function to create the notebook."""
    # Create notebooks directory if it doesn't exist
    notebooks_dir = Path("notebooks")
    notebooks_dir.mkdir(exist_ok=True)
    
    # Create the notebook
    output_path = notebooks_dir / "nba_analysis.ipynb"
    create_analysis_notebook(output_path)
    print(f"Created notebook at: {output_path}")
    print("You can now run 'jupyter notebook notebooks/nba_analysis.ipynb' to open it")

if __name__ == "__main__":
    main() 