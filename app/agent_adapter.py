from typing import Any, List


RETRIEVAL_TOOLS = {
    "faiss_retriever",
    "get_marketing_context",
    "search",
    "retriever",
    "retrieval_tool",
}

SOURCE_ALIASES = {
    "docs/product_faq.txt": "doc_product_faq",
    "product_faq.txt": "doc_product_faq",
    "product_faq": "doc_product_faq",
    "docs/return_policy.md": "doc_return_policy",
    "return_policy.md": "doc_return_policy",
    "return_policy": "doc_return_policy",
}


def _dedupe(values: List[str]) -> List[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _stringify_items(items: Any, keys: List[str]) -> List[str]:
    if not isinstance(items, list):
        return []

    values: List[str] = []
    for item in items:
        if isinstance(item, str):
            values.append(item)
        elif isinstance(item, dict):
            value = next((item.get(key) for key in keys if item.get(key)), None)
            values.append(str(value or item))
        else:
            values.append(str(item))
    return values


def normalize_tool_trace(items: Any) -> List[str]:
    tools = _stringify_items(items, ["tool_name", "name", "tool", "id"])
    normalized = []
    for tool in tools:
        normalized.append(tool)
        if tool in RETRIEVAL_TOOLS:
            normalized.append("retrieval")
    return _dedupe(normalized)


def normalize_retrieved_context(items: Any) -> List[str]:
    sources = _stringify_items(items, ["source_id", "source", "document_id", "id", "url"])
    normalized = []
    for source in sources:
        normalized.append(source)
        alias = SOURCE_ALIASES.get(source)
        if alias:
            normalized.append(alias)
    return _dedupe(normalized)
