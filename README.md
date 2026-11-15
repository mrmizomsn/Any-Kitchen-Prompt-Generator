# Kitchen Prompt Generator

<p align="center">
  <img src="screenshots/screenshot-logo.webp" alt="logo sample" width="300" />
</p>


**An offline, single-file web tool that builds ultra-high-end, photorealistic architectural kitchen-interior prompts for modern generative image AI models.**

Feed it a flat-colour kitchen mask (exported via the included Blender script), choose your materials, finishes, lighting, and camera settings for each component, and it compiles a single, copy-ready prompt that maps every surface property to its corresponding mask colour.


<div align="center">

![Version](https://img.shields.io/badge/version-v3.28-c07a53)
![Repo Size](https://img.shields.io/github/repo-size/mrmizomsn/Any-Kitchen-Prompt-Generator?color=c07a53)
![GitHub downloads](https://img.shields.io/github/downloads/mrmizomsn/Any-Kitchen-Prompt-Generator/total?color=c07a53)
![GitHub stars](https://img.shields.io/github/stars/mrmizomsn/Any-Kitchen-Prompt-Generator?color=c07a53)
![License](https://img.shields.io/github/license/mrmizomsn/Any-Kitchen-Prompt-Generator?color=c07a53)
![Blender](https://img.shields.io/badge/Blender-3.6%20%7C%204.x%20%7C%205.0-c07a53)

</div>
---

## Table of Contents

- [Key Features](#key-features)
- [How the Pieces Fit Together](#how-the-pieces-fit-together)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [Using the Mask Add-on (Blender)](#using-the-mask-add-on-blender)
- [Using the Prompt Generator](#using-the-prompt-generator)
- [Tag Management](#tag-management)
- [Material Matrix](#material-matrix)
- [Geometric Anchoring](#geometric-anchoring)
- [Built-in Quality Checks](#built-in-quality-checks)
- [Data and Privacy](#data-and-privacy)
- [Troubleshooting](#troubleshooting)
- [Version Notes](#version-notes)

---

## Key Features

### Why This App Exists
Instead of manually writing and tweaking prompts for every surface in your reference image, the app can build complete, structured prompts in just a few clicks. Simply choose your materials, surface finishes, lighting modes, and camera settings from the built-in library, and the app automatically compiles a ready-to-paste prompt to turn your 3D scene into a photorealistic render—or restyle existing materials—using your preferred AI image generator.
- **Tag-Management UI** Quick-access tags for every component's *Custom Appendix Text*, and for every field in *Template Structure Settings*. (see [Built-in tags](#built-in-tags)). 

  - **`＋ Tag` and `clear tag` buttons** sit together at the top of each appendix text area.
  - `＋ Tag` saves the current text as a reusable tag, expanding your prompt library for one-click reuse.
  - `clear tag` erases the text inserted from the selected tag and removes the tag's highlight.
  - Tags can be inserted with one click, renamed, edited (the pencil icon, or double-click) and deleted. Inserting a tag keeps a one-step **undo** of the replaced text.

### Mask-Reference Processing
- Works from a **flat-colour mask** with black wireframe outlines, produced by the included Blender add-on. (see [Render Samples](#Render-Samples)). 

- The **Image Lab** tab lets you upload the mask, click a region to assign its colour to a component (mask eyedropper), or import the add-on's **JSON legend** so colours, names and custom components are filled in automatically.
- A **presence threshold** (default 0.01 % of mask pixels) decides which components exist in the mask, so absent components never appear in the prompt.
- A **rendered-output checker** compares the colour of a region in the AI-generated image with its target.

### Prompt Library & Materials Matrix
- **57 countertop stones** in five groups, each with a descriptive phrase, e.g. Arabescato Breccia and Fantastico Arni.
- **18 wood species** in three groups, with **9 grain-and-cut options**.
- **Flooring** in wood or stone, with 8 wood patterns, 12 stone patterns and a 9-option stone finish list (Polished, Honed, Leathered, Brushed, Tumbled, Acid-Washed, Bush-Hammered, Flamed, Sandblasted). Flooring stone includes Black Basalt (see the note under [Material Matrix](#material-matrix)).
- **Hardware**: five handle styles plus finish selection; glass-cabinet handles, pendant materials, steel-door finishes and LED accent colour temperatures each have their own menus.
- **10 lighting modes** and **10 camera profiles**, with rules that flag contradictory combinations.

### Geometric Anchoring
- Every prompt carries a **LOCKED GEOMETRY** block that forbids changing camera position, perspective, crop, aspect ratio, room dimensions, cabinet layout, panel divisions, handle and shelf positions, or object placement.
- An optional **Geometry Exception** lets you state, in your own words, a change you do want. It is injected exactly as typed, and only while its checkbox is ticked.


---

## How the Pieces Fit Together

```mermaid
flowchart TD
    A["**1. Blender 3D Scene**<br/>Assign kitchen parts & export via <code>Any_kitchen_masks_V3.py</code>"] --> B["**2. Mask & Json Files**<br/>&lt;scene&gt;_mask.png + &lt;scene&gt;_mask.json"]
    B --> C["**3. Kitchen Prompt Generator**<br/>Load mask/Json file in Image Lab & configure materials, lighting & camera"]
    C --> D["**4. AI Image Generation (e.g., Nano Banana)**<br/>Paste compiled prompt + attach <code>_mask.png</code> as reference"]
    D --> E["**5. Color Accuracy Verification**<br/>Check final render against target mask colors"]

---

## Repository Structure



| Item | Purpose |
|---|---|
| `kitchen_prompt_generator.html` | The whole app: UI, prompt compiler. Works offline. |
| `Any_kitchen_masks_V3.py` | A **Blender add-on** (v3.0.0, requires Blender 3.6+) Assigns mask colors to scene objects by kitchen component and exports a flat-colour mask PNG alongside a JSON file mapping each assigned color to its component. |
| Asset folders | Swatch images the app refers to by folder and name. The app reports the expected path of each swatch (153 in total: 57 Countertop Materials / 49 Flooring Materials / 12 Flooring Patterns Stone / 8 Flooring Patterns Wood / 9 Grain & cut / 18 Wood Species). |

---

## Getting Started

The generator needs **no installation, build step, server or internet connection**.

### Option A: Clone the repository

```bash
git clone https://github.com/<your-username>/Any-Kitchen-Prompt-Generator.git
cd Any-Kitchen-Prompt-Generator
```

### Option B: Download a ZIP

1. On the GitHub repository page, choose **Code → Download ZIP**.
2. Extract the archive anywhere on your computer.

### Run the app

1. Open the folder and **double-click `kitchen_prompt_generator.html`**, or right-click it and choose **Open with → Microsoft Edge** (or Chrome, Firefox, Safari or any other modern browser).
2. The page opens with the live prompt on the right and the component panel on the left. You can start immediately.

> **Tip:** keep the asset folders next to the HTML file so swatch paths match.

---
## Render Samples

- Image Samples: Pre-packaged sample assets (including a reference color mask and its matching Blender-exported JSON legend) are provided to let you test and verify the Image Lab workflow instantly without needing to generate your own 3D export.

- Generate the Render: Upload the flat-color mask image as the reference input in your generative AI model, paste the compiled prompt, and generate your photorealistic architectural visualization.

![Mask sample](screenshots/screenshot-Kitchen-01_mask-21-9.webp)
*Flat-color material mask exported from Blender.*

![Rendred image](screenshots/screenshot-render01.webp)
![Rendred image](screenshots/screenshot-render1.webp)
*Final photorealistic architectural renders generated by the AI model.*

---
## Using the Mask Add-on (Blender)

`Any_kitchen_masks_V3.py is a Blender Python utility script designed to export scene masks as flat colors along with a corresponding JSON file, ready for seamless import into the kitchen Prompt web application.

1. In Blender: Open **`Any_kitchen_masks_V3.py`** inside the Text Editor and click **Run Script** 
2. Open the panel: **3D Viewport → Sidebar (N) → Any Kitchen Mask**.
3. Assign objects to components (16 built-in components such as Base Cabinets, Upper Cabinets, Countertop, Hardware, Flooring and Lighting). Objects are matched automatically by name patterns, and you can override the assignment manually. You can also add **custom components**, edit display names (internal keys never change), and use **Mask All Scene** to register components hidden behind other geometry.
4. Save your `.blend` file, then **export**. The add-on writes, next to the saved `.blend`:
   - `<blendname>_mask.png`: a flat-colour material-ID mask (unassigned objects and background are white, wireframe outlines are black)
   - `<blendname>_mask.json`: the legend (schema 3)
5. The add-on locks render settings during export (Workbench engine, flat shading, no anti-aliasing, Standard view transform) and restores your original settings afterwards. Component colours are kept visibly distinct from one another using CIEDE2000 (ΔE ≥ 5).

![Blender addon](screenshots/screenshot-Blender-mask.webp)
---

## Using the Prompt Generator

1. **Automatic Legend Loading:** load **_mask.json** as your Blender legend. All mask colors assigned to each object in Blender will automatically load inside the Image Lab.
   - **Manual Component Mapping (Optional):** Open Image Lab and upload your **_mask.png** then choose a component from the drop-down menu, and click directly on the corresponding part of the image mask; the picked mask color will be assigned to that part automatically.
   - **Note**:If no mask is loaded in the Image Lab, the app generates a standard "no-mask" prompt listing all components. Click the × button beside any entry to delete its mask color; doing so automatically excludes that component from the generated prompt. Clearing all mask colors reverts the entire prompt template back to standard no-mask mode, restoring all kitchen components to the prompt.
2. **Configure each component** in the left panel: material, colour, coating, sheen, wood species, grain and cut, stone and finish, hardware, lighting and so on.
3. **Add your own wording** in each component's *Custom Appendix Text*, or insert a saved tag.
4. **Pick a lighting mode and a camera profile** in the lighting section and in *Template Structure Settings*.
5. Review the **Rule check** under the prompt.
6. Press **Copy prompt**, then paste it into Nano Banana and attach the mask image as the reference.
7. Use **Refine Materials** if you want concise, finish-specific fidelity directives appended to each material line.

The app has five tabs: **Prompt**, **Image Lab**, **Rules & Colour**, **Self-tests** and **Config & Log**. The last one provides **Export JSON** / **Import** of your full configuration and a run log.

![Prompt Generator View](screenshots/screenshot-prompt.webp)


![Image Lab: mask eyedropper with a sample mask](screenshots/screenshot-imagelab-json.webp)

*Image Lab, step 1: A Blender-generated legend JSON file (such as Kitchen 01_mask.json) is loaded into the Image Lab, automatically parses the scene's color-coding schema and injects the precise HEX color masks into their corresponding architectural components (such as base cabinets, countertops, flooring, and hardware).*


![Image Lab: mask eyedropper with a sample mask](screenshots/screenshot-image-lab.webp)

*Image Lab, step 1 Manual Component Mapping(Without JSON): A (mask.png) is loaded without a JSON file, clicking a region assigns its colour to the selected component. Components with a colour show their share of the mask and are marked "in prompt". Components without one are "excluded".*

---
## TEMPLATE STRUCTURE SETTINGS

Customize the underlying prompt architecture by editing template blocks, reordering sections, and inserting dynamic tags.

![Prompt Structure](screenshots/screenshot-Prompt-structure.webp)

## Built-in tags

Inject Pre-configured parameters defining professional camera models, optics, cinematic lighting rigs, and rendering engine parameters to anchor the prompt's visual quality.

![Built-in tags](screenshots/screenshot-Built-in-tages01.webp)
![Built-in tags](screenshots/screenshot-Built-in-tages02.webp)

## Tag Management

![Tag Management View](screenshots/screenshot-tags.webp)

| Action | How |
|---|---|
| Save a tag | Type text in a component's *Custom Appendix Text* and press **＋ Tag** |
| Insert a tag | Click the tag chip. It **replaces** the field text, and a one-step **Undo** appears |
| Clear a tag | Press **clear tag**. The inserted text is erased and the chip is deselected |
| Rename or edit | Click the pencil icon on the chip, or double-click the chip |
| Delete | Click the **×** on the chip |

Notes:

- **`clear tag` only erases text that matches the selected tag.** If you typed or edited the text by hand, it is left alone and the app tells you no tag is selected.
- Limits: up to **30 tags per component** (2,000 characters each) and **20 tags per template field** (12,000 characters each). Duplicate texts are rejected.
- Tags are saved with your configuration, so they survive reloads and JSON export/import.

---

## Material Matrix

Selecting any material from the list—along with its finish type, grain, cut, surface pigment, and pigment colors—automatically injects its complete physical specification into the corresponding component slot of the prompt, paired with its assigned mask color.

![Marble list](screenshots/screenshot-Marble-list.webp)
![Wood list](screenshots/screenshot-Wood-species.webp)

| Area | Options |
|---|---|
| Countertop stone | 57 stones: White & Calacatta (14), Black & Charcoal (9), Grey & Silver (9), Beige, Cream & Brown (7), Exotic & Colored (18); includes **Arabescato Breccia** and **Fantastico Arni** |
| Wood species | Domestic hardwoods (8), softwoods (4), luxury exotic hardwoods (6) |
| Grain and cut | Straight grain, flat-sawn, rift-sawn, quarter-sawn, book-matched, slip-matched, chevron, herringbone, end-grain block |
| Flooring | Wood or stone; 8 wood patterns, 12 stone patterns; 9 stone finishes |
| Hardware | 5 handle styles with finish choice; 5 glass-cabinet handle types |
| Pendant lights | 8 materials (Opal Glass, Smoked Glass, Ribbed Glass, Matte Black Metal, Brushed Brass, Woven Rattan, Concrete, Linear LED bar) |
| Steel doors | 5 finishes (Matte Black, Oil-Rubbed Bronze, Industrial Charcoal, Warm Champagne Gold, Pristine White) |
| Light accents | 4 colour temperatures (2700K to 5000K) |
| Lighting | 10 modes, from Neutral Daylight (default) to Cinematic Low-Key |
| Camera | 10 profiles, from Full-Frame DSLR (24mm Tilt-Shift) to OM System OM-1 Mark II |

---

## Geometric Anchoring

Image models can drift: walls shift, cabinets gain extra doors, perspective changes. The generator counters this in the prompt itself:

- A **LOCKED GEOMETRY** block states that camera position, perspective, crop, aspect ratio, room dimensions, architectural structure, cabinet layout, door/drawer/panel divisions, handle and shelf positions, and object placement must not change, and that no objects may be added, removed, moved, resized or redesigned.
- Objects cut off by the frame stay cut off.
- The wireframe in the reference is declared to be used **only** to locate surfaces; the output must not contain outlines, wireframes or flat shading.
- The **aspect ratio** is a template slot (`{ASPECT}`), set from an imported legend's resolution, so the prompt and the mask always agree.
- Specifications that overlap follow explicit precedence rules (the more specific rule wins), and HEX values are declared exact colour targets.
- **Geometry Exception** is the only sanctioned way to allow a structural change. It is off by default.

---

## Built-in Quality Checks

- **Self-tests tab:** a suite of 114 automated checks (prompt snapshots, component exclusion, import/export round-trips, colour maths, tag behaviour and more) that runs on page load. All should show a tick.
- **Rule check:** flags contradictory choices, such as a long-exposure camera profile with flash lighting, or ambiguous mask colours.
- **Rules & Colour tab:** reports adjacent surfaces whose colours are too close (ΔE2000) and near-duplicate palette entries.
- **Rendered-output checker:** measures how close the AI result is to your target colours.

---

## Data and Privacy

- The app works **offline** and sends nothing to any server.
- Your current configuration and run log are kept in your browser's `localStorage` on this device. Use **Config & Log → Export JSON** to back them up or move them to another browser.
- The copyable prompt is plain text. All colour highlighting in the preview is display-only and never enters the copied text, exports or presets.

---

## Troubleshooting

| Problem | What to try |
|---|---|
| Swatch previews are empty | Keep the six asset folders next to the HTML file and keep their names unchanged |
| A component is missing from the prompt | It may be below the mask presence threshold, or absent from the legend. Lower the threshold in **Image Lab** |
| Colours look wrong after exporting a mask | Only use the _mask.png file automatically exported next to your .blend project file—do not use viewport screenshots or manually save renders unless Blender is using the Workbench render engine. |
| `clear tag` shows "No tag is selected" | The field's text no longer matches a saved tag (it was typed or edited by hand), so nothing is erased |
| Settings vanished | Browser data was cleared or you opened the file in another browser. Import your exported JSON |
| Self-tests show a failure | Re-download the HTML file. Please open an issue and attach the failing test name |

---

## Version Notes
- **V3.29**: eliminates all contradictory finish phrases across wood cabinet and floor prompt texts, ensuring surface sheen is controlled exclusively by your selected sheen level. Wood floor reflection descriptions now dynamically adapt to your finish tier, and the wood Refine option always preserves sheen notes alongside texture details.
- **V3.27**: Stone descriptions now leave the finish to the selected finish control.
- **V3.25**: `＋ Tag` moved above each appendix text area, new `clear tag` button, and a regression test for both.
- **V3.24**: flat, solid colour-coded labels with readable contrast on the dark panel.
- **V3.23**: mask-colour labels in the prompt preview and panels (display only).
- **V3.22**: tags extended to Template Structure Settings; all appendix fields are resizable text areas.
- **V3.21**: 27 additional countertop stones and the first tag system.

---

## License

*This project is licensed under the **GNU General Public License v3.0 (GPLv3)**. See the [LICENSE](LICENSE) file for details.*
