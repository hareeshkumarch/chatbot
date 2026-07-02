import pytest

from app.connectors.database.sql_connector import SQLConnector


@pytest.fixture
def connector():
    return SQLConnector({"connection_url": "postgresql+asyncpg://user:pass@localhost/db"}, {})


async def test_rejects_non_select_statements(connector):
    with pytest.raises(ValueError):
        await connector.run_readonly_query("DELETE FROM users")


async def test_rejects_insert_disguised_with_whitespace(connector):
    with pytest.raises(ValueError):
        await connector.run_readonly_query("   insert into users values (1)")


async def test_rejects_forbidden_keyword_inside_select(connector):
    with pytest.raises(ValueError):
        await connector.run_readonly_query("SELECT * FROM users; DROP TABLE users;")


async def test_rejects_update_forbidden_keyword(connector):
    with pytest.raises(ValueError):
        await connector.run_readonly_query("SELECT 1; UPDATE accounts SET balance = 0")


@pytest.mark.parametrize("keyword", ["insert", "update", "delete", "drop", "alter", "truncate", "grant", "revoke", "create", "attach", "exec"])
async def test_forbidden_keywords_are_case_insensitive(connector, keyword):
    with pytest.raises(ValueError):
        await connector.run_readonly_query(f"SELECT * FROM t WHERE x = 1 -- {keyword.upper()}")
