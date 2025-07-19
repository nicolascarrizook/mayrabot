"""
Progress bar utilities for professional UX
"""

import asyncio
from typing import Optional, Any
from telegram import Update
from telegram.ext import ContextTypes
from telegram_bot.config import settings


class ProgressTracker:
    """Track and display progress for long operations"""
    
    def __init__(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.update = update
        self.context = context
        self.message = None
        self.current_step = 0
        self.total_steps = 6
        self.start_time = None
        
    async def start(self, title: str = "Generando Plan Nutricional"):
        """Start progress tracking"""
        self.start_time = asyncio.get_event_loop().time()
        self.message = await self.update.effective_message.reply_text(
            self._format_progress(title, 0)
        )
        
    async def update_progress(self, step: int, custom_message: Optional[str] = None):
        """Update progress display"""
        self.current_step = step
        
        # Calculate elapsed time
        elapsed = int(asyncio.get_event_loop().time() - self.start_time)
        
        # Estimate remaining time based on progress
        if step > 0:
            time_per_step = elapsed / step
            remaining_steps = self.total_steps - step
            estimated_remaining = int(time_per_step * remaining_steps)
        else:
            estimated_remaining = 60  # Initial estimate
        
        # Update message
        if self.message:
            try:
                await self.message.edit_text(
                    self._format_progress(
                        "Generando Plan Nutricional",
                        step,
                        custom_message,
                        elapsed,
                        estimated_remaining
                    ),
                    parse_mode='Markdown'
                )
            except Exception:
                # Message might be too old to edit
                pass
                
    def _format_progress(
        self, 
        title: str, 
        step: int,
        custom_message: Optional[str] = None,
        elapsed: int = 0,
        remaining: int = 0
    ) -> str:
        """Format progress message with visual bar"""
        
        # Progress bar
        filled = "█" * (step * 2)
        empty = "░" * ((self.total_steps - step) * 2)
        percentage = int((step / self.total_steps) * 100)
        
        # Step messages
        steps = {
            0: "📋 Iniciando proceso...",
            1: "👤 Analizando datos del paciente...",
            2: "🔍 Buscando recetas apropiadas en base de datos...",
            3: "🤖 Generando plan personalizado con IA...",
            4: "📊 Calculando valores nutricionales...",
            5: "📄 Creando documento PDF profesional...",
            6: "✅ ¡Plan completado!"
        }
        
        current_message = custom_message or steps.get(step, "Procesando...")
        
        # Time formatting
        time_info = ""
        if elapsed > 0:
            elapsed_min = elapsed // 60
            elapsed_sec = elapsed % 60
            if elapsed_min > 0:
                time_info = f"\n⏱️ Tiempo: {elapsed_min}m {elapsed_sec}s"
            else:
                time_info = f"\n⏱️ Tiempo: {elapsed_sec}s"
                
            if remaining > 0 and step < self.total_steps:
                remaining_min = remaining // 60
                remaining_sec = remaining % 60
                if remaining_min > 0:
                    time_info += f" | Restante: ~{remaining_min}m {remaining_sec}s"
                else:
                    time_info += f" | Restante: ~{remaining_sec}s"
        
        # Compose message
        message = f"""
**{title}** 🍎

{current_message}

`[{filled}{empty}]` {percentage}%{time_info}

_{self._get_tip(step)}_
"""
        
        return message.strip()
    
    def _get_tip(self, step: int) -> str:
        """Get contextual tips during generation"""
        tips = {
            0: "Preparando todo para generar tu plan personalizado...",
            1: "Calculando tus necesidades calóricas según tu objetivo...",
            2: "Seleccionando las mejores recetas para tu perfil...",
            3: "Adaptando el plan a tus preferencias y restricciones...",
            4: "Balanceando macronutrientes para resultados óptimos...",
            5: "Diseñando un documento profesional y fácil de seguir...",
            6: "Tu plan está listo. ¡Revisa el PDF completo!"
        }
        return tips.get(step, "Procesando tu información...")
    
    async def complete(self, success: bool = True):
        """Complete progress tracking"""
        if success:
            final_message = f"""
✅ **¡Plan Nutricional Generado!**

Tu plan personalizado está listo y incluye:
• 3 días de menús completos y equilibrados
• Recetas detalladas con ingredientes exactos
• Valores nutricionales calculados
• Recomendaciones personalizadas

📄 El PDF con toda la información se enviará a continuación...
"""
        else:
            final_message = f"""
❌ **Error al generar el plan**

Hubo un problema al procesar tu solicitud. Por favor:
• Verifica que todos los datos estén correctos
• Intenta nuevamente en unos minutos
• Si el problema persiste, contacta al soporte

{settings.EMOJI_INFO} Código de error guardado para revisión.
"""
        
        if self.message:
            try:
                await self.message.edit_text(final_message, parse_mode='Markdown')
            except Exception:
                pass


async def show_instant_feedback(update: Update, field: str, value: Any):
    """Show instant feedback for field validation"""
    
    feedback_messages = {
        'weight': _weight_feedback,
        'height': _height_feedback,
        'age': _age_feedback,
        'objective': _objective_feedback,
        'activity': _activity_feedback,
        'pathologies': _pathology_feedback
    }
    
    handler = feedback_messages.get(field)
    if handler:
        message = handler(value)
        if message:
            await update.message.reply_text(message, parse_mode='Markdown')


def _weight_feedback(data: dict) -> str:
    """Generate weight feedback"""
    weight = data.get('weight', 0)
    height = data.get('height', 0)
    
    if weight and height:
        bmi = weight / ((height/100) ** 2)
        
        if bmi < 18.5:
            category = "bajo peso"
            emoji = "📉"
        elif bmi < 25:
            category = "peso normal"
            emoji = "✅"
        elif bmi < 30:
            category = "sobrepeso"
            emoji = "📊"
        else:
            category = "obesidad"
            emoji = "📈"
            
        return f"{emoji} **IMC calculado:** {bmi:.1f} ({category})\n_Tu plan se adaptará a este objetivo._"
    
    return None


def _height_feedback(data: dict) -> str:
    """Generate height feedback"""
    height = data.get('height', 0)
    
    if height:
        return f"📏 **Altura registrada:** {height} cm"
    
    return None


def _age_feedback(data: dict) -> str:
    """Generate age feedback"""
    age = data.get('age', 0)
    
    if age < 18:
        return "👶 **Menor de edad detectado**\n_El plan incluirá consideraciones de crecimiento._"
    elif age > 65:
        return "👴 **Adulto mayor**\n_Se ajustarán las necesidades nutricionales._"
    
    return None


def _objective_feedback(data: dict) -> str:
    """Generate objective feedback"""
    objective = data.get('objective', '')
    weight = data.get('weight', 70)
    
    messages = {
        'mantenimiento': f"⚖️ **Objetivo: Mantener peso**\n_Calorías estimadas: ~{int(weight * 30)} kcal/día_",
        'bajar_05': f"📉 **Objetivo: Bajar 0.5 kg/semana**\n_Déficit moderado de 500 kcal/día_",
        'bajar_1': f"📉 **Objetivo: Bajar 1 kg/semana**\n_Déficit de 1000 kcal/día (supervisado)_",
        'subir_05': f"📈 **Objetivo: Subir 0.5 kg/semana**\n_Superávit de 500 kcal/día_",
        'subir_1': f"📈 **Objetivo: Subir 1 kg/semana**\n_Superávit de 1000 kcal/día_"
    }
    
    return messages.get(objective, "")


def _activity_feedback(data: dict) -> str:
    """Generate activity feedback"""
    activity_type = data.get('activity_type', '')
    frequency = data.get('activity_frequency', 0)
    
    if activity_type == 'sedentario':
        return "🪑 **Estilo de vida sedentario**\n_Se ajustarán las calorías base._"
    elif frequency >= 5:
        return "💪 **Atleta activo**\n_Plan con mayor aporte calórico y proteico._"
    elif frequency >= 3:
        return "🏃 **Actividad moderada**\n_Buen balance para tu nivel de actividad._"
    
    return None


def _pathology_feedback(data: dict) -> str:
    """Generate pathology feedback"""
    pathologies = data.get('pathologies', [])
    
    if not pathologies or pathologies == ['no']:
        return None
        
    alerts = []
    
    for pathology in pathologies:
        path_lower = pathology.lower()
        
        if 'diabetes' in path_lower:
            alerts.append("🩺 **Diabetes detectada**: Control de índice glucémico")
        elif 'hipertension' in path_lower or 'hipertensión' in path_lower:
            alerts.append("🩺 **Hipertensión**: Plan bajo en sodio")
        elif 'celiac' in path_lower or 'celiaq' in path_lower:
            alerts.append("🩺 **Celiaquía**: Todas las recetas serán sin gluten")
        elif 'colesterol' in path_lower:
            alerts.append("🩺 **Colesterol alto**: Limitación de grasas saturadas")
            
    if alerts:
        return "\n".join(alerts) + "\n_Tu plan será adaptado a estas condiciones._"
    
    return None