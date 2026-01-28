"""
Test script for text enrichment functionality
"""

from nltk_backen import enrich_text_only, summarize_text

print("="*70)
print("NLTK Text Enrichment Test")
print("="*70)

# Test 1: Standalone enrichment
print("\n--- Test 1: Standalone Enrichment ---")
test_text1 = "Create a Python API with database and testing."

result1 = enrich_text_only(test_text1)

print(f"\nOriginal Text:")
print(test_text1)

print(f"\nEnriched Text:")
print(result1['enriched_text'])

print(f"\nReplacements Made: {result1['num_replacements']}")
for replacement in result1['enrichment_replacements']:
    print(f"  - '{replacement['keyword']}' -> '{replacement['replacement'][:60]}...'")

# Test 2: Enrichment with summarization
print("\n\n--- Test 2: Enrichment + Summarization ---")
test_text2 = """
We need to build a microservices architecture using Python and JavaScript.
The system should have a REST API with proper error handling.
Use Docker for deployment and implement CI/CD pipeline.
Add comprehensive testing and documentation.
The database should be PostgreSQL with proper indexing.
"""

result2 = summarize_text(
    text=test_text2,
    summary_length=2,
    enrich_keywords=True,
    correct_spelling=False
)

print(f"\nOriginal Text ({len(test_text2)} chars):")
print(test_text2[:100] + "...")

print(f"\nEnrichments Made: {len(result2['enrichment_replacements'])}")
for replacement in result2['enrichment_replacements'][:3]:
    print(f"  - '{replacement['keyword']}'")

print(f"\nEnriched Text Length: {len(result2['enriched_text'])} chars")
print(f"Summary ({result2['summarization']['num_sentences']} sentences):")
print(result2['summary'])

# Test 3: Custom enrichment rules
print("\n\n--- Test 3: Custom Enrichment Rules ---")
custom_rules = {
    "AI": "Artificial Intelligence with machine learning and deep learning capabilities",
    "model": "trained neural network model with proper validation and testing"
}

test_text3 = "Train an AI model for image recognition."

result3 = enrich_text_only(test_text3, custom_enrichment_rules=custom_rules)

print(f"\nOriginal: {test_text3}")
print(f"Enriched: {result3['enriched_text']}")
print(f"Replacements: {result3['num_replacements']}")

# Test 4: Case-insensitive matching
print("\n\n--- Test 4: Case-Insensitive Matching ---")
test_text4 = "Use PYTHON and React for the frontend."

result4 = enrich_text_only(test_text4)

print(f"\nOriginal: {test_text4}")
print(f"Enriched: {result4['enriched_text'][:100]}...")
print(f"Replacements: {result4['num_replacements']}")

print("\n" + "="*70)
print("All enrichment tests completed!")
print("="*70)
