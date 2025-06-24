# Update outdated Usagi files with kotobuki

With new releases of the OMOP vocabularies, some target concepts defined with
Usagi might have become non-standard. With kotobuki you can update
outdated Usagi files by replacing non-standard target concepts with standard
alternatives.

## Requirements

- Read access to an OMOP CDM database, populated with a recent release of the OMOP
vocabularies. The more vocabularies are included, the higher the probability of
finding standard concept alternatives.
- If searching for new concepts via homonyms, an indexed CONCEPT_NAME column
(only applies to row-oriented databases, see [Homonyms](#homonyms)).

## Option 1 (command line)

See explanation inside the CLI help menu:
```shell
update-usagi-file --help
```

For more information on how to provide a database URL, see the
[SQLAlchemy docs](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls)

## Option 2 (Python)

The same functionality is accessible directly via Python:

```python
from pathlib import Path
from sqlalchemy import create_engine
from kotobuki import update_usagi_file

engine = create_engine("postgresql://user:password@localhost:5432/my_db")
usagi_file = Path("~/my_usagi_save_file.csv")

update_usagi_file(
    engine=engine,
    vocab_schema="my_cdm",
    usagi_file=usagi_file,
    allow_homonyms=False,
    write_map_paths=False,
    inspect_only=False,
    overwrite=False,
)
```

## Search algorithm
Kotobuki uses the concept relationships stored in the OMOP vocabularies
to find standard alternatives. The following relationship types are included:

- `Maps to`
- `Concept replaced by`
- `Concept poss_eq to`
- `Concept same_as to`

For each distinct non-standard target concept these relationships are traversed in a
recursive manner, until a `Maps to` relationship is found, as this will always
direct to a standard concept.

If all relationship paths have been traversed without finding a standard concept,
the mapping is left as is.

### One to many mappings
Some non-standard concepts have multiple `Maps to` relationships to standard
concept. In those cases, every target concept will result in a new line in the
mapping table.

### Maps to value
Sometimes a non-standard concept contains both `Maps to` and `Maps to value`
(value_as_concept_id) relationships. When this occurs, the original Usagi mapping is
replaced by at least two new ones (one for the `Maps to` relationship and one
per `Maps to value` relationship).
If the original Usagi file did not have a `mappingType` column,
this column will be added to make sure the mapping types can be distinguished.

### Homonyms
In addition to the concept relationships, it is possible to search for standard
concepts by looking at concepts with an identical concept name.
Searching for homonyms needs to be explicitly activated and will only be used if
the concept relationships of the original concept do not link to a standard concept.

All available homonyms will be parsed for concept relationships (just like the original
non-standard concept) until a standard concept is found or all relationship paths have
been traversed.

To include homonyms, add the `--allow-homonyms`/`-h` flag (CLI), or provide
`allow_homonyms=True` (Python).

> ⚠️ **WARNING:**
> Searching for standard concepts via homonyms is less reliable than via the concept
> relationships, especially for concepts with a short name.

### Diagram

Recursive search algorithm as a flowchart.
Homonym search (light blue) is an optional step.

```mermaid
---
title: Recursive Search Algorithm
config:
  theme: 'neutral'
  fontFamily: "\"arial\", sans-serif"
  flowchart: 
    curve: linear
---
flowchart TB
    classDef optional fill:#BBDEFB
    classDef regular fill:#e5efc3
    classDef subgraph_style fill:#f6faeb
    
    fetch[Fetch relationships<br>for target concept_id]:::regular
    maps_to{Any 'Maps to' relationship?}:::regular
    replaced_by{Any 'Concept replaced by'<br>relationship?}:::regular
    same_equal{Any 'same as' or 'possibly<br>equal' relationship?}:::regular
    homonym{Any other concepts<br>with the same name?}:::optional
    
    result:::subgraph_style
    subgraph result[Result]
        no_cigar[At least we tried.<br><br>Keep the original mapping.]:::regular
        success[Success!✨<br><br>Replace old mapping with<br>all 'Maps to' and 'Maps to<br>value' relationships.]:::regular
    end
    
    fetch ==> maps_to
    maps_to == NO ==> replaced_by
    replaced_by == NO ==> same_equal
    same_equal == NO ==> homonym
    homonym == NO ==> no_cigar

    replaced_by == YES ==> fetch
    same_equal == YES ==> fetch
    homonym == YES ==> fetch
    maps_to == YES ==> success
    
```

## Output
By default, the updated Usagi mappings will be written to a new file. If you provide the
`overwrite` option, the original file will be updated instead. Any recognized fields
related to the updated concept will be changed as well (e.g. concept domain, class, as
present in the Usagi review file.)

Alternatively, you can only log findings to the console without writing anything. To do so,
add the `--inspect-only`/`-s` flag (CLI), or provide `inspect_only=True` (Python).

### Mapping paths
If preferred, an additional file can be written which contains the mapping paths for
all updated mappings. In there you can see exactly which steps were taken to go from the
original non-standard concept to a standard alternative.

To write the mapping paths, add the `--write-map-paths`/`-m` flag (CLI), or provide
`write_map_paths=True` (Python).

> ℹ️ **NOTE:**
> Mappings paths currently don't include `Maps to value` relationships.
