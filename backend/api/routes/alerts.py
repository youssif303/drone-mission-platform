from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.database.db import get_db
from backend.models.alert import AlertDB, AlertRuleDB, AlertResponse, AlertRuleCreate, AlertRuleResponse

router = APIRouter(prefix="", tags=["Alerts"])

@router.get("/alerts", response_model=List[AlertResponse])
async def list_alerts(severity: Optional[str] = None, alert_type: Optional[str] = None, limit: int = 50, db: AsyncSession = Depends(get_db)):
    query = select(AlertDB)
    if severity:
        query = query.filter(AlertDB.severity == severity)
    if alert_type:
        query = query.filter(AlertDB.alert_type == alert_type)
        
    query = query.order_by(desc(AlertDB.timestamp)).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/alert-rules", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(rule: AlertRuleCreate, db: AsyncSession = Depends(get_db)):
    db_rule = AlertRuleDB(**rule.model_dump())
    db.add(db_rule)
    await db.commit()
    await db.refresh(db_rule)
    return db_rule

@router.get("/alert-rules", response_model=List[AlertRuleResponse])
async def list_alert_rules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AlertRuleDB))
    return result.scalars().all()

@router.put("/alert-rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(rule_id: int, rule_update: AlertRuleCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AlertRuleDB).filter(AlertRuleDB.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    for key, value in rule_update.model_dump().items():
        setattr(rule, key, value)
        
    await db.commit()
    await db.refresh(rule)
    return rule

@router.delete("/alert-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AlertRuleDB).filter(AlertRuleDB.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    await db.delete(rule)
    await db.commit()
