"""Built-in LLM tools for skill discovery (search_skills, fetch_skill)."""

import logging

from langchain_core.tools.structured import StructuredTool
from pydantic import BaseModel, Field

from ols.src.skills.skill_loader import SkillRegistry, load_skill_content

logger = logging.getLogger(__name__)


class SearchSkillsInput(BaseModel):
    """Input schema for the search_skills tool."""

    query: str = Field(description="Free-text search query to find relevant skills")


class FetchSkillInput(BaseModel):
    """Input schema for the fetch_skill tool."""

    skill_name: str = Field(description="Exact name of the skill to fetch")


def _search_skills(query: str, registry: SkillRegistry) -> str:
    """Search the skill registry and return matching entries."""
    results = registry.search(query)
    if not results:
        return "No matching skills found."
    return "\n".join(f"- {e.name}: {e.description}" for e in results)


def _fetch_skill(skill_name: str, registry: SkillRegistry) -> str:
    """Fetch the full SKILL.md content for a given skill name."""
    entry = registry.get(skill_name)
    if entry is None:
        return f"Skill '{skill_name}' not found. Use search_skills to find available skills."
    return load_skill_content(entry)


def create_skill_tools(registry: SkillRegistry) -> list[StructuredTool]:
    """Create the search_skills and fetch_skill LangChain tools.

    These tools are always bound to the LLM so it can progressively
    discover domain-specific instructions on demand.
    """
    if not registry.entries:
        return []

    skill_index = registry.to_index_string()

    search_tool = StructuredTool.from_function(
        func=lambda query: _search_skills(query, registry),
        name="search_skills",
        description=(
            "Search for relevant troubleshooting or operational skills. "
            "Returns matching skill names and descriptions. "
            "Use this when the user's question might benefit from "
            "step-by-step domain-specific instructions.\n"
            f"Available skills:\n{skill_index}"
        ),
        args_schema=SearchSkillsInput,
    )

    fetch_tool = StructuredTool.from_function(
        func=lambda skill_name: _fetch_skill(skill_name, registry),
        name="fetch_skill",
        description=(
            "Fetch the full step-by-step instructions for a skill by name. "
            "Call this after search_skills finds a relevant skill. "
            "The instructions will guide you through the troubleshooting process."
        ),
        args_schema=FetchSkillInput,
    )
    return [search_tool, fetch_tool]
