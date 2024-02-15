"""A class helps redact the question based on the regex filters provided in the config file."""

import logging
import re
from collections import namedtuple
from typing import Optional

from ols.utils import config

logger = logging.getLogger(__name__)

RegexFilter = namedtuple("RegexFilter", "pattern, name, replace_with_string")


class QuestionFilter:
    """Redact the question based on the regex filters provided in the config file."""

    def __init__(self, regex_filters: Optional[list[RegexFilter]]) -> None:
        """Initialize the class instance."""
        self.regex_filters = regex_filters

    @classmethod
    def setup(cls) -> "QuestionFilter":
        """Set up  the class instance using question_filter found in Config."""
        logger.debug(f"Question filters : {config.ols_config.question_filters}")
        regex_filters: list[RegexFilter] = []
        if not config.ols_config.question_filters:
            return cls(regex_filters)
        for filter in config.ols_config.question_filters:
            try:
                pattern = re.compile(
                    str(filter.regular_expression), flags=re.IGNORECASE
                )
                regex_filters.append(
                    RegexFilter(
                        pattern=pattern,
                        name=filter.name,
                        replace_with_string=filter.replace_with_string,
                    )
                )
            except Exception as e:
                logger.error(f"Error while compiling regex {filter.regular_expression}")
                logger.error(e)
        return cls(regex_filters)

    def redact_question(self, question: str) -> str:
        """Redact the question using regex built."""
        for filter in self.regex_filters:
            question, count = filter.pattern.subn(filter.replace_with_string, question)
            logger.info(f"Replaced: {count} matched with filter : {filter.name}")
        return question
