\restrict dbmate

-- Dumped from database version 18.6 (Homebrew)
-- Dumped by pg_dump version 18.6 (Homebrew)

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: schema_migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_migrations (
    version character varying(128) NOT NULL
);


--
-- Name: ログインセッション; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."ログインセッション" (
    "セッションIDハッシュ" character varying(64) CONSTRAINT "ログインセッション_セッションIDハッシ_not_null" NOT NULL,
    "職員番号" character varying(20) NOT NULL,
    "作成日時" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "無操作期限" timestamp with time zone NOT NULL,
    "絶対有効期限" timestamp with time zone NOT NULL,
    "最終利用日時" timestamp with time zone,
    "失効日時" timestamp with time zone,
    CONSTRAINT "ck_ログインセッション_期限" CHECK (("無操作期限" <= "絶対有効期限"))
);


--
-- Name: 問い合わせ; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."問い合わせ" (
    "問い合わせ番号" integer NOT NULL,
    "問い合わせ職員番号" character varying(20),
    "問い合わせ当時の所属" character varying(30) NOT NULL,
    "受付経路" character varying(20) NOT NULL,
    "問い合わせ分類" character varying(30) NOT NULL,
    "件名" character varying(100) NOT NULL,
    "緊急度" integer NOT NULL,
    "受付時の処理" integer NOT NULL,
    "問い合わせ詳細" character varying(1000),
    "受付担当者" character varying(20),
    "対応担当者" character varying(20),
    "受信日時" timestamp with time zone NOT NULL,
    "登録日時" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "引き受け日時" timestamp with time zone,
    "対応完了日時" timestamp with time zone,
    CONSTRAINT "問い合わせ_受付時の処理_check" CHECK (("受付時の処理" = ANY (ARRAY[1, 2, 3]))),
    CONSTRAINT "問い合わせ_緊急度_check" CHECK (("緊急度" = ANY (ARRAY[1, 2, 3])))
);


--
-- Name: 問い合わせ_問い合わせ番号_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."問い合わせ" ALTER COLUMN "問い合わせ番号" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public."問い合わせ_問い合わせ番号_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: 問い合わせ調査; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."問い合わせ調査" (
    "問い合わせ調査番号" integer NOT NULL,
    "調査番号" integer NOT NULL,
    "問い合わせ番号" integer NOT NULL,
    "問い合わせ調査状態" integer DEFAULT 1 NOT NULL,
    "調査開始日時" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "断念日時" timestamp with time zone,
    "リアクション被要求日時" timestamp with time zone,
    "リアクション日時" timestamp with time zone,
    "リアクション内容" integer,
    "NGでの移行先調査番号" integer,
    CONSTRAINT "ck_問い合わせ調査_NG移行先は別調査" CHECK ((("NGでの移行先調査番号" IS NULL) OR ("NGでの移行先調査番号" <> "調査番号"))),
    CONSTRAINT "問い合わせ調査_リアクション内容_check" CHECK (("リアクション内容" = ANY (ARRAY[1, 2]))),
    CONSTRAINT "問い合わせ調査_問い合わせ調査状態_check" CHECK (("問い合わせ調査状態" = ANY (ARRAY[1, 2, 3, 4, 5])))
);


--
-- Name: 問い合わせ調査_問い合わせ調査番号_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."問い合わせ調査" ALTER COLUMN "問い合わせ調査番号" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public."問い合わせ調査_問い合わせ調査番号_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: 職員; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."職員" (
    "職員番号" character varying(20) NOT NULL,
    "氏名" character varying(30) NOT NULL,
    "所属" character varying(30) NOT NULL
);


--
-- Name: 職員認証情報; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."職員認証情報" (
    "職員番号" character varying(20) NOT NULL,
    "パスワードハッシュ" text NOT NULL,
    "ログイン可否" boolean DEFAULT true NOT NULL,
    "作成日時" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "更新日時" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "パスワード更新日時" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: 調査; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."調査" (
    "調査番号" integer NOT NULL,
    "調査の名称" character varying(30) NOT NULL,
    "原因・仮説" character varying(1000),
    "情シス側での対応" character varying(1000),
    "問い合わせ者側で必要な対応" character varying(1000),
    "調査状態" integer DEFAULT 1 NOT NULL,
    "調査開始日時" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "対応案策定予定日時" timestamp with time zone,
    "進捗更新の次回更新予定日時" timestamp with time zone,
    "リアクション要求日時" timestamp with time zone,
    "調査断念日時" timestamp with time zone,
    "最新移行先の調査番号" integer,
    CONSTRAINT "調査_調査状態_check" CHECK (("調査状態" = ANY (ARRAY[1, 2, 3])))
);


--
-- Name: 調査_調査番号_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."調査" ALTER COLUMN "調査番号" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public."調査_調査番号_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- Name: 問い合わせ調査 uq_問い合わせ調査_問い合わせ_調査; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."問い合わせ調査"
    ADD CONSTRAINT "uq_問い合わせ調査_問い合わせ_調査" UNIQUE ("問い合わせ番号", "調査番号");


--
-- Name: ログインセッション ログインセッション_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ログインセッション"
    ADD CONSTRAINT "ログインセッション_pkey" PRIMARY KEY ("セッションIDハッシュ");


--
-- Name: 問い合わせ 問い合わせ_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."問い合わせ"
    ADD CONSTRAINT "問い合わせ_pkey" PRIMARY KEY ("問い合わせ番号");


--
-- Name: 問い合わせ調査 問い合わせ調査_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."問い合わせ調査"
    ADD CONSTRAINT "問い合わせ調査_pkey" PRIMARY KEY ("問い合わせ調査番号");


--
-- Name: 職員 職員_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."職員"
    ADD CONSTRAINT "職員_pkey" PRIMARY KEY ("職員番号");


--
-- Name: 職員認証情報 職員認証情報_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."職員認証情報"
    ADD CONSTRAINT "職員認証情報_pkey" PRIMARY KEY ("職員番号");


--
-- Name: 調査 調査_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."調査"
    ADD CONSTRAINT "調査_pkey" PRIMARY KEY ("調査番号");


--
-- Name: idx_ログインセッション_職員番号; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "idx_ログインセッション_職員番号" ON public."ログインセッション" USING btree ("職員番号");


--
-- Name: ログインセッション fk_ログインセッション_職員認証情報; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ログインセッション"
    ADD CONSTRAINT "fk_ログインセッション_職員認証情報" FOREIGN KEY ("職員番号") REFERENCES public."職員認証情報"("職員番号") ON DELETE CASCADE;


--
-- Name: 問い合わせ fk_問い合わせ_受付担当者; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."問い合わせ"
    ADD CONSTRAINT "fk_問い合わせ_受付担当者" FOREIGN KEY ("受付担当者") REFERENCES public."職員"("職員番号") ON DELETE SET NULL;


--
-- Name: 問い合わせ fk_問い合わせ_問い合わせ職員; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."問い合わせ"
    ADD CONSTRAINT "fk_問い合わせ_問い合わせ職員" FOREIGN KEY ("問い合わせ職員番号") REFERENCES public."職員"("職員番号") ON DELETE SET NULL;


--
-- Name: 問い合わせ fk_問い合わせ_対応担当者; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."問い合わせ"
    ADD CONSTRAINT "fk_問い合わせ_対応担当者" FOREIGN KEY ("対応担当者") REFERENCES public."職員"("職員番号") ON DELETE SET NULL;


--
-- Name: 問い合わせ調査 fk_問い合わせ調査_NG移行先; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."問い合わせ調査"
    ADD CONSTRAINT "fk_問い合わせ調査_NG移行先" FOREIGN KEY ("NGでの移行先調査番号") REFERENCES public."調査"("調査番号");


--
-- Name: 問い合わせ調査 fk_問い合わせ調査_問い合わせ; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."問い合わせ調査"
    ADD CONSTRAINT "fk_問い合わせ調査_問い合わせ" FOREIGN KEY ("問い合わせ番号") REFERENCES public."問い合わせ"("問い合わせ番号");


--
-- Name: 問い合わせ調査 fk_問い合わせ調査_調査; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."問い合わせ調査"
    ADD CONSTRAINT "fk_問い合わせ調査_調査" FOREIGN KEY ("調査番号") REFERENCES public."調査"("調査番号");


--
-- Name: 職員認証情報 fk_職員認証情報_職員; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."職員認証情報"
    ADD CONSTRAINT "fk_職員認証情報_職員" FOREIGN KEY ("職員番号") REFERENCES public."職員"("職員番号") ON DELETE CASCADE;


--
-- Name: 調査 fk_調査_最新移行先; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."調査"
    ADD CONSTRAINT "fk_調査_最新移行先" FOREIGN KEY ("最新移行先の調査番号") REFERENCES public."調査"("調査番号");


--
-- PostgreSQL database dump complete
--

\unrestrict dbmate


--
-- Dbmate schema migrations
--

INSERT INTO public.schema_migrations (version) VALUES
    ('20261101163000');
