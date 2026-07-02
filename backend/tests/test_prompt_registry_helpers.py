from app.llm.base import Message
from app.llm.prompt_registry import render_prompt_with_user_message


def test_render_prompt_with_user_message_appends_user_turn():
    messages = render_prompt_with_user_message("general_chat", "hello")
    assert messages[-1].role == "user"
    assert messages[-1].content == "hello"
    assert messages[0].role == "system"


def test_render_prompt_with_user_message_places_history_between_system_and_user():
    history = [Message(role="user", content="earlier question"), Message(role="assistant", content="earlier answer")]
    messages = render_prompt_with_user_message("general_chat", "latest question", history=history)

    assert messages[0].role == "system"
    assert messages[1].content == "earlier question"
    assert messages[2].content == "earlier answer"
    assert messages[-1].role == "user"
    assert messages[-1].content == "latest question"
    assert len(messages) == 4


def test_render_prompt_with_user_message_no_history_is_just_system_and_user():
    messages = render_prompt_with_user_message("query_rewrite", "some content")
    assert len(messages) == 2
    assert messages[0].role == "system"
    assert messages[1].role == "user"


def test_render_prompt_with_user_message_empty_history_list_behaves_like_none():
    messages = render_prompt_with_user_message("general_chat", "hi", history=[])
    assert len(messages) == 2
