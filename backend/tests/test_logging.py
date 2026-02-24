"""Tests for structured logging configuration."""

import logging

from app.core.logging import (
    add_request_id,
    generate_request_id,
    request_id_var,
    setup_logging,
)


class TestStructuredLogging:
    def test_setup_logging_development(self):
        setup_logging(environment="development")
        root = logging.getLogger()
        assert len(root.handlers) >= 1

    def test_setup_logging_production(self):
        setup_logging(environment="production")
        root = logging.getLogger()
        assert len(root.handlers) >= 1

    def test_generate_request_id(self):
        rid = generate_request_id()
        assert isinstance(rid, str)
        assert len(rid) == 12

    def test_add_request_id_with_context(self):
        token = request_id_var.set("test-req-123")
        try:
            event_dict = {}
            result = add_request_id(None, None, event_dict)
            assert result["request_id"] == "test-req-123"
        finally:
            request_id_var.reset(token)

    def test_add_request_id_without_context(self):
        token = request_id_var.set(None)
        try:
            event_dict = {}
            result = add_request_id(None, None, event_dict)
            assert "request_id" not in result
        finally:
            request_id_var.reset(token)
