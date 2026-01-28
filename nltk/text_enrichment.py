# text_enrichment.py
"""
Text enrichment module for expanding keywords with detailed descriptions.
"""

import re
import traceback

# Default enrichment rules for text expansion
DEFAULT_ENRICHMENT_RULES = {
    # Programming Languages
    "python": "Python 3.11+ using only standard libraries (os, sys, json, pathlib, typing, dataclasses)",
    "javascript": "JavaScript ES6+ with modern syntax (async/await, arrow functions, destructuring)",
    "typescript": "TypeScript 5.0+ with strict type checking enabled",
    "java": "Java 17 LTS with modern features (records, sealed classes, pattern matching)",
    "c++": "C++20 with modern features (concepts, ranges, coroutines)",
    "rust": "Rust 1.70+ with safe, idiomatic code following Rust best practices",
    "go": "Go 1.21+ with idiomatic Go patterns and error handling",
    
    # Frameworks & Libraries
    "react": "React 18+ with functional components and hooks (useState, useEffect, useContext)",
    "vue": "Vue 3 with Composition API and TypeScript support",
    "django": "Django 4.2 LTS with proper ORM usage and security best practices",
    "flask": "Flask 3.0+ with blueprints and proper error handling",
    "fastapi": "FastAPI with async/await, Pydantic models, and automatic OpenAPI documentation",
    "express": "Express.js 4.x with middleware pattern and proper error handling",
    
    # Databases
    "database": "SQLite database with proper indexing, transactions, and foreign key constraints",
    "sql": "SQL with proper indexing, parameterized queries to prevent SQL injection",
    "postgresql": "PostgreSQL 15+ with JSONB support, proper indexing, and connection pooling",
    "mongodb": "MongoDB 6.0+ with proper schema validation and indexing strategies",
    "redis": "Redis 7.0+ for caching and session management with proper key expiration",
    
    # Development Practices
    "api": "RESTful API following OpenAPI 3.0 specification with proper versioning and error handling",
    "rest api": "RESTful API with proper HTTP methods (GET, POST, PUT, DELETE), status codes, and JSON responses",
    "testing": "comprehensive unit tests with pytest/jest achieving >80% code coverage",
    "documentation": "clear inline documentation with docstrings/JSDoc and README with usage examples",
    "error handling": "robust error handling with try-catch blocks, proper logging, and user-friendly error messages",
    
    # Architecture & Patterns
    "microservices": "microservices architecture with proper service boundaries, API gateways, and inter-service communication",
    "mvc": "Model-View-Controller pattern with clear separation of concerns",
    "clean code": "clean, maintainable code following SOLID principles and DRY (Don't Repeat Yourself)",
    
    # Tools & Technologies
    "docker": "Docker containerization with multi-stage builds and proper layer caching",
    "kubernetes": "Kubernetes orchestration with proper resource limits, health checks, and rolling updates",
    "git": "Git version control with meaningful commit messages and feature branch workflow",
    "ci/cd": "CI/CD pipeline with automated testing, linting, and deployment stages",
}

def enrich_text(text: str, enrichment_rules: dict = None) -> tuple[str, list]:
    """
    Enrich text by replacing keywords with detailed descriptions.
    
    Args:
        text: Input text to enrich
        enrichment_rules: Dictionary mapping keywords to detailed descriptions.
                         If None, uses DEFAULT_ENRICHMENT_RULES.
    
    Returns:
        tuple: (enriched_text, list of replacements made)
    """
    try:
        if enrichment_rules is None:
            enrichment_rules = DEFAULT_ENRICHMENT_RULES
        
        enriched_text = text
        replacements = []
        
        # Sort rules by length (longest first) to handle multi-word phrases first
        sorted_rules = sorted(enrichment_rules.items(), key=lambda x: len(x[0]), reverse=True)
        
        for keyword, replacement in sorted_rules:
            # Use word boundaries to avoid partial matches
            # Case-insensitive matching
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = list(re.finditer(pattern, enriched_text, re.IGNORECASE))
            
            if matches:
                # Replace from end to start to preserve positions
                for match in reversed(matches):
                    start, end = match.span()
                    original = enriched_text[start:end]
                    enriched_text = enriched_text[:start] + replacement + enriched_text[end:]
                    
                    replacements.append({
                        "keyword": original,
                        "replacement": replacement,
                        "position": start
                    })
        
        return enriched_text, replacements
    except Exception as e:
        print(f"[Enrichment] Error during enrichment: {e}")
        traceback.print_exc()
        return text, []
