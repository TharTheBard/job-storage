import abc

from sqlalchemy import String, Integer
from sqlalchemy import UniqueConstraint, ForeignKey
from sqlalchemy import Table, Column, MetaData


class BaseTable(abc.ABC):
    # Name of sql table
    __table_name__: str = "default"
    table: Table

    def __init__(self, meta_data: MetaData) -> None:
        _ = meta_data

    @property
    def name(self) -> str:
        return type(self).__table_name__

    @property
    def c(self) -> Column:
        return self.table.c


class Candidates(BaseTable):
    __table_name__ = "candidates"

    def __init__(self, meta_data: MetaData) -> None:
        super().__init__(meta_data)
        self.table = Table(
            type(self).__table_name__,
            meta_data,
            Column("id", Integer(), primary_key=True),
            Column("full_name", String()),
            Column("expected_salary", Integer())
        )


class Skills(BaseTable):
    __table_name__ = "skills"

    def __init__(self, meta_data: MetaData) -> None:
        super().__init__(meta_data)
        self.table = Table(
            type(self).__table_name__,
            meta_data,
            Column("id", Integer(), primary_key=True),
            Column("title", String(), unique=True),
        )


class CandidatesSkills(BaseTable):
    __table_name__ = "candidates_skills"

    def __init__(self, meta_data: MetaData) -> None:
        super().__init__(meta_data)
        self.table = Table(
            type(self).__table_name__,
            meta_data,
            Column("candidate_id", Integer(), ForeignKey("candidates.id"), nullable=False),
            Column("skill_id", Integer(), ForeignKey("skills.id"), nullable=False),
            UniqueConstraint("candidate_id", "skill_id"),
        )


class Jobs(BaseTable):
    __table_name__ = "jobs"

    def __init__(self, meta_data: MetaData) -> None:
        super().__init__(meta_data)
        self.table = Table(
            type(self).__table_name__,
            meta_data,
            Column("id", Integer(), primary_key=True),
            Column("title", String(), unique=True),
            Column("salary", Integer()),
            Column("description", String(), server_default=None),
        )


class JobsCandidates(BaseTable):
    __table_name__ = "jobs_candidates"

    def __init__(self, meta_data: MetaData) -> None:
        super().__init__(meta_data)
        self.table = Table(
            type(self).__table_name__,
            meta_data,
            Column("job_id", Integer(), ForeignKey("jobs.id"), nullable=False),
            Column("candidate_id", Integer(), ForeignKey("candidates.id"), nullable=False),
            UniqueConstraint("job_id", "candidate_id"),
        )
