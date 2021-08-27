from django.template.defaulttags import register


@register.filter
def get_form(job_id, forms):
    return forms[f"job_{job_id}"]
