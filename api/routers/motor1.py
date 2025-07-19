"""
Motor 1: New patient plan generation
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any
import logging
from datetime import datetime
import uuid
from pathlib import Path

from api.models.patient import PatientData
from api.services.chromadb_service import ChromaDBService
from api.services.plan_generator import PlanGeneratorService
from api.services.pdf_generator import PDFGeneratorService
from api.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


def get_chromadb_service() -> ChromaDBService:
    """Dependency to get ChromaDB service"""
    return ChromaDBService()


@router.post("/generate-plan")
async def generate_new_plan(
    patient_data: PatientData,
    background_tasks: BackgroundTasks,
    chromadb: ChromaDBService = Depends(get_chromadb_service)
) -> Dict[str, Any]:
    """
    Generate a new nutrition plan for a patient
    
    This endpoint implements Motor 1: Complete plan generation for new patients
    """
    try:
        # Generate unique plan ID
        plan_id = f"plan_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d')}"
        
        logger.info(f"Starting plan generation for patient: {patient_data.name}, Plan ID: {plan_id}")
        
        # Initialize services
        plan_generator = PlanGeneratorService(chromadb)
        pdf_generator = PDFGeneratorService()
        
        # Generate the nutrition plan
        nutrition_plan = await plan_generator.generate_plan(patient_data)
        
        # Generate PDF in background
        background_tasks.add_task(
            pdf_generator.generate_pdf,
            plan_id,
            patient_data,
            nutrition_plan
        )
        
        # Prepare meal data for response
        # Since it's "Tres Días y Carga", all days have the same meals
        day_meals = {}
        
        # Add debug logging
        logger.info(f"Nutrition plan type: {type(nutrition_plan)}")
        logger.info(f"Has days attribute: {hasattr(nutrition_plan, 'days')}")
        logger.info(f"Number of days: {len(nutrition_plan.days) if hasattr(nutrition_plan, 'days') else 0}")
        
        if hasattr(nutrition_plan, 'days') and nutrition_plan.days:
            # Get meals from the first day (all days are identical)
            first_day = nutrition_plan.days[0]
            logger.info(f"First day type: {type(first_day)}")
            logger.info(f"First day has meals: {hasattr(first_day, 'meals')}")
            
            # Handle meals as attribute (dataclass) not as dictionary
            if hasattr(first_day, 'meals') and first_day.meals:
                logger.info(f"Meals type: {type(first_day.meals)}")
                logger.info(f"Meals keys: {list(first_day.meals.keys()) if isinstance(first_day.meals, dict) else 'Not a dict'}")
                
                # If meals is a dict, iterate through it
                if isinstance(first_day.meals, dict):
                    for meal_type, meal_data in first_day.meals.items():
                        logger.info(f"Processing meal {meal_type}: {type(meal_data)}")
                        
                        # Handle meal_data whether it's a dict or has attributes
                        if isinstance(meal_data, dict):
                            day_meals[meal_type] = {
                                "name": meal_data.get("name", ""),
                                "description": meal_data.get("description", ""),
                                "ingredients": meal_data.get("ingredients", []),
                                "preparation": meal_data.get("preparation", ""),
                                "calories": meal_data.get("calories", 0),
                                "portion": meal_data.get("portion", ""),
                                "macros": meal_data.get("macros", {})
                            }
                        else:
                            # If meal_data is an object with attributes
                            day_meals[meal_type] = {
                                "name": getattr(meal_data, "name", ""),
                                "description": getattr(meal_data, "description", ""),
                                "ingredients": getattr(meal_data, "ingredients", []),
                                "preparation": getattr(meal_data, "preparation", ""),
                                "calories": getattr(meal_data, "calories", 0),
                                "portion": getattr(meal_data, "portion", ""),
                                "macros": getattr(meal_data, "macros", {})
                            }
                else:
                    logger.warning(f"Meals is not a dictionary: {type(first_day.meals)}")
            else:
                logger.warning("First day has no meals attribute or meals is empty")
        else:
            logger.warning("Nutrition plan has no days")
        
        logger.info(f"Final day_meals: {list(day_meals.keys())}")
        
        # Return plan summary with meal data
        return {
            "status": "success",
            "plan_id": plan_id,
            "patient_name": patient_data.name,
            "total_days": len(nutrition_plan.days) if hasattr(nutrition_plan, 'days') else 3,
            "total_calories": nutrition_plan.total_daily_calories if hasattr(nutrition_plan, 'total_daily_calories') else 2000,
            "daily_calories": nutrition_plan.total_daily_calories if hasattr(nutrition_plan, 'total_daily_calories') else 2000,  # Add for compatibility
            "bmi": patient_data.bmi,
            "bmi_category": patient_data.bmi_category,
            "pdf_status": "generating",
            "pdf_path": f"/api/v1/plans/{plan_id}/pdf",
            "plan_summary": {
                "meals_per_day": patient_data.meals_per_day,
                "economic_level": patient_data.economic_level,
                "pathologies": patient_data.pathologies,
                "allergies": patient_data.allergies
            },
            "meals": day_meals,  # Include the actual meal data
            "message": "Plan generated successfully. PDF will be available shortly."
        }
        
    except Exception as e:
        logger.error(f"Error generating plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating plan: {str(e)}")


@router.get("/plan/{plan_id}")
async def get_plan_details(plan_id: str) -> Dict[str, Any]:
    """Get details of a generated plan"""
    # TODO: Implement plan retrieval from storage
    return {
        "plan_id": plan_id,
        "status": "not_implemented",
        "message": "Plan retrieval will be implemented with storage service"
    }


@router.get("/plan/{plan_id}/pdf")
async def get_plan_pdf(plan_id: str):
    """Download the PDF for a generated plan"""
    from fastapi.responses import FileResponse
    import os
    
    # Construct the expected PDF filename
    pdf_directory = Path(settings.pdf_output_directory)
    
    # Look for PDF files that start with the plan_id
    matching_files = list(pdf_directory.glob(f"{plan_id}_*.pdf"))
    
    if not matching_files:
        logger.error(f"PDF not found for plan_id: {plan_id}")
        raise HTTPException(status_code=404, detail="PDF not found for this plan")
    
    # Use the first matching file
    pdf_path = matching_files[0]
    
    if not pdf_path.exists():
        logger.error(f"PDF file does not exist: {pdf_path}")
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    # Return the PDF file
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=pdf_path.name,
        headers={
            "Content-Disposition": f"attachment; filename={pdf_path.name}"
        }
    )


@router.post("/validate-patient")
async def validate_patient_data(patient_data: PatientData) -> Dict[str, Any]:
    """
    Validate patient data before plan generation
    
    This endpoint checks if the patient data is complete and valid
    """
    try:
        # Calculate nutritional requirements
        bmr = calculate_bmr(patient_data)
        tdee = calculate_tdee(bmr, patient_data.activity_level)
        
        # Check for potential issues
        warnings = []
        
        if patient_data.bmi < 18.5:
            warnings.append("Patient is underweight. Plan will focus on healthy weight gain.")
        elif patient_data.bmi > 30:
            warnings.append("Patient is obese. Plan will focus on gradual weight loss.")
        
        if len(patient_data.allergies) > 5:
            warnings.append("Multiple allergies detected. Recipe selection may be limited.")
        
        if patient_data.age < 18:
            warnings.append("Patient is under 18. Nutritional needs for growth will be considered.")
        elif patient_data.age > 65:
            warnings.append("Patient is over 65. Age-specific nutritional needs will be considered.")
        
        return {
            "status": "valid",
            "patient_name": patient_data.name,
            "bmi": patient_data.bmi,
            "bmi_category": patient_data.bmi_category,
            "estimated_calories": round(tdee),
            "warnings": warnings,
            "recommendations": {
                "meals_per_day": patient_data.meals_per_day,
                "hydration": "8-10 glasses of water daily",
                "exercise": get_exercise_recommendation(patient_data.activity_level)
            }
        }
        
    except Exception as e:
        logger.error(f"Error validating patient data: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid patient data: {str(e)}")


def calculate_bmr(patient: PatientData) -> float:
    """Calculate Basal Metabolic Rate using Mifflin-St Jeor equation"""
    if patient.gender == "male":
        bmr = 10 * patient.weight + 6.25 * patient.height - 5 * patient.age + 5
    else:
        bmr = 10 * patient.weight + 6.25 * patient.height - 5 * patient.age - 161
    return bmr


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """Calculate Total Daily Energy Expenditure"""
    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9
    }
    return bmr * activity_multipliers.get(activity_level, 1.2)


def get_exercise_recommendation(activity_level: str) -> str:
    """Get exercise recommendation based on activity level"""
    recommendations = {
        "sedentary": "Start with 30 minutes of light walking daily",
        "light": "Maintain 30-45 minutes of moderate exercise 3-4 times/week",
        "moderate": "Continue with 45-60 minutes of exercise 4-5 times/week",
        "active": "Maintain current activity level with variety in exercises",
        "very_active": "Ensure adequate rest and recovery between intense sessions"
    }
    return recommendations.get(activity_level, "Consult with a fitness professional")