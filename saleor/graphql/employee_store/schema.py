import graphene

from .mutations.mutations import ImportUserData

class EmployeeStoreMutations(graphene.ObjectType):
    # Base mutations
    import_user_data = ImportUserData.Field()
