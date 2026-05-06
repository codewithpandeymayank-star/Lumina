with open('app/pages/Chat.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_css = 'html, body, .stApp {'
new_css = '''[data-testid="stAppViewContainer"] { background: #06090f !important; }
[data-testid="stMain"] { background: #06090f !important; }
[data-testid="stMainBlockContainer"] { background: #06090f !important; }
[data-testid="stVerticalBlock"] { background: #06090f !important; }
section[data-testid="stMain"] > div { background: #06090f !important; }
html, body, .stApp {'''

content = content.replace(old_css, new_css, 1)
with open('app/pages/Chat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done! Lines added:", content.count('stMainBlockContainer'))
