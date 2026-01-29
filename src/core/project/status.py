from datetime import datetime, timedelta, timezone
from typing import Tuple
from core.domain.project import Project

class ProjectStatus:
    """Project Status Calculator Business Logic."""
    
    STALE_THRESHOLD_DAYS = 30

    @staticmethod
    def calculate_staleness(project: Project) -> Tuple[bool, int]:
        """
        Calculate if a project is stale based on last_modified_at.
        
        Args:
            project: Project entity
            
        Returns:
            Tuple[bool, int]: (is_stale, days_inactive)
        """
        # Determine base date (prefer last_modified, fallback to created_at, then now)
        base_date = project.last_modified_at or project.created_at
        
        if not base_date:
            base_date = datetime.now(timezone.utc)

        # Enforce timezone awareness (assume UTC if naive)
        if base_date.tzinfo is None:
            base_date = base_date.replace(tzinfo=timezone.utc)
            
        # Compare with current UTC time
        now = datetime.now(timezone.utc)
        delta = now - base_date
        days_inactive = max(0, delta.days)
        
        is_stale = days_inactive >= ProjectStatus.STALE_THRESHOLD_DAYS
        
        return is_stale, days_inactive
