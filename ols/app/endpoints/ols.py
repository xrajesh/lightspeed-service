"""Handlers for all OLS-related REST API endpoints."""

import logging

from fastapi import APIRouter, HTTPException, status
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

from ols import constants
from ols.app.models.models import LLMRequest
from ols.app.utils import Utils
from ols.src.llms.llm_loader import LLMLoader
from ols.src.query_helpers.docs_summarizer import DocsSummarizer
from ols.src.query_helpers.question_validator import QuestionValidator
from ols.src.query_helpers.yaml_generator import YamlGenerator
from ols.utils import config

logger = logging.getLogger(__name__)

router = APIRouter(tags=["query"])


@router.post("/query")
def conversation_request(llm_request: LLMRequest) -> LLMRequest:
    """Handle conversation requests for the OLS endpoint.

    Args:
        llm_request: The request containing a query and conversation ID.

    Returns:
        Response containing the processed information.
    """
    # Initialize variables
    previous_input = None
    conversation = llm_request.conversation_id

    # Generate a new conversation ID if not provided
    if conversation is None:
        conversation = Utils.get_suid()
        logger.info(f"{conversation} New conversation")
    else:
        previous_input = config.conversation_cache.get(conversation)
        logger.info(f"{conversation} Previous conversation input: {previous_input}")

    llm_response = LLMRequest(query=llm_request.query, conversation_id=conversation)

    # Log incoming request
    logger.info(f"{conversation} Incoming request: {llm_request.query}")

    # Validate the query
    question_validator = QuestionValidator()
    try:
        validation_result = question_validator.validate_question(
            conversation, llm_request.query
        )
    except Exception as validation_error:
        logger.error("Error while validating question")
        logger.error(validation_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while validating question",
        )

    validation = validation_result[0]
    question_type = validation_result[1]

    match (validation, question_type):
        case (constants.SUBJECT_INVALID, _):
            logger.info(
                f"{conversation} - Query is not relevant to kubernetes or ocp, returning"
            )
            llm_response.response = str(
                {
                    "detail": {
                        "response": "I can only answer questions about \
            OpenShift and Kubernetes. Please rephrase your question"
                    }
                }
            )
        case (constants.SUBJECT_VALID, constants.CATEGORY_GENERIC):
            logger.info(
                f"{conversation} - Question is not about yaml, sending for generic info"
            )
            # Summarize documentation
            docs_summarizer = DocsSummarizer()
            try:
                llm_response.response, _ = docs_summarizer.summarize(
                    conversation, llm_request.query
                )
            except Exception as summarizer_error:
                logger.error("Error while obtaining answer for user question")
                logger.error(summarizer_error)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error while obtaining answer for user question",
                )
        case (constants.SUBJECT_VALID, constants.CATEGORY_YAML):
            logger.info(
                f"{conversation} - Question is about yaml, sending to the YAML generator"
            )
            yaml_generator = YamlGenerator()
            try:
                generated_yaml = yaml_generator.generate_yaml(
                    conversation, llm_request.query, previous_input
                )
            except Exception as yamlgenerator_error:
                logger.error("Error while obtaining yaml for user question")
                logger.error(yamlgenerator_error)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error while obtaining answer for user question",
                )
            llm_response.response = generated_yaml
        case (constants.SUBJECT_VALID, constants.CATEGORY_UNKNOWN):
            logger.info(
                f"{conversation} - Query is relevant, but cannot identify the intent"
            )
            llm_response.response = str(
                {
                    "detail": {
                        "response": "Question does not provide enough context, \
                Please rephrase your question or provide more detail"
                    }
                }
            )

    if config.conversation_cache is not None:
        config.conversation_cache.insert_or_append(
            conversation,
            llm_request.query + "\n\n" + str(llm_response.response or ""),
        )
    return llm_response


@router.post("/debug/query")
def conversation_request_debug_api(llm_request: LLMRequest) -> LLMRequest:
    """Handle requests for the base LLM completion endpoint.

    Args:
        llm_request: The request containing a query.

    Returns:
        Response containing the processed information.
    """
    if llm_request.conversation_id is None:
        conversation = Utils.get_suid()
    else:
        conversation = llm_request.conversation_id

    llm_response = LLMRequest(query=llm_request.query)
    llm_response.conversation_id = conversation

    logger.info(f"{conversation} New conversation")
    logger.info(f"{conversation} Incoming request: {llm_request.query}")

    bare_llm = LLMLoader(
        config.ols_config.default_provider,
        config.ols_config.default_model,
    ).llm

    prompt = PromptTemplate.from_template("{query}")
    llm_chain = LLMChain(llm=bare_llm, prompt=prompt, verbose=True)
    response = llm_chain(inputs={"query": llm_request.query})

    logger.info(f"{conversation} Model returned: {response}")

    llm_response.response = response["text"]

    return llm_response
