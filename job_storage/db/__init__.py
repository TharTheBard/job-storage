from typing import List, Dict, Any

from flask import current_app as app
from sqlalchemy import exc, select, bindparam, MetaData, create_engine
from sqlalchemy_utils import database_exists, create_database
from dataclasses import asdict

from . import tables
from job_storage import validators as v
from job_storage import custom_exceptions as j_exc


class Storage(object):
    convention = {
        "ix": 'ix_%(column_0_label)s',
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"}

    def __init__(
            self,
            user,
            password,
            host,
            port,
            path,
            echo=False,
            pool_size=2,
            pool_recycle=1320,
            isolation_level='read committed'.upper()
    ):
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.path = path

        self.client = create_engine(
            self.uri,
            echo=echo,
            pool_size=pool_size,
            pool_recycle=pool_recycle,
            isolation_level=isolation_level)
        if not database_exists(self.client.url):
            create_database(self.client.url)
        self.metadata = MetaData(
            bind=self.client,
            naming_convention=Storage.convention)

        self.candidates = tables.Candidates(self.metadata)
        self.skills = tables.Skills(self.metadata)
        self.candidates_skills = tables.CandidatesSkills(self.metadata)
        self.jobs = tables.Jobs(self.metadata)
        self.jobs_candidates = tables.JobsCandidates(self.metadata)

        self.metadata.create_all()
        self._define_statements()

    @property
    def uri(self):
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.path}"

    def execute(self, stm, con=None, **kwargs):
        if con is None:
            con = self.client
        return con.execute(stm, **kwargs)

    def select(self, stm, con=None, **kwargs):
        cur = self.execute(stm, con, **kwargs)
        return cur.fetchall()

    def select_dicts(self, stm, con=None, **kwargs) -> List[Dict[str, Any]]:
        return [dict(row) for row in self.execute(stm, con, **kwargs)]

    def update(self, stm, con=None, **kwargs):
        cur = self.execute(stm, con, **kwargs)
        return cur.rowcount

    def insert(self, stm, con=None, **kwargs):
        cur = self.execute(stm, con=con, **kwargs)
        return cur.inserted_primary_key[0]

    def delete(self, stm, con=None, **kwargs):
        cur = self.execute(stm, con=con, **kwargs)
        return cur.rowcount

    def ping(self) -> bool:
        """
        Try to connect
        :return: True if success, False otherwise
        """
        return self.client is not None

    # DB METHODS:
    def list_candidates(self):
        with self.client.connect() as con:
            candidates = self.select_dicts(self.candidates_stm, con)
            for candidate in candidates:
                candidate_skills = self.select_dicts(self.candidate_skills_stm, con, candidate_id=candidate["id"])
                candidate["skills"] = candidate_skills
        return candidates

    def find_candidate(self, candidate_id):
        with self.client.connect() as con:
            try:
                candidate = self.select_dicts(self.candidates_stm.where(self.candidates.c.id == candidate_id), con)[0]
                candidate_skills = self.select_dicts(self.candidate_skills_stm, con, candidate_id=candidate["id"])
                candidate["skills"] = candidate_skills
            except IndexError:
                raise j_exc.ForeignKeyViolationError("Candidate does not exist", 404)
        return candidate

    def list_skills(self):
        with self.client.connect() as con:
            data = self.select_dicts(self.skills_stm, con)
        return data

    def list_jobs(self):
        with self.client.connect() as con:
            data = self.select_dicts(self.jobs_stm, con)
        return data

    def find_job(self, job_id):
        with self.client.connect() as con:
            try:
                job = self.select_dicts(self.jobs_stm.where(self.jobs.c.id == job_id), con)[0]
                job_candidates = self.select_dicts(self.job_candidates_stm, con, job_id=job_id)
                job["candidates"] = job_candidates
            except IndexError:
                raise j_exc.ForeignKeyViolationError("Job does not exist", 404)
        return job

    def insert_job(self, payload: v.jobs.InsertJob):
        with self.client.connect() as con:
            trans = con.begin()
            try:
                self.insert(
                    self.jobs.table.insert().values(asdict(payload)),
                    con
                )
            except exc.SQLAlchemyError as e:
                trans.rollback()
                app.logger.warning(f'Insert job error - {e}')
                raise j_exc.DatabaseError
            else:
                trans.commit()

    def force_insert_job(self, job_id, payload: v.jobs.InsertJob):
        with self.client.connect() as con:
            trans = con.begin()
            try:
                found_jobs = self.select_dicts(self.jobs_stm.where(self.jobs.c.id == job_id), con)
                if len(found_jobs) < 1:
                    self.insert(
                        self.jobs.table.insert().values(asdict(payload)),
                        con
                    )
                else:
                    self.update(
                        self.update_job_stm,
                        con,
                        job_id=job_id,
                        **asdict(payload)
                    )
            except exc.SQLAlchemyError as e:
                trans.rollback()
                app.logger.warning(f'Force insert job error - {e}')
                raise j_exc.DatabaseError
            else:
                trans.commit()

    def delete_job(self, job_id):
        with self.client.connect() as con:
            trans = con.begin()
            try:
                rowcount = self.delete(
                    self.jobs.table.delete().where(self.jobs.c.id == job_id).returning(self.jobs.c.id),
                    con
                )
                if rowcount < 1:
                    trans.rollback()
                    raise j_exc.ForeignKeyViolationError("Job does not exist", 404)
            except exc.SQLAlchemyError as e:
                trans.rollback()
                app.logger.warning(f'Delete job error - {e}')
                raise j_exc.DatabaseError
            else:
                trans.commit()

    def insert_candidate(self, payload: v.candidates.InsertCandidate):
        with self.client.connect() as con:
            trans = con.begin()
            try:
                candidate_dict = asdict(payload)
                skills = candidate_dict.pop("skills")
                candidate_id = self.insert(
                    self.candidates.table.insert().values(**candidate_dict),
                    con
                )
                skill_ids = []
                for skill_title in skills:
                    found_skills = self.select_dicts(self.skills_stm.where(self.skills.c.title == skill_title), con)
                    if len(found_skills) < 0:
                        skill_id = found_skills[0]["id"]
                    else:
                        skill_id = self.insert(self.skills.table.insert().values(title=skill_title), con)
                    skill_ids.append(skill_id)
                self.execute(
                    self.candidates_skills.table.insert().values(
                        [{"candidate_id": candidate_id, "skill_id": skill_id} for skill_id in skill_ids]
                    ),
                    con
                )
            except exc.SQLAlchemyError as e:
                trans.rollback()
                app.logger.warning(f'Insert candidate error - {e}')
                raise j_exc.DatabaseError
            else:
                trans.commit()

    def force_insert_candidate(self, candidate_id, payload: v.candidates.InsertCandidate):
        with self.client.connect() as con:
            trans = con.begin()
            try:
                candidate_dict = asdict(payload)
                skills = candidate_dict.pop("skills")
                found_candidates = self.select_dicts(self.candidates_stm.where(self.candidates.c.id == candidate_id), con)
                if len(found_candidates) < 1:
                    candidate_id = self.insert(self.candidates.table.insert().values(**candidate_dict), con)
                else:
                    self.update(self.update_candidate_stm, con, candidate_id=candidate_id, **candidate_dict)

                skill_ids = []
                for skill_title in skills:
                    found_skills = self.select_dicts(self.skills_stm.where(self.skills.c.title == skill_title), con)
                    if len(found_skills) > 0:
                        skill_id = found_skills[0]["id"]
                    else:
                        skill_id = self.insert(self.skills.table.insert().values(title=skill_title), con)
                    skill_ids.append(skill_id)
                self.delete(self.candidates_skills.table.delete().where(
                    self.candidates_skills.c.candidate_id == candidate_id), con)
                self.execute(
                    self.candidates_skills.table.insert().values(
                        [{"candidate_id": candidate_id, "skill_id": skill_id} for skill_id in skill_ids]
                    ),
                    con
                )
            except exc.SQLAlchemyError as e:
                trans.rollback()
                app.logger.warning(f'Force insert candidate error - {e}')
                raise j_exc.DatabaseError
            else:
                trans.commit()

    def delete_candidate(self, candidate_id):
        with self.client.connect() as con:
            trans = con.begin()
            try:
                found_candidates = self.select_dicts(self.candidates_stm.where(self.candidates.c.id == candidate_id), con)
                if len(found_candidates) < 1:
                    trans.rollback()
                    raise j_exc.ForeignKeyViolationError("Candidate does not exist", 404)

                self.delete(self.candidates_skills.table.delete().where(
                    self.candidates_skills.c.candidate_id == candidate_id), con)
                self.delete(
                    self.candidates.table.delete().where(self.candidates.c.id == candidate_id),
                    con
                )
            except exc.SQLAlchemyError as e:
                trans.rollback()
                app.logger.warning(f'Delete candidate error - {e}')
                raise j_exc.DatabaseError
            else:
                trans.commit()

    def apply_candidate(self, candidate_id, job_id):
        with self.client.connect() as con:
            trans = con.begin()
            try:
                found_candidates = self.select_dicts(self.candidates_stm.where(self.candidates.c.id == candidate_id), con)
                if len(found_candidates) < 1:
                    raise j_exc.ForeignKeyViolationError("Candidate does not exist", 404)
                found_jobs = self.select_dicts(self.jobs_stm.where(self.jobs.c.id == job_id), con)
                if len(found_jobs) < 1:
                    raise j_exc.ForeignKeyViolationError("Job does not exist", 404)
                self.execute(
                    self.jobs_candidates.table.insert().values(
                        {"job_id": job_id, "candidate_id": candidate_id}
                    ),
                    con
                )
            except exc.SQLAlchemyError as e:
                trans.rollback()
                app.logger.warning(f'Apply candidate error - {e}')
                raise j_exc.DatabaseError
            else:
                trans.commit()

    # STATEMENT DECLARATIONS
    def _define_statements(self):
        # JOINS
        candidates_skills_join = self.candidates.table. \
            join(self.candidates_skills.table, self.candidates.c.id == self.candidates_skills.c.candidate_id). \
            outerjoin(self.skills.table, self.candidates_skills.c.skill_id == self.skills.c.id)

        jobs_candidates_join = self.jobs.table. \
            join(self.jobs_candidates.table, self.jobs.c.id == self.jobs_candidates.c.candidate_id). \
            outerjoin(self.candidates.table, self.jobs_candidates.c.candidate_id == self.candidates.c.id)

        # STATEMENTS
        self.jobs_stm = select([
            self.jobs.c.id,
            self.jobs.c.title,
            self.jobs.c.salary,
            self.jobs.c.description,
        ]).select_from(self.jobs.table)

        self.candidates_stm = select([
            self.candidates.c.id,
            self.candidates.c.full_name,
            self.candidates.c.expected_salary,
        ]).select_from(self.candidates.table)

        self.skills_stm = select([
            self.skills.c.id,
            self.skills.c.title,
        ]).select_from(self.skills.table)

        self.candidate_skills_stm = select([
            self.skills.c.id,
            self.skills.c.title,
        ]).select_from(candidates_skills_join). \
            where(self.candidates.c.id == bindparam("candidate_id"))

        self.job_candidates_stm = select([
            self.candidates.c.id,
            self.candidates.c.full_name,
            self.candidates.c.expected_salary,
        ]).select_from(jobs_candidates_join). \
            where(self.jobs.c.id == bindparam("job_id"))

        self.update_job_stm = self.jobs.table.update(). \
            where(self.jobs.c.id == bindparam("job_id")). \
            values(
                title=bindparam("title"),
                salary=bindparam("salary"),
                description=bindparam("description"),
        )

        self.update_candidate_stm = self.candidates.table.update(). \
            where(self.candidates.c.id == bindparam("candidate_id")). \
            values(
            full_name=bindparam("full_name"),
            expected_salary=bindparam("expected_salary"),
        )
