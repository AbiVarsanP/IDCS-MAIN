

def analyze_text_with_perplexity(text: str) -> dict:
    """
    Enhanced sentiment analysis using Perplexity API.
    Returns: {
        'sentiment_label': str,  # Very Positive, Positive, Neutral, Negative, Very Negative
        'sentiment_score': float,  # 0-1
        'emotion_label': str,     # joy, frustration, confusion, motivation
        'aspect_scores': dict     # clarity, interaction, punctuality, fairness
    }
    If API fails or key missing, returns Neutral/0.0 and empty aspects.
    """
    import os
    import requests
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("[Analyzer] PERPLEXITY_API_KEY not set. Using TextBlob fallback.")
        return textblob_sentiment(text)
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    prompt = (
        "Classify the sentiment of this text as one of: Very Positive, Positive, Neutral, Negative, Very Negative. "
        "Also, extract the main emotion (joy, frustration, confusion, motivation). "
        "Return JSON: {\"sentiment_label\": <label>, \"sentiment_score\": <0-1>, \"emotion_label\": <emotion>}\nText: " + text
    )
    payload = {
        "model": "pplx-7b-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        import json as _json
        # Try to extract JSON from the response content
        try:
            result = _json.loads(content)
        except Exception:
            import re
            match = re.search(r'\{.*\}', content)
            if match:
                result = _json.loads(match.group(0))
            else:
                print(f"[Analyzer] Could not parse JSON from API response: {content}")
                return {
                    "sentiment_label": "Neutral",
                    "sentiment_score": 0.0,
                    "emotion_label": "",
                    "aspect_scores": aspect_sentiment_stub(text)
                }
        sentiment_label = result.get("sentiment_label", "Neutral")
        sentiment_score = float(result.get("sentiment_score", 0.0))
        emotion_label = result.get("emotion_label", "")
        return {
            "sentiment_label": sentiment_label,
            "sentiment_score": sentiment_score,
            "emotion_label": emotion_label,
            "aspect_scores": aspect_sentiment_stub(text)
        }
    except Exception as e:
        print(f"[Analyzer] Exception during API call: {e}. Using TextBlob fallback.")
        return textblob_sentiment(text)


def textblob_sentiment(text: str) -> dict:
    try:
        from textblob import TextBlob
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        # Map polarity to label and score
        if polarity > 0.3:
            label = "Positive"
        elif polarity < -0.3:
            label = "Negative"
        else:
            label = "Neutral"
        score = abs(polarity)
        return {
            "sentiment_label": label,
            "sentiment_score": score,
            "emotion_label": "",
            "aspect_scores": aspect_sentiment_stub(text)
        }
    except Exception as e:
        print(f"[Analyzer] TextBlob fallback failed: {e}")
        return {
            "sentiment_label": "Neutral",
            "sentiment_score": 0.0,
            "emotion_label": "",
            "aspect_scores": aspect_sentiment_stub(text)
        }


def aspect_sentiment_stub(text: str) -> dict:
    """
    Simple keyword-based aspect sentiment stub for clarity, interaction, punctuality, fairness.
    Returns a dict of aspect: score (0-1)
    """
    aspects = {
        'clarity': ["clear", "confusing", "understand", "explain"],
        'interaction': ["interactive", "questions", "discussion", "engage"],
        'punctuality': ["late", "on time", "punctual", "delay"],
        'fairness': ["fair", "biased", "partial", "unfair"]
    }
    text_lower = text.lower()
    aspect_scores = {}
    for aspect, keywords in aspects.items():
        score = 0.0
        for kw in keywords:
            if kw in text_lower:
                score += 0.25
        aspect_scores[aspect] = min(score, 1.0)
    return aspect_scores
