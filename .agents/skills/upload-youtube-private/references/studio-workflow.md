# Studio workflow verified on Lucas Academy

Verified with Codex’s in-app browser on 2026-11-21. Studio changes frequently; inspect the actual DOM before using a selector.

## Bootstrap and files

The bundled browser package exposes `scripts/browser-client.mjs` and `setupBrowserRuntime()`. Discover its installed path, import it through the persistent Node REPL, list browsers once, choose the advertised `iab` backend, and read `browser.documentation()`. Reuse the selected browser and tab handles. Do not inspect browser profile files or cookies.

For local four-block Desktop packages:

```bash
python scripts/prepare_upload.py --package '/absolute/path/to/package' --output '/absolute/path/to/upload-manifest.json'
```

Resolve the script path against the skill directory, not the project working directory. The helper expects `资料/播放与字幕数据.json` and reads each MP4, its SRT and the English/Chinese four-block metadata files. It checks ffprobe dimensions/duration, file hashes, metadata lengths and timed caption text. It does not send any files. For other package formats, prepare the same information from the explicitly supplied files instead of guessing filenames. Restrict the browser upload to the owner-authorized entries.

## Upload and English metadata

1. Verify the channel on the page, inspect Videos/Shorts for matching uploads, then use **Create → Upload videos → Select files**.
2. Start `tab.playwright.waitForEvent('filechooser')` before clicking Select files, then use the chooser’s `setFiles([absolutePath])`. Do not use unsupported `locator.setInputFiles`.
3. Wait for the actual upload dialog and title textbox. Scope form locators to that upload dialog: the underlying video page may contain identical textboxes and links. Fill the English title and description. Click the title field to blur the description before opening advanced settings.
4. **Do not blindly press Escape after typing hashtags.** A suggestions popup sometimes appears asynchronously. Without that popup, Escape can close the entire upload editor and leave a private draft. If this happens, use the upload panel’s **Edit video <filename>** or the existing draft in Content. Do not upload the file again.
5. Under **Show advanced settings**, enter the supplied tags separated by commas and commit with Enter. Verify the resulting tag chips. The current owner’s metadata uses lowercase hashtags even in Studio’s tags field. Preserve the project’s default tags and source attribution.
6. Inspect language, category, audience and disclosure controls. For these original-painting/real classical recording/deterministic 3D-gallery films: English labels, Education, established general-audience setting, no paid promotion, and no realistic AI-generated media. Other projects need their own factual answers.
7. Record the displayed video link/ID immediately. It exists before the final Save and is the duplicate-prevention anchor. Store processing/check status as observed, not inferred.
8. Open **Visibility**, check **Private**, verify it is checked, then Save. Wait for the editor to close. Verify the resulting edit page or Content row shows **Private**. Do not choose Unlisted, Public or a schedule.

Saving immediately after upload can open a **Video processing** dialog saying the private video is still processing SD. This is not an upload failure. Close that status dialog, continue with the existing video ID, and check processing again later. Do not resubmit the file or claim processing is complete merely because the byte upload reached 100%.

While SD is still processing, the edit page can show Visibility **Pending**, even after Private was selected and saved. Record this as pending, finish independent uploads or subtitle work, and recheck it before claiming the handoff is complete. Do not change it to Public to clear Pending.

## Chinese SRT and localized metadata

The upload wizard’s **Video elements → Subtitles → Add** opened the **English subtitles** editor for an English-language video. That is the source-language track; it is not the right place for a Chinese translation.

After saving the private video:

1. Open its edit page, then the sidebar **Languages** entry. Wait for **Add language**.
2. **Add language → Chinese (Simplified)** opens the language details dialog. Under **Media**, choose **Add** specifically in the **Subtitles / Manual subtitles** row, not Audio.
3. In **Chinese (Simplified) subtitles**, choose **Upload file → With timing → Continue**. Start the filechooser wait before Continue, then provide the matching `.zh-Hans.srt`.
4. Wait for the four expected caption textboxes (or the actual expected cue count). Check text and timing before saving. Timecode displays may use video frames rather than SRT milliseconds.
5. The subtitle dialog’s **Publish** button saves that subtitle track on the private video. Verify the language-scoped dialog before clicking it. It does not change the video’s visibility.
6. On the Languages table, confirm **Chinese (Simplified)** shows a published manual subtitle track. After saving localized metadata, wait for its own Published cell as well; the table can briefly show the prior state after the dialog closes.
7. If translated title/description are part of the supplied upload package, open the Chinese language details, fill them, and choose **Update**. Saving metadata before entering the subtitle editor avoids a **Save and continue?** interruption. If that interruption appears after editing, Save changes preserves the authorized translation.
8. Verify published subtitle/translation status and confirm the video still shows Private on its Details page or the final Content list.

## Evidence and handoff

Keep a receipt per file: local SHA-256, video ID, Studio edit URL, Private status, subtitle language/cue count/status, localized metadata status, processing quality and check notices. Do not resolve claims, remove music or delete videos without a separate request.

Save a screenshot of the final Content list showing the uploaded titles and Private visibility, and a language screenshot when useful. Include a screenshot in the final reply and keep the finished Studio tab as a deliverable. A local upload receipt must not contain cookies, tokens or other login material.
