"""
Test script for NLTK Text Summarization endpoint
"""

from nltk_backen import summarize_text

# Test text with spelling errors
test_text = """
Artifical inteligence is transformng the way we live and work. Machine lerning algorithms 
can now proces vast amounts of data and make predctions with remarkble accuracy. Deep 
learning, a subset of machine learning, uses neural networks with multiple layers to learn 
complex patterns in data. These tecnologies are being applied in various fields such as 
healthcare, finance, transportation, and entertainment. Self-driving cars use computer vision 
and sensor fusion to navigate roads safely. In healthcare, AI systems can analyze medical 
images to detect diseases earlier than human doctors. Natural language processing enables 
machines to understand and generate human language, powering virtual assistants and 
translation services. As AI continues to advance, it raises important questions about ethics, 
privacy, and the future of work. Researchers and policymakers are working to ensure that 
AI development benefits society while minimizing potential risks.
"""

print("="*70)
print("NLTK Text Summarization Test")
print("="*70)

# Test 1: Full pipeline with spelling correction
print("\n--- Test 1: Full Pipeline (with spelling correction) ---")
result1 = summarize_text(
    text=test_text,
    summary_length=3,
    correct_spelling=True,
    use_spacy=True
)

print(f"\nOriginal Text Length: {len(result1['original_text'])} characters")
print(f"Spelling Corrections Made: {len(result1['spelling_corrections'])}")
if result1['spelling_corrections']:
    print("Corrections:")
    for corr in result1['spelling_corrections'][:5]:  # Show first 5
        print(f"  - '{corr['original']}' -> '{corr['corrected']}'")

print(f"\nPreprocessing Stats:")
print(f"  - Sentences: {result1['preprocessing']['num_sentences']}")
print(f"  - Words: {result1['preprocessing']['num_words']}")
print(f"  - Unique Tokens: {result1['preprocessing']['num_unique_tokens']}")

print(f"\nSummarization Stats:")
print(f"  - Summary Sentences: {result1['summarization']['num_sentences']}")
print(f"  - Compression Ratio: {result1['summarization']['compression_ratio']:.2%}")

print(f"\nSummary:")
print(result1['summary'])

# Test 2: Without spelling correction
print("\n\n--- Test 2: Without Spelling Correction ---")
result2 = summarize_text(
    text=test_text,
    summary_length=2,
    correct_spelling=False,
    use_spacy=False
)

print(f"Summary Sentences: {result2['summarization']['num_sentences']}")
print(f"Summary:")
print(result2['summary'])

# Test 3: Short text
print("\n\n--- Test 3: Short Text ---")
short_text = "This is a short text. It has only two sentences."
result3 = summarize_text(
    text=short_text,
    summary_length=5,
    correct_spelling=True
)

print(f"Summary:")
print(result3['summary'])
print(f"Compression Ratio: {result3['summarization']['compression_ratio']:.2%}")

print("\n" + "="*70)
print("All tests completed!")
print("="*70)
