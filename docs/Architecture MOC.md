---
tags: [moc, architecture]
created: 2025-10-19
---
# Architecture MOC

> Foundation documents, technical architecture, and infrastructure planning

## Project Foundation

### Core Documents
- [[architecture/OVERVIEW|Project Overview]] - High-level project vision and goals
- [[architecture/WEBSITE-SPECS|Website Specs]] - Original specifications and requirements
- [[architecture/WEB-IMPLEMENTATION-PLAN|Web Implementation Plan]] - Implementation strategy
- [[architecture/DATA-MODEL|Data Model]] - Foundational data model documentation

## Technical Architecture

### Database & Data Layer
- [[architecture/sqlalchemy-architecture-recommendation|SQLAlchemy Architecture]] - ORM design and patterns
- [[architecture/DATA-MODEL|Data Model]] - Schema and relationships
- [[architecture/ETL-CHANGE-DETECTION|ETL Change Detection]] - Extract, transform, load processes

### Infrastructure & Deployment
- [[architecture/staging-deployment-plan|Staging Deployment Plan]] - Deployment strategy and environments
- [[architecture/CODE-PROMOTION|Code Promotion Strategy]] - How code moves through environments

## System Design

### Architecture Patterns
*Review your architecture docs and add cross-references as patterns emerge*

### Integration Points
- Reference site and newspaper sections share the data model
- Common infrastructure and deployment strategy

## Related Areas

- [[Reference Site MOC]] - Reference site implementation
- [[Newspaper MOC]] - Newspaper site implementation
- [[Optimization MOC]] - Performance optimization work

## Quick Reference

**Key Technologies:**
- SQLAlchemy (ORM)
- PostgreSQL (assumed from data model docs)
- [Add other key technologies as you document them]

**Environments:**
- Development
- Staging (see deployment plan)
- Production

---

[[README|← Back to Home]]