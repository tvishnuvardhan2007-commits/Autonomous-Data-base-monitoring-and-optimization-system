"""Conservative optimization workflow. This module never executes arbitrary SQL."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any

@dataclass(frozen=True)
class OptimizationProposal:
    id: str
    target_id: str
    title: str
    rationale: str
    sql_preview: str
    risk: str = "medium"
    requires_approval: bool = True
    status: str = "PROPOSED"

def propose_index(target_id: str, table: str, column: str, evidence: str) -> OptimizationProposal:
    """Generate a review-only PostgreSQL index proposal from simple identifiers."""
    ident = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")
    if not ident.fullmatch(table) or not ident.fullmatch(column):
        raise ValueError("Table and column must be simple SQL identifiers.")
    index_name = f"idx_{table}_{column}"[:63]
    # Quoting simple validated identifiers is still required; no user SQL is accepted.
    sql = f'CREATE INDEX CONCURRENTLY IF NOT EXISTS "{index_name}" ON "{table}" ("{column}");'
    return OptimizationProposal(
        id=f"idx-{target_id}-{table}-{column}", target_id=target_id,
        title=f"Review index on {table}.{column}",
        rationale=f"Candidate derived from supplied evidence: {evidence[:300]}",
        sql_preview=sql, risk="medium", requires_approval=True, status="PROPOSED",
    )

def approve_proposal(proposal: OptimizationProposal, actor: str, authorized: bool) -> dict[str, Any]:
    """Approval changes workflow status only. SQL execution is intentionally not provided."""
    if not authorized:
        raise PermissionError("An authorized operator must approve this proposal.")
    return {
        "proposal_id": proposal.id, "status": "APPROVED_FOR_MANUAL_EXECUTION",
        "approved_by": actor, "approved_at": datetime.now(timezone.utc).isoformat(),
        "sql_preview": proposal.sql_preview,
        "executed": False,
        "message": "Approval recorded only. Execute manually after staging validation and a rollback plan.",
    }
