import json
import re

def clean_json(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            # Read raw content to handle potential trailing commas or syntax errors manually if needed
            # But json.load usually fails on trailing commas. 
            # Let's try standard load first, if it fails, we might need a more robust parser or regex fix.
            content = f.read()
            
        # Fix trailing commas in arrays/objects (simple regex approach)
        content = re.sub(r',(\s*[\}\]])', r'\1', content)
        
        data = json.loads(content)
        
        if not isinstance(data, list):
            print("Error: Root element is not a list.")
            return

        cleaned_data = []
        seen_entries = set()

        for item in data:
            # 1. Ensure non-empty fields
            if not item.get('word') or not item.get('telegram_file_id'):
                continue

            # 2. Normalize fields
            word = item['word'].strip()
            category = item.get('category', 'Uncategorized').strip()
            # Unify apostrophes (e.g. ’ to ')
            category = category.replace("’", "'").replace("`", "'")
            definition = item.get('definition', '').strip()
            file_id = item['telegram_file_id'].strip()

            # 3. Remove duplicates (based on title and file_id)
            unique_key = (word.lower(), file_id)
            if unique_key in seen_entries:
                continue
            
            seen_entries.add(unique_key)

            cleaned_data.append({
                "word": word,
                "category": category,
                "telegram_file_id": file_id,
                "definition": definition
            })

        # 4. Output cleaned JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
            
        print(f"✅ Successfully cleaned data. Saved to {output_file}")
        print(f"Original count: {len(data)}")
        print(f"Cleaned count: {len(cleaned_data)}")

    except json.JSONDecodeError as e:
        print(f"❌ JSON Syntax Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Create a dummy raw_data.json if it doesn't exist for demonstration
    import os
    if not os.path.exists('raw_data.json'):
        print("ℹ️ 'raw_data.json' not found. Please create it with your data.")
    else:
        clean_json('raw_data.json', 'cleaned_data.json')
