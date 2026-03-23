# FFmpeg Reel Generator

Free Instagram Reel generator using FFmpeg. Deploy on Railway.

## Deploy
1. Push this repo to GitHub
2. Connect to Railway → Deploy
3. Copy your Railway public URL

## API
POST /generate
{
  "topic": "AI in 2026",
  "caption": "Caption text with #hashtags",
  "script": "30 second reel script..."
}

Returns:
{
  "video_url": "https://your-app.railway.app/video/abc123"
}
