"""User Activity Logging & Audit Trail Service."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import UserActivityLog
from app.models.employee import Employee


class ActivityService:
    """Provides structured audit logging for all employee actions across attendance, tasks, visits, and travel."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_activity(
        self,
        tenant_id: uuid.UUID,
        employee_id: uuid.UUID,
        activity_type: str,
        description: str,
        network_type: str = "OFFICE_WIFI",
        is_office_wifi: bool = True,
        ip_address: Optional[str] = None,
        location_latitude: Optional[float] = None,
        location_longitude: Optional[float] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> UserActivityLog:
        """Records an immutable activity log entry."""
        log = UserActivityLog(
            tenant_id=tenant_id,
            employee_id=employee_id,
            activity_type=activity_type,
            description=description,
            network_type=network_type,
            is_office_wifi=is_office_wifi,
            ip_address=ip_address,
            location_latitude=location_latitude,
            location_longitude=location_longitude,
            metadata_json=metadata_json or {},
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(log)
        # Also update employee's last seen telemetry if location is available
        if location_latitude is not None and location_longitude is not None:
            emp = await self.db.get(Employee, employee_id)
            if emp:
                emp.last_known_latitude = location_latitude
                emp.last_known_longitude = location_longitude
                emp.last_seen_at = datetime.now(timezone.utc)
                emp.current_network_type = network_type

        await self.db.commit()
        return log

    async def get_activity_logs(
        self,
        tenant_id: uuid.UUID,
        employee_id: Optional[uuid.UUID] = None,
        activity_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[dict]:
        """Fetches chronological activity logs for tenant admin audit."""
        stmt = (
            select(UserActivityLog, Employee)
            .join(Employee, UserActivityLog.employee_id == Employee.id)
            .where(UserActivityLog.tenant_id == tenant_id)
            .order_by(UserActivityLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if employee_id:
            stmt = stmt.where(UserActivityLog.employee_id == employee_id)
        if activity_type:
            stmt = stmt.where(UserActivityLog.activity_type == activity_type)

        rows = (await self.db.execute(stmt)).all()
        results = []
        for log, emp in rows:
            results.append({
                "id": str(log.id),
                "employee_id": str(emp.id),
                "employee_name": emp.full_name,
                "employee_code": emp.employee_code,
                "activity_type": log.activity_type,
                "description": log.description,
                "network_type": log.network_type,
                "is_office_wifi": log.is_office_wifi,
                "ip_address": log.ip_address,
                "location_latitude": log.location_latitude,
                "location_longitude": log.location_longitude,
                "metadata": log.metadata_json,
                "created_at": log.created_at.isoformat(),
                "created_at_formatted": log.created_at.strftime("%b %d, %Y • %I:%M:%S %p"),
            })
        return results
