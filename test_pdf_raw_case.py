import sys
sys.stdout.reconfigure(encoding='utf-8')
import pypdf

reader = pypdf.PdfReader('uploads/1790913742_ChemistryXII.pdf')
full_text = '\n'.join([p.extract_text() or '' for p in reader.pages])

print(f"Total pages: {len(reader.pages)}, Total chars: {len(full_text)}")

lines = full_text.split('\n')
for i, line in enumerate(lines):
    if any(k in line.lower() for k in ['case', 'read the passage', 'direction', 'paragraph', 'section-d', 'section d', 'section e', 'section-e']):
        print(f"--- Line {i}: {line} ---")
        for j in range(max(0, i-2), min(len(lines), i+25)):
            print(f"  {lines[j]}")
        print("="*60)
