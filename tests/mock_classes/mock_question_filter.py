"""Mocked QuestionFilter."""


class MockQuestionFilter:
    """Mocked chat engine."""

    def __init__(self, *args, **kwargs):
        """Store all provided arguments for later usage."""
        self.args = args
        self.kwargs = kwargs

    def setup():
        """Return summary for given query."""
        return MockQuestionFilter()

    def redact_question(self, question):
        """Return mocked response."""
        return question
