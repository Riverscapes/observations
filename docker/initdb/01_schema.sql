-- DDL: use PostgreSQL

CREATE EXTENSION postgis;

CREATE TABLE observation_types (
    id              INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            VARCHAR(20)
);

CREATE UNIQUE INDEX ux_observation_types_name ON observation_types(name);


CREATE TABLE observations (
    id              INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    geom            GEOMETRY(Point, 4326),
    obs_date        TIMESTAMPTZ NOT NULL,
    observer        VARCHAR(100),
    purpose         VARCHAR(100),
    confidence      smallint,
    obs_year        smallint,
    obs_type_id     INTEGER NOT NULL,
    metadata        JSONB,
    added_on        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_on       TIMESTAMPTZ NOT NULL DEFAULT now(),

     CONSTRAINT fk_observations_obs_type_id FOREIGN KEY (obs_type_id) REFERENCES observation_types(id)
);


CREATE INDEX idx_observations_geom ON observations USING GIST(geom);

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