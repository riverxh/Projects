--
-- PostgreSQL database dump
--

-- Dumped from database version 16.6 (Debian 16.6-1.pgdg120+1)
-- Dumped by pg_dump version 16.6 (Debian 16.6-1.pgdg120+1)

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

--
-- Name: proyecto; Type: SCHEMA; Schema: -; Owner: estudiante
--

CREATE SCHEMA proyecto;


ALTER SCHEMA proyecto OWNER TO estudiante;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: construccion_agrupada; Type: TABLE; Schema: proyecto; Owner: estudiante
--

CREATE TABLE proyecto.construccion_agrupada (
    codigo_agrupacion text NOT NULL,
    anio integer NOT NULL,
    obras_total bigint,
    area_m2 double precision,
    valor_miles_colones double precision,
    obras_nuevas bigint,
    area_nueva_m2 double precision,
    valor_nueva_miles double precision,
    obras_ampliacion bigint,
    area_ampliacion_m2 double precision,
    valor_ampliacion_miles double precision,
    obras_reparacion bigint,
    valor_reparacion_miles double precision,
    codigos_construccion text,
    origen_construccion text
);


ALTER TABLE proyecto.construccion_agrupada OWNER TO estudiante;

--
-- Name: construccion_cantonal; Type: TABLE; Schema: proyecto; Owner: estudiante
--

CREATE TABLE proyecto.construccion_cantonal (
    anio integer NOT NULL,
    codigo_canton text NOT NULL,
    canton text,
    obras_total bigint,
    area_m2 double precision,
    valor_miles_colones double precision,
    obras_nuevas bigint,
    area_nueva_m2 double precision,
    valor_nueva_miles double precision,
    obras_ampliacion bigint,
    area_ampliacion_m2 double precision,
    valor_ampliacion_miles double precision,
    obras_reparacion bigint,
    valor_reparacion_miles double precision,
    archivo text,
    hoja text,
    fila integer,
    fuente_url text,
    columnas_metricas text
);


ALTER TABLE proyecto.construccion_cantonal OWNER TO estudiante;

--
-- Name: destinos_cantonales; Type: TABLE; Schema: proyecto; Owner: estudiante
--

CREATE TABLE proyecto.destinos_cantonales (
    anio integer,
    codigo_canton text,
    canton text,
    obras_total bigint,
    area_m2 double precision,
    valor_miles_colones double precision,
    obras_nuevas bigint,
    area_nueva_m2 double precision,
    valor_nueva_miles double precision,
    obras_ampliacion bigint,
    area_ampliacion_m2 double precision,
    valor_ampliacion_miles double precision,
    obras_reparacion bigint,
    valor_reparacion_miles double precision,
    archivo text,
    hoja text,
    fila integer,
    fuente_url text,
    columnas_metricas text,
    destino text,
    categoria text,
    nivel text,
    id text NOT NULL,
    provincia text
);


ALTER TABLE proyecto.destinos_cantonales OWNER TO estudiante;

--
-- Name: integrado; Type: TABLE; Schema: proyecto; Owner: estudiante
--

CREATE TABLE proyecto.integrado (
    codigo_agrupacion text NOT NULL,
    anio integer NOT NULL,
    obras_total bigint,
    area_m2 double precision,
    valor_miles_colones double precision,
    obras_nuevas bigint,
    area_nueva_m2 double precision,
    valor_nueva_miles double precision,
    obras_ampliacion bigint,
    area_ampliacion_m2 double precision,
    valor_ampliacion_miles double precision,
    obras_reparacion bigint,
    valor_reparacion_miles double precision,
    codigos_construccion text,
    origen_construccion text,
    poblacion double precision,
    hombres double precision,
    mujeres double precision,
    codigos_poblacion text,
    origen_poblacion text,
    agrupacion text,
    provincia text,
    area_por_habitante double precision,
    CONSTRAINT integrado_check CHECK (((poblacion > (0)::double precision) AND (area_m2 >= (0)::double precision)))
);


ALTER TABLE proyecto.integrado OWNER TO estudiante;

--
-- Name: poblacion_agrupada; Type: TABLE; Schema: proyecto; Owner: estudiante
--

CREATE TABLE proyecto.poblacion_agrupada (
    codigo_agrupacion text NOT NULL,
    anio integer NOT NULL,
    poblacion double precision,
    hombres double precision,
    mujeres double precision,
    codigos_poblacion text,
    origen_poblacion text
);


ALTER TABLE proyecto.poblacion_agrupada OWNER TO estudiante;

--
-- Name: poblacion_cantonal; Type: TABLE; Schema: proyecto; Owner: estudiante
--

CREATE TABLE proyecto.poblacion_cantonal (
    codigo_canton text NOT NULL,
    canton text,
    archivo text,
    hoja text,
    fuente_url text,
    poblacion double precision,
    hombres double precision,
    mujeres double precision,
    celda_total text,
    celda_hombres text,
    celda_mujeres text,
    anio integer NOT NULL,
    fila integer
);


ALTER TABLE proyecto.poblacion_cantonal OWNER TO estudiante;

--
-- Name: predicciones; Type: TABLE; Schema: proyecto; Owner: estudiante
--

CREATE TABLE proyecto.predicciones (
    codigo_agrupacion text NOT NULL,
    agrupacion text,
    provincia text,
    anio_objetivo integer NOT NULL,
    anio_datos integer,
    observado_m2 double precision,
    prediccion_m2 double precision,
    persistencia_m2 double precision,
    modelo text NOT NULL,
    error_m2 double precision,
    error_absoluto_m2 double precision,
    CONSTRAINT predicciones_check CHECK (((prediccion_m2 >= (0)::double precision) AND (anio_datos = (anio_objetivo - 1))))
);


ALTER TABLE proyecto.predicciones OWNER TO estudiante;

--
-- Name: territorios; Type: TABLE; Schema: proyecto; Owner: estudiante
--

CREATE TABLE proyecto.territorios (
    codigo_agrupacion text NOT NULL,
    agrupacion text,
    provincia text
);


ALTER TABLE proyecto.territorios OWNER TO estudiante;

--
-- Name: construccion_agrupada construccion_agrupada_pkey; Type: CONSTRAINT; Schema: proyecto; Owner: estudiante
--

ALTER TABLE ONLY proyecto.construccion_agrupada
    ADD CONSTRAINT construccion_agrupada_pkey PRIMARY KEY (codigo_agrupacion, anio);


--
-- Name: construccion_cantonal construccion_cantonal_pkey; Type: CONSTRAINT; Schema: proyecto; Owner: estudiante
--

ALTER TABLE ONLY proyecto.construccion_cantonal
    ADD CONSTRAINT construccion_cantonal_pkey PRIMARY KEY (codigo_canton, anio);


--
-- Name: destinos_cantonales destinos_cantonales_pkey; Type: CONSTRAINT; Schema: proyecto; Owner: estudiante
--

ALTER TABLE ONLY proyecto.destinos_cantonales
    ADD CONSTRAINT destinos_cantonales_pkey PRIMARY KEY (id);


--
-- Name: integrado integrado_pkey; Type: CONSTRAINT; Schema: proyecto; Owner: estudiante
--

ALTER TABLE ONLY proyecto.integrado
    ADD CONSTRAINT integrado_pkey PRIMARY KEY (codigo_agrupacion, anio);


--
-- Name: poblacion_agrupada poblacion_agrupada_pkey; Type: CONSTRAINT; Schema: proyecto; Owner: estudiante
--

ALTER TABLE ONLY proyecto.poblacion_agrupada
    ADD CONSTRAINT poblacion_agrupada_pkey PRIMARY KEY (codigo_agrupacion, anio);


--
-- Name: poblacion_cantonal poblacion_cantonal_pkey; Type: CONSTRAINT; Schema: proyecto; Owner: estudiante
--

ALTER TABLE ONLY proyecto.poblacion_cantonal
    ADD CONSTRAINT poblacion_cantonal_pkey PRIMARY KEY (codigo_canton, anio);


--
-- Name: predicciones predicciones_pkey; Type: CONSTRAINT; Schema: proyecto; Owner: estudiante
--

ALTER TABLE ONLY proyecto.predicciones
    ADD CONSTRAINT predicciones_pkey PRIMARY KEY (modelo, codigo_agrupacion, anio_objetivo);


--
-- Name: territorios territorios_pkey; Type: CONSTRAINT; Schema: proyecto; Owner: estudiante
--

ALTER TABLE ONLY proyecto.territorios
    ADD CONSTRAINT territorios_pkey PRIMARY KEY (codigo_agrupacion);


--
-- Name: construccion_agrupada construccion_agrupada_codigo_agrupacion_fkey; Type: FK CONSTRAINT; Schema: proyecto; Owner: estudiante
--

ALTER TABLE ONLY proyecto.construccion_agrupada
    ADD CONSTRAINT construccion_agrupada_codigo_agrupacion_fkey FOREIGN KEY (codigo_agrupacion) REFERENCES proyecto.territorios(codigo_agrupacion);


--
-- Name: integrado integrado_codigo_agrupacion_fkey; Type: FK CONSTRAINT; Schema: proyecto; Owner: estudiante
--

ALTER TABLE ONLY proyecto.integrado
    ADD CONSTRAINT integrado_codigo_agrupacion_fkey FOREIGN KEY (codigo_agrupacion) REFERENCES proyecto.territorios(codigo_agrupacion);


--
-- Name: poblacion_agrupada poblacion_agrupada_codigo_agrupacion_fkey; Type: FK CONSTRAINT; Schema: proyecto; Owner: estudiante
--

ALTER TABLE ONLY proyecto.poblacion_agrupada
    ADD CONSTRAINT poblacion_agrupada_codigo_agrupacion_fkey FOREIGN KEY (codigo_agrupacion) REFERENCES proyecto.territorios(codigo_agrupacion);


--
-- Name: predicciones predicciones_codigo_agrupacion_fkey; Type: FK CONSTRAINT; Schema: proyecto; Owner: estudiante
--

ALTER TABLE ONLY proyecto.predicciones
    ADD CONSTRAINT predicciones_codigo_agrupacion_fkey FOREIGN KEY (codigo_agrupacion) REFERENCES proyecto.territorios(codigo_agrupacion);


--
-- PostgreSQL database dump complete
--

