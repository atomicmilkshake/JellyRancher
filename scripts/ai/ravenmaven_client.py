#!/usr/bin/env python3
"""
Modular Poe.com API Client

A reusable client for interacting with Poe.com's OpenAI-compatible API.
Supports dynamic model selection and batch file processing with custom prompts.

Features:
- Dynamic model list retrieval from Poe API (with caching)
- Batch file processing with custom prompts
- Progress tracking and error handling
- Configurable via environment variables or parameters
"""

import os
import sys
import json
from typing import List, Dict, Optional, Callable
from pathlib import Path
from datetime import datetime, timedelta
import requests
import logging


class PoeClient:
    """Client for interacting with Poe.com API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout: int = 1800,  # Increased to 30 minutes (1800 seconds)
        cache_dir: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Poe client.
        
        Args:
            api_key: Poe API key (defaults to OPENAI_API_KEY env var)
            base_url: API base URL (defaults to OPENAI_BASE_URL env var)
            default_model: Default model to use (defaults to OPENAI_MODEL env var)
            timeout: Request timeout in seconds (default: 1800/30 minutes, matching Poe API standards)
            cache_dir: Directory for caching model lists (defaults to .cache/)
            logger: Logger instance for comprehensive API logging
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        # Normalize base URL: prefer bare domain (no /v1) so we can consistently build endpoints
        provided_base = base_url or os.getenv('OPENAI_BASE_URL', 'https://api.poe.com')
        provided_base = provided_base.rstrip('/')
        # If user supplied a URL that already includes /v1, strip it so we can append /v1 safely later
        if provided_base.endswith('/v1'):
            provided_base = provided_base[:-3]
        self.base_url = provided_base
        self.default_model = default_model or os.getenv('OPENAI_MODEL', 'Claude-Sonnet-4.5')
        self.timeout = timeout
        self.logger = logger or logging.getLogger(__name__)
        
        # Set up cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(os.getcwd()) / '.cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / 'models.json'
        self.cache_ttl = timedelta(hours=24)
        
        # Set up LLM I/O log directory
        self.llm_io_dir = Path(os.getcwd()) / 'LLM_io_log'
        self.llm_io_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.api_key:
            raise ValueError("API key required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.logger.info(f"PoeClient initialized with base_url={self.base_url}, default_model={self.default_model}")
    
    def get_available_models(self, use_cache: bool = True) -> List[str]:
        """
        Retrieve list of available models from Poe API.
        Uses caching to avoid repeated API calls (24 hour TTL).
        
        Args:
            use_cache: Whether to use cached results if available
            
        Returns:
            List of model names
        """
        # Try cache first if enabled
        if use_cache:
            try:
                if self.cache_file.exists():
                    raw = json.loads(self.cache_file.read_text(encoding='utf-8'))
                    ts = datetime.fromisoformat(raw.get('ts')) if raw.get('ts') else None
                    if ts and (datetime.now() - ts) < self.cache_ttl and raw.get('models'):
                        return raw.get('models')
            except Exception:
                pass  # Cache read failed, continue to network fetch
        
        # Fetch from API
        candidates = []
        headers = {'Authorization': f'Bearer {self.api_key}'}
        
        # Try multiple endpoint patterns
        endpoints = [
            f"{self.base_url}/v1/models",
            f"{self.base_url}/models",
            f"{self.base_url}/v1/engines",
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, headers=headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    
                    # OpenAI-style: {'data':[{'id': 'gpt-4'}...]}
                    if isinstance(data, dict):
                        if 'data' in data and isinstance(data['data'], list):
                            for item in data['data']:
                                if isinstance(item, dict) and 'id' in item:
                                    candidates.append(item['id'])
                        # Some providers return {'models': {...}}
                        elif 'models' in data and isinstance(data['models'], dict):
                            candidates.extend(list(data['models'].keys()))
                    elif isinstance(data, list):
                        # Fallback: list of ids
                        for item in data:
                            if isinstance(item, dict) and 'id' in item:
                                candidates.append(item['id'])
                    
                    # Stop early if we found candidates
                    if candidates:
                        # Write to cache
                        try:
                            cache_data = {
                                'ts': datetime.now().isoformat(),
                                'models': candidates
                            }
                            self.cache_file.write_text(
                                json.dumps(cache_data, ensure_ascii=False),
                                encoding='utf-8'
                            )
                        except Exception:
                            pass  # Cache write failed, but we have the data
                        return candidates
            except Exception:
                continue  # Try next endpoint
        
        # If API fetch failed, try to return cached models as a fallback (even when use_cache=False)
        try:
            if self.cache_file.exists():
                raw = json.loads(self.cache_file.read_text(encoding='utf-8'))
                if raw.get('models'):
                    return raw.get('models')
        except Exception:
            pass

        # Fallback to default models if API fetch and cache failed
        default_models = [
            'Claude-Sonnet-4.5',
            'gpt-4o-mini',
            'Claude-Instant-1',
            'gpt-4o-reasoning',
            'Claude-2',
            'GPT-4o',
            'GPT-4-Turbo',
            'GPT-3.5-Turbo',
            'Gemini-Pro',
            'Llama-3.1-405B'
        ]
        return default_models
    
    def send_message(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        logger: Optional[object] = None
    ) -> str:
        """
        Send a message to Poe API and get response.
        
        Args:
            prompt: The prompt/message to send
            model: Model to use (defaults to default_model)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)
            logger: Optional logger for diagnostic output
            
        Returns:
            Response text from the model
        """
        # Use provided logger or instance logger
        log = logger or self.logger
        
        # Generate unique transaction ID for this API call
        transaction_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        # Ensure we call the v1 chat completions endpoint (normalize base_url separately)
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': model or self.default_model,
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': max_tokens,
            'temperature': temperature
        }
        
        # Create LLM I/O log entry
        io_log_entry = {
            'transaction_id': transaction_id,
            'timestamp': datetime.now().isoformat(),
            'endpoint': url,
            'input': {
                'model': payload['model'],
                'messages': payload['messages'],
                'max_tokens': max_tokens,
                'temperature': temperature,
                'prompt_length': len(prompt)
            },
            'metadata': {
                'api_key_masked': self.api_key[:8] + '...' if self.api_key else None,
                'base_url': self.base_url,
                'timeout': self.timeout
            }
        }
        
        # Log comprehensive diagnostic information (plain text, no emojis)
        log.info(f"API Transaction {transaction_id}: Starting Poe API request")
        log.info(f"API Transaction {transaction_id}: Endpoint: {url}")
        log.info(f"API Transaction {transaction_id}: Model: {payload['model']}")
        log.info(f"API Transaction {transaction_id}: Prompt length: {len(prompt)} characters")
        log.info(f"API Transaction {transaction_id}: Parameters: max_tokens={max_tokens}, temperature={temperature}")
        log.debug(f"API Transaction {transaction_id}: Full payload: {json.dumps(payload, indent=2)}")
        
        # Preview prompt in log (truncated if too long)
        prompt_preview = prompt[:500] + "..." if len(prompt) > 500 else prompt
        log.info(f"API Transaction {transaction_id}: Prompt preview: {prompt_preview}")
        
        try:
            start_time = datetime.now()
            log.info(f"API Transaction {transaction_id}: Sending request...")
            
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Update I/O log with request metadata
            io_log_entry['request_metadata'] = {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'http_status': response.status_code,
                'response_headers': dict(response.headers),
                'request_headers': {k: v for k, v in headers.items() if k != 'Authorization'}  # Don't log full auth header
            }
            
            log.info(f"API Transaction {transaction_id}: Request completed in {duration:.2f} seconds")
            log.info(f"API Transaction {transaction_id}: HTTP Status: {response.status_code}")
            log.debug(f"API Transaction {transaction_id}: Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
            result = response.json()
            
            # Update I/O log with response data
            io_log_entry['output'] = result
            io_log_entry['success'] = True
            
            log.info(f"API Transaction {transaction_id}: Response received, parsing...")
            log.debug(f"API Transaction {transaction_id}: Raw response: {json.dumps(result, indent=2)}")
            
            if 'choices' in result and len(result['choices']) > 0:
                response_text = result['choices'][0]['message']['content']
                
                # Update I/O log with final response
                io_log_entry['final_response'] = {
                    'text': response_text,
                    'length': len(response_text),
                    'finish_reason': result['choices'][0].get('finish_reason')
                }
                
                log.info(f"API Transaction {transaction_id}: Response extracted ({len(response_text)} characters)")
                log.debug(f"API Transaction {transaction_id}: Response preview: {response_text[:200]}...")
                
                if 'usage' in result:
                    usage = result['usage']
                    io_log_entry['token_usage'] = usage
                    log.info(f"API Transaction {transaction_id}: Token usage: {usage}")
                
                # Save complete I/O log
                self._save_io_log(transaction_id, io_log_entry)
                
                log.info(f"API Transaction {transaction_id}: Complete I/O log saved to LLM_io_log/")
                return response_text
            else:
                error_msg = f"Unexpected API response format: {result}"
                io_log_entry['error'] = error_msg
                io_log_entry['success'] = False
                self._save_io_log(transaction_id, io_log_entry)
                
                log.error(f"API Transaction {transaction_id}: ERROR - {error_msg}")
                raise ValueError(error_msg)
                
        except requests.exceptions.Timeout as e:
            error_msg = f"Request timed out after {self.timeout} seconds: {e}"
            io_log_entry['error'] = error_msg
            io_log_entry['success'] = False
            self._save_io_log(transaction_id, io_log_entry)
            
            log.error(f"API Transaction {transaction_id}: TIMEOUT - {error_msg}")
            raise RuntimeError(error_msg)
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error - unable to reach {url}: {e}"
            io_log_entry['error'] = error_msg
            io_log_entry['success'] = False
            self._save_io_log(transaction_id, io_log_entry)
            
            log.error(f"API Transaction {transaction_id}: CONNECTION ERROR - {error_msg}")
            raise RuntimeError(error_msg)
        except requests.exceptions.HTTPError as e:
            # Provide a clearer, actionable message for 4xx/5xx HTTP errors, especially 403 Forbidden
            status_code = response.status_code if 'response' in locals() else None
            raw_text = response.text if 'response' in locals() else ''

            if status_code == 403:
                hint = (
                    "403 Forbidden: provider rejected the request. This usually means the API key is invalid, "
                    "the account lacks permission for this endpoint, or the provider is blocking the client (Cloudflare/ACL). "
                    "Check your OPENAI_API_KEY (or provider-specific key), account permissions, and the configured base_url."
                )
                error_msg = f"HTTP error {status_code}: 403 Forbidden. {hint}"
            else:
                error_msg = f"HTTP error {status_code}: {e}"

            io_log_entry['error'] = error_msg
            io_log_entry['success'] = False
            io_log_entry['raw_response'] = raw_text
            self._save_io_log(transaction_id, io_log_entry)

            log.error(f"API Transaction {transaction_id}: HTTP ERROR - {error_msg}")
            log.debug(f"API Transaction {transaction_id}: Raw error response (truncated): {raw_text[:1000]}...")
            raise RuntimeError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {e}"
            io_log_entry['error'] = error_msg
            io_log_entry['success'] = False
            self._save_io_log(transaction_id, io_log_entry)
            
            log.error(f"API Transaction {transaction_id}: REQUEST ERROR - {error_msg}")
            raise RuntimeError(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse JSON response: {e}"
            io_log_entry['error'] = error_msg
            io_log_entry['success'] = False
            io_log_entry['raw_response'] = response.text[:1000] if 'response' in locals() else None
            self._save_io_log(transaction_id, io_log_entry)
            
            log.error(f"API Transaction {transaction_id}: JSON PARSE ERROR - {error_msg}")
            log.debug(f"API Transaction {transaction_id}: Raw response: {response.text[:500]}..." if 'response' in locals() else "No response received")
            raise RuntimeError(error_msg)
    
    def _save_io_log(self, transaction_id: str, io_log_entry: dict):
        """Save complete I/O log entry to LLM_io_log directory."""
        try:
            filename = f"llm_transaction_{transaction_id}.json"
            filepath = self.llm_io_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(io_log_entry, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"💾 I/O log saved: {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save I/O log for transaction {transaction_id}: {e}")
    
    def process_file(
        self,
        filepath: str,
        prompt_template: str,
        model: Optional[str] = None,
        max_tokens: int = 2000
    ) -> Dict[str, any]:
        """
        Process a single file with a custom prompt.
        
        Args:
            filepath: Path to file to process
            prompt_template: Prompt template. Use {filepath}, {content}, {filename}, {extension} placeholders
            model: Model to use
            max_tokens: Maximum tokens in response
            
        Returns:
            Dictionary with file info and response
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {
                'filepath': filepath,
                'success': False,
                'error': f"Error reading file: {e}"
            }
        
        # Format prompt with file info
        prompt = prompt_template.format(
            filepath=filepath,
            content=content,
            filename=Path(filepath).name,
            extension=Path(filepath).suffix
        )
        
        try:
            response = self.send_message(prompt, model=model, max_tokens=max_tokens)
            return {
                'filepath': filepath,
                'success': True,
                'response': response,
                'model': model or self.default_model
            }
        except Exception as e:
            return {
                'filepath': filepath,
                'success': False,
                'error': str(e)
            }
    
    def process_files_batch(
        self,
        filepaths: List[str],
        prompt_template: str,
        model: Optional[str] = None,
        max_tokens: int = 2000,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[Dict[str, any]]:
        """
        Process multiple files with the same prompt template.
        
        Args:
            filepaths: List of file paths to process
            prompt_template: Prompt template with {filepath}, {content}, etc.
            model: Model to use
            max_tokens: Maximum tokens per response
            progress_callback: Optional callback(current, total, filepath) for progress
            
        Returns:
            List of result dictionaries
        """
        results = []
        total = len(filepaths)
        
        for idx, filepath in enumerate(filepaths, 1):
            if progress_callback:
                progress_callback(idx, total, filepath)
            
            result = self.process_file(filepath, prompt_template, model, max_tokens)
            results.append(result)
        
        return results


def interactive_model_selection(client: PoeClient) -> str:
    """
    Interactive model selection from available models.
    
    Args:
        client: PoeClient instance
        
    Returns:
        Selected model name
    """
    print("\nFetching available models from Poe.com...")
    models = client.get_available_models()
    
    print(f"\nAvailable models ({len(models)}):")
    for idx, model in enumerate(models, 1):
        marker = " (default)" if model == client.default_model else ""
        print(f"  {idx:2d}. {model}{marker}")
    
    while True:
        try:
            choice = input(f"\nSelect model (1-{len(models)}) or press Enter for default: ").strip()
            
            if not choice:
                print(f"Using default model: {client.default_model}")
                return client.default_model
            
            idx = int(choice)
            if 1 <= idx <= len(models):
                selected = models[idx - 1]
                print(f"Selected model: {selected}")
                return selected
            else:
                print(f"Please enter a number between 1 and {len(models)}")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(0)


def main():
    """Example usage and CLI interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Process files through Poe.com API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process files with custom prompt
  python poe_client.py file1.txt file2.py --prompt "Summarize this file: {content}"
  
  # Interactive model selection
  python poe_client.py files/*.py --prompt "Review this code: {content}" --interactive
  
  # Use specific model
  python poe_client.py *.md --prompt "Analyze: {content}" --model GPT-4o
  
  # Save results to JSON
  python poe_client.py *.txt --prompt "Summarize: {content}" --output results.json
  
  # List available models
  python poe_client.py --list-models
        """
    )
    
    parser.add_argument('files', nargs='*', help='Files to process')
    parser.add_argument('--prompt', help='Prompt template (use {filepath}, {content}, {filename}, {extension})')
    parser.add_argument('--model', help='Model to use (default: from env or Claude-Sonnet-4.5)')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactively select model')
    parser.add_argument('--list-models', action='store_true', help='List available models and exit')
    parser.add_argument('--max-tokens', type=int, default=2000, help='Max tokens per response')
    parser.add_argument('--output', '-o', help='Save results to JSON file')
    parser.add_argument('--api-key', help='Poe API key (default: OPENAI_API_KEY env var)')
    parser.add_argument('--base-url', help='API base URL (default: OPENAI_BASE_URL env var)')
    parser.add_argument('--no-cache', action='store_true', help='Disable model list caching')
    
    args = parser.parse_args()
    
    # Initialize client
    try:
        client = PoeClient(api_key=args.api_key, base_url=args.base_url)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # List models mode
    if args.list_models:
        print("Fetching available models from Poe.com...")
        models = client.get_available_models(use_cache=not args.no_cache)
        print(f"\nAvailable models ({len(models)}):")
        for idx, model in enumerate(models, 1):
            marker = " (default)" if model == client.default_model else ""
            print(f"  {idx:2d}. {model}{marker}")
        sys.exit(0)
    
    # Require files and prompt for processing mode
    if not args.files or not args.prompt:
        parser.error("files and --prompt are required (unless using --list-models)")
    
    # Select model
    if args.interactive:
        model = interactive_model_selection(client)
    else:
        model = args.model
    
    # Expand file patterns
    from glob import glob
    filepaths = []
    for pattern in args.files:
        matches = glob(pattern)
        if matches:
            filepaths.extend(matches)
        else:
            filepaths.append(pattern)  # Keep as-is if no glob match
    
    # Remove duplicates and filter existing files
    filepaths = [f for f in sorted(set(filepaths)) if os.path.isfile(f)]
    
    if not filepaths:
        print("Error: No valid files found")
        sys.exit(1)
    
    print(f"\nProcessing {len(filepaths)} files with model: {model or client.default_model}")
    print(f"Prompt template: {args.prompt[:100]}...")
    print()
    
    # Progress callback
    def show_progress(current, total, filepath):
        print(f"[{current}/{total}] Processing: {filepath}")
    
    # Process files
    results = client.process_files_batch(
        filepaths,
        args.prompt,
        model=model,
        max_tokens=args.max_tokens,
        progress_callback=show_progress
    )
    
    # Display results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80 + "\n")
    
    success_count = sum(1 for r in results if r['success'])
    print(f"Successfully processed: {success_count}/{len(results)}")
    
    for result in results:
        print(f"\n{'='*80}")
        print(f"File: {result['filepath']}")
        print(f"Status: {'✓ Success' if result['success'] else '✗ Failed'}")
        
        if result['success']:
            print(f"Model: {result['model']}")
            print(f"\nResponse:\n{result['response']}")
        else:
            print(f"Error: {result['error']}")
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"\n✓ Results saved to: {args.output}")


if __name__ == '__main__':
    main()
