# CampusFix AI

Campus reporting tool for maintenance and safety issues. Instead of reporting problems over WhatsApp or word of mouth, students and staff submit a photo + short description, and the app classifies it, sets a priority, checks for duplicates, and saves it as a ticket for facilities to handle.

The AI part works offline by default (rule-based vision + reasoning), and switches to Gemini for vision/reasoning when a `GEMINI_API_KEY` is provided.

Full docs and setup are in `campus-safety-assistant/campusfix-ai/README.md`.
