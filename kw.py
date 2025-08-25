import streamlit as st

import requests

from datetime import datetime, timedelta


# YouTube API Key

API_KEY = "AIzaSyBbeMjvsc_U1Y9zVPNHDdoR0lYobZAOYyI"

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"

YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"


# Streamlit App Title
st.title("🔥 YouTube Viral + High RPM Topics Tool")

# Input Fields
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)

# Expanded keyword list (viral + high RPM niches)
keywords = [
    # Viral Reddit/Story niches
    "Affair Relationship Stories", "Reddit Update", "Reddit Relationship Advice", 
    "Reddit Cheating", "AITA Update", "Open Marriage", "Cheating Story Real", 
    "Reddit Surviving Infidelity",

    # High RPM niches
    "Side Hustle 2025", "Make Money Online", "Investing for Beginners", 
    "Credit Card Hacks", "AI Tools 2025", "ChatGPT Hacks", "SaaS Review", 
    "Freelancer Income", "Small Business Tips", "Digital Marketing Strategy"
]

# Fetch Data Button
if st.button("Fetch Data"):
    try:
        # Calculate date range
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"

        all_results = []

        # Iterate over the list of keywords
        for keyword in keywords:
            st.write(f"🔎 Searching for keyword: {keyword}")

            # Define search parameters
            search_params = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "order": "viewCount",
                "publishedAfter": start_date,
                "maxResults": 5,
                "key": API_KEY,
            }

            # Fetch video data
            response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
            data = response.json()

            if "items" not in data or not data["items"]:
                continue

            videos = data["items"]
            video_ids = [video["id"]["videoId"] for video in videos if "id" in video and "videoId" in video["id"]]
            channel_ids = [video["snippet"]["channelId"] for video in videos if "snippet" in video and "channelId" in video["snippet"]]

            if not video_ids or not channel_ids:
                continue

            # Fetch video statistics
            stats_params = {"part": "statistics,snippet", "id": ",".join(video_ids), "key": API_KEY}
            stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
            stats_data = stats_response.json()

            # Fetch channel statistics
            channel_params = {"part": "statistics", "id": ",".join(channel_ids), "key": API_KEY}
            channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
            channel_data = channel_response.json()

            if "items" not in stats_data or "items" not in channel_data:
                continue

            stats = stats_data["items"]
            channels = channel_data["items"]

            # Collect results
            for video, stat, channel in zip(videos, stats, channels):
                title = video["snippet"].get("title", "N/A")
                description = video["snippet"].get("description", "")[:200]
                video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"

                views = int(stat["statistics"].get("viewCount", 0))
                likes = int(stat["statistics"].get("likeCount", 0)) if "likeCount" in stat["statistics"] else 0
                comments = int(stat["statistics"].get("commentCount", 0)) if "commentCount" in stat["statistics"] else 0

                subs = int(channel["statistics"].get("subscriberCount", 0))
                published_at = stat["snippet"].get("publishedAt", None)

                # Calculate days since upload
                if published_at:
                    upload_time = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
                    days_old = max((datetime.utcnow() - upload_time).days, 1)  # avoid division by zero
                else:
                    days_old = 1

                # Viral metrics
                view_velocity = views / days_old  # views per day
                engagement_ratio = (likes + comments) / views if views > 0 else 0
                views_per_sub = views / subs if subs > 0 else views

                # RPM weight (simple heuristic)
                rpm_keywords = ["finance", "investing", "money", "business", "AI", "marketing", "SaaS"]
                rpm_weight = 2 if any(word.lower() in title.lower() for word in rpm_keywords) else 1

                # Scoring formula
                score = (view_velocity * engagement_ratio * rpm_weight) + views_per_sub

                # Filter: only channels under 50k subs
                if subs < 50000:
                    all_results.append({
                        "Title": title,
                        "Description": description,
                        "URL": video_url,
                        "Views": views,
                        "Subscribers": subs,
                        "View Velocity": round(view_velocity, 2),
                        "Engagement": round(engagement_ratio, 4),
                        "Views/Sub": round(views_per_sub, 2),
                        "Score": round(score, 2),
                        "Keyword": keyword
                    })

        # Sort by score
        all_results = sorted(all_results, key=lambda x: x["Score"], reverse=True)

        # Display results
        if all_results:
            st.success(f"✅ Found {len(all_results)} viral trend results!")
            for result in all_results:
                st.markdown(
                    f"**Title:** {result['Title']}  \n"
                    f"**Keyword:** {result['Keyword']}  \n"
                    f"**Description:** {result['Description']}  \n"
                    f"**URL:** [Watch Video]({result['URL']})  \n"
                    f"**Views:** {result['Views']}  \n"
                    f"**Subscribers:** {result['Subscribers']}  \n"
                    f"**View Velocity (views/day):** {result['View Velocity']}  \n"
                    f"**Engagement Ratio:** {result['Engagement']}  \n"
                    f"**Views per Subscriber:** {result['Views/Sub']}  \n"
                    f"**🔥 Viral Score:** {result['Score']}"
                )
                st.write("---")
        else:
            st.warning("No results found for the given filters.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
