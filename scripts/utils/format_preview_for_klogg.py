import json

# Read the JSON from W: drive
with open(r'W:\#MEDIA\tv_organization_preview.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Format for klogg (line-based log viewer)
with open('tv_organization_preview_klogg.txt', 'w', encoding='utf-8') as f:
    f.write("TV Organization Preview - Proposed Changes\n")
    f.write("=" * 50 + "\n\n")

    for i, item in enumerate(data, 1):
        f.write(f"[{i:3d}] CURRENT:  {item['current_path']}\n")
        f.write(f"      PROPOSED: {item['proposed_path']}")
        if item.get('title_note'):
            f.write(f" {item['title_note']}")
        f.write("\n")
        if item.get('parsed_info'):
            parsed = item['parsed_info']
            f.write(f"      PARSED:   Show='{parsed.get('show','?')}' S{parsed.get('season',0):02d}E{parsed.get('episode',0):02d} '{parsed.get('title','?')}'\n")
        f.write("\n")

print(f"Formatted {len(data)} changes for klogg: tv_organization_preview_klogg.txt")