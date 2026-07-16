# Database

PRism uses PostgreSQL with SQLAlchemy ORM and Alembic for migrations.

## Tables
- `reviews`: Stores high-level PR review summaries and scores.
- `issues`: Stores individual findings (Security, Quality, Logic) associated with a review.
- `users`: Stores admin credentials for the Recruiter Dashboard.

## Migrations
```bash
alembic revision --autogenerate -m "Migration message"
alembic upgrade head
```
