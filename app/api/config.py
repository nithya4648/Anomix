from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.rule_config import RuleConfig
from app.schemas.rule_config import RuleConfigCreate, RuleConfigUpdate, RuleConfigResponse

router = APIRouter(prefix="/config/rules", tags=["Rule Config"])

@router.post("/", response_model=RuleConfigResponse)
def create_rule(rule: RuleConfigCreate, db: Session = Depends(get_db)):
    db_rule = RuleConfig(
        metric_name=rule.metric_name,
        threshold_value=rule.threshold_value,
        duration_minutes=rule.duration_minutes,
        severity=rule.severity,
        enabled=rule.enabled,
        recovery_confirmation_minutes=rule.recovery_confirmation_minutes,
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

@router.get("/", response_model=list[RuleConfigResponse])
def list_rules(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    rules = db.query(RuleConfig).offset(skip).limit(limit).all()
    return rules

@router.get("/{rule_id}", response_model=RuleConfigResponse)
def get_rule(rule_id: str, db: Session = Depends(get_db)):
    rule = db.query(RuleConfig).filter(RuleConfig.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule

@router.put("/{rule_id}", response_model=RuleConfigResponse)
def update_rule(rule_id: str, rule_update: RuleConfigUpdate, db: Session = Depends(get_db)):
    rule = db.query(RuleConfig).filter(RuleConfig.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    update_data = rule_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return rule

@router.delete("/{rule_id}", response_model=dict)
def delete_rule(rule_id: str, db: Session = Depends(get_db)):
    rule = db.query(RuleConfig).filter(RuleConfig.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
    return {"detail": "Rule deleted"}
