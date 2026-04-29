# Railway.app Deployment Guide

## Quick Setup (5 minutes)

### Prerequisites
- GitHub account with this repo connected
- Railway.app account (free tier available at https://railway.app)

### Steps

1. **Connect to Railway:**
   - Go to https://railway.app/dashboard
   - Click "New Project" → "Deploy from GitHub"
   - Select this repo
   - Railway auto-detects Streamlit and uses `Procfile`

2. **Environment Variables (optional):**
   - Railway automatically sets `$PORT` for you
   - No additional env vars needed for core app to work

3. **Wait for Deployment:**
   - Railway builds the Python environment
   - Installs `requirements.txt` automatically
   - Starts the app using `Procfile`
   - Takes ~2-3 minutes first time

4. **Access Your App:**
   - Railway gives you a public URL (e.g., `https://pdf-converse-production.up.railway.app`)
   - Share this link with evaluators

### Memory & Resources

- **Free Tier:** 8 GB shared monthly, 512 MB container RAM
- **If OOM Errors:** Upgrade to paid plan ($5/month) for dedicated resources
- **Optimization:** Our caching + memory-optimized indexing should fit comfortably in 512 MB

### Troubleshooting

**Blank screen on upload?**
- Check logs: Railway Dashboard → Your Project → Deployments → View Logs
- Monitor memory usage (Dashboard → Metrics)
- If OOM: Upgrade plan or reduce max PDF size

**Can't see logs?**
- Click "View Logs" in the Deployment panel
- Filter by recent timestamps
- Check for error stack traces

**Need to force rebuild?**
- Go to Deployments → Latest → Redeploy

### Git Push to Redeploy
Any push to `main` (or your connected branch) automatically triggers a new deployment.

---

## Alternative: Manual Procfile Testing

Test locally before deploying:

```bash
streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0
```

Then Railway runs the same command with `$PORT` substituted.
