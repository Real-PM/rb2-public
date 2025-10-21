# Newspaper Section - LLM-Generated Articles Brainstorm

## Overview
Generate short newspaper articles about games featuring Branch family members using LLM technology. Articles will combine structured game data with narrative play-by-play details to create engaging, period-appropriate sports journalism.
Additionally, we can provide filler articles from the database `messages` table.

## Data Sources

### Primary CSVs
1. **games.csv** - Game-level metadata
   - Columns: game_id, league_id, home_team, away_team, attendance, date, time, game_type, innings, runs0, runs1, hits0, hits1, errors0, errors1, winning_pitcher, losing_pitcher, save_pitcher, starter0, starter1

2. **players_game_batting.csv** - Individual batting performance per game
   - Columns: player_id, year, team_id, game_id, league_id, level_id, split_id, position, ab, h, k, pa, pitches_seen, g, gs, d, t, hr, r, rbi, sb, cs, bb, ibb, gdp, sh, sf, hp, ci, wpa, stint, ubr

3. **players_game_pitching_stats.csv** - Individual pitching performance per game
   - Columns: player_id, year, team_id, game_id, league_id, level_id, split_id, ip, ab, tb, ha, k, bf, rs, bb, r, er, gb, fb, pi, ipf, g, gs, w, l, s, sa, da, sh, sf, ta, hra, bk, ci, iw, wp, hp, gf, dp, qs, svo, bs, ra, cg, sho, sb, cs, hld, ir, irs, wpa, li, stint, outs, sd, md

4. **game_logs.csv** - Play-by-play details (LARGE FILE: 665K lines, 36MB)
   - Columns: game_id, type, line, text
   - Type codes:
     - 1 = Inning header
     - 2 = Batter/pitcher change
     - 3 = Play outcome (pitch, hit, out, etc.)
     - 4 = Inning summary
   - Contains: Pitch sequences, exit velocity, hit location, defensive plays, HTML links to players
   - **Challenge**: File grows continuously, needs pruning/archival strategy

### Supporting Data (from database)
- **players_core**: Name, position, biographical data
- **teams**: Team name, nickname, logo
- **leagues**: League name, logo
- **coaches**: Manager information

## Workflow Architecture

### 1. Identify Branch Family Games

**Initialization (one-time)**
```python
def get_branch_family_ids():
    """
    Query players_core for all Branch family members.
    Returns: List of player_ids
    """
    query = """
        SELECT player_id, first_name, last_name, nickname
        FROM players_core
        WHERE last_name = 'Branch'
        ORDER BY player_id;
    """
    return db.execute(query).fetchall()
```

**Daily/Batch Detection**
```python
def detect_branch_games(branch_player_ids, date_range=None):
    """
    Scan players_game_batting and players_game_pitching for Branch appearances.

    Args:
        branch_player_ids: List of player_ids to monitor
        date_range: Optional tuple (start_date, end_date) for incremental processing

    Returns:
        List of dicts: [{game_id, player_id, performance_type, stats}, ...]
    """
    # Query batting appearances
    batting_games = """
        SELECT DISTINCT
            pgb.game_id,
            pgb.player_id,
            'batting' as perf_type,
            pgb.ab, pgb.h, pgb.hr, pgb.rbi, pgb.bb, pgb.k, pgb.sb
        FROM players_game_batting pgb
        JOIN games g ON pgb.game_id = g.game_id
        WHERE pgb.player_id IN ({})
        {}
        AND pgb.split_id = 0  -- Overall stats, not splits
    """.format(
        ','.join(map(str, branch_player_ids)),
        f"AND g.date >= '{date_range[0]}' AND g.date <= '{date_range[1]}'" if date_range else ""
    )

    # Query pitching appearances
    pitching_games = """
        SELECT DISTINCT
            pgp.game_id,
            pgp.player_id,
            'pitching' as perf_type,
            pgp.ip, pgp.ha as h, pgp.r, pgp.er, pgp.k, pgp.bb,
            pgp.w, pgp.l, pgp.s, pgp.qs
        FROM players_game_pitching_stats pgp
        JOIN games g ON pgp.game_id = g.game_id
        WHERE pgp.player_id IN ({})
        {}
        AND pgp.split_id = 1  -- Overall stats
    """.format(
        ','.join(map(str, branch_player_ids)),
        f"AND g.date >= '{date_range[0]}' AND g.date <= '{date_range[1]}'" if date_range else ""
    )

    # Combine results
    batting_results = db.execute(batting_games).fetchall()
    pitching_results = db.execute(pitching_games).fetchall()

    return batting_results + pitching_results
```

### 2. Prioritize Games for Article Generation

**Newsworthiness Criteria**
```python
def calculate_newsworthiness(performance):
    """
    Score games based on performance quality to prioritize article generation.

    Returns: int score (0-100), higher = more newsworthy
    """
    score = 0
    perf_type = performance['perf_type']

    if perf_type == 'batting':
        # Must-generate events (score 80+)
        if performance['hr'] >= 2:
            score += 50  # Multi-HR game
        if performance['h'] >= 4:
            score += 40  # 4+ hit game
        if performance['rbi'] >= 5:
            score += 45  # 5+ RBI game

        # Should-generate events (score 50-79)
        if performance['hr'] == 1:
            score += 25
        if performance['h'] >= 3:
            score += 20
        if performance['rbi'] >= 3:
            score += 20
        if performance['sb'] >= 2:
            score += 15

        # Nice-to-have (score 20-49)
        if performance['h'] >= 2:
            score += 10
        if performance['rbi'] >= 1:
            score += 5

    elif perf_type == 'pitching':
        # Must-generate (80+)
        if performance['qs'] == 1 and performance['k'] >= 10:
            score += 60  # Quality start with 10+ K
        if performance['sho'] == 1:
            score += 70  # Shutout
        if performance['s'] == 1 and performance['ip'] >= 2:
            score += 40  # Multi-inning save

        # Should-generate (50-79)
        if performance['w'] == 1 and performance['ip'] >= 6:
            score += 35  # Win as starter
        if performance['qs'] == 1:
            score += 30  # Quality start
        if performance['s'] == 1:
            score += 25  # Save

        # Nice-to-have (20-49)
        if performance['w'] == 1:
            score += 15
        if performance['k'] >= 7:
            score += 10

    return min(score, 100)  # Cap at 100

def prioritize_games(branch_games):
    """
    Sort games by newsworthiness, add priority tier.

    Returns: List of games with 'priority' field added
    """
    scored_games = []
    for game in branch_games:
        score = calculate_newsworthiness(game)
        game['newsworthiness_score'] = score

        if score >= 80:
            game['priority'] = 'MUST_GENERATE'
        elif score >= 50:
            game['priority'] = 'SHOULD_GENERATE'
        elif score >= 20:
            game['priority'] = 'COULD_GENERATE'
        else:
            game['priority'] = 'SKIP'

        scored_games.append(game)

    return sorted(scored_games, key=lambda x: x['newsworthiness_score'], reverse=True)
```

### 3. Gather Game Context

**Basic Game Data**
```python
def get_game_context(game_id):
    """
    Fetch game metadata, teams, score, attendance, etc.

    Returns: dict with game details
    """
    query = """
        SELECT
            g.game_id,
            g.date,
            g.attendance,
            g.innings,
            g.runs0 as away_runs,
            g.runs1 as home_runs,
            g.hits0 as away_hits,
            g.hits1 as home_hits,
            ht.name as home_team_name,
            ht.nickname as home_team_nickname,
            ht.abbr as home_team_abbr,
            at.name as away_team_name,
            at.nickname as away_team_nickname,
            at.abbr as away_team_abbr,
            l.name as league_name,
            l.abbr as league_abbr,
            wp.first_name || ' ' || wp.last_name as winning_pitcher,
            lp.first_name || ' ' || lp.last_name as losing_pitcher,
            sp.first_name || ' ' || sp.last_name as save_pitcher
        FROM games g
        JOIN teams ht ON g.home_team = ht.team_id
        JOIN teams at ON g.away_team = at.team_id
        JOIN leagues l ON g.league_id = l.league_id
        LEFT JOIN players_core wp ON g.winning_pitcher = wp.player_id
        LEFT JOIN players_core lp ON g.losing_pitcher = lp.player_id
        LEFT JOIN players_core sp ON g.save_pitcher = sp.player_id
        WHERE g.game_id = {}
    """.format(game_id)

    return db.execute(query).fetchone()
```

**Branch Player Details**
```python
def get_branch_player_details(player_id, game_id, perf_type):
    """
    Get player name, position, and full game stats.

    Returns: dict with player info and stats
    """
    # Get player bio
    player_query = """
        SELECT
            player_id,
            first_name,
            last_name,
            nickname,
            position
        FROM players_core
        WHERE player_id = {}
    """.format(player_id)

    player = db.execute(player_query).fetchone()

    # Get stats for this game
    if perf_type == 'batting':
        stats_query = """
            SELECT ab, h, d as doubles, t as triples, hr, r, rbi, sb, cs, bb, k, pa
            FROM players_game_batting
            WHERE player_id = {} AND game_id = {} AND split_id = 0
        """.format(player_id, game_id)
    else:  # pitching
        stats_query = """
            SELECT ip, ha as h, r, er, bb, k, w, l, s, qs, cg, sho, bf, pi as pitches
            FROM players_game_pitching_stats
            WHERE player_id = {} AND game_id = {} AND split_id = 1
        """.format(player_id, game_id)

    stats = db.execute(stats_query).fetchone()

    return {
        'player': player,
        'stats': stats
    }
```

### 4. Parse game_logs.csv (Selective Extraction)

**Strategy**: Extract only Branch-related plays to minimize storage

```python
def extract_branch_plays_from_game_log(game_id, branch_player_ids):
    """
    Parse game_logs.csv for specific game and extract plays involving Branch family.

    Args:
        game_id: Game to extract
        branch_player_ids: List of player IDs to look for

    Returns: Structured play-by-play data for Branch players only
    """
    import csv

    # Build player ID string patterns to search for
    # e.g., "player_123.html" for player_id 123
    player_patterns = [f"player_{pid}.html" for pid in branch_player_ids]

    branch_plays = []
    current_inning = None
    context_buffer = []  # Keep 5 lines of context
    in_branch_sequence = False

    with open('etl/data/incoming/csv/game_logs.csv', 'r') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Only process this game
            if int(row['game_id']) != game_id:
                continue

            log_type = int(row['type'])
            text = row['text']

            # Track current inning
            if log_type == 1:  # Inning header
                if 'Top of' in text:
                    current_inning = int(text.split('Top of')[1].split('st')[0].split('nd')[0].split('rd')[0].split('th')[0].strip())
                    half = 'top'
                elif 'Bottom of' in text:
                    current_inning = int(text.split('Bottom of')[1].split('st')[0].split('nd')[0].split('rd')[0].split('th')[0].strip())
                    half = 'bottom'

            # Check if Branch player is mentioned
            branch_mentioned = any(pattern in text for pattern in player_patterns)

            if branch_mentioned or in_branch_sequence:
                if branch_mentioned and not in_branch_sequence:
                    # Start of Branch sequence - add context
                    in_branch_sequence = True
                    branch_plays.extend(context_buffer)

                branch_plays.append({
                    'game_id': game_id,
                    'inning': current_inning,
                    'half': half,
                    'type': log_type,
                    'line': int(row['line']),
                    'text': text
                })

                # If inning summary, end sequence
                if log_type == 4:
                    in_branch_sequence = False

                # If 5 lines after Branch at-bat, end sequence
                if in_branch_sequence and len(branch_plays) > 0:
                    last_branch_line = next((p['line'] for p in reversed(branch_plays)
                                            if any(pat in p['text'] for pat in player_patterns)), None)
                    if last_branch_line and int(row['line']) > last_branch_line + 5:
                        in_branch_sequence = False

            # Maintain context buffer (last 5 lines)
            context_buffer.append({
                'game_id': game_id,
                'inning': current_inning,
                'half': half if current_inning else None,
                'type': log_type,
                'line': int(row['line']),
                'text': text
            })
            if len(context_buffer) > 5:
                context_buffer.pop(0)

    return branch_plays

def structure_branch_at_bats(branch_plays, player_id):
    """
    Convert raw play sequence into structured at-bat summaries.

    Returns: List of at-bat dicts with pitch sequence and outcome
    """
    at_bats = []
    current_ab = None

    for play in branch_plays:
        text = play['text']

        # Detect start of at-bat
        if play['type'] == 2 and 'Batting:' in text and f"player_{player_id}.html" in text:
            if current_ab:
                at_bats.append(current_ab)

            current_ab = {
                'inning': play['inning'],
                'half': play['half'],
                'pitches': [],
                'outcome': None,
                'outcome_details': None
            }

        # Capture pitch sequence
        elif current_ab and play['type'] == 3:
            if any(x in text for x in ['Ball', 'Strike', 'Foul']):
                current_ab['pitches'].append(text)

            # Capture outcome
            if any(x in text for x in ['SINGLE', 'DOUBLE', 'TRIPLE', 'HOME RUN',
                                        'out', 'Strikes out', 'Base on Balls',
                                        'Grounds into double play']):
                current_ab['outcome'] = text

                # Extract details (exit velocity, location)
                if 'EV' in text:
                    import re
                    ev_match = re.search(r'EV ([\d.]+) MPH', text)
                    if ev_match:
                        current_ab['exit_velocity'] = float(ev_match.group(1))

                if 'location:' in text:
                    location = text.split('location:')[1].strip()
                    current_ab['hit_location'] = location

    if current_ab:
        at_bats.append(current_ab)

    return at_bats
```

### 5. Build LLM Prompt

```python
def build_article_prompt(game_context, branch_player_details, branch_at_bats=None):
    """
    Construct a detailed prompt for the LLM to generate a newspaper article.

    Args:
        game_context: Dict with game metadata
        branch_player_details: Dict with player info and stats
        branch_at_bats: Optional list of play-by-play at-bats

    Returns: String prompt for LLM
    """
    player = branch_player_details['player']
    stats = branch_player_details['stats']
    perf_type = 'batting' if 'ab' in stats else 'pitching'

    # Format player name
    full_name = f"{player['first_name']} {player['last_name']}"
    if player['nickname']:
        full_name = f"{player['first_name']} '{player['nickname']}' {player['last_name']}"

    # Build prompt
    prompt = f"""You are a veteran baseball sportswriter for the {game_context['league_name']} in {game_context['date'][:4]}.
Write a concise, engaging newspaper article (200-250 words) about the following game.
Focus on {full_name}'s performance and the game's key moments.
Use a journalistic style appropriate for 1960s-era sports section - descriptive but factual, with period-appropriate language.

GAME DETAILS:
- Date: {game_context['date']}
- Matchup: {game_context['away_team_nickname']} at {game_context['home_team_nickname']}
- Final Score: {game_context['away_team_abbr']} {game_context['away_runs']}, {game_context['home_team_abbr']} {game_context['home_runs']}
- Innings: {game_context['innings']}
- Attendance: {game_context['attendance']:,}
- Winning Pitcher: {game_context['winning_pitcher']}
- Losing Pitcher: {game_context['losing_pitcher']}
"""

    if game_context['save_pitcher']:
        prompt += f"- Save: {game_context['save_pitcher']}\n"

    prompt += f"\n{full_name.upper()}'S PERFORMANCE:\n"

    if perf_type == 'batting':
        prompt += f"- Position: {player['position']}\n"
        prompt += f"- Batting Line: {stats['h']}-for-{stats['ab']}"
        if stats['doubles']:
            prompt += f", {stats['doubles']} 2B"
        if stats['triples']:
            prompt += f", {stats['triples']} 3B"
        if stats['hr']:
            prompt += f", {stats['hr']} HR"
        prompt += f", {stats['rbi']} RBI, {stats['r']} R, {stats['bb']} BB, {stats['k']} K"
        if stats['sb']:
            prompt += f", {stats['sb']} SB"
        prompt += "\n"

        # Add play-by-play if available
        if branch_at_bats:
            prompt += "\nKEY AT-BATS:\n"
            for i, ab in enumerate(branch_at_bats, 1):
                prompt += f"\nAt-Bat {i} ({ab['half'].title()} of {ab['inning']}):\n"
                if ab['pitches']:
                    pitch_summary = f"  - Pitch sequence: {len(ab['pitches'])} pitches"
                    # Check for full count
                    if any('3-2' in p for p in ab['pitches']):
                        pitch_summary += " (went to 3-2 count)"
                    prompt += pitch_summary + "\n"

                if ab['outcome']:
                    prompt += f"  - Outcome: {ab['outcome']}\n"
                    if ab.get('exit_velocity'):
                        prompt += f"  - Exit Velocity: {ab['exit_velocity']} MPH\n"

    else:  # pitching
        prompt += f"- Pitching Line: {stats['ip']} IP, {stats['h']} H, {stats['r']} R, {stats['er']} ER, {stats['k']} K, {stats['bb']} BB\n"
        prompt += f"- Pitches Thrown: {stats['pitches']}\n"

        if stats['w']:
            prompt += f"- Result: WIN\n"
        elif stats['l']:
            prompt += f"- Result: LOSS\n"
        elif stats['s']:
            prompt += f"- Result: SAVE\n"

        if stats['qs']:
            prompt += f"- Quality Start: YES\n"
        if stats['cg']:
            prompt += f"- Complete Game: YES\n"
        if stats['sho']:
            prompt += f"- Shutout: YES\n"

    prompt += """
INSTRUCTIONS:
1. Write in past tense
2. Lead with the most compelling angle (Branch's key contribution or game-deciding moment)
3. Include the final score and game outcome in the opening paragraph
4. Describe 2-3 key moments from the game with specific details
5. Mention other notable performances if relevant to the story
6. End with a forward-looking statement (standings, next game, season record)
7. Use period-appropriate baseball terminology (no modern analytics jargon)
8. Keep it factual but engaging - this is journalism, not creative fiction

Generate the article with a headline on the first line (format: "HEADLINE: [headline text]"),
followed by a blank line, then the article body.
"""

    return prompt
```

### 6. Generate Article with LLM

```python
def generate_article_ollama(prompt, model='llama3'):
    """
    Call Ollama API to generate article from prompt.

    Args:
        prompt: String prompt built by build_article_prompt()
        model: Ollama model name (llama3, mistral, etc.)

    Returns: Generated article text
    """
    import requests
    import json

    # Ollama API endpoint (local)
    url = 'http://localhost:11434/api/generate'

    payload = {
        'model': model,
        'prompt': prompt,
        'stream': False,
        'options': {
            'temperature': 0.7,  # Some creativity but stay factual
            'top_p': 0.9,
            'max_tokens': 400  # ~250-300 words
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        return result['response']

    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama: {e}")
        return None

def generate_article_claude(prompt, api_key):
    """
    Call Claude API for higher-quality articles (use for milestone games).

    Args:
        prompt: String prompt
        api_key: Anthropic API key

    Returns: Generated article text
    """
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return message.content[0].text

    except Exception as e:
        print(f"Error calling Claude API: {e}")
        return None

def parse_article_output(raw_text):
    """
    Extract headline and body from LLM output.

    Returns: dict with 'headline' and 'body'
    """
    lines = raw_text.strip().split('\n')

    headline = None
    body_lines = []

    for line in lines:
        if line.startswith('HEADLINE:'):
            headline = line.replace('HEADLINE:', '').strip()
        elif line.strip() and headline:
            body_lines.append(line)

    # If no HEADLINE: marker found, use first line
    if not headline and lines:
        headline = lines[0].strip()
        body_lines = lines[2:] if len(lines) > 2 else []

    return {
        'headline': headline,
        'body': '\n\n'.join(body_lines)
    }
```

### 7. Store Article in Database

```sql
-- Database schema for newspaper articles
CREATE TABLE newspaper_articles (
    article_id SERIAL PRIMARY KEY,
    game_id INT REFERENCES games(game_id),
    article_date DATE NOT NULL,
    headline VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    article_type VARCHAR(50) NOT NULL,  -- 'game_recap_branch', 'milestone', 'user_written', 'game_generated'
    generation_method VARCHAR(50),       -- 'llm_ollama', 'llm_claude', 'manual'
    model_used VARCHAR(50),              -- 'llama3', 'claude-3-5-sonnet', NULL
    newsworthiness_score INT,            -- 0-100 priority score
    player_ids INT[],                    -- Array of featured player IDs
    team_ids INT[],                      -- Featured teams
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    published BOOLEAN DEFAULT FALSE,
    CONSTRAINT valid_score CHECK (newsworthiness_score >= 0 AND newsworthiness_score <= 100)
);

CREATE INDEX idx_articles_date ON newspaper_articles(article_date DESC);
CREATE INDEX idx_articles_player_ids ON newspaper_articles USING GIN(player_ids);
CREATE INDEX idx_articles_game_id ON newspaper_articles(game_id);
CREATE INDEX idx_articles_published ON newspaper_articles(published) WHERE published = TRUE;

-- Branch-specific game moments (extracted from game_logs)
CREATE TABLE branch_game_moments (
    moment_id SERIAL PRIMARY KEY,
    game_id INT REFERENCES games(game_id),
    player_id INT REFERENCES players_core(player_id),
    inning INT,
    inning_half VARCHAR(10),  -- 'top' or 'bottom'
    moment_type VARCHAR(50),   -- 'at_bat', 'pitching', 'defensive_play', 'baserunning'
    play_sequence JSONB,       -- Array of play-by-play lines
    outcome VARCHAR(200),
    exit_velocity DECIMAL(5,1),
    hit_location VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_moments_game_player ON branch_game_moments(game_id, player_id);
CREATE INDEX idx_moments_player ON branch_game_moments(player_id);
```

```python
def save_article(article_data, game_id, player_ids, team_ids):
    """
    Store generated article in database.

    Args:
        article_data: Dict with 'headline' and 'body'
        game_id: Game ID
        player_ids: List of featured player IDs
        team_ids: List of featured team IDs

    Returns: article_id of inserted record
    """
    query = """
        INSERT INTO newspaper_articles
        (game_id, article_date, headline, body, article_type, generation_method,
         model_used, newsworthiness_score, player_ids, team_ids, published)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING article_id;
    """

    # Get game date
    game_date = db.execute("SELECT date FROM games WHERE game_id = %s", (game_id,)).fetchone()['date']

    values = (
        game_id,
        game_date,
        article_data['headline'],
        article_data['body'],
        'game_recap_branch',
        article_data.get('generation_method', 'llm_ollama'),
        article_data.get('model_used', 'llama3'),
        article_data.get('newsworthiness_score', 50),
        player_ids,  # PostgreSQL array
        team_ids,    # PostgreSQL array
        True  # Auto-publish for now
    )

    result = db.execute(query, values)
    article_id = result.fetchone()['article_id']
    db.commit()

    return article_id
```

## game_logs.csv Management Strategy

### Challenge
- Current size: 665K lines, 36MB
- Grows by ~300-500 lines per game
- Full season (1,000+ games) = additional 300K-500K lines
- Multi-season accumulation will make file unwieldy

### Recommended Approach: Hybrid Storage

#### 1. Extract Branch Plays Only (Primary Strategy)
```python
def etl_branch_moments(game_id, branch_player_ids):
    """
    ETL job: Extract Branch plays from game_logs.csv and store in branch_game_moments table.
    Run after each game data import.
    """
    branch_plays = extract_branch_plays_from_game_log(game_id, branch_player_ids)
    structured_abs = structure_branch_at_bats(branch_plays, branch_player_ids[0])

    for ab in structured_abs:
        query = """
            INSERT INTO branch_game_moments
            (game_id, player_id, inning, inning_half, moment_type, play_sequence,
             outcome, exit_velocity, hit_location)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """

        values = (
            game_id,
            branch_player_ids[0],  # Would need to detect which player
            ab['inning'],
            ab['half'],
            'at_bat',
            json.dumps(ab['pitches']),
            ab['outcome'],
            ab.get('exit_velocity'),
            ab.get('hit_location')
        )

        db.execute(query, values)

    db.commit()
```

#### 2. Rolling Window: Keep Current Season Only
```python
def prune_game_logs(current_season_year):
    """
    Archive and prune game_logs.csv to keep only current season.
    Run at end of each season.
    """
    import shutil
    import gzip

    # Read full game_logs
    with open('etl/data/incoming/csv/game_logs.csv', 'r') as f:
        all_lines = f.readlines()

    # Separate current season from historical
    header = all_lines[0]
    current_season_lines = [header]
    historical_lines = [header]

    for line in all_lines[1:]:
        game_id = int(line.split(',')[0])
        # Query game year
        year = db.execute(
            "SELECT EXTRACT(YEAR FROM date) as year FROM games WHERE game_id = %s",
            (game_id,)
        ).fetchone()['year']

        if year == current_season_year:
            current_season_lines.append(line)
        else:
            historical_lines.append(line)

    # Archive historical data
    archive_path = f'etl/data/archive/game_logs_{current_season_year-1}.csv.gz'
    with gzip.open(archive_path, 'wt') as f:
        f.writelines(historical_lines)

    # Write current season only back to active file
    with open('etl/data/incoming/csv/game_logs.csv', 'w') as f:
        f.writelines(current_season_lines)

    print(f"Archived {len(historical_lines)-1} historical lines to {archive_path}")
    print(f"Kept {len(current_season_lines)-1} current season lines in active file")
```

#### 3. On-Demand Parsing for Regeneration
```python
def get_game_log_from_archive(game_id):
    """
    If regenerating an article for an old game, pull from archive.
    """
    import gzip

    # Determine which archive file based on game year
    year = db.execute(
        "SELECT EXTRACT(YEAR FROM date) as year FROM games WHERE game_id = %s",
        (game_id,)
    ).fetchone()['year']

    archive_path = f'etl/data/archive/game_logs_{year}.csv.gz'

    if not os.path.exists(archive_path):
        # Try active file
        return extract_branch_plays_from_game_log(game_id, branch_player_ids)

    # Parse from archive
    with gzip.open(archive_path, 'rt') as f:
        # Filter for game_id
        game_lines = [line for line in f if line.startswith(f"{game_id},")]

    # Process extracted lines
    # ... (same extraction logic)
```

## Full Pipeline Integration

```python
# Main orchestration script
def generate_branch_articles_pipeline(date_range=None):
    """
    End-to-end pipeline for generating Branch family articles.

    Args:
        date_range: Optional (start_date, end_date) for incremental processing

    Flow:
        1. Identify Branch games
        2. Prioritize by newsworthiness
        3. For each high-priority game:
            a. Gather context
            b. Extract game_log plays
            c. Build prompt
            d. Generate article
            e. Save to database
    """
    # 1. Get Branch family IDs
    branch_players = get_branch_family_ids()
    branch_ids = [p['player_id'] for p in branch_players]

    # 2. Detect Branch games
    branch_games = detect_branch_games(branch_ids, date_range)

    # 3. Prioritize
    prioritized = prioritize_games(branch_games)

    # Filter to MUST and SHOULD generate
    to_generate = [g for g in prioritized if g['priority'] in ['MUST_GENERATE', 'SHOULD_GENERATE']]

    print(f"Generating articles for {len(to_generate)} games...")

    # 4. Generate articles
    for game in to_generate:
        game_id = game['game_id']
        player_id = game['player_id']
        perf_type = game['perf_type']

        print(f"Processing game {game_id}, player {player_id}...")

        # Gather data
        game_context = get_game_context(game_id)
        player_details = get_branch_player_details(player_id, game_id, perf_type)

        # Extract plays (and store in branch_game_moments)
        branch_plays = extract_branch_plays_from_game_log(game_id, [player_id])
        at_bats = structure_branch_at_bats(branch_plays, player_id) if perf_type == 'batting' else None

        # Store moments
        etl_branch_moments(game_id, [player_id])

        # Build prompt
        prompt = build_article_prompt(game_context, player_details, at_bats)

        # Generate (use Claude for MUST_GENERATE, Ollama for SHOULD)
        if game['priority'] == 'MUST_GENERATE':
            raw_article = generate_article_claude(prompt, api_key=os.getenv('ANTHROPIC_API_KEY'))
            generation_method = 'llm_claude'
            model_used = 'claude-3-5-sonnet'
        else:
            raw_article = generate_article_ollama(prompt, model='llama3')
            generation_method = 'llm_ollama'
            model_used = 'llama3'

        if not raw_article:
            print(f"Failed to generate article for game {game_id}")
            continue

        # Parse output
        article = parse_article_output(raw_article)
        article['generation_method'] = generation_method
        article['model_used'] = model_used
        article['newsworthiness_score'] = game['newsworthiness_score']

        # Save
        article_id = save_article(
            article,
            game_id,
            player_ids=[player_id],
            team_ids=[game_context['home_team_id'], game_context['away_team_id']]
        )

        print(f"  → Created article {article_id}: {article['headline']}")

    print(f"\nGenerated {len(to_generate)} articles successfully!")
```

## Website Integration

### Flask Routes
```python
# In app/routes/newspaper.py

@bp.route('/newspaper')
def newspaper_home():
    """
    Newspaper home page - chronological feed of articles.
    """
    # Get recent articles (last 30 days)
    articles = db.execute("""
        SELECT
            article_id,
            headline,
            article_date,
            LEFT(body, 200) as excerpt,
            player_ids
        FROM newspaper_articles
        WHERE published = TRUE
        ORDER BY article_date DESC, created_at DESC
        LIMIT 50;
    """).fetchall()

    return render_template('newspaper/index.html', articles=articles)

@bp.route('/newspaper/article/<int:article_id>')
def article_detail(article_id):
    """
    Individual article page with full content and box score.
    """
    article = db.execute("""
        SELECT
            na.*,
            g.home_team, g.away_team, g.runs0, g.runs1
        FROM newspaper_articles na
        JOIN games g ON na.game_id = g.game_id
        WHERE na.article_id = %s;
    """, (article_id,)).fetchone()

    if not article:
        abort(404)

    # Get featured players
    players = db.execute("""
        SELECT player_id, first_name, last_name, position
        FROM players_core
        WHERE player_id = ANY(%s);
    """, (article['player_ids'],)).fetchall()

    # Get box score summary
    box_score = get_box_score_summary(article['game_id'])

    return render_template('newspaper/article.html',
                          article=article,
                          players=players,
                          box_score=box_score)

@bp.route('/newspaper/player/<int:player_id>')
def player_articles(player_id):
    """
    All articles mentioning a specific player.
    """
    articles = db.execute("""
        SELECT article_id, headline, article_date, LEFT(body, 150) as excerpt
        FROM newspaper_articles
        WHERE %s = ANY(player_ids)
        AND published = TRUE
        ORDER BY article_date DESC;
    """, (player_id,)).fetchall()

    player = db.execute("""
        SELECT first_name, last_name FROM players_core WHERE player_id = %s
    """, (player_id,)).fetchone()

    return render_template('newspaper/player_articles.html',
                          articles=articles,
                          player=player)
```

### Templates

**newspaper/index.html**
```html
{% extends "base.html" %}

{% block content %}
<div class="max-w-4xl mx-auto">
    <h1 class="text-4xl font-bold mb-8">The Branch Family Chronicle</h1>

    <div class="space-y-6">
        {% for article in articles %}
        <article class="border-b pb-6">
            <div class="text-sm text-gray-600 mb-2">{{ article.article_date }}</div>
            <h2 class="text-2xl font-bold mb-2">
                <a href="{{ url_for('newspaper.article_detail', article_id=article.article_id) }}"
                   class="hover:text-blue-700">
                    {{ article.headline }}
                </a>
            </h2>
            <p class="text-gray-800">{{ article.excerpt }}...</p>
            <a href="{{ url_for('newspaper.article_detail', article_id=article.article_id) }}"
               class="text-blue-600 hover:underline">
                Read more →
            </a>
        </article>
        {% endfor %}
    </div>
</div>
{% endblock %}
```

## Future Enhancements

### 1. Career Context
```python
def add_career_context(player_id, current_date):
    """
    Add season/career stats to article prompt for context.
    E.g., "Branch improved to .312 on the season with his 3-hit performance"
    """
    career_stats = db.execute("""
        SELECT
            SUM(h) as season_hits,
            SUM(ab) as season_abs,
            ROUND(SUM(h)::DECIMAL / NULLIF(SUM(ab), 0), 3) as season_avg
        FROM players_game_batting
        WHERE player_id = %s
        AND year = EXTRACT(YEAR FROM %s::date)
        AND split_id = 0
    """, (player_id, current_date)).fetchone()

    return career_stats
```

### 2. Series/Streak Detection
```python
def detect_hot_streak(player_id, game_id):
    """
    Identify if player is on a hitting streak to mention in article.
    """
    # Get last 10 games chronologically
    recent_games = db.execute("""
        SELECT game_id, h
        FROM players_game_batting pgb
        JOIN games g ON pgb.game_id = g.game_id
        WHERE pgb.player_id = %s
        AND g.date <= (SELECT date FROM games WHERE game_id = %s)
        ORDER BY g.date DESC
        LIMIT 10
    """, (player_id, game_id)).fetchall()

    # Count consecutive games with hit
    streak = 0
    for game in recent_games:
        if game['h'] > 0:
            streak += 1
        else:
            break

    return streak if streak >= 3 else None
```

### 3. Rivalry Context
```python
def get_rivalry_history(team1_id, team2_id, current_date):
    """
    Get head-to-head record for rivalry context in article.
    """
    record = db.execute("""
        SELECT
            COUNT(*) FILTER (WHERE home_team = %s AND runs1 > runs0) as team1_wins,
            COUNT(*) FILTER (WHERE away_team = %s AND runs0 > runs1) as team1_wins_away,
            COUNT(*) FILTER (WHERE home_team = %s AND runs1 > runs0) as team2_wins,
            COUNT(*) FILTER (WHERE away_team = %s AND runs0 > runs1) as team2_wins_away
        FROM games
        WHERE ((home_team = %s AND away_team = %s) OR (home_team = %s AND away_team = %s))
        AND EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM %s::date)
    """, (team1_id, team1_id, team2_id, team2_id,
          team1_id, team2_id, team2_id, team1_id,
          current_date)).fetchone()

    return record
```

### 4. Milestone Detection
```python
def check_milestones(player_id, perf_type, game_stats):
    """
    Detect career milestones (500th hit, 100th win, etc.)
    These should be MUST_GENERATE priority.
    """
    milestones = []

    if perf_type == 'batting':
        # Calculate career totals through this game
        career_hits = db.execute("""
            SELECT SUM(h) as total_hits
            FROM players_game_batting
            WHERE player_id = %s AND split_id = 0
        """, (player_id,)).fetchone()['total_hits']

        # Check if this game crossed milestone
        if career_hits >= 500 and career_hits - game_stats['h'] < 500:
            milestones.append({'type': 'hit', 'value': 500})
        if career_hits >= 1000 and career_hits - game_stats['h'] < 1000:
            milestones.append({'type': 'hit', 'value': 1000})

        # Check HR milestones
        career_hr = db.execute("""
            SELECT SUM(hr) as total_hr
            FROM players_game_batting
            WHERE player_id = %s AND split_id = 0
        """, (player_id,)).fetchone()['total_hr']

        if career_hr >= 100 and career_hr - game_stats['hr'] < 100:
            milestones.append({'type': 'home_run', 'value': 100})

    elif perf_type == 'pitching':
        # Win milestones
        career_wins = db.execute("""
            SELECT SUM(w) as total_wins
            FROM players_game_pitching_stats
            WHERE player_id = %s AND split_id = 1
        """, (player_id,)).fetchone()['total_wins']

        if career_wins >= 100 and career_wins - game_stats['w'] < 100:
            milestones.append({'type': 'win', 'value': 100})

    return milestones
```


## Other Features and Considerations  
- **Layout.** Should mimic online newspaper with one main column (70-80%) and a right column.  Within the main column, 
one hero feature story, then 3 columns of other stories spanning that column.  
- Use stories from `messages` table for filler stories.  
- **Box scores** are generated in game and can be fetched as html pages. We should explore the possibility (and desirability)
of using these as either a data source or as newspaper content.  
- **User generated content.**  Some content will be created by the user. We will need to create an input page to create 
this content. Should include an easy mechanism to generate links to players and teams.  
- **Content types.** We will have the following types of content:  
    - Reprinted stories from `messages`. Need a way to identify suitable messages.  
    - AI-generated stories based on significant achievements or games for Branch family members or the game in general.  
    - Journal entries, written by the user from the perspective of the current Branch family lead.  
    - Historical articles, written by the user to create/continue the narrative arc of baseball history or to deep dive 
  a special topic.  
    - Historical articles, written by AI to do the same.


## Next Steps

1. **Create user stories** for:
   - ETL pipeline modifications to detect Branch games
   - game_logs parsing and storage
   - LLM integration (Ollama + Claude fallback)
   - Database schema additions
   - Flask routes and templates
   - Background job scheduling (Celery/RQ)

2. **Technical decisions** to finalize:
   - LLM model selection (llama3 vs mistral vs mixtral)
   - Article generation frequency (real-time vs batch)
   - Editorial review process (human-in-loop?)
   - Multi-Branch game handling (multiple family members)
   - Integration with user-written articles

3. **Infrastructure setup**:
   - Ollama installation and model download
   - Background job queue (Celery/Redis or RQ)
   - Archive directory structure
   - API key management (Claude fallback)

4. **Testing strategy**:
   - Test with sample games (various performance levels)
   - LLM output quality assessment
   - Performance benchmarking (generation time)
   - Data accuracy validation
