# Climate Risk Assessment Tool - Complete Structure

## 1. Data Models & Schema

### Corporate Data Models
```
climate_risk_tool/
├── data_models/
│   ├── __init__.py
│   ├── corporate_data.py          # Financial, asset, operational data models
│   ├── emissions_data.py          # Scope 1, 2, 3 emissions models
│   ├── decarbonization_projects.py # Abatement project catalog
│   ├── validators.py              # Data validation and cleaning
│   └── schema.py                  # Pydantic schemas for API
```

### External Data Integration
```
├── external_data/
│   ├── __init__.py
│   ├── carbon_pricing.py          # IEA, NGFS scenario data
│   ├── technology_costs.py        # Solar, battery, EV cost curves
│   ├── commodity_prices.py        # Energy and commodity forecasts
│   └── climate_hazards.py         # Geospatial hazard data (placeholder)
```

## 2. Core Analysis Engines

### Transition Risk (Enhanced)
```
├── transition/
│   ├── __init__.py
│   ├── calculator.py              # Enhanced with sensitivity analysis
│   ├── cost_curves.py             # Technology cost modeling
│   ├── carbon_pricing.py          # Multi-scenario carbon price impact
│   └── sensitivity_analysis.py    # ΔEBITDA, ΔOPEX sensitivity
```

### Decarbonization & RE100 Strategy
```
├── decarbonization/
│   ├── __init__.py
│   ├── macc_generator.py          # Marginal Abatement Cost Curve
│   ├── pathway_optimizer.py       # Net-zero pathway optimization
│   ├── re100_strategy.py          # RE100 investment strategy
│   ├── project_prioritizer.py     # Abatement project ranking
│   └── financial_optimizer.py     # ROI, IRR, CAPEX optimization
```

### Physical Risk (Placeholder Structure)
```
├── physical/
│   ├── __init__.py
│   ├── risk_assessment.py         # Asset risk heat mapping
│   ├── financial_quantification.py # VaR, PML calculations
│   ├── geospatial_analysis.py     # GIS-based risk analysis
│   └── hazard_models.py           # Climate hazard modeling
```

## 3. Financial Analysis & Valuation
```
├── financial/
│   ├── __init__.py
│   ├── valuation.py              # NPV, IRR, WACC calculations
│   ├── cash_flow_modeling.py     # Multi-year cash flow projections
│   ├── investment_analysis.py    # CAPEX optimization & scheduling
│   └── risk_metrics.py           # Financial risk quantification
```

## 4. Reporting & Visualization
```
├── reporting/
│   ├── __init__.py
│   ├── report_generator.py       # Enhanced report generation
│   ├── visualizations.py         # Charts and graphs
│   ├── dashboard_data.py         # Data preparation for web interface
│   └── templates/                # Report templates
│       ├── financial_risk_report.md
│       ├── decarbonization_report.md
│       └── executive_summary.md
```

## 5. Web Interface Data Layer
```
├── web_interface/
│   ├── __init__.py
│   ├── data_ingestion.py         # Excel/CSV upload handling
│   ├── result_processor.py       # Web-friendly result formatting
│   ├── session_manager.py        # User session data management
│   └── api_endpoints.py          # FastAPI/Flask endpoints (future)
```

## 6. Configuration & Utilities
```
├── config/
│   ├── __init__.py
│   ├── scenarios.py              # Climate scenario definitions
│   ├── parameters.py             # Default parameters and constants
│   └── validation_rules.py       # Business logic validation
```

## 7. Data Processing Pipeline
```
├── pipeline/
│   ├── __init__.py
│   ├── data_loader.py           # Multi-format data loading
│   ├── preprocessor.py          # Data cleaning and preparation
│   ├── calculation_engine.py    # Main calculation orchestrator
│   └── output_formatter.py      # Result formatting and export
```