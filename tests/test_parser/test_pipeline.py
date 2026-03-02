from parser.pipeline import Deduplicator, Extractor, Normalizer, Validator


def test_pipeline_components(sample_parsed_payload: dict) -> None:
    extractor = Extractor()
    validator = Validator()
    normalizer = Normalizer()
    deduplicator = Deduplicator()

    place = extractor.from_payload(sample_parsed_payload)
    assert validator.validate(place)

    normalized = normalizer.normalize(place)
    assert normalized.name == "Test Cafe"

    deduped = deduplicator.deduplicate([normalized, normalized])
    assert len(deduped) == 1
