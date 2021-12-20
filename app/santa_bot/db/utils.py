from decimal import Decimal

from tortoise import fields
from tortoise.exceptions import ValidationError
from tortoise.validators import Validator


class PositiveValidator(Validator):
    """
    A validator to validate the given value whether greater than 0 or not.
    """

    def __call__(self, value: Decimal):
        if value is not None and value < 0:
            raise ValidationError(f"Excpected positive value instead of {value}")


class DecimalField(fields.DecimalField):

    def __init__(self, decimal_places=20, max_digits=50, default=0, **kwargs) -> None:
        super().__init__(decimal_places=decimal_places, max_digits=max_digits, **kwargs)
        self.validators.append(PositiveValidator())
        self.default = default
