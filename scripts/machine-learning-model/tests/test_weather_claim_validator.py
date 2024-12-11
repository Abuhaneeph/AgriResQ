from claim_processing import process_claims_from_text
from a import WeatherClaimValidator

def test_claim_processing():
    """
    Test the claim processing functionality
    """
    print("\n--- Testing Claim Processing ---")
    
    # Test various types of claims
    test_claims = [
        "Heavy rain in Lagos yesterday",
        "Severe drought in Kano this March",
        "Severe storm in Abuja last week",
        "Light floods in Port Harcourt recently",
        "Intense wildfire in Jos",
        "Unknown disaster in Kaduna"
    ]
    
    # Process claims
    processed_claims = process_claims_from_text(test_claims)
    
    # Print processed claims
    for claim in processed_claims:
        print("\nClaim:", claim['Claim'])
        print("Event Type:", claim['Event Type'])
        print("Severity:", claim['Severity'])
        print("Date:", claim['Date'])
        print("Location:", claim['Location'])
        print("Days:", claim['Days'])

def test_claim_validation():
    """
    Test the claim validation functionality
    """
    print("\n--- Testing Claim Validation ---")
    
    # Initialize validator
    validator = WeatherClaimValidator()
    
    # Processed claims to validate
    test_claims = [
        {
            "Event Type": "rain",
            "Severity": "Heavy",
            "Location": "Lagos",
            "Date": "2024-01-15",
            "Days": 7
        },
        {
            "Event Type": "drought",
            "Severity": "Severe",
            "Location": "Kano",
            "Date": "2024-04-15",
            "Days": 30
        },
        {
            "Event Type": "rain",
            "Severity": "Heavy",
            "Location": "Jos",
            "Date": "2024-06-15",
            "Days": 15
        }
    ]
    
    # Validate claims
    for claim in test_claims:
        print("\nValidating Claim:")
        for key, value in claim.items():
            print(f"{key}: {value}")
        
        # Perform validation
        validation_result = validator.analyze_claim(claim)
        
        print("\nValidation Result:")
        print("Status:", validation_result['validation_status'])
        
        if validation_result['current_weather']:
            print("Current Weather:")
            for key, value in validation_result['current_weather'].items():
                print(f"{key}: {value}")
        
        if validation_result.get('historical_analysis'):
            print("\nHistorical Analysis Summary:")
            historical_analysis = validation_result['historical_analysis']
            
            # Print key metrics if available
            if 'rainfall' in historical_analysis:
                print("Rainfall Statistics:")
                print(f"  Mean: {historical_analysis['rainfall']['mean']:.2f}")
                print(f"  Median: {historical_analysis['rainfall']['median']:.2f}")
                print(f"  Max: {historical_analysis['rainfall']['max']:.2f}")
                print(f"  90th Percentile: {historical_analysis['rainfall']['percentile_90']:.2f}")
            
            if 'temperature' in historical_analysis:
                print("Temperature Statistics:")
                print(f"  Mean: {historical_analysis['temperature']['mean']:.2f}")
                print(f"  Median: {historical_analysis['temperature']['median']:.2f}")
                print(f"  Max: {historical_analysis['temperature']['max']:.2f}")
                print(f"  Min: {historical_analysis['temperature']['min']:.2f}")
            
            if 'humidity' in historical_analysis:
                print("Humidity Statistics:")
                print(f"  Mean: {historical_analysis['humidity']['mean']:.2f}")
                print(f"  Max: {historical_analysis['humidity']['max']:.2f}")
            
            if 'rainfall_anomaly' in historical_analysis:
                print("\nRainfall Anomaly:")
                print(f"  Z-Score: {historical_analysis['rainfall_anomaly']['z_score']:.2f}")
                print(f"  Is Extreme: {historical_analysis['rainfall_anomaly']['is_extreme']}")
            
            if 'drought_indicators' in historical_analysis:
                print("\nDrought Indicators:")
                print(f"  Consecutive Dry Days: {historical_analysis['drought_indicators'].get('consecutive_dry_days', 'N/A')}")
                print(f"  Humidity Trend: {historical_analysis['drought_indicators'].get('humidity_trend', 'N/A')}")
        
        # Add historical data details
        historical_data = validator.fetch_historical_weather(
            claim['Location'], 
            claim['Date'], 
            claim['Days']
        )
        
        if not historical_data.empty:
            print("\nHistorical Weather Data:")
            print(historical_data.to_string())

def main():
    print("Weather Claim Processing and Validation Test Script")
    
    # Run claim processing tests
    test_claim_processing()
    
    # Run claim validation tests
    test_claim_validation()

if __name__ == "__main__":
    main()