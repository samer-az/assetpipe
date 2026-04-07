---
name: assetpipe
description: >
  AI-powered image generation for web design projects. Use this skill whenever
  building websites, landing pages, web apps, or any UI that needs visual assets.
  Triggers on: "generate image", "create hero", "make icon", "design banner",
  "need a background", "placeholder image", "web asset", "landing page image",
  any mention of creating/generating images during web development, or when the
  user is building a site and you recognize an image would improve it. Also use
  when editing or transforming existing images for web use. This skill works with
  the assetpipe MCP server — always prefer the MCP tools over manual
  approaches when available.
---

# AssetPipe — Skill Guide

You have access to an MCP server called `assetpipe` that generates
professional web design assets using Google Gemini. This skill teaches you
**when** and **how** to use it effectively.

## Available MCP Tools

| Tool                  | Purpose                                           |
|-----------------------|---------------------------------------------------|
| `generate_web_asset`  | Generate any type of web image asset               |
| `edit_web_asset`      | Modify an existing image                           |
| `remove_background`   | Remove background from any image → transparent PNG |
| `enhance_prompt`      | Preview the enhanced prompt before generating      |
| `list_asset_types`    | Show all asset types, styles, and configurations   |
| `batch_generate`      | Generate multiple related assets at once            |
| `init_project_style`  | Create a project style profile for consistent generation |
| `update_project_style` | Update fields in the project style profile              |
| `get_project_style`   | Read the current project style configuration             |

---

## When to Generate Images

### PROACTIVELY suggest image generation when:
- Building a landing page or marketing site → suggest hero images, illustrations
- Creating an e-commerce page → suggest product images, banners
- Building a dashboard → suggest placeholder avatars, icons
- Making a portfolio site → suggest background textures, hero banners
- Any UI that has `<img>` placeholders or lorem-picsum URLs

### DO NOT generate when:
- User explicitly wants stock photos or specific real photos
- The project already has all needed images
- User is only working on backend/logic code
- The image would be purely decorative with no UX value

---

## Asset Type Selection Guide

Choose the right `asset_type` based on what the user needs:

| Need                                    | asset_type      | Typical Size   |
|-----------------------------------------|-----------------|----------------|
| Full-width page header                  | `hero`          | 1536×768       |
| UI element icon                         | `icon`          | 512×512        |
| Brand mark / logo                       | `logo`          | 1024×1024      |
| Page/section background                 | `background`    | 1024×1024      |
| Blog post or card thumbnail             | `thumbnail`     | 640×360        |
| Feature section or explainer            | `illustration`  | 1024×768       |
| User profile placeholder                | `avatar`        | 256×256        |
| Social media or promo banner            | `banner`        | 1200×628       |
| E-commerce product shot                 | `product`       | 1024×1024      |
| Anything else                           | `custom`        | 1024×1024      |

---

## Style Selection Guide

Match the style to the project's design system:

| Project Vibe                        | Recommended Style   |
|-------------------------------------|---------------------|
| Corporate / SaaS                    | `minimal` or `flat` |
| Creative agency / Portfolio         | `gradient` or `3d`  |
| Tech startup                        | `glassmorphism`     |
| E-commerce / Lifestyle              | `photorealistic`    |
| Developer tools / CLI               | `neon` or `minimal` |
| Children / Education                | `flat` or `watercolor` |
| Architecture / Engineering          | `isometric`         |
| Blog / Editorial                    | `line-art` or `watercolor` |
| Gaming / Entertainment              | `neon` or `3d`      |

---

## Prompt Engineering Best Practices

### DO:
1. **Be specific about subject matter**: "A developer working at a standing desk with multiple monitors" not "a person working"
2. **Mention composition**: "centered", "rule of thirds", "negative space on the right for text"
3. **Include context of use**: "for a dark-themed dashboard" or "to be placed next to a pricing table"
4. **Specify text-safe zones**: "Leave the left third empty for text overlay"
5. **Reference the color palette** when the project has one

### DON'T:
1. Use vague prompts like "a nice image" or "something cool"
2. Include text in the prompt that should be rendered (AI text rendering is unreliable)
3. Request copyrighted characters, logos, or brand imagery
4. Ask for real people's faces

### Prompt Formula:
```
[Subject] + [Action/State] + [Environment] + [Composition] + [Mood/Lighting]
```

**Example:**
```
"A modern workspace with a laptop showing analytics,
 surrounded by plants and warm ambient lighting,
 shot from a slightly elevated angle,
 cozy and productive atmosphere"
```

---

## Transparent Images (No Background)

Use `transparent: true` on `generate_web_asset`, `edit_web_asset`, or `batch_generate` to produce images with no background (transparent PNG). This is ideal for:

- **Icons** that need to sit on any colored background
- **Logos** that must work on both light and dark themes
- **Product images** for e-commerce with clean cutouts
- **Illustrations** to overlay on sections
- **Stickers / badges / UI elements**

### When to use transparent:
- The image will be placed over a colored or gradient background in CSS
- The user asks for "no background", "transparent", "cutout", "isolated", or "PNG with alpha"
- Icons, logos, and product shots — default to suggesting `transparent: true`

### Standalone background removal:
Use `remove_background` to strip the background from any existing image file. No need to regenerate — just pass the file path.

```
User: "Remove the background from this product photo"
→ Use remove_background with input_image_path
```

---

## Workflow Patterns

### Pattern 1: Single Asset for a Section
```
User: "I'm building a landing page for a fitness app"
You: Generate a hero image that matches the theme

→ Use generate_web_asset with:
  - asset_type: "hero"
  - style: "photorealistic" or "gradient"
  - prompt: Describe the fitness theme specifically
  - color_palette: Match the project's colors if known
```

### Pattern 2: Full Page Asset Set
```
User: "Create all images for this landing page"
You: Use batch_generate with consistent brand_context

→ Use batch_generate with:
  - Multiple assets: hero, illustrations for features, background
  - Shared brand_context: "Fitness app, energetic, modern"
  - Shared color_palette: Project colors
```

### Pattern 3: Iterative Refinement
```
User: "The hero image doesn't feel right"
You: First use enhance_prompt to show what will change,
     then generate with adjusted parameters

→ Step 1: enhance_prompt to preview
→ Step 2: generate_web_asset with refined prompt
→ Step 3: If still not right, try different style or edit_web_asset
```

### Pattern 4: Edit Existing Image
```
User: "Make this image darker"
You: Use edit_web_asset with the source image

→ Use edit_web_asset with:
  - input_image_path: path to existing image
  - edit_prompt: Specific edit instructions
```

### Pattern 5: Transparent Asset
```
User: "Create a logo for my app, no background"
You: Generate with transparent: true

→ Use generate_web_asset with:
  - asset_type: "logo"
  - transparent: true
  - prompt: Describe the logo
```

### Pattern 6: Remove Background from Existing Image
```
User: "I have a product photo, remove the background"
You: Use the standalone remove_background tool

→ Use remove_background with:
  - input_image_path: path to the image
```

---

## Integration with Web Projects

### After generating an image:
1. **Move to project assets**: Copy the generated image to the project's image directory (e.g., `public/images/`, `src/assets/`, `static/`)
2. **Update HTML/CSS/JSX**: Reference the new image in the code
3. **Optimize if needed**: Consider suggesting image optimization tools for production

### File naming convention:
Use the `filename` parameter with descriptive, kebab-case names:
- `hero-fitness-landing` → `hero/hero-fitness-landing.png`
- `icon-dashboard-analytics` → `icon/icon-dashboard-analytics.png`
- `bg-gradient-dark` → `background/bg-gradient-dark.png`

### CSS integration tips:
- For backgrounds: suggest `background-size: cover` and `background-position: center`
- For heroes: remind about responsive considerations and `object-fit`
- For icons: suggest using them as `<img>` or inline if small enough

---

## Brand Consistency

When working on a multi-page project, maintain consistency by:

1. **Establishing brand context early**: Ask the user about their brand style on the first image generation
2. **Reusing parameters**: Keep the same `brand_context`, `color_palette`, and `style` across all generations
3. **Using batch_generate**: When creating multiple assets, batch them to ensure consistency
4. **Documenting choices**: After the first successful generation, note the parameters used for future reference

---

## Project Style Management

AssetPipe supports per-project style profiles that automatically apply to all image generations. Styles are stored in a `.assetpipe-style.json` file in the project root.

### Setting up a project style

On the **first image generation** for a project:

1. Call `get_project_style` to check if a style exists
2. If no style exists, ask the user about their design preferences:
   - What visual style? (flat, gradient, minimal, etc.)
   - What colors? (brand palette or general direction)
   - What's the project about? (brand context)
   - Any style directives? (e.g. "warm and personal", "corporate and clean")
3. Call `init_project_style` with their answers

### How it works

Once a style is configured:
- All `generate_web_asset`, `batch_generate`, `edit_web_asset`, and `enhance_prompt` calls automatically load and apply the project style
- Per-call parameters override project defaults (e.g., passing `style: "neon"` overrides the project's default style)
- When an override is detected, the response includes a `style_note` — mention this to the user so they're aware
- `style_directives` (free-text instructions) are always appended to prompts and cannot be overridden per-call

### Updating styles

Use `update_project_style` to change specific fields without affecting others. Common scenarios:
- User wants to change the color palette mid-project
- User wants to add a negative prompt after seeing unwanted patterns
- User refines the brand context as the project evolves

### Workflow Pattern 7: Setting Up Project Style

```
User: "I'm building a SaaS dashboard for a fintech startup"
You: Check for existing style → none found → ask about preferences

→ Use init_project_style with:
  - name: "Fintech Dashboard"
  - style: "minimal"
  - color_palette: "#1E3A5F, #4DA8DA, #F0F4F8"
  - brand_context: "Fintech SaaS, professional, trustworthy, clean"
  - style_directives: "Modern and data-driven aesthetic, blue tones"

→ All subsequent generate_web_asset calls automatically use these defaults
```

---

## Troubleshooting

| Issue                          | Solution                                    |
|--------------------------------|---------------------------------------------|
| Image looks too generic        | Add more specific details to the prompt      |
| Wrong aspect ratio             | Use the right `asset_type` for the use case  |
| Colors don't match brand       | Specify `color_palette` explicitly           |
| AI text in image is garbled    | Remove text from prompt; add text via CSS    |
| Style inconsistent across set  | Use `batch_generate` with shared parameters  |
| Image too busy for background  | Use `background` type + `minimal` style      |
| Generation fails               | Check API key, try simpler prompt first      |

---

## Quick Reference: Common Web Design Scenarios

### SaaS Landing Page
```json
{
  "hero": { "style": "gradient", "prompt": "Abstract tech visualization..." },
  "features": { "style": "flat", "asset_type": "illustration" },
  "background": { "style": "minimal", "prompt": "Subtle dot grid pattern..." }
}
```

### E-commerce Store
```json
{
  "hero": { "style": "photorealistic", "prompt": "Lifestyle product showcase..." },
  "products": { "style": "photorealistic", "asset_type": "product" },
  "banners": { "style": "gradient", "asset_type": "banner" }
}
```

### Portfolio Site
```json
{
  "hero": { "style": "3d", "prompt": "Creative abstract composition..." },
  "background": { "style": "watercolor", "prompt": "Soft artistic texture..." },
  "avatar": { "style": "flat", "asset_type": "avatar" }
}
```
