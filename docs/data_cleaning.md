# NBA Data Cleaning Guide

This guide details the data cleaning and preprocessing steps implemented in the NBA Expected Value Analysis project.

## Data Cleaning Process

### 1. Initial Data Validation

The `DataCleaner` class in `clean_data.py` implements comprehensive data validation:

```python
from src.data.clean_data import DataCleaner

# Initialize cleaner
cleaner = DataCleaner()

# Validate data types and structure
validation_results = cleaner.validate_data(df)
```

#### Validation Checks

- Data type consistency
- Missing value detection
- Duplicate entry identification
- Range validation for numeric fields
- Format verification for categorical data

### 2. Team Name Standardization

```python
def standardize_team_names(df: pd.DataFrame, team_col: str) -> pd.DataFrame:
    """
    Standardize team names to official NBA abbreviations.
    
    Args:
        df: DataFrame containing team names
        team_col: Name of the column containing team names
        
    Returns:
        DataFrame with standardized team names
    """
    team_mapping = {
        'Boston Celtics': 'BOS',
        'Brooklyn Nets': 'BKN',
        'New York Knicks': 'NYK',
        'Philadelphia 76ers': 'PHI',
        'Toronto Raptors': 'TOR',
        # ... additional mappings
    }
    
    return df.assign(**{team_col: df[team_col].map(team_mapping)})
```

### 3. Player Data Cleaning

```python
def clean_player_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize player data.
    
    Args:
        df: DataFrame containing player information
        
    Returns:
        Cleaned DataFrame with standardized player information
    """
    return (df
        .pipe(standardize_names)
        .pipe(clean_positions)
        .pipe(validate_status)
        .pipe(handle_missing_values)
    )
```

#### Cleaning Steps

1. Name standardization
2. Position validation
3. Status verification
4. Missing value handling

### 4. Statistical Data Cleaning

```python
def clean_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate statistical data.
    
    Args:
        df: DataFrame containing statistical information
        
    Returns:
        Cleaned DataFrame with validated statistics
    """
    return (df
        .pipe(remove_outliers)
        .pipe(handle_missing_stats)
        .pipe(validate_ranges)
        .pipe(calculate_derived_metrics)
    )
```

#### Statistical Validation

- Outlier detection and handling
- Missing value imputation
- Range validation
- Derived metric calculation

### 5. Data Integration

```python
def integrate_data_sources(
    lineups_df: pd.DataFrame,
    stats_df: pd.DataFrame,
    odds_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Integrate data from multiple sources.
    
    Args:
        lineups_df: DataFrame containing lineup information
        stats_df: DataFrame containing statistical information
        odds_df: DataFrame containing betting odds
        
    Returns:
        Integrated DataFrame with all relevant information
    """
    return (pd.merge(
        lineups_df,
        stats_df,
        on=['team', 'player'],
        how='left'
    ).merge(
        odds_df,
        on=['team', 'game_id'],
        how='left'
    ).pipe(validate_merged_data)
    )
```

## Data Quality Checks

### 1. Automated Validation

```python
def validate_data_quality(df: pd.DataFrame) -> Dict[str, bool]:
    """
    Perform comprehensive data quality checks.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Dictionary of validation results
    """
    checks = {
        'missing_values': check_missing_values(df),
        'duplicates': check_duplicates(df),
        'data_types': check_data_types(df),
        'value_ranges': check_value_ranges(df),
        'relationships': check_relationships(df)
    }
    
    return checks
```

### 2. Data Integrity Rules

```python
VALIDATION_RULES = {
    'player_name': {
        'type': str,
        'required': True,
        'unique': False
    },
    'team': {
        'type': str,
        'required': True,
        'unique': False,
        'values': TEAM_ABBREVIATIONS
    },
    'position': {
        'type': str,
        'required': True,
        'values': ['PG', 'SG', 'SF', 'PF', 'C']
    },
    'status': {
        'type': str,
        'required': True,
        'values': ['Active', 'GTD', 'OUT']
    }
}
```

## Error Handling

### 1. Missing Data Strategy

```python
def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing values based on column type.
    
    Args:
        df: DataFrame containing missing values
        
    Returns:
        DataFrame with handled missing values
    """
    strategies = {
        'numeric': 'median',
        'categorical': 'mode',
        'boolean': False,
        'datetime': 'drop'
    }
    
    return df.pipe(apply_missing_value_strategies, strategies)
```

### 2. Outlier Detection

```python
def detect_outliers(
    series: pd.Series,
    n_std: float = 3.0
) -> pd.Series:
    """
    Detect outliers using z-score method.
    
    Args:
        series: Series to check for outliers
        n_std: Number of standard deviations for threshold
        
    Returns:
        Boolean series indicating outlier status
    """
    z_scores = (series - series.mean()) / series.std()
    return abs(z_scores) > n_std
```

## Data Transformation

### 1. Feature Engineering

```python
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create derived features from existing data.
    
    Args:
        df: DataFrame containing raw features
        
    Returns:
        DataFrame with additional engineered features
    """
    return (df
        .pipe(calculate_efficiency_metrics)
        .pipe(calculate_performance_ratios)
        .pipe(create_categorical_features)
        .pipe(validate_engineered_features)
    )
```

### 2. Data Normalization

```python
def normalize_features(
    df: pd.DataFrame,
    numeric_cols: List[str]
) -> pd.DataFrame:
    """
    Normalize numeric features to standard scale.
    
    Args:
        df: DataFrame containing features to normalize
        numeric_cols: List of numeric column names
        
    Returns:
        DataFrame with normalized features
    """
    scaler = StandardScaler()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
    return df
```

## Best Practices

1. **Data Validation**
   - Implement comprehensive validation checks
   - Document validation rules
   - Log validation failures

2. **Error Handling**
   - Use appropriate strategies for different data types
   - Implement fallback methods
   - Log all data cleaning actions

3. **Performance**
   - Use vectorized operations
   - Implement efficient data structures
   - Monitor memory usage

4. **Documentation**
   - Maintain clear documentation
   - Version control data cleaning code
   - Track changes in cleaning logic

## Future Improvements

1. **Automation**
   - Automated data quality monitoring
   - Scheduled validation checks
   - Automated reporting

2. **Enhanced Validation**
   - More sophisticated outlier detection
   - Advanced relationship validation
   - Custom validation rules

3. **Performance Optimization**
   - Parallel processing
   - Improved memory management
   - Optimized algorithms
