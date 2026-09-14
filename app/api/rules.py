from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.database import get_db
from app.utils.security import verify_api_key

router = APIRouter(
    prefix="/api/v1/rules",
    tags=["rules"],
    dependencies=[Depends(verify_api_key)],
)

@router.get("/", response_model=list[schemas.Rule])
def read_rules(db: Session = Depends(get_db)):
    # No pagination as per design; return all rules
    return crud.rule.get_multi(db)

@router.post("/", response_model=schemas.Rule, status_code=status.HTTP_201_CREATED)
def create_rule(rule_in: schemas.RuleCreate, db: Session = Depends(get_db)):
    return crud.rule.create(db, obj_in=rule_in)

@router.patch("/{rule_id}", response_model=schemas.Rule)
def update_rule(rule_id: str, rule_in: schemas.RuleUpdate, db: Session = Depends(get_db)):
    db_rule = crud.rule.get(db, id=rule_id)
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return crud.rule.update(db, db_obj=db_rule, obj_in=rule_in)

@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(rule_id: str, db: Session = Depends(get_db)):
    db_rule = crud.rule.get(db, id=rule_id)
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    crud.rule.remove(db, id=rule_id)
    return None
