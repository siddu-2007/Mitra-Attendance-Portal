"""Activity Logging Service for Audit Trail."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.core.logging import logger
from app.models.activity import ActivityAction, ActivityLogModel


def log_activity(
    db: Any,
    admin_id: str,
    admin_name: str,
    action: ActivityAction,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> ActivityLogModel:
    """Record an audit trail event in Firestore activity_logs collection."""
    try:
        log_id = f"LOG_{uuid.uuid4().hex[:12].upper()}"
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = ActivityLogModel(
            logId=log_id,
            adminId=admin_id,
            adminName=admin_name,
            action=action,
            targetType=target_type,
            targetId=target_id,
            timestamp=timestamp,
            metadata=metadata or {},
        )
        db.collection("activity_logs").document(log_id).set(log_entry.model_dump())
        logger.info(f"Audit log recorded: {action} by {admin_name} ({admin_id}) on {target_type}:{target_id}")
        return log_entry
    except Exception as e:
        logger.error(f"Failed to record activity log: {e}")
        # Audit failure shouldn't crash the transaction, but is reported
        return ActivityLogModel(
            logId="error",
            adminId=admin_id,
            adminName=admin_name,
            action=action,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


def query_activity_logs(
    db: Any,
    action: Optional[str] = None,
    admin_id: Optional[str] = None,
    date: Optional[str] = None,
    target_type: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Query activity logs with multiple filter criteria and descending sort."""
    query = db.collection("activity_logs")

    if action:
        query = query.where("action", "==", action.upper())
    if admin_id:
        query = query.where("adminId", "==", admin_id)
    if target_type:
        query = query.where("targetType", "==", target_type.upper())

    docs = query.stream()
    logs = [d.to_dict() for d in docs]

    # Additional in-memory filtering for date prefix if specified
    if date:
        date_str = date.strip()
        logs = [l for l in logs if str(l.get("timestamp", "")).startswith(date_str)]

    # Sort descending by timestamp
    logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return logs[:limit]
