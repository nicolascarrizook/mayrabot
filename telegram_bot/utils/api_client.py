"""
API Client for communication with FastAPI backend
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin

from telegram_bot.config import settings

logger = logging.getLogger(__name__)


class APIClient:
    """Client for FastAPI backend communication."""
    
    def __init__(self):
        self.base_url = settings.API_BASE_URL
        self.timeout = aiohttp.ClientTimeout(total=settings.API_TIMEOUT)
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to API."""
        url = urljoin(self.base_url, endpoint)
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            try:
                logger.info(f"Making {method} request to {url}")
                
                kwargs = {}
                if data:
                    kwargs['json'] = data
                if params:
                    kwargs['params'] = params
                
                async with session.request(method, url, **kwargs) as response:
                    response_data = await response.json()
                    
                    if response.status >= 400:
                        logger.error(f"API error: {response.status} - {response_data}")
                        raise APIError(
                            f"API returned status {response.status}",
                            status_code=response.status,
                            response_data=response_data
                        )
                    
                    return response_data
                    
            except asyncio.TimeoutError:
                logger.error(f"Request to {url} timed out")
                raise APIError("Request timed out", status_code=408)
            except aiohttp.ClientError as e:
                logger.error(f"Client error: {str(e)}")
                raise APIError(f"Connection error: {str(e)}", status_code=503)
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise APIError(f"Unexpected error: {str(e)}", status_code=500)
    
    async def health_check(self) -> bool:
        """Check if API is healthy."""
        try:
            response = await self._make_request('GET', '/health')
            return response.get('status') == 'healthy'
        except Exception:
            return False
    
    async def generate_new_plan(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate new nutritional plan (Motor 1)."""
        logger.info("Generating new nutritional plan")
        
        # Prepare request data - convert to API format
        # Gender is already in correct format (male/female) from new handler
        
        # Convert lists that might be strings
        def ensure_list(value):
            if isinstance(value, list):
                return value
            if not value or value.lower() in ['ninguno', 'ninguna', 'no']:
                return []
            return [item.strip() for item in value.split(',')]
        
        # All fields for Tres Días y Carga method
        request_data = {
            "name": patient_data['name'],
            "age": patient_data['age'],
            "gender": patient_data['gender'],  # Already 'male' or 'female'
            "height": patient_data['height'],
            "weight": patient_data['weight'],
            "objective": patient_data['objective'],
            "activity_type": patient_data['activity_type'],
            "activity_frequency": patient_data.get('activity_frequency', 1),
            "activity_duration": patient_data.get('activity_duration', 30),
            "supplementation": ensure_list(patient_data.get('supplementation', [])),
            "pathologies": ensure_list(patient_data.get('pathologies', [])),
            "medications": ensure_list(patient_data.get('medications', [])),
            "allergies": ensure_list(patient_data.get('allergies', [])),
            "food_preferences": ensure_list(patient_data.get('food_preferences', patient_data.get('preferences', []))),
            "food_dislikes": ensure_list(patient_data.get('food_dislikes', patient_data.get('dislikes', []))),
            "meal_schedule": patient_data.get('meal_schedule', ''),
            "meals_per_day": patient_data['meals_per_day'],
            "include_snacks": patient_data.get('include_snacks', False),
            "snack_type": patient_data.get('snack_type'),
            "days_requested": patient_data.get('days_requested', 3),  # Always 3 for Tres Días
            "economic_level": patient_data.get('economic_level', 'medio'),
            "food_weight_type": patient_data.get('food_weight_type', 'crudo'),
            "personal_notes": patient_data.get('personal_notes')
        }
        
        response = await self._make_request('POST', '/api/v1/motor1/generate-plan', data=request_data)
        return response
    
    async def adjust_plan(self, adjustment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust existing plan (Motor 2)."""
        logger.info("Adjusting nutritional plan")
        
        response = await self._make_request('POST', '/api/v1/motor2/adjust-plan', data=adjustment_data)
        return response
    
    async def find_meal_alternatives(
        self, 
        meal_type: str,
        category: Optional[str] = None,
        avoid_ingredients: Optional[List[str]] = None,
        economic_level: str = "standard",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find meal alternatives (Motor 3)."""
        logger.info(f"Finding alternatives for {meal_type}")
        
        request_data = {
            "meal_type": meal_type,
            "avoid_ingredients": avoid_ingredients or [],
            "economic_level": economic_level,
            "limit": limit
        }
        
        if category:
            request_data["category"] = category
        
        response = await self._make_request('POST', '/api/v1/motor3/find-alternatives', data=request_data)
        return response.get('alternatives', [])
    
    async def replace_meal(self, replacement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Replace meal in plan (Motor 3)."""
        logger.info("Replacing meal in plan")
        
        response = await self._make_request('POST', '/api/v1/motor3/replace-meal', data=replacement_data)
        return response


class APIError(Exception):
    """Custom exception for API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


# Singleton instance
api_client = APIClient()