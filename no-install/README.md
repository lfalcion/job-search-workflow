# No-install edition — for people who have never used a terminal, GitHub, or an AI agent

You need: a free [claude.ai](https://claude.ai) account, your current CV as a file, and about fifteen minutes. Nothing is installed on your computer.

## One-time setup (15 minutes)
1. **Sign in to claude.ai.** A free account works (free accounts can have up to five Projects). A paid plan gives more usage per day, which matters once you are tailoring several CVs a week.
2. **Turn on file creation.** Click your initials (bottom-left) → **Settings** → **Capabilities** → switch on **Code execution and file creation**. This is what lets Claude hand you a Word or PDF file instead of text to copy.
3. **Create a Project.** Left sidebar → **Projects** → **New project** → name it *My job search*.
4. **Paste the instructions.** In the project, open **Set project instructions** (or "Instructions" in the right-hand panel). Open [`project-instructions.md`](project-instructions.md) on GitHub, click the copy icon at the top of the file, paste everything into the instructions box, save.
5. **Upload your CV.** In the project's **Knowledge** panel click **+** and add your current CV (PDF or Word). Also add the small file [`tracker-template.md`](tracker-template.md) from this folder.
6. **Start a chat inside the project and type:** `setup`

Claude will read your CV, turn it into a complete "master CV" document, ask you a handful of questions (target job titles, where you can work, salary expectations, what you don't want), and hand you two files to download and add to the project's Knowledge: `master.md` and `profile.md`. Do that once. From then on:

## Daily use
- **Tailor a CV:** start a new chat in the project, paste the job description, type `tailor cv`. You get the fit assessment, any warnings (visa, salary, location), and a Word + PDF CV to download. The chat also gives you an updated `tracker.md`; replace the old one in Knowledge when you remember to.
- **Review an interview:** record the call on your phone (see below), copy the phone's transcript, paste it into a new chat in the project with one line of context ("Acme, hiring manager interview, 12 September"), type `review interview`. You get a scorecard, better answers built only from your real experience, and the three things to fix before the next round.
- **See where you stand:** type `status`.

## Recording and transcribing interviews with just your phone
Your phone already transcribes speech on the device. No app to buy.
- **iPhone 12 or newer, iOS 18 or newer:** record in **Voice Memos**. Afterwards open the recording → tap **•••** → **View Transcript**; to copy everything, tap **•••** → **Copy Transcript**. Transcription follows your phone's system language, so set it to the language of the interview beforehand. Supported languages include English, Spanish, French, German, Italian, Portuguese, Japanese, Korean and Chinese.
- **Google Pixel:** the **Recorder** app transcribes on-device. Long-press the recording → **Share** → **Transcript (.txt)**, or open it and copy the text.
- **Samsung Galaxy with Galaxy AI:** **Voice Recorder** → open the recording → **Transcript**, then share or copy the text.
- **Anything else:** any recorder app that produces a text transcript is fine. Paste the text.

Check the law where you are before recording a call; many places require that at least one participant consents, some require everyone's consent.

## What this edition cannot do
- No automatic history of every change; you keep the files Claude gives you.
- No local speech-to-text on your computer; you use your phone's.
- If you later want the full version (folder on your computer, automatic tracker, phone-to-PDF via GitHub), see the [desktop edition](../docs/desktop-edition.md) and the main [README](../README.md). Your `master.md` and `profile.md` move across unchanged.

## Privacy
Your CV, salary numbers and interview transcripts are in a Claude project under your account. Treat it like a private document. Do not share the project.
