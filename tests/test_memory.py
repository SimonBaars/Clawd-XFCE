from clippy_xfce.agent.memory import MemoryStore, first_text, primary_text


def test_conversation_and_memory(tmp_path):
    store = MemoryStore(tmp_path / "mem.db")
    convo = store.create_conversation("New chat")
    store.add_message(convo.id, "user", [{"type": "text", "text": "Help me with Thunar"}])
    store.add_message(convo.id, "assistant", "Sure, let's look at the file manager.")
    loaded = store.messages(convo.id)
    assert loaded[0]["role"] == "user"
    assert "Thunar" in first_text(loaded[0]["content"])
    renamed = store.get_conversation(convo.id)
    assert "Thunar" in renamed.title

    store.remember("Uses XFCE on Arch", "fact", 3)
    store.remember("Prefers short answers", "preference")
    hits = store.search_memories("XFCE")
    assert hits and "Arch" in hits[0].text
    block = store.context_block()
    assert "Uses XFCE on Arch" in block


def test_summaries(tmp_path):
    store = MemoryStore(tmp_path / "mem.db")
    one = store.create_conversation("Mail")
    store.set_summary(one.id, "Helped file an expense report")
    two = store.create_conversation("Now")
    recent = store.recent_summaries(exclude=two.id)
    assert recent[0].summary.startswith("Helped")


def test_primary_text_ignores_desktop_block():
    content = [
        {"type": "text", "text": "Help with Thunar"},
        {"type": "text", "text": "Desktop now:\nUser: simon"},
    ]
    assert primary_text(content) == "Help with Thunar"
    assert first_text(content) == "Help with Thunar"
