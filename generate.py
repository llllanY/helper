import requests
import json
from datetime import datetime

# ---------- 你可以改这里的城市 ----------
CITY = "Harbin"          # 哈尔滨，可改成 Heihe（黑河）
LANG = "zh"              # 中文显示
# 关注词列表：新闻标题里有这些词就会在后面通知你
KEYWORDS = ["黑龙江", "哈尔滨", "黑河", "供暖", "低温"]

# ---------- 1. 抓天气 ----------
def get_weather(city):
    url = f"https://wttr.in/{city}?format=3&lang={LANG}"
    try:
        return requests.get(url, timeout=10).text.strip()
    except:
        return "天气获取失败"

# ---------- 2. 抓新闻（使用 NewsAPI 密钥）----------
def get_news():
    api_key = os.getenv("NEWSAPI_KEY")          # 从秘密坑里拿密钥
    if not api_key:
        return ["新闻密钥未配置"]
    # 用 country=cn 拿国内新闻，pageSize=10 取10条
    url = f"https://newsapi.org/v2/top-headlines?country=cn&pageSize=10&apiKey={api_key}"
    try:
        data = requests.get(url, timeout=10).json()
        if data.get("status") != "ok":
            return [f"新闻API错误: {data.get('message','')}"]
        articles = data.get("articles", [])
        return [a["title"] for a in articles if a.get("title")]
    except Exception as e:
        return [f"新闻获取失败: {e}"]

# ---------- 3. 用大模型生成简报 ----------
def generate_brief(weather, news_titles):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return "暂无 AI 简报（未配置密钥）"
    
    news_str = "\n".join(f"- {t}" for t in news_titles[:5])
    prompt = f"""你是黑龙江生活助手，请根据下面信息写一段70字以内的简报，语气亲切，带一句礼貌问候。不要超过70字。
天气：{weather}
今日新闻：{news_str}
简报："""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "max_tokens": 200
    }
    try:
        resp = requests.post("https://api.deepseek.com/v1/chat/completions",
                             headers=headers, json=payload, timeout=15)
        return resp.json()["choices"][0]["message"]["content"].strip()
    except:
        return "简报生成失败，请稍后再试"

# ---------- 4. 匹配关注词 ----------
def find_matches(news_titles, keywords):
    matches = []
    for t in news_titles:
        for kw in keywords:
            if kw in t:
                matches.append(t)
                break
    return matches

# ---------- 主流程 ----------
import os
weather = get_weather(CITY)
news_titles = get_news()
brief = generate_brief(weather, news_titles)
matched = find_matches(news_titles, KEYWORDS)

data = {
    "update_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "weather": weather,
    "brief": brief,
    "news": news_titles,
    "matches": matched
}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("数据已更新")
