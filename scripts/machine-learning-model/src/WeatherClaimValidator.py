import requests
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

class WeatherClaimValidator:
    def __init__(self, base_url='http://127.0.0.1:5000/weather'):
        """
        Initialize the Weather Claim Validator
        
        :param base_url: Base URL for the weather API endpoint
        """
        self.base_url = base_url
        
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
            # Clean numeric values
            data['rainfall'] = float(str(data.get('rainfall', '0')).split('mm')[0].strip())
            data['temperature'] = float(str(data.get('temperature', '0')).split('°')[0].strip())
            data['humidity'] = float(str(data.get('humidity', '0')).split('%')[0].strip())
            
            return data
        except requests.RequestException as e:
            print(f"Error fetching weather data: {e}")
            return None
        except (ValueError, KeyError) as e:
            print(f"Error parsing weather data: {e}")
            return None
    def fetch_historical_weather(self, location, base_date, days_before):
            """
            Fetch historical weather data for comparison

            :param location: City or region name
            :param base_date: Reference date
            :param days_before: Number of days to look back
            :return: DataFrame of historical weather data
            """
            historical_data = []
            base_date = datetime.strptime(base_date, '%Y-%m-%d')
        
            for day in range(days_before):
                check_date = (base_date - timedelta(days=day)).strftime('%Y-%m-%d')
            hourly_data = self.get_weather_data(location, check_date)
            
            if hourly_data:
                hourly_data['date'] = check_date
                historical_data.append(hourly_data)
        
            return pd.DataFrame(historical_data)
    

    def analyze_claim(self, claim_details):
        """
        Analyze a claim and validate it against current and historical weather data.

        :param claim_details: Dictionary containing claim details.
        :return: Validation result dictionary.
        """
        validation_result = {
            'claim_details': claim_details,
            'validation_status': 'Unable to Process',
            'current_weather': None,
            'historical_analysis': None,
            }

        # Determine the number of days of historical data to fetch
        event_type = claim_details.get('Event Type', '').lower()
        date_descriptor = claim_details.get('Date Descriptor', '').lower()  # e.g., "today", "yesterday", "this month"
    
        days_to_fetch = claim_details.get('Days', 1)  # Default to 1 day
        if event_type == 'drought':
        # Fetch at least 7 days for drought claims
            days_to_fetch = max(days_to_fetch, 7)
        elif date_descriptor == 'this month':
        # Fetch 30 days for "this month" claims
         days_to_fetch = 30

    # Fetch current weather data
        current_weather = self.get_weather_data(
        claim_details.get('Location'),
        claim_details.get('Date')
        )

        if current_weather:
            validation_result['current_weather'] = current_weather

        # Fetch and analyze historical data
        historical_data = self.fetch_historical_weather(
            claim_details.get('Location'),
            claim_details.get('Date'),
            days_to_fetch
        )

        if not historical_data.empty:
            validation_result['historical_analysis'] = self._analyze_historical_context(
                historical_data,
                claim_details.get('Event Type'),
                claim_details.get('Severity')
            )

            validation_result['validation_status'] = self._determine_claim_validity(
                validation_result['historical_analysis'],
                claim_details.get('Event Type'),
                claim_details.get('Severity')
            )

        return validation_result

    
    def _analyze_historical_context(self, historical_data, event_type, severity):
        """
        Analyze historical weather data context
        
        :param historical_data: DataFrame of historical weather data
        :param event_type: Type of weather event
        :param severity: Severity of the event
        :return: Dictionary of historical analysis
        """
        if historical_data.empty:
            return {'analysis': 'No historical data available'}
        
        # Compute basic statistical analyses
        analysis = {
            'rainfall': {
                'mean': historical_data['rainfall'].mean(),
                'median': historical_data['rainfall'].median(),
                'max': historical_data['rainfall'].max(),
                'percentile_90': historical_data['rainfall'].quantile(0.9)
            },
            'temperature': {
                'mean': historical_data['temperature'].mean(),
                'median': historical_data['temperature'].median(),
                'max': historical_data['temperature'].max(),
                'min': historical_data['temperature'].min()
            },
            'humidity': {
                'mean': historical_data['humidity'].mean(),
                'max': historical_data['humidity'].max()
            }
        }
        
        # Additional context based on event type
        if event_type == 'rain' or event_type == 'flood':
            analysis['rainfall_anomaly'] = self._compute_rainfall_anomaly(historical_data)
        
        if event_type == 'drought':
            analysis['drought_indicators'] = self._compute_drought_indicators(historical_data)
        
        return analysis
    
    def _compute_rainfall_anomaly(self, historical_data):
        """
        Compute rainfall anomalies
        
        :param historical_data: DataFrame of historical weather data
        :return: Dictionary of rainfall anomaly metrics
        """
        rainfall_values = historical_data['rainfall']
        
        return {
            'z_score': (rainfall_values.mean() - rainfall_values.max()) / rainfall_values.std(),
            'is_extreme': rainfall_values.max() > rainfall_values.quantile(0.95)
        }
    
    def _compute_drought_indicators(self, historical_data):
        """
        Compute drought-related indicators
        
        :param historical_data: DataFrame of historical weather data
        :return: Dictionary of drought indicators
        """
        return {
            'consecutive_dry_days': self._count_consecutive_low_rainfall_days(historical_data),
            'humidity_trend': historical_data['humidity'].diff().mean()
        }
    
    def _count_consecutive_low_rainfall_days(self, historical_data, threshold=0.1):
        """
        Count consecutive days with low rainfall
        
        :param historical_data: DataFrame of historical weather data
        :param threshold: Rainfall threshold for considering a day 'dry'
        :return: Maximum number of consecutive dry days
        """
        rainfall_series = historical_data['rainfall'] < threshold
        max_consecutive_dry = (rainfall_series.groupby((rainfall_series != rainfall_series.shift()).cumsum())
                                .sum().max())
        return max_consecutive_dry
    
    def _determine_claim_validity(self, historical_analysis, event_type, severity):
        """
        Determine the validity of a claim based on historical context
        
        :param historical_analysis: Dictionary of historical weather analysis
        :param event_type: Type of weather event
        :param severity: Severity of the event
        :return: Claim validation status
        """
        if isinstance(historical_analysis, str):
            return 'Unable to Validate - No Historical Data'
        
        # Validation logic for different event types
        if event_type == 'rain' or event_type == 'flood':
            rainfall_anomaly = historical_analysis.get('rainfall_anomaly', {})
            
            # Check if rainfall is extreme
            if rainfall_anomaly.get('is_extreme', False):
                return 'Validated - Extreme Rainfall Event'
            
            # Check severity mapping
            if severity == 'Heavy' and rainfall_anomaly.get('z_score', 0) > 2:
                return 'Partially Validated - Significant Rainfall Anomaly'
        
        elif event_type == 'drought':
            drought_indicators = historical_analysis.get('drought_indicators', {})
            
            # Check for prolonged dry periods
            if drought_indicators.get('consecutive_dry_days', 0) > 0:
                return 'Validated - Drought Conditions'
        
        return 'Inconclusive - Need Further Investigation'
    
   