# Now import the module
from claim_processing import process_claims_from_text


def test_claim_processing():
    input_claim = "Heavy rains yesterday destroyed crops in Lagos."
    input_claims = [
        "Heavy rains today destroyed crops in Lagos.",
        "Mild drought this month has severely impacted farming in Kano.",
        "Severe storm warnings were issued last month in Abuja.",
        "Light rainfall next month in Abuja with no major impact.",
        "Intense wildfire expected tomorrow in rural areas.",
        "mild drought in Kano today"
    ]
    processed_single_claim = process_claims_from_text(input_claim)
    print("Processed Single Claim:")
    print(processed_single_claim)

    processed_multiple_claims = process_claims_from_text(input_claims)
    print("\nProcessed Multiple Claims:")
    for claim in processed_multiple_claims:
        print(claim)


if __name__ == "__main__":
    test_claim_processing()
