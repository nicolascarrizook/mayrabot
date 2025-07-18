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


class ActivityType(str, Enum):
    """Type of physical activity"""
    SEDENTARIO = "sedentario"
    CAMINATAS = "caminatas"
    PESAS = "pesas"
    FUNCIONAL = "funcional"
    CROSSFIT = "crossfit"
    CALISTENIA = "calistenia"
    POWERLIFTING = "powerlifting"
    RUNNING = "running"
    CICLISMO = "ciclismo"
    FUTBOL = "futbol"
    OTRO = "otro"


class Objective(str, Enum):
    """Weight objective"""
    MANTENIMIENTO = "mantenimiento"
    BAJAR_025 = "bajar_025"  # Bajar 0.25 kg/semana
    BAJAR_05 = "bajar_05"    # Bajar 0.5 kg/semana
    BAJAR_075 = "bajar_075"  # Bajar 0.75 kg/semana
    BAJAR_1 = "bajar_1"      # Bajar 1 kg/semana
    SUBIR_025 = "subir_025"  # Subir 0.25 kg/semana
    SUBIR_05 = "subir_05"    # Subir 0.5 kg/semana
    SUBIR_075 = "subir_075"  # Subir 0.75 kg/semana
    SUBIR_1 = "subir_1"      # Subir 1 kg/semana


class FoodWeightType(str, Enum):
    """Type of food weight measurement"""
    CRUDO = "crudo"
    COCIDO = "cocido"


class EconomicLevel(str, Enum):
    """Economic level for recipe selection"""
    SIN_RESTRICCIONES = "sin_restricciones"
    MEDIO = "medio"
    LIMITADO = "limitado"
    BAJO_RECURSOS = "bajo_recursos"


class ProteinLevel(str, Enum):
    """Protein intake level based on activity and health conditions"""
    MUY_BAJA = "muy_baja"        # 0.5-0.8 g/kg (patologías renales)
    CONSERVADA = "conservada"     # 0.8-1.2 g/kg (normal)
    MODERADA = "moderada"         # 1.2-1.6 g/kg (personas activas no deportistas)
    ALTA = "alta"                 # 1.6-2.2 g/kg (uso deportivo)
    MUY_ALTA = "muy_alta"        # 2.2-2.8 g/kg (deportistas alto rendimiento)
    EXTREMA = "extrema"          # 3.0-3.5 g/kg (atletas con anabólicos)


class DistributionType(str, Enum):
    """Type of calorie and macronutrient distribution across meals"""
    TRADITIONAL = "traditional"   # Different percentages per meal (30-40-30, 25-35-15-25, etc.)
    EQUITABLE = "equitable"      # Equal distribution across all meals


class PatientData(BaseModel):
    """Patient information for plan generation"""
    
    # Basic information
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=1, le=120)
    gender: Gender
    height: float = Field(..., gt=0, le=300, description="Height in cm")
    weight: float = Field(..., gt=0, le=500, description="Weight in kg")
    
    # Objective
    objective: Objective
    
    # Physical activity details
    activity_type: ActivityType
    activity_frequency: int = Field(..., ge=1, le=7, description="Times per week")
    activity_duration: int = Field(..., description="Duration in minutes (30/45/60/75/90/120)")
    activity_level: Optional[ActivityLevel] = None  # Calculated from type, frequency and duration
    
    # Lifestyle
    economic_level: EconomicLevel = EconomicLevel.MEDIO
    supplementation: List[str] = Field(default_factory=list, description="Current supplements")
    meal_schedule: Optional[str] = Field(None, description="Usual meal and training schedule")
    
    # Medical conditions
    pathologies: List[str] = Field(default_factory=list)
    medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    food_preferences: List[str] = Field(default_factory=list, description="Le gusta")
    food_dislikes: List[str] = Field(default_factory=list, description="NO consume")
    
    # Plan preferences
    meals_per_day: int = Field(default=4, ge=3, le=4, description="3 or 4 main meals")
    include_snacks: bool = Field(default=False, description="Include colaciones")
    snack_type: Optional[str] = Field(None, description="por_saciedad, pre_entreno, post_entreno")
    days_requested: int = Field(default=3, description="Always 3 equal days for Tres Días y Carga method")
    food_weight_type: FoodWeightType = Field(default=FoodWeightType.CRUDO)
    
    # Optional notes
    personal_notes: Optional[str] = Field(None, description="Notas personales")
    
    # Macro customization
    carbs_percentage: Optional[int] = Field(None, ge=5, le=65, description="Porcentaje de carbohidratos del total calórico (5-65%)")
    protein_level: Optional[ProteinLevel] = Field(None, description="Nivel de proteína según actividad y salud")
    fat_percentage: Optional[int] = Field(None, ge=15, le=45, description="Porcentaje específico de grasas")
    distribution_type: DistributionType = Field(default=DistributionType.TRADITIONAL, description="Tipo de distribución de calorías y macros entre comidas")
    
    @validator('activity_duration')
    def validate_duration(cls, v):
        valid_durations = [30, 45, 60, 75, 90, 120]
        if v not in valid_durations:
            raise ValueError(f'Duration must be one of: {valid_durations}')
        return v
    
    @validator('carbs_percentage')
    def validate_carbs_percentage(cls, v):
        if v is not None and v % 5 != 0:
            raise ValueError('Carbs percentage must be in intervals of 5 (5, 10, 15, ..., 60, 65)')
        return v
    
    @validator('activity_level', pre=True, always=True)
    def calculate_activity_level(cls, v, values):
        """Calculate activity level from type, frequency and duration"""
        # If a value is provided, use it
        if v is not None:
            return v
            
        # Otherwise calculate it
        if 'activity_type' not in values or 'activity_frequency' not in values:
            return ActivityLevel.SEDENTARY
        
        activity_type = values.get('activity_type')
        frequency = values.get('activity_frequency', 1)
        
        # Calculate based on type and frequency
        if activity_type == 'sedentario' or activity_type == ActivityType.SEDENTARIO:
            return ActivityLevel.SEDENTARY
        elif frequency <= 2:
            return ActivityLevel.LIGHT
        elif frequency <= 4:
            return ActivityLevel.MODERATE
        elif frequency <= 5:
            return ActivityLevel.ACTIVE
        else:
            return ActivityLevel.VERY_ACTIVE
    
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