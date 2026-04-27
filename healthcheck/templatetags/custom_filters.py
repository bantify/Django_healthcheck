from django import template

register = template.Library()

@register.filter
def to_gb(value):
    try:
        return (value or 0) / 1024
    except:
        return 0
    
@register.filter
def free_percent(free, total):
    try:
        total = total or 0
        if total == 0:
            return 0
        return (free / total) * 100
    except:
        return 0

@register.filter
def percent(free, total):
    try:
        free = float(free)
        total = float(total)
        if total == 0:
            return "0"
        return round((free / total) * 100, 2)
    except:
        return "0"