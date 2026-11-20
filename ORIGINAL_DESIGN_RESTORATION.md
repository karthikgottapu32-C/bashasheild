# BHASHASHIELD — ORIGINAL DESIGN RESTORATION GUIDE

This document serves as the authoritative restoration manual for the original BhashaShield visual identity, theme system, 3D shield component, custom cursor, and cinematic breakup transition system.

---

## 1. Original Visual Architecture & Design Structure

The original BhashaShield visual identity is based on a high-contrast cybernetic aesthetic:
- **Art Direction**: Monolithic obsidian surfaces, high-specular reflective glass facets, electric lime energy vectors, and responsive 3D WebGL cyber shield.
- **Theme Engine**: Dynamic 60/30/10 proportional color system governed by CSS variables on `:root` and controlled by `ThemeContext`.
- **Default Theme**: `obsidian-lime` (Palette 06).
- **Interactive Layers**:
  1. `CustomCursor.tsx`: 3-layer GPU-accelerated cursor (central dot, 28px inner ring with accent fill, 44px outer ring, canvas velocity spark particles).
  2. `CinematicFragmentationTransition.tsx`: 18 obsidian polygonal glass shards (`clipPath`), angular luminous light sweep, canvas spark trajectory, route-specific motion vectors (`radial_pulse`, `scanner_shear`, `telemetry_lift`, `shield_convergence`, `omnidirectional`).
  3. `CyberShield3D.tsx`: Three.js procedural metallic faceted shield with glowing wireframe edges, energy pulse rings, and interactive mouse parallax.

---

## 2. Original Color Palette & Exact Hexadecimal Codes

### Core 60/30/10 Theme: Obsidian Lime (Palette 06)
- **Primary (60%) — Obsidian Black**: `#090B09` (Backgrounds, monolithic panels, deep canvas)
- **Secondary (30%) — Soft White**: `#F2F4EF` (Typography, headings, subtle borders, card structures)
- **Accent (10%) — Electric Lime**: `#B7F34A` (Threat indicators, interactive buttons, neon glow, shard glints)

#### Supporting Semantic Palette
- **Success / Clean**: `#32D74B` (Emerald)
- **Warning / Suspicious**: `#FFD60A` (Amber)
- **Danger / Malicious**: `#FF453A` (Coral)
- **Telemetry / System**: `#5AC8FA` (Electric Sky Blue)

### All 6 Preserved Original Palettes in `frontend/src/theme/palettes.ts`:
1. `midnight-lime`: Primary `#101C35`, Secondary `#F4F6F0`, Accent `#B7F34A`
2. `navy-coral`: Primary `#101C35`, Secondary `#F4F6F0`, Accent `#FF665C`
3. `forest-green`: Primary `#123B32`, Secondary `#F5F7F2`, Accent `#A6D96A`
4. `electric-purple`: Primary `#17142B`, Secondary `#F3F3F7`, Accent `#925BFF`
5. `original-cyber`: Primary `#070B14`, Secondary `#8B9BB4`, Accent `#00E5FF`
6. `obsidian-lime`: Primary `#090B09`, Secondary `#F2F4EF`, Accent `#B7F34A` (Default)

---

## 3. Original Component Structure

```text
frontend/src/
├── components/
│   ├── CinematicFragmentationTransition.tsx  # 18 glass shards + canvas sparks + light sweep
│   ├── CustomCursor.tsx                      # 3-layer GPU cursor + interactive morphing
│   ├── CyberShield3D.tsx                     # Three.js 3D faceted cyber shield
│   ├── EvidenceHighlighter.tsx               # Threat token & span highlighter
│   ├── Navbar.tsx                            # Desktop/mobile nav + 60/30/10 studio trigger
│   └── RiskGauge.tsx                         # Circular risk indicator
├── views/
│   ├── LandingPageView.tsx                   # Hero 3D shield + typography + feature matrix
│   ├── TextGuardView.tsx                     # Real-time scan terminal + attack presets
│   ├── DashboardView.tsx                     # Threat telemetry & analytics
│   └── EvaluationView.tsx                    # Empirical benchmark KPIs & confusion matrix
├── theme/
│   ├── palettes.ts                           # Palette definitions (6 original themes)
│   ├── ThemeContext.tsx                      # React context injecting CSS root variables
│   ├── ColorPaletteSelector.tsx              # Palette switching modal
│   └── ColorRatioControl.tsx                 # 60/30/10 proportional sliders
├── services/
│   └── api.ts                                # FastAPI Axios integration
└── App.tsx                                   # Lifecycle router with midpoint transition swap
```

---

## 4. Backup Locations

The complete original frontend is archived and verified in two independent locations:

1. **Uncompressed Directory Backup**:
   `backups/frontend-before-ai-lab/`
2. **Compressed Zip Archive**:
   `backups/frontend-before-ai-lab.zip`

Both backups contain all source files, components, configuration files (`package.json`, `vite.config.ts`, `tailwind.config.js`), scripts, and public assets.

---

## 5. Exact Restoration Procedure

To revert the frontend to its exact state before the AI Lab transformation:

### Option A: Restoring from Directory Backup
In PowerShell or Terminal from the project root (`C:\Users\karth\Downloads\hack with aditya`):

```powershell
# 1. Remove current frontend source (keep node_modules to avoid re-installing)
Remove-Item -Recurse -Force frontend\src, frontend\public, frontend\scripts

# 2. Copy the backup files back into frontend
robocopy backups\frontend-before-ai-lab frontend /E /XD node_modules dist

# 3. Verify compilation
cd frontend
npm run build
```

### Option B: Restoring from Zip Archive
```powershell
# 1. Expand archive over frontend directory
Expand-Archive -Path backups\frontend-before-ai-lab.zip -DestinationPath frontend -Force

# 2. Verify compilation
cd frontend
npm run build
```

### Option C: In-App Palette Switch
If you wish to view the original Obsidian Lime design without modifying code files:
1. Open the website at `http://localhost:5173`.
2. Click the **60/30/10 Theme Studio** button in the navigation bar.
3. Select **Palette 06: OBSIDIAN LIME**.
4. The system immediately applies `#090B09`, `#F2F4EF`, and `#B7F34A` across all components, 3D shield, cursor, and transitions.
