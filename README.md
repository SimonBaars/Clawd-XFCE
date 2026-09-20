# Clippy for XFCE

A native XFCE companion that sits on your desktop, talks in a speech bubble, remembers past chats, looks at the screen, and uses **Claude Computer Use** to click, type, and run tools.

## What you get

- Authentic Office Assistant animations (43 of them) plus the original sound set
- Always-on-top paperclip that you can drag, right-click, or summon with `Ctrl+Alt+C`
- Speech-bubble chat with conversation history
- Long-term memory across chats
- Live desktop context: windows, workspace, clipboard, time
- Screen capture for Claude, with Clippy hidden so it does not photobomb itself
- Computer use: screenshot, zoom, click, drag, scroll, type, keys
- Bash and a precise text-editor tool
- XFCE integration: `.desktop` launcher, tray icon, optional autostart

## Requirements

- XFCE on X11 (this laptop profile: XFCE 4.20)
- Python 3.11+ with GTK 3, PyGObject, Wnck
- An Anthropic API key

System packages already used: `python-gobject`, `gtk3`, `libwnck3`, `libayatana-appindicator`, `libkeybinder3`, `xclip`, `python-pillow`.

## Install

```bash
make install
clippy
```

Or:

```bash
./scripts/install.sh --dev
```

The first run opens settings if no key is found. Clippy also looks for `ANTHROPIC_API_KEY` and common local config files.

## Use

- Click Clippy or press `Ctrl+Alt+C` to talk
- Ask it to look at the screen, click things, edit files, or remember facts
- Right-click Clippy for New chat, History, Settings, Hide, Quit
- Settings: model, computer-use confirmations, screenshot policy, size, sounds, autostart

```bash
clippy              # start the companion
clippy --ask        # show the speech bubble
clippy --new        # start a fresh chat (keeps long-term memory)
clippy --say "…"    # send a message to the running Clippy
clippy --quit
clippy --prepare    # extract sprites/sounds and exit
```

Destructive shell commands always ask first unless you set confirmations to “never”.

## Tests

```bash
make test
```

A live API check runs only when `ANTHROPIC_API_KEY` is set.

## Assets

Sprites, animation data, and sounds come from [clippy.js](https://github.com/pi0/clippyjs) (extracted from the original Office Assistant). Clippy the character remains a Microsoft creation. Application code is MIT.

Re-download:

```bash
python3 scripts/fetch_sprites.py
```
