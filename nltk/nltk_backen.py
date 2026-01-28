# server.py
from mcp.server.fastmcp import FastMCP
import nltk
import spacy
from textblob import TextBlob
from collections import Counter
import string
import re
import traceback
from typing import Optional

# Create an MCP server for Text Summarization
mcp = FastMCP("NLTK Text Summarizer")

# Global variables for models (lazy loading)
nlp = None

def ensure_nltk_data():
    """Ensure required NLTK data is downloaded."""
    required_data = [
        ('tokenizers/punkt_tab', 'punkt_tab'),
        ('corpora/stopwords', 'stopwords'),
        ('taggers/averaged_perceptron_tagger', 'averaged_perceptron_tagger')
    ]
    
    for path, name in required_data:
        try:
            nltk.data.find(path)
        except LookupError:
            print(f"[NLTK] Downloading {name}...")
            nltk.download(name, quiet=True)

def ensure_spacy_model():
    """Ensure spaCy model is loaded."""
    global nlp
    if nlp is None:
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("[spaCy] Model 'en_core_web_sm' not found. Please install it with:")
            print("python -m spacy download en_core_web_sm")
            raise

def correct_spelling_errors(text: str) -> tuple[str, list]:
    """
    Correct spelling errors in text using TextBlob.
    
    Returns:
        tuple: (corrected_text, list of corrections made)
    """
    try:
        blob = TextBlob(text)
        corrected = str(blob.correct())
        
        # Find differences
        corrections = []
        original_words = text.split()
        corrected_words = corrected.split()
        
        for i, (orig, corr) in enumerate(zip(original_words, corrected_words)):
            if orig != corr:
                corrections.append({"original": orig, "corrected": corr, "position": i})
        
        return corrected, corrections
    except Exception as e:
        print(f"[Spelling] Error during correction: {e}")
        return text, []

def preprocess_text(text: str, use_spacy: bool = True) -> dict:
    """
    Preprocess text with tokenization, stopword removal, and lemmatization.
    
    Returns:
        dict: Contains tokens, cleaned_tokens, lemmas, and cleaned_text
    """
    try:
        ensure_nltk_data()
        
        # Tokenize sentences and words
        sentences = nltk.sent_tokenize(text)
        words = nltk.word_tokenize(text)
        
        # Get stopwords
        stop_words = set(nltk.corpus.stopwords.words('english'))
        
        # Remove punctuation and stopwords, convert to lowercase
        cleaned_tokens = [
            word.lower() for word in words 
            if word.lower() not in stop_words and word not in string.punctuation
        ]
        
        # Lemmatization with spaCy (optional)
        lemmas = []
        if use_spacy:
            ensure_spacy_model()
            doc = nlp(text)
            lemmas = [
                token.lemma_.lower() for token in doc 
                if not token.is_stop and not token.is_punct
            ]
        
        return {
            "sentences": sentences,
            "tokens": words,
            "cleaned_tokens": cleaned_tokens,
            "lemmas": lemmas if use_spacy else cleaned_tokens,
            "num_sentences": len(sentences),
            "num_words": len(words)
        }
    except Exception as e:
        print(f"[Preprocessing] Error: {e}")
        traceback.print_exc()
        return {
            "sentences": [text],
            "tokens": text.split(),
            "cleaned_tokens": text.split(),
            "lemmas": [],
            "num_sentences": 1,
            "num_words": len(text.split())
        }

def summarize_text_extractive(text: str, preprocessed: dict, num_sentences: int = 3) -> dict:
    """
    Perform extractive summarization using sentence scoring.
    
    Args:
        text: Original text
        preprocessed: Preprocessed text data
        num_sentences: Number of sentences to include in summary
    
    Returns:
        dict: Contains summary, sentence_scores, and metadata
    """
    try:
        sentences = preprocessed["sentences"]
        
        # If text is shorter than requested summary, return all
        if len(sentences) <= num_sentences:
            return {
                "summary": text,
                "num_sentences": len(sentences),
                "sentence_scores": {},
                "compression_ratio": 1.0
            }
        
        # Calculate word frequencies from cleaned tokens
        word_freq = Counter(preprocessed["cleaned_tokens"])
        
        # Normalize frequencies
        max_freq = max(word_freq.values()) if word_freq else 1
        for word in word_freq:
            word_freq[word] = word_freq[word] / max_freq
        
        # Score sentences based on word frequencies
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            sentence_words = nltk.word_tokenize(sentence.lower())
            score = 0
            word_count = 0
            
            for word in sentence_words:
                if word in word_freq:
                    score += word_freq[word]
                    word_count += 1
            
            # Average score per word in sentence
            if word_count > 0:
                sentence_scores[i] = score / word_count
            else:
                sentence_scores[i] = 0
        
        # Get top N sentences by score
        top_sentence_indices = sorted(
            sentence_scores.keys(), 
            key=lambda x: sentence_scores[x], 
            reverse=True
        )[:num_sentences]
        
        # Sort by original order to maintain coherence
        top_sentence_indices.sort()
        
        # Build summary
        summary_sentences = [sentences[i] for i in top_sentence_indices]
        summary = " ".join(summary_sentences)
        
        compression_ratio = len(summary_sentences) / len(sentences)
        
        return {
            "summary": summary,
            "num_sentences": len(summary_sentences),
            "sentence_scores": {i: sentence_scores[i] for i in top_sentence_indices},
            "compression_ratio": compression_ratio
        }
    except Exception as e:
        print(f"[Summarization] Error: {e}")
        traceback.print_exc()
        return {
            "summary": text,
            "num_sentences": preprocessed["num_sentences"],
            "sentence_scores": {},
            "compression_ratio": 1.0
        }

@mcp.tool()
def summarize_text(
    text: str, 
    summary_length: int = 3, 
    correct_spelling: bool = True,
    use_spacy: bool = True
) -> dict:
    """
    Summarize text with spelling correction and preprocessing.
    
    This tool performs the following steps:
    1. Spelling correction (optional)
    2. Text preprocessing (tokenization, stopword removal, lemmatization)
    3. Extractive summarization using sentence scoring
    
    Args:
        text: Input text to summarize
        summary_length: Number of sentences in the summary (default: 3)
        correct_spelling: Whether to correct spelling errors (default: True)
        use_spacy: Whether to use spaCy for lemmatization (default: True)
    
    Returns:
        dict: Contains:
            - original_text: Original input text
            - corrected_text: Text after spelling correction
            - spelling_corrections: List of spelling corrections made
            - summary: The generated summary
            - preprocessing: Preprocessing metadata
            - summarization: Summarization metadata
            - error: Error message if any
    """
    try:
        result = {
            "original_text": text,
            "corrected_text": text,
            "spelling_corrections": [],
            "summary": "",
            "preprocessing": {},
            "summarization": {},
            "error": None
        }
        
        # Step 1: Spelling Correction
        if correct_spelling:
            print("[NLTK Summarizer] Correcting spelling...")
            corrected_text, corrections = correct_spelling_errors(text)
            result["corrected_text"] = corrected_text
            result["spelling_corrections"] = corrections
            text_to_process = corrected_text
        else:
            text_to_process = text
        
        # Step 2: Preprocessing
        print("[NLTK Summarizer] Preprocessing text...")
        preprocessed = preprocess_text(text_to_process, use_spacy=use_spacy)
        result["preprocessing"] = {
            "num_sentences": preprocessed["num_sentences"],
            "num_words": preprocessed["num_words"],
            "num_unique_tokens": len(set(preprocessed["cleaned_tokens"]))
        }
        
        # Step 3: Summarization
        print("[NLTK Summarizer] Generating summary...")
        summary_result = summarize_text_extractive(
            text_to_process, 
            preprocessed, 
            num_sentences=summary_length
        )
        result["summary"] = summary_result["summary"]
        result["summarization"] = {
            "num_sentences": summary_result["num_sentences"],
            "compression_ratio": summary_result["compression_ratio"],
            "sentence_scores": summary_result["sentence_scores"]
        }
        
        print(f"[NLTK Summarizer] Summary generated successfully ({summary_result['num_sentences']} sentences)")
        return result
        
    except Exception as e:
        error_msg = f"Error summarizing text: {str(e)}"
        print(f"[NLTK Summarizer] {error_msg}")
        traceback.print_exc()
        return {
            "original_text": text,
            "corrected_text": text,
            "spelling_corrections": [],
            "summary": "",
            "preprocessing": {},
            "summarization": {},
            "error": error_msg
        }

# Run the server
if __name__ == "__main__":
    import sys
    
    print("="*70)
    print("NLTK Text Summarizer MCP Server")
    print("="*70)
    print("Features:")
    print("  - Spelling correction with TextBlob")
    print("  - Text preprocessing with NLTK")
    print("  - Lemmatization with spaCy")
    print("  - Extractive summarization")
    print("="*70)
    print("\nServer is starting...")
    print("Press Ctrl+C to stop the server\n")
    
    # Run the server with HTTP transport
    mcp.run(transport="streamable-http")
