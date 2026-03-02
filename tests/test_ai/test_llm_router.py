import pytest

from ai.llm_router import LLMRouter


@pytest.mark.asyncio
async def test_router_fallback_to_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    router = LLMRouter()

    async def fake_local(*args, **kwargs):
        return "ok"

    router.openai_client = None
    monkeypatch.setattr(router.ollama_client, "complete", fake_local)

    result = await router.route("recommendations", "prompt")
    assert result == "ok"
