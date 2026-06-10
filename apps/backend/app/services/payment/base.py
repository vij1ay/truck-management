from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class PaymentResult:
    success: bool
    reference_no: str
    message: str
    gateway_data: dict = field(default_factory=dict)


class PaymentGateway(ABC):
    """Abstract payment gateway — implement for each provider."""

    @abstractmethod
    def process_payment(
        self,
        amount: Decimal,
        invoice_no: str,
        metadata: dict,
    ) -> PaymentResult: ...
