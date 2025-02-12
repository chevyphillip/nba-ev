"""
Interactive NBA Statistics Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

def load_data(date_str: str) -> dict:
    """Load NBA data from Excel file."""
    data_path = Path(f"data/nba_stats_{date_str}.xlsx")
    
    data = {}
    with pd.ExcelFile(data_path) as excel:
        for sheet_name in excel.sheet_names:
            data[sheet_name] = pd.read_excel(excel, sheet_name)
    return data

def create_team_comparison(team_stats: pd.DataFrame):
    """Create interactive team comparison visualization."""
    fig = px.scatter(
        team_stats,
        x='offensive_rating',
        y='defensive_rating',
        color='win_pct',
        size='possessions',
        hover_data=['team', 'win_pct', 'net_rating'],
        title='Team Offensive vs Defensive Ratings',
        labels={
            'offensive_rating': 'Offensive Rating',
            'defensive_rating': 'Defensive Rating',
            'win_pct': 'Win Percentage'
        }
    )
    
    # Add quadrant lines
    fig.add_hline(y=team_stats['defensive_rating'].median(), line_dash="dash", line_color="gray")
    fig.add_vline(x=team_stats['offensive_rating'].median(), line_dash="dash", line_color="gray")
    
    return fig

def create_player_distribution(player_stats: pd.DataFrame, stat_column: str, stat_name: str):
    """Create interactive player distribution visualization."""
    fig = go.Figure()
    
    # Add violin plot
    fig.add_trace(go.Violin(
        y=player_stats[stat_column],
        box_visible=True,
        line_color='blue',
        meanline_visible=True,
        fillcolor='lightblue',
        opacity=0.6,
        name=stat_name
    ))
    
    # Add individual points for top players
    top_players = player_stats.nlargest(10, stat_column)
    fig.add_trace(go.Scatter(
        x=[0] * len(top_players),
        y=top_players[stat_column],
        mode='markers+text',
        name='Top Players',
        text=top_players['name'],
        textposition="top right",
        marker=dict(color='red', size=10),
        hovertemplate="%{text}<br>" + f"{stat_name}: %{{y}}<extra></extra>"
    ))
    
    fig.update_layout(
        title=f'Distribution of {stat_name}',
        showlegend=False,
        hovermode='closest'
    )
    
    return fig

def create_matchup_analysis(matchups: pd.DataFrame, team_stats: pd.DataFrame):
    """Create interactive matchup analysis visualization."""
    merged_data = pd.merge(
        matchups,
        team_stats[['team', 'offensive_rating', 'defensive_rating']],
        left_on='home_team',
        right_on='team'
    ).merge(
        team_stats[['team', 'offensive_rating', 'defensive_rating']],
        left_on='away_team',
        right_on='team',
        suffixes=('_home', '_away')
    )
    
    fig = px.scatter(
        merged_data,
        x='offensive_rating_home',
        y='offensive_rating_away',
        hover_data=['home_team', 'away_team'],
        title='Matchup Analysis: Offensive Ratings',
        labels={
            'offensive_rating_home': 'Home Team Offensive Rating',
            'offensive_rating_away': 'Away Team Offensive Rating'
        }
    )
    
    # Add diagonal line
    fig.add_trace(go.Scatter(
        x=[merged_data['offensive_rating_home'].min(), merged_data['offensive_rating_home'].max()],
        y=[merged_data['offensive_rating_home'].min(), merged_data['offensive_rating_home'].max()],
        mode='lines',
        line=dict(dash='dash', color='gray'),
        name='Equal Rating Line'
    ))
    
    return fig

def main():
    st.set_page_config(page_title="NBA Statistics Dashboard", layout="wide")
    
    st.title("NBA Statistics Dashboard")
    
    # Load data
    try:
        data = load_data(st.sidebar.date_input("Select Date").strftime("%Y%m%d"))
    except FileNotFoundError:
        st.error("No data available for selected date")
        return
    
    # Sidebar filters
    st.sidebar.header("Filters")
    min_minutes = st.sidebar.slider("Minimum Minutes Played", 0, 48, 15)
    selected_teams = st.sidebar.multiselect(
        "Select Teams",
        options=sorted(data['team_stats']['team'].unique())
    )
    
    # Apply filters
    if selected_teams:
        data['team_stats'] = data['team_stats'][data['team_stats']['team'].isin(selected_teams)]
        data['player_stats'] = data['player_stats'][data['player_stats']['team'].isin(selected_teams)]
    
    data['player_stats'] = data['player_stats'][data['player_stats']['mpg_x'] >= min_minutes]
    
    # Team Analysis Section
    st.header("Team Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(create_team_comparison(data['team_stats']), use_container_width=True)
    
    with col2:
        st.plotly_chart(create_matchup_analysis(data['matchups'], data['team_stats']), use_container_width=True)
    
    # Player Analysis Section
    st.header("Player Analysis")
    
    stat_options = {
        'Points Per Game': 'ppg_x',
        'Assists Per Game': 'apg_x',
        'Rebounds Per Game': 'rpg',
        'True Shooting %': 'TS_PCT'
    }
    
    selected_stat = st.selectbox("Select Statistic", list(stat_options.keys()))
    st.plotly_chart(
        create_player_distribution(
            data['player_stats'],
            stat_options[selected_stat],
            selected_stat
        ),
        use_container_width=True
    )

if __name__ == "__main__":
    main() 