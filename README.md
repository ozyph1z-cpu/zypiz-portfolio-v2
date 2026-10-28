# Zypiz portfolio

Live: https://ozyph1z-cpu.github.io/zypiz-portfolio-v2/

A static site. Every word on the page lives in `content.json`; `build.py` turns it into `index.html`.

## Change the site

1. Edit `content.json`.
2. Run:

   ```
   python build.py
   ```

   It checks the JSON first. If a field is missing, has the wrong type, points to a missing video or image,
   links to a section that doesn't exist, or still has a `TODO` in published text, it stops, lists every
   problem, and writes nothing. When it passes it writes `index.html`, `sitemap.xml` and `robots.txt`.
3. Commit and push. GitHub Pages serves the repo root (`main` branch, `/`).

Python 3.9+ and nothing else (standard library only).

## Files

| Path | What it is |
| --- | --- |
| `content.json` | All content: hero, stats, work, cases, systems, process, tools, about, FAQ, contacts, SEO |
| `src/page.html` | Page skeleton with `{{placeholders}}` |
| `src/style.css`, `src/main.js` | Inlined into `index.html` by the build. JS only adds interactions; the page works without it |
| `build.py` | Validation + render |
| `assets/` | Images. Video posters are `poster-<key>.webp`, tool logos `logo-<id>.png/svg` |
| `media/<key>.mp4` | 6 s silent loop for the card |
| `media/full/<key>.mp4` | Full cut with sound (player), each under 3 MB |
| `media/reel_<key>.mp4` | 3.4 s cuts for the hero phone |
| `og.jpg`, `apple-touch-icon.png`, `favicon.webp` | Share image (1200×630) and icons |

## Content rules

- Text is escaped. The only markup allowed is `<em>…</em>` (lime highlight).
- A new video needs a `work` entry plus the three files `media/<k>.mp4`, `media/full/<k>.mp4` and `assets/poster-<k>.webp`.
- `cases`, `faq` items have `"publish"`: `false` keeps them out of the page until they are real.
- `testimonials` renders only when the list is not empty. Add a quote only with the client's permission.
- Numbers must be real and say what they measure (`"measures"` on each case result).

## Open items (hidden until filled)

- FAQ: delivery time, weekly volume, free or paid test.
- Crown Cards case: Ads Manager numbers (CTR, hook rate, CPA or ROAS, named) and permission.
- Proof screenshots for each case (`"proof": "assets/proof-….webp"`).
- Client testimonials.

## Checks

`python build.py --check` validates and fails if `index.html` is not what the build would produce.
The GitHub Action in `.github/workflows/build.yml` runs it on every push.

Note: GitHub Pages serves this site under `/zypiz-portfolio-v2/`, so search engines read `robots.txt` only from the
domain root. Submit `sitemap.xml` in Google Search Console, or move the site to a custom domain to make `robots.txt` count.
