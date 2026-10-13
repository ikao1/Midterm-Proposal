# Midterm Proposal

## 2D-to-3D Parallax Tool for Blender

A Blender add-on that takes a single 2D drawing or illustration, lets an artist cut it into layers on the canvas, and instantly converts those layers into depth-arranged 3D mesh objects that parallax and shift perspective as you move the view — a "living" version of the drawing.

## The Chore It Ends

Today, parallaxing a 2D drawing means manually cutting pieces in Photoshop, importing each as a separate texture, creating a plane per piece by hand, guessing a Z-depth, parenting them to a camera/rig, and re-importing every time the art changes. That's roughly **1–4 hours per illustration** for a handful of layers, and it's done every time the artwork is revised (often weekly on a production).

This tool collapses that to: **open image → cut → depth-assign → done**, in minutes, and it re-runs on the updated image.

## The UI

An operator in its own **"2D Parallax"** tab in the N-panel.

- **Load Image** field + "Bring into Scene" button (creates a reference plane facing camera).
- **Cut Tool**: click-drag Lasso / Rectangle / Polygon modes to draw a layer boundary on the image.
- Panel per layer:
  - name field
  - **Depth slider** (0.0–1.0)
  - **Buffer/feather slider**
  - **Scale XY**
  - enable/disable checkbox
- **Depth presets**: Foreground / Mid / Background buttons; **Save/Load preset** menu.
- **Preview in Viewport** toggle (real-time parallax via the existing camera) and **Render Preview** button.
- **Inpaint Holes** toggle (fill the gap a cut layer leaves behind).
- **Rebuild / Update from Image** button (re-cuts all layers when the source art changes).
- **Export Scene** button (bake layers to a clean, self-contained mesh scene the artist can keep editing).

## Why It's Advanced

More than one script:

- Each cut becomes a real **editable mesh object** (a plane cut to the mask shape, with the source image as a texture and the mask as its alpha) — moveable, scalable, rotatable in 3D like any other object.
- Operates on the artist's selection and live scene state, not hardcoded paths.
- Non-destructive: each layer is generated from stored cut masks, so it re-generates on **Rebuild** and is fully **undoable** (single operator + `bl_info` undo).
- Remembers settings per-scene (custom properties) and offers **presets** for depth.
- **Previews before committing**: viewport parallax runs live so the artist sees the result before an export/bake.
- Handles mistakes gracefully: no image loaded, empty mask, or a layer that would occlude everything gets a friendly warning instead of a crash.

## The Three Weeks

| Milestone | Deliverable |
| --- | --- |
| **By Oct 13** | Create a GUI for N-panel for the purposes of importing images as a camera-facing plane; freehand/rectangle cut; each cut becomes its own textured mesh object at a Z-depth; basic viewport parallax. |
| **By Oct 20** | Depth/buffer/scale controls, presets, live preview, undo, save/load settings, hole-filling, and a full N-panel UI. |
| **By Oct 26** | Update UI design of GUI N panel, mesh cleanup/thickness options, robustness passes, and 2–3 demo drawings polished for crit. |

## The Smallest Version That Still Counts

Image imports, artist draws 3–5 regions, each becomes a moveable mesh plane at an adjustable depth, and moving the camera parallaxes them convincingly. That alone replaces the manual Photoshop-import-plane-depth loop and demos well.

## The Riskiest Part

Automatic/painterly **hole-filling (inpainting)** behind cut layers — a foreground cut leaves an empty region, and doing that without a real diffusion/inpaint model is hard.

- **Fallback:** clone-stretch nearby pixels or just leave the background intact and cut only what's needed.

The second risk is clean **layer separation** from a flat drawing without leaking pixels or hard edges.
