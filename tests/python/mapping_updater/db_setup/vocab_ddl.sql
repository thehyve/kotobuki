-- postgresql DDL Specification for a subset of vocabulary tables in OMOP Common Data Model 5.4
-- Adds PKs, but no FKs or indexes

CREATE TABLE vocab.CONCEPT (
                               concept_id integer NOT NULL,
                               concept_name varchar(255) NOT NULL,
                               domain_id varchar(20) NOT NULL,
                               vocabulary_id varchar(20) NOT NULL,
                               concept_class_id varchar(20) NOT NULL,
                               standard_concept varchar(1) NULL,
                               concept_code varchar(50) NOT NULL,
                               valid_start_date date NOT NULL,
                               valid_end_date date NOT NULL,
                               invalid_reason varchar(1) NULL );

CREATE TABLE vocab.CONCEPT_RELATIONSHIP (
                                            concept_id_1 integer NOT NULL,
                                            concept_id_2 integer NOT NULL,
                                            relationship_id varchar(20) NOT NULL,
                                            valid_start_date date NOT NULL,
                                            valid_end_date date NOT NULL,
                                            invalid_reason varchar(1) NULL );

ALTER TABLE vocab.CONCEPT ADD CONSTRAINT xpk_CONCEPT PRIMARY KEY (concept_id);
ALTER TABLE vocab.concept_relationship ADD CONSTRAINT xpk_concept_relationship
    PRIMARY KEY (concept_id_1, concept_id_2, relationship_id);
