import graphene

from .mutations.mutations import ImportEmployeeData
from .mutations.mutations import ImportInventoryData
from .bulk_mutations.order_bulk_fulfill import OrderBulkFulfill

class EmployeeStoreMutations(graphene.ObjectType):
    import_employee_data = ImportEmployeeData.Field()
    import_inventory_data = ImportInventoryData.Field()
    order_bulk_fulfill = OrderBulkFulfill.Field()
