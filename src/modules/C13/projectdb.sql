--
-- PostgreSQL database dump
--

\restrict besNBPp8R0NGjGVri9dtYseovWk7DreNs9YrWJH3vDezHfLWdntmMm5pzRgHZpg

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: create_cohort(text); Type: FUNCTION; Schema: public; Owner: gaurav
--

CREATE FUNCTION public.create_cohort(name text) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    cid INT;
BEGIN

INSERT INTO patient_cohorts(cohort_name)
VALUES(name)
RETURNING cohort_id INTO cid;

RETURN cid;

END;
$$;


ALTER FUNCTION public.create_cohort(name text) OWNER TO gaurav;

--
-- Name: expand_query_terms(text); Type: FUNCTION; Schema: public; Owner: gaurav
--

CREATE FUNCTION public.expand_query_terms(term text) RETURNS TABLE(expanded_term text)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT synonym
    FROM synonyms
    WHERE word = term;

    RETURN QUERY
    SELECT term;
END;
$$;


ALTER FUNCTION public.expand_query_terms(term text) OWNER TO gaurav;

--
-- Name: extract_age(text); Type: FUNCTION; Schema: public; Owner: gaurav
--

CREATE FUNCTION public.extract_age(q text) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    age_val INT;
BEGIN
    age_val := regexp_replace(q, '.*above ([0-9]+).*', '\1')::INT;
    RETURN age_val;
EXCEPTION
    WHEN others THEN
        RETURN NULL;
END;
$$;


ALTER FUNCTION public.extract_age(q text) OWNER TO gaurav;

--
-- Name: extract_gender(text); Type: FUNCTION; Schema: public; Owner: gaurav
--

CREATE FUNCTION public.extract_gender(q text) RETURNS text
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF q ILIKE '%male%' THEN
        RETURN 'male';
    ELSIF q ILIKE '%female%' THEN
        RETURN 'female';
    END IF;

    RETURN NULL;
END;
$$;


ALTER FUNCTION public.extract_gender(q text) OWNER TO gaurav;

--
-- Name: extract_symptom(text); Type: FUNCTION; Schema: public; Owner: gaurav
--

CREATE FUNCTION public.extract_symptom(q text) RETURNS text
    LANGUAGE plpgsql
    AS $$
DECLARE
    sym TEXT;
BEGIN

    -- direct symptom match
    SELECT symptom_name
    INTO sym
    FROM symptoms
    WHERE q ILIKE '%' || symptom_name || '%'
    LIMIT 1;

    IF sym IS NOT NULL THEN
        RETURN sym;
    END IF;

    -- synonym match
    SELECT s.word
    INTO sym
    FROM synonyms s
    WHERE q ILIKE '%' || s.synonym || '%'
    LIMIT 1;

    RETURN sym;

END;
$$;


ALTER FUNCTION public.extract_symptom(q text) OWNER TO gaurav;

--
-- Name: log_search_query(integer, text, text); Type: FUNCTION; Schema: public; Owner: gaurav
--

CREATE FUNCTION public.log_search_query(uid integer, q text, type text) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    qid INT;
BEGIN

    INSERT INTO search_queries(user_id,query_text,search_type)
    VALUES(uid,q,type)
    RETURNING query_id INTO qid;

    RETURN qid;

END;
$$;


ALTER FUNCTION public.log_search_query(uid integer, q text, type text) OWNER TO gaurav;

--
-- Name: run_patient_search(integer, text, text); Type: FUNCTION; Schema: public; Owner: gaurav
--

CREATE FUNCTION public.run_patient_search(uid integer, q text, search_type text) RETURNS TABLE(patient_id integer, first_name text, last_name text, gender text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    qid INT;
    cid INT;
BEGIN

    -- Step 1: log the search query
    qid := log_search_query(uid, q, search_type);

    -- Step 2: create a cohort
    INSERT INTO patient_cohorts(cohort_name)
    VALUES ('Cohort for query: ' || q)
    RETURNING cohort_id INTO cid;

    -- Step 3: run search and store results
    RETURN QUERY
    WITH results AS (
        SELECT * FROM search_patients_nl(q)
    )
    SELECT r.patient_id, r.first_name, r.last_name, r.gender
    FROM results r;

    -- Step 4: store results separately
    INSERT INTO search_results(query_id, patient_id, relevance_score)
    SELECT qid, r.patient_id, 1.0
    FROM search_patients_nl(q) r;

END;
$$;


ALTER FUNCTION public.run_patient_search(uid integer, q text, search_type text) OWNER TO gaurav;

--
-- Name: save_user_query(integer, text); Type: FUNCTION; Schema: public; Owner: gaurav
--

CREATE FUNCTION public.save_user_query(uid integer, q text) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN

INSERT INTO saved_queries(user_id,query_text)
VALUES(uid,q);

END;
$$;


ALTER FUNCTION public.save_user_query(uid integer, q text) OWNER TO gaurav;

--
-- Name: search_patients(text); Type: FUNCTION; Schema: public; Owner: gaurav
--

CREATE FUNCTION public.search_patients(symptom text) RETURNS TABLE(patient_id integer, name text)
    LANGUAGE plpgsql
    AS $$
BEGIN
RETURN QUERY
SELECT p.patient_id,p.first_name
FROM patients p
JOIN visits v ON p.patient_id=v.patient_id
JOIN patient_symptoms ps ON v.visit_id=ps.visit_id
JOIN symptoms s ON ps.symptom_id=s.symptom_id
WHERE s.symptom_name = symptom;
END;
$$;


ALTER FUNCTION public.search_patients(symptom text) OWNER TO gaurav;

--
-- Name: search_patients_nl(text); Type: FUNCTION; Schema: public; Owner: gaurav
--

CREATE FUNCTION public.search_patients_nl(q text) RETURNS TABLE(patient_id integer, first_name text, last_name text, gender text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    g TEXT;
    a INT;
    s TEXT;
BEGIN

    g := extract_gender(q);
    a := extract_age(q);
    s := extract_symptom(q);

    RETURN QUERY
    SELECT DISTINCT 
    p.patient_id,
    p.first_name,
    p.last_name,
    p.gender::TEXT
    FROM patients p
    LEFT JOIN visits v ON p.patient_id = v.patient_id
    LEFT JOIN patient_symptoms ps ON v.visit_id = ps.visit_id
    LEFT JOIN symptoms sy ON ps.symptom_id = sy.symptom_id
    WHERE
        (g IS NULL OR p.gender = g)
        AND
        (a IS NULL OR DATE_PART('year', AGE(p.date_of_birth)) > a)
        AND
        (s IS NULL OR sy.symptom_name = s);

END;
$$;


ALTER FUNCTION public.search_patients_nl(q text) OWNER TO gaurav;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: doctors; Type: TABLE; Schema: public; Owner: gaurav
--

CREATE TABLE public.doctors (
    doctor_id integer NOT NULL,
    doctor_name text NOT NULL,
    specialization text
);


ALTER TABLE public.doctors OWNER TO gaurav;

--
-- Name: doctors_doctor_id_seq; Type: SEQUENCE; Schema: public; Owner: gaurav
--

CREATE SEQUENCE public.doctors_doctor_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.doctors_doctor_id_seq OWNER TO gaurav;

--
-- Name: doctors_doctor_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaurav
--

ALTER SEQUENCE public.doctors_doctor_id_seq OWNED BY public.doctors.doctor_id;


--
-- Name: lab_results; Type: TABLE; Schema: public; Owner: gaurav
--

CREATE TABLE public.lab_results (
    result_id integer NOT NULL,
    visit_id integer,
    test_id integer,
    result_value numeric,
    result_date date
);


ALTER TABLE public.lab_results OWNER TO gaurav;

--
-- Name: lab_results_result_id_seq; Type: SEQUENCE; Schema: public; Owner: gaurav
--

CREATE SEQUENCE public.lab_results_result_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.lab_results_result_id_seq OWNER TO gaurav;

--
-- Name: lab_results_result_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaurav
--

ALTER SEQUENCE public.lab_results_result_id_seq OWNED BY public.lab_results.result_id;


--
-- Name: lab_tests; Type: TABLE; Schema: public; Owner: gaurav
--

CREATE TABLE public.lab_tests (
    test_id integer NOT NULL,
    test_name text
);


ALTER TABLE public.lab_tests OWNER TO gaurav;

--
-- Name: lab_tests_test_id_seq; Type: SEQUENCE; Schema: public; Owner: gaurav
--

CREATE SEQUENCE public.lab_tests_test_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.lab_tests_test_id_seq OWNER TO gaurav;

--
-- Name: lab_tests_test_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaurav
--

ALTER SEQUENCE public.lab_tests_test_id_seq OWNED BY public.lab_tests.test_id;


--
-- Name: patients; Type: TABLE; Schema: public; Owner: gaurav
--

CREATE TABLE public.patients (
    patient_id integer NOT NULL,
    first_name text NOT NULL,
    last_name text NOT NULL,
    gender character varying(10),
    date_of_birth date NOT NULL,
    phone character varying(15),
    city text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    search_vector tsvector,
    CONSTRAINT patients_gender_check CHECK (((gender)::text = ANY ((ARRAY['male'::character varying, 'female'::character varying, 'other'::character varying])::text[])))
);


ALTER TABLE public.patients OWNER TO gaurav;

--
-- Name: patient_age_view; Type: VIEW; Schema: public; Owner: gaurav
--

CREATE VIEW public.patient_age_view AS
 SELECT patient_id,
    first_name,
    last_name,
    gender,
    date_part('year'::text, age((date_of_birth)::timestamp with time zone)) AS age,
    city
   FROM public.patients;


ALTER VIEW public.patient_age_view OWNER TO gaurav;

--
-- Name: patient_cohorts; Type: TABLE; Schema: public; Owner: gaurav
--

CREATE TABLE public.patient_cohorts (
    cohort_id integer NOT NULL,
    cohort_name text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.patient_cohorts OWNER TO gaurav;

--
-- Name: patient_cohorts_cohort_id_seq; Type: SEQUENCE; Schema: public; Owner: gaurav
--

CREATE SEQUENCE public.patient_cohorts_cohort_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.patient_cohorts_cohort_id_seq OWNER TO gaurav;

--
-- Name: patient_cohorts_cohort_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaurav
--

ALTER SEQUENCE public.patient_cohorts_cohort_id_seq OWNED BY public.patient_cohorts.cohort_id;


--
-- Name: patient_symptoms; Type: TABLE; Schema: public; Owner: gaurav
--

CREATE TABLE public.patient_symptoms (
    record_id integer NOT NULL,
    visit_id integer,
    symptom_id integer
);


ALTER TABLE public.patient_symptoms OWNER TO gaurav;

--
-- Name: patient_symptoms_record_id_seq; Type: SEQUENCE; Schema: public; Owner: gaurav
--

CREATE SEQUENCE public.patient_symptoms_record_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.patient_symptoms_record_id_seq OWNER TO gaurav;

--
-- Name: patient_symptoms_record_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaurav
--

ALTER SEQUENCE public.patient_symptoms_record_id_seq OWNED BY public.patient_symptoms.record_id;


--
-- Name: patient_visit_summary; Type: VIEW; Schema: public; Owner: gaurav
--

CREATE VIEW public.patient_visit_summary AS
SELECT
    NULL::integer AS patient_id,
    NULL::text AS first_name,
    NULL::bigint AS total_visits;


ALTER VIEW public.patient_visit_summary OWNER TO gaurav;

--
-- Name: patients_patient_id_seq; Type: SEQUENCE; Schema: public; Owner: gaurav
--

CREATE SEQUENCE public.patients_patient_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.patients_patient_id_seq OWNER TO gaurav;

--
-- Name: patients_patient_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaurav
--

ALTER SEQUENCE public.patients_patient_id_seq OWNED BY public.patients.patient_id;


--
-- Name: query_templates; Type: TABLE; Schema: public; Owner: gaurav
--

CREATE TABLE public.query_templates (
    template_id integer NOT NULL,
    template_pattern text,
    sql_template text,
    description text
);


ALTER TABLE public.query_templates OWNER TO gaurav;

--
-- Name: query_templates_template_id_seq; Type: SEQUENCE; Schema: public; Owner: gaurav
--

CREATE SEQUENCE public.query_templates_template_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.query_templates_template_id_seq OWNER TO gaurav;

--
-- Name: query_templates_template_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaurav
--

ALTER SEQUENCE public.query_templates_template_id_seq OWNED BY public.query_templates.template_id;


--
-- Name: saved_queries; Type: TABLE; Schema: public; Owner: gaurav
--

CREATE TABLE public.saved_queries (
    saved_id integer NOT NULL,
    user_id integer,
    query_text text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.saved_queries OWNER TO gaurav;

--
-- Name: saved_queries_saved_id_seq; Type: SEQUENCE; Schema: public; Owner: gaurav
--

CREATE SEQUENCE public.saved_queries_saved_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.saved_queries_saved_id_seq OWNER TO gaurav;

--
-- Name: saved_queries_saved_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaurav
--

ALTER SEQUENCE public.saved_queries_saved_id_seq OWNED BY public.saved_queries.saved_id;


--
-- Name: search_queries; Type: TABLE; Schema: public; Owner: gaurav
--

CREATE TABLE public.search_queries (
    query_id integer NOT NULL,
    query_text text NOT NULL,
    search_type character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    user_id integer
);


ALTER TABLE public.search_queries OWNER TO gaurav;

--
-- Name: search_queries_query_id_seq; Type: SEQUENCE; Schema: public; Owner: gaurav
--

CREATE SEQUENCE public.search_queries_query_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.search_queries_query_id_seq OWNER TO gaurav;

--
-- Name: search_queries_query_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaurav
--

ALTER SEQUENCE public.search_queries_query_id_seq OWNED BY public.search_queries.query_id;


--
-- Name: search_results; Type: TABLE; Schema: public; Owner: gaurav
--

CREATE TABLE public.search_results (
    result_id integer NOT NULL,
    query_id integer,
    patient_id integer,
    relevance_score numeric
);


ALTER TABLE public.search_results OWNER TO gaurav;

--
-- Name: search_results_result_id_seq; Type: SEQUENCE; Schema: public; Owner: gaurav
--

CREATE SEQUENCE public.search_results_result_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.search_results_result_id_seq OWNER TO gaurav;

--
-- Name: search_results_result_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaurav
--

ALTER SEQUENCE public.search_results_result_id_seq OWNED BY public.search_results.result_id;


--
-- Name: symptom_hierarchy; Type: TABLE; Schema: public; Owner: gaurav
--

CREATE TABLE public.symptom_hierarchy (
    parent_symptom integer,
    child_symptom integer
);


ALTER TABLE public.symptom_hierarchy OWNER TO gaurav;

--
-- Name: symptoms; Type: TABLE; Schema: public; Owner: gaurav
--

CREATE TABLE public.symptoms (
    symptom_id integer NOT NULL,
    symptom_name text NOT NULL
);


ALTER TABLE public.symptoms OWNER TO gaurav;

--
-- Name: symptoms_symptom_id_seq; Type: SEQUENCE; Schema: public; Owner: gaurav
--

CREATE SEQUENCE public.symptoms_symptom_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.symptoms_symptom_id_seq OWNER TO gaurav;

--
-- Name: symptoms_symptom_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaurav
--

ALTER SEQUENCE public.symptoms_symptom_id_seq OWNED BY public.symptoms.symptom_id;


--
-- Name: synonyms; Type: TABLE; Schema: public; Owner: gaurav
--

CREATE TABLE public.synonyms (
    synonym_id integer NOT NULL,
    word text,
    synonym text
);


ALTER TABLE public.synonyms OWNER TO gaurav;

--
-- Name: synonyms_synonym_id_seq; Type: SEQUENCE; Schema: public; Owner: gaurav
--

CREATE SEQUENCE public.synonyms_synonym_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.synonyms_synonym_id_seq OWNER TO gaurav;

--
-- Name: synonyms_synonym_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaurav
--

ALTER SEQUENCE public.synonyms_synonym_id_seq OWNED BY public.synonyms.synonym_id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: gaurav
--

CREATE TABLE public.users (
    user_id integer NOT NULL,
    username text NOT NULL,
    role character varying(20),
    department text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.users OWNER TO gaurav;

--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: gaurav
--

CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_user_id_seq OWNER TO gaurav;

--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaurav
--

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;


--
-- Name: visits; Type: TABLE; Schema: public; Owner: gaurav
--

CREATE TABLE public.visits (
    visit_id integer NOT NULL,
    patient_id integer,
    doctor_id integer,
    visit_date date NOT NULL,
    diagnosis text,
    notes text
);


ALTER TABLE public.visits OWNER TO gaurav;

--
-- Name: visits_visit_id_seq; Type: SEQUENCE; Schema: public; Owner: gaurav
--

CREATE SEQUENCE public.visits_visit_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.visits_visit_id_seq OWNER TO gaurav;

--
-- Name: visits_visit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaurav
--

ALTER SEQUENCE public.visits_visit_id_seq OWNED BY public.visits.visit_id;


--
-- Name: doctors doctor_id; Type: DEFAULT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.doctors ALTER COLUMN doctor_id SET DEFAULT nextval('public.doctors_doctor_id_seq'::regclass);


--
-- Name: lab_results result_id; Type: DEFAULT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.lab_results ALTER COLUMN result_id SET DEFAULT nextval('public.lab_results_result_id_seq'::regclass);


--
-- Name: lab_tests test_id; Type: DEFAULT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.lab_tests ALTER COLUMN test_id SET DEFAULT nextval('public.lab_tests_test_id_seq'::regclass);


--
-- Name: patient_cohorts cohort_id; Type: DEFAULT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.patient_cohorts ALTER COLUMN cohort_id SET DEFAULT nextval('public.patient_cohorts_cohort_id_seq'::regclass);


--
-- Name: patient_symptoms record_id; Type: DEFAULT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.patient_symptoms ALTER COLUMN record_id SET DEFAULT nextval('public.patient_symptoms_record_id_seq'::regclass);


--
-- Name: patients patient_id; Type: DEFAULT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.patients ALTER COLUMN patient_id SET DEFAULT nextval('public.patients_patient_id_seq'::regclass);


--
-- Name: query_templates template_id; Type: DEFAULT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.query_templates ALTER COLUMN template_id SET DEFAULT nextval('public.query_templates_template_id_seq'::regclass);


--
-- Name: saved_queries saved_id; Type: DEFAULT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.saved_queries ALTER COLUMN saved_id SET DEFAULT nextval('public.saved_queries_saved_id_seq'::regclass);


--
-- Name: search_queries query_id; Type: DEFAULT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.search_queries ALTER COLUMN query_id SET DEFAULT nextval('public.search_queries_query_id_seq'::regclass);


--
-- Name: search_results result_id; Type: DEFAULT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.search_results ALTER COLUMN result_id SET DEFAULT nextval('public.search_results_result_id_seq'::regclass);


--
-- Name: symptoms symptom_id; Type: DEFAULT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.symptoms ALTER COLUMN symptom_id SET DEFAULT nextval('public.symptoms_symptom_id_seq'::regclass);


--
-- Name: synonyms synonym_id; Type: DEFAULT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.synonyms ALTER COLUMN synonym_id SET DEFAULT nextval('public.synonyms_synonym_id_seq'::regclass);


--
-- Name: users user_id; Type: DEFAULT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.users ALTER COLUMN user_id SET DEFAULT nextval('public.users_user_id_seq'::regclass);


--
-- Name: visits visit_id; Type: DEFAULT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.visits ALTER COLUMN visit_id SET DEFAULT nextval('public.visits_visit_id_seq'::regclass);


--
-- Data for Name: doctors; Type: TABLE DATA; Schema: public; Owner: gaurav
--

COPY public.doctors (doctor_id, doctor_name, specialization) FROM stdin;
1	Dr Mehta	Cardiology
2	Dr Singh	General Medicine
3	Dr Sharma	Neurology
4	Dr Patel	Pulmonology
5	Dr Verma	Endocrinology
\.


--
-- Data for Name: lab_results; Type: TABLE DATA; Schema: public; Owner: gaurav
--

COPY public.lab_results (result_id, visit_id, test_id, result_value, result_date) FROM stdin;
1	1	1	150	2025-03-01
2	2	1	110	2025-03-02
3	3	3	13	2025-03-02
4	4	3	12	2025-03-03
5	5	2	210	2025-03-04
6	6	1	130	2025-03-04
7	7	1	180	2025-03-05
8	8	3	11	2025-03-06
9	9	2	190	2025-03-07
10	10	1	120	2025-03-08
11	11	1	240	2025-03-08
12	12	2	200	2025-03-09
13	13	2	220	2025-03-10
14	14	3	12	2025-03-10
15	15	1	140	2025-03-11
\.


--
-- Data for Name: lab_tests; Type: TABLE DATA; Schema: public; Owner: gaurav
--

COPY public.lab_tests (test_id, test_name) FROM stdin;
1	glucose
2	cholesterol
3	hemoglobin
\.


--
-- Data for Name: patient_cohorts; Type: TABLE DATA; Schema: public; Owner: gaurav
--

COPY public.patient_cohorts (cohort_id, cohort_name, created_at) FROM stdin;
1	Cohort for query: patients with fever	2026-03-16 18:42:24.849254
2	Cohort for query: patients with pyrexia	2026-03-16 18:42:38.335751
3	Cohort for query: female patients with cephalalgia	2026-03-16 18:42:44.693787
4	Cohort for query: patients with tussis	2026-03-16 18:46:50.006386
\.


--
-- Data for Name: patient_symptoms; Type: TABLE DATA; Schema: public; Owner: gaurav
--

COPY public.patient_symptoms (record_id, visit_id, symptom_id) FROM stdin;
1	1	1
2	2	1
3	2	2
4	3	3
5	4	3
6	5	2
7	6	5
8	7	1
9	8	3
10	9	6
11	10	7
12	11	5
13	12	2
14	13	4
15	14	3
16	15	5
\.


--
-- Data for Name: patients; Type: TABLE DATA; Schema: public; Owner: gaurav
--

COPY public.patients (patient_id, first_name, last_name, gender, date_of_birth, phone, city, created_at, search_vector) FROM stdin;
1	Rahul	Sharma	male	1975-02-10	\N	Delhi	2026-03-16 18:40:22.922058	\N
2	Amit	Verma	male	1980-06-20	\N	Mumbai	2026-03-16 18:40:22.922058	\N
3	Neha	Singh	female	1990-05-01	\N	Delhi	2026-03-16 18:40:22.922058	\N
4	Riya	Gupta	female	2001-01-01	\N	Kolkata	2026-03-16 18:40:22.922058	\N
5	Karan	Malhotra	male	1972-03-14	\N	Delhi	2026-03-16 18:40:22.922058	\N
6	Pooja	Mehta	female	1985-08-19	\N	Mumbai	2026-03-16 18:40:22.922058	\N
7	Arjun	Kapoor	male	1995-12-12	\N	Delhi	2026-03-16 18:40:22.922058	\N
8	Sneha	Iyer	female	1988-07-07	\N	Chennai	2026-03-16 18:40:22.922058	\N
9	Rohit	Das	male	1970-04-04	\N	Kolkata	2026-03-16 18:40:22.922058	\N
10	Priya	Shah	female	1992-09-09	\N	Ahmedabad	2026-03-16 18:40:22.922058	\N
11	Anil	Reddy	male	1968-03-21	\N	Hyderabad	2026-03-16 18:40:22.922058	\N
12	Kavita	Nair	female	1979-11-30	\N	Kochi	2026-03-16 18:40:22.922058	\N
13	Vikas	Yadav	male	1983-10-10	\N	Delhi	2026-03-16 18:40:22.922058	\N
14	Ananya	Sen	female	1997-06-15	\N	Kolkata	2026-03-16 18:40:22.922058	\N
15	Suresh	Patel	male	1976-12-05	\N	Ahmedabad	2026-03-16 18:40:22.922058	\N
\.


--
-- Data for Name: query_templates; Type: TABLE DATA; Schema: public; Owner: gaurav
--

COPY public.query_templates (template_id, template_pattern, sql_template, description) FROM stdin;
1	patients with {symptom}	SELECT p.patient_id,p.first_name\n FROM patients p\n JOIN visits v ON p.patient_id=v.patient_id\n JOIN patient_symptoms ps ON v.visit_id=ps.visit_id\n JOIN symptoms s ON ps.symptom_id=s.symptom_id\n WHERE s.symptom_name = '{symptom}'	\N
\.


--
-- Data for Name: saved_queries; Type: TABLE DATA; Schema: public; Owner: gaurav
--

COPY public.saved_queries (saved_id, user_id, query_text, created_at) FROM stdin;
\.


--
-- Data for Name: search_queries; Type: TABLE DATA; Schema: public; Owner: gaurav
--

COPY public.search_queries (query_id, query_text, search_type, created_at, user_id) FROM stdin;
1	patients with fever	clinical	2026-03-16 18:42:24.849254	1
2	patients with pyrexia	clinical	2026-03-16 18:42:38.335751	1
3	female patients with cephalalgia	clinical	2026-03-16 18:42:44.693787	2
4	patients with tussis	clinical	2026-03-16 18:46:50.006386	1
\.


--
-- Data for Name: search_results; Type: TABLE DATA; Schema: public; Owner: gaurav
--

COPY public.search_results (result_id, query_id, patient_id, relevance_score) FROM stdin;
1	1	1	1.0
2	1	2	1.0
3	1	7	1.0
4	2	1	1.0
5	2	2	1.0
6	2	7	1.0
7	4	2	1.0
8	4	5	1.0
9	4	12	1.0
\.


--
-- Data for Name: symptom_hierarchy; Type: TABLE DATA; Schema: public; Owner: gaurav
--

COPY public.symptom_hierarchy (parent_symptom, child_symptom) FROM stdin;
\.


--
-- Data for Name: symptoms; Type: TABLE DATA; Schema: public; Owner: gaurav
--

COPY public.symptoms (symptom_id, symptom_name) FROM stdin;
1	fever
2	cough
3	headache
4	chest pain
5	fatigue
6	shortness of breath
7	nausea
\.


--
-- Data for Name: synonyms; Type: TABLE DATA; Schema: public; Owner: gaurav
--

COPY public.synonyms (synonym_id, word, synonym) FROM stdin;
1	fever	pyrexia
2	cough	tussis
3	headache	cephalalgia
4	fatigue	tiredness
5	chest pain	angina
6	shortness of breath	dyspnea
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: gaurav
--

COPY public.users (user_id, username, role, department, created_at) FROM stdin;
1	dr_mehta	doctor	cardiology	2026-03-16 18:40:17.411923
2	dr_singh	doctor	general medicine	2026-03-16 18:40:17.411923
3	dr_sharma	doctor	neurology	2026-03-16 18:40:17.411923
4	researcher1	researcher	epidemiology	2026-03-16 18:40:17.411923
5	admin	admin	system	2026-03-16 18:40:17.411923
\.


--
-- Data for Name: visits; Type: TABLE DATA; Schema: public; Owner: gaurav
--

COPY public.visits (visit_id, patient_id, doctor_id, visit_date, diagnosis, notes) FROM stdin;
1	1	1	2025-03-01	viral fever	\N
2	2	2	2025-03-02	flu	\N
3	3	2	2025-03-02	migraine	\N
4	4	3	2025-03-03	headache	\N
5	5	4	2025-03-04	bronchitis	\N
6	6	1	2025-03-04	fatigue	\N
7	7	2	2025-03-05	viral fever	\N
8	8	3	2025-03-06	migraine	\N
9	9	4	2025-03-07	asthma	\N
10	10	2	2025-03-08	nausea	\N
11	11	5	2025-03-08	diabetes	\N
12	12	2	2025-03-09	flu	\N
13	13	1	2025-03-10	chest pain	\N
14	14	3	2025-03-10	migraine	\N
15	15	1	2025-03-11	fatigue	\N
\.


--
-- Name: doctors_doctor_id_seq; Type: SEQUENCE SET; Schema: public; Owner: gaurav
--

SELECT pg_catalog.setval('public.doctors_doctor_id_seq', 5, true);


--
-- Name: lab_results_result_id_seq; Type: SEQUENCE SET; Schema: public; Owner: gaurav
--

SELECT pg_catalog.setval('public.lab_results_result_id_seq', 15, true);


--
-- Name: lab_tests_test_id_seq; Type: SEQUENCE SET; Schema: public; Owner: gaurav
--

SELECT pg_catalog.setval('public.lab_tests_test_id_seq', 3, true);


--
-- Name: patient_cohorts_cohort_id_seq; Type: SEQUENCE SET; Schema: public; Owner: gaurav
--

SELECT pg_catalog.setval('public.patient_cohorts_cohort_id_seq', 4, true);


--
-- Name: patient_symptoms_record_id_seq; Type: SEQUENCE SET; Schema: public; Owner: gaurav
--

SELECT pg_catalog.setval('public.patient_symptoms_record_id_seq', 16, true);


--
-- Name: patients_patient_id_seq; Type: SEQUENCE SET; Schema: public; Owner: gaurav
--

SELECT pg_catalog.setval('public.patients_patient_id_seq', 15, true);


--
-- Name: query_templates_template_id_seq; Type: SEQUENCE SET; Schema: public; Owner: gaurav
--

SELECT pg_catalog.setval('public.query_templates_template_id_seq', 1, true);


--
-- Name: saved_queries_saved_id_seq; Type: SEQUENCE SET; Schema: public; Owner: gaurav
--

SELECT pg_catalog.setval('public.saved_queries_saved_id_seq', 1, false);


--
-- Name: search_queries_query_id_seq; Type: SEQUENCE SET; Schema: public; Owner: gaurav
--

SELECT pg_catalog.setval('public.search_queries_query_id_seq', 4, true);


--
-- Name: search_results_result_id_seq; Type: SEQUENCE SET; Schema: public; Owner: gaurav
--

SELECT pg_catalog.setval('public.search_results_result_id_seq', 9, true);


--
-- Name: symptoms_symptom_id_seq; Type: SEQUENCE SET; Schema: public; Owner: gaurav
--

SELECT pg_catalog.setval('public.symptoms_symptom_id_seq', 7, true);


--
-- Name: synonyms_synonym_id_seq; Type: SEQUENCE SET; Schema: public; Owner: gaurav
--

SELECT pg_catalog.setval('public.synonyms_synonym_id_seq', 6, true);


--
-- Name: users_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: gaurav
--

SELECT pg_catalog.setval('public.users_user_id_seq', 5, true);


--
-- Name: visits_visit_id_seq; Type: SEQUENCE SET; Schema: public; Owner: gaurav
--

SELECT pg_catalog.setval('public.visits_visit_id_seq', 15, true);


--
-- Name: doctors doctors_pkey; Type: CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.doctors
    ADD CONSTRAINT doctors_pkey PRIMARY KEY (doctor_id);


--
-- Name: lab_results lab_results_pkey; Type: CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.lab_results
    ADD CONSTRAINT lab_results_pkey PRIMARY KEY (result_id);


--
-- Name: lab_tests lab_tests_pkey; Type: CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.lab_tests
    ADD CONSTRAINT lab_tests_pkey PRIMARY KEY (test_id);


--
-- Name: patient_cohorts patient_cohorts_pkey; Type: CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.patient_cohorts
    ADD CONSTRAINT patient_cohorts_pkey PRIMARY KEY (cohort_id);


--
-- Name: patient_symptoms patient_symptoms_pkey; Type: CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.patient_symptoms
    ADD CONSTRAINT patient_symptoms_pkey PRIMARY KEY (record_id);


--
-- Name: patients patients_pkey; Type: CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT patients_pkey PRIMARY KEY (patient_id);


--
-- Name: query_templates query_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.query_templates
    ADD CONSTRAINT query_templates_pkey PRIMARY KEY (template_id);


--
-- Name: saved_queries saved_queries_pkey; Type: CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.saved_queries
    ADD CONSTRAINT saved_queries_pkey PRIMARY KEY (saved_id);


--
-- Name: search_queries search_queries_pkey; Type: CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.search_queries
    ADD CONSTRAINT search_queries_pkey PRIMARY KEY (query_id);


--
-- Name: search_results search_results_pkey; Type: CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.search_results
    ADD CONSTRAINT search_results_pkey PRIMARY KEY (result_id);


--
-- Name: symptoms symptoms_pkey; Type: CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.symptoms
    ADD CONSTRAINT symptoms_pkey PRIMARY KEY (symptom_id);


--
-- Name: symptoms symptoms_symptom_name_key; Type: CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.symptoms
    ADD CONSTRAINT symptoms_symptom_name_key UNIQUE (symptom_name);


--
-- Name: synonyms synonyms_pkey; Type: CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.synonyms
    ADD CONSTRAINT synonyms_pkey PRIMARY KEY (synonym_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: visits visits_pkey; Type: CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.visits
    ADD CONSTRAINT visits_pkey PRIMARY KEY (visit_id);


--
-- Name: patient_search_idx; Type: INDEX; Schema: public; Owner: gaurav
--

CREATE INDEX patient_search_idx ON public.patients USING gin (search_vector);


--
-- Name: patient_visit_summary _RETURN; Type: RULE; Schema: public; Owner: gaurav
--

CREATE OR REPLACE VIEW public.patient_visit_summary AS
 SELECT p.patient_id,
    p.first_name,
    count(v.visit_id) AS total_visits
   FROM (public.patients p
     LEFT JOIN public.visits v ON ((p.patient_id = v.patient_id)))
  GROUP BY p.patient_id;


--
-- Name: lab_results lab_results_test_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.lab_results
    ADD CONSTRAINT lab_results_test_id_fkey FOREIGN KEY (test_id) REFERENCES public.lab_tests(test_id);


--
-- Name: lab_results lab_results_visit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.lab_results
    ADD CONSTRAINT lab_results_visit_id_fkey FOREIGN KEY (visit_id) REFERENCES public.visits(visit_id);


--
-- Name: patient_symptoms patient_symptoms_symptom_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.patient_symptoms
    ADD CONSTRAINT patient_symptoms_symptom_id_fkey FOREIGN KEY (symptom_id) REFERENCES public.symptoms(symptom_id);


--
-- Name: patient_symptoms patient_symptoms_visit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.patient_symptoms
    ADD CONSTRAINT patient_symptoms_visit_id_fkey FOREIGN KEY (visit_id) REFERENCES public.visits(visit_id) ON DELETE CASCADE;


--
-- Name: saved_queries saved_queries_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.saved_queries
    ADD CONSTRAINT saved_queries_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: search_queries search_queries_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.search_queries
    ADD CONSTRAINT search_queries_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: search_results search_results_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.search_results
    ADD CONSTRAINT search_results_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(patient_id);


--
-- Name: search_results search_results_query_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.search_results
    ADD CONSTRAINT search_results_query_id_fkey FOREIGN KEY (query_id) REFERENCES public.search_queries(query_id);


--
-- Name: visits visits_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.visits
    ADD CONSTRAINT visits_doctor_id_fkey FOREIGN KEY (doctor_id) REFERENCES public.doctors(doctor_id);


--
-- Name: visits visits_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gaurav
--

ALTER TABLE ONLY public.visits
    ADD CONSTRAINT visits_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(patient_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict besNBPp8R0NGjGVri9dtYseovWk7DreNs9YrWJH3vDezHfLWdntmMm5pzRgHZpg

