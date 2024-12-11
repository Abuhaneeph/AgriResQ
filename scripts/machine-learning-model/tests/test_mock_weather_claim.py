import numpy as np


class MockWeatherClaimValidator:
    """
    Mock validator for testing weather claims without actual API calls.
    """
    
    def __init__(self):
        self.mock_historical_data = {
            "rainfall": np.random.normal(loc=50, scale=15, size=100),  # Mock rainfall data in mm
            "temperature": np.random.normal(loc=25, scale=5, size=100),  # Mock temperature in °C
            "humidity": np.random.normal(loc=60, scale=10, size=100),  # Mock humidity in percentage
        }

    def calculate_z_score(self, value, data):
        """
        Calculate the z-score of a value given a dataset.
        """
        mean = np.mean(data)
        std = np.std(data)
        return (value - mean) / std

    def analyze_claim(self, claim):
        """
        Validate and analyze a claim using mock historical data.
        """
        event_type = claim["Event Type"]
        severity = claim["Severity"]

        # Choose mock data based on event type
        if event_type in ["rain", "flood"]:
            historical_data = self.mock_historical_data["rainfall"]
            observed_value = 80 if severity == "Heavy" else 20  # Mock observed values
        elif event_type in ["drought"]:
            historical_data = self.mock_historical_data["humidity"]
            observed_value = 20 if severity == "Severe" else 50
        else:
            observed_value = None
            historical_data = None

        # Calculate z-score and determine if it's extreme
        if observed_value is not None and historical_data is not None:
            z_score = self.calculate_z_score(observed_value, historical_data)
            is_extreme = abs(z_score) > 2
        else:
            z_score = None
            is_extreme = None

        return {
            "validation_status": "Valid" if historical_data is not None else "Invalid",
            "z_score": z_score,
            "is_extreme": is_extreme,
            "historical_data_summary": {
                "mean": np.mean(historical_data) if historical_data is not None else None,
                "std": np.std(historical_data) if historical_data is not None else None,
                "data": historical_data if historical_data is not None else None,
            } if historical_data is not None else None
        }


def test_mock_claim_validation():
    """
    Test the claim validation functionality with mock data.
    """
    print("\n--- Testing Mock Claim Validation ---")
    
    # Initialize mock validator
    validator = MockWeatherClaimValidator()
    
    # Mock processed claims
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
        print("Z-Score:", f"{validation_result['z_score']:.2f}" if validation_result['z_score'] is not None else "N/A")
        print("Is Extreme:", validation_result['is_extreme'])

        if validation_result.get("historical_data_summary"):
            print("\nHistorical Data Summary:")
            summary = validation_result["historical_data_summary"]
            print(f"  Mean: {summary['mean']:.2f}")
            print(f"  Std Dev: {summary['std']:.2f}")
            print(f"  Historical Data (first 10): {summary['data'][:10]}")  # Show first 10 data points


if __name__ == "__main__":
    test_mock_claim_validation()
