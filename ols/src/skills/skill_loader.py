"""Loader and registry for agent skill files (SKILL.md)."""

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ols.constants import SKILL_DESCRIPTION_MAX_LENGTH, SKILL_FILE_NAME

logger = logging.getLogger(__name__)

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_KV_RE = re.compile(r"^(\w[\w-]*):\s*(.+)$", re.MULTILINE)

DEFAULT_SEARCH_THRESHOLD = 0.05
DEFAULT_MAX_RESULTS = 5


@dataclass
class SkillEntry:
    """Lightweight index entry for a single skill."""

    name: str
    description: str
    path: str  # absolute path to SKILL.md


@dataclass
class SkillRegistry:
    """In-memory registry of all discovered skills."""

    entries: list[SkillEntry] = field(default_factory=list)
    _by_name: dict[str, SkillEntry] = field(default_factory=dict, repr=False)
    _vectorizer: Optional[TfidfVectorizer] = field(default=None, repr=False)
    _tfidf_matrix: Optional[np.ndarray] = field(default=None, repr=False)

    def add(self, entry: SkillEntry) -> None:
        """Add a skill entry to the registry."""
        self._by_name[entry.name] = entry
        self.entries.append(entry)

    def build_index(self) -> None:
        """Build the TF-IDF matrix from all registered skill entries."""
        if not self.entries:
            return
        corpus = [f"{e.name} {e.description}" for e in self.entries]
        self._vectorizer = TfidfVectorizer(
            stop_words="english",
            token_pattern=r"(?u)\b\w[\w-]+\b",
        )
        self._tfidf_matrix = self._vectorizer.fit_transform(corpus)
        logger.debug("TF-IDF index built for %d skills", len(self.entries))

    def get(self, name: str) -> SkillEntry | None:
        """Retrieve a skill by its exact name."""
        return self._by_name.get(name)

    def search(
        self,
        query: str,
        max_results: int = DEFAULT_MAX_RESULTS,
        threshold: float = DEFAULT_SEARCH_THRESHOLD,
    ) -> list[SkillEntry]:
        """Rank skills by TF-IDF cosine similarity to the query."""
        if not query.strip() or not self.entries:
            return []

        if self._vectorizer is None or self._tfidf_matrix is None:
            self.build_index()

        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._tfidf_matrix).flatten()

        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [
            self.entries[idx]
            for idx, score in ranked[:max_results]
            if score >= threshold
        ]

    def to_index_string(self) -> str:
        """Return a concise, newline-separated index suitable for an LLM prompt."""
        return "\n".join(
            f"- {e.name}: {e.description}" for e in self.entries
        )


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Extract YAML-style frontmatter key/value pairs from a SKILL.md file."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    return dict(_KV_RE.findall(match.group(1)))


def _load_skill_from_dir(skill_dir: str) -> SkillEntry | None:
    """Attempt to load a single skill from a directory containing SKILL.md."""
    skill_path = os.path.join(skill_dir, SKILL_FILE_NAME)
    if not os.path.isfile(skill_path):
        logger.debug("No %s in %s – skipping", SKILL_FILE_NAME, skill_dir)
        return None

    with open(skill_path, encoding="utf-8") as fh:
        text = fh.read()

    meta = _parse_frontmatter(text)
    name = meta.get("name", os.path.basename(skill_dir))
    description = meta.get("description", "")[:SKILL_DESCRIPTION_MAX_LENGTH]

    if not description:
        logger.warning("Skill %s has no description – it may not be discoverable", name)

    return SkillEntry(name=name, description=description, path=skill_path)


def load_skill_content(entry: SkillEntry) -> str:
    """Read the full content of a skill file (called at fetch time)."""
    with open(entry.path, encoding="utf-8") as fh:
        return fh.read()


def load_skills(directories: list[str]) -> SkillRegistry:
    """Scan directories for skill folders and build an in-memory registry."""
    registry = SkillRegistry()
    for base_dir in directories:
        if not os.path.isdir(base_dir):
            logger.warning("Skill directory does not exist: %s", base_dir)
            continue
        for child in sorted(os.listdir(base_dir)):
            child_path = os.path.join(base_dir, child)
            if not os.path.isdir(child_path):
                continue
            entry = _load_skill_from_dir(child_path)
            if entry is not None:
                registry.add(entry)
                logger.info("Loaded skill: %s (%s)", entry.name, entry.path)

    registry.build_index()
    logger.info("Skill registry: %d skills loaded", len(registry.entries))
    return registry
