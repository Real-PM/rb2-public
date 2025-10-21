# RB2 - OOTP Baseball Reference Website

## Quick Start
- **What**: Flask web app + PostgreSQL - baseball statistics reference site similar to baseball-reference.com and a 
complementary newspaper-type site.
- **Main Docs**: See `docs/OVERVIEW.MD` for detailed project info, `docs/WEBSITE-SPECS.MD` for UI specs
- **Database**: PostgreSQL at 192.168.10.94:5432, database: ootp_dev, user: ootp_etl (credentials in .mcp.json)
- **Virtual Env**: ~/virtual-envs/rb2
- **Run App**: `cd web && python run.py` (dev server on localhost:5000)


## Important Documentation
- **@docs/WEBSITE-SPECS.MD** - Complete UI/UX specifications and implementation status (READ THIS FIRST for frontend work)
- **@docs/OVERVIEW.MD** - Project architecture and technical overview
- **@docs/DATA-MODEL.MD** - Database schema documentation

## Backlog & Planning Documents (Load as needed)
- `docs/backlog-active.md` - Active feature backlog (@-mention when planning new features)
- `docs/backlog-completed.md` - Completed work history (@-mention for reference/context)
- Use: Load these only during feature planning sessions, not for bug fixes or optimizations

## Project Structure

### `/web` - Flask Application
- `app/` - Main application package
  - `models/` - SQLAlchemy models (Player, Team, League stats)
  - `routes/` - Blueprint routes (players, teams, leaderboards, newspaper)
  - `services/` - Business logic layer
  - `templates/` - Jinja2 templates with Tailwind CSS
  - `static/` - CSS, JS, images
  - `utils/` - Helper functions
- `run.py` - Application entry point

### `/etl` - Data Pipeline
- `main.py` - ETL orchestration
- `src/` - ETL modules
  - `database/` - DB connection and operations
  - `loaders/` - Data loading logic
  - `transformers/` - Data transformation
  - `utils/` - ETL utilities
- `data/` - Data directories (incoming, processed, archive)
- `logs/` - ETL execution logs
- `docs/` - ETL documentation (INCREMENTAL_LOADING.MD, QUICK_START_INCREMENTAL.MD)

### `/docs` - Project Documentation
- **WEBSITE-SPECS.MD** - Detailed UI/UX specifications with implementation status
- **OVERVIEW.MD** - Project overview and architecture
- **DATA-MODEL.MD** - Database schema and relationships  
- **BACKLOG.MD** - Active feature backlog
- Performance docs, optimization strategy, phase plans

### `/scripts` - Utilities
- SQL scripts for indexes, views, calculations
- Performance measurement tools
- Image processing utilities

### `/false_start` - Legacy PHP Version (IGNORE)
Old PHP implementation - not in use

## Key Technologies
- **Backend**: Flask, SQLAlchemy
- **Frontend**: Jinja2 templates, Tailwind CSS (CDN)
- **Database**: PostgreSQL 
- **ETL**: Custom Python pipeline

## Database Quick Reference
Main tables:
- `players_core` - Player biographical data
- `players_career_batting_stats`, `players_career_pitching_stats` - Player statistics
- `teams`, `team_roster`, `team_record` - Team data
- `leagues`, `sub_leagues`, `divisions` - League structure
- `games` - Game data (for future features)
- `coaches` - Coach/staff data

Use the PostgreSQL MCP to query: just ask naturally about tables, schemas, or data!

## Common Tasks

**Start dev server:**
```bash
cd web && python run.py
```

**Run ETL:**
```bash
cd etl && python main.py
```

**Database queries:**
Just ask! The PostgreSQL MCP is connected.

**Check ETL logs:**
```bash
tail -f etl/logs/etl_$(date +%Y-%m-%d).log
```

## Development Guidelines
- UI specs are in `docs/WEBSITE-SPECS.MD` - reference for all frontend work
- Follow Flask blueprint pattern for new routes
- Use SQLAlchemy models - don't write raw SQL unless necessary
- Tailwind via CDN for styling
- Mobile-first responsive design
- All player/team links should be functional

## Current Status
- **Completed**: Player pages (list, detail), basic team pages, standings
- **In Progress**: Team year pages, leaderboards
- **Not Started**: League pages, year pages, newspaper section

See `docs/WEBSITE-SPECS.MD` for detailed feature status and implementation notes.

## Performance Notes
- Large codebase with heavy data queries
- Watch for N+1 query issues
- Consider caching for leaderboards
- See `docs/optimization-strategy.md` for performance work

## Testing Site
Use Puppeteer MCP for browser testing - curl results differ from actual browser load times!

## Architecture Note
This is a solo development project using Claude Code as primary development tool. The @architect subagent handles architectural decisions. Keep it simple - no need for elaborate workflows.