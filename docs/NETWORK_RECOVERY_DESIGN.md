# Network Gallery Recovery Design

**Project:** EO1-Museum  
**Status:** Proposed — not implemented  
**Current release:** v0.43.3  
**Baseline:** supplied `MainActivity.java` (snapshot 2026-11-08)  
**Target release:** TBD  
**Last updated:** 2026-11-08

## 1. Purpose and scope

The Electric Objects EO1 should behave like an unattended art frame even when the PC gallery server is stopped deliberately, restarted, temporarily unreachable, or serving a newly curated collection. A network interruption should not leave the display indefinitely blank, require an error-dialog response, or inadvertently replace the Internal Gallery.

This document specifies a proposed recovery policy for the **Network Gallery display**. It does not authorize automatic downloading of a new Internal Gallery collection. Existing local playback and Safe Sync protections should be preserved.

## 2. Current implementation (verified in MainActivity.java)

- On startup, the app probes the configured PC server for up to **5 seconds**; if unavailable, it switches to the Internal Gallery. It does not keep monitoring the server after this fallback.
- A successful Network Gallery page load calls `startNetworkSync()`. The `networkSyncStarted` flag prevents additional calls during the same process lifetime. This is a one-shot gate, not a collection-version check.
- `isNetworkGalleryReachable()` performs an HTTP GET of the gallery root and considers a 2xx–3xx response reachable. This does **not** establish that `images.js` and all media are valid.
- WebView's `onReceivedError()` is logged; the comment correctly notes that Android 4.4 may report subresource errors. There is no general post-load, continuous server-health/reconnect loop.
- Network MP4 playback has a 15-second preparation watchdog and falls back to the Internal Gallery after three consecutive video failures. This is **not** equivalent to detecting all server outages.
- Safe Sync reads `/eo1-status`, checks the configured trusted server ID and `SYNC=1`, reads `images.js`, limits base artworks to `MAX_MEDIA_FILES` (default **100**), estimates transfer sizes using HTTP HEAD, and requires `MIN_FREE_MB` (default **200**) free after staging.
- Safe Sync downloads a complete replacement collection into `images_new`, validates it, then swaps directory names while retaining the old gallery until activation succeeds. Existing recovery covers some interrupted swap states; it must not be assumed to handle every crash window.

These statements describe the supplied Java file, not the behavior of an independently verified running APK or PC server implementation.

## 3. Goals and non-goals

### Goals

1. Recover automatically from brief server interruptions while Network Gallery is selected.
2. Detect a changed gallery after a server restart, without assuming every restart changes the collection.
3. Fall back to a usable Internal Gallery after a prolonged outage.
4. Respect manual mode changes: the user must remain in control.
5. Keep Network Gallery reloads independent from Safe Sync and protect the existing local collection.
6. Provide concise, non-blocking on-screen status and useful diagnostic logs.
7. Stay compatible with Android 4.4.2 / API 19 and the EO1's constrained hardware.

### Non-goals

- Background polling after an intentional switch to Internal Gallery.
- Automatic return from Internal Gallery to Network Gallery when the PC server comes back.
- Replacing or downloading the Internal Gallery on every reconnection.
- Changing the gallery's image-display timing, local pan/MP4 behavior, or playback order.
- Treating a single missing image or video as proof that the whole server is down.

## 4. Proposed operating policy

The following are **initial design defaults**, subject to testing and confirmation:

| Parameter | Proposed default | Notes |
| --- | ---: | --- |
| Health-check interval | 10 seconds | Only while Network Gallery is active or recovering |
| Per-check timeout | 2 seconds | Network I/O on worker thread, never the UI thread |
| Outage grace period | 60 seconds | Measured with `SystemClock.elapsedRealtime()` |
| Successful checks to confirm recovery | 2 | Avoids reacting to a single transient success |
| Startup server wait | Existing 5 seconds | Keep existing behavior initially |
| Automatic return from Internal Gallery | Disabled | Manual selection only |
| Automatic Safe Sync on reconnection | Disabled by recovery mechanism | Separate, explicitly controlled operation |

An outage timer begins at the first confirmed failed health check. The app continues to retry while the grace period is active. If the server becomes healthy, the app reloads the Network Gallery only when necessary. If the grace period expires, it switches to Internal Gallery and stops monitoring.

## 5. Server health versus gallery readiness

These are different conditions:

- **Server reachable:** the configured server responds over HTTP.
- **Gallery ready:** the server can serve a valid gallery manifest (`images.js`) and the assets referenced by that manifest are in a consistent, publishable state.
- **Gallery changed:** a published gallery revision differs from the revision currently loaded by EO1.

A root-page HTTP 200 response alone is insufficient to prove readiness. Likewise, a temporary 404 while the PC operator is replacing files should not be treated as a permanent failure.

### Recommended PC-side contract (requires server changes)

Add a small endpoint such as `GET /eo1-gallery-status` returning machine-readable data, for example:

```json
{
  "ready": true,
  "gallery_revision": "2026-11-08T01:00:00Z-7c1f",
  "manifest": "images.js"
}
```

The response format and endpoint name are **proposals**, not currently verified server features. The PC server should publish a new revision only after its manifest and required media are ready. During collection replacement, it should report `ready: false` (or another explicitly documented temporary state). Avoid deriving revisions solely from process uptime: restarting an unchanged gallery should not trigger a needless reload.

For initial implementation without PC changes, a fallback probe may check the root page and `images.js`, but that cannot reliably distinguish an unchanged collection from a new one. Do not advertise full collection-change detection until a versioned readiness contract is implemented.

## 6. Proposed client state machine

| State | Entry condition | Behavior | Exit condition |
| --- | --- | --- | --- |
| `STARTUP_PROBE` | App launch | Existing bounded 5-second probe | Healthy → `NETWORK_ACTIVE`; otherwise → `LOCAL` |
| `NETWORK_ACTIVE` | Network Gallery ready | Play gallery; poll health/revision at low frequency | Failed checks → `NETWORK_RECOVERING`; revision changed → `NETWORK_RELOADING`; manual local → `LOCAL` |
| `NETWORK_RECOVERING` | Network failure after a working session | Keep last usable frame if possible; show brief status; retry without dialogs | Stable recovery → `NETWORK_ACTIVE` or `NETWORK_RELOADING`; 60-second outage → `LOCAL`; manual local → `LOCAL` |
| `NETWORK_RELOADING` | New ready revision detected | Reload WebView/manifest once; protect against overlapping reloads | Successful load → `NETWORK_ACTIVE`; load failure → `NETWORK_RECOVERING` |
| `LOCAL` | Manual choice, startup failure, or prolonged outage | Run Internal Gallery; stop Network Gallery polling | Explicit manual selection of Network Gallery |

### Manual mode selection has priority

Any manual change away from Network Gallery cancels pending health checks, delayed reloads, and recovery callbacks. A stale network response must not switch the app back to Network Gallery. Use a session/generation token to reject callbacks from an earlier mode session.

### Recovering a displayed artwork

Keep the last successfully rendered artwork visible where technically possible. A WebView page may already have unloaded assets or show a blank frame, so this is a **best-effort** behavior. A guaranteed last-frame fallback would require an explicit image cache or snapshot mechanism and is outside the initial implementation. After the grace period, prefer a functioning Internal Gallery to a blank Network Gallery.

## 7. Reloading a changed collection

1. Poll the server's readiness and revision from a background worker.
2. Ignore a revision while the server reports `ready: false`.
3. When the server reports a new ready revision, confirm it is stable and different from the last successfully loaded revision.
4. Allow any in-progress native network video to finish, or define a bounded interruption policy. **Proposed default:** defer reload until the video ends, with a timeout to avoid indefinite deferral.
5. Perform one controlled WebView reload, with appropriate cache handling for `index.html` and `images.js`.
6. Mark the revision active only after the page and its manifest have loaded successfully; avoid repeatedly reloading the same failed revision in a tight loop.
7. Do **not** trigger a Safe Sync solely because the gallery was reloaded.

If the PC server restarts but the revision is unchanged, continue normal playback without a forced reload unless the current page has become unusable.

## 8. Safe Sync must remain independent

The existing code invokes `startNetworkSync()` after `onPageFinished()`, and `networkSyncStarted` prevents a second attempt within the same process. This is insufficient as a long-term policy because a successful page reload and an authorized Internal Gallery update are separate events.

**Proposed separation:**

- **Network display recovery:** health checks, revision checks, WebView reload, and fallback. No file writes to the Internal Gallery.
- **Safe Sync:** an independently gated task, subject to the PC server's explicit `SYNC=1` request, trusted-server validation, size checks, free-space reserve, staging, and activation safeguards.
- Define when Safe Sync can be requested again (for example, a deliberate user action or a newly authorized server-side sync request). Do not simply clear `networkSyncStarted` on every page load.
- A failed Safe Sync must not interrupt Network Gallery playback or destroy the previous Internal Gallery.
- Keep the default `MAX_MEDIA_FILES=100` and `MIN_FREE_MB=200` unless the user deliberately changes configuration.

This separation will require a careful refactor of the current `onPageFinished()` / `startNetworkSync()` relationship. It should not be implemented by adding unconditional calls to `startNetworkSync()` during reconnection.

## 9. UI and logging

Use the existing non-blocking `syncStatusView` or a separate status channel, but ensure recovery notices do not overwrite active Safe Sync progress messages. Avoid modal dialogs for routine server restarts or intentional PC shutdowns.

Suggested messages:

- `PC Gallery connection lost — retrying...`
- `PC Gallery reconnected`
- `New collection detected — reloading...`
- `PC Gallery unavailable — switching to Internal Gallery`
- `Gallery reload failed — retrying...`

Logs should record: session/generation ID, state transition, failed URL or endpoint, HTTP status/exception, outage duration, detected revision, reload attempt/result, fallback reason, and whether the user changed modes manually. Do not log unnecessary repeated messages every 10 seconds.

## 10. Implementation plan

**Phase 1 — Client lifecycle and recovery**

- Introduce explicit network states and a generation token.
- Run bounded health probes on a background thread; post UI updates safely.
- Implement 60-second grace-period fallback and cancel work on manual mode change or Activity destruction.
- Prevent overlapping probes and reloads; avoid leaking threads or callbacks.
- Preserve existing MP4 watchdog and local playback behavior; reconcile the video-failure fallback with the new outage logic.

**Phase 2 — PC gallery publication contract**

- Add a readiness/revision endpoint to the PC server.
- Publish collections atomically or mark them not-ready during replacement.
- Ensure a revision represents content, not merely server uptime.
- Document cache behavior for `index.html`, `images.js`, and media paths.

**Phase 3 — Controlled reload and sync decoupling**

- Detect stable revision changes and reload only when necessary.
- Define safe reload timing around native MP4 playback.
- Separate Safe Sync authorization and one-shot lifecycle from WebView load events.
- Preserve existing staging, size verification, trusted-server, and minimum-free-space checks.

**Phase 4 — Validation on actual EO1 hardware**

- Test repeated interruptions and collection swaps under Android 4.4.2.
- Measure CPU, memory, UI responsiveness, and network traffic over prolonged operation.
- Verify that the app can remain unattended and that the Internal Gallery is never unintentionally replaced.

## 11. Acceptance test matrix

| Test | Expected result |
| --- | --- |
| Boot with PC server off | Existing 5-second fallback to Internal Gallery |
| Boot with PC server on | Network Gallery opens normally |
| Stop server for 15 seconds; restart unchanged | Retry and resume without modal dialog or local fallback |
| Stop server for over 60 seconds | Switch to Internal Gallery; stop polling |
| Restart server after local fallback | Remain in Internal Gallery until manual selection |
| Restart server with unchanged gallery revision | No unnecessary collection reload |
| Publish a new, ready collection | Detect new revision and reload Network Gallery once |
| Replace files while manifest is temporarily unavailable | Wait/retry; do not accept half-published collection |
| Server responds 200 but gallery is not ready | Do not treat root HTTP response alone as gallery readiness |
| Manually select Internal Gallery during recovery | Cancel retries; never jump back to Network Gallery |
| Network MP4 playing when revision changes | Apply defined deferred-reload policy without deadlock |
| Server requests no sync (`SYNC=0`) | No Internal Gallery download or replacement |
| Authorized Safe Sync with insufficient space | Reject sync and retain existing Internal Gallery |
| Authorized Safe Sync interrupted mid-transfer | Retain existing Internal Gallery; clean staging if possible |
| Repeated reconnect/reload cycles | No runaway threads, duplicate reloads, or persistent blank screen |

## 12. Open decisions

1. Confirm the proposed **10-second polling / 60-second fallback** defaults after real-device testing.
2. Decide whether a new revision should interrupt a long-running native MP4 or wait for completion (recommended: defer with a bounded timeout).
3. Define the exact server readiness/revision endpoint and atomic publication method.
4. Decide how an operator explicitly re-authorizes Safe Sync after the initial one-shot attempt.
5. Decide whether an optional last-frame cache is worth the complexity on EO1 hardware.

---

**Implementation note:** This document is a design proposal only. No Java or PC server code is changed by this document.
