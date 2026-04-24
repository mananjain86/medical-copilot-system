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
	log_search_query(uid, query, type)
  save_user_query(uid, query)
  expand_query_terms(term)

Steps implemented here:
  1. parse_query()         - Extract gender / age / symptom from raw text
  2. expand_terms()        - Synonym expansion via the synonyms table
  3. generate_sql()        - Build dynamic SQL from parsed query (for DBMS demo tab)
	4. run_search()          - Execute generated SQL + persist query/results
  5. get_search_history()  - Fetch past queries for a user
	6. Cohort helpers        - create_search_cohort(), get_cohorts()
"""

from __future__ import annotations

import os
import re
import io
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras
from psycopg2 import sql as psy_sql

_C13_ENV_PATH = Path(__file__).with_name(".env")
_ROOT_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"


def _load_env_file(path: Path, override: bool) -> None:
	"""Load key-value pairs from a .env file path."""

	if not path.exists():
		return

	try:
		from dotenv import load_dotenv
		load_dotenv(path, override=override)
		return
	except ImportError:
		pass

	for raw_line in path.read_text(encoding="utf-8").splitlines():
		line = raw_line.strip()
		if not line or line.startswith("#") or "=" not in line:
			continue
		key, value = line.split("=", 1)
		key = key.strip()
		value = value.strip().strip('"').strip("'")
		if override or key not in os.environ:
			os.environ[key] = value


def _load_c13_env_file() -> None:
	"""Load root .env first, then C13-local .env as fallback."""

	_load_env_file(_ROOT_ENV_PATH, override=False)
	_load_env_file(_C13_ENV_PATH, override=False)


_load_c13_env_file()

_DATABASE_PRIVATE_URL = os.getenv("DATABASE_URL")
_DATABASE_PUBLIC_URL = os.getenv("DATABASE_PUBLIC_URL")
_DATABASE_URL = _DATABASE_PRIVATE_URL or _DATABASE_PUBLIC_URL
_DB_HOST     = os.getenv("DB_HOST",     "localhost")
_DB_PORT     = int(os.getenv("DB_PORT", "5432"))
_DB_NAME     = os.getenv("DB_NAME",     "projectdb")
_DB_USER     = os.getenv("DB_USER",     "postgres")
_DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
_DB_SSLMODE  = os.getenv("DB_SSLMODE") or os.getenv("PGSSLMODE")


PROJECTDB_SQL_PATH = Path(__file__).with_name("projectdb.sql")


def _sync_serial_sequence(conn, table_name: str, pk_column: str) -> None:
	"""Ensure the serial sequence for a table PK is aligned with existing rows."""

	with conn.cursor() as cur:
		cur.execute("SELECT pg_get_serial_sequence(%s, %s)", (table_name, pk_column))
		row = cur.fetchone()
		if not row or not row[0]:
			return
		sequence_name = row[0]

		table_ident = psy_sql.Identifier(*table_name.split("."))
		pk_ident = psy_sql.Identifier(pk_column)
		cur.execute(
			psy_sql.SQL("SELECT COALESCE(MAX({pk}), 0) FROM {table}").format(
				pk=pk_ident,
				table=table_ident,
			)
		)
		max_id = int(cur.fetchone()[0] or 0)

		# With is_called=false, the next nextval() returns this exact value.
		next_value = max(1, max_id + 1)
		cur.execute("SELECT setval(%s, %s, false)", (sequence_name, next_value))


def _repair_c13_write_sequences(conn) -> None:
	"""Fix key write-path sequences that can drift after repeated SQL imports."""

	for table_name, pk_column in (
		("search_queries", "query_id"),
		("search_results", "result_id"),
		("patient_cohorts", "cohort_id"),
		("saved_queries", "saved_id"),
		("patient_cohort_members", "member_id"),
	):
		_sync_serial_sequence(conn, table_name, pk_column)


@dataclass
class SearchQuery:
	"""Holds everything we parsed out of the user's natural language input."""

	raw_text: str
	search_type: str = "clinical"
	gender: str | None = None
	age_above: int | None = None
	age_below: int | None = None
	age_is: int | None = None
	symptom: str | None = None
	diagnosis: str | None = None
	city: str | None = None
	department: str | None = None
	status: str | None = None
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
	"age",
	"over", "above", "older", "greater", "more",
	"under", "below", "younger", "less",
	"than", "between", "at", "least", "most",
	"min", "max", "minimum", "maximum",
	"male", "female", "man", "men", "woman", "women", "lady", "ladies",
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
	"cardiology department": "Cardiology",
	"endo": "Endocrinology",
	"endocrinology": "Endocrinology",
	"endocrinology department": "Endocrinology",
	"general medicine": "General Medicine",
	"general medicine department": "General Medicine",
	"neurology": "Neurology",
	"neurology department": "Neurology",
	"neuro": "Neurology",
	"pulmonology": "Pulmonology",
	"pulmonology department": "Pulmonology",
	"pulmo": "Pulmonology",
}


def _normalize_query(text: str) -> str:
	"""Normalize common natural-language medical phrases to dataset terms."""

	q = text.lower().strip()
	for src, dst in _CONCEPT_MAP.items():
		q = q.replace(src, dst)
	return q


def _extract_age_bounds(lower: str) -> tuple[int | None, int | None, int | None]:
	"""Extract age bounds (min, max, exact) from natural-language text."""

	age_above: int | None = None
	age_below: int | None = None
	age_is: int | None = None

	between = re.search(r"between\s+(\d+)\s+(?:and|to)\s+(\d+)", lower)
	if between:
		a, b = int(between.group(1)), int(between.group(2))
		age_above, age_below = min(a, b), max(a, b)
		return age_above, age_below, age_is

	exact = re.search(r"(?:aged|is|age)\s+(\d+)(?:\s+years\s+old)?", lower)
	if exact:
		age_is = int(exact.group(1))
		return age_above, age_below, age_is

	over = re.search(r"(?:above|older than|over|greater than|more than|at least|min|minimum)\s+(\d+)", lower)
	if over:
		age_above = int(over.group(1))

	under = re.search(r"(?:below|under|younger than|less than|at most|max|maximum)\s+(\d+)", lower)
	if under:
		age_below = int(under.group(1))

	return age_above, age_below, age_is


@dataclass
class SearchResult:
	"""One patient row returned by the search."""

	patient_id: int
	first_name: str
	last_name: str
	gender: str
	age: int
	status: str


@dataclass
class GeneratedSQL:
	"""The SQL query built dynamically from the NL input."""

	sql: str
	params: dict[str, Any]
	explanation: str


def get_connection(
	dsn: str | None = _DATABASE_URL,
	host: str = _DB_HOST,
	port: int = _DB_PORT,
	dbname: str = _DB_NAME,
	user: str = _DB_USER,
	password: str = _DB_PASSWORD,
) -> psycopg2.extensions.connection:
	"""Open and return a PostgreSQL connection.

	Priority order:
	1) DATABASE_URL / DATABASE_PUBLIC_URL
	2) DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD
	"""

	if dsn:
		kwargs: dict[str, Any] = {}
		if _DB_SSLMODE and "sslmode=" not in dsn:
			kwargs["sslmode"] = _DB_SSLMODE
		try:
			return psycopg2.connect(dsn, **kwargs)
		except psycopg2.OperationalError:
			if _DATABASE_PUBLIC_URL and dsn != _DATABASE_PUBLIC_URL:
				return psycopg2.connect(_DATABASE_PUBLIC_URL, **kwargs)
			raise

	return psycopg2.connect(
		host=host, port=port, dbname=dbname, user=user, password=password
	)


def _load_sql_dump_via_psycopg2(conn: psycopg2.extensions.connection, sql_text: str) -> None:
	"""Execute a pg_dump plain SQL file, including COPY ... FROM stdin blocks, without psql."""

	skipped_prefixes = (
		"\\",
		"SET transaction_timeout",
	)

	with conn.cursor() as cur:
		def _execute_chunk_if_sql(lines_chunk: list[str]) -> None:
			if not lines_chunk:
				return

			# Avoid sending comment-only sections to PostgreSQL, which raises
			# "can't execute an empty query" in psycopg2.
			sql_lines = [
				ln
				for ln in lines_chunk
				if ln.strip() and not ln.lstrip().startswith("--")
			]
			if not sql_lines:
				return

			candidate = "".join(sql_lines).strip()
			if not candidate:
				return

			cur.execute(candidate)

		chunk: list[str] = []
		lines = sql_text.splitlines(keepends=True)
		i = 0

		while i < len(lines):
			line = lines[i]
			stripped = line.strip()

			if stripped.startswith(skipped_prefixes):
				i += 1
				continue

			if " OWNER TO " in line:
				i += 1
				continue

			if stripped.startswith("COPY ") and stripped.endswith("FROM stdin;"):
				_execute_chunk_if_sql(chunk)
				chunk = []

				copy_cmd = line
				i += 1
				copy_data: list[str] = []
				while i < len(lines):
					data_line = lines[i]
					if data_line.strip() == "\\.":
						break
					copy_data.append(data_line)
					i += 1

				cur.copy_expert(copy_cmd, io.StringIO("".join(copy_data)))
				i += 1
				continue

			chunk.append(line)
			i += 1

		_execute_chunk_if_sql(chunk)


def initialize_projectdb(
	dsn: str | None = _DATABASE_URL,
	host: str = _DB_HOST,
	port: int = _DB_PORT,
	dbname: str = _DB_NAME,
	user: str = _DB_USER,
	password: str = _DB_PASSWORD,
	sql_file: str | None = None,
) -> str:
	"""
	Create the `projectdb` database if needed and load the bundled `projectdb.sql` dump.

	Local flow (no DATABASE_URL):
	1) Create database using psql with user `postgres`
	2) Load projectdb.sql into that database with psql

	Hosted flow (DATABASE_URL): keeps psycopg2 loader path for managed DB URLs.
	"""

	target_sql = Path(sql_file) if sql_file else PROJECTDB_SQL_PATH
	if not target_sql.exists():
		raise FileNotFoundError(f"SQL file not found: {target_sql}")

	if dsn:
		conn = get_connection(dsn=dsn)
		conn.autocommit = True
		try:
			_load_sql_dump_via_psycopg2(conn, target_sql.read_text(encoding="utf-8"))
		finally:
			conn.close()
		return f"Loaded database from {target_sql} via DATABASE_URL"

	def _run_psql_command(args: list[str]) -> None:
		env = os.environ.copy()
		if password:
			env["PGPASSWORD"] = password
		proc = subprocess.run(
			args,
			capture_output=True,
			text=True,
			env=env,
			check=False,
		)
		if proc.returncode != 0:
			stderr = (proc.stderr or "").strip()
			stdout = (proc.stdout or "").strip()
			details = stderr or stdout or "Unknown psql error"
			raise RuntimeError(f"Command failed: {' '.join(args)}\n{details}")

	admin_user = "postgres"
	db_identifier = dbname.replace('"', '""')
	db_literal = dbname.replace("'", "''")
	create_db_sql = (
		f"SELECT 'CREATE DATABASE \"{db_identifier}\"' "
		f"WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '{db_literal}')\\gexec"
	)

	_run_psql_command([
		"psql",
		"-v",
		"ON_ERROR_STOP=1",
		"-h",
		host,
		"-p",
		str(port),
		"-U",
		admin_user,
		"-d",
		"postgres",
		"-c",
		create_db_sql,
	])

	_run_psql_command([
		"psql",
		"-v",
		"ON_ERROR_STOP=1",
		"-h",
		host,
		"-p",
		str(port),
		"-U",
		admin_user,
		"-d",
		dbname,
		"-f",
		str(target_sql),
	])

	return f"Created/verified {dbname} and loaded {target_sql} via psql as user postgres"


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

	age_above, age_below, age_is = _extract_age_bounds(lower)

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

	search_type = "clinical"
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

	status = None
	if "active" in lower:
		status = "Active"
	elif "discharged" in lower:
		status = "Discharged"

	return SearchQuery(
		raw_text=text,
		search_type=search_type,
		gender=gender,
		age_above=age_above,
		age_below=age_below,
		age_is=age_is,
		city=city,
		department=department,
		status=status,
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


def _table_has_column(conn, table_name: str, column_name: str) -> bool:
	"""Check whether a table contains a given column (schema-aware)."""

	if "." in table_name:
		schema_name, rel_name = table_name.split(".", 1)
	else:
		schema_name, rel_name = "public", table_name

	with conn.cursor() as cur:
		cur.execute(
			"""
			SELECT 1
			FROM information_schema.columns
			WHERE table_schema = %s
			  AND table_name = %s
			  AND column_name = %s
			LIMIT 1
			""",
			(schema_name, rel_name, column_name),
		)
		return cur.fetchone() is not None


def generate_sql(query: SearchQuery, include_patient_status: bool = True) -> GeneratedSQL:
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

	if query.age_is:
		conditions.append("DATE_PART('year', AGE(p.date_of_birth)) = %(age_is)s")
		params["age_is"] = query.age_is
		notes.append(f"age = {query.age_is}")

	# When both symptom and diagnosis resolve (often from the same term like
	# "diabetes"), combine them with OR so a patient matching EITHER is returned.
	if query.symptom and query.diagnosis:
		conditions.append(
			"(sy.symptom_name ILIKE %(symptom_lk)s OR syn.synonym ILIKE %(symptom_lk)s"
			" OR v.diagnosis ILIKE %(diagnosis_lk)s)"
		)
		params["symptom"] = query.symptom
		params["symptom_lk"] = f"%{query.symptom}%"
		params["diagnosis"] = query.diagnosis
		params["diagnosis_lk"] = f"%{query.diagnosis}%"
		notes.append(f"symptom = '{query.symptom}' OR diagnosis ~= '{query.diagnosis}'")
	elif query.symptom:
		conditions.append("(sy.symptom_name ILIKE %(symptom_lk)s OR syn.synonym ILIKE %(symptom_lk)s)")
		params["symptom"] = query.symptom
		params["symptom_lk"] = f"%{query.symptom}%"
		notes.append(f"symptom = '{query.symptom}' (+ synonyms)")
	elif query.diagnosis:
		conditions.append("v.diagnosis ILIKE %(diagnosis_lk)s")
		params["diagnosis"] = query.diagnosis
		params["diagnosis_lk"] = f"%{query.diagnosis}%"
		notes.append(f"diagnosis ~= '{query.diagnosis}'")


	if query.city:
		conditions.append("p.city ILIKE %(city)s")
		params["city"] = query.city
		notes.append(f"city = '{query.city}'")

	if query.department:
		conditions.append("d.specialization ILIKE %(department)s")
		params["department"] = query.department
		notes.append(f"department = '{query.department}'")

	if query.status and include_patient_status:
		conditions.append("p.status ILIKE %(status)s")
		params["status"] = query.status
		notes.append(f"status = '{query.status}'")

	# Keyword fallback: fire when there are unstructured terms not already handled by
	# explicit symptom/diagnosis filters.  This lets a query like
	# "age above 50 cancer patients" apply BOTH the age filter AND a 'cancer' keyword
	# filter — regardless of the detected search_type.
	keyword_terms = [
		term for term in (query.expanded_terms or [])
		if len(term) >= 3 and term not in _STOPWORDS
	]
	has_clinical_structured = query.symptom or query.diagnosis
	has_any_structured = any([
		query.gender, query.age_above, query.age_below,
		query.symptom, query.diagnosis, query.city, query.department,
	])
	# Apply keyword filter when:
	#   a) pure clinical query with no structured filters (original behaviour), OR
	#   b) any search type that has keywords but no symptom/diagnosis resolved
	should_apply_keywords = keyword_terms and not has_clinical_structured and (
		(query.search_type == "clinical" and not has_any_structured)
		or (query.search_type != "laboratory")
	)
	if should_apply_keywords:
		kw_clauses: list[str] = []
		for idx, kw in enumerate(sorted(set(keyword_terms))[:10]):
			key = f"kw_{idx}"
			params[key] = f"%{kw}%"
			# Build the OR columns — exclude columns already covered by a structured
			# filter OR that would contradict it.  E.g. if d.specialization='Cardiology'
			# is already in the WHERE clause, adding d.specialization ILIKE '%heart%' 
			# would always be false and cause 0 results.
			kw_cols = [
				f"p.first_name ILIKE %({key})s",
				f"p.last_name ILIKE %({key})s",
				f"p.city ILIKE %({key})s",
				f"v.diagnosis ILIKE %({key})s",
				f"sy.symptom_name ILIKE %({key})s",
				f"syn.synonym ILIKE %({key})s",
			]
			# Only search doctor specialization if no department filter already set
			if not query.department:
				kw_cols.append(f"d.specialization ILIKE %({key})s")
			kw_clauses.append("(" + " OR ".join(kw_cols) + ")")
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
			"    p.city,\n"
			+ ("    p.status" if include_patient_status else "    'Active'::text AS status")
		)

	sql = (
		f"SELECT DISTINCT\n{select_cols}\n"
		f"FROM patients p\n"
		f"{joins}"
		f"{where_clause}\n"
		f"ORDER BY p.patient_id;"
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
	Execute generated SQL and return patient rows.

	This is the single runtime search path used by nl_search_pipeline(), which
	keeps parsing/filter behavior in one place (Python) while persisting audit
	rows in DB tables.
	"""

	if sql_payload is None:
		raise ValueError("sql_payload is required for run_search()")

	query_id: int | None = None
	_repair_c13_write_sequences(conn)
	with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
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
			age=int(row.get("age", 0)),
			status=row.get("status", "Active")
		)
		for row in rows
	]

	return results, query_id


def _ensure_cohort_member_table(conn) -> None:
	"""Ensure patient_cohort_members exists for cohort/member persistence."""

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
	_repair_c13_write_sequences(conn)
	clean_query = " ".join(str(nl_query or "").split())[:80]
	cohort_name = clean_query or f"{search_type.title()} Cohort"
	norm_cohort_name = cohort_name.lower()

	with conn.cursor() as cur:
		cur.execute(
			"""
			SELECT cohort_id
			FROM patient_cohorts
			WHERE LOWER(REGEXP_REPLACE(TRIM(cohort_name), '\\s+', ' ', 'g')) = %s
			ORDER BY created_at DESC, cohort_id DESC
			LIMIT 1
			""",
			(norm_cohort_name,),
		)
		existing = cur.fetchone()
		if existing:
			cohort_id = int(existing[0])
			# Keep one cohort per generated name and refresh members for latest run.
			cur.execute("DELETE FROM patient_cohort_members WHERE cohort_id = %s", (cohort_id,))
		else:
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

	_repair_c13_write_sequences(conn)
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


def get_cohorts(conn) -> list[dict[str, Any]]:
	"""Return all patient cohorts from patient_cohorts."""

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
	has_patient_status_col = _table_has_column(conn, "patients", "status")
	parsed.expanded_terms = sorted(
		set(expand_terms(conn, normalized_query))
		| set(re.findall(r"[a-zA-Z]+", normalized_query))
	)
	parsed.symptom = resolve_symptom(conn, nl_query)
	parsed.diagnosis = resolve_diagnosis(conn, nl_query)
	sql_payload = generate_sql(parsed, include_patient_status=has_patient_status_col)

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
