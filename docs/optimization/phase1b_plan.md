# Phase 1B: Query Profiling & Application Optimization

**Goal:** Identify and fix N+1 queries and application-level performance issues
**Target:** 30-50% performance improvement through profiling-driven optimization

---

## Step 1: Enable Query Logging & Profiling

### 1.1 Add Flask-DebugToolbar
```bash
pip install flask-debugtoolbar
```

### 1.2 Enable SQLAlchemy Query Logging
Already configured in `web/app/config.py`:
- Development: `SQLALCHEMY_ECHO = True`

### 1.3 Add Request Timing Middleware
Track time per request to identify slow routes.

---

## Step 2: Profile Critical Pages

### Priority Order (worst performers):
1. **Coach Main** (8572ms) - Slowest page
2. **Front Page** (3930ms) - Worst degradation (+24.8%)
3. **Player Detail** (4119ms) - Consistently slow

### For Each Page:
1. Count total queries executed
2. Identify N+1 patterns
3. Find cascade loading issues
4. Check for inefficient joins
5. Look for missing eager loading

---

## Step 3: Fix Application Issues

### Common Patterns to Fix:
- Replace `lazy='joined'` with proper eager loading
- Add `selectinload()` or `joinedload()` where needed
- Use `load_only()` to limit columns fetched
- Combine related queries with proper joins
- Move complex logic from templates to services

---

## Step 4: Measure & Iterate

- Re-test after each fix
- Compare to baseline (3 runs each)
- Document improvements
- Keep changes that work, revert what doesn't

---

## Step 5: Clean Up Indexes

Drop unused indexes identified in Phase 1:
- `idx_player_status_team_id`
- `idx_player_status_retired`
- `idx_team_relations_composite`
- `idx_teams_league_level`
- `idx_sub_leagues_composite`
- `idx_divisions_composite`
- `idx_team_history_composite`
- `idx_team_record_position`

Keep only the heavily-used ones.
