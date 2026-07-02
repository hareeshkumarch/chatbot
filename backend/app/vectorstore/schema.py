from dataclasses import dataclass, field


@dataclass
class ChunkPayload:
    tenant_id: str
    document_id: str
    chunk_index: int
    text: str
    source_type: str
    source_uri: str
    title: str
    created_at: str
    page_number: int | None = None
    connector_id: str | None = None
    authority_weight: float = 1.0
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "text": self.text,
            "source_type": self.source_type,
            "source_uri": self.source_uri,
            "title": self.title,
            "created_at": self.created_at,
            "page_number": self.page_number,
            "connector_id": self.connector_id,
            "authority_weight": self.authority_weight,
            **self.extra,
        }


COLLECTION_PREFIX = "tenant_chunks_"


def collection_name(tenant_id: str) -> str:
    return f"{COLLECTION_PREFIX}{tenant_id.replace('-', '')}"
