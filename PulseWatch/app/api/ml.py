from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.utils.security import verify_api_key
from app.schemas import EvaluationMetricResponse
from app.services.evaluation_service import EvaluationService
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/ml", tags=["ml", "evaluation"])


@router.post("/evaluation/{metric_name}", response_model=EvaluationMetricResponse)
async def evaluate_metric(
    metric_name: str,
    period_hours: int = 24,
    confidence_threshold: float = 0.5,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> EvaluationMetricResponse:
    """
    Evaluate anomaly detection performance for a metric.
    
    Uses detected anomalies with high confidence as ground truth.
    Calculates precision, recall, F1-score, and confusion matrix.
    """

    try:
        evaluation_service = EvaluationService(db)
        eval_metric = evaluation_service.evaluate_metric(
            metric_name=metric_name,
            period_hours=period_hours,
            confidence_threshold=confidence_threshold,
        )

        if not eval_metric:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient data to evaluate metric: {metric_name}",
            )

        return EvaluationMetricResponse.from_db_model(eval_metric)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating metric: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to evaluate metric",
        )


@router.get("/evaluation/{metric_name}", response_model=list[EvaluationMetricResponse])
async def get_evaluation_history(
    metric_name: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> list[EvaluationMetricResponse]:
    """Get evaluation history for a metric"""

    try:
        evaluation_service = EvaluationService(db)
        eval_metrics = evaluation_service.get_evaluation_history(
            metric_name=metric_name,
            limit=limit,
        )

        return [EvaluationMetricResponse.from_db_model(em) for em in eval_metrics]

    except Exception as e:
        logger.error(f"Error getting evaluation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch evaluation history",
        )


@router.get("/evaluation/{metric_name}/latest", response_model=Optional[EvaluationMetricResponse])
async def get_latest_evaluation(
    metric_name: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> Optional[EvaluationMetricResponse]:
    """Get latest evaluation for a metric"""

    try:
        evaluation_service = EvaluationService(db)
        eval_metric = evaluation_service.get_latest_evaluation(metric_name=metric_name)

        return EvaluationMetricResponse.from_db_model(eval_metric) if eval_metric else None

    except Exception as e:
        logger.error(f"Error getting latest evaluation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch latest evaluation",
        )


@router.get("/health", response_model=dict)
async def ml_health():
    """ML pipeline health check"""
    return {
        "status": "healthy",
        "detectors": ["isolation_forest", "zscore"],
        "models": "initialized",
    }
