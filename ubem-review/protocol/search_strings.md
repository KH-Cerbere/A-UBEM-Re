# Search Strings

Searches should be saved with the exact database, date, query string, filters,
and number of returned records. These strings are starting points and should be
adapted to each search interface.

## Core Concepts

- UBEM
- urban building energy modeling
- urban building energy model
- city-scale building energy simulation
- city scale building energy modelling
- urban energy modeling
- urban energy modelling
- building stock energy modeling
- building stock energy modelling
- district-scale building energy simulation
- neighborhood-scale building energy model
- large-scale building energy simulation

## Boolean Search Blocks

### UBEM and Named Variants

```text
("urban building energy model*" OR UBEM OR "urban building energy simulation")
```

### City-Scale Simulation

```text
("city-scale building energy simulation" OR "city scale building energy simulation" OR "district-scale building energy simulation" OR "neighborhood-scale building energy simulation")
```

### Urban Energy Modeling

```text
("urban energy model*" OR "urban energy simulation" OR "urban energy demand model*" OR "urban-scale energy model*")
```

### Building Stock Modeling

```text
("building stock energy model*" OR "building stock model*" OR "stock-scale building energy model*" OR "large-scale building energy simulation")
```

## Combined Query Candidates

```text
("urban building energy model*" OR UBEM) AND (building* OR district* OR city OR cities OR urban)
```

```text
("city-scale building energy simulation" OR "district-scale building energy simulation") AND (energy OR demand OR consumption)
```

```text
("urban energy model*" OR "urban energy simulation") AND ("building stock" OR buildings OR residential OR commercial)
```

```text
("building stock energy model*" OR "large-scale building energy simulation") AND (urban OR city OR district OR neighborhood)
```

```text
("urban building energy modeling" OR "urban building energy modelling" OR UBEM OR "city-scale building energy simulation" OR "urban energy modeling" OR "building stock energy modeling")
```

## Suggested API Queries

Use one query per API call when possible, then deduplicate downstream.

```text
urban building energy modeling
urban building energy modelling
UBEM building energy
city-scale building energy simulation
district-scale building energy simulation
urban energy modeling buildings
urban energy modelling buildings
building stock energy modeling urban
large-scale building energy simulation
```

## Source Exclusion Note

Some APIs do not support reliable publisher exclusion in the query language.
Apply MDPI/MPDI exclusion during post-processing using source, venue, publisher,
and URL metadata. Do not manually invent replacement records.
