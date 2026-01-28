from decimal import Decimal


def format_monetary_decimal(value: Decimal | None) -> str | None:
    """
    Format a Decimal monetary value to string with minimum 2 decimal places.

    If the value has more than 2 significant decimal places, all are displayed.
    Otherwise, exactly 2 decimal places are shown.

    Args:
        value: Decimal value or None

    Returns:
        Formatted string or None if input is None
    """
    if value is None:
        return None

    # Handle special values
    if value.is_nan():
        return "NaN"
    if value.is_infinite():
        return "Infinity" if value > 0 else "-Infinity"

    # Convert to string and strip trailing zeros/decimal point
    value_str = format(value, "f").rstrip("0").rstrip(".")

    # Check if there's a decimal point
    if "." not in value_str:
        # No decimal point means it's a whole number
        return f"{value:.2f}"

    # Get the number of decimal places after normalization
    decimal_places = len(value_str.split(".")[1])

    # If 2 or fewer decimal places, format with exactly 2
    if decimal_places <= 2:
        return f"{value:.2f}"

    # Otherwise, preserve all significant decimal places
    return str(value_str)


# Test cases
if __name__ == "__main__":
    test_cases = [
        # (Decimal("0"), "0.00"),
        (Decimal("0.00000000"), "0.00"),
        (Decimal("5.100000"), "5.10"),
        (Decimal("5.1"), "5.10"),
        (Decimal("4.97"), "4.97"),
        (Decimal("5.6543547"), "5.6543547"),
        (Decimal("10"), "10.00"),
        (Decimal("0.1"), "0.10"),
        (Decimal("0.01"), "0.01"),
        (Decimal("123.456789"), "123.456789"),
        (Decimal("1E-5"), "0.00001"),  # Scientific notation
        (None, None),
        (Decimal("0.0"), "0.00"),
        (Decimal("99.9"), "99.90"),
        (Decimal("NaN"), "NaN"),
        (Decimal("Infinity"), "Infinity"),
        (Decimal("-Infinity"), "-Infinity"),
        (Decimal("200000000.00000000"), "200000000.00"),
        (Decimal("0.00000001"), "0.00000001"),
    ]

    print("Testing format_monetary_decimal:")
    for input_val, expected in test_cases:
        result = format_monetary_decimal(input_val)
        status = "✓" if result == expected else "✗"
        print(f"{status} {input_val} -> {result} (expected: {expected})")
