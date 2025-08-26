import streamlit as st
import requests
import json
import os
from datetime import datetime, timedelta

# ---------------------------
# CONFIG
# ---------------------------
API_KEY = "AIzaSyBbeMjvsc_U1Y9zVPNHDdoR0lYobZAOYyI"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"
JSON_FILE = "trends.json"   # Storage file for results
CACHE_HOURS = 12            # How long to reuse saved results before refetching

st.title("📊 YouTube Viral Topics Tool with Trends Storage")

# ---------------------------
# USER INPUT
# ---------------------------
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)

keywords_input = st.text_area(
    "Enter keywords (comma separated):",
    "Reddit Update, AI Tools 2025, Investing for Beginners"
)
keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]

# ---------------------------
# FUNCTION: Check cache
# ---------------------------
def load_cached_results():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r") as f:
            data = json.load(f)
            last_saved = datetime.fromisoformat(data["timestamp"])
            if datetime.utcnow() - last_saved < timedelta(hours=CACHE_HOURS):
                return data["results"]
    return None

def save_results(results):
    with open(JSON_FILE, "w") as f:
        json.dump({"timestamp": datetime.utcnow().isoformat(), "results": results}, f, indent=2)

# ---------------------------
# FETCH DATA
# ---------------------------
if st.button("Fetch Data"):

    cached = load_cached_results()
    if cached:
        st.info("Loaded results from cache (no new API call).")
        all_results = cached
    else:
        try:
            start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
            all_results = []

            for keyword in keywords:
                st.write(f"🔎 Searching for keyword: **{keyword}**")

                search_params = {
                    "part": "snippet",
                    "q": keyword,
                    "type": "video",
                    "order": "viewCount",
                    "publishedAfter": start_date,
                    "maxResults": 5,
                    "key": API_KEY,
                }

                response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
                data = response.json()

                if "items" not in data or not data["items"]:
                    continue

                videos = data["items"]
                video_ids = [v["id"]["videoId"] for v in videos if "id" in v and "videoId" in v["id"]]
                channel_ids = [v["snippet"]["channelId"] for v in videos if "snippet" in v]

                if not video_ids or not channel_ids:
                    continue

                # Video stats
                stats_params = {"part": "statistics", "id": ",".join(video_ids), "key": API_KEY}
                stats_data = requests.get(YOUTUBE_VIDEO_URL, params=stats_params).json()

                # Channel stats
                channel_params = {"part": "statistics", "id": ",".join(channel_ids), "key": API_KEY}
                channel_data = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params).json()

                if "items" not in stats_data or "items" not in channel_data:
                    continue

                for video, stat, channel in zip(videos, stats_data["items"], channel_data["items"]):
                    title = video["snippet"].get("title", "N/A")
                    description = video["snippet"].get("description", "")[:200]
                    video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
                    published_at = video["snippet"].get("publishedAt", datetime.utcnow().isoformat())
                    views = int(stat["statistics"].get("viewCount", 0))
                    subs = int(channel["statistics"].get("subscriberCount", 0))

                    # Calculate velocity
                    published_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    days_old = max((datetime.utcnow() - published_date).days, 1)
                    view_velocity = views / days_old

                    # Viral Score
                    score = (view_velocity * 0.7) + ((views / (subs+1)) * 0.3)

                    if subs < 50000:  # Flexible sub filter
                        all_results.append({
                            "Title": title,
                            "Description": description,
                            "URL": video_url,
                            "Views": views,
                            "Subscribers": subs,
                            "ViewVelocity": round(view_velocity, 2),
                            "Score": round(score, 2),
                            "Keyword": keyword
                        })

            # Sort by Viral Score (descending)
            all_results = sorted(all_results, key=lambda x: x["Score"], reverse=True)

            # Save for later use
            save_results(all_results)

        except Exception as e:
            st.error(f"❌ An error occurred: {e}")
            all_results = []

    # ---------------------------
    # DISPLAY RESULTS
    # ---------------------------
    if all_results:
        st.success(f"✅ Found {len(all_results)} results!")
        for result in all_results:
            st.markdown(
                f"**Title:** {result['Title']}  \n"
                f"**Description:** {result['Description']}  \n"
                f"**Keyword:** {result['Keyword']}  \n"
                f"**URL:** [Watch Video]({result['URL']})  \n"
                f"**Views:** {result['Views']}  \n"
                f"**Subscribers:** {result['Subscribers']}  \n"
                f"**Velocity (views/day):** {result['ViewVelocity']}  \n"
                f"**Viral Score:** {result['Score']}"
            )
            st.write("---")
    else:
        st.warning("⚠️ No results found for the given keywords.")
