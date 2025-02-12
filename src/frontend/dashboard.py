"""
Streamlit dashboard for NBA data visualization.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional

import altair as alt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.database.models import Base, Game, Player, Team

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database connection
engine = create_engine("sqlite:///data/nba.db")
Session = sessionmaker(bind=engine)

def load_data():
    """Load data from database."""
    session = Session()
    
    try:
        # Load team stats
        teams_df = pd.read_sql(
            """
            SELECT * FROM teams
            """,
            engine
        )
        
        # Load player stats
        players_df = pd.read_sql(
            """
            SELECT * FROM players
            WHERE games_played > 0
            """,
            engine
        )
        
        # Load game stats
        games_df = pd.read_sql(
            """
            SELECT * FROM games
            """,
            engine
        )
        
        return teams_df, players_df, games_df
    
    finally:
        session.close()

def plot_team_ratings(teams_df: pd.DataFrame):
    """Plot team offensive and defensive ratings."""
    fig = px.scatter(
        teams_df,
        x='offensive_rating',
        y='defensive_rating',
        text='name',
        title='Team Offensive vs Defensive Ratings',
        labels={
            'offensive_rating': 'Offensive Rating (points per 100 possessions)',
            'defensive_rating': 'Defensive Rating (points allowed per 100 possessions)'
        }
    )
    
    fig.update_traces(textposition='top center')
    st.plotly_chart(fig)

def plot_player_stats(players_df: pd.DataFrame):
    """Plot player statistics."""
    # Points vs Assists scatter plot
    fig1 = px.scatter(
        players_df,
        x='points',
        y='assists',
        text='name',
        title='Player Points vs Assists',
        labels={
            'points': 'Points per Game',
            'assists': 'Assists per Game'
        }
    )
    fig1.update_traces(textposition='top center')
    st.plotly_chart(fig1)
    
    # Shooting percentages
    shooting_stats = players_df[
        ['name', 'field_goal_pct', 'three_point_pct', 'free_throw_pct']
    ].dropna()
    
    fig2 = go.Figure()
    
    for stat in ['field_goal_pct', 'three_point_pct', 'free_throw_pct']:
        fig2.add_trace(go.Box(
            y=shooting_stats[stat],
            name=stat.replace('_', ' ').title()
        ))
    
    fig2.update_layout(title='Shooting Percentages Distribution')
    st.plotly_chart(fig2)

def plot_game_trends(games_df: pd.DataFrame):
    """Plot game-related trends."""
    # Total score trend
    games_df['date'] = pd.to_datetime(games_df['start_time']).dt.date
    daily_scores = games_df.groupby('date')['total_score'].mean().reset_index()
    
    fig = px.line(
        daily_scores,
        x='date',
        y='total_score',
        title='Average Total Score Trend',
        labels={
            'date': 'Date',
            'total_score': 'Average Total Score'
        }
    )
    st.plotly_chart(fig)
    
    # Home vs Away win distribution
    home_wins = games_df['home_win'].value_counts()
    fig2 = px.pie(
        values=home_wins.values,
        names=['Home Team Wins', 'Away Team Wins'],
        title='Home vs Away Team Wins'
    )
    st.plotly_chart(fig2)

def main():
    """Main function for the Streamlit dashboard."""
    st.title("NBA Data Analysis Dashboard")
    
    try:
        # Load data
        teams_df, players_df, games_df = load_data()
        
        # Sidebar filters
        st.sidebar.title("Filters")
        
        # Team analysis section
        st.header("Team Analysis")
        plot_team_ratings(teams_df)
        
        # Player analysis section
        st.header("Player Analysis")
        min_games = st.sidebar.slider(
            "Minimum Games Played",
            min_value=0,
            max_value=82,
            value=20
        )
        filtered_players = players_df[players_df['games_played'] >= min_games]
        plot_player_stats(filtered_players)
        
        # Game analysis section
        st.header("Game Analysis")
        plot_game_trends(games_df)
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        logger.error(f"Dashboard error: {str(e)}")

if __name__ == "__main__":
    main() 