import os
import json
import random
import requests
from datetime import datetime
import google.generativeai as genai
import pytz

# Setup Gemini
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY is not set.")
    exit(1)

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# Load campaigns
campaigns_file = 'campaigns.json'
if not os.path.exists(campaigns_file):
    print("No campaigns.json found.")
    exit(1)

with open(campaigns_file, 'r', encoding='utf-8') as f:
    campaigns = json.load(f)

if not campaigns:
    print("No campaigns available.")
    exit(1)


# Date Filter Logic
import pytz
from datetime import datetime
try:
    kst = pytz.timezone('Asia/Seoul')
    today = datetime.now(kst)
    valid_campaigns = []
    for c in campaigns:
        end_date_str = c.get('end_date')
        if not end_date_str:
            valid_campaigns.append(c)
        else:
            try:
                # Parse YYYY-MM-DD
                end_date = datetime.strptime(end_date_str.strip(), "%Y-%m-%d")
                end_date = kst.localize(end_date.replace(hour=23, minute=59, second=59))
                if today <= end_date:
                    valid_campaigns.append(c)
            except Exception as e:
                print(f"Date parse error for {c.get('name')}: {e}")
                valid_campaigns.append(c)
    if not valid_campaigns:
        print("No valid campaigns available (all expired).")
        exit(1)
    campaign = random.choice(valid_campaigns)
except Exception as e:
    print("Fallback in date filter:", e)
    campaign = random.choice(campaigns)


# =================================================================
# 1. ë¦¬ì–¼ ?°ì´??ê¸°ë°˜ SEO (?¤ì´ë²??ë™?„ì„±/?°ê?ê²€?‰ì–´ ?¤ì‹œê°?ì¶”ì¶œ)
# =================================================================
main_keyword = campaign.get('keywords', [campaign['name']])[0]
real_keywords = [main_keyword]
try:
    # ?¤ì´ë²?ëª¨ë°”???ë™?„ì„± API (?¸ì¦ ë¶ˆí•„?? ê°€???¤ì‹œê°??¸ë Œ?œë? ë°˜ì˜?˜ëŠ” ë¡±í…Œ???¤ì›Œ??
    url = f"https://mac.search.naver.com/mobile/ac?q={main_keyword}&st=1&r_format=json&q_enc=UTF-8"
    res = requests.get(url, timeout=5)
    data = res.json()
    if 'items' in data and len(data['items']) > 0 and len(data['items'][0]) > 0:
        real_keywords = [item[0] for item in data['items'][0][:4]]  # ?ìœ„ 4ê°?ì¶”ì¶œ
except Exception as e:
    print("Trend API fetch failed, using fallback:", e)

keyword_str = ", ".join(real_keywords)
print(f"?”¥ Extracted Real Trend Keywords: {keyword_str}")

# =================================================================
# 2. ë³¸ë¬¸ ?‘ì„± (2-Pass ë¡œì§)
# =================================================================
prompt = f"""
?¹ì‹ ?€ ìµœê³ ???œíœ´ë§ˆì???CPA) ì¹´í”¼?¼ì´?°ì…?ˆë‹¤.
?¤ìŒ ìº í˜???•ë³´ë¥?ë°”íƒ•?¼ë¡œ ë¸”ë¡œê·??¬ìŠ¤??'ë³¸ë¬¸'ë§??‘ì„±?˜ì„¸?? 
?ˆë? YAML Frontmatter(--- layout: post ... ---)ë¥??‘ì„±?˜ì? ë§ˆì„¸?? ?¤ì§ ë§ˆí¬?¤ìš´ ë³¸ë¬¸ ?ìŠ¤?¸ë§Œ ì¶œë ¥?˜ì„¸??

[ìº í˜???•ë³´]
- ?´ë¦„: {campaign['name']}
- ?œíƒ: {campaign['benefits']}
- ?€ê²?ë°?ê·œì¹™: {campaign['rules']}
- ë§í¬: {campaign['link']}
- ?€ê²?ë¡±í…Œ???¤ì›Œ?? {keyword_str}

[2-Pass ?‘ì„± ë¡œì§]
1. (Pass 1) ì°½ì˜?ì¸ ?¤í† ë¦¬í…”ë§?ì´ˆì•ˆ???‘ì„±?©ë‹ˆ?? ?€ê²Ÿì˜ ê³ ì¶©???ê·¹?˜ê³  ?œíƒ??ê°•ì¡°?˜ì„¸??
2. (Pass 2) ì´ˆì•ˆ??ê²€? í•˜ë©?ê¸ˆì??´ë‚˜ ê·œì¹™ ?„ë°˜???†ëŠ”ì§€ ?•ì¸?˜ê³ , ìµœì¢…?ìœ¼ë¡?ê°€???ì—°?¤ëŸ½ê³??¤ë“???ˆëŠ” ?„ë²½??ë³¸ë¬¸???ì„±?˜ì„¸??

[?„ìˆ˜ êµ¬ì¡°]
1. ê¸€ ì¤‘ê°„ì¤‘ê°„???ì—°?¤ëŸ½ê²?ë²„íŠ¼ ?•íƒœ??CPA ë§í¬ë¥?2???´ìƒ ?½ì…?˜ì„¸??
(ë²„íŠ¼ HTML ?ˆì‹œ: <div style="text-align: center; margin: 20px 0;"><a href="{campaign['link']}" style="background-color: #ff5722; color: white; padding: 15px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 18px;" target="_blank">?‘‰ ë¬´ë£Œ ?ë‹´ ? ì²­?˜ê¸°</a></div>)
2. ê¸€???´ìš©ê³??´ìš¸ë¦¬ëŠ” ê³ í™”ì§??¸ìŠ¤?Œë˜???´ë?ì§€ URL(https://source.unsplash.com/800x600/?{main_keyword})??ë§ˆí¬?¤ìš´ ?•íƒœë¡?2???´ìƒ ?½ì…?˜ì„¸??

ì¶œë ¥?€ 2-Passë¥?ê±°ì¹œ ìµœì¢… 'ë³¸ë¬¸ ?´ìš©'ë§??´ì£¼?¸ìš”.
"""

max_retries = 3
for attempt in range(max_retries):
    response = model.generate_content(prompt)
    body_content = response.text.strip()
    
    # 3-Pass Validation Check
    has_button = "href=" in body_content or "<a " in body_content
    has_image = "source.unsplash.com" in body_content or "<img" in body_content or "![" in body_content
    
    if has_button and has_image:
        break
    else:
        error_msgs = []
        if not has_button: error_msgs.append("?˜ìµ??ë²„íŠ¼(a ?œê·¸) ?„ë½")
        if not has_image: error_msgs.append("?´ë?ì§€(unsplash ?? ?„ë½")
        prompt += f"\n\n[?œìŠ¤??ê²½ê³ ] {', '.join(error_msgs)} ?˜ì—ˆ?µë‹ˆ?? ë°˜ë“œ??ë²„íŠ¼ê³??´ë?ì§€ë¥??¬í•¨???¤ì‹œ ?‘ì„±?˜ì„¸??"


# AI ?¤ë¥˜ ë°©ì–´ (Frontmatter ?œê±°)
import re
body_content = re.sub(r'^---.*?---\s*', '', body_content, flags=re.DOTALL)
body_content = re.sub(r'??s*layout:.*???s*', '', body_content, flags=re.DOTALL)

kst = pytz.timezone('Asia/Seoul')
now = datetime.now(kst)
date_str = now.strftime('%Y-%m-%d %H:%M:%S +0900')
file_date_str = now.strftime('%Y-%m-%d')
file_time_str = now.strftime('%H-%M-%S')

# =================================================================
# 3. ë¦¬ì–¼ ?°ì´??ê¸°ë°˜ SEO ?œëª© ?ì„±
# =================================================================
title_prompt = f"""??ê¸€?€ êµ¬ê?/?¤ì´ë²?ê²€??? ì…(SEO)??ê·¹ë??”í•´???©ë‹ˆ?? 
ë°©ê¸ˆ ?¬í„¸ ê²€???¸ë Œ???ë™?„ì„±)?ì„œ ì¶”ì¶œ???¤ì œ ë¡±í…Œ???¤ì›Œ?œëŠ” ?¤ìŒê³?ê°™ìŠµ?ˆë‹¤: [{keyword_str}]

???¤ì œ ?¤ì›Œ?œë“¤ ì¤?1~2ê°œë? ë°˜ë“œ???œëª© ?ë?ë¶„ì— ?ì—°?¤ëŸ½ê²?ë°°ì¹˜?˜ì—¬, ?€ê²?ê³ ê°??ê³ ì¶©???´ê²°?´ì£¼??ê¿€???•ë³´ê¸€ ?ë‚Œ?¼ë¡œ 40~60??ê¸¸ì´???œëª©???‘ì„±?˜ì„¸??
(?¨ìˆœ ê´‘ê³ ì²˜ëŸ¼ ë³´ì´ì§€ ?Šê²Œ, ?¹ìˆ˜ë¬¸ì ?œì™¸, ë³¸ë¬¸ ?†ì´ ?œëª©ë§?ì¶œë ¥)"""

title_response = model.generate_content(title_prompt)
title = title_response.text.strip().replace('"', '').replace("'", "")

category = "?•ë³´"
if campaign.get('keywords'):
    category = campaign['keywords'][0]

frontmatter = f"""---
layout: post
title: "{title}"
date: {date_str}
categories: [{category}]
---
"""

final_post = frontmatter + "\n\n" + body_content

os.makedirs('_posts', exist_ok=True)
filename = f"_posts/{file_date_str}-{file_time_str}.md"
with open(filename, 'w', encoding='utf-8') as f:
    f.write(final_post)

# -------------------------------------------------------------
# 4. POST_LOG.md (ë°œí–‰ ?€?? ê¸°ë¡
# -------------------------------------------------------------
try:
    log_file = "POST_LOG.md"
    platform = campaign.get('platform', 'ê¸°í?')
    camp_name = campaign.get('name', '?´ë¦„?†ìŒ')
    log_entry = f"- `{file_date_str}` | [{platform}] {camp_name} | {title}"
"
    
    # ?Œì¼???†ìœ¼ë©??¤ë” ?¬ê³  ?ì„±
    if not os.path.exists(log_file):
        with open(log_file, 'w', encoding='utf-8') as lf:
            lf.write("# ?“ ?ë™ ?¬ìŠ¤??ë°œí–‰ ?€??

")
            
    with open(log_file, 'a', encoding='utf-8') as lf:
        lf.write(log_entry)
except Exception as e:
    print("Log write failed:", e)

print(f"??Generated {filename}")
