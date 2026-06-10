from app.agent_adapter import normalize_retrieved_context, normalize_tool_trace


def test_normalize_tool_trace_adds_retrieval_alias():
    tools = normalize_tool_trace(["faiss_retriever", "search", "get_marketing_context"])

    assert "faiss_retriever" in tools
    assert "search" in tools
    assert "get_marketing_context" in tools
    assert "retrieval" in tools


def test_normalize_retrieved_context_adds_expected_source_aliases():
    sources = normalize_retrieved_context(["docs/product_faq.txt", "docs/return_policy.md"])

    assert "docs/product_faq.txt" in sources
    assert "docs/return_policy.md" in sources
    assert "doc_product_faq" in sources
    assert "doc_return_policy" in sources
