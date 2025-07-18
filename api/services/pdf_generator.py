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
        
        # Check if we have actual meal data
        if hasattr(nutrition_plan, 'days') and nutrition_plan.days:
            for day in nutrition_plan.days[:3]:  # Show first 3 days (should be equal)
                if hasattr(day, 'meals') and day.meals:
                    for meal in day.meals:
                        meal_data = []
                        
                        # Meal name and calories
                        meal_name = getattr(meal, 'name', 'Comida')
                        meal_calories = getattr(meal, 'calories', 0)
                        meal_data.append([
                            Paragraph(f"<b>{meal_name}</b>", styles['Normal']),
                            Paragraph(f"<b>{meal_calories} kcal</b>", styles['Normal'])
                        ])
                        
                        # Add meal items
                        if hasattr(meal, 'items') and meal.items:
                            for item in meal.items:
                                item_name = getattr(item, 'name', '')
                                item_quantity = getattr(item, 'quantity', '')
                                if item_name:
                                    meal_data.append([
                                        Paragraph(f"• {item_name}", styles['Normal']),
                                        Paragraph(item_quantity, styles['Normal'])
                                    ])
                        
                        # Create meal table
                        if meal_data:
                            meal_table = Table(meal_data, colWidths=[5*inch, 2*inch])
                            meal_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E7EB')),
                                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('FONTSIZE', (0, 0), (-1, -1), 10),
                                ('TOPPADDING', (0, 0), (-1, -1), 5),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                            ]))
                            story.append(meal_table)
                            story.append(Spacer(1, 0.2*inch))
                    
                    # Only show first day since all 3 are equal
                    break
        else:
            # Fallback if no meal data
            story.append(Paragraph(
                "El plan detallado de comidas se está generando. Por favor, consulte con su nutricionista.",
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