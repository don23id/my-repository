import datetime
from .models import VisitCount

class VisitCounterMiddleware:
    """
    Middleware для подсчета посещений сайта
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Получаем текущую дату
        today = datetime.date.today()

        # ---- START OF CHANGE ----
        # Check if it's an AJAX request by looking for a common header.
        # request.headers is a case-insensitive dict-like object.
        is_ajax_request = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        # ---- END OF CHANGE ----

        # Проверяем, является ли запрос обычным просмотром страницы (не AJAX, не статические файлы и т.д.)
        # Exclude admin, static, media paths, AJAX requests, and non-GET requests
        if not request.path.startswith(('/admin/', '/static/', '/media/')) \
           and not is_ajax_request \
           and request.method == 'GET':

            # Получаем или создаем запись для текущей даты
            visit_count, created = VisitCount.objects.get_or_create(date=today)

            # Если запись создана или это новая сессия (для этого дня), увеличиваем счетчик
            # To count one visit per session per day, we make the session key date-specific
            session_key_for_today_visit = f'visited_day_{today.isoformat()}'

            if session_key_for_today_visit not in request.session:
                visit_count.count += 1
                visit_count.save()

                # Отмечаем, что пользователь посетил сайт в этой сессии для этого дня
                request.session[session_key_for_today_visit] = True
                # Optionally, set an expiry for this session key if sessions are very long
                # request.session.set_expiry(some_value_in_seconds_or_datetime)

        response = self.get_response(request)
        return response