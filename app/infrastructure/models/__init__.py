"""SQLAlchemy ORM models.

Import every model module here so that ``Base.metadata`` is populated
when ``DatabaseManager.create_all()`` or Alembic autogenerate runs.

Adding a new model:
  1. Create the module (e.g. ``analysis_session.py``).
  2. Define the class inheriting from ``Base`` and ``TimestampMixin``.
  3. Import it in this file (the import itself registers metadata).
"""

from app.infrastructure.models.analysis_session import AnalysisSession
from app.infrastructure.models.audit_log import AuditLog

__all__ = [
    "AnalysisSession",
    "AuditLog",
]
