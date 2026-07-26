"""Compatibility import for the storage-owned lead repository.

New code should import from ``backend.storage.repositories``. Existing sales
assistant imports remain supported to avoid a breaking migration.
"""

from backend.storage.repositories.lead_repository import LeadRepository, SavedLead

__all__ = ["LeadRepository", "SavedLead"]
