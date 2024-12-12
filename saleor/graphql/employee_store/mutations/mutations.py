import graphene
from graphene import Enum

from ....employee_store.tasks.import_employee_data_monthly import import_data as import_data_monthly
from ....employee_store.tasks.import_employee_data_daily import import_data as import_daily_data

class ImportTypeEnum(Enum):
    DAILY = "Daily"
    MONTHLY = "Monthly"

class ImportUserData(graphene.Mutation):
    class Arguments:
        importType = ImportTypeEnum(required=True, description="The type of Import (Daily or Monthly).")
        manual = graphene.Boolean(required=False, description="Whether the import is a manual update.")

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, importType, manual=False):
        if importType == ImportTypeEnum.DAILY:
            result, message = import_daily_data(manual)
        elif importType == ImportTypeEnum.MONTHLY:
            result, message = import_data_monthly()
        else:
            raise ValueError(f"Unknown import type: {importType}")
        return ImportUserData(success=result, message=f"Received: {importType} - {message}")
