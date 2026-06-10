import uuid
from decimal import Decimal

from app.services.payment.base import PaymentGateway, PaymentResult


class DummyPaymentGateway(PaymentGateway):
    """Simulated payment gateway — always succeeds. Replace with real gateway later."""

    def process_payment(
        self,
        amount: Decimal,
        invoice_no: str,
        metadata: dict,
    ) -> PaymentResult:
        ref = f"DUMMY-{uuid.uuid4().hex[:8].upper()}"
        return PaymentResult(
            success=True,
            reference_no=ref,
            message=f"Dummy payment of {amount} processed for {invoice_no}",
            gateway_data={"simulated": True, "amount": str(amount), "invoice_no": invoice_no},
        )
