# SQLAlchemy Model Architecture Recommendation for RB2 Flask Application

## Executive Summary

This document provides architectural guidance for implementing SQLAlchemy models for the RB2 Flask application, which interfaces with a PostgreSQL database containing 50+ tables with complex relationships and materialized views. The recommendations focus on maintainability, performance, and scalability while handling the unique challenges of baseball statistics data.

## 1. Model Organization Strategy

### 1.1 Proposed File Structure

```
/web/app/models/
├── __init__.py              # Central imports and model registry
├── base.py                  # Base model class and mixins
├── enums.py                 # Shared enums and constants
│
├── core/                    # Core domain models
│   ├── __init__.py
│   ├── player.py           # PlayerCore, PlayerCurrentStatus
│   ├── team.py             # Team, TeamRecord, TeamRelations
│   ├── league.py           # League, SubLeague, Division
│   └── geography.py        # Nation, State, City, Park
│
├── stats/                   # Statistics models
│   ├── __init__.py
│   ├── batting.py          # CareerBattingStats, BattingRatings
│   ├── pitching.py         # CareerPitchingStats, PitchingRatings
│   ├── fielding.py         # CareerFieldingStats, FieldingRatings
│   └── game.py             # Game, GameSummary
│
├── history/                 # Historical tracking
│   ├── __init__.py
│   ├── team_history.py     # TeamHistory, TeamHistoryRecord
│   ├── league_history.py   # LeagueHistory, LeagueAwards
│   └── roster.py           # TeamRoster, TeamRosterStaff
│
├── content/                 # Content management
│   ├── __init__.py
│   ├── newspaper.py        # NewspaperArticle, ArticleCategory
│   └── media.py            # PersonImage, TeamLogo, LeagueLogo
│
├── views/                   # Read-only view models
│   ├── __init__.py
│   └── leaderboards.py     # Materialized view models
│
└── branch/                  # Special branch family tracking
    ├── __init__.py
    └── family.py           # BranchFamilyMember, BranchOrbitTeam
```

### 1.2 Grouping Rationale

**Domain-Based Organization**: Models are grouped by business domain rather than technical similarities. This approach:
- Improves discoverability (developers can find team-related models in one place)
- Reduces circular import risks
- Allows for domain-specific optimizations
- Facilitates team ownership if the project scales

**Separate View Models**: Materialized views get their own directory because they:
- Are read-only
- Have different lifecycle management
- May require special query optimizations

## 2. Relationship Mapping Strategy

### 2.1 Core Relationship Patterns

```python
# Example: Player relationships
class PlayerCore(Base):
    __tablename__ = 'players_core'

    # One-to-One relationships
    current_status = relationship(
        'PlayerCurrentStatus',
        back_populates='player',
        uselist=False,
        lazy='joined'  # Always load status with player
    )

    # One-to-Many relationships
    batting_stats = relationship(
        'PlayerCareerBattingStats',
        back_populates='player',
        lazy='dynamic'  # Large collection, load on demand
    )

    # Many-to-Many through association
    teams = relationship(
        'Team',
        secondary='team_roster',
        back_populates='players',
        lazy='select'  # Load when accessed
    )
```

### 2.2 Bidirectional vs Unidirectional

**Bidirectional Relationships** (use when both sides need navigation):
- Player ↔ PlayerCurrentStatus
- Team ↔ League
- Player ↔ Team (through roster)
- Article ↔ Player/Team (through tags)

**Unidirectional Relationships** (use for performance or to avoid circularity):
- Stats → Player (no need for player.all_fielding_stats)
- LeaderboardView → Player (views don't need reverse relationships)
- PersonImage → Player (player doesn't need to know about images)

### 2.3 Circular Dependency Prevention

```python
# Use string references for forward declarations
class League(Base):
    parent_league = relationship(
        'League',  # String reference
        remote_side=[league_id],
        backref='child_leagues'
    )

# Use late binding for circular dependencies
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .team import Team  # Import only for type hints
```

### 2.4 Lazy Loading Strategies

| Strategy | Use Case | Example |
|----------|----------|---------|
| `lazy='joined'` | Small, always-needed data | Player → CurrentStatus |
| `lazy='select'` | Medium-sized, sometimes needed | Team → Division |
| `lazy='dynamic'` | Large collections | Player → BattingStats (years of data) |
| `lazy='subquery'` | Collections needed in bulk | League → Teams |
| `lazy='selectin'` | Avoid N+1 for collections | Team → Roster |
| `lazy='noload'` | Never auto-load | Archived data relationships |

## 3. Core vs Extended Models

### 3.1 Model Hierarchy

```python
# Base model with common functionality
class BaseModel:
    """Base model with common columns and methods"""
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

# Core models (high-frequency access)
class PlayerCore(BaseModel, Base):
    """Core player biographical data - cached aggressively"""
    __table_args__ = {'schema': 'public', 'extend_existing': True}

class PlayerCurrentStatus(BaseModel, Base):
    """Current season status - moderate caching"""
    pass

# Extended models (stats, calculated data)
class PlayerCareerBattingStats(BaseModel, Base):
    """Career stats - lazy loaded, cached per session"""
    pass
```

### 3.2 Composition over Inheritance

```python
# Use mixins for shared behavior
class StatsMixin:
    """Shared statistical calculations"""

    @hybrid_property
    def batting_average(self):
        if self.ab and self.ab > 0:
            return round(self.h / self.ab, 3)
        return 0.000

    @batting_average.expression
    def batting_average(cls):
        return case(
            (cls.ab > 0, func.round(cls.h * 1.0 / cls.ab, 3)),
            else_=0.000
        )

class PlayerCareerBattingStats(Base, StatsMixin):
    """Apply mixin to batting stats"""
    pass
```

### 3.3 Handling Player Stats Separation

```python
class PlayerProfile:
    """Service layer aggregator for complete player data"""

    def __init__(self, player_id: int):
        self.core = PlayerCore.query.get(player_id)
        self.status = self.core.current_status
        self._batting_stats = None
        self._pitching_stats = None

    @property
    def batting_stats(self):
        """Lazy load batting stats when needed"""
        if self._batting_stats is None:
            self._batting_stats = PlayerCareerBattingStats.query.filter_by(
                player_id=self.core.player_id
            ).all()
        return self._batting_stats

    @property
    def career_war(self):
        """Aggregate calculated property"""
        return sum(s.war for s in self.batting_stats if s.war)
```

## 4. View Model Strategy

### 4.1 Materialized View Models

```python
class LeaderboardCareerBatting(Base):
    """Read-only model for materialized view"""
    __tablename__ = 'leaderboard_career_batting'
    __table_args__ = {'info': {'is_view': True}}  # Mark as view

    player_id = Column(Integer, primary_key=True)
    # ... other columns

    # No relationships defined - use service layer for joins

    @classmethod
    def refresh(cls):
        """Refresh materialized view - called after ETL"""
        db.session.execute(
            text('REFRESH MATERIALIZED VIEW CONCURRENTLY leaderboard_career_batting')
        )
        db.session.commit()
```

### 4.2 Read-Only Enforcement

```python
class ReadOnlyMixin:
    """Prevent modifications to view models"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._lock_modifications()

    def _lock_modifications(self):
        """Make instance read-only after creation"""
        def raise_error(*args, **kwargs):
            raise RuntimeError(f"{self.__class__.__name__} is read-only")

        self.__setattr__ = raise_error
        self.__delattr__ = raise_error

class LeaderboardView(ReadOnlyMixin, Base):
    """All leaderboard views are read-only"""
    __abstract__ = True
```

## 5. Indexing and Performance

### 5.1 SQLAlchemy-Level Indexes

```python
class PlayerCareerBattingStats(Base):
    __tablename__ = 'players_career_batting_stats'

    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_player_year_team', 'player_id', 'year', 'team_id'),
        Index('idx_year_war', 'year', 'war', postgresql_using='btree'),
        Index('idx_batting_avg', 'batting_average',
              postgresql_where=text('ab >= 300')),  # Partial index
    )
```

### 5.2 Relationship Loading Optimization

```python
# Query optimization with options
def get_team_with_roster(team_id: int):
    return Team.query.options(
        selectinload(Team.players),  # Avoid N+1
        joinedload(Team.league),      # Join in single query
        defer(Team.logo_data),        # Don't load heavy columns
        undefer(Team.name)            # But do load this deferred column
    ).get(team_id)

# Subquery loading for aggregates
def get_players_with_stats():
    subq = db.session.query(
        PlayerCareerBattingStats.player_id,
        func.sum(PlayerCareerBattingStats.hr).label('career_hr')
    ).group_by(PlayerCareerBattingStats.player_id).subquery()

    return db.session.query(PlayerCore, subq.c.career_hr).join(
        subq, PlayerCore.player_id == subq.c.player_id
    ).all()
```

## 6. Specific Challenge Solutions

### 6.1 Composite Keys

```python
class TeamRoster(Base):
    """Handle composite primary key"""
    __tablename__ = 'team_roster'

    team_id = Column(Integer, ForeignKey('teams.team_id'), primary_key=True)
    player_id = Column(Integer, ForeignKey('players_core.player_id'), primary_key=True)
    position = Column(SmallInteger)
    jersey_number = Column(SmallInteger)

    # Relationships
    team = relationship('Team', back_populates='roster_entries')
    player = relationship('PlayerCore', back_populates='team_entries')

    # Composite unique constraint
    __table_args__ = (
        UniqueConstraint('team_id', 'jersey_number', name='uq_team_jersey'),
    )
```

### 6.2 Newspaper Embedded References

```python
class NewspaperArticle(Base):
    """Handle text with embedded references"""
    __tablename__ = 'newspaper_articles'

    content = Column(Text)

    @property
    def parsed_content(self):
        """Parse embedded references in content"""
        import re
        pattern = r'\[player:(\d+)\]'

        def replace_ref(match):
            player_id = match.group(1)
            player = PlayerCore.query.get(player_id)
            if player:
                return f'<a href="/players/{player_id}">{player.full_name}</a>'
            return match.group(0)

        return re.sub(pattern, replace_ref, self.content)

    # Many-to-many tags
    player_tags = relationship(
        'PlayerCore',
        secondary='article_player_tags',
        lazy='selectin'  # Load tags with article
    )
```

### 6.3 League Constants Tables

```python
class LeagueConstants(Base):
    """Model for calculation constants - read frequently, write rarely"""
    __tablename__ = 'league_constants'
    __table_args__ = {'info': {'cache_ttl': 3600}}  # Cache for 1 hour

    league_id = Column(Integer, primary_key=True)
    year = Column(SmallInteger, primary_key=True)
    woba_weights = Column(JSON)  # Store as JSON

    @classmethod
    def get_for_calculation(cls, league_id: int, year: int):
        """Cached getter for calculations"""
        cache_key = f'constants:{league_id}:{year}'
        result = cache.get(cache_key)
        if not result:
            result = cls.query.filter_by(
                league_id=league_id, year=year
            ).first()
            cache.set(cache_key, result, timeout=3600)
        return result
```

## 7. Base Model Implementation

```python
# base.py
from sqlalchemy import Column, DateTime, Integer, event
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import Session
from datetime import datetime

Base = declarative_base()

class TimestampMixin:
    """Automatic timestamp management"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CacheableMixin:
    """Caching support for models"""

    @classmethod
    def cache_key(cls, **kwargs):
        """Generate cache key from kwargs"""
        return f"{cls.__tablename__}:{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"

    @classmethod
    def get_cached(cls, **kwargs):
        """Get with caching"""
        from app.extensions import cache
        key = cls.cache_key(**kwargs)
        result = cache.get(key)
        if result is None:
            result = cls.query.filter_by(**kwargs).first()
            cache.set(key, result, timeout=300)
        return result

class BaseModel(TimestampMixin, CacheableMixin):
    """Base model with all common functionality"""

    @declared_attr
    def __tablename__(cls):
        """Auto-generate table name from class name"""
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

    def to_dict(self):
        """Convert model to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        """Default representation"""
        return f"<{self.__class__.__name__} {self.to_dict()}>"
```

## 8. Key Architectural Patterns

### 8.1 Service Layer Pattern

```python
# services/player_service.py
class PlayerService:
    """Encapsulate complex player queries and operations"""

    @staticmethod
    def get_player_profile(player_id: int):
        """Get complete player profile with stats"""
        player = PlayerCore.query.options(
            joinedload(PlayerCore.current_status),
            selectinload(PlayerCore.images)
        ).get_or_404(player_id)

        batting_stats = PlayerCareerBattingStats.query.filter_by(
            player_id=player_id
        ).order_by(PlayerCareerBattingStats.year.desc()).all()

        return {
            'player': player,
            'stats': batting_stats,
            'career_totals': PlayerService._calculate_career_totals(batting_stats)
        }

    @staticmethod
    def search_players(query: str, limit: int = 10):
        """Full-text search with caching"""
        cache_key = f'player_search:{query}:{limit}'
        result = cache.get(cache_key)
        if not result:
            result = PlayerCore.query.filter(
                func.to_tsvector('english', PlayerCore.first_name + ' ' + PlayerCore.last_name)
                .match(query)
            ).limit(limit).all()
            cache.set(cache_key, result, timeout=300)
        return result
```

### 8.2 Query Builder Pattern

```python
class LeaderboardQueryBuilder:
    """Build complex leaderboard queries"""

    def __init__(self, model):
        self.model = model
        self.query = model.query
        self.filters = []

    def filter_active(self, active_only: bool = False):
        if active_only:
            self.query = self.query.filter(self.model.is_active == True)
        return self

    def filter_year_range(self, start_year: int = None, end_year: int = None):
        if start_year:
            self.query = self.query.filter(self.model.year >= start_year)
        if end_year:
            self.query = self.query.filter(self.model.year <= end_year)
        return self

    def order_by_stat(self, stat: str, descending: bool = True):
        column = getattr(self.model, stat)
        self.query = self.query.order_by(column.desc() if descending else column)
        return self

    def paginate(self, page: int, per_page: int = 50):
        return self.query.paginate(page=page, per_page=per_page)
```

## 9. Anti-Patterns to Avoid

### 9.1 Common Pitfalls

**❌ Don't: Load entire relationships unnecessarily**
```python
# Bad - loads all stats for all players
players = Player.query.all()
for player in players:
    total_hr = sum(stat.hr for stat in player.batting_stats)
```

**✅ Do: Use aggregation queries**
```python
# Good - single query with aggregation
result = db.session.query(
    PlayerCore.player_id,
    func.sum(PlayerCareerBattingStats.hr).label('total_hr')
).join(PlayerCareerBattingStats).group_by(PlayerCore.player_id).all()
```

**❌ Don't: Mix business logic in models**
```python
# Bad - business logic in model
class Player(Base):
    def calculate_contract_value(self):
        # Complex business logic here
        pass
```

**✅ Do: Use service layer**
```python
# Good - business logic in service
class ContractService:
    def calculate_player_value(self, player: Player):
        # Complex business logic here
        pass
```

**❌ Don't: Circular imports**
```python
# Bad - circular dependency
# In player.py
from .team import Team

# In team.py
from .player import Player
```

**✅ Do: Use string references or TYPE_CHECKING**
```python
# Good - avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .team import Team

class Player(Base):
    team = relationship('Team')  # String reference
```

## 10. Example Implementations

### 10.1 Player Model

```python
# models/core/player.py
from sqlalchemy import Column, Integer, String, Date, SmallInteger, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property
from app.models.base import Base, BaseModel

class PlayerCore(BaseModel, Base):
    __tablename__ = 'players_core'

    # Primary key
    player_id = Column(Integer, primary_key=True)

    # Basic info
    first_name = Column(String(50))
    last_name = Column(String(50))
    nick_name = Column(String(50))
    date_of_birth = Column(Date)

    # Foreign keys
    city_of_birth_id = Column(Integer, ForeignKey('cities.city_id'))
    nation_id = Column(Integer, ForeignKey('nations.nation_id'))

    # Physical attributes
    height = Column(SmallInteger)  # in inches
    weight = Column(SmallInteger)  # in pounds
    bats = Column(SmallInteger)  # 1=R, 2=L, 3=S
    throws = Column(SmallInteger)  # 1=R, 2=L

    # Relationships
    current_status = relationship(
        'PlayerCurrentStatus',
        back_populates='player',
        uselist=False,
        lazy='joined'  # Always load status
    )

    batting_stats = relationship(
        'PlayerCareerBattingStats',
        back_populates='player',
        lazy='dynamic',  # Query interface for large collection
        order_by='PlayerCareerBattingStats.year.desc()'
    )

    images = relationship(
        'PersonImage',
        primaryjoin="and_(PlayerCore.player_id==PersonImage.person_id, "
                   "PersonImage.person_type=='player')",
        viewonly=True,
        lazy='select'
    )

    # Hybrid properties
    @hybrid_property
    def full_name(self):
        if self.nick_name:
            return f"{self.first_name} '{self.nick_name}' {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    @hybrid_property
    def age(self):
        from datetime import date
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) <
                (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

    @property
    def height_display(self):
        """Format height as feet'inches"""
        if self.height:
            feet = self.height // 12
            inches = self.height % 12
            return f"{feet}'{inches}\""
        return None

    @property
    def is_active(self):
        """Check if player is currently active"""
        return self.current_status and not self.current_status.retired

    def career_stats_summary(self):
        """Get career totals - cached"""
        cache_key = f'player_career:{self.player_id}'
        from app.extensions import cache

        result = cache.get(cache_key)
        if not result:
            stats = self.batting_stats.with_entities(
                func.sum(PlayerCareerBattingStats.g).label('games'),
                func.sum(PlayerCareerBattingStats.ab).label('at_bats'),
                func.sum(PlayerCareerBattingStats.h).label('hits'),
                func.sum(PlayerCareerBattingStats.hr).label('home_runs'),
                func.sum(PlayerCareerBattingStats.rbi).label('rbis'),
                func.sum(PlayerCareerBattingStats.war).label('war')
            ).first()
            result = stats._asdict() if stats else {}
            cache.set(cache_key, result, timeout=3600)

        return result
```

### 10.2 Team Model

```python
# models/core/team.py
from sqlalchemy import Column, Integer, String, SmallInteger, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, BaseModel

class Team(BaseModel, Base):
    __tablename__ = 'teams'

    team_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    abbr = Column(String(10))
    nickname = Column(String(50))
    logo_file_name = Column(String(200))

    # Foreign keys
    city_id = Column(Integer, ForeignKey('cities.city_id'))
    park_id = Column(Integer, ForeignKey('parks.park_id'))
    league_id = Column(Integer, ForeignKey('leagues.league_id'))
    parent_team_id = Column(Integer, ForeignKey('teams.team_id'))

    # Relationships
    league = relationship('League', back_populates='teams', lazy='select')
    city = relationship('City', lazy='joined')
    park = relationship('Park', lazy='select')

    # Self-referential relationship
    parent_team = relationship(
        'Team',
        remote_side=[team_id],
        backref='affiliates'
    )

    # Players through roster
    current_roster = relationship(
        'TeamRoster',
        back_populates='team',
        lazy='dynamic',
        primaryjoin="and_(Team.team_id==TeamRoster.team_id, "
                   "TeamRoster.season_year==extract('year', func.current_date()))"
    )

    # Current record
    record = relationship(
        'TeamRecord',
        uselist=False,
        lazy='select',
        back_populates='team'
    )

    @property
    def full_name(self):
        """Get full team name"""
        return f"{self.name} {self.nickname}" if self.nickname else self.name

    @property
    def current_players(self):
        """Get current roster players"""
        return [roster.player for roster in self.current_roster]

    def get_season_stats(self, year: int):
        """Get team stats for a specific year"""
        from app.models.history import TeamHistoryBattingStats, TeamHistoryPitchingStats

        batting = TeamHistoryBattingStats.query.filter_by(
            team_id=self.team_id,
            year=year
        ).first()

        pitching = TeamHistoryPitchingStats.query.filter_by(
            team_id=self.team_id,
            year=year
        ).first()

        return {'batting': batting, 'pitching': pitching}
```

### 10.3 Leaderboard View Model

```python
# models/views/leaderboards.py
from sqlalchemy import Column, Integer, String, SmallInteger, Numeric, Boolean
from app.models.base import Base

class LeaderboardCareerBatting(Base):
    """Read-only model for career batting leaderboard materialized view"""
    __tablename__ = 'leaderboard_career_batting'
    __table_args__ = {
        'info': {'is_view': True},
        'extend_existing': True
    }

    # Primary key
    player_id = Column(Integer, primary_key=True)

    # Player info
    first_name = Column(String(50))
    last_name = Column(String(50))

    # Aggregate stats
    seasons = Column(Integer)
    g = Column(Integer)
    pa = Column(Integer)
    ab = Column(Integer)
    h = Column(Integer)
    hr = Column(Integer)
    rbi = Column(Integer)
    sb = Column(Integer)

    # Calculated stats
    avg = Column(Numeric(4, 3))
    obp = Column(Numeric(4, 3))
    slg = Column(Numeric(4, 3))
    war = Column(Numeric(8, 3))

    # Status
    is_active = Column(Boolean)

    # No relationships - join manually when needed

    @property
    def full_name(self):
        """Format name with active indicator"""
        name = f"{self.first_name} {self.last_name}"
        return f"{name}*" if self.is_active else name

    @classmethod
    def top_by_stat(cls, stat: str, limit: int = 10, active_only: bool = False):
        """Get top players by a specific stat"""
        query = cls.query
        if active_only:
            query = query.filter(cls.is_active == True)

        stat_column = getattr(cls, stat)
        return query.order_by(stat_column.desc()).limit(limit).all()

    @classmethod
    def refresh(cls):
        """Refresh the materialized view"""
        from app.extensions import db
        db.session.execute(
            text('REFRESH MATERIALIZED VIEW CONCURRENTLY leaderboard_career_batting')
        )
        db.session.commit()

    def __setattr__(self, key, value):
        """Prevent modifications to view data"""
        if hasattr(self, '_sa_instance_state'):
            raise RuntimeError(f"Cannot modify read-only view {self.__class__.__name__}")
        super().__setattr__(key, value)
```

## 11. Migration Strategy

### Phase 1: Core Models (Week 1)
1. Implement base.py with mixins
2. Create core models (Player, Team, League)
3. Test relationships and basic queries
4. Validate against existing data

### Phase 2: Statistics Models (Week 1-2)
1. Implement stats models with calculated properties
2. Create service layer for complex queries
3. Add caching layer
4. Performance testing with large datasets

### Phase 3: View Models (Week 2)
1. Map materialized views
2. Implement read-only protections
3. Create refresh mechanisms
4. Test leaderboard queries

### Phase 4: Content Models (Week 2-3)
1. Implement newspaper and media models
2. Handle embedded references
3. Test article tagging system
4. Validate search functionality

## 12. Testing Strategy

```python
# tests/models/test_player.py
import pytest
from app.models.core import PlayerCore

class TestPlayerModel:
    def test_player_relationships(self, db_session):
        """Test player relationship loading"""
        player = PlayerCore.query.first()
        assert player.current_status is not None  # Joined load
        assert player.batting_stats.count() > 0  # Dynamic relationship

    def test_hybrid_properties(self, db_session):
        """Test calculated properties"""
        player = PlayerCore.query.first()
        assert isinstance(player.full_name, str)
        assert player.age is None or isinstance(player.age, int)

    def test_career_stats_caching(self, db_session, cache):
        """Test stats caching"""
        player = PlayerCore.query.first()

        # First call hits database
        stats1 = player.career_stats_summary()

        # Second call uses cache
        with assert_num_queries(0):
            stats2 = player.career_stats_summary()

        assert stats1 == stats2
```

## Conclusion

This architecture provides a robust foundation for the RB2 Flask application's data layer. Key benefits include:

1. **Maintainability**: Clear organization and separation of concerns
2. **Performance**: Optimized loading strategies and caching
3. **Scalability**: Service layer pattern allows for growth
4. **Type Safety**: Clear model definitions with proper relationships
5. **Flexibility**: Mixins and composition allow for code reuse

The recommended approach balances the complexity of the database schema with the need for a maintainable and performant application. Start with the core models and progressively add complexity as needed, always keeping performance considerations in mind.