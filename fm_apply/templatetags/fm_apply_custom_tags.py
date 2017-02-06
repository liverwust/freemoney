from django import template
from django.utils.html import format_html


register = template.Library()


@register.simple_tag(takes_context=True)
def fm_navigation_buttons(context):
    buttons = []
    current_index = None
    for index, step in enumerate(context['STEPS']):
        if step.short_identifier == context['current_step'].short_identifier:
            current_index = index
            break
    if current_index == None:
        raise ValueError('invalid step identifier')
    if current_index == 0:
        buttons.append(('Start', 'btn-default'))
    else:
        buttons.append(('Cancel', 'btn-danger'))
        if current_index > 1:
            buttons.append(('Previous', 'btn-default'))
        if (current_index + 1) < len(context['STEPS']):
            buttons.append(('Next', 'btn-default'))
        else:
            buttons.append(('Submit', 'btn-success'))
    total_html = format_html('<div class="btn-group" role="group">')
    for button in buttons:
        total_html += format_html(
            '<button type="submit" name="{}" value="{}" class="{}">{}</button>',
            'submit-type',
            button[0],
            "btn " + button[1],
            button[0]
        )
    total_html += format_html('</div>')
    return total_html
