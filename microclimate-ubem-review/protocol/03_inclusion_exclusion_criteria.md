# Inclusion and Exclusion Criteria

These criteria are used for title/abstract screening of
`data/processed/deduplicated_records.csv`. Automated screening is a first pass
only; uncertain records must be retained for manual review.

## Include

1. Studies explicitly related to UBEM, district-scale building energy modeling,
   city-scale building energy simulation, or building stock energy modeling.
2. Studies that include urban microclimate, urban climate, local weather, UHI,
   urban canopy, CFD, ENVI-met, WRF, UWG, or sensor-based weather correction.
3. Studies that analyze energy demand, heating, cooling, peak load, thermal
   comfort, overheating, retrofit, carbon, or policy scenarios.
4. Review articles directly discussing UBEM-microclimate coupling, UCM-UBEM
   integration, or weather data transformation for urban energy modeling.
5. Studies at neighborhood, campus, district, or city scale.

## Exclude

1. Single-building BEM without urban context.
2. Pure urban climate studies with no building energy outcome.
3. Pure HVAC control studies without urban-scale modeling.
4. Pure remote sensing studies with no energy modeling link.
5. General UBEM reviews with no visible microclimate relevance, unless they are
   explicitly retained as background by a human reviewer.

## Uncertain

Use `uncertain` when the metadata is insufficient for a reliable include/exclude
decision. In particular:

- Do not exclude a paper solely because the abstract is missing.
- If the paper mentions UBEM and microclimate but the energy outcome is unclear,
  mark `uncertain`.
- Papers without enough metadata for screening should be marked `uncertain`
  rather than excluded, unless title/metadata clearly places them outside scope.

## Screening Labels

- `include`: eligible for full-text review or extraction.
- `exclude`: outside scope under the criteria above.
- `uncertain`: keep for manual review.

## Decision Rule

An `include` decision needs visible evidence from title, abstract, keywords,
venue, or other local metadata that the study connects urban-scale building
energy modeling, microclimate/urban-climate information, and an energy,
comfort, carbon, retrofit, or policy outcome. Automated scripts must not infer
paper content beyond the available metadata.
