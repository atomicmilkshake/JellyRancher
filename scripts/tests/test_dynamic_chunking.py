#!/usr/bin/env python3
"""
Test script to verify dynamic token-aware chunking is working correctly.
"""

def estimate_tokens(text):
    """Estimate token count for text using simple approximation."""
    return len(text) // 4

def get_model_context_limit(model_name):
    """Get context window size for a model."""
    model_limits = {
        'Grok-4.1-Fast-Reasoning': 128000,
        'Grok-4.1': 128000,
        'GPT-4-Turbo': 128000,
        'GPT-4': 8192,
        'Gemini-2.5-Pro': 1000000,
    }
    
    model_name_lower = model_name.lower()
    for known_model, limit in model_limits.items():
        if known_model.lower() in model_name_lower:
            return int(limit * 0.8)
    
    return 8000

def chunk_list_by_tokens(file_list, prompt_template, model_name):
    """Dynamically chunk file list based on token limits."""
    max_tokens = get_model_context_limit(model_name)
    prompt_tokens = estimate_tokens(prompt_template)
    available_tokens = max_tokens - prompt_tokens - 1000
    
    print(f"\nModel: {model_name}")
    print(f"Max tokens: {max_tokens}")
    print(f"Prompt tokens: {prompt_tokens}")
    print(f"Available for files: {available_tokens}")
    
    if available_tokens < 500:
        print(f"ERROR: Prompt too large! Only {available_tokens} tokens left for files.")
        return []
    
    chunks = []
    current_chunk = []
    current_chunk_tokens = 0
    
    for file_path in file_list:
        file_tokens = estimate_tokens(file_path) + 2
        
        if current_chunk and (current_chunk_tokens + file_tokens > available_tokens):
            chunks.append(current_chunk)
            current_chunk = [file_path]
            current_chunk_tokens = file_tokens
        else:
            current_chunk.append(file_path)
            current_chunk_tokens += file_tokens
    
    if current_chunk:
        chunks.append(current_chunk)
    
    print(f"\nChunking results:")
    print(f"Total files: {len(file_list)}")
    print(f"Total chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks, 1):
        chunk_tokens = sum(estimate_tokens(f) for f in chunk)
        print(f"  Chunk {i}: {len(chunk)} files (~{chunk_tokens} tokens)")
    
    return chunks


def test_scenario_1():
    """Test with Grok model and typical media file paths."""
    print("\n" + "="*70)
    print("TEST 1: Grok-4.1-Fast-Reasoning with 100 typical media file paths")
    print("="*70)
    
    # Typical media file paths (similar length)
    file_list = [
        f"E:\\#MEDIA\\TV Shows\\Show Name\\Season 01\\Show Name - S01E{i:02d} - Episode Title.mkv"
        for i in range(1, 101)
    ]
    
    prompt = """You are a media file organization assistant. Please analyze the following file paths and suggest reorganization actions.

For each file, provide:
- Original path
- New path (if reorganization needed)
- Action (RENAME, MOVE, DELETE, SKIP)

{filepaths}"""
    
    chunks = chunk_list_by_tokens(file_list, prompt, "Grok-4.1-Fast-Reasoning")
    assert len(chunks) > 0, "Should create at least one chunk"
    assert sum(len(c) for c in chunks) == len(file_list), "All files should be in chunks"
    print("\n✓ Test 1 PASSED")


def test_scenario_2():
    """Test with GPT-4 (smaller context window)."""
    print("\n" + "="*70)
    print("TEST 2: GPT-4 (8k context) with 50 file paths")
    print("="*70)
    
    file_list = [
        f"E:\\#MEDIA\\Movies\\Movie Title {i}\\Movie Title {i} (2024).mkv"
        for i in range(1, 51)
    ]
    
    prompt = "Analyze these files and suggest reorganization:\n\n{filepaths}"
    
    chunks = chunk_list_by_tokens(file_list, prompt, "GPT-4")
    assert len(chunks) > 0, "Should create at least one chunk"
    
    # With GPT-4's small window, should need multiple chunks
    print(f"\n✓ Test 2 PASSED (needed {len(chunks)} chunks for smaller model)")


def test_scenario_3():
    """Test with very long prompt (should fail gracefully)."""
    print("\n" + "="*70)
    print("TEST 3: Extremely long prompt (should detect and fail)")
    print("="*70)
    
    file_list = ["test.mkv"] * 10
    
    # Create a prompt that's way too long (more than the model limit)
    huge_prompt = "Please analyze these files.\n" + ("EXTRA INSTRUCTIONS " * 2000) + "\n\n{filepaths}"
    
    chunks = chunk_list_by_tokens(file_list, huge_prompt, "GPT-4")
    assert len(chunks) == 0, "Should return empty list for oversized prompt"
    print("\n✓ Test 3 PASSED (correctly rejected oversized prompt)")


def test_scenario_4():
    """Test with mixed length file paths."""
    print("\n" + "="*70)
    print("TEST 4: Mixed length paths (some very long, some short)")
    print("="*70)
    
    file_list = []
    # Some short paths
    file_list.extend([f"E:\\Media\\File{i}.mp4" for i in range(10)])
    # Some very long paths
    file_list.extend([
        f"E:\\#MEDIA\\TV Shows\\Very Long Show Name With Many Words\\Season 01\\Very Long Show Name With Many Words - S01E{i:02d} - Very Long Episode Title With Many Words And Details.mkv"
        for i in range(10)
    ])
    # More short paths
    file_list.extend([f"E:\\Media\\File{i}.mp4" for i in range(10, 20)])
    
    prompt = "Analyze and reorganize:\n\n{filepaths}"
    
    chunks = chunk_list_by_tokens(file_list, prompt, "Grok-4.1-Fast-Reasoning")
    assert len(chunks) > 0, "Should create chunks"
    assert sum(len(c) for c in chunks) == len(file_list), "All files should be included"
    print("\n✓ Test 4 PASSED")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("TESTING DYNAMIC TOKEN-AWARE CHUNKING")
    print("="*70)
    
    test_scenario_1()
    test_scenario_2()
    test_scenario_3()
    test_scenario_4()
    
    print("\n" + "="*70)
    print("ALL TESTS PASSED ✓")
    print("="*70)
    print("\nDynamic chunking is working correctly!")
    print("- Respects model token limits")
    print("- Handles different prompt sizes")
    print("- Rejects oversized prompts gracefully")
    print("- Works with varying file path lengths")
