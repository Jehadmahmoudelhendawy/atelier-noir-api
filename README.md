# Atelier Noir AI Concierge API

This is the serverless API backend for the Atelier Noir AI Concierge, optimized to run natively on **Vercel** with zero setup.

## Features
- **Irish English Tone**: Converses in warm, charming, and professional Irish English by default.
- **Color & Style Matchmaker**: Mentions and matches matching items in the catalog (e.g. matching navy suits with ties/pocket squares, matching beige suits with brown leather belts/shoes).
- **No Cold Starts**: Written in pure Node.js serverless functions with zero dependencies (using built-in fetch).
- **CORS Enabled**: Automatically handles cross-origin requests from any frontend.

## Project Structure
- `/api/chat.js`: The main serverless function endpoint.
- `products.json`: The product catalogue database (prices in €).

---

## How to Push to GitHub

Run these commands in your terminal inside the `atelier-noir-api` directory to push the code to your GitHub repository:

```bash
# Add all files
git add .

# Commit changes
git commit -m "Initialize Atelier Noir chatbot API with Irish English tone and Vercel compatibility"

# Push to your repository
git branch -M master
git push -u origin master
```

---

## How to Deploy on Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard) and click **"Add New"** > **"Project"**.
2. Import your repository **`atelier-noir-api`** from your GitHub account.
3. In the **Environment Variables** section, add your OpenRouter API key:
   - **Key**: `OPENROUTER_API_KEY`
   - **Value**: `sk-or-v1-...` (your actual OpenRouter API key)
4. Click **Deploy**.
5. Once deployed, copy your deployment domain URL (e.g., `https://atelier-noir-api.vercel.app`).
6. Update your frontend's `config.js` to point to the new Vercel API:
   ```javascript
   window.__CHAT_API__ = "https://your-project-name.vercel.app/api/chat";
   ```
