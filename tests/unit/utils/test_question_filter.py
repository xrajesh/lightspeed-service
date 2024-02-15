"""Unit test for the question filter."""

import re
from unittest import TestCase

from ols.utils.question_filter import QuestionFilter, RegexFilter


class TestQuestionFilter(TestCase):
    """Test the question filter class."""

    def setUp(self):
        """Set up the test."""
        self.regex_filters = [
            RegexFilter(re.compile(r"\b(?:image)\b"), "perfect_word", "REDACTED_image"),
            RegexFilter(
                re.compile(r"(?:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"),
                "ip_address",
                "REDACTED_IP",
            ),
        ]
        self.question_filter = QuestionFilter(self.regex_filters)

    def test_redact_question_image_ip(self):
        """Test redact question with perfect word  and ip."""
        question = (
            "write a deployment yaml for the mongodb image with nodeip as 1.123.0.99"
        )
        redacted_question = self.question_filter.redact_question(question)
        self.assertEqual(
            redacted_question,
            "write a deployment yaml for the mongodb REDACTED_image with nodeip as REDACTED_IP",
        )

    def test_redact_question_mongopart_url_phone(self):
        """Test redact question with partial_word, url and phone number."""
        self.regex_filters = [
            RegexFilter(re.compile(r"(?:mongo)"), "any_string_match", "REDACTED_MONGO"),
            RegexFilter(
                re.compile(r"(?:https?://)?(?:www\.)?[\w\.-]+\.\w+"),
                "url",
                "REDACTED_URL",
            ),
            RegexFilter(
                re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
                "phone_number",
                "REDACTED_PHONE_NUMBER",
            ),
        ]
        self.question_filter = QuestionFilter(self.regex_filters)
        question = "write a deployment yaml for the mongodb image from www.mongodb.com\
            and call me at 123-456-7890"
        redacted_question = self.question_filter.redact_question(question)
        self.assertEqual(
            redacted_question,
            "write a deployment yaml for the REDACTED_MONGOdb image from REDACTED_URL\
            and call me at REDACTED_PHONE_NUMBER",
        )
