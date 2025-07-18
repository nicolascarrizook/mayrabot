"""
OpenAI Service for AI-powered generation
"""

import os
import logging
from typing import Dict, Any, List
from openai import OpenAI
from api.config import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI API"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.temperature = settings.openai_temperature
        self.max_tokens = settings.openai_max_tokens
    
    async def generate_meal_plan(
        self,
        patient_info: Dict[str, Any],
        recipes: List[Dict[str, Any]],
        requirements: Dict[str, Any]
    ) -> str:
        """
        Generate a meal plan using GPT-4
        
        Args:
            patient_info: Patient data and preferences
            recipes: Available recipes from ChromaDB
            requirements: Nutritional requirements with prompt
            
        Returns:
            Generated meal plan text (JSON format)
        """
        # Use the prompt from requirements
        prompt = requirements.get('prompt', '')
        
        if not prompt:
            raise ValueError("Prompt is required in requirements")
        
        try:
            # Get system prompt for nutritionist role
            from prompts.base_prompt import BasePromptTemplate
            system_prompt = BasePromptTemplate.get_system_prompt()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}  # Force JSON response
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating meal plan: {e}")
            raise
    
    async def adjust_meal_plan(
        self,
        prompt: str
    ) -> str:
        """
        Generate adjustments to an existing meal plan
        
        Args:
            prompt: Complete prompt for plan adjustment
            
        Returns:
            Adjusted plan in JSON format
        """
        try:
            from prompts.base_prompt import BasePromptTemplate
            system_prompt = BasePromptTemplate.get_system_prompt()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error adjusting meal plan: {e}")
            raise
    
    async def find_meal_replacement(
        self,
        prompt: str
    ) -> str:
        """
        Find suitable meal replacements
        
        Args:
            prompt: Complete prompt for meal replacement
            
        Returns:
            Replacement options in JSON format
        """
        try:
            from prompts.base_prompt import BasePromptTemplate
            system_prompt = BasePromptTemplate.get_system_prompt()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error finding meal replacement: {e}")
            raise