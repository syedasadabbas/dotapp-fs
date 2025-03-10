from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get value from dictionary by key"""
    return dictionary.get(key)

@register.filter
def multiply(value, arg):
    """Multiply value by argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return None

@register.filter
def format_timedelta(td):
    """Format timedelta into readable string"""
    if not td:
        return "0 minutes"
    
    days = td.days
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    
    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    
    return ", ".join(parts) if parts else "less than a minute"
