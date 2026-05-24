import pytest

from backend.core.workflow.internal.tasks import add_task, list_tasks, update_task


@pytest.mark.asyncio
async def test_add_and_list(db_session):
    result = await add_task(db_session, title="テストタスク")
    assert result["title"] == "テストタスク"
    assert result["status"] == "todo"

    tasks = await list_tasks(db_session)
    assert len(tasks) == 1
    assert tasks[0]["title"] == "テストタスク"


@pytest.mark.asyncio
async def test_update_task(db_session):
    created = await add_task(db_session, title="更新テスト")
    updated = await update_task(db_session, created["id"], status="done")
    assert updated is not None
    assert updated["status"] == "done"


@pytest.mark.asyncio
async def test_update_nonexistent(db_session):
    result = await update_task(db_session, "nonexistent", status="done")
    assert result is None


@pytest.mark.asyncio
async def test_list_by_status(db_session):
    await add_task(db_session, title="タスク1")
    created = await add_task(db_session, title="タスク2")
    await update_task(db_session, created["id"], status="done")

    todo = await list_tasks(db_session, status="todo")
    assert len(todo) == 1
    done = await list_tasks(db_session, status="done")
    assert len(done) == 1
