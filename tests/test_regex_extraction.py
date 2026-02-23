import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.brain.regex_extractor import RegexExtractor

def test_regex_extraction():
    extractor = RegexExtractor()
    
    test_cases = [
        ("خونه ۵ تا ۹ میلیارد تومانی میخوام", (5_000_000_000, 9_000_000_000)),
        ("بودجم بین ۸۰۰ تا ۹۰۰ میلیون هست", (800_000_000, 900_000_000)),
        ("حداقل ۲ میلیارد بودجه دارم", (2_000_000_000, None)),
        ("زیر ۳ میلیارد باشه", (None, 3_000_000_000)),
        ("یه مورد ۶ میلیاردی", (None, 6_000_000_000)),
    ]
    
    for text, expected in test_cases:
        extracted = extractor.extract_all(text)
        b_min = extracted.get('budget_min')
        b_max = extracted.get('budget_max')
        print(f"Text: '{text}' -> Extracted: Min={b_min}, Max={b_max}")
        assert (b_min, b_max) == expected, f"Failed for '{text}'. Expected {expected}, got {(b_min, b_max)}"

    print("\n✅ Regex extraction test PASSED!")

if __name__ == "__main__":
    test_regex_extraction()
