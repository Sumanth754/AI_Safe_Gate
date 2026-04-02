from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

class PIIScrubber:
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        
        # Add custom regex for phone numbers to be more robust
        phone_pattern = Pattern(name="phone_number_pattern", regex=r"(\d{3}-\d{4}|\d{3}-\d{3}-\d{4}|\(\d{3}\) \d{3}-\d{4})", score=0.5)
        phone_recognizer = PatternRecognizer(supported_entity="PHONE_NUMBER", patterns=[phone_pattern])
        
        # Add custom regex for API Keys/Secrets
        secret_pattern = Pattern(name="secret_key_pattern", regex=r"(AKIA[0-9A-Z]{16}|[a-zA-Z0-9]{32,})", score=0.6)
        secret_recognizer = PatternRecognizer(supported_entity="SECRET_KEY", patterns=[secret_pattern])
        
        # Add custom regex for SSN
        ssn_pattern = Pattern(name="ssn_pattern", regex=r"(\d{3}-\d{2}-\d{4})", score=0.8)
        ssn_recognizer = PatternRecognizer(supported_entity="SSN", patterns=[ssn_pattern])
        
        self.analyzer.registry.add_recognizer(phone_recognizer)
        self.analyzer.registry.add_recognizer(secret_recognizer)
        self.analyzer.registry.add_recognizer(ssn_recognizer)
        
        self.anonymizer = AnonymizerEngine()

    def scrub(self, text: str):
        # Analyze the text for PII
        results = self.analyzer.analyze(text=text, language='en', 
                                        entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION", "URL", "IP_ADDRESS", "SECRET_KEY", "SSN"])
        
        # Define operators for anonymization
        operators = {
            "PERSON": OperatorConfig("replace", {"new_value": "<PERSON>"}),
            "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),
            "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<PHONE>"}),
            "LOCATION": OperatorConfig("replace", {"new_value": "<LOCATION>"}),
            "URL": OperatorConfig("replace", {"new_value": "<URL>"}),
            "IP_ADDRESS": OperatorConfig("replace", {"new_value": "<IP>"}),
            "SECRET_KEY": OperatorConfig("replace", {"new_value": "<SECRET_KEY>"}),
            "SSN": OperatorConfig("replace", {"new_value": "<SSN>"}),
        }

        # Anonymize the text
        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators
        )

        return anonymized_result.text, len(results)

if __name__ == "__main__":
    scrubber = PIIScrubber()
    test_text = "My name is John Doe and my email is john.doe@example.com. I live in New York."
    scrubbed_text, count = scrubber.scrub(test_text)
    print(f"Original: {test_text}")
    print(f"Scrubbed: {scrubbed_text}")
    print(f"Leaks found: {count}")
