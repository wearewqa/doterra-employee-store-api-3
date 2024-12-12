import graphene

from .mutations.mutations import ImportEmployeeData
from .mutations.mutations import ImportInventoryData

class EmployeeStoreMutations(graphene.ObjectType):
    import_employee_data = ImportEmployeeData.Field()
    import_inventory_data = ImportInventoryData.Field()
