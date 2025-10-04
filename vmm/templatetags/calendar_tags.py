from django import template
from django.utils import timezone
import calendar
from datetime import date, datetime

register = template.Library()

@register.simple_tag
def get_calendar_days(month, year):
    """
    Retorna uma lista de dicionários com informações sobre cada dia do calendário
    incluindo dias do mês anterior e próximo para preencher a grade
    """
    cal = calendar.Calendar(firstweekday=6)  # Domingo como primeiro dia
    days = []
    today = timezone.now().date()
    
    # Obter todos os dias do mês (incluindo dias de outros meses para completar semanas)
    for day in cal.itermonthdates(year, month):
        day_info = {
            'day': day.day,
            'date': day,
            'current_month': day.month == month,
            'is_today': day == today
        }
        days.append(day_info)
    
    return days

@register.simple_tag
def get_status_counts(eventos):
    """
    Conta eventos por status
    """
    counts = {
        'planejamento': 0,
        'confirmado': 0,
        'em_andamento': 0,
        'concluido': 0,
        'cancelado': 0
    }
    
    for evento in eventos:
        if evento.status in counts:
            counts[evento.status] += 1
    
    return counts

@register.filter
def get_month_name(month_number):
    """
    Retorna o nome do mês em português
    """
    months = {
        1: 'Janeiro',
        2: 'Fevereiro',
        3: 'Março',
        4: 'Abril',
        5: 'Maio',
        6: 'Junho',
        7: 'Julho',
        8: 'Agosto',
        9: 'Setembro',
        10: 'Outubro',
        11: 'Novembro',
        12: 'Dezembro'
    }
    return months.get(month_number, '')