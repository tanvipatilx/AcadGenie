from django import template

register = template.Library()

_ICONS = {
    'notes':     'bi-journal-text',
    'pdf':       'bi-file-earmark-pdf',
    'pyp':       'bi-clock-history',
    'imp_q':     'bi-patch-question',
    'youtube':   'bi-youtube',
    'reference': 'bi-book-half',
}

@register.filter
def resource_icon(resource_type):
    """Return the Bootstrap Icon class for a given resource type string."""
    return _ICONS.get(resource_type, 'bi-file-earmark')
