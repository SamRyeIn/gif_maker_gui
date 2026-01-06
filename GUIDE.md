# FFGIF Maker

### Quick Reference Guide

---

## Getting Started

1. **Launch the app** from `dist/FFGIF Maker.app` or run `python FFGIF_Maker.py`
2. **Select your images** using the "Select Files..." button
3. **Adjust settings** as needed
4. **Click "Create GIF"** and wait for processing

---

## Settings

| Setting | Description | Default |
|---------|-------------|---------|
| **Frame Rate** | Frames per second (higher = faster animation) | 4 fps |
| **Scale Mode** | Choose between factor or pixel dimensions | By Factor |
| **Scale Factor** | Multiplier for original size (0.5 = half) | 0.5 |
| **Pixel Size** | Exact output dimensions in pixels | 640 x 480 |
| **Output Name** | Filename for the generated GIF | Auto-generated |

---

## Scale Mode Options

### By Factor
Scales relative to original image size:
- `0.25` = Quarter size
- `0.5` = Half size
- `1.0` = Original size
- `2.0` = Double size

### By Pixels
Sets exact output dimensions:
- Width and height in pixels
- Images will be stretched to fit

---

## Output Filename

Auto-generated from:
```
{first_image_name}_{date}.gif
```

**Date source priority:**
1. EXIF DateTimeOriginal (when photo was taken)
2. File modification date
3. Current date

**Format:** `YYYYMMDD` (e.g., `20260105`)

---

## Preview Panel

After GIF creation, the preview shows:
- **Animated preview** of the generated GIF
- **Dimensions** (width x height in pixels)
- **Frame count** (number of frames)
- **File size** (KB or MB)

Click **"Open GIF"** to view in your default image viewer.

---

## FFmpeg Output

Check **"Show FFmpeg output"** to see:
- Full command being executed
- Processing progress
- Any warnings or errors

Useful for troubleshooting or understanding the conversion process.

---

## Tips

### For Smaller File Sizes
- Use a lower scale factor (0.25 or 0.5)
- Reduce frame rate (2-4 fps)
- Use fewer source images

### For Better Quality
- Use higher scale factor
- Source images should be consistent exposure
- Avoid mixing portrait and landscape orientations

### For Smoother Animation
- Higher frame rate (8-15 fps)
- More source images
- Consistent timing between shots

---

## Supported Formats

**Input:** JPG, JPEG, PNG, BMP, TIFF, TIF

**Output:** GIF (animated, infinite loop)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "FFmpeg not found" | Install FFmpeg: `brew install ffmpeg` |
| App won't open | Right-click → Open (first launch on macOS) |
| GIF too large | Reduce scale factor or frame rate |
| Animation too fast/slow | Adjust frame rate |
| Error with images | Ensure all images are same format |

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Quit | ⌘Q |
| Close Window | ⌘W |

---

## Requirements

- **macOS** 10.13 or later
- **FFmpeg** installed (`brew install ffmpeg`)
- **~50MB** disk space for app

---

## Technical Details

FFGIF Maker uses FFmpeg's two-pass encoding:

1. **Pass 1:** Analyzes all frames to generate an optimal 256-color palette
2. **Pass 2:** Creates the GIF using Floyd-Steinberg dithering

This produces higher quality GIFs than single-pass conversion.

---

*Version 1.0 | [Source on GitHub]*
