class OrderError(Exception):
    """ flutter comic order error"""


class CreateOrderError(OrderError):
    """ flutter comic create order error"""


class EsureOrderError(OrderError):
    """ flutter comic esure order error"""