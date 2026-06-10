from app.models.invoice import PaymentMethod
from app.services.payment.base import PaymentGateway, PaymentResult
from app.services.payment.dummy_gateway import DummyPaymentGateway


def get_payment_gateway(method: PaymentMethod) -> PaymentGateway:
    """Return the appropriate gateway for the given payment method."""
    # All methods currently route to DummyGateway.
    # Replace specific cases here when real integrations are added.
    return DummyPaymentGateway()


__all__ = ["PaymentGateway", "PaymentResult", "DummyPaymentGateway", "get_payment_gateway"]
