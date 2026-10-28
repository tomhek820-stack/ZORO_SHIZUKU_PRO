# ZORO TELEGRAM ARCHIVER PRO

Telegram chat/channel exporter for Android + Termux. The Python tool uses your own Telegram account via Telethon and creates a local ZIP containing message data, an HTML viewer, and downloaded media.

## Important
- Export only conversations and media your account is authorized to access.
- Telegram API credentials are entered locally and are not uploaded by this project.
- The `.session` file contains login credentials: keep it private and never share it.
- Some chats may be unavailable due to Telegram permissions, deleted history, protected content, or API restrictions.
- This first version performs the export in Termux. The Android APK is a companion/setup dashboard; it does not bypass Telegram restrictions or independently extract other accounts' data.

## Install in Termux
1. Install Termux from a trusted source and open it.
2. Run:
   ```sh
   pkg update -y && pkg upgrade -y
   pkg install -y python git
   termux-setup-storage
   mkdir -p ~/zoro-telegram-archiver
   cd ~/zoro-telegram-archiver
   ```
3. Download the Python script and requirements from this repository's `telegram-archiver/` directory, or clone the repository and `cd telegram-archiver`.
4. Install dependencies:
   ```sh
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
5. Create API credentials at https://my.telegram.org/apps. Keep `api_id` and `api_hash` private.
6. Start the exporter:
   ```sh
   python zoro_telegram_archiver.py
   ```
7. Enter API ID, API hash, and your phone number when prompted. Enter the Telegram login code (and 2FA password if enabled) in Termux.
8. ZIP files are written to `~/storage/shared/ZORO_Telegram_Archives/` when shared storage is available; otherwise to `~/ZORO_Telegram_Archives/`.

## Export options
- Choose a dialog from your accessible private chats, groups, or channels.
- Choose all available messages or a date range.
- Download available media or export text/metadata only.
- Output ZIP contains `messages.json`, `index.html`, `media/`, and `manifest.json`.

## Android APK
The companion APK can be built from `android/` with Android Gradle Plugin and Java 17, or by the GitHub Actions workflow in `.github/workflows/telegram-archiver-android.yml`. It explains setup and opens Termux if installed. The Python exporter remains the engine for this version.

## Troubleshooting
- `API_ID_INVALID`: verify credentials from `my.telegram.org/apps`.
- Login code issues: run from an interactive Termux terminal; do not run the first login in a background task.
- `FloodWaitError`: wait the duration shown and retry; do not repeatedly restart rapidly.
- Missing media: check free storage and network access. Some protected or expired media cannot be downloaded.
- Keep session files private. To log out, stop the script and remove the local `*.session` file only if you intend to revoke that local session.

## Privacy
All exports are created locally. This tool does not upload chats or ZIP files to a server. Review the code before entering account credentials.