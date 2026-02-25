---
description: Frontend architecture — React 18 + TypeScript + TailwindCSS v4 with Apple-inspired design system, SSE streaming, and component patterns
---

# Frontend Skill

## Tech Stack
- **Framework**: React 18 + TypeScript + Vite 7
- **Styling**: TailwindCSS v4 with `@theme` design tokens
- **Fonts**: Inter (UI) + JetBrains Mono (code) via Google Fonts
- **Markdown**: react-markdown + remark-gfm
- **Icons**: Emoji-based (no external icon library)

## Design System — Branding Rules

### Color Palette (Logo-Derived)
- **Primary**: `#3ecfef` (cyan) — the logo's defining color
- **Tones**: `#5bb8d4`, `#88c8d8`, `#70b8cc`, `#a0d0e0`, `#c0dce6` — varying cyan/teal intensities
- **Text**: `#f5f5f7` (primary), `#a1a1aa` (secondary), `#636370` (tertiary)
- **Background**: `#000000` (pure black), `#030309`, `#0c0c14`, `#141420`
- **Borders**: `rgba(255,255,255,0.06)` and `rgba(255,255,255,0.1)`

### FORBIDDEN Colors
- ❌ No purple, pink, red, gold/yellow as accents
- ❌ No generic "AI" rainbow gradients
- ❌ No saturated primary colors (pure blue, green, orange)
- ✅ Only cyan/teal/silver/white derived from the logo

### Apple-Inspired Aesthetics
- **Glassmorphism**: `backdrop-filter: blur(40px) saturate(180%)` with low-opacity backgrounds
- **Animations**: Always use `cubic-bezier(0.16, 1, 0.3, 1)` easing (Apple spring)
- **Shadows**: Subtle — `box-shadow: 0 8px 32px rgba(0,0,0,0.4)`
- **Borders**: 1px with `rgba(255,255,255,0.06-0.1)`
- **Typography**: -0.01em letter-spacing on body, -0.02em on headings
- **Interactions**: `hover:scale-[1.02] active:scale-[0.98]` on buttons

## Component Architecture

```
App.tsx
├── Sidebar.tsx          — Logo, agent palette, status indicators
├── ChatArea.tsx          — Messages + WelcomeScreen + ChatInput
│   ├── MessageBubble.tsx — User/assistant messages with markdown
│   └── ChatInput.tsx     — Textarea with slash command palette
└── ArtifactPanel.tsx     — Code viewer, circuit diagram, results histogram
```

## SSE Streaming Pattern

```typescript
// Frontend reads SSE events from POST /api/chat/send
fetch('/api/chat/send', { method: 'POST', body: JSON.stringify({...}) })
  .then(async (res) => {
    const reader = res.body.getReader();
    // Parse: event: token|artifact|done + data: JSON
  });
```

## Key Files
- `src/index.css` — TailwindCSS v4 `@theme` tokens + global styles
- `src/types/index.ts` — TypeScript interfaces + AGENTS array
- `src/services/api.ts` — API client with SSE parser
- `src/hooks/useChat.ts` — Chat state management + streaming
