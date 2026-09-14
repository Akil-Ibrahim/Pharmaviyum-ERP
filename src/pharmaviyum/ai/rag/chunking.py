"""Medical-aware document chunking (multi-language SEA)."""
from __future__ import annotations
import re
from typing import Literal
from uuid import uuid4
from .schemas import Document, Chunk

SECTION_PATTERNS = {
    "indications": re.compile(r"(indications?|ch[ỉỉ] \u0111[ịị]nh|ข้อบ่งใช้|indikasi)", re.IGNORECASE),
    "dosage": re.compile(r"(dosage|dos(?:a|ing)|liều dùng|ขนาดยา)", re.IGNORECASE),
    "contraindications": re.compile(r"(contraindications?|ch[ốố]ng ch[ỉỉ] \u0111[ịị]nh|ข้อห้ามใช้)", re.IGNORECASE),
    "interactions": re.compile(r"(drug interactions?|tương tác thu[ốố]c|ปฏิกิริยาระหว่างยา)", re.IGNORECASE),
    "side_effects": re.compile(r"(side effects?|tác d[ụụ]ng ph[ụụ]|ผลข้างเคียง)", re.IGNORECASE),
}

MAX_CHUNK_TOKENS = 512
CHUNK_OVERLAP = 50


class MedicalChunker:
    """Domain-aware chunking for pharmaceutical documents."""
    
    def __init__(self, max_tokens: int = MAX_CHUNK_TOKENS, overlap: int = CHUNK_OVERLAP):
        self.max_tokens = max_tokens
        self.overlap = overlap
    
    def chunk(self, document: Document, strategy: Literal["medical", "semantic", "recursive"] = "medical") -> list[Chunk]:
        """Chunk document using specified strategy."""
        if strategy == "medical":
            return self._medical_chunking(document)
        elif strategy == "semantic":
            return self._semantic_chunking(document)
        return self._recursive_chunking(document)
    
    def _medical_chunking(self, document: Document) -> list[Chunk]:
        """Section-aware chunking preserving medical context."""
        chunks: list[Chunk] = []
        current_section: str | None = None
        current_content: list[str] = []
        chunk_index = 0
        
        for line in document.content.split("\n"):
            section_type = self._detect_section(line)
            
            if section_type and section_type != current_section:
                if current_section and current_content:
                    chunk = self._create_chunk(document, "\n".join(current_content), current_section, chunk_index)
                    if chunk:
                        chunks.append(chunk)
                        chunk_index += 1
                current_section = section_type
                current_content = [line]
            else:
                current_content.append(line)
                if self._count_tokens("\n".join(current_content)) > self.max_tokens:
                    chunk = self._create_chunk(document, "\n".join(current_content[:-1]), current_section or "general", chunk_index)
                    if chunk:
                        chunks.append(chunk)
                        chunk_index += 1
                    current_content = current_content[-(self.overlap // 10):]
        
        if current_content:
            chunk = self._create_chunk(document, "\n".join(current_content), current_section or "general", chunk_index)
            if chunk:
                chunks.append(chunk)
        
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
                chunk = self._create_chunk(document, " ".join(current_sentences), self._classify_content(" ".join(current_sentences)), chunk_index)
                if chunk:
                    chunks.append(chunk)
                    chunk_index += 1
                current_sentences, current_tokens = self._get_overlap(current_sentences)
            
            current_sentences.append(sentence)
            current_tokens += sentence_tokens
        
        if current_sentences:
            chunk = self._create_chunk(document, " ".join(current_sentences), self._classify_content(" ".join(current_sentences)), chunk_index)
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def _recursive_chunking(self, document: Document) -> list[Chunk]:
        """Fallback: recursive character split."""
        separators = ["\n\n", "\n", ". ", " ", ""]
        return self._recursive_split(document.content, separators, document)
    
    def _recursive_split(self, text: str, separators: list[str], document: Document) -> list[Chunk]:
        if self._count_tokens(text) <= self.max_tokens:
            chunk = self._create_chunk(document, text, "general", 0)
            return [chunk] if chunk else []
        
        separator = separators[0] if separators else ""
        parts = text.split(separator) if separator else [text[i:i + self.max_tokens * 4] for i in range(0, len(text), self.max_tokens * 4)]
        
        chunks: list[Chunk] = []
        current_parts: list[str] = []
        current_tokens = 0
        chunk_index = 0
        
        for part in parts:
            part_tokens = self._count_tokens(part)
            if current_tokens + part_tokens > self.max_tokens and current_parts:
                chunk = self._create_chunk(document, separator.join(current_parts), "general", chunk_index)
                if chunk:
                    chunks.append(chunk)
                    chunk_index += 1
                current_parts, current_tokens = [], 0
            current_parts.append(part)
            current_tokens += part_tokens
        
        if current_parts:
            chunk = self._create_chunk(document, separator.join(current_parts), "general", chunk_index)
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def _detect_section(self, line: str) -> str | None:
        line = line.strip()
        if not line or len(line) > 100:
            return None
        for section_type, pattern in SECTION_PATTERNS.items():
            if pattern.search(line):
                return section_type
        return None
    
    def _classify_content(self, content: str) -> str:
        for section_type, pattern in SECTION_PATTERNS.items():
            if pattern.search(content.lower()):
                return section_type
        return "general"
    
    def _split_sentences(self, text: str) -> list[str]:
        pattern = r'(?<=[.!?។])\s+(?=[A-ZА-Я\u0400-\u04FF\u1000-\u109F])'
        return [s.strip() for s in re.split(pattern, text) if s.strip()]
    
    def _create_chunk(self, document: Document, content: str, chunk_type: str, chunk_index: int) -> Chunk | None:
        content = content.strip()
        if not content or len(content) < 10:
            return None
        return Chunk(
            id=uuid4(),
            document_id=document.id,
            content=content,
            chunk_index=chunk_index,
            chunk_type=chunk_type,  # type: ignore
            metadata={**document.metadata, "source": document.source, "doc_type": document.doc_type, "country": document.country, "language": document.language},
            token_count=self._count_tokens(content),
        )
    
    def _get_overlap(self, sentences: list[str]) -> tuple[list[str], int]:
        overlap_sentences, overlap_tokens = [], 0
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
