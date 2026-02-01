# API Setup Guide - Sports Prediction Framework

This guide walks you through obtaining API keys for the three recommended sports data APIs.

---

## 1. API-SPORTS (Primary - Recommended)

**Website:** https://api-sports.io

### Step-by-Step:

1. **Visit the website**
   - Go to https://api-sports.io
   - Click "Register" or "Sign Up" in the top right

2. **Create an account**
   - Enter your email address
   - Create a password
   - Verify your email

3. **Subscribe to Free Plan**
   - After logging in, go to "My Account" or "Dashboard"
   - Look for "Tennis API" (or "All Sports API")
   - Click "Subscribe" on the **Free Plan**
   - Free tier includes: **100 requests/day**

4. **Get your API Key**
   - Go to "Dashboard" or "My Account"
   - Find section labeled "API Key" or "Credentials"
   - Copy your API key (format: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

5. **Important Endpoints for Tennis:**
   - Base URL: `https://v1.tennis.api-sports.io`
   - Players: `/players`
   - Rankings: `/rankings`
   - Head-to-Head: `/h2h`
   - Matches: `/games`

### Add to .env file:
```bash
API_SPORTS_KEY=your_actual_api_key_here
API_SPORTS_BASE_URL=https://v1.tennis.api-sports.io
```

---

## 2. RapidAPI - Tennis API (Matchstat)

**Website:** https://rapidapi.com

### Step-by-Step:

1. **Visit RapidAPI**
   - Go to https://rapidapi.com
   - Click "Sign Up" (top right)

2. **Create account**
   - Sign up with email or Google/GitHub
   - Verify your email

3. **Find Tennis API**
   - Search for "Tennis Live Data" or "Ultimate Tennis"
   - Popular options:
     - **"Ultimate Tennis API"** by Matchstat
     - **"Tennis Live Data"** by Live Sports API
   - Click on the API you want

4. **Subscribe to Free Plan**
   - Click "Subscribe to Test" button
   - Select **"Basic Plan"** (usually free)
   - Free tier typically includes: **500-1000 requests/month**

5. **Get your API Key**
   - After subscribing, you'll see "Code Snippets" section
   - Look for the header `x-rapidapi-key`
   - Copy the key (format: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
   - Also note the `x-rapidapi-host` value

### Add to .env file:
```bash
RAPIDAPI_KEY=your_actual_rapidapi_key_here
RAPIDAPI_HOST=ultimate-tennis1.p.rapidapi.com
```

---

## 3. Stevegtennis.com API (Backup)

**Website:** https://www.stevegtennis.com

### Step-by-Step:

1. **Visit the website**
   - Go to https://www.stevegtennis.com
   - Look for "API" or "Developer" section in the footer

2. **Request API Access**
   - Currently, this site may not have a public self-service API signup
   - You may need to:
     - Contact them directly via email
     - Or use their free web scraping-friendly pages
   - Check their Terms of Service for data usage

3. **Alternative: Web Scraping (if allowed)**
   - If they don't offer an API, you might use their public data
   - Always check `robots.txt` and Terms of Service first
   - Be respectful with request rates

### Add to .env file (if API available):
```bash
STEVEGTENNIS_API_KEY=your_actual_key_here
STEVEGTENNIS_BASE_URL=https://api.stevegtennis.com
```

---

## Complete .env File Template

Once you have your keys, your `.env` file should look like this:

```bash
# API-SPORTS (Primary)
API_SPORTS_KEY=your_api_sports_key_here
API_SPORTS_BASE_URL=https://v1.tennis.api-sports.io

# RapidAPI (Secondary)
RAPIDAPI_KEY=your_rapidapi_key_here
RAPIDAPI_HOST=ultimate-tennis1.p.rapidapi.com

# Stevegtennis (Backup)
STEVEGTENNIS_API_KEY=your_stevegtennis_key_here
STEVEGTENNIS_BASE_URL=https://api.stevegtennis.com

# Database
DB_PATH=./data/predictions.db

# Environment
ENVIRONMENT=development
```

---

## Testing Your API Keys

After setting up your keys, test them:

### 1. API-SPORTS Test:
```bash
curl -X GET "https://v1.tennis.api-sports.io/rankings/atp?date=2024-01-01" \
  -H "x-rapidapi-key: YOUR_API_SPORTS_KEY"
```

### 2. RapidAPI Test:
```bash
curl -X GET "https://ultimate-tennis1.p.rapidapi.com/players" \
  -H "x-rapidapi-key: YOUR_RAPIDAPI_KEY" \
  -H "x-rapidapi-host: ultimate-tennis1.p.rapidapi.com"
```

---

## Important Notes

### Rate Limits:
- **API-SPORTS**: 100 requests/day (free tier)
- **RapidAPI**: 500-1000 requests/month (varies by API)
- Our caching system helps stay within these limits

### Best Practices:
1. **Never commit your .env file to git** (already in .gitignore)
2. **Start with API-SPORTS** as primary source
3. **Use RapidAPI as fallback** when primary fails or rate limited
4. **Cache aggressively** to minimize API calls

### Cost Considerations:
- All three offer free tiers suitable for development
- If you need more requests, paid plans are available:
  - API-SPORTS: ~$15-30/month for 1000+ requests/day
  - RapidAPI: ~$10-50/month depending on the specific API

---

## Troubleshooting

### "401 Unauthorized" Error:
- Double-check your API key is correct
- Ensure no extra spaces in .env file
- Verify the API key is active (not expired)

### "429 Rate Limit Exceeded":
- You've hit your daily/monthly limit
- Wait for the limit to reset (usually 24 hours)
- Use cached data in the meantime
- Consider upgrading to paid tier if needed

### "403 Forbidden":
- API endpoint might not be available on free tier
- Check API documentation for free tier limitations
- Try a different endpoint

---

## Next Steps

After obtaining your API keys:
1. ✅ Save them to `.env` file
2. ✅ Test each API with curl commands above
3. ✅ Update code to load from environment variables
4. ✅ Run integration tests
5. ✅ Start fetching real tennis data!
