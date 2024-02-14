
import re
import logging
from ols.utils import config
from collections import namedtuple
constants = []
ip_address_regex = r"(?:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
perfect_word_regex = r"\b(?:fullword)\b"
anywhere_in_word_regex = r"(?:partword)"
url_regex = r"(?:https?://)?(?:www\.)?[\w\.-]+\.\w+"
constants.append(ip_address_regex)
constants.append(perfect_word_regex)
constants.append(anywhere_in_word_regex)
constants.append(url_regex)

logger = logging.getLogger(__name__)

#namedtuple
RegexFilter = namedtuple("RegexFilter", "pattern, name, replace_with_string")



class QuestionFilter:
    def __init__(self, regex_filters):
        self.regex_filters = regex_filters

    @classmethod
    def setup(cls):
        logger.info(f"Question filters : {config.ols_config.question_filters}")
        regex_filters = []
        for filter in config.ols_config.question_filters:
            try:
                pattern = re.compile(filter.regular_expression,flags=re.IGNORECASE)              
                regex_filters.append(RegexFilter(pattern=pattern,name=filter.name,replace_with_string=filter.replace_with_string))   
            except Exception as e:
                logger.error(f"Error while compiling regex {filter.regular_expression}")
                logger.error(e)
        return cls(regex_filters)

    def redact_question(self, question):
        for filter in self.regex_filters:
            question, count = filter.pattern.subn(filter.replace_with_string, question)
            logger.info(f"Number of replacements with filter : {count} {filter[1]}")
        return question

