- [Fireball](https://motionarray.com/stock-motion-graphics/free-fireball-stock-video-footage-53/)
- [Dragon Breath](https://freesound.org/people/CGEffex/sounds/94102/)
- [Comic Runes](https://www.dafont.com/comicrunes.font) (`fonts/ComicRunes.otf`) — by
  Adrian Candela ([behance.net/takuminokami](https://www.behance.net/takuminokami)),
  Creative Commons Attribution-NoDerivatives. Used for the Edit/Delete buttons on
  the Vendors page.

## Regenerating the processed login-transition assets

The raw masters (`originals/fireball.mov`, the original `originals/dragon-breath.flac`) are not
committed to git (see `.gitignore` — `*.mov`; the flac is kept since it's
small). If you need to redo `finals/fireball.webm` or `finals/dragon-breath.mp3` from those
originals — e.g. to retune timing/opacity, or because a new source clip was
dropped in — here's exactly how the current versions were produced.

Tooling: [ffmpeg](https://ffmpeg.org/) with a `libvpx-vp9` encoder (needed for
the video's alpha channel). Installed here via
`winget install --id Gyan.FFmpeg -e`.

### finals/fireball.webm (from originals/fireball.mov)

```sh
ffmpeg -y -i originals/fireball.mov \
  -map_metadata -1 -map_chapters -1 \
  -vf "scale=1280:720:flags=lanczos,eq=gamma=0.55:saturation=1.7,format=yuva420p,geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':a='min(255,lum(X,Y)*4.5)'" \
  -c:v libvpx-vp9 -pix_fmt yuva420p -crf 32 -b:v 0 -cpu-used 2 -auto-alt-ref 0 -an \
  finals/fireball.webm
```

What each piece does, in case it needs retuning:

- `-map_metadata -1 -map_chapters -1` — strips the source .mov's metadata
  (it was a QuickTime file; leftover `qt` brand tags confused some
  players when carried into the WebM container).
- `scale=1280:720` — the source was 4K (4096x2304); this crops the size
  (and therefore file size) down to something reasonable for a fullscreen
  web overlay. Bump this up if the flame looks soft on very large displays.
- `eq=gamma=0.55:saturation=1.7` — brightens midtones (gamma < 1 lifts
  everything except true black, which stays exactly 0 — this preserves
  the transparency in the next step) and boosts color saturation so the
  flame reads as vivid orange/red rather than pale. Raise `saturation`
  for more vivid color; raise `gamma` toward 1.0 to reduce the brightening.
- `format=yuva420p,geq=...:a='min(255,lum(X,Y)*4.5)'` — this is the real
  alpha-transparency step. It derives each pixel's alpha (opacity) from
  its own brightness (luminance), amplified 4.5x and clamped to fully
  opaque (255). The source footage has a pure black background, so black
  pixels get alpha 0 (fully transparent, revealing the page underneath)
  while any moderately-lit flame pixel gets pushed to fully opaque. This
  went through several iterations — an earlier `a='lum(X,Y)'` (no boost)
  and `a='lum(X,Y)*2.2'` both left the flame body visibly see-through;
  4.5x was the multiplier that finally read as solid. If a future source
  clip looks translucent again, raise this multiplier; if it looks like a
  too-hard silhouette with no soft smoky edges, lower it.
- `-c:v libvpx-vp9 -pix_fmt yuva420p` — VP9 in a WebM container is one of
  the few web video codecs that support a real alpha channel (Chrome/
  Firefox; **not Safari** — there's no fallback for Safari currently).
- `-auto-alt-ref 0` — required; libvpx's automatic alt-ref frames corrupt
  alpha-channel playback if left on.
- `-crf 32 -b:v 0 -cpu-used 2` — constant-quality VBR encoding. Lower
  `-crf` = higher quality/bigger file.
- `-an` — drops audio (the source clip had none of interest; sound is
  handled by the separate `finals/dragon-breath.mp3`, played in sync by
  `App.vue`, not muxed into the video).

### finals/dragon-breath.mp3 (from originals/dragon-breath.flac)

The original file is 5.18s but opens with about a second of near-silence
before the actual roar. That lead-in was located with:

```sh
ffmpeg -i originals/dragon-breath.flac -af "silencedetect=noise=-30dB:d=0.1" -f null -
```

which reported silence from `0` to `1.032608`, loud content from
`1.032608` to `4.730408`, then silence again to the end. The clip was
then trimmed to start right at the roar's onset (so it can be played in
lockstep with the video's own immediate fire onset — see `App.vue`, both
start playing together when the transition triggers) and given a short
fade-out instead of an abrupt cut:

```sh
ffmpeg -y -ss 1.032608 -to 4.9 -i originals/dragon-breath.flac \
  -af "afade=t=out:st=4.6:d=0.3" \
  -c:a libmp3lame -b:a 160k \
  finals/dragon-breath.mp3
```

If a different source sound is dropped in later, rerun the
`silencedetect` pass first to find its actual onset — don't reuse
`1.032608` blindly, that's specific to this recording. `-to` should land
a little past where the loud content ends (per silencedetect), and
`afade`'s `st` (fade start) a bit before that, so the fade covers the
natural tail without an audible hard cutoff.

### finals/fireball-reverse.webm and finals/dragon-breath-reverse.mp3 (sign-out transition)

Played forward by `App.vue` on sign-out to get the visual/audio mirror of
the login transition (flame gathering in rather than dissipating, roar
played backwards). A true reverse (rather than a hand-scrubbed
`currentTime`, which is what `<video>`'s lack of negative `playbackRate`
support would otherwise force) needs whole-clip filters
(`reverse`/`areverse`), which is why these are pre-rendered files instead
of something done at runtime.

**fireball-reverse.webm is built from `originals/fireball.mov`, not from
`finals/fireball.webm`** — i.e. it's the same recipe as `finals/fireball.webm`
above with `reverse` appended to the end of the `-vf` chain, not a
re-encode of the already-alpha-baked file:

```sh
ffmpeg -y -i originals/fireball.mov \
  -map_metadata -1 -map_chapters -1 \
  -vf "scale=1280:720:flags=lanczos,eq=gamma=0.55:saturation=1.7,format=yuva420p,geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':a='min(255,lum(X,Y)*4.5)',reverse" \
  -c:v libvpx-vp9 -pix_fmt yuva420p -crf 32 -b:v 0 -cpu-used 2 -auto-alt-ref 0 -an \
  finals/fireball-reverse.webm
```

This matters: an earlier version of this file was produced by re-encoding
`finals/fireball.webm` itself (`ffmpeg -i finals/fireball.webm -vf reverse
...`), decoding its already-baked alpha side-stream, reversing frame
order, and re-encoding. That round-trip silently lost the alpha channel —
ffmpeg's filtergraph negotiated the decode as plain `yuv420p` (no alpha
plane) since `reverse` alone doesn't require one, and the `-pix_fmt
yuva420p` on the encode side then just padded a fake fully-opaque channel
onto it, producing a solid opaque video with no transparency at all
(visible in the app as a black rectangle instead of the fire receding to
reveal the page). Deriving alpha fresh from the raw master via `geq`
(same as the forward file) and only reordering frames afterward with
`reverse` avoids that failure mode entirely — always regenerate from
`originals/fireball.mov`, not from `finals/fireball.webm`, if this needs
retuning. `originals/fireball.mov` isn't committed (see the note above)
and needs re-downloading from the source in the first bullet at the top
of this file if it's not present locally.

```sh
ffmpeg -y -i finals/dragon-breath.mp3 -af areverse \
  -c:a libmp3lame -b:a 160k \
  finals/dragon-breath-reverse.mp3
```

The audio doesn't have an analogous gotcha — `dragon-breath-reverse.mp3`
is a straightforward `areverse` of the already-finished
`finals/dragon-breath.mp3`, no alpha channel involved.
