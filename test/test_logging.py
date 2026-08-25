import logging

from wyrmwood_coffee.logging import (
    RequestContextFilter,
    request_context,
)


def test_request_context_filter_does_not_overwrite_existing_fields(caplog):
    caplog.set_level(logging.DEBUG, logger="wyrmwood_coffee.test_filter")
    filter_logger = logging.getLogger("wyrmwood_coffee.test_filter")
    context_filter = RequestContextFilter()
    filter_logger.addFilter(context_filter)

    token = request_context.set({"path": "/generic", "method": "GET"})
    try:
        filter_logger.debug("specific event", extra={"path": "/specific"})
    finally:
        request_context.reset(token)
        filter_logger.removeFilter(context_filter)

    record = caplog.records[-1]
    assert record.path == "/specific"
    assert record.method == "GET"
