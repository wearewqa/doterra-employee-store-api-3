from pprint import pprint
from django.apps import AppConfig

class EmployeeStoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'saleor.employee_store'

    def ready(self):
        return
