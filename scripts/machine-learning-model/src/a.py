import requests
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from enum import Enum

class EventType(Enum):
    RAIN = 'rain'
    FLOOD = 'flood'
    DROUGHT = 'drought'

class Severity(Enum):
    MILD = 'mild'
    MODERATE = 'moderate'
    SEVERE = 'severe'

class WeatherClaimValidator:
    def __init__(self, base_url='http://127.0.0.1:5000/weather'):
        self.base_url = base_url
        self.MIN_DROUGHT_DAYS = 7  # Minimum days needed for drought analysis
        self.MONTHLY_DAYS = 30
        self.RAINFALL_THRESHOLD = 0.1  # mm, threshold for dry day
        self.EXTREME_RAINFALL_PERCENTILE = 95
        
    def get_weather_data(self, location, date, hour=12):
        try:
            params = {
                'location': location,
                'date': date,
                'hour': hour
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            return {
                'rainfall': self._parse_numeric_value(data.get('rainfall', '0'), 'mm'),
                'temperature': self._parse_numeric_value(data.get('temperature', '0'), '°'),
                'humidity': self._parse_numeric_value(data.get('humidity', '0'), '%'),
                'location': location,
                'date': date
            }
        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"Error processing weather data: {e}")
            return None

    def _parse_numeric_value(self, value_str, unit):
        """Parse numeric values with units safely"""
        try:
            return float(str(value_str).split(unit)[0].strip())
        except (ValueError, IndexError):
            return 0.0

    def _determine_analysis_period(self, claim_details):
        """Determine the appropriate analysis period based on claim type"""
        event_type = claim_details.get('Event Type', '').lower()
        date_descriptor = claim_details.get('Date Descriptor', '').lower()
        
        if event_type == EventType.DROUGHT.value:
            if date_descriptor == 'this month':
                return self.MONTHLY_DAYS
            return max(claim_details.get('Days', self.MIN_DROUGHT_DAYS), self.MIN_DROUGHT_DAYS)
        
        if date_descriptor == 'this month':
            return self.MONTHLY_DAYS
        elif date_descriptor == 'yesterday':
            return 2  # Current day + yesterday
        return 1  # Default to current day only

    def _validate_claim_inputs(self, claim_details):
        """Validate incoming claim details"""
        required_fields = ['Location', 'Date', 'Event Type', 'Severity']
        if not all(field in claim_details for field in required_fields):
            return False, "Missing required claim details"
            
        event_type = claim_details.get('Event Type', '').lower()
        if event_type == EventType.DROUGHT.value and claim_details.get('Days', 0) < self.MIN_DROUGHT_DAYS:
            return False, f"Drought claims require minimum {self.MIN_DROUGHT_DAYS} days of data"
            
        return True, None

    def analyze_claim(self, claim_details):
        """Enhanced claim analysis with input validation and improved context handling"""
        is_valid, error_message = self._validate_claim_inputs(claim_details)
        if not is_valid:
            return {
                'validation_status': 'Invalid Claim',
                'error_message': error_message
            }

        days_to_analyze = self._determine_analysis_period(claim_details)
        
        historical_data = self.fetch_historical_weather(
            claim_details['Location'],
            claim_details['Date'],
            days_to_analyze
        )
        
        if historical_data.empty:
            return {
                'validation_status': 'Unable to Validate',
                'error_message': 'No weather data available'
            }

        analysis_result = self._analyze_historical_context(
            historical_data,
            claim_details['Event Type'],
            claim_details['Severity']
        )

        return {
            'validation_status': self._determine_claim_validity(
                analysis_result,
                claim_details['Event Type'],
                claim_details['Severity']
            ),
            'historical_analysis': analysis_result,
            'data_period': f"{days_to_analyze} days",
            'location': claim_details['Location']
        }

    def _analyze_historical_context(self, historical_data, event_type, severity):
        """Enhanced historical context analysis with improved statistical measures"""
        if historical_data.empty:
            return {'analysis': 'No historical data available'}
        
        analysis = {
            'rainfall_stats': {
                'mean': historical_data['rainfall'].mean(),
                'median': historical_data['rainfall'].median(),
                'max': historical_data['rainfall'].max(),
                'std': historical_data['rainfall'].std(),
                'consecutive_dry_days': self._count_consecutive_low_rainfall_days(historical_data),
                'total_rainfall': historical_data['rainfall'].sum()
            },
            'temperature_stats': {
                'mean': historical_data['temperature'].mean(),
                'max': historical_data['temperature'].max(),
                'min': historical_data['temperature'].min(),
                'range': historical_data['temperature'].max() - historical_data['temperature'].min()
            }
        }
        
        if event_type in [EventType.RAIN.value, EventType.FLOOD.value]:
            analysis['event_specific'] = self._analyze_rainfall_event(historical_data)
        elif event_type == EventType.DROUGHT.value:
            analysis['event_specific'] = self._analyze_drought_event(historical_data)
            
        return analysis

    def _analyze_rainfall_event(self, data):
        """Detailed analysis for rainfall events"""
        daily_totals = data.groupby('date')['rainfall'].sum()
        return {
            'peak_daily_rainfall': daily_totals.max(),
            'rainfall_intensity': daily_totals.max() / 24,  # mm/hour
            'extreme_rainfall_threshold': daily_totals.quantile(0.95),
            'days_above_normal': len(daily_totals[daily_totals > daily_totals.mean() + daily_totals.std()]),
            'total_period_rainfall': daily_totals.sum()
        }

    def _analyze_drought_event(self, data):
        """Detailed analysis for drought events"""
        return {
            'dry_spell_length': self._count_consecutive_low_rainfall_days(data),
            'total_rainfall': data['rainfall'].sum(),
            'avg_daily_rainfall': data['rainfall'].mean(),
            'days_below_threshold': len(data[data['rainfall'] < self.RAINFALL_THRESHOLD]),
            'humidity_trend': data['humidity'].diff().mean(),
            'temperature_anomaly': (data['temperature'].mean() - data['temperature'].rolling(window=7).mean()).mean()
        }

    def _determine_claim_validity(self, analysis, event_type, severity):
        """Enhanced claim validity determination with more sophisticated criteria"""
        if not analysis or 'event_specific' not in analysis:
            return 'Unable to Validate - Insufficient Data'

        event_data = analysis['event_specific']
        
        if event_type in [EventType.RAIN.value, EventType.FLOOD.value]:
            return self._validate_rainfall_claim(event_data, severity)
        elif event_type == EventType.DROUGHT.value:
            return self._validate_drought_claim(event_data, severity)
            
        return 'Unable to Validate - Unknown Event Type'

    def _validate_rainfall_claim(self, event_data, severity):
        """Validate rainfall-related claims with specific criteria"""
        peak_rainfall = event_data['peak_daily_rainfall']
        intensity = event_data['rainfall_intensity']
        threshold = event_data['extreme_rainfall_threshold']
        
        if peak_rainfall > threshold * 1.5:
            return 'Validated - Extreme Rainfall Event'
        elif peak_rainfall > threshold and severity.lower() in ['moderate', 'severe']:
            return 'Validated - Significant Rainfall'
        elif intensity > 10 and severity.lower() == 'severe':  # 10mm/hour threshold
            return 'Validated - High Intensity Rainfall'
        elif peak_rainfall > threshold * 0.75:
            return 'Partially Validated - Moderate Rainfall'
            
        return 'Invalid - Rainfall Below Expected Threshold'

    def _validate_drought_claim(self, event_data, severity):
        """Validate drought claims with comprehensive criteria"""
        dry_spell = event_data['dry_spell_length']
        total_rainfall = event_data['total_rainfall']
        days_below_threshold = event_data['days_below_threshold']
        
        if dry_spell >= 14 and severity.lower() == 'severe':
            return 'Validated - Severe Drought Conditions'
        elif dry_spell >= 7 and days_below_threshold >= 5:
            return 'Validated - Moderate Drought Conditions'
        elif total_rainfall < 5 and dry_spell >= 5:  # 5mm total rainfall threshold
            return 'Partially Validated - Mild Drought Conditions'
            
        return 'Invalid - Insufficient Drought Indicators'