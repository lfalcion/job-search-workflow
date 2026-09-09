# Desktop edition — no GitHub account, no terminal

For people who are comfortable installing an app and downloading a file, but have never used a terminal or GitHub. You need a paid Claude plan (Pro or Max) because the Claude Code desktop app requires one; if you want a free path, use the [no-install edition](../no-install/README.md).

## 1. Download the workflow (2 minutes)
1. Open https://github.com/lfalcion/job-search-workflow in your browser. No account needed.
2. Click the green **Code** button → **Download ZIP**.
3. Unzip it. You get a folder called `job-search-workflow-main`. Rename it to `job-search` and move it somewhere you keep documents — ideally inside your iCloud Drive, OneDrive or Google Drive folder so it is backed up automatically.

## 2. Install the Claude Code desktop app (5 minutes)
1. Download it from https://code.claude.com/docs/en/desktop (macOS, Windows; Linux beta) and install.
2. **Windows only:** the app needs *Git for Windows*. If it asks, install it from https://git-scm.com/downloads/win, then restart the app. (Git is only used to keep a history of your files; you never type git commands.)
3. Open the app, sign in with your Claude account, click the **Code** tab.

## 3. Point it at your folder and type one word (10–20 minutes)
1. In the Code tab: **Environment** → *Local*. **Project folder** → choose the `job-search` folder you made. Leave the model and permission mode as suggested.
2. Type `setup` and press Enter.

The assistant checks your computer and explains what it found in plain words, asks permission before installing anything, asks for your current CV (drag the file into the chat or paste the text), turns it into your master CV, asks a few questions about what you are looking for, and finishes by telling you the two phrases you will use from then on.

If it offers to create a GitHub repository, you can say no. Your folder works fine on its own; the cloud-drive folder is your backup.

## 4. Daily use
- **Tailor a CV:** save the job description as a text file in the `jds` folder (or just paste it into the chat) and type `tailor cv`. The PDF appears in the `output` folder.
- **Review an interview:** record on your phone. Either copy the phone's own transcript (iPhone Voice Memos: **•••** → **Copy Transcript**; Pixel Recorder: share transcript) into a text file in `interviews/inbox`, or copy the audio file there if you let `setup` install the speech tools. Then type `review interview` and name the company and stage.
- **Where am I:** type `status`.

## When something goes wrong
Type what you see into the chat. The assistant can run the checks itself (`setup_check`) and fix most things. If it says something needs a new terminal window after an install, close and reopen the app.
