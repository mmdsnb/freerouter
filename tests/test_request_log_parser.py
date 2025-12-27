"""
Unit tests for request_log_parser module
"""
import pytest
from freerouter.cli.request_log_parser import (
    RequestLogParser, APIRequest, APIResponse, LogStreamFilter
)


class TestURLExtraction:
    """Test URL extraction and completion logic"""

    def test_extract_url_completes_v1_endpoint(self):
        """Test that /v1/ URLs get /chat/completions appended"""
        curl_text = "curl -X POST \\\nhttps://api.xiaomimomo.com/v1/ \\\n"
        url = RequestLogParser.extract_url(curl_text)
        assert url == "https://api.xiaomimomo.com/v1/chat/completions"

    def test_extract_url_completes_v1_without_trailing_slash(self):
        """Test that /v1 URLs (no trailing slash) get /chat/completions appended"""
        curl_text = "curl -X POST \\\nhttps://api.xiaomimomo.com/v1 \\\n"
        url = RequestLogParser.extract_url(curl_text)
        assert url == "https://api.xiaomimomo.com/v1/chat/completions"

    def test_extract_url_handles_complete_url(self):
        """Test that complete URLs are not modified"""
        curl_text = "curl -X POST \\\nhttps://api.test.com/v1/chat/completions \\\n"
        url = RequestLogParser.extract_url(curl_text)
        assert url == "https://api.test.com/v1/chat/completions"

    def test_extract_url_handles_different_endpoint(self):
        """Test URLs with different endpoints"""
        curl_text = "curl -X POST \\\nhttps://api.test.com/v1/models \\\n"
        url = RequestLogParser.extract_url(curl_text)
        assert url == "https://api.test.com/v1/models"

    def test_extract_url_returns_none_for_invalid(self):
        """Test that invalid curl text returns None"""
        curl_text = "some random text"
        url = RequestLogParser.extract_url(curl_text)
        assert url is None


class TestRequestBodyExtraction:
    """Test request body parsing"""

    def test_extract_request_body_valid(self):
        """Test parsing valid request body"""
        body_str = "{'model': 'mimo-v2-flash', 'messages': [{'role': 'user', 'content': 'hi'}]}"
        body = RequestLogParser.extract_request_body(body_str)
        assert body is not None
        assert body['model'] == 'mimo-v2-flash'
        assert len(body['messages']) == 1
        assert body['messages'][0]['role'] == 'user'

    def test_extract_request_body_removes_empty_extra_body(self):
        """Test that empty extra_body field is removed"""
        body_str = "{'model': 'test', 'extra_body': {}}"
        body = RequestLogParser.extract_request_body(body_str)
        assert body is not None
        assert 'extra_body' not in body

    def test_extract_request_body_keeps_non_empty_extra_body(self):
        """Test that non-empty extra_body is kept"""
        body_str = "{'model': 'test', 'extra_body': {'key': 'value'}}"
        body = RequestLogParser.extract_request_body(body_str)
        assert body is not None
        assert 'extra_body' in body
        assert body['extra_body']['key'] == 'value'

    def test_extract_request_body_handles_boolean_conversion(self):
        """Test that Python True/False are converted to JSON true/false"""
        body_str = "{'stream': True, 'echo': False}"
        body = RequestLogParser.extract_request_body(body_str)
        assert body is not None
        assert body['stream'] is True
        assert body['echo'] is False

    def test_extract_request_body_returns_none_for_invalid(self):
        """Test that invalid JSON returns None"""
        body_str = "{'invalid: json"
        body = RequestLogParser.extract_request_body(body_str)
        assert body is None


class TestRequestParsing:
    """Test API request parsing"""

    def test_parse_request_with_valid_log(self):
        """Test parsing valid request log chunk"""
        log_chunk = """14:23:45 POST Request Sent from LiteLLM:
curl -X POST \\
https://api.xiaomimomo.com/v1/ \\
-H 'Authorization: sk-test' \\
-d '{'model': 'mimo-v2-flash', 'messages': [{'role': 'user', 'content': 'hi'}]}'
"""
        request = RequestLogParser.parse_request(log_chunk)
        assert request is not None
        assert request.timestamp == "14:23:45"
        assert request.url == "https://api.xiaomimomo.com/v1/chat/completions"
        assert request.method == "POST"
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == "Bearer sk-test"
        assert request.body['model'] == 'mimo-v2-flash'

    def test_parse_request_with_no_url(self):
        """Test that request without URL returns None"""
        log_chunk = "Some random log line"
        request = RequestLogParser.parse_request(log_chunk)
        assert request is None

    def test_parse_request_uses_current_time_if_no_timestamp(self):
        """Test that missing timestamp uses current time"""
        log_chunk = """POST Request Sent from LiteLLM:
curl -X POST \\
https://api.test.com/v1/ \\
-H 'Authorization: sk-test' \\
-d '{'model': 'test'}'
"""
        request = RequestLogParser.parse_request(log_chunk)
        assert request is not None
        # Should have some timestamp (format HH:MM:SS)
        assert ":" in request.timestamp
        assert len(request.timestamp.split(":")) == 3


class TestResponseParsing:
    """Test API response parsing"""

    def test_parse_response_with_valid_log(self):
        """Test parsing valid response log chunk"""
        log_chunk = """14:23:46 RAW RESPONSE: {"id":"test123","created":1766858165,"model":"mimo-v2-flash","object":"chat.completion","choices":[{"finish_reason":"length","index":0,"message":{"content":"Hello! How can I help you today?","role":"assistant"}}],"usage":{"completion_tokens":10,"prompt_tokens":28,"total_tokens":38}}
"""
        response = RequestLogParser.parse_response(log_chunk)
        assert response is not None
        assert response.timestamp == "14:23:46"
        assert response.status_code == 200
        assert response.data['id'] == 'test123'
        assert response.data['model'] == 'mimo-v2-flash'

    def test_parse_response_with_no_json(self):
        """Test that response without JSON returns None"""
        log_chunk = "Some random log line"
        response = RequestLogParser.parse_response(log_chunk)
        assert response is None

    def test_parse_response_with_invalid_json(self):
        """Test that invalid JSON returns None"""
        log_chunk = "14:23:46 RAW RESPONSE: {invalid json}"
        response = RequestLogParser.parse_response(log_chunk)
        assert response is None


class TestLogMarkerDetection:
    """Test log marker detection helpers"""

    def test_is_request_log_positive(self):
        """Test detecting request log marker"""
        line = "14:23:45 POST Request Sent from LiteLLM:"
        assert RequestLogParser.is_request_log(line) is True

    def test_is_request_log_negative(self):
        """Test not detecting request on other lines"""
        line = "Some other log line"
        assert RequestLogParser.is_request_log(line) is False

    def test_is_response_log_positive(self):
        """Test detecting response log marker"""
        line = "14:23:46 RAW RESPONSE: {}"
        assert RequestLogParser.is_response_log(line) is True

    def test_is_response_log_negative(self):
        """Test not detecting response on other lines"""
        line = "Some other log line"
        assert RequestLogParser.is_response_log(line) is False


class TestAPIRequestFormatting:
    """Test APIRequest.format() method"""

    def test_format_request_with_color(self):
        """Test formatting request with ANSI color codes"""
        request = APIRequest(
            timestamp="14:23:45",
            method="POST",
            url="https://api.test.com/v1/chat/completions",
            headers={"Authorization": "Bearer sk-test"},
            body={"model": "test-model", "messages": []}
        )
        formatted = request.format(with_color=True)
        assert "🚀 REQUEST" in formatted
        assert "14:23:45" in formatted
        assert "POST" in formatted
        assert "https://api.test.com/v1/chat/completions" in formatted
        assert "Authorization" in formatted
        assert "test-model" in formatted
        # Check for ANSI codes
        assert "\033[" in formatted

    def test_format_request_without_color(self):
        """Test formatting request without ANSI color codes"""
        request = APIRequest(
            timestamp="14:23:45",
            method="POST",
            url="https://api.test.com/v1/chat/completions",
            headers={},
            body={}
        )
        formatted = request.format(with_color=False)
        assert "🚀 REQUEST" in formatted
        # Should not have ANSI codes
        assert "\033[" not in formatted


class TestAPIResponseFormatting:
    """Test APIResponse.format() method"""

    def test_format_response_with_content(self):
        """Test formatting response with message content"""
        response = APIResponse(
            timestamp="14:23:46",
            status_code=200,
            duration_ms=150,
            data={
                "id": "test123",
                "model": "mimo-v2-flash",
                "choices": [{
                    "message": {
                        "content": "Hello! How can I help you today?"
                    }
                }],
                "usage": {
                    "prompt_tokens": 28,
                    "completion_tokens": 10,
                    "total_tokens": 38
                }
            }
        )
        formatted = response.format(with_color=True)
        assert "📥 RESPONSE" in formatted
        assert "14:23:46" in formatted
        assert "200 OK" in formatted
        assert "150ms" in formatted
        assert "Model: mimo-v2-flash" in formatted
        assert "ID: test123" in formatted
        assert "Hello! How can I help you today?" in formatted
        assert "prompt=28" in formatted
        assert "completion=10" in formatted
        assert "total=38" in formatted

    def test_format_response_without_color(self):
        """Test formatting response without ANSI color codes"""
        response = APIResponse(
            timestamp="14:23:46",
            status_code=200,
            duration_ms=None,
            data={"model": "test"}
        )
        formatted = response.format(with_color=False)
        assert "📥 RESPONSE" in formatted
        # Should not have ANSI codes
        assert "\033[" not in formatted

    def test_format_response_minimal_data(self):
        """Test formatting response with minimal data"""
        response = APIResponse(
            timestamp="14:23:46",
            status_code=None,
            duration_ms=None,
            data={}
        )
        formatted = response.format(with_color=False)
        assert "📥 RESPONSE" in formatted
        assert "14:23:46" in formatted


class TestLogStreamFilter:
    """Test LogStreamFilter class"""

    def test_filter_initialization(self):
        """Test filter initializes correctly"""
        log_filter = LogStreamFilter()
        assert log_filter.buffer == ""
        assert log_filter.in_request is False
        assert log_filter.in_response is False

    def test_filter_detects_request_start(self):
        """Test filter detects request log start"""
        log_filter = LogStreamFilter()
        line = "14:23:45 POST Request Sent from LiteLLM:"
        result = log_filter.process_line(line)
        assert result is None  # Not complete yet
        assert log_filter.in_request is True
        assert log_filter.buffer == line

    def test_filter_detects_response_start(self):
        """Test filter detects response log start"""
        log_filter = LogStreamFilter()
        line = "14:23:46 RAW RESPONSE: {"
        result = log_filter.process_line(line)
        assert result is None  # Not complete yet
        assert log_filter.in_response is True
        assert log_filter.buffer == line

    def test_filter_completes_request(self):
        """Test filter returns formatted request when complete"""
        log_filter = LogStreamFilter()

        # Start request
        log_filter.process_line("14:23:45 POST Request Sent from LiteLLM:\n")
        log_filter.process_line("curl -X POST \\\n")
        log_filter.process_line("https://api.test.com/v1/ \\\n")
        log_filter.process_line("-H 'Authorization: sk-test' \\\n")
        log_filter.process_line("-d '{'model': 'test'}'\n")

        # End with empty line
        result = log_filter.process_line("\n")

        assert result is not None
        assert "🚀 REQUEST" in result
        assert "https://api.test.com/v1/chat/completions" in result
        assert log_filter.in_request is False
        assert log_filter.buffer == ""

    def test_filter_completes_response(self):
        """Test filter returns formatted response when complete"""
        log_filter = LogStreamFilter()

        # Start response
        log_filter.process_line('14:23:46 RAW RESPONSE: {"id":"test","model":"test"}\n')

        # End with empty line
        result = log_filter.process_line("\n")

        assert result is not None
        assert "📥 RESPONSE" in result
        assert log_filter.in_response is False
        assert log_filter.buffer == ""

    def test_filter_ignores_non_request_lines(self):
        """Test filter ignores lines that aren't requests/responses"""
        log_filter = LogStreamFilter()
        result = log_filter.process_line("Some random log line\n")
        assert result is None
        assert log_filter.in_request is False
        assert log_filter.in_response is False

    def test_filter_handles_multiple_entries(self):
        """Test filter can handle multiple request/response pairs"""
        log_filter = LogStreamFilter()

        # First request
        log_filter.process_line("14:23:45 POST Request Sent from LiteLLM:\n")
        log_filter.process_line("curl -X POST \\\n")
        log_filter.process_line("https://api.test.com/v1/ \\\n")
        log_filter.process_line("-H 'Authorization: sk-test' \\\n")
        log_filter.process_line("-d '{'model': 'test1'}'\n")
        result1 = log_filter.process_line("\n")
        assert result1 is not None

        # Second request
        log_filter.process_line("14:23:47 POST Request Sent from LiteLLM:\n")
        log_filter.process_line("curl -X POST \\\n")
        log_filter.process_line("https://api.test.com/v1/ \\\n")
        log_filter.process_line("-H 'Authorization: sk-test' \\\n")
        log_filter.process_line("-d '{'model': 'test2'}'\n")
        result2 = log_filter.process_line("\n")
        assert result2 is not None

        # Both should be valid but different
        assert result1 != result2
