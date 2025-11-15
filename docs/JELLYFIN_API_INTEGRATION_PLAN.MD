# Document: Jellyfin API Integration Strategy & Implementation Plan

---

## Part 1: The Value and Purpose of the Jellyfin API

This section addresses the core questions: "What is the value and purpose of the Jellyfin API? What can it do? How is it useful? Is it...badass? Or a pile of garbage."

### What is it?
The Jellyfin API is a **RESTful API** that works over your network (HTTP/HTTPS). Think of it as the "back door" to your Jellyfin server. It's the programmatic interface that the official Jellyfin web-ui and mobile apps use to get information and tell the server what to do.

### What can it do?
Anything you can do in the web interface, you can do with the API. This includes:
* **Reading Data:** Get a complete list of all libraries, movies, shows, episodes, and their metadata.
* **Querying Items:** Find specific items, check their media streams (like subtitle tracks), and read their technical details.
* **Triggering Actions:** Tell the server to **refresh a library**, scan for new files, or refresh the metadata for a single item.
* **Managing Content:** Create or delete collections, manage playlists, and update metadata.
* **Managing Users & Stats:** Get playback statistics, see who is watching what, and manage user accounts.

### How is it useful?
Its usefulness comes down to two key concepts:
1.  **Automation:** This is the core of your "JellyRancher" application. Instead of you manually clicking "Scan Library" after adding files, your application can make an API call to do it instantly and automatically.
2.  **Integration:** The API is what allows the entire ecosystem of media tools to "talk" to Jellyfin. This is how Sonarr, Radarr, and Trakt are able to connect and update your library, mark shows as watched, etc.

### The Verdict: Is it badass or garbage?
It is **absolutely badass**. It's not a poorly documented afterthought; it is the fundamental engine that makes Jellyfin so powerful and extensible. The fact that your application can so deeply integrate with it is a testament to its excellent design.

---

## Part 2: API Integration in the Application Workflow

This section breaks down how the API can be used at *each stage* of the workflow you defined in your "Application Proposal."

### Step 1: Scan Folder List
* **API Action:** `GET /Items?Recursive=true&IncludeItemTypes=Movie,Episode&Fields=Path`
* **Purpose:** Before the tool even starts, it queries the Jellyfin database. This allows it to **cross-reference** your local file list against what Jellyfin *already* knows about.
* **Value-Add:**
    * Immediately identifies files that are already in the library.
    * Flags "orphaned" files (files Jellyfin has in its database but are missing from your disk).
    * Flags "new" files (files on your disk that Jellyfin has never seen).

### Step 2: Summarize Structure
* **API Action:** `GET /Views` or `GET /UserViews`
* **Purpose:** To get a high-level summary of the *current* library structure *as Jellyfin sees it*.
* **Value-Add:** This provides the "before" snapshot for the LLM. The AI can then compare its proposed "after" state to the "before" state from the API, leading to a much more intelligent reorganization plan.

### Step 3: Submit to LLM for Proposal
* **API Action:** `GET /Items/{itemId}?Fields=ProviderIds`
* **Purpose:** To get existing metadata (like TMDb or TVDB IDs) for items that were matched in Step 1.
* **Value-Add:** You feed this information *to* the LLM. The prompt becomes, "Here is a messy folder. By the way, I already know this folder contains `Movie (1999)` with TMDb ID `12345`. Please organize it." This prevents the LLM from guessing and ensures it uses the *correct* canonical data.

### Step 4: Build Canonical Database
* **API Action:** `POST /Items/{itemId}/Refresh`
* **Purpose:** This is a "test" or "check" action. As your tool generates NFO files (like for multi-part episodes), it can place one in a test folder and poke this API endpoint.
* **Value-Add:** This allows the tool to **verify its NFO files work** by asking Jellyfin to read it and then checking if the metadata updated correctly, all before rolling it out to your whole library.

### Step 5: Produce Editable Table for Review
* **API Action:** (No new API call, this uses data from Step 1)
* **Purpose:** To display the Jellyfin-related data in the review table.
* **Value-Add:** The user's table will have columns like "Jellyfin Status" with values like "Already in Library" or "New," all based on the data pulled from the API in the first step.

### Step 6: Execute Reorganization Plan
* **API Action 1:** `POST /Libraries/{libraryId}/Refresh`
* **Purpose:** This is the most critical API call. After your tool moves, renames, or deletes a file, it **must** tell Jellyfin to update itself.
* **Value-Add:** Instead of waiting for a slow, scheduled daily scan, your tool can trigger a targeted refresh *the instant* the file operation is complete. This makes the change appear in your library immediately.

* **API Action 2:** `POST /Collections/{collectionId}/Items`
* **Purpose:** To programmatically create new collections (e.g., "Star Wars Collection") and add the correct movies to it.
* **Value-Add:** This is pure automation. The LLM can propose a new collection, and your tool can create it and populate it via the API without you ever opening the web UI.

### Step 7: Evaluate Subtitle Coverage
* **API Action:** `GET /Items/{itemId}?Fields=MediaStreams`
* **Purpose:** To get server-side validation of subtitle tracks.
* **Value-Add:** This is far more reliable than just running `ffprobe` locally. This asks Jellyfin, "What subtitle streams do *you* see for this item?" This confirms not only that the file exists, but that Jellyfin has successfully processed and recognized it.

### Step 8: Obtain Subtitles
* **API Action:** `POST /Items/{itemId}/Refresh`
* **Purpose:** After your tool (using `subliminal`) downloads a new `.srt` file and places it next to the video file, it needs to tell Jellyfin to look again.
* **Value-Add:** This API call "nudges" Jellyfin to find the new subtitle file immediately, making it available for playback right away.

---

## Part 3: Remote vs. Local Access

You are correct: **Remote access is 100% possible.**

The API is just a web server. To connect, your application only needs two things:
1.  **The Server Address:** `http://localhost:8096` (if on the same machine) or `https://my-jellyfin-domain.com` (if on a remote server).
2.  **An API Key:** You generate this in your Jellyfin Dashboard (Admin > Advanced > API Keys).

As long as the machine running your "JellyRancher" application has network access to the server's address and has a valid API key, it can perform all these actions, whether the server is on the same computer or in a data center.

---

## Part 4: Recommended Integration Plan (Implementation)

Given that you have implemented Steps 1-4, the ideal time to integrate the API is **right now**, before you finalize Step 5 (the editable review table).

### The Rationale: Context vs. Action

You can think of the API integration in two phases:
1.  **Phase 1: Context (Read-Only).** Get the *current state* of the Jellyfin server.
2.  **Phase 2: Action (Read-Write).** *Tell* the Jellyfin server to do things (like refresh).

Your application's "brain" (the LLM in Step 3 and the database in Step 4) is currently "flying blind." It's making a plan based *only* on the file system. To make your application truly intelligent, it *must* have the "Phase 1" context *before* it even talks to the LLM.

### Recommended Integration Plan

Here is how you can retrofit the API into your existing work.

#### 1. Retrofit Your "Scan" (Steps 1-2)
Before you do anything else, your *very first action* should be to connect to the Jellyfin API and pull a complete list of all media items and their paths.

* **Action:** Use the API to get all items and their metadata (especially `ProviderIds` like TMDb/TVDB IDs and `Path`).
* **Result:** You now have a "Jellyfin-Aware File List" instead of a "Dumb File List." You can immediately cross-reference this with your local file scan.

#### 2. Enhance Your "Proposal" (Steps 3-4)
Now that you have this data, you can make your LLM proposal (Step 3) and canonical database (Step 4) infinitely smarter.

* **Action (Step 3):** When you send data to the LLM, you'll now include the Jellyfin data. Instead of saying, "Here's a folder named 'Star Trek TNG'," you'll say, "Here's a folder named 'Star Trek TNG' which **Jellyfin has already identified** as TVDB ID `71470`."
* **Action (Step 4):** When building your canonical database, you'll use the API data as the *primary source of truth*. If Jellyfin already has the correct TMDb ID, you don't need to guess or ask the LLM—you just use it. This saves you API calls to TMDB/TVDB and is 100% accurate.

#### 3. Build Your "Review Table" (Step 5) with Full Context
This is your current step and the payoff for doing the work above. Because you gathered the API context in Step 1, your editable table becomes far more powerful.

You can now add new, critical columns like:
* **`JellyfinStatus`**: (e.g., "New," "Already in Library," "Path Mismatch")
* **`CurrentTMDbID`**: (The ID Jellyfin *thinks* this item has)
* **`ProposedTMDbID`**: (The ID your canonical database *wants* it to have)
* **`ActionType`**: (e.g., "Move," "Move + Refresh Metadata," "Delete Orphan")

### The "Action" Phase (Steps 6-8)

By integrating now, you *also* set yourself up for the "Phase 2" action steps.

* **When you get to Step 6 (Execute):** You will already have the `itemId` for every file. After you move a file, you can immediately make a *targeted* API call to `POST /Items/{itemId}/Refresh` instead of triggering a slow, full-library scan.
* **When you get to Steps 7 & 8 (Subtitles):** You will use `GET /Items/{itemId}?Fields=MediaStreams` to check for subs, and `POST /Items/{itemId}/Refresh` to make Jellyfin see the new ones you download.

### Your First Step: Get a Client

You'll need a Python library to talk to the API. The most common one is `jellyfin-apiclient-python`.

```bash
pip install jellyfin-apiclient-python