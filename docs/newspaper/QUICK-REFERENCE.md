# Newspaper System - Quick Reference

**Last Updated:** October 20, 2025

---

## URLs

### Admin (No Auth in Dev)
```
/newspaper/admin/drafts          - List all draft articles
/newspaper/admin/review/<id>     - Review article
/newspaper/admin/create          - Create new article
/newspaper/admin/regenerate/<id> - Regenerate article (Phase 2)
```

### Public
```
/newspaper                    - Homepage
/newspaper/article/<slug>     - Article detail
```

---

## Key Files

### Models
```
web/app/models/newspaper.py
  - Article
  - ArticleCategory
  - ArticlePlayerTag
  - ArticleTeamTag
  - ArticleGameTag
```

### Routes
```
web/app/routes/newspaper.py         - Public routes
web/app/routes/newspaper_admin.py   - Admin routes
```

### Templates
```
web/app/templates/newspaper/
  - index.html               - Homepage
  - article.html             - Article detail
  - admin/drafts.html        - Draft list
  - admin/review.html        - Review page
  - admin/regenerate.html    - Regeneration form
  - admin/create.html        - Creation form
```

### Utilities
```
web/app/utils/article_links.py
  - auto_link_content()           - Convert names to links
  - process_article_for_display() - Helper for templates
```

---

## Database Tables

```sql
newspaper_articles       - Main articles
article_categories       - Categories
article_player_tags      - Player mentions
article_team_tags        - Team mentions
article_game_tags        - Game recaps
```

---

## Article Workflow

1. **AI Generated** (Phase 2)
   - Pipeline creates article → status='draft'
   - Appears in `/admin/drafts`
   - Admin reviews → Publish/Reject/Regenerate

2. **User Written**
   - User fills form at `/admin/create`
   - Auto-publishes with status='published'
   - Appears immediately on `/newspaper`

3. **Display**
   - Published articles show on homepage
   - Player/team names auto-linked
   - Related articles shown

---

## Auto-Linking

**How it works:**
```python
# In article content:
"Mike Branch hit two homers as the Red Sox won."

# After auto-linking:
"<a href='/players/123'>Mike Branch</a> hit two homers as the
<a href='/teams/45'>Red Sox</a> won."
```

**Matches:**
- Full player names ("Mike Branch")
- Last names only ("Branch")
- Full team names ("Boston Red Sox")
- Team nicknames ("Red Sox")

---

## Design Colors

```css
--forest-green:       #1B4D3E  /* Primary */
--forest-green-dark:  #163D31  /* Hover */
--cream:              #F5F1E8  /* Background */
--tan:                #E8DCC4  /* Secondary */
--leather-brown:      #8B4513  /* Accents */
--vintage-gold:       #B8860B  /* Highlights */
```

---

## Common Tasks

### Create Test Article
1. Go to `/newspaper/admin/create`
2. Fill title and content
3. Search and tag players/teams
4. Submit → appears on `/newspaper`

### Review Draft
1. Go to `/newspaper/admin/drafts`
2. Click "Review"
3. Click "Publish" or "Reject"

### Regenerate Article (Future)
1. Review article
2. Click "Regenerate"
3. Add feedback
4. Submit (Phase 2 will generate new version)

---

## Authentication

**Development:** Open access (no password)

**Production:** Implement Flask-Login
- See: `docs/newspaper/AUTHENTICATION-TODO.md`
- Run: `python web/scripts/create_admin.py`

---

## Troubleshooting

### "TemplateNotFound" Error
- Check template exists in correct directory
- Restart Flask app

### Foreign Key Error
- Game model not defined - this is expected
- ForeignKey declarations removed from Article/ArticleGameTag

### Auto-linking Not Working
- Check player/team tags are saved
- Check `processed_content` passed to template
- View page source to see generated HTML

### Date Picker Shows Wrong Year
- Check `current_game_date` in context processor
- Should pull from leagues table

---

## Phase 2 Integration Points

**When Phase 2 pipeline generates articles:**

```python
# In etl/src/newspaper/pipeline.py
from etl.src.newspaper.article_processor import ArticleProcessor

processor = ArticleProcessor(connection)
article_id = processor.process_and_save(
    raw_text=llm_output,
    game_id=12345,
    generation_metadata={
        'model_used': 'qwen2.5:14b',
        'newsworthiness_score': 85
    },
    player_ids=[123, 456],
    team_ids=[10, 20]
)

# Article now appears in /newspaper/admin/drafts
```

---

## Quick Checks

**Is it working?**
```bash
# Start Flask
cd /mnt/hdd/PycharmProjects/rb2/web
python run.py

# Visit in browser
http://localhost:5001/newspaper
http://localhost:5001/newspaper/admin/drafts
http://localhost:5001/newspaper/admin/create
```

**Create test article:**
1. Title: "Branch Homers Twice in Victory"
2. Content: "Mike Branch hit two home runs as Boston defeated Cleveland 5-3."
3. Tag: Mike Branch (player)
4. Tag: Boston Red Sox (team)
5. Submit
6. View on `/newspaper` → names should be links!

---

## Related Documentation

- `newspaper-implementation-plan.md` - Full plan
- `design-system.md` - Design specifications
- `AUTHENTICATION-TODO.md` - Auth setup guide
- `PHASE3-COMPLETION-SUMMARY.md` - What we built today

---

**Questions?** Check the implementation plan or completion summary.
