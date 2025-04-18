import streamlit as st
import requests
from bs4 import BeautifulSoup
import feedparser
import time
import os
import hashlib

# ================== 配置区 ==================
NEWS_CONFIG = {
    "global_hot": {
        "url": "https://news.google.com/rss",
        "is_rss": True,
        "cache_time": 300  # 5分钟缓存
    },
    "medical_research": {
        "url": "http://www.nature.com/subject/medicine/rss",
        "is_rss": True
    },
    "chongqing_news": {
        "url": "http://www.cq.gov.cn/ywdt/jrcq/",
        "selector": ".news-list li a"
    }
}

# ================== 缓存系统 ==================
class NewsCache:
    def __init__(self):
        self.cache_dir = "/tmp/news_cache"  # Streamlit Cloud可写目录
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_cache_path(self, key):
        return os.path.join(self.cache_dir, f"{hashlib.md5(key.encode()).hexdigest()}.cache")
    
    def get(self, key):
        cache_file = self._get_cache_path(key)
        if os.path.exists(cache_file):
            if time.time() - os.path.getmtime(cache_file) < NEWS_CONFIG[key].get("cache_time", 300):
                with open(cache_file, 'r') as f:
                    return f.read()
        return None
    
    def set(self, key, data):
        with open(self._get_cache_path(key), 'w') as f:
            f.write(str(data))

# ================== 核心爬虫 ==================
def smart_crawler(key):
    cache = NewsCache()
    cached = cache.get(key)
    if cached: return eval(cached)
    
    config = NEWS_CONFIG[key]
    try:
        if config.get("is_rss"):
            feed = feedparser.parse(config['url'])
            data = [{'title': entry.title, 'link': entry.link} for entry in feed.entries[:20]]
        else:
            res = requests.get(config['url'], headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            data = [{'title': item.text.strip(), 'link': config['url']} for item in soup.select(config['selector'])[:20]]
        
        cache.set(key, data)
        return data
    except Exception as e:
        st.error(f"抓取失败: {str(e)}")
        return []

# ================== 界面渲染 ==================
def main():
    st.title("实时新闻监测系统")
    
    # 自动刷新控制
    if st.sidebar.button("立即刷新"):
        for key in NEWS_CONFIG:
            NewsCache().set(key, "")  # 清空缓存
    
    # 展示模块
    tab1, tab2, tab3 = st.tabs(["全球热点", "医药研究", "重庆新闻"])
    
    with tab1:
        st.subheader("全球20大热点新闻")
        data = smart_crawler('global_hot')
        for idx, item in enumerate(data[:20], 1):
            st.markdown(f"{idx}. [{item['title']}]({item['link']})")
    
    with tab2:
        st.subheader("最新医药成果")
        data = smart_crawler('medical_research')
        for item in data[:10]:
            st.markdown(f"- [{item['title']}]({item['link']})")
    
    with tab3:
        st.subheader("重庆政务动态")
        data = smart_crawler('chongqing_news')
        for item in data[:20]:
            st.markdown(f"- [{item['title']}]({item['link']})")

# ================== 自动刷新机制 ==================
if __name__ == "__main__":
    st_autorefresh = os.environ.get('AUTO_REFRESH')  # 外部触发用
    main()
    if st_autorefresh:
        time.sleep(300)  # 配合外部服务实现刷新

