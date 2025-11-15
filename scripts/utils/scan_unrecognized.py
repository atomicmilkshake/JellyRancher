from pathlib import Path
import sys

# Ensure the scripts folder is on sys.path so we can import the organizer module
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from organize_tv_shows import parse_tv_filename
except Exception as e:
    print(f"ERROR: Could not import parse_tv_filename from organize_tv_shows: {e}")
    raise

ROOT = Path(r'W:\#MEDIA')

if not ROOT.exists():
    print(f"Root path does not exist: {ROOT}")
    raise SystemExit(1)

unrecognized = []
total = 0

for p in ROOT.rglob('*'):
    if not p.is_file():
        continue
    total += 1
    try:
        res = parse_tv_filename(p)
    except Exception as e:
        print(f"PARSER ERROR {p}: {e}")
        unrecognized.append(p)
        continue

    if res is None:
        print(str(p))
        unrecognized.append(p)

print('\n--- SUMMARY ---')
print(f'Total files scanned: {total}')
print(f'Unrecognized files: {len(unrecognized)}')

if len(unrecognized) > 0:
    out = Path(__file__).with_suffix('.unrecognized.txt')
    with open(out, 'w', encoding='utf-8') as f:
        for p in unrecognized:
            f.write(str(p) + '\n')
    print(f'List written to: {out}')
