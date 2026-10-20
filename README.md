# Motion Texture Studio — midterm proposal (resubmit)

An upgrade to my Week 5 **Texture GUI** Blender add-on (`texture_gui.py`, v1.8.0).

## The tool in one sentence

Motion Texture Studio is a Blender add-on that turns the existing Texture GUI into an animation tool: it maps stills, image sequences, and movies onto the selected object, animates every texture and relief control over time, and previews the moving surface live in the viewport.

**App:** Blender 5.2 LTS. It lives in the 3D Viewport sidebar (`N`) under the tab **Motion Texture**.

## The chore it ends

Today, putting moving imagery on a surface means building the shader by hand: wiring an Image Texture node, switching it to Image Sequence or Movie, setting frame range and cyclic playback, keyframing mapping offset/rotation, adding a bump or displacement node, keyframing the relief, checking playback, and redoing all of it when the art changes. That is roughly **45–90 minutes per asset**, repeated every revision. My current Texture GUI only handles still images and one surface at a time. This tool collapses the job to **open source → choose motion → preview → apply**, in minutes.

## The UI

Sidebar tab **Motion Texture** (`N`), collapsible sections:

- **Source**
  - `Open Still…`, `Open Image Sequence…`, `Open Movie…` buttons
  - source path field, `Refresh Source`, `Clear Source`
  - Frame Start, Frame End, FPS fields, `Auto from Source` toggle
  - Frame Offset field, Loop Mode menu (Once, Loop, Ping-Pong, Hold Last), Color Space menu (sRGB, Non-Color, Linear)
  - frame count / resolution readout
- **Playback**
  - `Play/Pause`, `Previous Frame`, `Next Frame`, Current Frame field, timeline scrubber
  - `Loop` toggle, Speed menu (0.25x, 0.5x, 1x, 1.5x, 2x)
  - `Preview on Selected` toggle, `Preview Render` button
- **Animate Texture**
  - `Enable Animation` toggle
  - keyframe buttons for Offset X/Y, Rotation, Scale, Tiling X/Y, Hue, Saturation, Brightness, Contrast, Relief, Depth, Glow
  - `Key at Current Frame`, `Delete Key`, `Clear Animation`
  - Interpolation menu (Constant, Linear, Bezier), `Copy Still Values to Frame 1`
  - Motion Preset menu (Scroll X, Scroll Y, Drift, Pulse, Breathe, Ripple, Flicker, Stop-Motion)
  - Speed and Amplitude sliders
- **Raised Surface**
  - Relief Mode menu (Bump, Displacement)
  - Relief Source menu (Image Luminance, Image Sequence, Noise, Wave)
  - `Animate Relief` toggle, Relief Amount, Depth, Midlevel, Detail, Detail Scale, Invert Relief
  - Motion Direction menu (X, Y, Radial), Speed, Amplitude, Phase Offset
  - `True Displacement` toggle, Subdivision Level slider
  - Normal Map field + `Load Normal Map…`, Normal Strength
  - Raised presets: Drift, Pulse, Ripple, Crawl, Breathe
- **Surface** (kept from v1.8)
  - Roughness, Metallic, Specular, IOR, Coat, Coat Roughness, Sheen, Sheen Roughness, Anisotropic, Subsurface, Transmission, Alpha
  - Glow, Glow Tint, `Glow From Image` toggle
  - Surface Preset menu (Matte, Glossy, Plastic, Ceramic, Metal, Brushed, Velvet, Glass, Glowing)
- **Apply / Bake**
  - `Apply to Selected`, `Apply to All Selected`, `Revert to Still`
  - `Bake Current Frame`, `Bake Motion to Image Sequence…`, `Cancel Bake`
  - `Undo`, `Redo`
- **Presets / Settings**
  - `Save Motion Preset…`, `Load Preset…`, `Rename`, `Delete`, `Import Preset…`, `Export Preset…`
  - `Remember Settings Per Object` toggle
  - `Reset Color`, `Reset Transform`, `Reset Surface`, `Reset Animation`, `Reset Everything`

## Why it's advanced

- Real **animation system**, not a single script: keyframes and drivers on node inputs, synced to the scene timeline, with loop modes, frame offsets, and interpolation.
- Handles **moving images** as a source: image sequences and movies with frame ranges, offsets, cyclic playback, and per-object timing.
- **Moving raised textures**: animated bump and optional true displacement, driven by image luminance, sequences, or procedural motion. Bump is the fast fallback; displacement is the heavy option.
- **Non-destructive preview**: edits run live in Material Preview; nothing is baked until you press Bake. `Preview Render` checks the current frame or range.
- Works on **whatever is selected**, with batch apply and per-object settings; remembers the last source, preset, and motion setup.
- **Presets saved to disk** as portable JSON (motion + surface), with optional thumbnail; can be imported/exported and shared.
- **Undo/redo** for apply and bake, and automatic stale-node-graph rebuild carried over from v1.8.
- **Handles mistakes without crashing**: missing/corrupt frames, unsupported codec, start frame after end frame, missing normal map, and unsupported true displacement all produce a clear warning and a safe fallback.
- **Bakes to a portable image sequence** so the animated texture can leave Blender and be handed off.

## The three weeks

| Milestone | Deliverable |
| --- | --- |
| **By Oct 13** | Existing Texture GUI v1.8 is the baseline: still-image path, surface presets, drag-and-drop, node rebuild. New: source manager for image sequences/movies; scene-synced playback; basic animated offset/rotation; live preview. |
| **By Oct 20** | Keyframes and interpolation for all texture/surface controls; moving raised surface (bump + optional displacement) with motion presets; per-object settings; save/load motion presets. |
| **By Oct 26** | Bake current frame and motion-to-sequence; batch apply; undo/redo; loop/offset edge cases; missing-file recovery; performance/cache pass; 2–3 demo assets; README + 60-second recording. |

## The smallest version that still counts

Load one image sequence or movie onto the selected object, animate Offset X/Y (scroll) and Relief/Depth (pulse) on the timeline, and preview the playback. No presets, no batch, no bake — still a real upgrade over the still-only v1.8 and enough to demo.

## The riskiest part

Frame-accurate, non-blocking playback and caching of movie/image-sequence textures while the material graph rebuilds, plus **true displacement** support/performance in EEVEE. Bake is the second risk.

- **Fallback:** prefer image sequences over compressed movies, ship animated **bump** as the primary “raised” look, bake only the current frame, and use proxy/reduced-resolution playback. If displacement is unreliable, keep it as an optional Cycles path and label it clearly.

---

# Install and run

## What you need

- **Blender 5.2 LTS** (tested on 5.2.1 LTS). Blender 4.2+ should also work but has not been tested.
- The file `motion_texture_studio.py` from this repo (no other install, no dependencies).

## Steps

1. Download this repo (green **Code** button → **Download ZIP**) or clone it.
2. Open Blender. Go to **Edit → Preferences → Add-ons**.
3. Click the **⌄** (dropdown) at the top right → **Install from Disk…**.
4. Select **`motion_texture_studio.py`**.
5. Tick the checkbox next to **Motion Texture Studio** to enable it.
6. In the 3D Viewport press **N** to open the sidebar and click the **Motion Texture** tab.
7. Select a mesh object (the default cube is fine). Click **Open Still…** and choose **`assets/test_texture.png`**.
8. Click **Apply to Selected**. The object now has a material called `MotionTexture_<objectname>`.
9. Open the **Animate Texture** section and click a motion preset such as **Scroll X**. Set the scene end frame to ~48 and press **Play/Pause** — the texture scrolls in the viewport.
10. For a sequence: **Open Image Sequence…** and pick the **first** file of a numbered sequence (`frame_0001.png`). The frame range is detected from the filenames.
11. For a movie: **Open Movie…** and pick a video file. The scene frame range is set to the movie's length, and pressing **Play** shows the video animating on the object surface.

If a movie or sequence codec will not load, use an **image sequence** instead — it is the more reliable path.

# What works right now

- Installs and registers as a Blender add-on; sidebar tab **Motion Texture** opens.
- Per-object material named `MotionTexture_<object>` with a full non-destructive node graph.
- **Sources:** still image, numbered image sequence (auto frame range), and movie. Loading a still or a movie now shows the texture on the object right away (the material is assigned to the mesh faces), and a loaded movie plays across the frame range instead of staying frozen on one frame.
- **Playback:** play/pause, frame step, scrub, preview render, scene-synced timeline.
- **Motion presets:** Scroll X/Y, Drift, Pulse, Breathe, Ripple, Flicker, Stop Motion.
- **Animation:** keyframe offset/rotation/scale/hue/brightness/contrast/relief/depth/glow, delete key, clear animation, linear/bezier/constant interpolation, copy still to frame 1.
- **Raised surface:** animated bump; relief source from image / noise / wave; relief motion presets Drift, Pulse, Ripple, Crawl.
- **True displacement:** optional, via a displacement output + subdivision modifier, with clear warning that it is heavy and best on Cycles.
- **Surface / color / transform / emission** controls and surface presets (Matte, Glossy, Plastic, Ceramic, Metal, Brushed, Velvet, Glass, Glowing).
- **Save / load / import / export** motion presets as JSON in Blender’s user presets folder.
- **Apply to Selected**, **Apply to All Selected**, **Rebuild**, **Revert to Still**, undo/redo.
- Drag-and-drop an image or movie onto the 3D Viewport.

# What does not work yet

- **Bake to image sequence** and **bake current frame** are not implemented.
- **Rename preset** and per-preset thumbnails are not implemented.
- **Loop modes** (Ping-Pong / Hold Last) and **playback speed** are not implemented.
- **Movie auto-duration** depends on the codec loading correctly; image sequences are more reliable.
- **True displacement** is unreliable in EEVEE and should be used on Cycles. Bump is the safe path.
- **“Apply to All Selected”** copies the current settings, but does not copy animation curves to the other objects.
- **Motion presets key across the whole scene frame range.** If the scene is long (e.g. 1152 frames) a preset like Scroll X moves the texture only a tiny amount over a short clip and looks almost frozen. Shorten the scene frame range to the length of your shot so the motion reads.
- The add-on was tested headless; interactive UI polish (button layout, long menus) is still rough.

## Fixed in this version

- Loading a **still image** or a **movie** now actually shows the texture on the object. Previously the material was created but never assigned to the mesh faces, so a fresh object kept its default grey material.
- A loaded **movie** now plays on the texture. Previously the movie's ImageUser frame duration was left at 1, so Blender clamped it to a single frame and the video looked frozen.

# Peer run

> A classmate who does not have Blender can still run this: use a portable (unzipped) Blender build — no install needed — or a screen-shared session. Record their name and three sentences here: what they did, what happened, what confused or broke.

- **Classmate:** _(name here)_
- **Sentences:**
  1. _(what they did)_
  2. _(what happened)_
  3. _(what confused or broke)_

# Running a classmate's tool

I tested **A6: Wire Body Profile (InBody Data Build)** by **Brent Shultz** (https://github.com/bshultz-sva/A6), a Maya 2027 tool that opens a "Wire Body Profile" window where you save body-composition measurements under a person's name and date and then reshape a blue wire-frame human figure with a slider.

1. I cloned the repo, opened `InBody Data Build.mb` in Maya 2027, launched the window, and entered three dated measurements for a test profile so the wire body had something to follow.
2. Everything in the README worked as described — Save Entry stored the entries, the history list loaded them back, Delete Selected Entry removed one, Rebuild Wire Body regenerated the figure (2196 triangles, 179 cm tall), and the Entry slider smoothly reshaped the wire body's height and limb/trunk thickness from the neutral body through each dated entry, with the "Exaggerate change" multiplier doing its job.
3. The only thing that tripped me up was that the window didn't open automatically when the scene loaded (I had to run `import body_profile_ui; body_profile_ui.show()` by hand), and the tool requires Maya 2027 specifically since the scene was saved in that version — but once it was open I could not get anything to actually break.

# Peer review: Fiori's Color Script Template Generator

I peer reviewed **Fiori Sims'** Color Script Template Generator (https://github.com/fiorisims/pfa-week06), a pygame palette tool that samples colors from images, builds a color script / palette sheet, and exports swatches to Photoshop.

1. The first issue I hit was that pygame crashed immediately the moment I clicked any button in the window, so I had opencode bypass that problem before I could use the tool at all.
2. After that workaround, every feature and button worked and ran smoothly — loading images, sampling and building the palette, and saving the sheet — with the only remaining exception being the Photoshop export button.
3. A nice touch was that each swatch displays its hex code, but the hex codes sometimes clip into the color palette area instead of staying fully inside their swatch.
