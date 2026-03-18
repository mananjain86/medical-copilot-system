"""
Module C13: Natural Language Patient Search System
===================================================
Backend logic using the actual PostgreSQL schema (projectdb.sql).

Database tables used:
  patients, visits, symptoms, patient_symptoms,
  synonyms, symptom_hierarchy,
  search_queries, search_results, saved_queries,
  patient_cohorts, query_templates,
  lab_results, lab_tests, doctors, users

Stored functions already in the DB that we call:
  run_patient_search(uid, query, type)
  search_patients_nl(query)
  log_search_query(uid, query, type)
  create_cohort(name)
  save_user_query(uid, query)
  expand_query_terms(term)
  extract_gender(query)
  extract_age(query)
  extract_symptom(query)

Steps implemented here:
  1. parse_query()         - Extract gender / age / symptom from raw text
  2. expand_terms()        - Synonym expansion via the synonyms table
  3. generate_sql()        - Build dynamic SQL from parsed query (for DBMS demo tab)
  4. run_search()          - Execute search via DB stored function
  5. get_search_history()  - Fetch past queries for a user
  6. Cohort helpers        - create_patient_cohort(), get_cohorts()
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras

# Load .env from the project root (safe no-op if file is missing or dotenv not installed)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[3] / ".env")
except ImportError:
    pass  # python-dotenv not installed; rely on environment variables directly

_DB_HOST     = os.getenv("DB_HOST",     "localhost")
_DB_PORT     = int(os.getenv("DB_PORT", "5432"))
_DB_NAME     = os.getenv("DB_NAME",     "projectdb")
_DB_USER     = os.getenv("DB_USER",     "gaurav")
_DB_PASSWORD = os.getenv("DB_PASSWORD", "")


PROJECTDB_SQL_PATH = Path(__file__).with_name("projectdb.sql")


@dataclass
class SearchQuery:
	"""Holds everything we parsed out of the user's natural language input."""

	raw_text: str
	search_type: str = "clinical"
	gender: str | None = None
	age_above: int | None = None
	age_below: int | None = None
	symptom: str | None = None
	diagnosis: str | None = None
	city: str | None = None
	department: str | None = None
	expanded_terms: list[str] = field(default_factory=list)


_STOPWORDS = {
	"patient",
	"patients",
	"with",
	"and",
	"or",
	"the",
	"a",
	"an",
	"show",
	"find",
	"search",
	"list",
	"get",
	"me",
	"all",
	"records",
	"record",
	"who",
	"having",
	"has",
	"in",
	"of",
	"for",
}


_CONCEPT_MAP: dict[str, str] = {
	# cardio terms
	"heart disease": "chest pain",
	"cardiac disease": "chest pain",
	"heart problem": "chest pain",
	"heart condition": "chest pain",
	"cardiac problem": "chest pain",
	"angina": "chest pain",
	# pulmonary terms
	"breathlessness": "shortness of breath",
	"shortness breath": "shortness of breath",
	"dyspnea": "shortness of breath",
	"difficulty breathing": "shortness of breath",
	"breathing problem": "shortness of breath",
	"coughing": "cough",
	"tussis": "cough",
	# neuro terms
	"head pain": "headache",
	"cephalalgia": "headache",
	# general medicine
	"high temperature": "fever",
	"pyrexia": "fever",
	"tired": "fatigue",
	"tiredness": "fatigue",
	"weakness": "fatigue",
	"vomiting": "nausea",
	"nauseous": "nausea",
	# diagnosis style terms
	"diabetic": "diabetes",
	"sugar": "diabetes",
	"high sugar": "diabetes",
	"flu": "flu",
	"cold": "flu",
	"influenza": "flu",
	"chest congestion": "bronchitis",
	"lung infection": "bronchitis",
	"asthmatic": "asthma",
}


_DEPARTMENT_MAP: dict[str, str] = {
	"cardio": "Cardiology",
	"cardiology": "Cardiology",
	"heart": "Cardiology",
	"endo": "Endocrinology",
	"endocrinology": "Endocrinology",
	"diabetes": "Endocrinology",
	"general medicine": "General Medicine",
	"general": "General Medicine",
	"neurology": "Neurology",
	"neuro": "Neurology",
	"brain": "Neurology",
	"pulmonology": "Pulmonology",
	"pulmo": "Pulmonology",
	"lung": "Pulmonology",
	"respiratory": "Pulmonology",
}


def _normalize_query(text: str) -> str:
	"""Normalize common natural-language medical phrases to dataset terms."""

	q = text.lower().strip()
	for src, dst in _CONCEPT_MAP.items():
		q = q.replace(src, dst)
	return q


def _extract_age_bounds(lower: str) -> tuple[int | None, int | None]:
	"""Extract age bounds from natural-language text."""

	age_above: int | None = None
	age_below: int | None = None

	between = re.search(r"between\s+(\d+)\s+(?:and|to)\s+(\d+)", lower)
	if between:
		a, b = int(between.group(1)), int(between.group(2))
		age_above, age_below = min(a, b), max(a, b)
		return age_above, age_below

	over = re.search(r"(?:above|older than|over|greater than|more than)\s+(\d+)", lower)
	if over:
		age_above = int(over.group(1))

	under = re.search(r"(?:below|under|younger than|less than)\s+(\d+)", lower)
	if under:
		age_below = int(under.group(1))

	return age_above, age_below


@dataclass
class SearchResult:
	"""One patient row returned by the search."""

	patient_id: int
	first_name: str
	last_name: str
	gender: str


@dataclass
class GeneratedSQL:
	"""The SQL query built dynamically from the NL input."""

	sql: str
	params: dict[str, Any]
	explanation: str


def get_connection(
	host: str = _DB_HOST,
	port: int = _DB_PORT,
	dbname: str = _DB_NAME,
	user: str = _DB_USER,
	password: str = _DB_PASSWORD,
) -> psycopg2.extensions.connection:
	"""Open and return a PostgreSQL connection using credentials from .env."""

	return psycopg2.connect(
		host=host, port=port, dbname=dbname, user=user, password=password
	)


def initialize_projectdb(
	host: str = _DB_HOST,
	port: int = _DB_PORT,
	dbname: str = _DB_NAME,
	user: str = _DB_USER,
	password: str = _DB_PASSWORD,
	sql_file: str | None = None,
) -> str:
	"""
	Create the `projectdb` database if needed and load the bundled `projectdb.sql` dump.

	This keeps the course project tied directly to the real database file instead of
	any dummy in-memory data.
	"""

	target_sql = Path(sql_file) if sql_file else PROJECTDB_SQL_PATH
	if not target_sql.exists():
		raise FileNotFoundError(f"SQL file not found: {target_sql}")

	admin_conn = psycopg2.connect(
		host=host,
		port=port,
		dbname="postgres",
		user=user,
		password=password,
	)
	admin_conn.autocommit = True
	try:
		with admin_conn.cursor() as cur:
			cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
			if cur.fetchone() is None:
				cur.execute(f'CREATE DATABASE "{dbname}"')
	finally:
		admin_conn.close()

	env = None
	if password:
		env = {"PGPASSWORD": password}

	command = [
		"psql",
		"-h",
		host,
		"-p",
		str(port),
		"-U",
		user,
		"-d",
		dbname,
		"-f",
		str(target_sql),
	]
	result = subprocess.run(command, check=False, capture_output=True, text=True, env=env)
	if result.returncode != 0:
		raise RuntimeError(result.stderr.strip() or "Failed to load projectdb.sql")

	return f"Loaded database from {target_sql} into {dbname}"


def parse_query(text: str) -> SearchQuery:
	"""
	Extract structured filters from raw text.

	Examples:
	  "female patients above 40 with fever"
	  "patients with pyrexia"
	"""

	lower = _normalize_query(text)

	gender = None
	if "female" in lower:
		gender = "female"
	elif "male" in lower:
		gender = "male"

	age_above, age_below = _extract_age_bounds(lower)

	city = None
	for c in ("ahmedabad", "chennai", "delhi", "hyderabad", "kochi", "kolkata", "mumbai"):
		if c in lower:
			city = c.title()
			break

	department = None
	for token, mapped in _DEPARTMENT_MAP.items():
		if token in lower:
			department = mapped
			break

	if any(word in lower for word in ("glucose", "hemoglobin", "cholesterol", "lab test", "lab result")):
		search_type = "laboratory"
	elif any(word in lower for word in ("visited", "last", "days", "week", "month", "recent")):
		search_type = "temporal"
	elif any(
		word in lower
		for word in (
			"symptom",
			"with fever",
			"with cough",
			"with headache",
			"with pain",
			"with fatigue",
			"with nausea",
			"with shortness",
			"disease",
			"diagnosis",
			"condition",
		)
	):
		search_type = "clinical"
	elif gender or age_above or age_below or city or department:
		search_type = "demographic"
	else:
		search_type = "clinical"

	return SearchQuery(
		raw_text=text,
		search_type=search_type,
		gender=gender,
		age_above=age_above,
		age_below=age_below,
		city=city,
		department=department,
	)


def expand_terms(conn, text: str) -> list[str]:
	"""
	Use the synonyms table in the DB to expand query keywords.
	E.g. 'pyrexia' -> adds 'fever'; 'fever' -> adds 'pyrexia'.
	"""

	words = re.findall(r"[a-zA-Z]+", text.lower())
	expanded: set[str] = set(words)

	with conn.cursor() as cur:
		for word in words:
			cur.execute("SELECT word FROM synonyms WHERE synonym ILIKE %s", (word,))
			for row in cur.fetchall():
				expanded.add(row[0])

			cur.execute("SELECT synonym FROM synonyms WHERE word ILIKE %s", (word,))
			for row in cur.fetchall():
				expanded.add(row[0])

			cur.execute("SELECT expanded_term FROM expand_query_terms(%s)", (word,))
			for row in cur.fetchall():
				expanded.add(row[0])

	return sorted(expanded)


def resolve_symptom(conn, text: str) -> str | None:
	"""Resolve raw text to a canonical symptom name."""

	lower = _normalize_query(text)

	with conn.cursor() as cur:
		# 0) identify direct token/phrase overlap with known symptom names
		cur.execute("SELECT symptom_name FROM symptoms")
		for (symptom_name,) in cur.fetchall():
			if symptom_name and symptom_name.lower() in lower:
				return symptom_name

		# 1) direct symptom phrase appears in the query text
		cur.execute(
			"""
			SELECT symptom_name
			FROM symptoms
			WHERE %s ILIKE '%%' || symptom_name || '%%'
			ORDER BY LENGTH(symptom_name) DESC
			LIMIT 1
			""",
			(lower,),
		)
		row = cur.fetchone()
		if row:
			return row[0]

		# 2) synonym appears in query text, map back to canonical symptom
		cur.execute(
			"""
			SELECT word
			FROM synonyms
			WHERE %s ILIKE '%%' || synonym || '%%'
			ORDER BY LENGTH(synonym) DESC
			LIMIT 1
			""",
			(lower,),
		)
		row = cur.fetchone()
		if row:
			return row[0]

		# 3) fallback token-wise exact match
		for token in re.findall(r"[a-zA-Z]+", lower):
			cur.execute(
				"SELECT symptom_name FROM symptoms WHERE symptom_name ILIKE %s LIMIT 1",
				(token,),
			)
			row = cur.fetchone()
			if row:
				return row[0]

			cur.execute(
				"SELECT word FROM synonyms WHERE synonym ILIKE %s LIMIT 1",
				(token,),
			)
			row = cur.fetchone()
			if row:
				return row[0]

	return None


def resolve_diagnosis(conn, text: str) -> str | None:
	"""Resolve diagnosis terms from NL query text using visits.diagnosis values."""

	normalized = _normalize_query(text)

	with conn.cursor() as cur:
		cur.execute(
			"""
			SELECT diagnosis
			FROM visits
			WHERE %s ILIKE '%%' || diagnosis || '%%'
			ORDER BY LENGTH(diagnosis) DESC
			LIMIT 1
			""",
			(normalized,),
		)
		row = cur.fetchone()
		if row:
			return row[0]

		for token in re.findall(r"[a-zA-Z]+", normalized):
			cur.execute(
				"SELECT diagnosis FROM visits WHERE diagnosis ILIKE %s LIMIT 1",
				(token,),
			)
			row = cur.fetchone()
			if row:
				return row[0]

	return None


def generate_sql(query: SearchQuery) -> GeneratedSQL:
	"""
	Build a dynamic SQL query from the parsed NL input using the real schema.
	"""

	conditions: list[str] = []
	params: dict[str, Any] = {}
	notes: list[str] = []

	if query.gender:
		conditions.append("p.gender = %(gender)s")
		params["gender"] = query.gender
		notes.append(f"gender = '{query.gender}'")

	if query.age_above:
		conditions.append("DATE_PART('year', AGE(p.date_of_birth)) > %(age_above)s")
		params["age_above"] = query.age_above
		notes.append(f"age > {query.age_above}")

	if query.age_below:
		conditions.append("DATE_PART('year', AGE(p.date_of_birth)) < %(age_below)s")
		params["age_below"] = query.age_below
		notes.append(f"age < {query.age_below}")

	if query.symptom:
		conditions.append("(sy.symptom_name = %(symptom)s OR syn.synonym = %(symptom)s)")
		params["symptom"] = query.symptom
		notes.append(f"symptom = '{query.symptom}' (+ synonyms)")

	if query.diagnosis:
		conditions.append("v.diagnosis ILIKE %(diagnosis)s")
		params["diagnosis"] = query.diagnosis
		notes.append(f"diagnosis ~= '{query.diagnosis}'")

	if query.city:
		conditions.append("p.city ILIKE %(city)s")
		params["city"] = query.city
		notes.append(f"city = '{query.city}'")

	if query.department:
		conditions.append("d.specialization ILIKE %(department)s")
		params["department"] = query.department
		notes.append(f"department = '{query.department}'")

	# Keyword fallback for free-text clinical queries when explicit entities are sparse.
	keyword_terms = [
		term for term in (query.expanded_terms or [])
		if len(term) >= 3 and term not in _STOPWORDS
	]
	if query.search_type == "clinical" and not any([
		query.gender,
		query.age_above,
		query.age_below,
		query.symptom,
		query.diagnosis,
		query.city,
		query.department,
	]) and keyword_terms:
		kw_clauses: list[str] = []
		for idx, kw in enumerate(sorted(set(keyword_terms))[:10]):
			key = f"kw_{idx}"
			params[key] = f"%{kw}%"
			kw_clauses.append(
				"(" 
				f"p.first_name ILIKE %({key})s OR "
				f"p.last_name ILIKE %({key})s OR "
				f"p.city ILIKE %({key})s OR "
				f"v.diagnosis ILIKE %({key})s OR "
				f"sy.symptom_name ILIKE %({key})s OR "
				f"syn.synonym ILIKE %({key})s OR "
				f"d.specialization ILIKE %({key})s"
				")"
			)
		if kw_clauses:
			conditions.append("(" + " OR ".join(kw_clauses) + ")")
			notes.append("keyword fallback")

	if query.search_type == "laboratory":
		conditions.append("lt.test_name ILIKE %(lab_term)s")
		params["lab_term"] = f"%{query.symptom or ''}%"
		notes.append("has lab result")

	where_clause = ("\nWHERE\n    " + "\n    AND ".join(conditions)) if conditions else ""

	if query.search_type == "laboratory":
		joins = (
			"LEFT JOIN visits v         ON p.patient_id = v.patient_id\n"
			"LEFT JOIN lab_results lr   ON v.visit_id   = lr.visit_id\n"
			"LEFT JOIN lab_tests lt     ON lr.test_id   = lt.test_id"
		)
		select_cols = (
			"    p.patient_id,\n"
			"    p.first_name,\n"
			"    p.last_name,\n"
			"    p.gender,\n"
			"    lt.test_name,\n"
			"    lr.result_value,\n"
			"    lr.result_date"
		)
	else:
		joins = (
			"LEFT JOIN visits v              ON p.patient_id  = v.patient_id\n"
			"LEFT JOIN patient_symptoms ps   ON v.visit_id    = ps.visit_id\n"
			"LEFT JOIN symptoms sy           ON ps.symptom_id = sy.symptom_id\n"
			"LEFT JOIN synonyms syn          ON sy.symptom_name = syn.word\n"
			"LEFT JOIN doctors d             ON v.doctor_id = d.doctor_id"
		)
		select_cols = (
			"    p.patient_id,\n"
			"    p.first_name,\n"
			"    p.last_name,\n"
			"    p.gender,\n"
			"    DATE_PART('year', AGE(p.date_of_birth)) AS age,\n"
			"    p.city"
		)

	sql = (
		f"SELECT DISTINCT\n{select_cols}\n"
		f"FROM patients p\n"
		f"{joins}"
		f"{where_clause}\n"
		f"ORDER BY p.patient_id\n"
		f"LIMIT 100;"
	)

	explanation = (
		f"Input: \"{query.raw_text}\"\n"
		f"Type : {query.search_type}\n"
		f"Filters applied: " + (", ".join(notes) if notes else "none - returns all patients")
	)

	return GeneratedSQL(sql=sql, params=params, explanation=explanation)


def run_search(
	conn,
	user_id: int,
	nl_query: str,
	search_type: str = "clinical",
	sql_payload: GeneratedSQL | None = None,
) -> tuple[list[SearchResult], int | None]:
	"""
	Execute query and return patient rows.

	If sql_payload is provided, we run the generated SQL directly so parsed NL filters
	are always applied, and still log the query in search_queries.
	"""

	query_id: int | None = None
	with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
		if sql_payload is None:
			cur.execute(
				"SELECT * FROM run_patient_search(%s, %s, %s)",
				(user_id, nl_query, search_type),
			)
			rows = cur.fetchall()
			cur.execute(
				"""
				SELECT query_id
				FROM search_queries
				WHERE user_id = %s AND query_text = %s AND search_type = %s
				ORDER BY query_id DESC
				LIMIT 1
				""",
				(user_id, nl_query, search_type),
			)
			qid_row = cur.fetchone()
			query_id = int(qid_row["query_id"]) if qid_row else None
		else:
			cur.execute("SELECT log_search_query(%s, %s, %s)", (user_id, nl_query, search_type))
			qid_row = cur.fetchone()
			query_id = int(next(iter(qid_row.values()))) if qid_row else None
			cur.execute(sql_payload.sql, sql_payload.params)
			rows = cur.fetchall()

			if query_id is not None and rows:
				for row in rows:
					cur.execute(
						"""
						INSERT INTO search_results(query_id, patient_id, relevance_score)
						VALUES (%s, %s, %s)
						""",
						(query_id, int(row["patient_id"]), 1.0),
					)
		conn.commit()

	results = [
		SearchResult(
			patient_id=int(row["patient_id"]),
			first_name=row["first_name"],
			last_name=row["last_name"],
			gender=row["gender"],
		)
		for row in rows
	]

	return results, query_id


def _ensure_cohort_member_table(conn) -> None:
	"""Ensure cohort-member mapping table exists for cohort persistence."""

	with conn.cursor() as cur:
		cur.execute(
			"""
			CREATE TABLE IF NOT EXISTS patient_cohort_members (
				member_id SERIAL PRIMARY KEY,
				cohort_id INTEGER NOT NULL REFERENCES patient_cohorts(cohort_id) ON DELETE CASCADE,
				patient_id INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
				query_id INTEGER REFERENCES search_queries(query_id) ON DELETE SET NULL,
				added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				UNIQUE (cohort_id, patient_id)
			)
			"""
		)
		conn.commit()


def create_search_cohort(
	conn,
	user_id: int,
	nl_query: str,
	search_type: str,
	patient_ids: list[int],
	query_id: int | None = None,
) -> int:
	"""Create a cohort for a search and persist its member patient ids."""

	_ensure_cohort_member_table(conn)
	cohort_name = f"U{user_id} | {search_type} | {nl_query[:80]}"

	with conn.cursor() as cur:
		cur.execute("INSERT INTO patient_cohorts(cohort_name) VALUES(%s) RETURNING cohort_id", (cohort_name,))
		cohort_id = int(cur.fetchone()[0])

		if patient_ids:
			for pid in sorted(set(patient_ids)):
				cur.execute(
					"""
					INSERT INTO patient_cohort_members(cohort_id, patient_id, query_id)
					VALUES (%s, %s, %s)
					ON CONFLICT (cohort_id, patient_id) DO NOTHING
					""",
					(cohort_id, int(pid), query_id),
				)

		conn.commit()

	return cohort_id


def get_search_history(conn, user_id: int) -> list[dict[str, Any]]:
	"""Fetch the last 20 queries made by a user from search_queries."""

	with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
		cur.execute(
			"""
			SELECT query_id, query_text, search_type, created_at
			FROM   search_queries
			WHERE  user_id = %s
			ORDER  BY created_at DESC
			LIMIT  20
			""",
			(user_id,),
		)
		return [dict(row) for row in cur.fetchall()]


def save_query(conn, user_id: int, query_text: str) -> None:
	"""Save a query to saved_queries via save_user_query()."""

	with conn.cursor() as cur:
		cur.execute("SELECT save_user_query(%s, %s)", (user_id, query_text))
		conn.commit()


def get_saved_queries(conn, user_id: int) -> list[dict[str, Any]]:
	"""Return all saved queries for the user."""

	with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
		cur.execute(
			"""
			SELECT saved_id, query_text, created_at
			FROM   saved_queries
			WHERE  user_id = %s
			ORDER  BY created_at DESC
			""",
			(user_id,),
		)
		return [dict(row) for row in cur.fetchall()]


def create_patient_cohort(conn, name: str) -> int:
	"""Create a named patient cohort via create_cohort()."""

	with conn.cursor() as cur:
		cur.execute("SELECT create_cohort(%s)", (name,))
		cohort_id = cur.fetchone()[0]
		conn.commit()
	return cohort_id


def get_cohorts(conn) -> list[dict[str, Any]]:
	"""Return all patient cohorts from patient_cohorts."""

	_ensure_cohort_member_table(conn)

	with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
		cur.execute(
			"""
			SELECT c.cohort_id, c.cohort_name, c.created_at,
			       COUNT(m.patient_id) AS member_count
			FROM patient_cohorts c
			LEFT JOIN patient_cohort_members m ON m.cohort_id = c.cohort_id
			GROUP BY c.cohort_id, c.cohort_name, c.created_at
			ORDER BY c.created_at DESC
			"""
		)
		return [dict(row) for row in cur.fetchall()]


def get_cohort_members(conn, cohort_id: int, limit: int = 200) -> list[dict[str, Any]]:
	"""Return patient members for a given cohort id with basic demographics."""

	_ensure_cohort_member_table(conn)

	with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
		cur.execute(
			"""
			SELECT
				m.cohort_id,
				m.patient_id,
				p.first_name,
				p.last_name,
				p.gender,
				DATE_PART('year', AGE(p.date_of_birth))::int AS age,
				p.city,
				m.query_id,
				m.added_at
			FROM patient_cohort_members m
			JOIN patients p ON p.patient_id = m.patient_id
			WHERE m.cohort_id = %s
			ORDER BY m.added_at DESC
			LIMIT %s
			""",
			(cohort_id, max(1, limit)),
		)
		return [dict(row) for row in cur.fetchall()]


def nl_search_pipeline(conn, user_id: int, nl_query: str) -> dict[str, Any]:
	"""
	Run the complete NL search pipeline and return everything the UI needs.
	"""

	parsed = parse_query(nl_query)
	normalized_query = _normalize_query(nl_query)
	parsed.expanded_terms = sorted(
		set(expand_terms(conn, normalized_query))
		| set(re.findall(r"[a-zA-Z]+", normalized_query))
	)
	parsed.symptom = resolve_symptom(conn, nl_query)
	parsed.diagnosis = resolve_diagnosis(conn, nl_query)
	sql_payload = generate_sql(parsed)

	# For clinical free-text with no resolved filter, avoid returning all patients.
	lower_q = nl_query.lower().strip()
	allow_all = any(
		phrase in lower_q
		for phrase in ("all patients", "all patient", "all records", "list all", "show all")
	)
	has_filter = any([
		parsed.gender,
		parsed.age_above,
		parsed.age_below,
		parsed.symptom,
		parsed.diagnosis,
		parsed.city,
		parsed.department,
	])
	if parsed.search_type == "clinical" and not has_filter and not allow_all:
		results: list[SearchResult] = []
		query_id: int | None = None
	else:
		results, query_id = run_search(
			conn,
			user_id,
			nl_query,
			parsed.search_type,
			sql_payload=sql_payload,
		)

	cohort_id: int | None = None
	if results:
		cohort_id = create_search_cohort(
			conn=conn,
			user_id=user_id,
			nl_query=nl_query,
			search_type=parsed.search_type,
			patient_ids=[r.patient_id for r in results],
			query_id=query_id,
		)

	return {
		"parsed": parsed,
		"sql": sql_payload,
		"results": results,
		"query_id": query_id,
		"cohort_id": cohort_id,
	}
