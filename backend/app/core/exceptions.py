class AppError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str, status_code: int | None = None, code: str | None = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class AuthError(AppError):
    status_code = 401
    code = "unauthorized"


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"


class ValidationAppError(AppError):
    status_code = 422
    code = "validation_error"


class ConnectorAuthError(AppError):
    status_code = 424
    code = "connector_auth_failed"


class ProviderUnavailableError(AppError):
    status_code = 503
    code = "provider_unavailable"


class RetrievalEmptyError(AppError):
    status_code = 200
    code = "no_relevant_content"
