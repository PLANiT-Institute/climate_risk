# Climate Financial Risk Assessment Tool

A comprehensive Python-based tool for assessing climate-related financial risks and net-zero pathways. This tool provides quantitative analysis of transition risk, physical risk, and climate Value at Risk (VaR) for portfolio assessment and regulatory compliance.

## 🌍 Overview

The Climate Financial Risk Assessment Tool calculates climate-related financial risks across multiple dimensions:

- **Transition Risk**: Models carbon pricing scenarios and emission reduction costs
- **Physical Risk**: Assesses climate hazard-based damage estimates using CLIMADA integration
- **Net-Zero Pathways**: Creates optimized emission reduction trajectories to net-zero by 2050
- **Climate Value at Risk (VaR)**: Performs Monte Carlo simulations for risk quantification

## 📋 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Configuration](#configuration)
- [Input Data Format](#input-data-format)
- [Output Structure](#output-structure)
- [API Reference](#api-reference)
- [Web Interface](#web-interface)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### Core Analysis Modules

1. **Transition Risk Analysis**
   - Carbon pricing scenario modeling (NDC, Below2C, NetZero)
   - Emission Trading System (ETS) cost calculations
   - Sector-specific carbon intensity analysis
   - NPV calculations with configurable discount rates

2. **Physical Risk Assessment**
   - CLIMADA integration for hazard modeling
   - Flood, drought, and extreme weather risk assessment
   - Asset-level damage estimates
   - Geospatial analysis capabilities

3. **Net-Zero Pathway Optimization**
   - Linear and absolute emission reduction trajectories
   - Cost-optimized abatement pathways using linear programming
   - Technology-specific marginal abatement cost curves (MACC)
   - Customizable target years and reduction rates

4. **Climate VaR Calculation**
   - Monte Carlo simulation framework
   - Probabilistic risk distributions
   - 95th percentile VaR estimates
   - Correlation modeling between risk factors

### Reporting and Visualization

- Automated report generation (Markdown and JSON formats)
- Interactive visualizations with matplotlib/seaborn
- Scenario comparison charts
- Risk distribution histograms
- Streamlit web interface for interactive analysis

### Advanced Features

- Multi-scenario analysis support
- Configurable time horizons and discount rates
- Sensitivity analysis capabilities
- Export to multiple formats (CSV, Excel, JSON)
- Command-line interface (CLI) for batch processing

## 🔧 Installation

### Prerequisites

- Python 3.8+ (recommended: 3.11)
- pip or conda package manager

### Core Dependencies

```bash
# Install core dependencies
pip install pandas numpy matplotlib seaborn scipy pulp openpyxl

# For geospatial analysis (optional)
pip install geopandas rasterio shapely

# For web interface (optional)
pip install streamlit

# For specialized climate modeling (optional)
pip install climada climada-petals
```

### Complete Installation

```bash
# Clone the repository
git clone https://github.com/your-username/climate-risk-tool.git
cd climate-risk-tool

# Install all dependencies
pip install -r requirements.txt

# Verify installation
python main.py --help
```

### Requirements File

Create a `requirements.txt` file with:

```txt
# Core data analysis
pandas>=1.5.0
numpy>=1.20.0
scipy>=1.8.0

# Visualization
matplotlib>=3.5.0
seaborn>=0.11.0

# Optimization
pulp>=2.6.0

# File formats
openpyxl>=3.0.0

# Geospatial (optional)
geopandas>=0.12.0
shapely>=1.8.0
rasterio>=1.3.0

# Climate modeling (optional)
climada>=3.0.0
climada-petals>=3.0.0

# Web interface (optional)
streamlit>=1.20.0
```

## 🚀 Quick Start

### Basic Usage

```bash
# Run with default settings
python main.py

# Specify custom input files
python main.py \
  --facilities data/my_facilities.xlsx \
  --carbon_prices data/my_carbon_prices.xlsx \
  --output_dir results/

# Run specific scenarios
python main.py --scenarios NDC Below2C --approaches linear optimal
```

### Example with Sample Data

```bash
# Generate sample data
python generate_example_csv.py

# Run analysis with sample data
python main.py \
  --facilities example_facilities.csv \
  --carbon_prices data/carbon_prices.xlsx \
  --n_simulations 5000
```

## 📖 Usage

### Command Line Interface

```bash
python main.py [OPTIONS]

Options:
  --facilities PATH           Path to facilities Excel/CSV file
  --carbon_prices PATH        Path to carbon prices Excel file
  --hazard PATH              Path to flood hazard netCDF file
  --abatement_costs PATH     Path to abatement costs Excel file
  --output_dir PATH          Output directory (default: outputs)
  --scenarios [NDC|Below2C|NetZero]  Scenarios to analyze
  --approaches [linear|optimal]      Net-zero approaches
  --discount_rate FLOAT      Discount rate for NPV (default: 0.03)
  --n_simulations INT        Monte Carlo simulations (default: 1000)
```

### Python API

```python
from main import ClimateRiskTool

# Configure analysis
config = {
    "facilities": "data/facilities.xlsx",
    "carbon_prices": "data/carbon_prices.xlsx",
    "hazard": "data/flood_hazard.nc",
    "output_dir": "results",
    "discount_rate": 0.03,
    "n_simulations": 1000
}

# Initialize tool
tool = ClimateRiskTool(config)

# Run financial risk analysis
tool.run_financial_risk_analysis(scenarios=["NDC", "Below2C"])

# Run net-zero analysis
tool.run_net_zero_analysis(approaches=["linear", "optimal"])

# Generate reports
tool.generate_reports()
```

## ⚙️ Configuration

### Scenarios

The tool supports three main climate scenarios:

1. **NDC (Nationally Determined Contributions)**
   - Current policy commitments
   - Moderate carbon pricing trajectory
   - ~3°C warming pathway

2. **Below2C (Below 2 Degrees)**
   - Paris Agreement ambitious targets
   - Higher carbon pricing
   - ~2°C warming pathway

3. **NetZero (Net Zero by 2050)**
   - Most ambitious scenario
   - Highest carbon pricing
   - 1.5°C warming pathway

### Net-Zero Approaches

1. **Linear Approach**
   - Constant emission reduction rate
   - Simple implementation
   - Uniform annual reductions

2. **Optimal Approach**
   - Cost-minimized pathway
   - Uses marginal abatement cost curves
   - Technology-specific optimization

## 📊 Input Data Format

### Facilities Data (Excel/CSV)

Required columns:
```csv
facility_id,facility_name,sector,country,latitude,longitude,annual_emissions_tco2,asset_value_usd
FAC001,Power Plant A,Energy,USA,40.7128,-74.0060,500000,1000000000
FAC002,Steel Mill B,Industry,DEU,52.5200,13.4050,750000,500000000
```

### Carbon Prices Data (Excel)

Required structure:
```csv
year,scenario,carbon_price_usd_per_tco2
2025,NDC,50
2025,Below2C,75
2025,NetZero,100
2030,NDC,75
2030,Below2C,125
2030,NetZero,200
```

### Abatement Costs Data (Excel)

Required structure:
```csv
sector,technology,abatement_potential_tco2,cost_usd_per_tco2
Energy,Solar PV,1000000,25
Energy,Wind,800000,30
Industry,Energy Efficiency,500000,40
```

## 📈 Output Structure

```
outputs/
├── financial_risk_summary.csv
├── scenario_comparison.png
├── transition_risk_NDC.csv
├── transition_risk_Below2C.csv
├── physical_risk_results.csv
├── netzero_pathway_linear.csv
├── netzero_pathway_optimal.csv
├── climate_var_linear_distribution.csv
├── climate_var_linear_hist.png
└── reports/
    ├── financial_risk/
    │   ├── financial_risk_report.md
    │   ├── summary.json
    │   └── visualizations/
    └── net_zero/
        ├── net_zero_report.md
        ├── summary.json
        └── visualizations/
```

### Key Output Files

1. **Financial Risk Summary** (`financial_risk_summary.csv`)
   - NPV costs by scenario
   - Annual cost profiles
   - Risk metrics

2. **Transition Risk Results** (`transition_risk_[scenario].csv`)
   - Facility-level carbon costs
   - Year-by-year projections
   - ETS cost calculations

3. **Physical Risk Results** (`physical_risk_results.csv`)
   - Hazard exposure assessments
   - Damage estimates
   - Risk ratings

4. **Net-Zero Pathways** (`netzero_pathway_[approach].csv`)
   - Emission trajectories
   - Abatement costs
   - Technology deployment

5. **Climate VaR Distribution** (`climate_var_[approach]_distribution.csv`)
   - Monte Carlo simulation results
   - Probability distributions
   - Risk quantiles

## 🖥️ Web Interface

Launch the Streamlit web interface:

```bash
streamlit run app/streamlit_app.py
```

Or use the simplified web interface:

```bash
python web.py
```

The web interface provides:
- Interactive parameter configuration
- Real-time analysis execution
- Dynamic visualizations
- Results download capabilities

## 📚 API Reference

### ClimateRiskTool Class

```python
class ClimateRiskTool:
    def __init__(self, config: Dict[str, Any])
    def run_financial_risk_analysis(self, scenarios: List[str] = None)
    def run_net_zero_analysis(self, approaches: List[str] = None)
    def generate_reports(self)
```

### Core Modules

#### TransitionRisk
```python
from util.transition_risk import TransitionRisk

tr = TransitionRisk(facilities_path, carbon_prices_path, scenario="NDC")
results = tr.run()
```

#### PhysicalRisk
```python
from util.physical_risk import PhysicalRisk

pr = PhysicalRisk(facilities_df, hazard_path)
results = pr.run()
```

#### NetZeroPathway
```python
from util.net_zero import NetZeroPathway, OptimalEmissionPathway

# Linear pathway
nz = NetZeroPathway(facilities_path, approach="linear")
pathway = nz.run()

# Optimal pathway
opt = OptimalEmissionPathway(facilities_path, carbon_prices_path, abatement_costs_path)
pathway = opt.run()
```

#### ClimateVaR
```python
from util.climate_var import ClimateVaR

cvar = ClimateVaR(transition_df, physical_df, netzero_df, discount_rate=0.03)
var_95, distribution = cvar.run_deep_monte_carlo(n_sim=1000, percentile=0.95)
```

## 🔍 Examples

### Example 1: Basic Analysis

```python
# Configure for basic analysis
config = {
    "facilities": "data/input_facilities.xlsx",
    "carbon_prices": "data/carbon_prices.xlsx",
    "output_dir": "basic_analysis",
    "discount_rate": 0.05
}

tool = ClimateRiskTool(config)
tool.run_financial_risk_analysis(scenarios=["NDC"])
```

### Example 2: Comprehensive Analysis

```python
# Full analysis with all scenarios and approaches
config = {
    "facilities": "data/large_portfolio.xlsx",
    "carbon_prices": "data/carbon_prices.xlsx",
    "hazard": "data/flood_hazard.nc",
    "abatement_costs": "data/abatement_costs.xlsx",
    "output_dir": "comprehensive_analysis",
    "discount_rate": 0.03,
    "n_simulations": 10000
}

tool = ClimateRiskTool(config)
tool.run_financial_risk_analysis(scenarios=["NDC", "Below2C", "NetZero"])
tool.run_net_zero_analysis(approaches=["linear", "optimal"])
tool.generate_reports()
```

### Example 3: Custom Scenario Analysis

```python
# Sensitivity analysis across discount rates
discount_rates = [0.02, 0.03, 0.05, 0.07]
results = {}

for rate in discount_rates:
    config = {
        "facilities": "data/facilities.xlsx",
        "carbon_prices": "data/carbon_prices.xlsx",
        "output_dir": f"sensitivity_{rate}",
        "discount_rate": rate
    }
    
    tool = ClimateRiskTool(config)
    tool.run_financial_risk_analysis()
    results[rate] = tool.results
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/

# Run specific test modules
python -m pytest tests/test_transition_risk.py
python -m pytest tests/test_net_zero.py

# Run with coverage
python -m pytest --cov=util tests/
```

## 📈 Performance Considerations

### Optimization Tips

1. **Large Portfolios**: Use batch processing for >1000 facilities
2. **Monte Carlo Simulations**: Start with 1000 simulations, increase as needed
3. **Geospatial Analysis**: Consider memory usage with large raster datasets
4. **Parallel Processing**: Utilize multiprocessing for scenario analysis

### Memory Management

```python
# For large datasets, process in chunks
chunk_size = 100
for i in range(0, len(facilities_df), chunk_size):
    chunk = facilities_df.iloc[i:i+chunk_size]
    # Process chunk
```

## 🔧 Troubleshooting

### Common Issues

1. **Memory Errors**: Reduce simulation count or process in batches
2. **Geospatial Dependencies**: Install GDAL system libraries
3. **Excel File Errors**: Ensure openpyxl is installed
4. **CLIMADA Issues**: Check system dependencies and data availability

### Debug Mode

```bash
# Enable verbose logging
python main.py --verbose --debug

# Check dependency versions
python -c "import pandas; print(pandas.__version__)"
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md).

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/your-username/climate-risk-tool.git

# Install development dependencies
pip install -r requirements-dev.txt

# Run pre-commit hooks
pre-commit install

# Run tests
python -m pytest
```

### Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Add docstrings to all public functions
- Write unit tests for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- CLIMADA platform for physical risk modeling
- Paris Agreement scenario frameworks
- IPCC AR6 methodologies
- Open-source climate risk community

## 📞 Support

For questions and support:
- Create an issue on GitHub
- Email: support@climate-risk-tool.com
- Documentation: https://climate-risk-tool.readthedocs.io

## 🗺️ Roadmap

### Upcoming Features

- [ ] Machine learning-based risk prediction
- [ ] Real-time data integration
- [ ] Enhanced visualization dashboard
- [ ] API endpoint development
- [ ] Docker containerization
- [ ] Cloud deployment templates

### Version History

- **v1.0.0**: Initial release with core functionality
- **v1.1.0**: Added optimal pathway optimization
- **v1.2.0**: Enhanced physical risk modeling
- **v2.0.0**: Web interface and API development (planned)

---

*This tool is designed for financial risk assessment and regulatory compliance. Results should be validated against industry standards and used in conjunction with expert judgment.*