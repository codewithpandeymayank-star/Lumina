with open('app/pages/Chat.py', 'r', encoding='utf-8') as f:
    content = f.read()

additions = """
[data-testid="stMainBlockContainer"] { background: #06090f !important; }
[data-testid="stVerticalBlock"] { background: #06090f !important; }
section[data-testid="stMain"] > div { background: #06090f !important; }
section[data-testid="stMain"] > div > div { background: #06090f !important; }
"""

target = '[data-testid="stAppViewContainer"] { background: #06090f !important; }'

if target in content:
    content = content.replace(target, target + additions)
    with open('app/pages/Chat.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed!")
else:
    print("Target not found!")
    idx = content.find("stAppView")
    print(content[max(0,idx-10):idx+80])
