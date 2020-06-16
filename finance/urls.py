from django.urls import path, register_converter
from datetime import datetime
from . import views

app_name = 'finance'

class DateConverter:
    regex = '\d{2}-\d{2}-\d{4}'

    def to_python(self, value):
        return datetime.strptime(value, '%m-%d-%Y')

    def to_url(self, value):
        return value

register_converter(DateConverter, 'mdy')


urlpatterns = [
    path('estimate/<int:invoice_id>', views.estimate, name='estimate'),
    path('invoice/<int:invoice_id>', views.invoice, name='invoice'),
    path('payroll/<mdy:paydate>/<mdy:beg>/<mdy:end>', views.payroll, name='payroll'),
]
