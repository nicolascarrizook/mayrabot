"""
Motor 2: Control/follow-up modifications
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, List
import logging
from datetime import datetime
import uuid

from api.models.patient import ControlData
from api.services.chromadb_service import ChromaDBService
from api.services.plan_adjuster import PlanAdjusterService
from api.services.pdf_generator import PDFGeneratorService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_chromadb_service() -> ChromaDBService:
    """Dependency to get ChromaDB service"""
    return ChromaDBService()


@router.post("/adjust-plan")
async def adjust_existing_plan(
    control_data: ControlData,
    background_tasks: BackgroundTasks,
    chromadb: ChromaDBService = Depends(get_chromadb_service)
) -> Dict[str, Any]:
    """
    Adjust an existing nutrition plan based on patient progress
    
    This endpoint implements Motor 2: Modifications for follow-up consultations
    """
    try:
        # Generate unique adjustment ID
        adjustment_id = f"adj_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d')}"
        
        logger.info(f"Starting plan adjustment for patient: {control_data.patient_data.name}")
        
        # Analyze progress
        progress_analysis = analyze_progress(control_data)
        
        # Initialize services
        plan_adjuster = PlanAdjusterService(chromadb)
        pdf_generator = PDFGeneratorService()
        
        # Generate adjusted plan
        adjusted_plan = await plan_adjuster.adjust_plan(
            control_data,
            progress_analysis
        )
        
        # Generate PDF in background
        background_tasks.add_task(
            pdf_generator.generate_adjusted_pdf,
            adjustment_id,
            control_data,
            adjusted_plan,
            progress_analysis
        )
        
        return {
            "status": "success",
            "adjustment_id": adjustment_id,
            "patient_name": control_data.patient_data.name,
            "progress_analysis": progress_analysis,
            "adjustments_made": adjusted_plan.adjustments_summary,
            "new_daily_calories": adjusted_plan.total_daily_calories,
            "pdf_status": "generating",
            "pdf_path": f"/api/v1/motor2/adjustment/{adjustment_id}/pdf",
            "recommendations": generate_recommendations(control_data, progress_analysis)
        }
        
    except Exception as e:
        logger.error(f"Error adjusting plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adjusting plan: {str(e)}")


@router.post("/analyze-progress")
async def analyze_patient_progress(control_data: ControlData) -> Dict[str, Any]:
    """
    Analyze patient progress without generating a new plan
    
    Useful for quick consultations and progress checks
    """
    try:
        progress_analysis = analyze_progress(control_data)
        recommendations = generate_recommendations(control_data, progress_analysis)
        
        return {
            "status": "success",
            "patient_name": control_data.patient_data.name,
            "days_on_plan": control_data.days_on_plan,
            "progress_analysis": progress_analysis,
            "recommendations": recommendations,
            "next_control": calculate_next_control_date(control_data, progress_analysis)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing progress: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing progress: {str(e)}")


def analyze_progress(control_data: ControlData) -> Dict[str, Any]:
    """Analyze patient progress and determine necessary adjustments"""
    
    # Calculate weight progress
    weight_change_per_week = (control_data.weight_change / control_data.days_on_plan) * 7
    
    # Determine progress status
    if control_data.weight_change < 0:  # Weight loss
        if weight_change_per_week < -1:
            progress_status = "rapid_loss"
            status_message = "Weight loss is too rapid"
        elif weight_change_per_week < -0.5:
            progress_status = "good_loss"
            status_message = "Weight loss is on track"
        else:
            progress_status = "slow_loss"
            status_message = "Weight loss is slower than expected"
    elif control_data.weight_change > 0:  # Weight gain
        if weight_change_per_week > 0.5:
            progress_status = "rapid_gain"
            status_message = "Weight gain is too rapid"
        else:
            progress_status = "moderate_gain"
            status_message = "Slight weight gain observed"
    else:
        progress_status = "stable"
        status_message = "Weight is stable"
    
    # Analyze adherence
    if control_data.adherence_percentage >= 90:
        adherence_status = "excellent"
    elif control_data.adherence_percentage >= 70:
        adherence_status = "good"
    elif control_data.adherence_percentage >= 50:
        adherence_status = "moderate"
    else:
        adherence_status = "poor"
    
    return {
        "weight_change": control_data.weight_change,
        "weight_change_percentage": control_data.weight_change_percentage,
        "weight_change_per_week": round(weight_change_per_week, 2),
        "progress_status": progress_status,
        "status_message": status_message,
        "adherence_status": adherence_status,
        "adherence_percentage": control_data.adherence_percentage,
        "current_bmi": calculate_current_bmi(control_data),
        "issues_reported": len(control_data.reported_issues) > 0,
        "changes_requested": len(control_data.requested_changes) > 0
    }


def generate_recommendations(
    control_data: ControlData,
    progress_analysis: Dict[str, Any]
) -> List[str]:
    """Generate recommendations based on progress analysis"""
    
    recommendations = []
    
    # Weight-based recommendations
    if progress_analysis["progress_status"] == "rapid_loss":
        recommendations.append("Increase caloric intake by 200-300 kcal/day")
        recommendations.append("Ensure adequate protein intake to preserve muscle mass")
    elif progress_analysis["progress_status"] == "slow_loss":
        recommendations.append("Review portion sizes and ensure accurate tracking")
        recommendations.append("Consider increasing physical activity")
    elif progress_analysis["progress_status"] == "rapid_gain":
        recommendations.append("Reduce caloric intake by 200-300 kcal/day")
        recommendations.append("Focus on nutrient-dense, lower-calorie foods")
    
    # Adherence-based recommendations
    if progress_analysis["adherence_status"] == "poor":
        recommendations.append("Simplify meal preparation with batch cooking")
        recommendations.append("Consider meal prep services or simpler recipes")
    elif progress_analysis["adherence_status"] == "moderate":
        recommendations.append("Identify specific challenges with plan adherence")
        recommendations.append("Consider flexibility in meal timing or choices")
    
    # Issue-based recommendations
    if control_data.reported_issues:
        if "hunger" in str(control_data.reported_issues).lower():
            recommendations.append("Increase fiber and protein content in meals")
            recommendations.append("Add healthy snacks between meals")
        if "fatigue" in str(control_data.reported_issues).lower():
            recommendations.append("Ensure adequate iron and B-vitamin intake")
            recommendations.append("Review meal timing for energy optimization")
    
    # Medical updates
    if control_data.new_pathologies:
        recommendations.append("Adjust plan for new medical conditions")
        recommendations.append("Consult with medical team for specific restrictions")
    
    return recommendations


def calculate_current_bmi(control_data: ControlData) -> float:
    """Calculate current BMI with updated weight"""
    height_m = control_data.patient_data.height / 100
    return round(control_data.current_weight / (height_m ** 2), 2)


def calculate_next_control_date(
    control_data: ControlData,
    progress_analysis: Dict[str, Any]
) -> str:
    """Suggest next control date based on progress"""
    
    # Determine follow-up frequency
    if progress_analysis["progress_status"] in ["rapid_loss", "rapid_gain"]:
        days_until_next = 7  # Weekly follow-up
    elif progress_analysis["adherence_status"] == "poor":
        days_until_next = 10  # More frequent support
    elif control_data.new_pathologies or control_data.new_medications:
        days_until_next = 14  # Bi-weekly for medical changes
    else:
        days_until_next = 21  # Standard 3-week follow-up
    
    return f"Recommended in {days_until_next} days"