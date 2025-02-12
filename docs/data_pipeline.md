## NBA Statistics Data Pipeline

### Data Collection

The pipeline collects data from two primary sources:

1. **Basketball Reference**
   - Columns collected:
     - `start_time`: Game start time
     - `away_team`: Away team name
     - `home_team`: Home team name
     - `away_team_score`: Away team score
     - `home_team_score`: Home team score

2. **NBA API**
   - Key columns collected:
     - `TEAM_ID`: Unique team identifier
     - `TEAM_NAME`: Team name
     - `GP`: Games played
     - `W`: Wins
     - `L`: Losses
     - `W_PCT`: Win percentage
     - `OFF_RATING`: Offensive rating
     - `DEF_RATING`: Defensive rating
     - `NET_RATING`: Net rating
     - `AST_PCT`: Assist percentage
     - `PACE`: Team pace
     - And various other advanced metrics

### Data Cleaning Process

#### Team Statistics Cleaning

1. **Column Standardization**
   NBA API columns are mapped to standardized names:

   ```
   TEAM_NAME -> team
   W -> wins
   L -> losses
   W_PCT -> win_pct
   OFF_RATING -> offensive_rating
   DEF_RATING -> defensive_rating
   NET_RATING -> net_rating
   EFG_PCT -> efg_pct
   TS_PCT -> ts_pct
   PACE -> pace
   AST_PCT -> ast_pct
   AST_TO -> ast_to
   AST_RATIO -> ast_ratio
   POSS -> possessions
   ```

2. **Basketball Reference Data Processing**
   - Home and away games are combined
   - Game-level statistics are aggregated by team
   - Calculated metrics include:
     - `games_played`: Total games
     - `points_per_game`: Average points per game

3. **Data Quality Checks**
   - Missing value handling
   - Outlier detection and treatment
   - Team name standardization (uppercase)
   - Duplicate removal

#### Player Statistics Cleaning

1. **Column Standardization**

   ```
   PLAYER_NAME -> name
   TEAM_ABBREVIATION -> team
   OFF_RATING -> offensive_rating
   DEF_RATING -> defensive_rating
   NET_RATING -> net_rating
   AST_PCT -> ast_pct
   AST_TO -> ast_to
   AST_RATIO -> ast_ratio
   USG_PCT -> usage_pct
   ```

2. **Data Processing**
   - Name standardization (Title Case)
   - Team name standardization (uppercase)
   - Missing value imputation
   - Per-game average calculations

### Visualization Data Preparation

The following DataFrames are prepared for visualization:

1. **Team Statistics**
   - Core metrics: offensive/defensive ratings, pace, win percentage
   - Scoring data from both home and away games
   - Advanced metrics from NBA API

2. **Pace Factors**
   - Team pace metrics
   - Possession-based statistics
   - Relative pace factors

3. **Efficiency Metrics**
   - Team and player efficiency calculations
   - Offensive and defensive efficiency
   - Usage and impact metrics

### Data Validation

The pipeline includes several validation steps:

1. **Team Name Consistency**
   - Checks for unknown teams in player statistics
   - Ensures team names match between datasets

2. **Statistical Consistency**
   - Validates scoring data between team and player statistics
   - Checks for large discrepancies in aggregated metrics

3. **Data Type Validation**
   - Ensures numeric columns contain valid data
   - Handles timezone-aware datetime columns

### Output Format

Data is saved in Excel format with the following sheets:

1. `team_stats`: Cleaned team statistics
2. `player_stats`: Cleaned player statistics
3. `team_efficiency`: Calculated team efficiency metrics
4. `player_efficiency`: Calculated player efficiency metrics
5. `pace_factors`: Team pace and possession metrics

### Visualization Outputs

The pipeline generates several visualization files:

1. `offensive_defensive_ratings.png`: Team offensive vs defensive ratings
2. `team_pace_factors.png`: Team pace analysis
3. `team_win_percentages.png`: Win percentage distribution
4. `scoring_distribution.png`: Team scoring distribution
5. `team_net_ratings.png`: Net rating analysis
