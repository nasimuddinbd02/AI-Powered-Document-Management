"""
Custom exception handling for the Document Management System.

Provides consistent error response formatting across the API.
"""

import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that wraps DRF's default handler
    with a consistent response envelope.

    Response format:
    {
        "success": false,
        "error": {
            "code": "error_code",
            "message": "Human-readable message",
            "details": { ... }  // optional
        }
    }
    """
    # Convert Django ValidationError to DRF ValidationError
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(detail=exc.message_dict if hasattr(exc, "message_dict") else exc.messages)

    # Call DRF's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        error_payload = {
            "success": False,
            "error": {
                "code": _get_error_code(exc),
                "message": _get_error_message(exc, response),
                "details": _get_error_details(exc, response),
            },
        }
        response.data = error_payload
    else:
        # Unhandled exception — log it and return a generic 500
        logger.exception("Unhandled exception: %s", exc, extra={"context": context})
        error_payload = {
            "success": False,
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected error occurred. Please try again later.",
                "details": None,
            },
        }
        response = Response(error_payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response


def _get_error_code(exc):
    """Derive a machine-readable error code from the exception."""
    if isinstance(exc, Http404):
        return "not_found"
    if isinstance(exc, ValidationError):
        return "validation_error"
    if isinstance(exc, APIException):
        return getattr(exc, "default_code", "api_error")
    return "internal_server_error"


def _get_error_message(exc, response):
    """Get a human-readable error message."""
    if isinstance(exc, Http404):
        return "The requested resource was not found."
    if isinstance(exc, ValidationError):
        return "One or more fields failed validation."
    if isinstance(exc, APIException):
        return str(exc.detail) if isinstance(exc.detail, str) else exc.default_detail
    return "An unexpected error occurred."


def _get_error_details(exc, response):
    """Extract detailed error information when available."""
    if isinstance(exc, ValidationError):
        return response.data if response else None
    if isinstance(exc, APIException) and not isinstance(exc.detail, str):
        return exc.detail
    return None


# =============================================================================
# Custom Exception Classes
# =============================================================================


class DocumentNotFoundError(APIException):
    """Raised when a requested document does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "The requested document was not found."
    default_code = "document_not_found"


class DocumentAccessDeniedError(APIException):
    """Raised when a user lacks permission to access a document."""

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have permission to access this document."
    default_code = "document_access_denied"


class FileTooLargeError(APIException):
    """Raised when an uploaded file exceeds the maximum allowed size."""

    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    default_detail = "The uploaded file exceeds the maximum allowed size."
    default_code = "file_too_large"


class UnsupportedFileTypeError(APIException):
    """Raised when an uploaded file type is not supported."""

    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    default_detail = "The uploaded file type is not supported."
    default_code = "unsupported_file_type"


class AIServiceUnavailableError(APIException):
    """Raised when the AI backend service is unavailable."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "The AI service is currently unavailable. Please try again later."
    default_code = "ai_service_unavailable"


class OCRProcessingError(APIException):
    """Raised when OCR processing fails."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "An error occurred during OCR processing."
    default_code = "ocr_processing_error"
