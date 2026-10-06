from uuid import UUID

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.persistence.database import Base
from app.services.project_service import ProjectService


def test_project_is_identical_after_database_restart(tmp_path):
    path = tmp_path / "restart.db"
    url = f"sqlite:///{path.as_posix()}"

    def factory():
        engine = create_engine(url)

        @event.listens_for(engine, "connect")
        def pragmas(connection, _record):
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA journal_mode=WAL")

        Base.metadata.create_all(engine)
        return engine, sessionmaker(bind=engine, expire_on_commit=False)

    engine, sessions = factory()
    with sessions() as session:
        service = ProjectService(session)
        project_id = UUID(service.create_project("Restart proof")["id"])
        function_id = UUID(str(service.create_function(project_id, 2, "Joint 2")["functions"][0]["id"]))
        motor = service.create_component(project_id, function_id, "M", "Motor")
        service.create_component(project_id, function_id, "B", "Encoder", parent_component_id=UUID(str(motor["id"])))
        before = service.get_project(project_id)
    engine.dispose()

    restarted_engine, restarted_sessions = factory()
    with restarted_sessions() as session:
        after = ProjectService(session).get_project(project_id)
    restarted_engine.dispose()
    assert after == before
