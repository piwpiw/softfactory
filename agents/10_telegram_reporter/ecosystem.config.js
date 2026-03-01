/**
 * pm2 ecosystem config — Sonol-Bot (Telegram Reporter)
 * Run: pm2 start ecosystem.config.js
 * Keep alive 24/7 with auto-restart on crash.
 */

module.exports = {
  apps: [
    {
      name: process.env.PM2_APP_NAME || "sonol-bot",
      script: "reporter_agent.py",
      interpreter: "python",
      args: "--listen",
      watch: false,
      autorestart: true,
      restart_delay: 5000,
      max_restarts: 10,
      env: {
        NODE_ENV: "production",
      },
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      out_file: "../../logs/sonol-bot-out.log",
      error_file: "../../logs/sonol-bot-error.log",
      merge_logs: true,
    },
  ],
};
