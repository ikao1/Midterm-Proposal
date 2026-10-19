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
