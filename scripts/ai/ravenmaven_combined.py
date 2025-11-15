import os
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from ravenmaven_client import PoeClient

def load_prompt_template(prompt_file):
    with open(prompt_file, 'r', encoding='utf-8') as f:
        return f.read()

def chunk_list(file_list, chunk_size):
    for i in range(0, len(file_list), chunk_size):
        yield file_list[i:i + chunk_size]

def ai_analysis(prompt, filepaths, client, model="Claude-Sonnet-4.5"):
    # Functional AI call using PoeClient
    response = client.send_message(prompt, model=model, max_tokens=8192)
    return response.strip()

def parse_markdown_table(md_table):
    # Simple parser for Markdown table (use pandas if complex)
    lines = md_table.split('\n')[2:]  # Skip header
    actions = []
    for line in lines:
        if line.strip():
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) == 3:
                actions.append({'old': parts[0], 'new': parts[1], 'action': parts[2]})
    return actions

def execute_actions(actions, jellyfin_dir, dry_run=False):
    for action in actions:
        old_path = action['old']
        new_path = action['new']
        act = action['action']
        if act == 'DELETE':
            if dry_run:
                print(f"[DRY RUN] Would delete: {old_path}")
            else:
                try:
                    os.remove(old_path)
                    print(f"Deleted: {old_path}")
                except Exception as e:
                    print(f"Error deleting {old_path}: {e}")
        elif act in ['RENAME', 'MOVE', 'RENAME & MOVE']:
            if dry_run:
                print(f"[DRY RUN] Would move/rename {old_path} to {new_path}")
            else:
                try:
                    os.makedirs(os.path.dirname(new_path), exist_ok=True)
                    os.rename(old_path, new_path)
                    print(f"Moved/renamed: {old_path} -> {new_path}")
                except Exception as e:
                    print(f"Error moving {old_path} to {new_path}: {e}")
        # SKIP does nothing

def build_structure_tree(actions):
    """Build the tree structure from actions, adapted from structure_preview_gui.py"""
    structure_tree = defaultdict(lambda: defaultdict(list))

    for action in actions:
        new_path = action['new']
        try:
            # Find the category (Movies or TV Shows) in the path
            path_str = str(new_path)
            if "/TV Shows/" in path_str or "\\TV Shows\\" in path_str:
                category = "TV Shows"
                # Extract show name and season info
                if "/TV Shows/" in path_str:
                    parts_after_tv = path_str.split("/TV Shows/", 1)[1]
                else:
                    parts_after_tv = path_str.split("\\TV Shows\\", 1)[1]
                show_parts = parts_after_tv.replace("\\", "/").split("/")
                if len(show_parts) >= 2:
                    show_name = show_parts[0]
                    season_or_file = show_parts[1]
                    if season_or_file.startswith("Season "):
                        # TV episode: TV Shows/Show Name/Season XX/filename
                        if len(show_parts) >= 3:
                            season = season_or_file
                            filename = show_parts[2]
                            structure_tree[category][show_name].append(f"{season}/{filename}")
                        else:
                            # Just season folder
                            structure_tree[category][show_name] = []
                    else:
                        # Direct file under show
                        structure_tree[category][show_name].append(season_or_file)
                else:
                    # Just show folder
                    structure_tree[category][show_name] = []
            elif "/Movies/" in path_str or "\\Movies\\" in path_str:
                category = "Movies"
                # Extract movie name
                if "/Movies/" in path_str:
                    parts_after_movies = path_str.split("/Movies/", 1)[1]
                else:
                    parts_after_movies = path_str.split("\\Movies\\", 1)[1]
                movie_parts = parts_after_movies.replace("\\", "/").split("/")
                movie_name = movie_parts[0]
                if len(movie_parts) >= 2:
                    # Movie file
                    filename = movie_parts[1]
                    structure_tree[category][movie_name].append(filename)
                else:
                    # Just movie folder
                    structure_tree[category][movie_name] = []
            else:
                # Unknown category, skip
                continue

        except Exception as e:
            print(f"Error parsing path {new_path}: {e}")

    return structure_tree

def display_structure(structure_tree, output_dir):
    """Display and save the proposed structure."""
    print("\nProposed Jellyfin Structure:")
    print("=" * 50)

    structure_text = "Proposed Jellyfin Structure\n" + "=" * 50 + "\n\n"

    for category, items in sorted(structure_tree.items()):
        print(f"{category}/")
        structure_text += f"{category}/\n"

        for item_name, files in sorted(items.items()):
            print(f"  {item_name}/")
            structure_text += f"  {item_name}/\n"

            for file in sorted(files):
                print(f"    {file}")
                structure_text += f"    {file}\n"

            print()
            structure_text += "\n"

        print()
        structure_text += "\n"

    # Save to file
    structure_file = output_dir / "proposed_structure.txt"
    with open(structure_file, 'w', encoding='utf-8') as f:
        f.write(structure_text)
    print(f"Structure saved to: {structure_file}")

def main():
    parser = argparse.ArgumentParser(description="Combined RavenMaven Batch and Cleanup Script")
    parser.add_argument('--list-file', default=r'E:\#MEDIA\list.txt', help='Path to file list')
    parser.add_argument('--chunk-size', type=int, default=75, help='Files per chunk')
    parser.add_argument('--prompt-file', default=r'V:\RavenMaven\predefined prompts\jellyfin-standardization.md', help='Prompt template file')
    parser.add_argument('--jellyfin-dir', default=r'E:\#MEDIA', help='Jellyfin directory')
    parser.add_argument('--dry-run', action='store_true', help='Simulate actions')
    parser.add_argument('--model', default='Claude-Sonnet-4.5', help='AI model to use')

    args = parser.parse_args()

    print("🎃 Starting Combined RavenMaven Processing - Time to get back to pumpkins! 🎃")

    # Create timestamped output folder
    script_dir = Path(__file__).parent
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = script_dir / f"ravenmaven_combined_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output folder: {output_dir}")

    # Read list file
    if not os.path.exists(args.list_file):
        print(f"Error: List file not found: {args.list_file}")
        return
    with open(args.list_file, 'r', encoding='utf-8') as f:
        file_list = [line.strip() for line in f if line.strip()]
    total_files = len(file_list)
    print(f"Found {total_files} files to process")

    # Load prompt template
    prompt_template = load_prompt_template(args.prompt_file)

    # Initialize AI client
    client = PoeClient()

    all_actions = []
    processed = 0
    for chunk_num, chunk in enumerate(chunk_list(file_list, args.chunk_size), 1):
        print(f"\n🔄 Processing chunk {chunk_num} with {len(chunk)} files...")

        # Prepare prompt with filepaths
        filepaths_str = "\n".join(f"- {fp}" for fp in chunk)
        prompt = prompt_template.replace('{filepaths}', filepaths_str)

        # AI analysis
        ai_response = ai_analysis(prompt, chunk, client, args.model)

        # Parse actions
        actions = parse_markdown_table(ai_response)
        all_actions.extend(actions)

        # Save chunk results
        chunk_result = {
            "chunk_num": chunk_num,
            "file_count": len(chunk),
            "ai_response": ai_response,
            "actions": actions,
            "timestamp": datetime.now().isoformat()
        }
        chunk_file = output_dir / f"chunk{chunk_num}_processed.json"
        with open(chunk_file, 'w', encoding='utf-8') as f:
            json.dump(chunk_result, f, indent=2, ensure_ascii=False)

        processed += len(chunk)
        print(f"📊 Progress: {processed} / {total_files} files processed")

    # Build and display structure
    structure_tree = build_structure_tree(all_actions)
    display_structure(structure_tree, output_dir)

    # Execute actions
    print("\nExecuting actions...")
    execute_actions(all_actions, args.jellyfin_dir, args.dry_run)

    print("\n🎃 Combined processing complete! Ready for pumpkin carving! 🎃")

if __name__ == "__main__":
    main()