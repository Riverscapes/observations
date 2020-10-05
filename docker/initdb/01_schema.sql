-- DDL: use PostgreSQL

CREATE EXTENSION postgis;

CREATE TABLE observation_types (
    id              INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            VARCHAR(20)
);

CREATE UNIQUE INDEX ux_observation_types_name ON observation_types(name);

CREATE TABLE uploads (
    id              INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    added_by        Varchar(100),
    file_name       VARCHAR(255),
    remarks         TEXT,
    added_on        TIMESTAMPTZ NOT NULL DEFAULT now(),
)


CREATE TABLE observations (
    id              INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    upload_id       INT,
    geom            GEOMETRY(Point, 4326),
    obs_date        TIMESTAMPTZ NOT NULL,
    observer        VARCHAR(100),
    obs_year        smallint,
    obs_type_id     INTEGER NOT NULL,
    is_public       BOOLEAN,
    purpose         VARCHAR(100),
    confidence      smallint,
    remarks         TEXT,
    metadata        JSONB,
    added_on        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_on      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_observations_obs_type_id FOREIGN KEY (obs_type_id) REFERENCES observation_types(id),
    CONSTRAINT fk_observations_upload_id FOREIGN KEY (upload_id) REFERENCES uploads(id)
);

CREATE INDEX idx_observations_geom ON observations USING GIST(geom);
CREATE INDEX idx_observations_upload_id ON observations(upload_id);
CREATE INDEX idx_observations_obs_type_id ON observations(obs_type_id);

/*
CREATE FUNCTION update_observations() RETURNS TRIGGER AS $$
BEGIN
    UPDATE observations SET updated_on = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER tr_observations_updated_on
AFTER UPDATE ON observations
FOR EACH ROW
EXECUTE PROCEDURE update_observations();

*/

CREATE VIEW vwObservations AS (
    SELECT
        id as observation_id,              
        upload_id,
        file_name,     
        ST_ASGEOJSON(geom) AS location,
        obs_date,
        observer,
        obs_year,
        obs_type_id,
        obs_type,
        purpose,
        confidence,
        remarks,
        CAST(metadata AS JSON),
        added_on,
        updated_on
    FROM observations o
        INNER JOIN observation_types ot ON o.obs_type_id = ot.id
        LEFT JOIN uploads u on o.upload_id = u.id
)