"""
Data Ingestion Handler for Web Interface

Handles file uploads, data validation, and preprocessing for the Streamlit
web interface. Supports multiple file formats and provides user feedback.
"""

import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict, List, Optional, Union, Tuple, Any
from pathlib import Path
import io
import json
from dataclasses import dataclass
import logging

from ..data_models.validators import DataValidator, QualityScorer
from ..data_models.corporate_data import CorporateDataModel, FinancialDataModel, AssetDataModel


@dataclass
class FileUploadConfig:
    """Configuration for file upload handling"""
    max_file_size_mb: int = 200
    allowed_extensions: List[str] = None
    required_columns: Dict[str, List[str]] = None
    
    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = ['.csv', '.xlsx', '.xls', '.json']
        
        if self.required_columns is None:
            self.required_columns = {
                'facilities': ['facility_id', 'latitude', 'longitude', 'annual_emissions_tco2'],
                'financial': ['year', 'revenue', 'ebitda', 'capex'],
                'emissions': ['facility_id', 'scope_1', 'scope_2'],
                'carbon_prices': ['year', 'scenario', 'carbon_price_usd_per_tco2']
            }


class FileUploadProcessor:
    """Handles file upload and initial processing"""
    
    def __init__(self, config: FileUploadConfig = None):
        self.config = config or FileUploadConfig()
        self.logger = logging.getLogger(__name__)
        
    def process_uploaded_file(self, uploaded_file, file_type: str) -> Tuple[pd.DataFrame, List[str]]:
        """
        Process uploaded file and return DataFrame with validation messages
        
        Args:
            uploaded_file: Streamlit uploaded file object
            file_type: Type of file ('facilities', 'financial', 'emissions', etc.)
            
        Returns:
            Tuple of (DataFrame, list of validation messages)
        """
        
        validation_messages = []
        
        # File size check
        file_size_mb = len(uploaded_file.getvalue()) / 1024 / 1024
        if file_size_mb > self.config.max_file_size_mb:
            validation_messages.append(
                f"File size ({file_size_mb:.1f} MB) exceeds limit ({self.config.max_file_size_mb} MB)"
            )
            return pd.DataFrame(), validation_messages
        
        # File extension check
        file_extension = Path(uploaded_file.name).suffix.lower()
        if file_extension not in self.config.allowed_extensions:
            validation_messages.append(
                f"File extension {file_extension} not supported. "
                f"Allowed: {', '.join(self.config.allowed_extensions)}"
            )
            return pd.DataFrame(), validation_messages
        
        # Read file based on extension
        try:
            df = self._read_file_by_extension(uploaded_file, file_extension)
            validation_messages.append(f"✓ File loaded successfully ({len(df)} rows)")
        except Exception as e:
            validation_messages.append(f"Error reading file: {str(e)}")
            return pd.DataFrame(), validation_messages
        
        # Validate required columns
        column_validation = self._validate_required_columns(df, file_type)
        validation_messages.extend(column_validation)
        
        # Basic data quality checks
        quality_checks = self._perform_quality_checks(df, file_type)
        validation_messages.extend(quality_checks)
        
        return df, validation_messages
    
    def _read_file_by_extension(self, uploaded_file, extension: str) -> pd.DataFrame:
        """Read file based on its extension"""
        
        if extension == '.csv':
            # Try different encodings and separators
            content = uploaded_file.getvalue()
            
            # Try UTF-8 first
            try:
                df = pd.read_csv(io.StringIO(content.decode('utf-8')))
            except UnicodeDecodeError:
                # Try latin-1 encoding
                df = pd.read_csv(io.StringIO(content.decode('latin-1')))
            
            # Auto-detect if semicolon separated
            if len(df.columns) == 1 and ';' in df.columns[0]:
                uploaded_file.seek(0)
                try:
                    df = pd.read_csv(io.StringIO(content.decode('utf-8')), sep=';')
                except UnicodeDecodeError:
                    df = pd.read_csv(io.StringIO(content.decode('latin-1')), sep=';')
                    
        elif extension in ['.xlsx', '.xls']:
            df = pd.read_excel(uploaded_file)
            
        elif extension == '.json':
            content = uploaded_file.getvalue().decode('utf-8')
            json_data = json.loads(content)
            
            if isinstance(json_data, list):
                df = pd.DataFrame(json_data)
            elif isinstance(json_data, dict):
                df = pd.DataFrame([json_data])
            else:
                raise ValueError("JSON file must contain a list of objects or a single object")
        
        else:
            raise ValueError(f"Unsupported file extension: {extension}")
        
        return df
    
    def _validate_required_columns(self, df: pd.DataFrame, file_type: str) -> List[str]:
        """Validate that required columns are present"""
        
        messages = []
        required_cols = self.config.required_columns.get(file_type, [])
        
        if not required_cols:
            return messages
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            messages.append(f"⚠️ Missing required columns: {', '.join(missing_cols)}")
        else:
            messages.append(f"✓ All required columns present: {', '.join(required_cols)}")
        
        # Check for extra useful columns
        extra_cols = [col for col in df.columns if col not in required_cols]
        if extra_cols:
            messages.append(f"ℹ️ Additional columns found: {', '.join(extra_cols[:5])}{'...' if len(extra_cols) > 5 else ''}")
        
        return messages
    
    def _perform_quality_checks(self, df: pd.DataFrame, file_type: str) -> List[str]:
        """Perform basic data quality checks"""
        
        messages = []
        
        # Check for empty DataFrame
        if df.empty:
            messages.append("⚠️ File is empty")
            return messages
        
        # Check for missing values
        missing_pct = (df.isnull().sum() / len(df) * 100)
        high_missing = missing_pct[missing_pct > 50]
        
        if not high_missing.empty:
            messages.append(f"⚠️ Columns with >50% missing values: {', '.join(high_missing.index.tolist())}")
        
        # Check for duplicate rows
        duplicate_rows = df.duplicated().sum()
        if duplicate_rows > 0:
            messages.append(f"⚠️ Found {duplicate_rows} duplicate rows")
        
        # File-type specific checks
        if file_type == 'facilities':
            messages.extend(self._check_facilities_data(df))
        elif file_type == 'financial':
            messages.extend(self._check_financial_data(df))
        elif file_type == 'emissions':
            messages.extend(self._check_emissions_data(df))
        elif file_type == 'carbon_prices':
            messages.extend(self._check_carbon_prices_data(df))
        
        return messages
    
    def _check_facilities_data(self, df: pd.DataFrame) -> List[str]:
        """Specific validation for facilities data"""
        messages = []
        
        # Check coordinates
        if 'latitude' in df.columns and 'longitude' in df.columns:
            invalid_lat = ((df['latitude'] < -90) | (df['latitude'] > 90)).sum()
            invalid_lng = ((df['longitude'] < -180) | (df['longitude'] > 180)).sum()
            
            if invalid_lat > 0:
                messages.append(f"⚠️ {invalid_lat} rows have invalid latitude values")
            if invalid_lng > 0:
                messages.append(f"⚠️ {invalid_lng} rows have invalid longitude values")
        
        # Check for reasonable emission values
        if 'annual_emissions_tco2' in df.columns:
            negative_emissions = (df['annual_emissions_tco2'] < 0).sum()
            if negative_emissions > 0:
                messages.append(f"⚠️ {negative_emissions} rows have negative emissions")
            
            # Check for extremely high values (likely data entry errors)
            high_emissions = (df['annual_emissions_tco2'] > 10000000).sum()  # 10M tons
            if high_emissions > 0:
                messages.append(f"⚠️ {high_emissions} rows have extremely high emissions (>10M tCO2)")
        
        return messages
    
    def _check_financial_data(self, df: pd.DataFrame) -> List[str]:
        """Specific validation for financial data"""
        messages = []
        
        # Check for negative revenue
        if 'revenue' in df.columns:
            negative_revenue = (df['revenue'] <= 0).sum()
            if negative_revenue > 0:
                messages.append(f"⚠️ {negative_revenue} rows have negative or zero revenue")
        
        # Check EBITDA vs Revenue consistency
        if 'revenue' in df.columns and 'ebitda' in df.columns:
            high_margin = ((df['ebitda'] / df['revenue']) > 1).sum()
            if high_margin > 0:
                messages.append(f"⚠️ {high_margin} rows have EBITDA > Revenue")
        
        return messages
    
    def _check_emissions_data(self, df: pd.DataFrame) -> List[str]:
        """Specific validation for emissions data"""
        messages = []
        
        # Check Scope totals consistency
        scope_cols = [col for col in df.columns if col.lower().startswith('scope_')]
        if len(scope_cols) >= 2:
            # Check for negative emissions
            for col in scope_cols:
                negative = (df[col] < 0).sum()
                if negative > 0:
                    messages.append(f"⚠️ {negative} rows have negative {col}")
        
        return messages
    
    def _check_carbon_prices_data(self, df: pd.DataFrame) -> List[str]:
        """Specific validation for carbon prices data"""
        messages = []
        
        if 'carbon_price_usd_per_tco2' in df.columns:
            negative_prices = (df['carbon_price_usd_per_tco2'] < 0).sum()
            if negative_prices > 0:
                messages.append(f"⚠️ {negative_prices} rows have negative carbon prices")
            
            # Check for extremely high prices (likely errors)
            high_prices = (df['carbon_price_usd_per_tco2'] > 1000).sum()
            if high_prices > 0:
                messages.append(f"⚠️ {high_prices} rows have carbon prices >$1000/tCO2")
        
        return messages


class DataIngestionHandler:
    """Main handler for web interface data ingestion"""
    
    def __init__(self):
        self.upload_processor = FileUploadProcessor()
        self.validator = DataValidator()
        self.quality_scorer = QualityScorer()
        
    def create_upload_interface(self, data_type: str) -> Dict[str, Any]:
        """
        Create Streamlit interface for data upload
        
        Args:
            data_type: Type of data to upload ('facilities', 'financial', etc.)
            
        Returns:
            Dictionary with uploaded data and metadata
        """
        
        st.subheader(f"Upload {data_type.title()} Data")
        
        # File uploader
        uploaded_file = st.file_uploader(
            f"Choose {data_type} file",
            type=['csv', 'xlsx', 'xls', 'json'],
            help=f"Upload your {data_type} data file. Supported formats: CSV, Excel, JSON"
        )
        
        result = {
            'data': pd.DataFrame(),
            'uploaded': False,
            'validation_messages': [],
            'quality_score': 0
        }
        
        if uploaded_file is not None:
            with st.spinner("Processing file..."):
                # Process uploaded file
                df, validation_messages = self.upload_processor.process_uploaded_file(
                    uploaded_file, data_type
                )
                
                result['data'] = df
                result['uploaded'] = True
                result['validation_messages'] = validation_messages
                
                # Display validation messages
                self._display_validation_messages(validation_messages)
                
                if not df.empty:
                    # Calculate quality score
                    quality_score = self.quality_scorer.calculate_overall_score(df, data_type)
                    result['quality_score'] = quality_score
                    
                    # Display data preview
                    self._display_data_preview(df, data_type)
                    
                    # Display quality score
                    self._display_quality_score(quality_score)
        
        return result
    
    def _display_validation_messages(self, messages: List[str]):
        """Display validation messages with appropriate styling"""
        
        if not messages:
            return
        
        # Separate messages by type
        success_msgs = [msg for msg in messages if msg.startswith('✓')]
        warning_msgs = [msg for msg in messages if msg.startswith('⚠️')]
        info_msgs = [msg for msg in messages if msg.startswith('ℹ️')]
        error_msgs = [msg for msg in messages if not any(msg.startswith(x) for x in ['✓', '⚠️', 'ℹ️'])]
        
        # Display each type with appropriate styling
        for msg in success_msgs:
            st.success(msg)
        
        for msg in info_msgs:
            st.info(msg)
            
        for msg in warning_msgs:
            st.warning(msg)
            
        for msg in error_msgs:
            st.error(msg)
    
    def _display_data_preview(self, df: pd.DataFrame, data_type: str):
        """Display preview of uploaded data"""
        
        st.subheader("Data Preview")
        
        # Basic statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rows", len(df))
        with col2:
            st.metric("Columns", len(df.columns))
        with col3:
            missing_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100)
            st.metric("Missing Data", f"{missing_pct:.1f}%")
        
        # Data preview table
        st.dataframe(df.head(10))
        
        # Column information
        with st.expander("Column Information"):
            col_info = pd.DataFrame({
                'Column': df.columns,
                'Data Type': df.dtypes,
                'Non-Null Count': df.count(),
                'Missing %': (df.isnull().sum() / len(df) * 100).round(1)
            })
            st.dataframe(col_info)
    
    def _display_quality_score(self, quality_score: float):
        """Display data quality score with visual indicator"""
        
        st.subheader("Data Quality Score")
        
        # Color-coded quality indicator
        if quality_score >= 80:
            color = "green"
            status = "Excellent"
        elif quality_score >= 60:
            color = "orange"
            status = "Good"
        else:
            color = "red"
            status = "Needs Improvement"
        
        st.metric(
            "Quality Score", 
            f"{quality_score:.0f}/100",
            help=f"Data quality status: {status}"
        )
        
        # Progress bar
        st.progress(quality_score / 100)
    
    def prepare_data_for_analysis(self, uploaded_data: Dict[str, Dict]) -> Dict[str, pd.DataFrame]:
        """
        Prepare all uploaded data for analysis
        
        Args:
            uploaded_data: Dictionary with data from all upload interfaces
            
        Returns:
            Dictionary with cleaned and validated DataFrames
        """
        
        prepared_data = {}
        
        for data_type, data_info in uploaded_data.items():
            if data_info['uploaded'] and not data_info['data'].empty:
                # Apply data cleaning and standardization
                cleaned_df = self._clean_and_standardize(data_info['data'], data_type)
                prepared_data[data_type] = cleaned_df
        
        return prepared_data
    
    def _clean_and_standardize(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """Apply data cleaning and standardization"""
        
        df_clean = df.copy()
        
        # Remove completely empty rows and columns
        df_clean = df_clean.dropna(how='all').dropna(axis=1, how='all')
        
        # Standardize column names (lowercase, underscores)
        df_clean.columns = df_clean.columns.str.lower().str.replace(' ', '_').str.replace('-', '_')
        
        # Data type specific cleaning
        if data_type == 'facilities':
            df_clean = self._clean_facilities_data(df_clean)
        elif data_type == 'financial':
            df_clean = self._clean_financial_data(df_clean)
        elif data_type == 'emissions':
            df_clean = self._clean_emissions_data(df_clean)
        
        return df_clean
    
    def _clean_facilities_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize facilities data"""
        
        # Ensure facility_id is string
        if 'facility_id' in df.columns:
            df['facility_id'] = df['facility_id'].astype(str)
        
        # Clean coordinate data
        for coord_col in ['latitude', 'longitude']:
            if coord_col in df.columns:
                # Convert to numeric, invalid values become NaN
                df[coord_col] = pd.to_numeric(df[coord_col], errors='coerce')
        
        return df
    
    def _clean_financial_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize financial data"""
        
        # Ensure year is integer
        if 'year' in df.columns:
            df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')
        
        # Convert financial columns to numeric
        financial_cols = ['revenue', 'ebitda', 'opex', 'capex', 'total_assets', 'debt', 'equity']
        for col in financial_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def _clean_emissions_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize emissions data"""
        
        # Convert emission columns to numeric
        emission_cols = [col for col in df.columns if 'scope' in col.lower() or 'emission' in col.lower()]
        for col in emission_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df