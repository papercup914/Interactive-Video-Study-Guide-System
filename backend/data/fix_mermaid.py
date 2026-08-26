import sqlite3
import json
import re

DB_PATH = 'backend/data/jobs.db'

def fix_mermaid_in_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Fetch all study guides just to be safe and fix any that have broken mermaid
    rows = conn.execute("SELECT id, document FROM study_guides").fetchall()
    
    updated_count = 0
    for row in rows:
        job_id = row['id']
        try:
            doc = json.loads(row['document'])
        except:
            continue
            
        modified = False
        for key, text in doc.items():
            if not isinstance(text, str):
                continue
                
            # Look for sequenceDiagram that is not inside a markdown code block
            # If sequenceDiagram is preceded by some spaces or just at start of line, but NOT preceded by ```mermaid
            if 'sequenceDiagram' in text and '```mermaid' not in text:
                print(f"Fixing mermaid in {job_id} -> {key}")
                
                # We can use a regex to wrap from sequenceDiagram to the end of the text, or to the next section.
                # Usually the LLM outputs it at the end, or followed by another heading.
                # Let's find the start of sequenceDiagram
                start_idx = text.find('sequenceDiagram')
                
                # Check if it's already wrapped in something
                if "```" in text[max(0, start_idx-20):start_idx]:
                    print("  Already inside some code block, fixing to ```mermaid")
                    # Just replace the opening backticks if it's ``` or ```text
                    # But wait, let's just do a simple replacement for now
                    text = text.replace('```\nsequenceDiagram', '```mermaid\nsequenceDiagram')
                else:
                    print("  Wrapping in ```mermaid ... ```")
                    # Find where the diagram ends (usually double newline or next heading #)
                    lines = text[start_idx:].split('\n')
                    diagram_lines = []
                    rest_lines = []
                    in_diagram = True
                    for line in lines:
                        if in_diagram and (line.strip().startswith('#') or line.strip().startswith('```')):
                            in_diagram = False
                        if in_diagram:
                            diagram_lines.append(line)
                        else:
                            rest_lines.append(line)
                            
                    diagram_str = '\n'.join(diagram_lines).strip()
                    rest_str = '\n'.join(rest_lines)
                    
                    fixed_text = text[:start_idx] + "\n```mermaid\n" + diagram_str + "\n```\n\n" + rest_str
                    doc[key] = fixed_text
                modified = True
                
        if modified:
            conn.execute("UPDATE study_guides SET document = ? WHERE id = ?", (json.dumps(doc, ensure_ascii=False), job_id))
            updated_count += 1
            
    conn.commit()
    conn.close()
    print(f"Updated {updated_count} records.")

if __name__ == '__main__':
    fix_mermaid_in_db()
