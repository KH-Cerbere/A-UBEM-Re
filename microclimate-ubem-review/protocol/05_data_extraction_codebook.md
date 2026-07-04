# Data Extraction Codebook

The evidence matrix is the core evidence base for the review. It must be filled
only from abstracts, PDF notes, extraction tables, source text, tables, figures,
supplementary materials, or traceable researcher notes.

Do not infer paper findings. If information is absent, write `not reported`.

## Identity Fields

- `paper_id`: stable local identifier assigned after deduplication.
- `citation_key`: local citation key generated from available metadata or
  imported from BibTeX.
- `title`: source title.
- `year`: publication year.
- `source`: import source, such as OpenAlex, Crossref, arXiv, local_bibtex, or
  local_csv.
- `DOI`: normalized DOI from imported metadata.
- `journal`: journal, conference, repository, or report venue.
- `doi`: lower-case duplicate of `DOI` for export compatibility.

## Study Description

- `study_type`: empirical, modeling, review, methodological, framework,
  case_study, dataset, or not reported.
- `review_or_original`: review, original, or not reported.
- `city`: case-study city or not reported.
- `country`: case-study country or not reported.
- `climate_zone`: reported climate zone or not reported.
- `spatial_scale`: neighborhood, campus, district, city, regional, stock,
  multi-city, or not reported.
- `building_type`: residential, commercial, office, school, mixed, public,
  industrial, or not reported.
- `urban_form_variables`: sky view factor, canyon geometry, morphology, tree
  canopy, land cover, density, albedo, impervious surface, or not reported.

## Microclimate Evidence

- `microclimate_variable`: air temperature, humidity, wind speed, solar
  radiation, longwave radiation, surface temperature, land surface temperature,
  UHI intensity, tree canopy, sky view factor, anthropogenic heat, or not
  reported.
- `microclimate_data_source`: weather station, mobile sensor, IoT sensor,
  satellite, remote sensing, ENVI-met, WRF, UCM, UWG, CFD, EPW/TMY, field
  campaign, or not reported.
- `weather_file_type`: EPW, TMY, morphed EPW, UWG-transformed EPW,
  sensor-corrected weather, WRF-derived weather, or not reported.
- `microclimate_model`: UWG, ENVI-met, WRF, UCM, CFD, custom model, or not
  reported.

## UBEM and Coupling Evidence

- `ubem_tool`: CitySim, UMI, TEASER, CityBES, SimStadt, custom UBEM, or not
  reported.
- `bem_engine`: EnergyPlus, DOE-2, Modelica, TRNSYS, ESP-r, custom engine, or
  not reported.
- `coupling_strategy`: EPW substitution, weather file transformation, UWG,
  CFD coupling, ENVI-met coupling, WRF/UCM coupling, sensor-based correction,
  remote-sensing correction, hybrid observational-simulation workflow,
  co-simulation, or not reported.
- `coupling_direction`: one-way, two-way, offline, online, iterative, or not
  reported.
- `temporal_resolution`: sub-hourly, hourly, daily, monthly, annual, scenario,
  or not reported.
- `spatial_resolution`: sensor point, building, block, grid, neighborhood,
  district, city, regional, or not reported.

## Validation and Uncertainty Evidence

- `validation_data`: weather stations, mobile sensors, IoT sensors, smart
  meters, district heating/cooling data, measured indoor temperature, satellite
  land surface temperature, utility bills, benchmark, or not reported.
- `calibration_method`: manual calibration, automated calibration, Bayesian,
  inverse modeling, parameter tuning, none, or not reported.
- `uncertainty_method`: sensitivity analysis, Monte Carlo, scenario analysis,
  Bayesian, ensemble, error propagation, none, or not reported.
- `sensitivity_method`: local sensitivity, global sensitivity, Morris, Sobol,
  scenario comparison, none, or not reported.

## Output and Application Evidence

- `energy_output`: heating EUI, cooling EUI, total EUI, electricity, gas, peak
  load, demand profile, or not reported.
- `comfort_output`: thermal comfort, overheating hours, indoor temperature,
  heat exposure, or not reported.
- `carbon_output`: operational carbon, emissions, grid carbon, lifecycle carbon,
  or not reported.
- `policy_application`: retrofit, heat mitigation, climate adaptation, carbon
  policy, zoning, urban planning, resilience, demand response, or not reported.
- `key_finding`: author-reported finding relevant to microclimate-aware UBEM, or
  not reported.
- `reported_energy_impact`: quantitative or qualitative reported energy impact,
  or not reported.
- `reported_temperature_impact`: quantitative or qualitative reported
  temperature impact, or not reported.
- `limitations`: author-reported limitations, or not reported.
- `reproducibility`: code/data availability, workflow transparency, partial,
  unavailable, or not reported.
- `relevance_to_review`: high, medium, low, background, or not reported.

## Critical Fields

These fields are most important for evidence synthesis:

- `microclimate_data_source`
- `coupling_strategy`
- `validation_data`
- `uncertainty_method`
- `reported_energy_impact`
- `policy_application`
