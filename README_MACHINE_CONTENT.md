# Machine content and image mapping

## Machine images (source)

Imported into Flask static as:
- `static/images/machines/`

Note:
- The original `Machine Images/` source folder can be removed after import to keep the repository clean.

## Sanitized filenames

| Original file | Sanitized filename | Used as |
|---|---|---|
| `page_20.png` | `glass_tempering_furnace.png` | Featured machine + hero |
| `page_21.png` | `production_line.png` | Production line visuals + page headers |
| `CNC Glass Cutting Machine.png` | `cnc_glass_cutting_machine.png` | Machine cards + gallery |
| `CNC Glass Engraving Center.png` | `cnc_glass_engraving_center.png` | Machine cards + gallery |
| `Glass Storage Rack.png` | `glass_storage_rack.png` | Machine cards + gallery |
| `Line Cutting Glass Automatic Fully.png` | `line_cutting_automatic.png` | Machine cards + gallery |
| `Precision High SANKIN.png` | `precision_high_sankin.png` | Machine cards + gallery |
| `2436SKTF.png` | `2436sktf.png` | Machine cards + login header image |

## Bilingual titles and descriptions

Machine records are stored in `machines` table using:
- `title_en`, `title_ar`
- `short_desc_en`, `short_desc_ar`
- `long_desc_en`, `long_desc_ar`

Gallery records are stored in `gallery_items` table using:
- `title_en`, `title_ar`
- `description_en`, `description_ar`

This prevents English/Arabic from being mixed in one sentence and keeps the UI clean.

## Seeding behavior

On first run (empty DB), the app seeds:
- Machines (with bilingual content)
- Gallery items (derived from machines)
- Process steps
- Baseline specs for the featured tempering furnace

Seed logic is in `models.seed_if_empty()`.

## Adding a new machine later

1) Add an image to `static/images/machines/` (use lowercase + underscores)
2) Login as Admin
3) Go to:
   - `/admin/machines` → Add machine
4) Optionally add specs:
   - `/admin/specifications` → Add spec rows
5) Optionally add a gallery item:
   - `/admin/gallery` → Add item

