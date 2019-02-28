class OrderError(Exception):
    """ flutter comic order error"""

class SignOrderError(OrderError):
    """sign order"""

class VerifyOrderError(OrderError):
    """verify order"""

class CreateOrderError(OrderError):
    """ flutter comic create order error"""

class EsureOrderError(OrderError):
    """ flutter comic esure order error"""