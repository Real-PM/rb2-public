# Branch Baseball - Design System Documentation

## Overview

This design system establishes a cohesive visual identity for the Branch Baseball universe, encompassing both the **Branch Baseball Encyclopedia** (reference site) and the upcoming **Branch Baseball Newspaper** site. The design philosophy embraces classic baseball aesthetics with a minimalist, readable approach.

---

## Brand Identity

### Project Names

- **Branch Baseball Encyclopedia** - The comprehensive reference site
  - Home to player stats, team records, leaderboards, and historical data
  - Clean, data-focused, encyclopedia-style presentation

- **Branch Baseball Newspaper** - The narrative companion site
  - AI-generated game articles and Branch family stories
  - Vintage newspaper aesthetic with modern readability
  - More visual storytelling, less spare than Encyclopedia

### Logo

**Design**: Crossed baseball bats with baseball
- SVG location: `/web/app/static/images/logo.svg`
- Simple, iconic design works at any size
- Baseball with vintage stitching detail
- Leather brown bats with darker knobs

**Typography**:
- Logo text uses **Bebas Neue** (sans-serif, condensed)
- "BRANCH BASEBALL" in all caps with letter-spacing
- "ENCYCLOPEDIA" subtitle in smaller text
- Art Deco influence: clean, geometric, readable

---

## Color Palette

### Primary Colors

```css
--forest-green:       #1B4D3E   /* Primary navigation, headers */
--forest-green-dark:  #163D31   /* Hover states, deeper accents */
--forest-green-light: #2A6B54   /* Lighter accents, secondary elements */
```

**Usage**: Primary brand color inspired by classic baseball field green. Use for:
- Navigation bars
- Primary headings
- League/division headers
- CTAs and important links

### Secondary Colors

```css
--cream:              #F5F1E8   /* Page background, light text */
--tan:                #E8DCC4   /* Card borders, hover backgrounds */
```

**Usage**: Neutral, warm backgrounds that evoke vintage paper:
- Main page background (cream)
- Card/section backgrounds (white with tan borders)
- Hover states on list items
- Secondary text on dark backgrounds

### Accent Colors

```css
--leather-brown:      #8B4513   /* Borders, decorative accents */
--leather-brown-dark: #6B3410   /* Bat knobs, deeper brown */
--vintage-gold:       #B8860B   /* Hover text, special highlights */
```

**Usage**: Warm accents inspired by vintage baseball equipment:
- Border decoration (leather brown)
- Hover text color (vintage gold)
- Baseball stitching details
- Special callouts or badges

### Utility Colors

```css
--field-green:        #2D5F4A   /* Alternate green for variety */
```

---

## Typography

### Font Families

#### Display/Logo Font
```css
font-family: 'Bebas Neue', sans-serif;
```
- **Where**: Logo, large headings, sub-league names
- **Characteristics**: Condensed, all-caps friendly, athletic
- **Letter-spacing**: `0.05em` for readability

#### Serif Headings
```css
font-family: 'Playfair Display', serif;
```
- **Where**: Main page headings (`.deco-heading`)
- **Characteristics**: Art Deco influence, elegant, bold
- **Weight**: 700 (bold)
- **Use for**: H1 titles, feature article headlines

#### Body Text
```css
font-family: system-ui, sans-serif; /* Tailwind default */
```
- **Where**: All body text, tables, lists
- **Characteristics**: Readable, neutral
- **Sizes**:
  - Small: `text-xs` (0.75rem)
  - Body: `text-sm` (0.875rem), `text-base` (1rem)
  - Headings: `text-lg` (1.125rem), `text-xl` (1.25rem), `text-4xl` (2.25rem)

---

## Component Styles

### Navigation Bar

```html
<nav class="bg-forest text-cream shadow-lg">
```

**Properties**:
- Background: Forest green (`#1B4D3E`)
- Text: Cream (`#F5F1E8`)
- Height: `h-16` (4rem)
- Hover: `bg-forest-dark` + `text-vintage-gold`
- Drop shadow for depth

**Logo Display**:
- Icon: 40px × 40px (`h-10 w-10`)
- Scales up 10% on hover (`hover:scale-110`)
- Text: Two-line layout with smaller subtitle

### Cards & Sections

**Standard Card**:
```html
<div class="bg-white rounded-lg shadow-lg p-6 border-2 border-tan">
```

**Properties**:
- White background for content
- 2px tan border for warmth
- Rounded corners (`rounded-lg`)
- Generous padding (`p-6`)
- Drop shadow for elevation

**Section Headers**:
```html
<h2 class="text-xl font-bold text-forest mb-4 border-b-2 border-leather pb-2">
```

- Forest green text
- 2px leather brown bottom border
- Bottom padding + margin for spacing

### Tables

**Standings Tables**:
- Sub-league header: `bg-forest text-cream`
- Division header: `bg-tan` with `text-forest`
- Rows: Hover state with `hover:bg-gray-50`
- Borders: `border-gray-200` for subtle separation

### Links

**Primary Links**:
```css
color: var(--forest-green);
hover: var(--vintage-gold);
transition: all 0.2s ease-in-out;
```

**Navigation Links**:
- Base: Cream text
- Hover: Vintage gold text + darker background

### Buttons & Inputs

**Search Input**:
```html
<input class="bg-forest-dark text-cream placeholder-tan
              focus:ring-2 focus:ring-vintage-gold">
```

- Dark forest background
- Cream text
- Tan placeholder text
- Vintage gold focus ring

---

## Layout Patterns

### Page Background
```css
body { background-color: #F5F1E8; } /* cream */
```

### Container
```html
<div class="container mx-auto px-4 py-8">
```

### Grid Layouts

**Homepage (Two-column)**:
```html
<div class="grid grid-cols-1 lg:grid-cols-5 gap-8">
  <div class="lg:col-span-2"><!-- Sidebar --></div>
  <div class="lg:col-span-3"><!-- Main content --></div>
</div>
```

**Standings (Responsive two-column)**:
```html
<div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
```

---

## Footer Design

**Structure**: Three-column layout on desktop, stacked on mobile

**Styling**:
```html
<footer class="bg-forest-dark text-tan mt-12 border-t-4 border-leather">
```

**Sections**:
1. **About** - Project description
2. **Quick Links** - Navigation
3. **Credits** - Developer attribution + tech stack

**Properties**:
- Dark forest background
- Tan text for readability
- 4px leather border on top
- Vintage gold hover color for links

---

## Newspaper Site - Design Direction

### Visual Differences from Encyclopedia

While maintaining the same color palette and fonts, the Newspaper site will:

1. **More Visual Content**
   - Larger hero images
   - Featured article cards with thumbnails
   - Photo galleries from games
   - Pull quotes and callouts

2. **Vintage Newspaper Elements**
   - Nameplate/masthead at top
   - Column-based article layouts
   - Bylines and datelines
   - "Above the fold" content hierarchy
   - Section headers (Sports, Branch Family News, etc.)

3. **Typography Emphasis**
   - Larger, bolder headlines (Playfair Display serif)
   - Subheadings and decks
   - Drop caps on article openings
   - More varied text sizes for hierarchy

4. **Layout Patterns**
   - Multi-column article text (2-3 columns on desktop)
   - Sidebar widgets (Recent Articles, Branch Family Tree, etc.)
   - Featured story cards
   - Article list views with excerpts

### Component Ideas

**Article Card**:
```html
<div class="bg-white border-2 border-leather rounded-lg overflow-hidden shadow-lg">
  <div class="bg-tan border-b-2 border-leather px-4 py-2">
    <span class="text-xs text-forest font-bold">JUNE 15, 1969</span>
  </div>
  <div class="p-6">
    <h3 class="text-2xl font-bold text-forest deco-heading mb-2">
      BRANCH'S BURST PUMMELS CLEVELAND
    </h3>
    <p class="text-sm text-gray-700 mb-3">
      Donovan Branch smashed two home runs and drove in five runs...
    </p>
    <a href="#" class="text-vintage-gold hover:text-forest font-medium">
      Read Full Article →
    </a>
  </div>
</div>
```

**Masthead**:
```html
<header class="bg-cream border-b-4 border-leather py-8">
  <div class="text-center">
    <h1 class="text-6xl font-bold text-forest deco-heading">
      THE BRANCH BASEBALL GAZETTE
    </h1>
    <p class="text-sm text-gray-600 mt-2 tracking-widest">
      EST. 1960 | YOUR SOURCE FOR BRANCH FAMILY BASEBALL
    </p>
  </div>
</header>
```

**Article Byline**:
```html
<div class="border-t border-b border-leather py-2 my-4">
  <p class="text-xs text-gray-600">
    By <span class="font-bold">AI Sports Reporter</span> |
    June 15, 1969 | Boston, MA
  </p>
</div>
```

---

## Responsive Behavior

### Breakpoints (Tailwind defaults)
- **sm**: 640px
- **md**: 768px
- **lg**: 1024px
- **xl**: 1280px
- **2xl**: 1536px

### Mobile Considerations

**Navigation**:
- Hamburger menu below `md` breakpoint
- Full logo + text collapses to icon on mobile
- Search moves to accordion in mobile menu

**Grids**:
- Single column on mobile
- Two columns at `lg` breakpoint
- Three columns (if used) at `xl`

**Typography**:
- Scale down heading sizes on mobile
- Ensure 16px minimum for body text
- Adjust logo text to single line if needed

---

## Animation & Transitions

### Standard Transition
```css
transition: all 0.2s ease-in-out;
```

**Applied to**:
- Link hover states
- Button interactions
- Card hover effects

### Specific Animations

**Logo hover**:
```css
transition-transform group-hover:scale-110
```

**Dropdown menus**:
- Fade in/out with `hidden` class toggle
- Slight delay on mouse leave (200ms)

---

## Accessibility

### Color Contrast

All text/background combinations meet WCAG AA standards:
- Forest green text on cream background: ✓
- Cream text on forest green background: ✓
- Vintage gold used only for hover/decorative: ✓

### Focus States

All interactive elements include visible focus indicators:
```css
focus:outline-none focus:ring-2 focus:ring-vintage-gold
```

### Semantic HTML

- Use proper heading hierarchy (H1 → H2 → H3)
- Navigation wrapped in `<nav>` elements
- Main content in `<main>` tag
- Footer in `<footer>`

---

## File Structure

```
/web/app/static/
  /css/
    custom.css          # Custom styles and CSS variables
  /images/
    logo.svg            # Branch Baseball logo
  /js/
    (existing JS files)

/web/app/templates/
  base.html             # Base template with nav/footer
  index.html            # Homepage
  (other templates inherit from base.html)
```

---

## Implementation Notes

### Tailwind Configuration

Custom colors are defined inline in `base.html`:

```javascript
tailwind.config = {
  theme: {
    extend: {
      colors: {
        'forest': { DEFAULT: '#1B4D3E', dark: '#163D31', light: '#2A6B54' },
        'cream': '#F5F1E8',
        'tan': '#E8DCC4',
        'leather': { DEFAULT: '#8B4513', dark: '#6B3410' },
        'field': '#2D5F4A',
        'vintage-gold': '#B8860B',
      }
    }
  }
}
```

### Custom CSS Variables

Defined in `/web/app/static/css/custom.css`:

```css
:root {
  --forest-green: #1B4D3E;
  --forest-green-dark: #163D31;
  --forest-green-light: #2A6B54;
  --cream: #F5F1E8;
  --tan: #E8DCC4;
  --leather-brown: #8B4513;
  --leather-brown-dark: #6B3410;
  --field-green: #2D5F4A;
  --vintage-gold: #B8860B;
}
```

### Font Loading

Fonts loaded via Google Fonts CDN in `custom.css`:

```css
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Playfair+Display:wght@400;700&display=swap');
```

---

## Future Enhancements

### Phase 3 (Newspaper Site)
1. Create newspaper-specific templates
2. Implement article card components
3. Design masthead and nameplate
4. Build article detail page layout
5. Add vintage newspaper decorative elements
6. Create article list/archive views

### Potential Additions
- Dark mode variant (optional)
- Print stylesheet for articles
- Social sharing cards with branded graphics
- Animated scoreboard widget
- Interactive team logos
- Player photo overlays with stats

---

## Design Principles

1. **Minimalism with Warmth**: Clean layouts with warm, vintage-inspired colors
2. **Hierarchy through Typography**: Use font sizes and weights to guide the eye
3. **Generous Whitespace**: Don't crowd the page; let content breathe
4. **Consistent Interaction**: All links and buttons behave predictably
5. **Performance First**: Use system fonts, SVG graphics, minimal custom CSS
6. **Mobile-Friendly**: Touch targets, readable text, responsive grids
7. **Baseball Heritage**: Colors and design evoke classic ballparks and vintage sports media

---

## Contact & Maintenance

**Design System Owner**: [Your Name]
**Portfolio**: [Your Portfolio URL]
**Last Updated**: 2025-10-20
**Version**: 1.0

For design questions or suggestions, please refer to this document first. All updates should be reflected here to maintain consistency across both sites.
