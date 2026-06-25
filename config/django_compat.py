import inspect

from django.db import models


def check_constraint(*, condition, name):
    parameters = inspect.signature(models.CheckConstraint).parameters
    if "condition" in parameters:
        return models.CheckConstraint(condition=condition, name=name)
    return models.CheckConstraint(check=condition, name=name)
