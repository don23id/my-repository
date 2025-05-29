from .models import VisitCount
import datetime
from django.db.models import Sum # <--- IMPORT Sum HERE

def visit_counter(request):
    """
    Контекстный процессор для передачи данных счетчика посещений в шаблоны
    """
    today = datetime.date.today()

    # Получаем статистику посещений
    try:
        today_visits = VisitCount.objects.get(date=today).count
    except VisitCount.DoesNotExist:
        today_visits = 0

    # Общее количество посещений
    total_visits_data = VisitCount.objects.aggregate(total=Sum('count'))
    total_visits = total_visits_data['total'] or 0

    return {
        'today_visits': today_visits,
        'total_visits': total_visits,
    }