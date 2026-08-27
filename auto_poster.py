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
# 1. 由ъ뼹 ?곗씠??湲곕컲 SEO (?ㅼ씠踰??먮룞?꾩꽦/?곌?寃?됱뼱 ?ㅼ떆媛?異붿텧)
# =================================================================
main_keyword = campaign.get('keywords', [campaign['name']])[0]
real_keywords = [main_keyword]
try:
    # ?ㅼ씠踰?紐⑤컮???먮룞?꾩꽦 API (?몄쬆 遺덊븘?? 媛???ㅼ떆媛??몃젋?쒕? 諛섏쁺?섎뒗 濡깊뀒???ㅼ썙??
    url = f"https://mac.search.naver.com/mobile/ac?q={main_keyword}&st=1&r_format=json&q_enc=UTF-8"
    res = requests.get(url, timeout=5)
    data = res.json()
    if 'items' in data and len(data['items']) > 0 and len(data['items'][0]) > 0:
        real_keywords = [item[0] for item in data['items'][0][:4]]  # ?곸쐞 4媛?異붿텧
except Exception as e:
    print("Trend API fetch failed, using fallback:", e)

keyword_str = ", ".join(real_keywords)
print(f"?뵦 Extracted Real Trend Keywords: {keyword_str}")

# =================================================================
# 2. 蹂몃Ц ?묒꽦 (2-Pass 濡쒖쭅)
# =================================================================
prompt = f"""
?뱀떊? 理쒓퀬???쒗쑕留덉???CPA) 移댄뵾?쇱씠?곗엯?덈떎.
?ㅼ쓬 罹좏럹???뺣낫瑜?諛뷀깢?쇰줈 釉붾줈洹??ъ뒪??'蹂몃Ц'留??묒꽦?섏꽭?? 
?덈? YAML Frontmatter(--- layout: post ... ---)瑜??묒꽦?섏? 留덉꽭?? ?ㅼ쭅 留덊겕?ㅼ슫 蹂몃Ц ?띿뒪?몃쭔 異쒕젰?섏꽭??

[罹좏럹???뺣낫]
- ?대쫫: {campaign['name']}
- ?쒗깮: {campaign['benefits']}
- ?寃?諛?洹쒖튃: {campaign['rules']}
- 留곹겕: {campaign['link']}
- ?寃?濡깊뀒???ㅼ썙?? {keyword_str}

[2-Pass ?묒꽦 濡쒖쭅]
1. (Pass 1) 李쎌쓽?곸씤 ?ㅽ넗由ы뀛留?珥덉븞???묒꽦?⑸땲?? ?寃잛쓽 怨좎땐???먭레?섍퀬 ?쒗깮??媛뺤“?섏꽭??
2. (Pass 2) 珥덉븞??寃?좏븯硫?湲덉??대굹 洹쒖튃 ?꾨컲???녿뒗吏 ?뺤씤?섍퀬, 理쒖쥌?곸쑝濡?媛???먯뿰?ㅻ읇怨??ㅻ뱷???덈뒗 ?꾨꼍??蹂몃Ц???앹꽦?섏꽭??

[?꾩닔 援ъ“]
1. 湲 以묎컙以묎컙???먯뿰?ㅻ읇寃?踰꾪듉 ?뺥깭??CPA 留곹겕瑜?2???댁긽 ?쎌엯?섏꽭??
(踰꾪듉 HTML ?덉떆: <div style="text-align: center; margin: 20px 0;"><a href="{campaign['link']}" style="background-color: #ff5722; color: white; padding: 15px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 18px;" target="_blank">?몛 臾대즺 ?곷떞 ?좎껌?섍린</a></div>)
2. 湲???댁슜怨??댁슱由щ뒗 怨좏솕吏??몄뒪?뚮옒???대?吏 URL(https://source.unsplash.com/800x600/?{main_keyword})??留덊겕?ㅼ슫 ?뺥깭濡?2???댁긽 ?쎌엯?섏꽭??

異쒕젰? 2-Pass瑜?嫄곗튇 理쒖쥌 '蹂몃Ц ?댁슜'留??댁＜?몄슂.
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
        if not has_button: error_msgs.append("?섏씡??踰꾪듉(a ?쒓렇) ?꾨씫")
        if not has_image: error_msgs.append("?대?吏(unsplash ?? ?꾨씫")
        prompt += f"\n\n[?쒖뒪??寃쎄퀬] {', '.join(error_msgs)} ?섏뿀?듬땲?? 諛섎뱶??踰꾪듉怨??대?吏瑜??ы븿???ㅼ떆 ?묒꽦?섏꽭??"


# AI ?ㅻ쪟 諛⑹뼱 (Frontmatter ?쒓굅)
import re
body_content = re.sub(r'^---.*?---\s*', '', body_content, flags=re.DOTALL)
body_content = re.sub(r'??s*layout:.*???s*', '', body_content, flags=re.DOTALL)

kst = pytz.timezone('Asia/Seoul')
now = datetime.now(kst)
date_str = now.strftime('%Y-%m-%d %H:%M:%S +0900')
file_date_str = now.strftime('%Y-%m-%d')
file_time_str = now.strftime('%H-%M-%S')

# =================================================================
# 3. 由ъ뼹 ?곗씠??湲곕컲 SEO ?쒕ぉ ?앹꽦
# =================================================================
title_prompt = f"""??湲? 援ш?/?ㅼ씠踰?寃???좎엯(SEO)??洹밸??뷀빐???⑸땲?? 
諛⑷툑 ?ы꽭 寃???몃젋???먮룞?꾩꽦)?먯꽌 異붿텧???ㅼ젣 濡깊뀒???ㅼ썙?쒕뒗 ?ㅼ쓬怨?媛숈뒿?덈떎: [{keyword_str}]

???ㅼ젣 ?ㅼ썙?쒕뱾 以?1~2媛쒕? 諛섎뱶???쒕ぉ ?욌?遺꾩뿉 ?먯뿰?ㅻ읇寃?諛곗튂?섏뿬, ?寃?怨좉컼??怨좎땐???닿껐?댁＜??轅???뺣낫湲 ?먮굦?쇰줈 40~60??湲몄씠???쒕ぉ???묒꽦?섏꽭??
(?⑥닚 愿묎퀬泥섎읆 蹂댁씠吏 ?딄쾶, ?뱀닔臾몄옄 ?쒖쇅, 蹂몃Ц ?놁씠 ?쒕ぉ留?異쒕젰)"""

title_response = model.generate_content(title_prompt)
title = title_response.text.strip().replace('"', '').replace("'", "")

category = "?뺣낫"
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
# 4. POST_LOG.md (諛쒗뻾 ??? 湲곕줉
# -------------------------------------------------------------
try:
    log_file = "POST_LOG.md"
    platform = campaign.get('platform', '湲고?')
    camp_name = campaign.get('name', '?대쫫?놁쓬')
    log_entry = f"- `{file_date_str}` | [{platform}] {camp_name} | {title}"
"
    
    # ?뚯씪???놁쑝硫??ㅻ뜑 ?ш퀬 ?앹꽦
    if not os.path.exists(log_file):
        with open(log_file, 'w', encoding='utf-8') as lf:
            lf.write("# ?뱷 ?먮룞 ?ъ뒪??諛쒗뻾 ???

")
            
    with open(log_file, 'a', encoding='utf-8') as lf:
        lf.write(log_entry)
except Exception as e:
    print("Log write failed:", e)

print(f"??Generated {filename}")
