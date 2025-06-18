--
-- PostgreSQL database dump
--

-- Dumped from database version 14.17 (Homebrew)
-- Dumped by pg_dump version 14.17 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: JobPosting; Type: TABLE; Schema: public; Owner: datajob_user
--

CREATE TABLE public."JobPosting" (
    posting_id integer NOT NULL,
    company_id integer,
    platform_id integer,
    title character varying(200),
    job_type character varying(50),
    location character varying(100),
    "position" character varying(20),
    experience_min character varying(20),
    experience_max character varying(20),
    education character varying(20),
    tech_stack character varying(100),
    is_data_job boolean,
    url character varying(500),
    apply_end_date character varying(10),
    crawled_at timestamp without time zone
);


ALTER TABLE public."JobPosting" OWNER TO datajob_user;

--
-- Name: JobPosting_posting_id_seq; Type: SEQUENCE; Schema: public; Owner: datajob_user
--

CREATE SEQUENCE public."JobPosting_posting_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public."JobPosting_posting_id_seq" OWNER TO datajob_user;

--
-- Name: JobPosting_posting_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: datajob_user
--

ALTER SEQUENCE public."JobPosting_posting_id_seq" OWNED BY public."JobPosting".posting_id;


--
-- Name: jobposting; Type: TABLE; Schema: public; Owner: datajob_user
--

CREATE TABLE public.jobposting (
    posting_id bigint NOT NULL,
    company_id integer,
    platform_id integer,
    title character varying(200) NOT NULL,
    job_type character varying(50),
    location character varying(100),
    "position" character varying(50),
    experience_min character varying(20),
    experience_max character varying(20),
    education character varying(20),
    tech_stack character varying(255),
    is_data_job boolean,
    url character varying(500),
    apply_end_date character varying(20),
    crawled_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.jobposting OWNER TO datajob_user;

--
-- Name: TABLE jobposting; Type: COMMENT; Schema: public; Owner: datajob_user
--

COMMENT ON TABLE public.jobposting IS '채용 공고 정보를 저장하는 테이블';


--
-- Name: COLUMN jobposting.posting_id; Type: COMMENT; Schema: public; Owner: datajob_user
--

COMMENT ON COLUMN public.jobposting.posting_id IS '공고 고유 ID (PK)';


--
-- Name: COLUMN jobposting.company_id; Type: COMMENT; Schema: public; Owner: datajob_user
--

COMMENT ON COLUMN public.jobposting.company_id IS '회사 ID (FK)';


--
-- Name: COLUMN jobposting.platform_id; Type: COMMENT; Schema: public; Owner: datajob_user
--

COMMENT ON COLUMN public.jobposting.platform_id IS '공고가 수집된 플랫폼 ID (FK)';


--
-- Name: COLUMN jobposting.title; Type: COMMENT; Schema: public; Owner: datajob_user
--

COMMENT ON COLUMN public.jobposting.title IS '공고 제목';


--
-- Name: COLUMN jobposting.job_type; Type: COMMENT; Schema: public; Owner: datajob_user
--

COMMENT ON COLUMN public.jobposting.job_type IS '근무 형태 (예: 정규직, 계약직, 인턴)';


--
-- Name: COLUMN jobposting.location; Type: COMMENT; Schema: public; Owner: datajob_user
--

COMMENT ON COLUMN public.jobposting.location IS '근무 지역';


--
-- Name: COLUMN jobposting."position"; Type: COMMENT; Schema: public; Owner: datajob_user
--

COMMENT ON COLUMN public.jobposting."position" IS '채용 포지션 (예: 데이터 엔지니어, 백엔드 개발자)';


--
-- Name: COLUMN jobposting.experience_min; Type: COMMENT; Schema: public; Owner: datajob_user
--

COMMENT ON COLUMN public.jobposting.experience_min IS '요구 최소 경력 (예: 신입, 3년)';


--
-- Name: COLUMN jobposting.experience_max; Type: COMMENT; Schema: public; Owner: datajob_user
--

COMMENT ON COLUMN public.jobposting.experience_max IS '요구 최대 경력 (예: 5년, 무관)';


--
-- Name: COLUMN jobposting.education; Type: COMMENT; Schema: public; Owner: datajob_user
--

COMMENT ON COLUMN public.jobposting.education IS '학력 조건 (예: 학사 이상, 무관)';


--
-- Name: COLUMN jobposting.tech_stack; Type: COMMENT; Schema: public; Owner: datajob_user
--

COMMENT ON COLUMN public.jobposting.tech_stack IS '주요 기술 스택 (콤마로 구분)';


--
-- Name: COLUMN jobposting.is_data_job; Type: COMMENT; Schema: public; Owner: datajob_user
--

COMMENT ON COLUMN public.jobposting.is_data_job IS '데이터 관련 직무 여부';


--
-- Name: COLUMN jobposting.url; Type: COMMENT; Schema: public; Owner: datajob_user
--

COMMENT ON COLUMN public.jobposting.url IS '원본 채용 공고 링크';


--
-- Name: COLUMN jobposting.apply_end_date; Type: COMMENT; Schema: public; Owner: datajob_user
--

COMMENT ON COLUMN public.jobposting.apply_end_date IS '공고 접수 마감일';


--
-- Name: COLUMN jobposting.crawled_at; Type: COMMENT; Schema: public; Owner: datajob_user
--

COMMENT ON COLUMN public.jobposting.crawled_at IS '데이터 수집(크롤링)된 시각';


--
-- Name: jobposting_posting_id_seq; Type: SEQUENCE; Schema: public; Owner: datajob_user
--

CREATE SEQUENCE public.jobposting_posting_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.jobposting_posting_id_seq OWNER TO datajob_user;

--
-- Name: jobposting_posting_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: datajob_user
--

ALTER SEQUENCE public.jobposting_posting_id_seq OWNED BY public.jobposting.posting_id;


--
-- Name: JobPosting posting_id; Type: DEFAULT; Schema: public; Owner: datajob_user
--

ALTER TABLE ONLY public."JobPosting" ALTER COLUMN posting_id SET DEFAULT nextval('public."JobPosting_posting_id_seq"'::regclass);


--
-- Name: jobposting posting_id; Type: DEFAULT; Schema: public; Owner: datajob_user
--

ALTER TABLE ONLY public.jobposting ALTER COLUMN posting_id SET DEFAULT nextval('public.jobposting_posting_id_seq'::regclass);


--
-- Data for Name: JobPosting; Type: TABLE DATA; Schema: public; Owner: datajob_user
--

COPY public."JobPosting" (posting_id, company_id, platform_id, title, job_type, location, "position", experience_min, experience_max, education, tech_stack, is_data_job, url, apply_end_date, crawled_at) FROM stdin;
\.


--
-- Data for Name: jobposting; Type: TABLE DATA; Schema: public; Owner: datajob_user
--

COPY public.jobposting (posting_id, company_id, platform_id, title, job_type, location, "position", experience_min, experience_max, education, tech_stack, is_data_job, url, apply_end_date, crawled_at) FROM stdin;
151	101	2	[쿠팡] 데이터 분석가 모집	정규직	경기 성남시	데이터 분석가	신입	3년	재학생/휴학생	SQL, Python, R, Tableau	t	https://career.쿠팡.com/job/111	2025-08-17	2025-06-15 23:08:07.553804+09
152	102	2	[라인] 백엔드 개발자 모집	정규직	서울 강남구	백엔드 개발자	2년	무관	재학생/휴학생	Java, Kotlin, Spring, AWS	f	https://career.라인.com/job/112	2025-09-03	2025-06-15 23:08:07.553804+09
153	103	1	[SKT] 머신러닝 엔지니어 모집	인턴	서울 강남구	머신러닝 엔지니어	5년	10년	학사 이상	Python, Scikit-learn, Docker	t	https://career.skt.com/job/113	2025-08-24	2025-06-15 23:08:07.553804+09
154	104	2	[삼성전자] AI 엔지니어 모집	인턴	제주 제주시	AI 엔지니어	5년	10년	학사 이상	Python, TensorFlow, PyTorch, K8s	t	https://career.삼성전자.com/job/114	상시채용	2025-06-15 23:08:07.553804+09
155	105	3	[당근마켓] 데이터 사이언티스트 모집	정규직	서울 중구	데이터 사이언티스트	3년	7년	무관	Python, SQL, MLflow, Airflow	t	https://career.당근마켓.com/job/115	2025-07-28	2025-06-15 23:08:07.553804+09
156	106	2	[배달의민족] 프론트엔드 개발자 모집	정규직	경기 성남시	프론트엔드 개발자	4년	무관	재학생/휴학생	React, TypeScript, Next.js	f	https://career.배달의민족.com/job/116	2025-08-18	2025-06-15 23:08:07.553804+09
157	107	1	[SKT] 프론트엔드 개발자 모집	정규직	서울 강남구	프론트엔드 개발자	2년	무관	무관	React, TypeScript, Next.js	f	https://career.skt.com/job/117	2025-08-14	2025-06-15 23:08:07.553804+09
158	108	2	[라인] 데이터 사이언티스트 모집	정규직	서울 송파구	데이터 사이언티스트	3년	7년	재학생/휴학생	Python, SQL, MLflow, Airflow	t	https://career.라인.com/job/118	2025-09-06	2025-06-15 23:08:07.553804+09
159	109	1	[쿠팡] 데이터 사이언티스트 모집	인턴	경기 성남시	데이터 사이언티스트	3년	7년	무관	Python, SQL, MLflow, Airflow	t	https://career.쿠팡.com/job/119	2025-08-04	2025-06-15 23:08:07.553804+09
160	110	2	[네이버] 데이터 사이언티스트 모집	정규직	경기 수원시	데이터 사이언티스트	2년	무관	학사 이상	Python, SQL, MLflow, Airflow	t	https://career.네이버.com/job/120	2025-07-16	2025-06-15 23:08:07.553804+09
161	111	2	[마켓컬리] 데이터 엔지니어 모집	정규직	서울 송파구	데이터 엔지니어	2년	무관	무관	Kafka, Spark, Hadoop, Scala, Python	t	https://career.마켓컬리.com/job/121	2025-07-11	2025-06-15 23:08:07.553804+09
162	112	1	[쿠팡] 데이터 엔지니어 모집	정규직	서울 중구	데이터 엔지니어	3년	7년	재학생/휴학생	Kafka, Spark, Hadoop, Scala, Python	t	https://career.쿠팡.com/job/122	2025-07-05	2025-06-15 23:08:07.553804+09
163	113	3	[마켓컬리] 소프트웨어 개발자 모집	인턴	서울 중구	소프트웨어 개발자	5년	10년	학사 이상	C++, C, Linux	f	https://career.마켓컬리.com/job/123	2025-07-29	2025-06-15 23:08:07.553804+09
164	114	1	[SKT] 데이터 엔지니어 모집	인턴	경기 수원시	데이터 엔지니어	2년	무관	재학생/휴학생	Kafka, Spark, Hadoop, Scala, Python	t	https://career.skt.com/job/124	상시채용	2025-06-15 23:08:07.553804+09
165	115	3	[카카오] 데이터 엔지니어 모집	정규직	제주 제주시	데이터 엔지니어	신입	3년	재학생/휴학생	Kafka, Spark, Hadoop, Scala, Python	t	https://career.카카오.com/job/125	2025-07-14	2025-06-15 23:08:07.553804+09
166	116	1	[배달의민족] 데이터 엔지니어 모집	정규직	서울 강남구	데이터 엔지니어	5년	10년	석사 이상	Kafka, Spark, Hadoop, Scala, Python	t	https://career.배달의민족.com/job/126	2025-08-13	2025-06-15 23:08:07.553804+09
167	117	1	[네이버] 데이터 사이언티스트 모집	인턴	서울 송파구	데이터 사이언티스트	3년	7년	재학생/휴학생	Python, SQL, MLflow, Airflow	t	https://career.네이버.com/job/127	2025-07-21	2025-06-15 23:08:07.553804+09
168	118	1	[라인] 머신러닝 엔지니어 모집	인턴	서울 강남구	머신러닝 엔지니어	신입	3년	무관	Python, Scikit-learn, Docker	t	https://career.라인.com/job/128	2025-06-25	2025-06-15 23:08:07.553804+09
169	119	2	[당근마켓] 데이터 엔지니어 모집	정규직	서울 중구	데이터 엔지니어	3년	7년	무관	Kafka, Spark, Hadoop, Scala, Python	t	https://career.당근마켓.com/job/129	2025-07-22	2025-06-15 23:08:07.553804+09
170	120	2	[라인] 데이터 엔지니어 모집	인턴	서울 강남구	데이터 엔지니어	3년	7년	석사 이상	Kafka, Spark, Hadoop, Scala, Python	t	https://career.라인.com/job/130	2025-07-03	2025-06-15 23:08:07.553804+09
171	121	1	[당근마켓] 프론트엔드 개발자 모집	인턴	서울 강남구	프론트엔드 개발자	2년	무관	학사 이상	React, TypeScript, Next.js	f	https://career.당근마켓.com/job/131	2025-08-23	2025-06-15 23:08:07.553804+09
172	122	2	[네이버] 소프트웨어 개발자 모집	정규직	경기 수원시	소프트웨어 개발자	3년	7년	재학생/휴학생	C++, C, Linux	f	https://career.네이버.com/job/132	상시채용	2025-06-15 23:08:07.553804+09
173	123	3	[네이버] 소프트웨어 개발자 모집	인턴	서울 송파구	소프트웨어 개발자	신입	3년	무관	C++, C, Linux	f	https://career.네이버.com/job/133	2025-07-22	2025-06-15 23:08:07.553804+09
174	124	2	[배달의민족] 백엔드 개발자 모집	정규직	서울 강남구	백엔드 개발자	신입	3년	석사 이상	Java, Kotlin, Spring, AWS	f	https://career.배달의민족.com/job/134	상시채용	2025-06-15 23:08:07.553804+09
175	125	3	[네이버] 프론트엔드 개발자 모집	정규직	제주 제주시	프론트엔드 개발자	5년	10년	재학생/휴학생	React, TypeScript, Next.js	f	https://career.네이버.com/job/135	2025-08-24	2025-06-15 23:08:07.553804+09
176	126	1	[마켓컬리] 데이터 엔지니어 모집	인턴	서울 송파구	데이터 엔지니어	신입	3년	석사 이상	Kafka, Spark, Hadoop, Scala, Python	t	https://career.마켓컬리.com/job/136	상시채용	2025-06-15 23:08:07.553804+09
177	127	2	[SKT] 프론트엔드 개발자 모집	인턴	서울 중구	프론트엔드 개발자	신입	3년	재학생/휴학생	React, TypeScript, Next.js	f	https://career.skt.com/job/137	2025-08-23	2025-06-15 23:08:07.553804+09
178	128	2	[당근마켓] 소프트웨어 개발자 모집	정규직	제주 제주시	소프트웨어 개발자	4년	무관	석사 이상	C++, C, Linux	f	https://career.당근마켓.com/job/138	2025-06-26	2025-06-15 23:08:07.553804+09
179	129	1	[배달의민족] 백엔드 개발자 모집	인턴	경기 수원시	백엔드 개발자	2년	무관	무관	Java, Kotlin, Spring, AWS	f	https://career.배달의민족.com/job/139	상시채용	2025-06-15 23:08:07.553804+09
180	130	1	[라인] 소프트웨어 개발자 모집	인턴	제주 제주시	소프트웨어 개발자	4년	무관	학사 이상	C++, C, Linux	f	https://career.라인.com/job/140	2025-08-05	2025-06-15 23:08:07.553804+09
181	131	1	[당근마켓] 데이터 사이언티스트 모집	인턴	서울 서초구	데이터 사이언티스트	3년	7년	재학생/휴학생	Python, SQL, MLflow, Airflow	t	https://career.당근마켓.com/job/141	2025-06-27	2025-06-15 23:08:07.553804+09
182	132	3	[카카오] 데이터 엔지니어 모집	정규직	제주 제주시	데이터 엔지니어	2년	무관	무관	Kafka, Spark, Hadoop, Scala, Python	t	https://career.카카오.com/job/142	상시채용	2025-06-15 23:08:07.553804+09
183	133	3	[토스] 프론트엔드 개발자 모집	인턴	서울 중구	프론트엔드 개발자	2년	무관	석사 이상	React, TypeScript, Next.js	f	https://career.토스.com/job/143	2025-07-20	2025-06-15 23:08:07.553804+09
184	134	2	[토스] 데이터 분석가 모집	인턴	서울 송파구	데이터 분석가	3년	7년	학사 이상	SQL, Python, R, Tableau	t	https://career.토스.com/job/144	2025-07-19	2025-06-15 23:08:07.553804+09
185	135	3	[쿠팡] 프론트엔드 개발자 모집	인턴	경기 성남시	프론트엔드 개발자	4년	무관	무관	React, TypeScript, Next.js	f	https://career.쿠팡.com/job/145	2025-07-20	2025-06-15 23:08:07.553804+09
186	136	3	[라인] AI 엔지니어 모집	정규직	경기 수원시	AI 엔지니어	2년	무관	석사 이상	Python, TensorFlow, PyTorch, K8s	t	https://career.라인.com/job/146	상시채용	2025-06-15 23:08:07.553804+09
187	137	2	[배달의민족] 모바일 앱 개발자 모집	인턴	제주 제주시	모바일 앱 개발자	3년	7년	무관	Kotlin, Swift, RxJava	f	https://career.배달의민족.com/job/147	2025-09-09	2025-06-15 23:08:07.553804+09
188	138	3	[쿠팡] 소프트웨어 개발자 모집	인턴	서울 서초구	소프트웨어 개발자	2년	무관	재학생/휴학생	C++, C, Linux	f	https://career.쿠팡.com/job/148	2025-09-09	2025-06-15 23:08:07.553804+09
189	139	2	[네이버] 데이터 분석가 모집	정규직	서울 송파구	데이터 분석가	2년	무관	무관	SQL, Python, R, Tableau	t	https://career.네이버.com/job/149	2025-08-09	2025-06-15 23:08:07.553804+09
190	140	1	[삼성전자] AI 엔지니어 모집	정규직	경기 수원시	AI 엔지니어	5년	10년	무관	Python, TensorFlow, PyTorch, K8s	t	https://career.삼성전자.com/job/150	2025-07-13	2025-06-15 23:08:07.553804+09
191	141	2	[토스] 모바일 앱 개발자 모집	인턴	서울 중구	모바일 앱 개발자	4년	무관	학사 이상	Kotlin, Swift, RxJava	f	https://career.토스.com/job/151	2025-07-26	2025-06-15 23:08:07.553804+09
192	142	2	[마켓컬리] 백엔드 개발자 모집	인턴	서울 중구	백엔드 개발자	3년	7년	석사 이상	Java, Kotlin, Spring, AWS	f	https://career.마켓컬리.com/job/152	2025-07-24	2025-06-15 23:08:07.553804+09
193	143	2	[배달의민족] 데이터 사이언티스트 모집	정규직	경기 수원시	데이터 사이언티스트	2년	무관	재학생/휴학생	Python, SQL, MLflow, Airflow	t	https://career.배달의민족.com/job/153	2025-06-27	2025-06-15 23:08:07.553804+09
194	144	1	[삼성전자] 모바일 앱 개발자 모집	인턴	경기 수원시	모바일 앱 개발자	신입	3년	무관	Kotlin, Swift, RxJava	f	https://career.삼성전자.com/job/154	2025-08-17	2025-06-15 23:08:07.553804+09
195	145	1	[배달의민족] 데이터 사이언티스트 모집	인턴	경기 성남시	데이터 사이언티스트	5년	10년	석사 이상	Python, SQL, MLflow, Airflow	t	https://career.배달의민족.com/job/155	2025-08-24	2025-06-15 23:08:07.553804+09
196	146	3	[라인] 백엔드 개발자 모집	인턴	경기 수원시	백엔드 개발자	2년	무관	석사 이상	Java, Kotlin, Spring, AWS	f	https://career.라인.com/job/156	2025-08-15	2025-06-15 23:08:07.553804+09
197	147	3	[토스] AI 엔지니어 모집	정규직	서울 강남구	AI 엔지니어	4년	무관	무관	Python, TensorFlow, PyTorch, K8s	t	https://career.토스.com/job/157	상시채용	2025-06-15 23:08:07.553804+09
198	148	1	[마켓컬리] 데이터 분석가 모집	인턴	서울 송파구	데이터 분석가	신입	3년	재학생/휴학생	SQL, Python, R, Tableau	t	https://career.마켓컬리.com/job/158	2025-07-21	2025-06-15 23:08:07.553804+09
199	149	2	[쿠팡] 데이터 분석가 모집	정규직	서울 강남구	데이터 분석가	5년	10년	석사 이상	SQL, Python, R, Tableau	t	https://career.쿠팡.com/job/159	상시채용	2025-06-15 23:08:07.553804+09
200	150	2	[토스] 데이터 엔지니어 모집	정규직	경기 성남시	데이터 엔지니어	4년	무관	석사 이상	Kafka, Spark, Hadoop, Scala, Python	t	https://career.토스.com/job/160	상시채용	2025-06-15 23:08:07.553804+09
201	151	1	[SKT] 데이터 엔지니어 모집	인턴	서울 중구	데이터 엔지니어	2년	무관	학사 이상	Kafka, Spark, Hadoop, Scala, Python	t	https://career.skt.com/job/161	2025-09-06	2025-06-15 23:08:07.553804+09
202	152	1	[마켓컬리] 머신러닝 엔지니어 모집	인턴	서울 중구	머신러닝 엔지니어	4년	무관	석사 이상	Python, Scikit-learn, Docker	t	https://career.마켓컬리.com/job/162	상시채용	2025-06-15 23:08:07.553804+09
203	153	3	[당근마켓] 데이터 엔지니어 모집	인턴	서울 서초구	데이터 엔지니어	3년	7년	학사 이상	Kafka, Spark, Hadoop, Scala, Python	t	https://career.당근마켓.com/job/163	상시채용	2025-06-15 23:08:07.553804+09
204	154	1	[마켓컬리] 데이터 엔지니어 모집	인턴	서울 송파구	데이터 엔지니어	5년	10년	학사 이상	Kafka, Spark, Hadoop, Scala, Python	t	https://career.마켓컬리.com/job/164	2025-08-21	2025-06-15 23:08:07.553804+09
205	155	2	[네이버] 백엔드 개발자 모집	인턴	서울 송파구	백엔드 개발자	신입	3년	학사 이상	Java, Kotlin, Spring, AWS	f	https://career.네이버.com/job/165	2025-07-13	2025-06-15 23:08:07.553804+09
206	156	1	[마켓컬리] 프론트엔드 개발자 모집	정규직	경기 수원시	프론트엔드 개발자	신입	3년	재학생/휴학생	React, TypeScript, Next.js	f	https://career.마켓컬리.com/job/166	2025-09-04	2025-06-15 23:08:07.553804+09
207	157	2	[쿠팡] 머신러닝 엔지니어 모집	인턴	서울 강남구	머신러닝 엔지니어	5년	10년	석사 이상	Python, Scikit-learn, Docker	t	https://career.쿠팡.com/job/167	2025-07-06	2025-06-15 23:08:07.553804+09
208	158	1	[라인] 머신러닝 엔지니어 모집	인턴	경기 수원시	머신러닝 엔지니어	3년	7년	석사 이상	Python, Scikit-learn, Docker	t	https://career.라인.com/job/168	상시채용	2025-06-15 23:08:07.553804+09
209	159	3	[쿠팡] 데이터 분석가 모집	정규직	서울 강남구	데이터 분석가	5년	10년	무관	SQL, Python, R, Tableau	t	https://career.쿠팡.com/job/169	2025-08-23	2025-06-15 23:08:07.553804+09
210	160	2	[쿠팡] 데이터 분석가 모집	인턴	서울 송파구	데이터 분석가	4년	무관	석사 이상	SQL, Python, R, Tableau	t	https://career.쿠팡.com/job/170	상시채용	2025-06-15 23:08:07.553804+09
211	161	3	[삼성전자] AI 엔지니어 모집	인턴	제주 제주시	AI 엔지니어	4년	무관	재학생/휴학생	Python, TensorFlow, PyTorch, K8s	t	https://career.삼성전자.com/job/171	2025-08-02	2025-06-15 23:08:07.553804+09
212	162	3	[네이버] 데이터 엔지니어 모집	인턴	경기 성남시	데이터 엔지니어	3년	7년	무관	Kafka, Spark, Hadoop, Scala, Python	t	https://career.네이버.com/job/172	2025-06-27	2025-06-15 23:08:07.553804+09
213	163	3	[쿠팡] 머신러닝 엔지니어 모집	인턴	서울 중구	머신러닝 엔지니어	신입	3년	석사 이상	Python, Scikit-learn, Docker	t	https://career.쿠팡.com/job/173	상시채용	2025-06-15 23:08:07.553804+09
214	164	2	[라인] 데이터 엔지니어 모집	인턴	경기 성남시	데이터 엔지니어	3년	7년	무관	Kafka, Spark, Hadoop, Scala, Python	t	https://career.라인.com/job/174	2025-06-25	2025-06-15 23:08:07.553804+09
215	165	1	[마켓컬리] 데이터 엔지니어 모집	인턴	경기 수원시	데이터 엔지니어	4년	무관	학사 이상	Kafka, Spark, Hadoop, Scala, Python	t	https://career.마켓컬리.com/job/175	2025-07-03	2025-06-15 23:08:07.553804+09
216	166	1	[마켓컬리] 소프트웨어 개발자 모집	인턴	서울 송파구	소프트웨어 개발자	4년	무관	학사 이상	C++, C, Linux	f	https://career.마켓컬리.com/job/176	2025-07-09	2025-06-15 23:08:07.553804+09
217	167	1	[삼성전자] 백엔드 개발자 모집	인턴	서울 중구	백엔드 개발자	5년	10년	재학생/휴학생	Java, Kotlin, Spring, AWS	f	https://career.삼성전자.com/job/177	2025-07-12	2025-06-15 23:08:07.553804+09
218	168	3	[라인] 머신러닝 엔지니어 모집	인턴	서울 송파구	머신러닝 엔지니어	신입	3년	재학생/휴학생	Python, Scikit-learn, Docker	t	https://career.라인.com/job/178	2025-08-13	2025-06-15 23:08:07.553804+09
219	169	3	[배달의민족] 모바일 앱 개발자 모집	인턴	서울 서초구	모바일 앱 개발자	2년	무관	무관	Kotlin, Swift, RxJava	f	https://career.배달의민족.com/job/179	2025-08-16	2025-06-15 23:08:07.553804+09
220	170	1	[카카오] 프론트엔드 개발자 모집	정규직	서울 송파구	프론트엔드 개발자	신입	3년	무관	React, TypeScript, Next.js	f	https://career.카카오.com/job/180	2025-08-01	2025-06-15 23:08:07.553804+09
\.


--
-- Name: JobPosting_posting_id_seq; Type: SEQUENCE SET; Schema: public; Owner: datajob_user
--

SELECT pg_catalog.setval('public."JobPosting_posting_id_seq"', 1, false);


--
-- Name: jobposting_posting_id_seq; Type: SEQUENCE SET; Schema: public; Owner: datajob_user
--

SELECT pg_catalog.setval('public.jobposting_posting_id_seq', 220, true);


--
-- Name: JobPosting JobPosting_pkey; Type: CONSTRAINT; Schema: public; Owner: datajob_user
--

ALTER TABLE ONLY public."JobPosting"
    ADD CONSTRAINT "JobPosting_pkey" PRIMARY KEY (posting_id);


--
-- Name: jobposting jobposting_pkey; Type: CONSTRAINT; Schema: public; Owner: datajob_user
--

ALTER TABLE ONLY public.jobposting
    ADD CONSTRAINT jobposting_pkey PRIMARY KEY (posting_id);


--
-- Name: ix_JobPosting_posting_id; Type: INDEX; Schema: public; Owner: datajob_user
--

CREATE INDEX "ix_JobPosting_posting_id" ON public."JobPosting" USING btree (posting_id);


--
-- PostgreSQL database dump complete
--

