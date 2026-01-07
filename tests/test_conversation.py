"""Tests for conversation storage."""

import tempfile
from pathlib import Path
from unittest import mock

import pytest

from orcx import conversation
from orcx.schema import Message


@pytest.fixture
def temp_db():
    """Use temporary database for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        with mock.patch.object(conversation, "DB_PATH", db_path):
            yield db_path


class TestCreateConversation:
    def test_creates_with_id(self, temp_db):
        conv = conversation.create(model="test/model")
        assert len(conv.id) == 4
        assert conv.model == "test/model"
        assert conv.messages == []

    def test_creates_with_agent(self, temp_db):
        conv = conversation.create(model="test/model", agent="test-agent")
        assert conv.agent == "test-agent"


class TestGetConversation:
    def test_get_existing(self, temp_db):
        created = conversation.create(model="test/model")
        fetched = conversation.get(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.model == created.model

    def test_get_missing(self, temp_db):
        result = conversation.get("xxxx")
        assert result is None


class TestGetLast:
    def test_get_last_returns_most_recent(self, temp_db):
        conversation.create(model="model1")
        conv2 = conversation.create(model="model2")
        last = conversation.get_last()
        assert last is not None
        assert last.id == conv2.id

    def test_get_last_empty(self, temp_db):
        result = conversation.get_last()
        assert result is None


class TestUpdateConversation:
    def test_update_messages(self, temp_db):
        conv = conversation.create(model="test/model")
        conv.messages.append(Message(role="user", content="hello"))
        conv.messages.append(Message(role="assistant", content="hi"))
        conversation.update(conv)

        fetched = conversation.get(conv.id)
        assert fetched is not None
        assert len(fetched.messages) == 2
        assert fetched.messages[0].content == "hello"

    def test_update_tokens_and_cost(self, temp_db):
        conv = conversation.create(model="test/model")
        conv.total_tokens = 100
        conv.total_cost = 0.001
        conversation.update(conv)

        fetched = conversation.get(conv.id)
        assert fetched is not None
        assert fetched.total_tokens == 100
        assert fetched.total_cost == 0.001


class TestListRecent:
    def test_list_returns_recent(self, temp_db):
        for i in range(5):
            conversation.create(model=f"model{i}")
        result = conversation.list_recent(limit=3)
        assert len(result) == 3

    def test_list_empty(self, temp_db):
        result = conversation.list_recent()
        assert result == []


class TestDelete:
    def test_delete_existing(self, temp_db):
        conv = conversation.create(model="test/model")
        assert conversation.delete(conv.id) is True
        assert conversation.get(conv.id) is None

    def test_delete_missing(self, temp_db):
        assert conversation.delete("xxxx") is False


class TestClean:
    def test_clean_deletes_old_conversations(self, temp_db):
        conv = conversation.create(model="test/model")
        # Manually backdate the conversation
        with conversation._connect() as conn:
            conn.execute(
                "UPDATE conversations SET updated_at = datetime('now', '-60 days') WHERE id = ?",
                (conv.id,),
            )
        # Clean conversations older than 30 days
        count = conversation.clean(days=30)
        assert count == 1
        assert conversation.get(conv.id) is None

    def test_clean_keeps_recent_conversations(self, temp_db):
        conv = conversation.create(model="test/model")
        count = conversation.clean(days=30)
        assert count == 0
        assert conversation.get(conv.id) is not None

    def test_clean_respects_days_parameter(self, temp_db):
        conv = conversation.create(model="test/model")
        # Backdate to 10 days ago
        with conversation._connect() as conn:
            conn.execute(
                "UPDATE conversations SET updated_at = datetime('now', '-10 days') WHERE id = ?",
                (conv.id,),
            )
        # Should not delete (10 < 30)
        assert conversation.clean(days=30) == 0
        # Should delete (10 > 5)
        assert conversation.clean(days=5) == 1
