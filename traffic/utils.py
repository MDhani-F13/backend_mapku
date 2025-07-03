from datetime import date
from .models import APICallQuota

MAX_DIRECTIONS_CALLS = 5000

def can_make_directions_call():
    obj, _ = APICallQuota.objects.get_or_create(name="directions_api")
    today = date.today()

    # Reset setiap bulan
    if obj.reset_month.month != today.month or obj.reset_month.year != today.year:
        obj.count = 0
        obj.reset_month = today
        obj.save()

    if obj.count < MAX_DIRECTIONS_CALLS:
        obj.count += 1
        obj.save()
        return True
    return False