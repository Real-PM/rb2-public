"""Player routes"""
from flask import Blueprint, render_template, request, abort, send_file, make_response
from app.models import Player, PlayerCurrentStatus, PlayerBattingStats, PlayerPitchingStats
from app.services import player_service
from sqlalchemy import desc, func, and_
from app.extensions import db, cache
import string
import os

bp = Blueprint('players', __name__)


class DictToObject:
    """Convert dict to object with attribute access for template compatibility

    Handles key name aliasing for template compatibility:
    - 'avg' -> 'batting_average'
    - 'obp' -> 'on_base_percentage'
    - 'slg' -> 'slugging_percentage'
    """
    def __init__(self, d):
        # First, update dict normally
        self.__dict__.update(d)

        # Then add aliases for short key names (from yearly stats) to match template expectations
        # IMPORTANT: Check if key exists in source dict, not in self.__dict__
        if 'avg' in d:
            self.batting_average = d['avg']
        if 'obp' in d:
            self.on_base_percentage = d['obp']
        if 'slg' in d:
            self.slugging_percentage = d['slg']
        # OPS might come from both short and long form
        if 'ops' in d and not hasattr(self, 'ops'):
            self.ops = d['ops']


def _convert_dict_list_to_objects(dict_list):
    """Convert list of dicts to list of objects for template compatibility"""
    if not dict_list:
        return []
    return [DictToObject(d) if isinstance(d, dict) else d for d in dict_list]


def _make_player_detail_cache_key():
    """Generate cache key for player detail route"""
    return f'player_detail_{request.view_args.get("player_id")}'


@bp.route('/')
@cache.cached(timeout=600, key_prefix='players_list')
def players_list():
    """Players home page - alphabetical layout with notable players by letter.

    For each letter A-Z:
    - Letter is clickable (links to /players/letter/X)
    - Shows 10 notable players (by career WAR) whose last name starts with that letter
    """
    # OPTIMIZED: Single query to get all players with their career WAR
    # Then process in Python to group by letter and take top 10

    # Get all players with career WAR in one query
    all_players_with_war = (
        db.session.query(
            Player.player_id,
            Player.first_name,
            Player.last_name,
            func.sum(PlayerBattingStats.war).label('career_war'),
            func.substr(Player.last_name, 1, 1).label('first_letter')
        )
        .outerjoin(PlayerBattingStats, and_(
            Player.player_id == PlayerBattingStats.player_id,
            PlayerBattingStats.split_id == 1
        ))
        .group_by(Player.player_id, Player.first_name, Player.last_name)
        .order_by(desc('career_war'))
        .all()
    )

    # Group by first letter and take top 10 per letter
    players_by_letter = {}
    for row in all_players_with_war:
        letter = row.first_letter.upper() if row.first_letter else 'Z'

        if letter not in players_by_letter:
            players_by_letter[letter] = []

        # Only keep top 10 per letter
        if len(players_by_letter[letter]) < 10:
            # Create a simple object to hold player data
            player_data = type('PlayerData', (), {
                'player_id': row.player_id,
                'display_name': f"{row.first_name} {row.last_name}",
                'career_war': row.career_war
            })()
            players_by_letter[letter].append(player_data)

    return render_template('players/list.html', players_by_letter=players_by_letter)


@bp.route('/letter/<letter>')
@cache.cached(timeout=600)
def players_by_letter(letter):
    """Show all players whose last name starts with the given letter.

    Args:
        letter: Single letter A-Z

    Returns:
        Page with all players for that letter, showing name and years of service
    """
    # Validate letter
    letter = letter.upper()
    if len(letter) != 1 or letter not in string.ascii_uppercase:
        abort(404)

    # Get all players whose last name starts with this letter
    # Include their years of service (min/max year from stats)
    # OPTIMIZATION: Use load_only to prevent cascading eager loads
    from sqlalchemy.orm import load_only, raiseload

    players_query = (
        db.session.query(
            Player,
            func.min(PlayerBattingStats.year).label('first_year'),
            func.max(PlayerBattingStats.year).label('last_year')
        )
        .options(
            load_only(Player.player_id, Player.first_name, Player.last_name),
            raiseload('*')  # Block all relationship cascades
        )
        .outerjoin(PlayerBattingStats, and_(
            Player.player_id == PlayerBattingStats.player_id,
            PlayerBattingStats.split_id == 1  # Overall stats only
        ))
        .filter(Player.last_name.like(f'{letter}%'))
        .group_by(Player.player_id)
        .order_by(Player.last_name, Player.first_name)
        .all()
    )

    return render_template('players/letter.html',
                          letter=letter,
                          players=players_query)


@bp.route('/<int:player_id>')
def player_detail(player_id):
    """Player detail page - bio, stats, ratings

    OPTIMIZATION: Use load_only to minimize data fetching and prevent
    cascading eager loads. Only load columns we actually use in the template.
    Manual caching implemented due to Flask-Caching decorator issues.
    """
    # Manual cache check
    # Note: Flask-Caching automatically adds CACHE_KEY_PREFIX (e.g., 'rb2_staging:')
    cache_key = f'player_detail:{player_id}'
    cached_data = cache.get(cache_key)

    import logging
    logging.warning(f"Cache lookup for {cache_key}: {'HIT' if cached_data else 'MISS'}")

    if cached_data is not None:
        logging.warning(f"Cache hit! Returning cached data for player {player_id}")
        return cached_data

    from sqlalchemy.orm import load_only, selectinload, raiseload, lazyload
    from app.models import PlayerCurrentStatus, City, State, Nation, Team
    from app.models import PlayerBattingRatings, PlayerPitchingRatings, PlayerFieldingRatings

    # Query with strict column and relationship control
    # CRITICAL: Override model's lazy='joined' with selectinload + load_only to prevent cascades
    player = (Player.query
              .options(
                  # Load only core player bio fields
                  load_only(
                      Player.player_id,
                      Player.first_name,
                      Player.last_name,
                      Player.nick_name,
                      Player.date_of_birth,
                      Player.height,
                      Player.weight,
                      Player.bats,
                      Player.throws,
                      Player.city_of_birth_id,
                      Player.nation_id,
                      Player.second_nation_id
                  ),
                  # Load city with state and nation for birthplace_display
                  selectinload(Player.city_of_birth).load_only(
                      City.city_id,
                      City.name,
                      City.state_id,
                      City.nation_id
                  ).selectinload(City.state).load_only(
                      State.state_id,
                      State.nation_id,
                      State.abbreviation
                  ).selectinload(State.nation).load_only(
                      Nation.nation_id,
                      Nation.abbreviation
                  ).raiseload('*'),
                  # Load nation name only (no cascades)
                  selectinload(Player.nation).load_only(
                      Nation.nation_id,
                      Nation.name,
                      Nation.abbreviation
                  ).raiseload('*'),
                  # Load second nation if exists
                  selectinload(Player.second_nation).load_only(
                      Nation.nation_id,
                      Nation.name,
                      Nation.abbreviation
                  ).raiseload('*'),
                  # Load current status with minimal team info
                  selectinload(Player.current_status).load_only(
                      PlayerCurrentStatus.player_id,
                      PlayerCurrentStatus.team_id,
                      PlayerCurrentStatus.position,
                      PlayerCurrentStatus.retired
                  ).selectinload(PlayerCurrentStatus.team).load_only(
                      Team.team_id,
                      Team.name,
                      Team.abbr
                  ).raiseload('*'),
                  # Override lazy='joined' on ratings - use lazyload instead
                  # This prevents them from being loaded in the main query
                  lazyload(Player.batting_ratings),
                  lazyload(Player.pitching_ratings),
                  lazyload(Player.fielding_ratings),
                  # Block ALL other relationships
                  raiseload('*')
              )
              .filter_by(player_id=player_id)
              .first_or_404())

    # Get batting stats with career totals from service layer (split by league level)
    # OPTIMIZATION: These service calls are already optimized with raw SQL
    # Each call executes 2 SQL queries (yearly stats + career totals aggregation)
    # Total: 4 calls * 2 queries = 8 SQL queries for stats
    # Note: We only fetch Major and Minor league stats separately (not "ALL LEVELS")
    # This reduces query load by 33% while still providing complete data
    batting_data_major_raw = player_service.get_player_career_batting_stats(player_id, league_level_filter=1)
    batting_data_minor_raw = player_service.get_player_career_batting_stats(player_id, league_level_filter=2)

    # Get pitching stats with career totals from service layer (split by league level)
    pitching_data_major_raw = player_service.get_player_career_pitching_stats(player_id, league_level_filter=1)
    pitching_data_minor_raw = player_service.get_player_career_pitching_stats(player_id, league_level_filter=2)

    # Get trade history
    trade_history_raw = player_service.get_player_trade_history(player_id)

    # Get player news (contracts, injuries, awards, highlights, career milestones)
    player_news_raw = player_service.get_player_news(player_id)

    # Convert dicts to objects for template compatibility
    batting_data_major = {
        'yearly_stats': _convert_dict_list_to_objects(batting_data_major_raw.get('yearly_stats', [])),
        'career_totals': DictToObject(batting_data_major_raw['career_totals']) if batting_data_major_raw.get('career_totals') else None
    }
    batting_data_minor = {
        'yearly_stats': _convert_dict_list_to_objects(batting_data_minor_raw.get('yearly_stats', [])),
        'career_totals': DictToObject(batting_data_minor_raw['career_totals']) if batting_data_minor_raw.get('career_totals') else None
    }
    pitching_data_major = {
        'yearly_stats': _convert_dict_list_to_objects(pitching_data_major_raw.get('yearly_stats', [])),
        'career_totals': DictToObject(pitching_data_major_raw['career_totals']) if pitching_data_major_raw.get('career_totals') else None
    }
    pitching_data_minor = {
        'yearly_stats': _convert_dict_list_to_objects(pitching_data_minor_raw.get('yearly_stats', [])),
        'career_totals': DictToObject(pitching_data_minor_raw['career_totals']) if pitching_data_minor_raw.get('career_totals') else None
    }
    trade_history = _convert_dict_list_to_objects(trade_history_raw)
    player_news = _convert_dict_list_to_objects(player_news_raw)

    rendered_html = render_template('players/detail.html',
                          player=player,
                          batting_data_major=batting_data_major,
                          batting_data_minor=batting_data_minor,
                          pitching_data_major=pitching_data_major,
                          pitching_data_minor=pitching_data_minor,
                          trade_history=trade_history,
                          player_news=player_news)

    # Cache the rendered HTML string
    import logging
    set_result = cache.set(cache_key, rendered_html, timeout=600)
    logging.warning(f"Cache set for {cache_key}: {set_result}")

    # Immediately test retrieval
    test_get = cache.get(cache_key)
    logging.warning(f"Immediate cache test for {cache_key}: {'SUCCESS' if test_get else 'FAILED'}")

    return rendered_html


@bp.route('/image/<int:player_id>')
def player_image(player_id):
    """Serve player image from ETL data directory.

    Returns player_{player_id}.png or a placeholder if not found.
    """
    # Path to player images
    # From web/app/routes -> up 3 levels to rb2/ -> etl/data/images/players
    image_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        '../../../etl/data/images/players'
    ))

    image_path = os.path.join(image_dir, f'player_{player_id}.png')

    if os.path.exists(image_path):
        return send_file(image_path, mimetype='image/png')
    else:
        # Return 404 or a placeholder image
        abort(404)