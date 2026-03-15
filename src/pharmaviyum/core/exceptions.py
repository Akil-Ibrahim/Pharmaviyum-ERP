"""Custom application exceptions"""

class APIException(Exception):
    """Base API exception"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class EntityNotFound(APIException):
    """404 - Entity not found"""
    def __init__(self, entity: str, entity_id: str):
        super().__init__(
            f"{entity} with id {entity_id} not found",
            status_code=404
        )


class ValidationError(APIException):
    """422 - Validation error"""
    def __init__(self, message: str):
        super().__init__(message, status_code=422)


class UnauthorizedError(APIException):
    """401 - Unauthorized"""
    def __init__(self):
        super().__init__("Unauthorized", status_code=401)


class ForbiddenError(APIException):
    """403 - Forbidden"""
    def __init__(self):
        super().__init__("Forbidden", status_code=403)


class ConflictError(APIException):
    """409 - Conflict"""
    def __init__(self, message: str):
        super().__init__(message, status_code=409)
