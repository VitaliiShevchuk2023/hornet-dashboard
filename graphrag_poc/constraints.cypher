CREATE CONSTRAINT obs_id IF NOT EXISTS
FOR (o:Observation) REQUIRE o.id IS UNIQUE;

CREATE CONSTRAINT species_name IF NOT EXISTS
FOR (s:Species) REQUIRE s.name IS UNIQUE;

CREATE CONSTRAINT bundesland_name IF NOT EXISTS
FOR (b:Bundesland) REQUIRE b.name IS UNIQUE;

CREATE CONSTRAINT keyword_type IF NOT EXISTS
FOR (h:LocalityKeyword) REQUIRE h.type IS UNIQUE;

CREATE POINT INDEX obs_location IF NOT EXISTS
FOR (o:Observation) ON (o.location);
