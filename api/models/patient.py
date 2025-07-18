"""
Patient data models
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import date


class Gender(str, Enum):
    """Patient gender"""
    MALE = "male"
    FEMALE = "female"


class ActivityLevel(str, Enum):
    """Physical activity level"""
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"


class EconomicLevel(str, Enum):
    """Economic level for recipe selection"""
    ECONOMICO = "economico"
    STANDARD = "standard"
    PREMIUM = "premium"


class PatientData(BaseModel):
    """Patient information for plan generation"""
    
    # Basic information
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=1, le=120)
    gender: Gender
    height: float = Field(..., gt=0, le=300, description="Height in cm")
    weight: float = Field(..., gt=0, le=500, description="Weight in kg")
    
    # Lifestyle
    activity_level: ActivityLevel
    economic_level: EconomicLevel = EconomicLevel.STANDARD
    
    # Medical conditions
    pathologies: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    food_preferences: List[str] = Field(default_factory=list)
    food_dislikes: List[str] = Field(default_factory=list)
    
    # Plan preferences
    meals_per_day: int = Field(default=4, ge=3, le=6)
    days_requested: int = Field(default=7, ge=1, le=30)
    
    # Optional notes
    observations: Optional[str] = None
    
    @validator('height')
    def validate_height(cls, v):
        if v < 50 or v > 250:
            raise ValueError('Height must be between 50 and 250 cm')
        return v
    
    @validator('weight')
    def validate_weight(cls, v):
        if v < 20 or v > 300:
            raise ValueError('Weight must be between 20 and 300 kg')
        return v
    
    @property
    def bmi(self) -> float:
        """Calculate BMI"""
        height_m = self.height / 100
        return round(self.weight / (height_m ** 2), 2)
    
    @property
    def bmi_category(self) -> str:
        """Get BMI category"""
        bmi = self.bmi
        if bmi < 18.5:
            return "underweight"
        elif bmi < 25:
            return "normal"
        elif bmi < 30:
            return "overweight"
        else:
            return "obese"


class ControlData(BaseModel):
    """Data for control/follow-up modifications (Motor 2)"""
    
    patient_data: PatientData
    current_weight: float = Field(..., gt=0, le=500, description="Current weight in kg")
    days_on_plan: int = Field(..., ge=1)
    adherence_percentage: float = Field(default=80.0, ge=0, le=100)
    
    # Changes or issues
    reported_issues: List[str] = Field(default_factory=list)
    requested_changes: List[str] = Field(default_factory=list)
    
    # Medical updates
    new_pathologies: List[str] = Field(default_factory=list)
    new_medications: List[str] = Field(default_factory=list)
    
    @property
    def weight_change(self) -> float:
        """Calculate weight change"""
        return round(self.current_weight - self.patient_data.weight, 2)
    
    @property
    def weight_change_percentage(self) -> float:
        """Calculate weight change percentage"""
        if self.patient_data.weight > 0:
            return round((self.weight_change / self.patient_data.weight) * 100, 2)
        return 0.0


class MealReplacementRequest(BaseModel):
    """Request for meal replacement (Motor 3)"""
    
    patient_data: PatientData
    meal_to_replace: str = Field(..., description="Description of the meal to replace")
    meal_type: str = Field(..., description="Type: desayuno, almuerzo, merienda, cena, colacion")
    reason: str = Field(..., description="Reason for replacement")
    
    # Constraints for replacement
    maintain_calories: bool = Field(default=True)
    alternative_ingredients: List[str] = Field(default_factory=list)
    avoid_ingredients: List[str] = Field(default_factory=list)
    
    @validator('meal_type')
    def validate_meal_type(cls, v):
        valid_types = ['desayuno', 'almuerzo', 'merienda', 'cena', 'colacion']
        if v.lower() not in valid_types:
            raise ValueError(f'Meal type must be one of: {", ".join(valid_types)}')
        return v.lower()