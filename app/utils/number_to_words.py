def number_to_words(amount: float) -> str:
    """Convert a numeric amount to words (Indian rupee format)."""
    try:
        value = int(round(amount or 0))
    except Exception:
        return "zero rupees"

    if value == 0:
        return "zero rupees"

    ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    scales = [(10000000, "crore"), (100000, "lakh"), (1000, "thousand"), (100, "hundred")]

    def int_to_words(n: int) -> str:
        if n < 20:
            return ones[n]
        if n < 100:
            return tens[n // 10] + (" " + ones[n % 10] if n % 10 else "")
        for scale_value, scale_name in scales:
            if n >= scale_value:
                quotient, remainder = divmod(n, scale_value)
                result = int_to_words(quotient) + " " + scale_name
                if remainder:
                    result += " " + int_to_words(remainder)
                return result
        return ""

    return int_to_words(value) + " rupees"
