---
name: upload-youtube-private
description: Upload owner-authorized videos and timed subtitles to YouTube Studio through Codex’s in-app browser, saving as Private for the owner to publish. Use for upload-only or unpublish handoffs, including Lucas Academy Desktop upload packages.
---

# Upload YouTube Private

Deliver an uploaded, reviewable video with its metadata and correctly labelled subtitle tracks. A request to upload while the owner will publish means **Private**, with no schedule. This skill does not authorize uploading other files, publishing, deleting existing videos, changing channel settings, or disputing copyright claims.

## Prepare the actual upload

Read the project’s upload conventions and the final local package. Use the final revised export, not a superseded copy. Match the video, title, description, tags and SRT by their common stem. For the Lucas Academy four-block metadata format, [scripts/prepare_upload.py](scripts/prepare_upload.py) checks the package and produces a local manifest; it never uploads anything.

Read [references/studio-workflow.md](references/studio-workflow.md) for the UI flow verified in this environment, including the separate Chinese-subtitle path. Treat button names as examples and use fresh page evidence when Studio changes.

## Operate the requested browser

Use the available Browser plugin runtime through `mcp__node_repl.js`. Select the advertised **in-app browser** when requested, reuse its handle, and read its returned documentation. Do not silently switch to Chrome, extract browser credentials, use undocumented YouTube endpoints, or bypass a browser security rejection.

Verify the visible channel before sending files. For Lucas Academy, the owner-confirmed channel is `UCtn9_kNupjZvWAJVOqWUbYw`; verify its displayed name as well. Check the relevant content list for an existing matching upload. A delayed form or ambiguous result is a reason to inspect the existing draft, not to submit a duplicate.

An explicit request to upload the named package to the channel authorizes that upload. Do not ask again merely because the action sends the authorized video files. Apply the active browser’s confirmation policy if a materially different action becomes necessary. If authentication needs user interaction, keep rendering/preparation work moving while requesting that interaction.

## Save and verify

Fill the supplied metadata and preserve source attributions. Use the visible audience, disclosure, category and language controls based on the actual content and owner’s established settings; do not infer child-directed content from an education category, or synthetic media from AI-assisted coding alone.

Choose **Private**, verify it is checked, and save. Attach translation SRTs under their actual language. The upload wizard’s subtitle button may open only the source-language editor: never put Chinese text under English to complete the task faster.

A subtitle editor’s **Publish** button applies to that subtitle track; it can make the track available on an already-private video. Confirm the dialog’s language and scope, then verify the video itself remains Private. Do not click the video’s Public/Publish or Schedule controls for an upload-only task.

Record each video’s ID/edit link, final local file hash, visibility, subtitle language/status and processing/check results. Save a screenshot showing the completed result and include a screenshot in the final reply. Report platform claims or pending processing exactly as shown; do not promise copyright clearance. Keep the finished Studio tab as a deliverable and leave publication to the owner.
