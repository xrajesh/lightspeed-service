"""Class responsible for generating YAML responses to user requests."""

import logging

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

from ols import constants
from ols.src.llms.llm_loader import LLMLoader
from ols.src.query_helpers import QueryHelper

logger = logging.getLogger(__name__)


class YamlGenerator(QueryHelper):
    """This class is responsible for generating YAML responses to user requests."""

    def generate_yaml(
        self, conversation_id: str, query: str, history: str | None = None, **kwargs
    ) -> str:
        """Generate YAML response to a user request.

        Args:
          conversation_id: The identifier for the conversation or task context.
          query: The user request.
          history: The history of the conversation (if available).
          **kwargs: Additional keyword arguments for customization.

        Returns:
            The generated YAML response.
        """
        verbose = kwargs.get("verbose", "").lower() == "true"
        settings_string = (
            f"conversation: {conversation_id}, "
            f"query: {query}, "
            f"provider: {self.provider}, "
            f"model: {self.model}, "
            f"verbose: {verbose}"
        )
        logger.info(f"{conversation_id} call settings: {settings_string}")
        logger.info(f"{conversation_id} using model: {self.model}")

        bare_llm = LLMLoader(self.provider, self.model).llm

        if history:
            prompt_instructions = PromptTemplate.from_template(
                constants.YAML_GENERATOR_WITH_HISTORY_PROMPT_TEMPLATE
            )
            task_query = prompt_instructions.format(query=query, history=history)
        else:
            prompt_instructions = PromptTemplate.from_template(
                constants.YAML_GENERATOR_PROMPT_TEMPLATE
            )
            task_query = prompt_instructions.format(query=query)

        logger.info(f"{conversation_id} task query: {task_query}")
        llm_chain = LLMChain(llm=bare_llm, verbose=verbose, prompt=prompt_instructions)
        response = llm_chain(inputs={"query": query, "history": history})
        logger.info(f"{conversation_id} response:\n{response['text']}")
        return response["text"]
