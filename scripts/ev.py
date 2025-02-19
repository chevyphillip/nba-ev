"""
NBA Event and Player Props EV Calculator.
"""
import discord
import requests
import asyncio
import json
import math
from datetime import datetime, timedelta
import logging
from ratelimit import limits, sleep_and_retry, RateLimitException
import time
from discord import Embed, Color
from typing import Tuple, Optional
import os

# --- CONFIGURATION ---
BOT_TOKEN = "MTMzMjQxMDA5MzM0MTI0NTUzMA.G-G_sV.7m_7q9zoBDmU6tQvmXTMSDixEAxcoghvNkSfKU"
ODDS_API_KEY = "fee2d65aaf5ca5e90072b4b6e54e4f43"
CHANNEL_ID = 1318707908896362568
SPORT = 'basketball_nba'
REGION = 'us,us2,us_dfs,eu,us_ex'
KELLY_FRACTION = 0.25
PROP_MARKETS = 'player_points,player_rebounds,player_assists,player_threes,player_blocks,player_steals'
PROP_BOOKMAKERS = 'pinnacle,betonlineag,fanduel,draftkings,fliff,underdog,betmgm,betrivers,ballybet,espnbet,novig,prophetx'
INCLUDE_LINKS = 'true'
INCLUDE_SIDS = 'true'
INCLUDE_BET_LIMITS = 'true'

# Consensus Settings
CONSENSUS_ODDS_THRESHOLD = 0.30  # Increased to 30% maximum difference between books to accommodate more variance
WEIGHTED_BOOKS = {
    'betonlineag': 0.4,  # BetOnline weight
    'fanduel': 0.3,      # FanDuel weight
    'draftkings': 0.3,   # DraftKings weight
    'betmgm': 0.3,       # BetMGM weight
    'betrivers': 0.2,    # BetRivers weight
    'prophetx': 0.2,     # Added ProphetExchange
    'underdog': 0.2,     # Added Underdog
    'fliff': 0.2         # Added Fliff
}
MIN_BOOKS_FOR_CONSENSUS = 2  # Minimum number of books needed for consensus
MAX_PROB_DIFF = 0.10  # Maximum allowed probability difference (10%)
MIN_EDGE_THRESHOLD = 0.02  # Minimum edge required (2%)
MAX_EDGE_THRESHOLD = 0.20  # Maximum edge allowed (20%)

# Rate limiting configuration
CALLS_PER_SECOND = 1  # Free tier: 1 request per second
CALLS_PER_MONTH = 500  # Free tier: 500 requests per month
MONTHLY_PERIOD = 30 * 24 * 60 * 60  # 30 days in seconds

# Bankroll Management Settings
BANKROLL = 1000.0  # Base bankroll size
MIN_UNIT_PCT = 0.01  # 1% minimum unit size
MAX_UNIT_PCT = 0.03  # 3% maximum unit size
BASE_UNIT = BANKROLL * MIN_UNIT_PCT  # Base unit size ($10 for $1000 bankroll)

# Alert Settings
ALERT_DELAY = 3  # Seconds to wait between each +EV alert
MAX_ALERTS_PER_EVENT = 10  # Increased from 5 to allow more alerts
MAX_EDGE_CALC = 0.15       # Increased to 15% maximum edge for calculations

# --- DATA STORAGE ---
pinnacle_odds_history = {}  # To Store Pinnacle Odds

# Add color constants for embeds
COLORS = {
    'positive_ev': Color.green(),
    'neutral': Color.blue(),
    'warning': Color.orange(),
    'error': Color.red()
}

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Create a log filename with timestamp
log_filename = f"logs/ev_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure logging to write to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Log startup information
logger.info("Starting NBA EV Calculator")
logger.info(f"Logging to file: {log_filename}")
logger.info("Configuration:")
logger.info(f"- Consensus Odds Threshold: {CONSENSUS_ODDS_THRESHOLD}")
logger.info(f"- Minimum Books for Consensus: {MIN_BOOKS_FOR_CONSENSUS}")
logger.info(f"- Edge Thresholds: Min={MIN_EDGE_THRESHOLD}, Max={MAX_EDGE_THRESHOLD}")
logger.info(f"- Kelly Fraction: {KELLY_FRACTION}")

# --- RATE LIMITING DECORATORS ---
@sleep_and_retry
@limits(calls=CALLS_PER_SECOND, period=1)  # 1 request per second
@limits(calls=CALLS_PER_MONTH, period=MONTHLY_PERIOD)  # 500 requests per month
def make_api_request(url: str, params: dict = None) -> dict:
    """Make a rate-limited API request."""
    try:
        response = requests.get(url, params=params)
        
        # Check for rate limit errors
        if response.status_code == 429:
            retry_after = int(response.headers.get('retry-after', 60))
            logger.warning(f"Rate limit exceeded. Waiting {retry_after} seconds")
            time.sleep(retry_after)
            return make_api_request(url, params)  # Retry after waiting
            
        response.raise_for_status()
        return response.json()
        
    except RateLimitException:
        logger.error("Rate limit exceeded for the current time period")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise

# --- HELPER FUNCTIONS ---

def get_upcoming_events(api_key: str, sport: str) -> list:
    """Gets a list of upcoming NBA events."""
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/events"
    params = {"apiKey": api_key}
    
    try:
        data = make_api_request(url, params)
        logger.info(f"Found {len(data)} upcoming events")
        return data
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        return []

def get_player_props(api_key: str, sport: str, event_id: str) -> dict:
    """Gets player props for a specific event."""
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/events/{event_id}/odds"
    params = {
        "apiKey": api_key,
        "regions": REGION,
        "markets": PROP_MARKETS,
        "oddsFormat": "american",
        "bookmakers": PROP_BOOKMAKERS,
        "includeLinks": INCLUDE_LINKS,
        "includeSids": INCLUDE_SIDS,
        "includeBetLimits": INCLUDE_BET_LIMITS
    }
    
    try:
        data = make_api_request(url, params)
        logger.info(f"Retrieved player props for event {event_id}")
        return data
    except Exception as e:
        logger.error(f"Error fetching player props for event {event_id}: {e}")
        return {}

def american_to_decimal(odds: float) -> float:
    """Converts American odds to decimal odds."""
    if odds > 0:
        return 1 + (odds / 100)
    else:
        return 1 - (100 / odds)

def calculate_implied_probability(odds: float) -> float:
    """
    Calculates implied probability from American odds.
    
    Args:
        odds: American odds
    
    Returns:
        Implied probability as a decimal
    """
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)

def devig_pinnacle_odds(odds1: float, odds2: float, pinnacle_hold: float) -> tuple:
    """Devigs odds using Pinnacle as the sharp book."""
    prob1 = calculate_implied_probability(odds1)
    prob2 = calculate_implied_probability(odds2)
    total_prob = prob1 + prob2
    
    # Remove hold adjustment since we're getting fair odds from multiple books
    true_prob1 = prob1 / total_prob
    true_prob2 = prob2 / total_prob
    
    return true_prob1, true_prob2

def calculate_edge(bet_odds: float, true_prob: float) -> float:
    """
    Calculates the betting edge with a maximum cap.
    
    Args:
        bet_odds: American odds
        true_prob: True probability after devigging
    
    Returns:
        Edge as a decimal, capped at MAX_EDGE_CALC (15%)
    """
    decimal_odds = american_to_decimal(bet_odds)
    raw_edge = (decimal_odds * true_prob) - 1
    return min(raw_edge, MAX_EDGE_CALC)  # Cap the edge at 15%

def calculate_hold(odds1: float, odds2: float) -> float:
    """
    Calculate the sportsbook hold percentage.
    
    Args:
        odds1: First side odds (American)
        odds2: Second side odds (American)
    
    Returns:
        Hold percentage as a decimal (e.g., 0.0476 for 4.76%)
    """
    prob1 = calculate_implied_probability(odds1)
    prob2 = calculate_implied_probability(odds2)
    total_probability = prob1 + prob2
    hold = total_probability - 1.0
    return max(0, hold)  # Ensure non-negative hold

def kelly_criterion(edge: float, odds: float, kelly_fraction: float = 0.5) -> tuple:
    """
    Calculates the Kelly Criterion bet size with bankroll management.
    
    Args:
        edge: Edge as a decimal (e.g., 0.05 for 5%)
        odds: American odds
        kelly_fraction: Fraction of Kelly to use (default 0.5 for half Kelly)
    
    Returns:
        Tuple of (unit_size, dollar_amount)
    """
    decimal_odds = american_to_decimal(odds)
    
    # Calculate win probability from edge and odds
    implied_prob = calculate_implied_probability(odds)
    win_prob = edge + implied_prob
    
    # Standard Kelly formula: f* = (bp - q) / b
    # where: b = decimal odds - 1, p = win probability, q = loss probability
    b = decimal_odds - 1
    p = win_prob
    q = 1 - p
    
    kelly_pct = ((b * p) - q) / b if b > 0 else 0
    
    # Apply Kelly fraction and unit constraints
    bet_pct = min(MAX_UNIT_PCT, kelly_pct * kelly_fraction)
    bet_pct = max(MIN_UNIT_PCT, bet_pct)
    
    # Calculate unit size and dollar amount
    units = bet_pct / MIN_UNIT_PCT  # Convert to units
    dollar_amount = units * BASE_UNIT
    
    return units, dollar_amount

def is_plus_ev(edge: float, min_threshold: float = MIN_EDGE_THRESHOLD, max_threshold: float = MAX_EDGE_THRESHOLD) -> bool:
    """
    Checks if a bet has positive expected value (EV).
    Now using a very low minimum threshold to catch more opportunities.
    
    Args:
        edge: Calculated edge as a decimal
        min_threshold: Minimum edge required (now 0.1%)
        max_threshold: Maximum +EV allowed (now 20%)
    
    Returns:
        bool: True if edge is between min and max thresholds
    """
    return edge > min_threshold and edge <= max_threshold

def calculate_consensus_line(player, market_type, prop_type, line_value, bookmakers, logger):
    """Calculate consensus line from multiple bookmakers."""
    try:
        available_books = []
        weighted_odds = []
        total_weight = 0
        
        # Book weights (higher weight = more influence on consensus)
        book_weights = {
            'pinnacle': 0.5,
            'fanduel': 0.3,
            'draftkings': 0.3,
            'betmgm': 0.3,
            'betonlineag': 0.4,
            'fliff': 0.2,
            'underdog': 0.2
        }

        # First check if we have enough books
        valid_books = [book for book in bookmakers if book in book_weights]
        if len(valid_books) < MIN_BOOKS_FOR_CONSENSUS:
            logger.warning(f"Insufficient bookmakers ({len(valid_books)}) for consensus. Need at least {MIN_BOOKS_FOR_CONSENSUS}.")
            return None, None, None

        # Get odds from each book
        for book_name, book_data in bookmakers.items():
            if book_name not in book_weights:
                continue

            try:
                main_odds, opp_odds = find_matching_odds(
                    player, market_type, prop_type, line_value, book_data, logger
                )
                
                if main_odds and opp_odds:
                    # Convert odds to probabilities
                    main_prob = american_to_prob(main_odds)
                    opp_prob = american_to_prob(opp_odds)
                    
                    # Calculate hold
                    hold = (main_prob + opp_prob) - 1
                    
                    logger.info(f"Added odds from {book_name} (weight: {book_weights[book_name]}): {main_odds}/{opp_odds}")
                    available_books.append({
                        'name': book_name,
                        'main_odds': main_odds,
                        'opp_odds': opp_odds,
                        'main_prob': main_prob,
                        'opp_prob': opp_prob,
                        'hold': hold,
                        'weight': book_weights[book_name]
                    })
                    weighted_odds.append({
                        'main_prob': main_prob,
                        'opp_prob': opp_prob,
                        'weight': book_weights[book_name]
                    })
                    total_weight += book_weights[book_name]
            except Exception as e:
                logger.warning(f"Error getting odds from {book_name}: {str(e)}")
                continue

        if not available_books:
            logger.warning("No valid odds found from any bookmaker")
            return None, None, None

        # Log available odds
        logger.info("Available odds from all books:")
        for book in available_books:
            logger.info(f"{book['name']}: {book['main_odds']}/{book['opp_odds']} (Hold: {book['hold']*100:.2f}%)")

        # Calculate weighted average probabilities
        weighted_main_prob = sum(odds['main_prob'] * odds['weight'] for odds in weighted_odds) / total_weight
        weighted_opp_prob = sum(odds['opp_prob'] * odds['weight'] for odds in weighted_odds) / total_weight

        # Check probability differences
        max_main_diff = 0
        max_opp_diff = 0
        for book in available_books:
            main_diff = abs(book['main_prob'] - weighted_main_prob)
            opp_diff = abs(book['opp_prob'] - weighted_opp_prob)
            max_main_diff = max(max_main_diff, main_diff)
            max_opp_diff = max(max_opp_diff, opp_diff)
            logger.info(f"Comparing probabilities: {book['main_prob']:.4f} vs {weighted_main_prob:.4f}")
            logger.info(f"Comparing probabilities: {book['opp_prob']:.4f} vs {weighted_opp_prob:.4f}")

        logger.info(f"Max implied probability differences: {max_main_diff*100:.2f}%/{max_opp_diff*100:.2f}%")

        # Only reject if both differences are too high
        if max_main_diff > MAX_PROB_DIFF and max_opp_diff > MAX_PROB_DIFF:
            logger.warning(f"Odds difference too high for consensus: {max_main_diff*100:.2f}%/{max_opp_diff*100:.2f}%")
            return None, None, None

        # Convert consensus probabilities back to American odds
        consensus_main = prob_to_american(weighted_main_prob)
        consensus_opp = prob_to_american(weighted_opp_prob)

        return consensus_main, consensus_opp, len(available_books)

    except Exception as e:
        logger.error(f"Error calculating consensus line: {str(e)}")
        return None, None, None

def calculate_fair_value(odds1: float, odds2: float) -> Tuple[float, float, float]:
    """
    Calculate fair value odds and hold percentage.
    
    Args:
        odds1: First side odds (American)
        odds2: Second side odds (American)
    
    Returns:
        Tuple of (fair_value_odds1, fair_value_odds2, hold_percentage)
    """
    # Calculate implied probabilities
    prob1 = calculate_implied_probability(odds1)
    prob2 = calculate_implied_probability(odds2)
    
    # Calculate hold (vig)
    hold = (prob1 + prob2) - 1
    
    # Remove the hold to get fair probabilities
    total_prob = prob1 + prob2
    fair_prob1 = prob1 / total_prob
    fair_prob2 = prob2 / total_prob
    
    # Convert fair probabilities back to American odds
    def prob_to_american(prob: float) -> float:
        if prob >= 0.5:
            return -100 * prob / (1 - prob)
        else:
            return 100 * (1 - prob) / prob
    
    fair_odds1 = prob_to_american(fair_prob1)
    fair_odds2 = prob_to_american(fair_prob2)
    
    return fair_odds1, fair_odds2, hold

def calculate_ev(bet_odds: float, fair_odds: float) -> Tuple[float, float]:
    """
    Calculate EV and edge for a bet.
    
    Args:
        bet_odds: The odds you can bet at (American)
        fair_odds: The fair odds (American)
    
    Returns:
        Tuple of (edge_percentage, ev_percentage)
    """
    # Convert odds to probabilities
    bet_prob = calculate_implied_probability(bet_odds)
    fair_prob = calculate_implied_probability(fair_odds)
    
    # Calculate profit multiplier
    if bet_odds < 0:
        profit = abs(100 / bet_odds)
    else:
        profit = bet_odds / 100
    
    # Calculate EV
    ev = (fair_prob * profit - (1 - fair_prob)) * 100
    
    # Calculate edge
    edge = (1 / bet_prob) * fair_prob - 1
    edge_percentage = edge * 100
    
    # Log calculations for debugging
    logger.info(f"EV Calculation Details:")
    logger.info(f"  Bet odds: {bet_odds:+d} (implied prob: {bet_prob:.4f})")
    logger.info(f"  Fair odds: {fair_odds:+.2f} (implied prob: {fair_prob:.4f})")
    logger.info(f"  Profit multiplier: {profit:.4f}")
    logger.info(f"  EV: {ev:.2f}%")
    logger.info(f"  Edge: {edge_percentage:.2f}%")
    
    return edge_percentage, ev

def calculate_fair_value_change(current_fv: float, previous_fv: float) -> float:
    """
    Calculate the percentage change in fair value.
    
    Args:
        current_fv: Current fair value odds (American)
        previous_fv: Previous fair value odds (American)
    
    Returns:
        Percentage change in fair value
    """
    if not previous_fv:
        return 0.0
    
    return ((current_fv - previous_fv) / abs(previous_fv)) * 100

def process_odds(bet_odds: float, market_odds1: float, market_odds2: float) -> Tuple[float, float, float, float]:
    """
    Process odds to get edge, EV, and fair value.
    
    Args:
        bet_odds: The odds you can bet at (American)
        market_odds1: First market odds (American)
        market_odds2: Second market odds (American)
    
    Returns:
        Tuple of (edge_percentage, ev_percentage, fair_value, hold_percentage)
    """
    # Calculate fair value and hold
    fair_odds1, fair_odds2, hold = calculate_fair_value(market_odds1, market_odds2)
    
    # Log the fair odds calculation
    logger.info(f"Fair odds calculation:")
    logger.info(f"  Market odds: {market_odds1:+d}/{market_odds2:+d}")
    logger.info(f"  Fair odds: {fair_odds1:+.2f}/{fair_odds2:+.2f}")
    logger.info(f"  Hold: {hold*100:.2f}%")
    
    # Calculate edge and EV using fair odds
    edge_pct, ev_pct = calculate_ev(bet_odds, fair_odds1)
    
    # Log detailed edge calculation
    logger.info(f"Edge calculation details:")
    logger.info(f"  Bet odds: {bet_odds:+d}")
    logger.info(f"  Fair odds: {fair_odds1:+.2f}")
    logger.info(f"  Raw edge: {edge_pct:.2f}%")
    logger.info(f"  Raw EV: {ev_pct:.2f}%")
    logger.info(f"  Meets threshold: {is_plus_ev(edge_pct/100)}")
    
    # Calculate win probability for logging
    fair_prob = calculate_implied_probability(fair_odds1)
    bet_prob = calculate_implied_probability(bet_odds)
    logger.info(f"Probability comparison:")
    logger.info(f"  Fair probability: {fair_prob:.4f}")
    logger.info(f"  Implied bet probability: {bet_prob:.4f}")
    
    return edge_pct, ev_pct, fair_odds1, hold * 100

async def process_player_props(event_id: str, props_data: dict, channel) -> None:
    """Process player props for an event and send alerts for +EV opportunities."""
    if not props_data:
        logger.warning(f"No props data available for event {event_id}")
        return

    home_team = props_data.get('home_team', 'Unknown')
    away_team = props_data.get('away_team', 'Unknown')
    alerts_sent = 0
    ev_opportunities_found = 0
    
    # Add tracking counters
    total_props_found = 0
    props_filtered_no_market = 0
    props_filtered_no_outcome = 0
    props_filtered_no_opposing = 0
    props_filtered_consensus = 0
    props_processed = 0
    edges_calculated = 0
    positive_edges_found = 0
    
    # Get all available bookmakers
    all_bookmakers = props_data.get('bookmakers', [])
    if not all_bookmakers:
        logger.warning(f"No bookmakers found for event {event_id}")
        return
    
    logger.info(f"Processing {len(all_bookmakers)} bookmakers for {away_team} @ {home_team}")
    
    # Find Pinnacle odds
    pin_odds = next((bm for bm in all_bookmakers if bm['key'] == 'pinnacle'), None)
    use_consensus = False
    
    if not pin_odds:
        logger.warning(f"No Pinnacle odds found for event {event_id}, using consensus lines")
        use_consensus = True
        
        # Check if we have enough bookmakers for consensus
        if len(all_bookmakers) < 2:
            logger.warning(f"Insufficient bookmakers ({len(all_bookmakers)}) for consensus lines in event {event_id}")
            return
        logger.info(f"Using consensus lines with {len(all_bookmakers)} bookmakers")

    try:
        # Get reference odds source
        reference_odds = pin_odds if not use_consensus else all_bookmakers[0]
        if not reference_odds:
            logger.warning(f"No reference odds available for event {event_id}")
            return
            
        # Verify reference odds has markets
        markets = reference_odds.get('markets', [])
        if not markets:
            logger.warning(f"No markets found in reference odds for event {event_id}")
            return
        
        logger.info(f"Processing {len(markets)} markets")
        
        # Process each market
        for market in markets:
            market_key = market.get('key', 'unknown')
            outcomes = market.get('outcomes', [])
            total_props_found += len(outcomes)
            
            logger.info(f"Found {len(outcomes)} props in market {market_key}")
            
            if alerts_sent >= MAX_ALERTS_PER_EVENT:
                logger.info(f"Reached maximum alerts ({MAX_ALERTS_PER_EVENT}) for event {event_id}")
                break

            # Process each player prop
            for outcome in outcomes:
                try:
                    # Log the full outcome structure
                    logger.info(f"Full outcome data: {json.dumps(outcome, indent=2)}")
                    
                    description = outcome.get('description', '')
                    if not description:
                        props_filtered_no_outcome += 1
                        logger.debug(f"Filtered - Empty description")
                        continue

                    # Log the raw description and additional fields
                    logger.info(f"Processing description: '{description}'")
                    logger.info(f"Additional fields: name={outcome.get('name', 'N/A')}, handicap={outcome.get('handicap', 'N/A')}")

                    # Modified parsing logic to handle different formats
                    player_name = description
                    prop_details = None

                    # Get over/under from name field and point value
                    if 'name' in outcome and 'point' in outcome:
                        over_under = outcome['name']  # 'Over' or 'Under'
                        point_value = outcome['point']
                        prop_details = f"{over_under} {point_value}"
                        logger.info(f"Constructed prop details from name and point: {prop_details}")

                    if not prop_details:
                        props_filtered_no_outcome += 1
                        logger.info(f"Filtered - Could not find prop details for {player_name}")
                        continue

                    logger.info(f"Parsed player: '{player_name}', details: '{prop_details}'")

                    # Get the line value with more detailed logging
                    try:
                        # Get point value directly
                        line_value = outcome.get('point')
                        if line_value is None:
                            logger.info(f"Failed to extract line value - no point field")
                            props_filtered_no_outcome += 1
                            continue
                            
                        logger.info(f"Extracted line value: {line_value}")
                    except Exception as e:
                        logger.error(f"Error parsing line value: {str(e)}")
                        props_filtered_no_outcome += 1
                        continue
                    
                    # Determine if it's over/under with logging
                    is_over = outcome.get('name', '').lower() == 'over'
                    prop_type = 'Over' if is_over else 'Under'
                    logger.info(f"Determined prop type: {prop_type} from name field: {outcome.get('name')}")

                    logger.debug(f"Processing {player_name} {prop_type} {line_value} {market_key}")

                    # Get reference odds (either Pinnacle or consensus)
                    if use_consensus:
                        pin_price, pin_opposing_price, pin_hold = calculate_consensus_line(
                            player_name, market_key, prop_type, line_value, all_bookmakers, logger
                        )
                        if not pin_price or not pin_opposing_price:
                            props_filtered_consensus += 1
                            logger.debug(f"No consensus line available for {player_name} {prop_type} {line_value}")
                            continue
                        pinnacle_bet_limit = "N/A (Consensus)"
                    else:
                        pin_price = outcome.get('price')
                        opposing_outcome = next(
                            (o for o in market.get('outcomes', []) 
                             if o.get('description', '').startswith(player_name) and 
                             (('Over' in o.get('description', '') and not is_over) or 
                              ('Under' in o.get('description', '') and is_over))),
                            None
                        )
                        if not opposing_outcome:
                            props_filtered_no_opposing += 1
                            continue
                        pin_opposing_price = opposing_outcome.get('price')
                        if not pin_opposing_price:
                            props_filtered_no_opposing += 1
                            continue
                        pin_hold = calculate_hold(pin_price, pin_opposing_price)
                        pinnacle_bet_limit = market.get('limit', "N/A")

                    # Log reference odds details
                    logger.info(f"Reference odds for {player_name} {prop_type} {line_value}: {pin_price:+d}/{pin_opposing_price:+d} (Hold: {pin_hold*100:.2f}%)")

                    # Devig odds
                    true_prob, _ = devig_pinnacle_odds(pin_price, pin_opposing_price, pin_hold)
                    logger.debug(f"Devigged probability: {true_prob:.4f}")

                    # Check other books for the same prop
                    for book in all_bookmakers:
                        book_name = book.get('key', 'unknown')
                        if book['key'] == 'pinnacle' or (use_consensus and book == reference_odds):
                            continue

                        try:
                            book_market = next(
                                (m for m in book.get('markets', []) if m['key'] == market_key),
                                None
                            )
                            if not book_market:
                                props_filtered_no_market += 1
                                continue

                            book_outcome = next(
                                (o for o in book_market.get('outcomes', []) 
                                 if o.get('description', '').startswith(player_name) and 
                                 ((is_over and 'Over' in o.get('description', '')) or 
                                  (not is_over and 'Under' in o.get('description', '')))),
                                None
                            )
                            if not book_outcome:
                                props_filtered_no_outcome += 1
                                continue

                            book_price = book_outcome.get('price')
                            if not book_price:
                                props_filtered_no_outcome += 1
                                continue

                            props_processed += 1

                            # Calculate edge, EV, and fair value
                            edge_pct, ev_pct, fair_value, hold_pct = process_odds(
                                book_price, pin_price, pin_opposing_price
                            )
                            edges_calculated += 1
                            
                            # Log edge calculation details
                            logger.info(f"Edge calculation for {book_name} {player_name} {prop_type} {line_value}:")
                            logger.info(f"Book odds: {book_price:+d}, Edge: {edge_pct:.2f}%, EV: {ev_pct:.2f}%, Hold: {hold_pct:.2f}%")
                            
                            if edge_pct > 0:
                                positive_edges_found += 1
                                logger.info(f"Found positive edge: {edge_pct:.2f}% (EV: {ev_pct:.2f}%) on {book_name} {player_name} {prop_type} {line_value}")

                            # Calculate fair value change if we have history
                            fv_change = 0.0
                            if event_id in pinnacle_odds_history:
                                prev_fair_value = pinnacle_odds_history[event_id].get('fair_value')
                                if prev_fair_value:
                                    fv_change = calculate_fair_value_change(fair_value, prev_fair_value)
                            
                            # Store current fair value in history
                            if event_id not in pinnacle_odds_history:
                                pinnacle_odds_history[event_id] = {}
                            pinnacle_odds_history[event_id]['fair_value'] = fair_value
                            
                            if edge_pct > 0:
                                ev_opportunities_found += 1
                                logger.debug(f"Found {edge_pct:.2f}% edge (EV: {ev_pct:.2f}%) on {book_name} {player_name} {prop_type} {line_value}")

                            # Check if +EV is within acceptable range
                            if is_plus_ev(edge_pct/100):  # Convert edge_pct to decimal for is_plus_ev
                                units, dollar_amount = kelly_criterion(edge_pct/100, book_price, KELLY_FRACTION)
                                logger.info(f"Found +EV alert: {book_name} {player_name} {prop_type} {line_value} (Edge: {edge_pct:.2f}%, EV: {ev_pct:.2f}%)")
                                
                                # Format market name for display
                                market_display = market_key.replace('player_', '').replace('_', ' ').title()
                                
                                # Create embed message
                                embed = Embed(
                                    title=f"{book_name.upper()} {player_name} {prop_type} {line_value}",
                                    description=f"{away_team} @ {home_team}",
                                    color=COLORS['positive_ev']
                                )
                                
                                # Add game time if available
                                game_time = props_data.get('commence_time')
                                if game_time:
                                    game_time = datetime.fromtimestamp(game_time)
                                    embed.add_field(
                                        name="Game Time",
                                        value=game_time.strftime("%A, %B %d, %Y %I:%M %p"),
                                        inline=False
                                    )

                                # Add main bet details
                                embed.add_field(
                                    name="EV Details",
                                    value=f"Edge: {edge_pct:.2f}%\nEV: {ev_pct:.2f}%\nKelly: {units:.2f}u\nBet: ${dollar_amount:.2f}",
                                    inline=True
                                )

                                # Add odds details
                                embed.add_field(
                                    name="Odds Info",
                                    value=f"Current: {book_price:+d}\nFV: {fair_value:+.0f}\nFV Δ: {fv_change:+.2f}%",
                                    inline=True
                                )

                                # Add source of truth section
                                source_text = (
                                    f"Pinnacle {pin_price:+d}/{pin_opposing_price:+d}\n"
                                    f"Hold: {pin_hold*100:.2f}%\n"
                                    f"{pinnacle_bet_limit}"
                                )
                                embed.add_field(
                                    name="Source of Truth",
                                    value=source_text,
                                    inline=False
                                )

                                # Add Pinnacle odds history if available
                                if event_id in pinnacle_odds_history:
                                    history = pinnacle_odds_history[event_id]
                                    history_text = "\n".join([
                                        f"Curr: {history['current']:+d} ${history['current_limit']}",
                                        f"Prev: {history['previous']:+d} ${history['prev_limit']}",
                                        f"Open: {history['open']:+d} ${history['open_limit']}"
                                    ])
                                    embed.add_field(
                                        name="Pinnacle Odds History",
                                        value=f"```\n{history_text}\n```",
                                        inline=False
                                    )

                                # Add bet links if available
                                if 'links' in book_outcome:
                                    us_link = book_outcome['links'].get('us')
                                    if us_link:
                                        embed.add_field(
                                            name="Bet Links",
                                            value=f"[US Bet Link]({us_link})",
                                            inline=False
                                        )

                                # Add footer with timestamp
                                embed.set_footer(text="Sourced Betting • ")
                                embed.timestamp = datetime.utcnow()

                                # Send embed message
                                await channel.send(embed=embed)
                                alerts_sent += 1
                                logger.info(f"Sent +EV alert ({edge_pct:.2f}%) for {player_name} {market_display} {prop_type} {line_value} - {units:.2f}u")
                                
                                # Wait between alerts
                                await asyncio.sleep(ALERT_DELAY)

                        except Exception as e:
                            logger.error(f"Error processing {book_name} for {player_name}: {str(e)}")
                            continue

                except Exception as e:
                    logger.error(f"Error processing prop for {description}: {str(e)}")
                    continue

    except Exception as e:
        logger.error(f"Error processing event {event_id}: {str(e)}")
    finally:
        # Log summary statistics
        logger.info(f"\nEvent {event_id} Processing Summary:")
        logger.info(f"Total props found: {total_props_found}")
        logger.info(f"Props filtered - No market: {props_filtered_no_market}")
        logger.info(f"Props filtered - No outcome: {props_filtered_no_outcome}")
        logger.info(f"Props filtered - No opposing: {props_filtered_no_opposing}")
        logger.info(f"Props filtered - Consensus: {props_filtered_consensus}")
        logger.info(f"Props processed: {props_processed}")
        logger.info(f"Edges calculated: {edges_calculated}")
        logger.info(f"Positive edges found: {positive_edges_found}")
        logger.info(f"Alerts sent: {alerts_sent}")
        
        # Calculate and log conversion rates
        if total_props_found > 0:
            process_rate = (props_processed / total_props_found) * 100
            logger.info(f"Props processing rate: {process_rate:.1f}%")
        
        if edges_calculated > 0:
            edge_success_rate = (positive_edges_found / edges_calculated) * 100
            logger.info(f"Edge success rate: {edge_success_rate:.1f}%")
            
        if positive_edges_found > 0:
            alert_conversion = (alerts_sent / positive_edges_found) * 100
            logger.info(f"Alert conversion rate: {alert_conversion:.1f}%")

def american_to_prob(odds: int) -> float:
    """Convert American odds to probability."""
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)

def prob_to_american(prob: float) -> int:
    """Convert probability to American odds."""
    if prob >= 0.5:
        return int(round(-100 * prob / (1 - prob)))
    else:
        return int(round(100 * (1 - prob) / prob))

def find_matching_odds(player: str, market_type: str, prop_type: str, line_value: float, 
                      book_data: dict, logger) -> tuple:
    """Find matching odds for a player prop from a bookmaker."""
    try:
        market = next((m for m in book_data.get('markets', []) 
                      if m['key'] == market_type), None)
        if not market:
            return None, None

        # Find main outcome
        main_outcome = next(
            (o for o in market.get('outcomes', [])
             if o.get('description', '') == player and
             o.get('point') == line_value and
             o.get('name', '').lower() == prop_type.lower()),
            None
        )

        # Find opposing outcome
        opp_type = 'under' if prop_type.lower() == 'over' else 'over'
        opp_outcome = next(
            (o for o in market.get('outcomes', [])
             if o.get('description', '') == player and
             o.get('point') == line_value and
             o.get('name', '').lower() == opp_type),
            None
        )

        if main_outcome and opp_outcome:
            return main_outcome.get('price'), opp_outcome.get('price')
        
        return None, None

    except Exception as e:
        logger.error(f"Error finding matching odds: {str(e)}")
        return None, None

# --- DISCORD BOT ---
class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

intents = discord.Intents.default()
client = MyClient(intents=intents)

@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user}')
    client.loop.create_task(scan_for_ev())

async def scan_for_ev():
    """Scans for +EV bets periodically and sends alerts."""
    remaining_requests = CALLS_PER_MONTH
    
    while True:
        try:
            channel = client.get_channel(CHANNEL_ID)
            if not channel:
                logger.error("Could not find Discord channel")
                await asyncio.sleep(60)
                continue

            # Check remaining requests
            if remaining_requests <= 0:
                logger.warning("Monthly API limit reached. Waiting for next period...")
                await asyncio.sleep(3600)  # Wait an hour before checking again
                remaining_requests = CALLS_PER_MONTH
                continue

            # Get upcoming events
            events = get_upcoming_events(ODDS_API_KEY, SPORT)
            if not events:
                logger.warning("No upcoming events found")
                await asyncio.sleep(60)
                continue
            
            remaining_requests -= 1  # Decrement request counter

            # Process each event
            for event in events:
                event_id = event.get('id')
                if not event_id:
                    continue

                logger.info(f"Processing event: {event_id}")
                
                # Get player props for the event
                props_data = get_player_props(ODDS_API_KEY, SPORT, event_id)
                if props_data:
                    await process_player_props(event_id, props_data, channel)
                    remaining_requests -= 1  # Decrement request counter
                
                # Add delay between API calls to respect rate limits
                await asyncio.sleep(1)  # Ensure 1 second between requests

                # Check remaining requests after each event
                if remaining_requests <= 0:
                    logger.warning("Monthly API limit reached during event processing")
                    break

            # Wait before next scan
            await asyncio.sleep(60)

        except RateLimitException:
            logger.error("Rate limit exceeded. Waiting before retrying...")
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"Error in scan_for_ev: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    client.run(BOT_TOKEN)
