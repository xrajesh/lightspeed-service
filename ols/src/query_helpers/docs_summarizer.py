"""A class for summarizing documentation context."""

import logging
from typing import Optional

import llama_index
from llama_index import ServiceContext, StorageContext, load_index_from_storage
from llama_index.prompts import PromptTemplate
from llama_index.chat_engine.condense_question import CondenseQuestionChatEngine
from llama_index.response.schema import Response

from ols import constants
from ols.src.llms.llm_loader import LLMLoader
from ols.src.query_helpers import QueryHelper
from ols.utils import config
from ols.src.query_helpers.chat_history import get_llama_index_chat_history

logger = logging.getLogger(__name__)


class DocsSummarizer(QueryHelper):
    """A class for summarizing documentation context."""

    def summarize(
        self, conversation: str, query: str, history: Optional[str] = None, **kwargs
    ) -> tuple[str, str]:
        """Summarize the given query based on the provided conversation context.

        Args:
            conversation: The unique identifier for the conversation.
            query: The query to be summarized.
            history: The history of the conversation (if available).
            kwargs: Additional keyword arguments for customization (model, verbose, etc.).

        Returns:
            A tuple containing the summary as a string and referenced documents as a string.
        """
        bare_llm = LLMLoader(self.provider, self.model).llm

        verbose = kwargs.get("verbose", "").lower() == "true"

        # Set up llama index to show prompting if verbose is True
        # TODO: remove this, we can't be setting global handlers, it will
        # affect other calls
        if verbose:
            llama_index.set_global_handler("simple")

        settings_string = (
            f"conversation: {conversation}, "
            f"query: {query}, "
            f"provider: {self.provider}, "
            f"model: {self.model}, "
            f"verbose: {verbose}"
        )
        logger.info(f"{conversation} call settings: {settings_string}")

        # TODO: use history there
        logger.info(f"History:  {history}")
        chat_history=get_llama_index_chat_history(history)
        logger.info(f"Chat history:  {history}")
        summarization_template = PromptTemplate(constants.SUMMARIZATION_TEMPLATE)

        logger.info(f"{conversation} Getting service context")

        embed_model = "local:BAAI/bge-base-en"

        service_context = ServiceContext.from_defaults(
            chunk_size=1024, llm=bare_llm, embed_model=embed_model, **kwargs
        )

        logger.info(
            f"{conversation} using embed model: {service_context.embed_model!s}"
        )

        # TODO get this from global config
        if (
            config.ols_config.reference_content is not None
            and config.ols_config.reference_content.product_docs_index_path is not None
        ):
            use_llm_without_reference_content = False
            try:
                storage_context = StorageContext.from_defaults(
                    persist_dir=config.ols_config.reference_content.product_docs_index_path
                )
                logger.info(f"{conversation} Setting up index")
                index = load_index_from_storage(
                    storage_context=storage_context,
                    service_context=service_context,
                    index_id=config.ols_config.reference_content.product_docs_index_id,
                    verbose=verbose,
                )
                logger.info(f"{conversation} Setting up query engine")

                logger.info(f"{conversation} Submitting summarization query")

                chat_engine=index.as_chat_engine(
                    service_context=service_context,
                    chat_history=chat_history,
                    chat_mode="context",
                    system_prompt=summarization_template,
                )
                summary=chat_engine.chat(query)

                referenced_documents = "\n".join(
                    [
                        source_node.node.metadata["file_name"]
                        for source_node in summary.source_nodes
                    ]
                )
            except Exception as err:
                logger.error(f"Error loading vector index: {err}")
                use_llm_without_reference_content = True
        else:
            logger.info("Reference content is not configured")
            use_llm_without_reference_content = True

        if use_llm_without_reference_content:
            logger.info("Using llm to answer the query without reference content")
            response = bare_llm.invoke(query)
            summary = Response(
                f""" The following response was generated without access to reference content:
                        {response}
                    """
            )
            referenced_documents = ""

        logger.info(f"{conversation} Summary response: {summary!s}")
        logger.info(f"{conversation} Referenced documents: {referenced_documents}")

        return str(summary), referenced_documents
