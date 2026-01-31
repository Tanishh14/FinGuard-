"""
GNN Fraud Rings - graph from real transactions only.
"""
from typing import List, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.dependencies import get_db, get_current_active_user
from app.db.models import Transaction as TransactionModel

router = APIRouter()


@router.get(
    "/clusters",
    response_model=dict,
)
async def get_gnn_clusters(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    GET /api/v1/gnn/clusters
    Build graph from real transactions only. Returns 404 if no data.
    """
    q = select(TransactionModel).where(TransactionModel.user_id == current_user.id)
    r = await db.execute(q)
    rows = r.scalars().all()

    if not rows:
        return {"nodes": [], "edges": [], "clusters": []}

    node_ids = set()
    edges: List[dict] = []
    for t in rows:
        uid = str(t.user_id) if t.user_id else None
        did = t.device_id
        mid = t.merchant_id
        if uid:
            node_ids.add(("user", uid))
        if did:
            node_ids.add(("device", did))
        if mid:
            node_ids.add(("merchant", mid))
        if uid and did:
            edges.append({"source": f"user_{uid}", "target": f"device_{did}"})
        if uid and mid:
            edges.append({"source": f"user_{uid}", "target": f"merchant_{mid}"})
    
    nodes = [
        {"id": f"{typ}_{nid}", "type": typ, "label": nid[:8] + "..." if len(str(nid)) > 8 else str(nid)}
        for (typ, nid) in node_ids
    ]
    
    # Deduplicate edges by (source, target)
    seen_edges = set()
    unique_edges = []
    for e in edges:
        key = (e["source"], e["target"])
        if key not in seen_edges:
            seen_edges.add(key)
            unique_edges.append(e)
    
    # Clusters: group by shared device or merchant (simplified from real graph)
    clusters: List[dict] = []
    by_device: dict[str, List[Any]] = {}
    by_merchant: dict[str, List[Any]] = {}
    for t in rows:
        if t.device_id:
            by_device.setdefault(t.device_id, []).append(t)
        if t.merchant_id:
            by_merchant.setdefault(t.merchant_id, []).append(t)
    
    cid = 0
    for dev, txns in by_device.items():
        if len(txns) >= 2:
            risk_avg = sum(t.risk_score or 0 for t in txns) / len(txns)
            clusters.append({
                "id": str(cid),
                "type": "user-cluster",
                "users": len(set(t.user_id for t in txns if t.user_id)),
                "devices": 1,
                "location": txns[0].location_city or txns[0].location_country or "N/A",
                "risk": round(risk_avg, 1),
            })
            cid += 1
    
    for mid, txns in by_merchant.items():
        if len(txns) >= 2:
            risk_avg = sum(t.risk_score or 0 for t in txns) / len(txns)
            clusters.append({
                "id": str(cid),
                "type": "merchant-ring",
                "merchants": 1,
                "location": txns[0].location_city or txns[0].location_country or "N/A",
                "risk": round(risk_avg, 1),
            })
            cid += 1
    
    return {"nodes": nodes, "edges": unique_edges, "clusters": clusters}
