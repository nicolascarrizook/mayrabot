"""
PDF Generator Service - Creates PDF documents for nutrition plans
"""

import os
import logging
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.platypus.flowables import KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY

from api.config import settings
from api.models.patient import PatientData, ControlData

logger = logging.getLogger(__name__)


class PDFGeneratorService:
    """Service for generating PDF documents"""
    
    def __init__(self):
        self.output_dir = Path(settings.pdf_output_directory)
        self.output_dir.mkdir(exist_ok=True)
        self.template_dir = Path(settings.pdf_template_directory)
    
    async def generate_pdf(
        self,
        plan_id: str,
        patient_data: PatientData,
        nutrition_plan: Any
    ) -> str:
        """
        Generate PDF for a nutrition plan
        
        Args:
            plan_id: Unique plan identifier
            patient_data: Patient information
            nutrition_plan: Generated nutrition plan
            
        Returns:
            Path to generated PDF
        """
        logger.info(f"Generating PDF for plan {plan_id}")
        
        pdf_filename = f"{plan_id}_{patient_data.name.replace(' ', '_')}.pdf"
        pdf_path = self.output_dir / pdf_filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Container for the 'Flowable' objects
        story = []
        
        # Get styles
        styles = self._get_custom_styles()
        
        # Add header
        story.extend(self._create_header(styles, patient_data, plan_id))
        
        # Add patient summary
        story.extend(self._create_patient_summary(styles, patient_data))
        
        # Add nutritional calculations
        story.extend(self._create_nutritional_info(styles, patient_data, nutrition_plan))
        
        # Add meal plan
        story.extend(self._create_meal_plan(styles, nutrition_plan))
        
        # Add recommendations
        story.extend(self._create_recommendations(styles, patient_data))
        
        # Add footer
        story.extend(self._create_footer(styles))
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"PDF generated: {pdf_path}")
        return str(pdf_path)
    
    def _get_custom_styles(self):
        """Get custom paragraph styles for the PDF"""
        styles = getSampleStyleSheet()
        
        # Title style
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1E3A8A'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Subtitle style
        styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2563EB'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        # Section header
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#374151'),
            spaceAfter=10,
            spaceBefore=10,
            borderWidth=1,
            borderColor=colors.HexColor('#E5E7EB'),
            borderPadding=5,
            backColor=colors.HexColor('#F9FAFB')
        ))
        
        return styles
    
    def _create_header(self, styles, patient_data: PatientData, plan_id: str) -> List:
        """Create PDF header"""
        story = []
        
        # Title
        title = Paragraph(
            "Plan Nutricional Personalizado<br/>Método Tres Días y Carga",
            styles['CustomTitle']
        )
        story.append(title)
        
        # Subtitle with date and ID
        subtitle = Paragraph(
            f"Dieta Inteligente® & Nutrición Evolutiva<br/>"
            f"Fecha: {datetime.now().strftime('%d/%m/%Y')} | ID: {plan_id}",
            styles['Normal']
        )
        story.append(subtitle)
        story.append(Spacer(1, 0.5*inch))
        
        return story
    
    def _create_patient_summary(self, styles, patient_data: PatientData) -> List:
        """Create patient summary section"""
        story = []
        
        # Section header
        story.append(Paragraph("Datos del Paciente", styles['SectionHeader']))
        
        # Patient data table
        data = [
            ['Nombre:', patient_data.name, 'Edad:', f"{patient_data.age} años"],
            ['Sexo:', 'Masculino' if patient_data.gender.value == 'male' else 'Femenino', 
             'Objetivo:', self._format_objective(patient_data.objective.value)],
            ['Altura:', f"{patient_data.height} cm", 'Peso:', f"{patient_data.weight} kg"],
            ['IMC:', f"{patient_data.bmi}", 'Categoría:', self._format_bmi_category(patient_data.bmi_category)],
            ['Actividad:', self._format_activity(patient_data), '', '']
        ]
        
        # Add medical conditions if any
        if patient_data.pathologies:
            data.append(['Patologías:', ', '.join(patient_data.pathologies), '', ''])
        if patient_data.allergies:
            data.append(['Alergias:', ', '.join(patient_data.allergies), '', ''])
        if patient_data.medications:
            data.append(['Medicación:', ', '.join(patient_data.medications), '', ''])
        
        table = Table(data, colWidths=[2*inch, 2.5*inch, 1.5*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.3*inch))
        
        return story
    
    def _create_nutritional_info(self, styles, patient_data: PatientData, nutrition_plan: Any) -> List:
        """Create nutritional calculations section"""
        story = []
        
        story.append(Paragraph("Información Nutricional", styles['SectionHeader']))
        
        # Calculate calories based on objective
        daily_calories = nutrition_plan.total_daily_calories if hasattr(nutrition_plan, 'total_daily_calories') else 2000
        
        info_text = f"""
        <b>Calorías Diarias Recomendadas:</b> {daily_calories} kcal<br/>
        <b>Distribución de Macronutrientes:</b><br/>
        • Proteínas: {int(daily_calories * 0.25 / 4)}g ({int(daily_calories * 0.25)} kcal - 25%)<br/>
        • Carbohidratos: {int(daily_calories * 0.45 / 4)}g ({int(daily_calories * 0.45)} kcal - 45%)<br/>
        • Grasas: {int(daily_calories * 0.30 / 9)}g ({int(daily_calories * 0.30)} kcal - 30%)<br/>
        <br/>
        <b>Comidas por día:</b> {patient_data.meals_per_day} principales
        """
        
        if patient_data.include_snacks:
            snack_type_map = {
                'saciedad': 'Por saciedad',
                'pre_entreno': 'Pre-entreno',
                'post_entreno': 'Post-entreno'
            }
            info_text += f" + colaciones ({snack_type_map.get(patient_data.snack_type, '')})"
        
        story.append(Paragraph(info_text, styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        return story
    
    def _create_meal_plan(self, styles, nutrition_plan: Any) -> List:
        """Create detailed meal plan section"""
        story = []
        
        story.append(Paragraph("Plan de Alimentación - 3 Días Iguales", styles['SectionHeader']))
        story.append(Paragraph("Método Tres Días y Carga | Dieta Inteligente® & Nutrición Evolutiva", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Define meal order and emojis
        meal_order = ['desayuno', 'almuerzo', 'merienda', 'cena']
        meal_names = {
            'desayuno': '🌅 DESAYUNO',
            'almuerzo': '☀️ ALMUERZO', 
            'merienda': '🍵 MERIENDA',
            'cena': '🌙 CENA'
        }
        
        # Check if we have actual meal data
        if hasattr(nutrition_plan, 'days') and nutrition_plan.days:
            # Get first day (all days are identical in Tres Días y Carga)
            first_day = nutrition_plan.days[0]
            
            if hasattr(first_day, 'meals') and isinstance(first_day.meals, dict):
                # Add note about 3 equal days
                story.append(Paragraph(
                    "<i>Este plan se repite idéntico durante los 3 días</i>",
                    styles['Normal']
                ))
                story.append(Spacer(1, 0.2*inch))
                
                # Process each meal in order
                for meal_type in meal_order:
                    if meal_type in first_day.meals:
                        meal = first_day.meals[meal_type]
                        
                        # Create meal section
                        meal_data = []
                        
                        # Meal header with emoji and calories
                        meal_header = meal_names.get(meal_type, meal_type.upper())
                        calories = meal.get('calories', 0)
                        
                        meal_data.append([
                            Paragraph(f"<b>{meal_header}</b>", styles['Heading3']),
                            Paragraph(f"<b>{calories} kcal</b>", styles['Normal'])
                        ])
                        
                        # Meal name/description
                        if meal.get('name'):
                            meal_data.append([
                                Paragraph(f"<i>{meal['name']}</i>", styles['Normal']),
                                ""
                            ])
                            meal_data.append(["", ""])  # Spacer row
                        
                        # Ingredients section
                        if meal.get('ingredients') and len(meal['ingredients']) > 0:
                            meal_data.append([
                                Paragraph("<b>Ingredientes:</b>", styles['Normal']),
                                ""
                            ])
                            
                            for ingredient in meal['ingredients']:
                                if isinstance(ingredient, dict):
                                    food = ingredient.get('alimento', ingredient.get('name', ''))
                                    quantity = ingredient.get('cantidad', ingredient.get('quantity', ''))
                                    ing_type = ingredient.get('tipo', '')
                                    
                                    # Format ingredient line
                                    ing_text = f"• {food}"
                                    if quantity:
                                        ing_text += f" - {quantity}"
                                    if ing_type and ing_type != 'crudo':
                                        ing_text += f" ({ing_type})"
                                else:
                                    ing_text = f"• {ingredient}"
                                
                                meal_data.append([
                                    Paragraph(ing_text, styles['Normal']),
                                    ""
                                ])
                        
                        # Preparation section
                        if meal.get('preparation'):
                            meal_data.append(["", ""])  # Spacer row
                            meal_data.append([
                                Paragraph("<b>Preparación:</b>", styles['Normal']),
                                ""
                            ])
                            
                            # Split long preparation text into paragraphs
                            prep_text = meal['preparation']
                            if len(prep_text) > 300:
                                # Break into sentences
                                sentences = prep_text.split('. ')
                                current_para = ""
                                for sentence in sentences:
                                    if len(current_para) + len(sentence) < 300:
                                        current_para += sentence + ". "
                                    else:
                                        if current_para:
                                            meal_data.append([
                                                Paragraph(current_para.strip(), styles['Normal']),
                                                ""
                                            ])
                                        current_para = sentence + ". "
                                if current_para:
                                    meal_data.append([
                                        Paragraph(current_para.strip(), styles['Normal']),
                                        ""
                                    ])
                            else:
                                meal_data.append([
                                    Paragraph(prep_text, styles['Normal']),
                                    ""
                                ])
                        
                        # Macros section
                        if meal.get('macros'):
                            macros = meal['macros']
                            carbs = macros.get('carbohydrates', macros.get('carbos', 0))
                            proteins = macros.get('proteins', macros.get('proteinas', 0))
                            fats = macros.get('fats', macros.get('grasas', 0))
                            
                            if carbs or proteins or fats:
                                meal_data.append(["", ""])  # Spacer row
                                macro_text = f"<b>Macros:</b> Carbohidratos: {carbs}g | Proteínas: {proteins}g | Grasas: {fats}g"
                                meal_data.append([
                                    Paragraph(macro_text, styles['Normal']),
                                    ""
                                ])
                        
                        # Create meal table with better styling
                        if len(meal_data) > 1:  # Only create table if we have content
                            meal_table = Table(meal_data, colWidths=[5.5*inch, 1.5*inch])
                            meal_table.setStyle(TableStyle([
                                # Header row styling
                                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E0F2FE')),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
                                # General styling
                                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                ('FONTSIZE', (0, 0), (-1, -1), 10),
                                ('TOPPADDING', (0, 0), (-1, -1), 6),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
                                # Alternating row colors
                                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                            ]))
                            
                            story.append(meal_table)
                            story.append(Spacer(1, 0.4*inch))
            else:
                # Log the actual structure for debugging
                logger.warning(f"Unexpected meal structure. Type: {type(first_day.meals) if hasattr(first_day, 'meals') else 'No meals attribute'}")
                story.append(Paragraph(
                    "Error: No se pudieron cargar las comidas del plan. Por favor, contacte soporte.",
                    styles['Normal']
                ))
        else:
            # No days in nutrition plan
            logger.error("No days found in nutrition plan")
            story.append(Paragraph(
                "El plan nutricional está siendo procesado. Por favor, intente nuevamente en unos momentos.",
                styles['Normal']
            ))
        
        story.append(Spacer(1, 0.3*inch))
        return story
    
    def _create_recommendations(self, styles, patient_data: PatientData) -> List:
        """Create recommendations section"""
        story = []
        
        story.append(Paragraph("Recomendaciones Generales", styles['SectionHeader']))
        
        recommendations = [
            "• Respetar los horarios de las comidas establecidos",
            "• Consumir al menos 2 litros de agua al día",
            "• Las cantidades indicadas son en gramos crudos (salvo indicación contraria)",
            "• Puede condimentar con hierbas, especias, limón y vinagre sin restricción",
            "• Evitar el consumo de alcohol durante el plan",
            "• Realizar actividad física según lo indicado",
            "• Ante cualquier duda o malestar, consultar con el profesional"
        ]
        
        # Add specific recommendations based on objective
        if patient_data.objective.value.startswith('bajar'):
            recommendations.insert(0, "• Objetivo: Reducción de peso gradual y sostenible")
        elif patient_data.objective.value.startswith('subir'):
            recommendations.insert(0, "• Objetivo: Aumento de peso con masa muscular magra")
        else:
            recommendations.insert(0, "• Objetivo: Mantenimiento del peso actual")
        
        for rec in recommendations:
            story.append(Paragraph(rec, styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        return story
    
    def _create_footer(self, styles) -> List:
        """Create PDF footer"""
        story = []
        
        story.append(Spacer(1, 0.5*inch))
        
        footer_text = """
        <i>Este plan nutricional ha sido generado de forma personalizada según los datos proporcionados.
        Se recomienda realizar un seguimiento regular con un profesional de la nutrición para ajustar
        el plan según la evolución y las necesidades individuales.</i>
        """
        
        story.append(Paragraph(footer_text, styles['Normal']))
        
        return story
    
    def _format_objective(self, objective: str) -> str:
        """Format objective for display"""
        objectives = {
            'mantenimiento': 'Mantenimiento',
            'bajar_05': 'Bajar 0.5 kg/semana',
            'bajar_1': 'Bajar 1 kg/semana',
            'subir_05': 'Subir 0.5 kg/semana',
            'subir_1': 'Subir 1 kg/semana'
        }
        return objectives.get(objective, objective)
    
    def _format_bmi_category(self, category: str) -> str:
        """Format BMI category for display"""
        categories = {
            'underweight': 'Bajo peso',
            'normal': 'Normal',
            'overweight': 'Sobrepeso',
            'obese': 'Obesidad'
        }
        return categories.get(category, category)
    
    def _format_activity(self, patient_data: PatientData) -> str:
        """Format activity information"""
        activity_type = patient_data.activity_type.value.replace('_', ' ').title()
        if patient_data.activity_frequency > 0:
            return f"{activity_type} - {patient_data.activity_frequency}x/semana, {patient_data.activity_duration} min"
        return activity_type
    
    async def generate_adjusted_pdf(
        self,
        adjustment_id: str,
        control_data: ControlData,
        adjusted_plan: Any,
        progress_analysis: Dict[str, Any]
    ) -> str:
        """
        Generate PDF for an adjusted plan
        
        Args:
            adjustment_id: Unique adjustment identifier
            control_data: Control consultation data
            adjusted_plan: Adjusted nutrition plan
            progress_analysis: Patient progress analysis
            
        Returns:
            Path to generated PDF
        """
        logger.info(f"Generating adjusted PDF for {adjustment_id}")
        
        # For now, use the same generation logic
        pdf_filename = f"{adjustment_id}_adjusted_{control_data.patient_data.name.replace(' ', '_')}.pdf"
        pdf_path = self.output_dir / pdf_filename
        
        # Would implement adjusted plan PDF generation here
        # For now, create a simple file
        pdf_path.touch()
        
        logger.info(f"Adjusted PDF generated: {pdf_path}")
        return str(pdf_path)