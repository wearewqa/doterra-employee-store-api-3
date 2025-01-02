from collections.abc import Iterable
from typing import Union
from uuid import UUID

from ....site.models import Site

import graphene

from ....order import models
from ....order.actions import create_fulfillments
from ....permission.enums import OrderPermissions
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.mutations import BaseBulkMutation
from ...core.types import NonNullList, OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ...order.types import Order

class OrderBulkFulfill(BaseBulkMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of orders IDs to fulfill."
        )

    class Meta:
        description = "Fulfill orders."
        model = models.Order
        object_type = Order
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def bulk_action(cls, info: ResolveInfo, queryset, /) -> None:

        manager = get_plugin_manager_promise(info.context).get()
        for order in queryset:
            if order.status == models.OrderStatus.UNFULFILLED or order.status == models.OrderStatus.PARTIALLY_FULFILLED:
                warehouses = get_warehouses_for_order(order)
                if not warehouses:
                    raise ValueError("No warehouse available for fulfilling the order.")

                for warehouse_pk in warehouses:
                    unfulfilled_lines = [
                        {
                            "order_line": line,
                            "quantity": line.quantity_unfulfilled
                        } for line in order.lines.filter(quantity_fulfilled__lt=models.F("quantity"))
                    ]

                    create_fulfillments(
                        order=order,
                        user=info.context.user,
                        app=get_app_promise(info.context).get(),
                        fulfillment_lines_for_warehouses={warehouse_pk: unfulfilled_lines},
                        manager=manager,
                        site_settings=Site.objects.get_current().settings,
                    )

    @classmethod
    def get_channel_ids(cls, instances) -> Iterable[Union[UUID, int]]:
        """Get the instances channel ids for channel permission accessible check."""
        return [order.channel_id for order in instances]

def get_warehouses_for_order(order):
    warehouses = set()
    for line in order.lines.all():
        for allocation in line.allocations.all():
            warehouses.add(allocation.stock.warehouse.pk)
    return list(warehouses)
