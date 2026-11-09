"""Medical-aware document chunking (multi-language SEA)."""

from __future__ import annotations

import re
from typing import Literal, cast
from uuid import uuid4

from .schemas import Chunk, Document

SECTION_PATTERNS = {
    "indications": re.compile(
        r"(indications?|ch[ỉỉ] \u0111[ịị]nh|ข้อบ่งใช้|indikasi)", re.IGNORECASE
    ),
    "dosage": re.compile(r"(dosage|dos(?:a|ing)|liều dùng|ขนาดยา)", re.IGNORECASE),
    "contraindications": re.compile(
        r"(contraindications?|ch[ốố]ng ch[ỉỉ] \u0111[ịị]nh|ข้อห้ามใช้)", re.IGNORECASE
    ),
    "interactions": re.compile(
        r"(drug interactions?|tương tác thu[ốố]c|ปฏิกิริยาระหว่างยา)", re.IGNORECASE
    ),
    "side_effects": re.compile(
        r"(side effects?|tác d[ụụ]ng ph[ụụ]|ผลข้างเคียง)", re.IGNORECASE
    ),
}

ChunkType = Literal[
    "indications",
    "dosage",
    "contraindications",
    "interactions",
    "side_effects",
    "general",
]

MAX_CHUNK_TOKENS = 512
CHUNK_OVERLAP = 50


class MedicalChunker:
    """Domain-aware chunking for pharmaceutical documents."""

    def __init__(
        self, max_tokens: int = MAX_CHUNK_TOKENS, overlap: int = CHUNK_OVERLAP
    ):
        self.max_tokens = max_tokens
        self.overlap = overlap

    def chunk(
        self,
        document: Document,
        strategy: Literal["medical", "semantic", "recursive"] = "medical",
    ) -> list[Chunk]:
        """Chunk document using specified strategy."""
        if strategy == "medical":
            return self._medical_chunking(document)
        elif strategy == "semantic":
            return self._semantic_chunking(document)
        return self._recursive_chunking(document)

    def _medical_chunking(self, document: Document) -> list[Chunk]:
        """Section-aware chunking preserving medical context."""
        chunks: list[Chunk] = []
        current_section: ChunkType | None = None
        current_content: list[str] = []
        chunk_index = 0

        def append_section(section: ChunkType | None, content: list[str]) -> None:
            nonlocal chunk_index
            section_type = section or "general"
            text = "\n".join(content)
            overlap_tokens = min(max(self.overlap, 0), max(self.max_tokens - 1, 0))
            chunk_limit = max(1, self.max_tokens - overlap_tokens)
            parts = self._split_text_to_max_tokens(
                text,
                ["\n\n", "\n", ". ", " ", ""],
                max_tokens=chunk_limit,
            )
            for index, part in enumerate(parts):
                if index and overlap_tokens:
                    overlap_text = parts[index - 1][-overlap_tokens * 4 :]
                    if " " in overlap_text:
                        overlap_text = overlap_text.split(" ", 1)[1]
                    part = overlap_text + part
                chunk = self._create_chunk(document, part, section_type, chunk_index)
                if chunk:
                    chunks.append(chunk)
                    chunk_index += 1

        for line in document.content.split("\n"):
            section_type = self._detect_section(line)

            if section_type and section_type != current_section:
                if current_content:
                    append_section(current_section, current_content)
                current_section = section_type
                current_content = [line]
            else:
                current_content.append(line)

        if current_content:
            append_section(current_section, current_content)

        return chunks

    def _semantic_chunking(self, document: Document) -> list[Chunk]:
        """Semantic chunking using sentence boundaries."""
        sentences = self._split_sentences(document.content)
        chunks: list[Chunk] = []
        current_sentences: list[str] = []
        current_tokens = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_tokens = self._count_tokens(sentence)
            if current_tokens + sentence_tokens > self.max_tokens and current_sentences:
                chunk = self._create_chunk(
                    document,
                    " ".join(current_sentences),
                    self._classify_content(" ".join(current_sentences)),
                    chunk_index,
                )
                if chunk:
                    chunks.append(chunk)
                    chunk_index += 1
                current_sentences, current_tokens = self._get_overlap(current_sentences)

            current_sentences.append(sentence)
            current_tokens += sentence_tokens

        if current_sentences:
            chunk = self._create_chunk(
                document,
                " ".join(current_sentences),
                self._classify_content(" ".join(current_sentences)),
                chunk_index,
            )
            if chunk:
                chunks.append(chunk)

        return chunks

    def _recursive_chunking(self, document: Document) -> list[Chunk]:
        """Fallback: recursive character split."""
        separators = ["\n\n", "\n", ". ", " ", ""]
        return self._recursive_split(document.content, separators, document)

    def _recursive_split(
        self, text: str, separators: list[str], document: Document
    ) -> list[Chunk]:
        chunks: list[Chunk] = []
        for chunk_index, part in enumerate(
            self._split_text_to_max_tokens(text, separators)
        ):
            chunk = self._create_chunk(document, part, "general", chunk_index)
            if chunk:
                chunks.append(chunk)
        return chunks

    def _split_text_to_max_tokens(
        self,
        text: str,
        separators: list[str],
        max_tokens: int | None = None,
    ) -> list[str]:
        token_limit = max_tokens or self.max_tokens

        def split(value: str, separator_index: int = 0) -> list[str]:
            if self._count_tokens(value) <= token_limit:
                return [value]

            for index in range(separator_index, len(separators)):
                separator = separators[index]
                if separator:
                    if separator not in value:
                        continue
                    raw_parts = value.split(separator)
                    parts = [
                        *(part + separator for part in raw_parts[:-1]),
                        raw_parts[-1],
                    ]
                else:
                    width = max(1, token_limit * 4)
                    parts = [value[i : i + width] for i in range(0, len(value), width)]

                result: list[str] = []
                current: list[str] = []

                def append_current() -> None:
                    if current:
                        result.append("".join(current))
                        current.clear()

                for part in parts:
                    if not part:
                        continue
                    if self._count_tokens(part) > token_limit:
                        append_current()
                        result.extend(split(part, index + 1))
                        continue

                    candidate = "".join([*current, part])
                    if current and self._count_tokens(candidate) > token_limit:
                        append_current()
                    current.append(part)

                append_current()
                return result

            width = max(1, token_limit * 4)
            return [value[i : i + width] for i in range(0, len(value), width)]

        return split(text)

    def _detect_section(self, line: str) -> ChunkType | None:
        line = line.strip()
        if not line or len(line) > 100:
            return None
        for section_type, pattern in SECTION_PATTERNS.items():
            if pattern.search(line):
                return cast(ChunkType, section_type)
        return None

    def _classify_content(self, content: str) -> ChunkType:
        for section_type, pattern in SECTION_PATTERNS.items():
            if pattern.search(content.lower()):
                return cast(ChunkType, section_type)
        return "general"

    def _split_sentences(self, text: str) -> list[str]:
        pattern = r"(?<=[.!?។])\s+(?=[A-ZА-Я\u0400-\u04FF\u1000-\u109F])"
        return [s.strip() for s in re.split(pattern, text) if s.strip()]

    def _create_chunk(
        self,
        document: Document,
        content: str,
        chunk_type: Literal[
            "indications",
            "dosage",
            "contraindications",
            "interactions",
            "side_effects",
            "general",
        ],
        chunk_index: int,
    ) -> Chunk | None:
        content = content.strip()
        if not content or len(content) < 10:
            return None
        return Chunk(
            id=uuid4(),
            document_id=document.id,
            content=content,
            chunk_index=chunk_index,
            chunk_type=chunk_type,
            metadata={
                **document.metadata,
                "source": document.source,
                "doc_type": document.doc_type,
                "country": document.country,
                "language": document.language,
            },
            token_count=self._count_tokens(content),
        )

    def _get_overlap(self, sentences: list[str]) -> tuple[list[str], int]:
        overlap_sentences: list[str] = []
        overlap_tokens = 0
        for s in reversed(sentences):
            t = self._count_tokens(s)
            if overlap_tokens + t > self.overlap:
                break
            overlap_sentences.insert(0, s)
            overlap_tokens += t
        return overlap_sentences, overlap_tokens

    @staticmethod
    def _count_tokens(text: str) -> int:
        return len(text) // 4
