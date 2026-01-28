# Script to add enrich_text_only endpoint to nltk_backen.py

endpoint_code = '''
@mcp.tool()
def enrich_text_only(
    text: str,
    custom_enrichment_rules: dict = None
) -> dict:
    """
    Enrich text by replacing keywords with detailed descriptions.
    
    Useful for preprocessing text before sending to LLMs.
    
    Args:
        text: Input text to enrich
        custom_enrichment_rules: Custom enrichment rules dict (optional)
    
    Returns:
        dict: enriched_text, enrichment_replacements, num_replacements
    """
    try:
        enriched_text, replacements = enrich_text(text, custom_enrichment_rules)
        print(f"[NLTK Enrichment] Enriched text with {len(replacements)} replacements")
        
        return {
            "original_text": text,
            "enriched_text": enriched_text,
            "enrichment_replacements": replacements,
            "num_replacements": len(replacements),
            "error": None
        }
    except Exception as e:
        error_msg = f"Error enriching text: {str(e)}"
        print(f"[NLTK Enrichment] {error_msg}")
        traceback.print_exc()
        return {
            "original_text": text,
            "enriched_text": text,
            "enrichment_replacements": [],
            "num_replacements": 0,
            "error": error_msg
        }

'''

with open('nltk_backen.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the position to insert (before "# Run the server")
insert_marker = "# Run the server"
insert_pos = content.find(insert_marker)

if insert_pos != -1:
    new_content = content[:insert_pos] + endpoint_code + content[insert_pos:]
    
    # Also update the features list
    new_content = new_content.replace(
        '    print("Features:")\n    print("  - Spelling correction with TextBlob")',
        '    print("Features:")\n    print("  - Keyword enrichment for LLM preprocessing")\n    print("  - Spelling correction with TextBlob")'
    )
    
    # Update error response to include enrichment fields
    old_error = '''        return {
            "original_text": text,
            "corrected_text": text,
            "spelling_corrections": [],
            "summary": "",
            "preprocessing": {},
            "summarization": {},
            "error": error_msg
        }'''
    
    new_error = '''        return {
            "original_text": text,
            "enriched_text": text,
            "enrichment_replacements": [],
            "corrected_text": text,
            "spelling_corrections": [],
            "summary": "",
            "preprocessing": {},
            "summarization": {},
            "error": error_msg
        }'''
    
    new_content = new_content.replace(old_error, new_error)
    
    with open('nltk_backen.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Successfully added enrich_text_only endpoint!")
else:
    print("Could not find insertion point")
