# Slipstream Documentation

This directory contains all design documents, specifications, and planning materials for the Slipstream AI swim coach project.

---

## Quick Links

| Document | Description |
|----------|-------------|
| [Technical Spec](./specs/technical-spec.md) | Complete system architecture and component specs |
| [User Journey](./specs/user-journey.md) | End-to-end user experience flow |
| [Implementation Plan](./plans/implementation-plan.md) | 9-branch parallel development plan |
| [Project Structure](./project-structure.md) | Directory structure and code organization |

---

## Documentation Structure

```
thoughts/
├── index.md                 # This file - documentation overview
├── project-structure.md     # Directory structure & code organization
│
├── specs/                   # Technical specifications
│   ├── technical-spec.md    # Main technical spec (architecture, components)
│   ├── user-journey.md      # User experience and interaction flow
│   ├── local-models.md      # ML models: pose estimation & STT
│   └── workout-modes.md     # Structured workout/interval system
│
├── plans/                   # Implementation planning
│   └── implementation-plan.md  # 9-branch development strategy
│
├── design/                  # Design decisions & diagrams
│   ├── dashboard-layouts.md # Dashboard UI options and layouts
│   └── data-flow-diagrams.md  # Visual data flow through system
│
└── hardware/                # Hardware setup
    ├── purchase-list.md     # Shopping list with links
    └── connection-diagram.md  # Physical connection diagrams
```

---

## Specifications

### [Technical Specification](./specs/technical-spec.md)
The main technical specification covering:
- System architecture (Jetson + MCP server + Claude)
- Component specifications (MCP tools, WebSocket, dashboard)
- STT integration architecture (log-based polling)
- Verification strategy

### [User Journey](./specs/user-journey.md)
Complete user experience flow through all system states:
- Wake up (Sleeping → Standby)
- Pre-swim planning
- Session start/swimming/rest
- Session end and summary
- Voice interaction design principles

### [Local Models](./specs/local-models.md)
Detailed spec for ML models running locally:
- YOLO11-Pose for pose estimation
- Whisper for speech-to-text
- Laptop verification strategy
- Post-estimation algorithms (stroke detection, rate calculation)

### [Workout Modes](./specs/workout-modes.md)
Structured workout and interval system:
- Workout data model (segments, state machine)
- MCP tools for workout control
- Automatic segment transitions
- WebSocket state push format

---

## Plans

### [Implementation Plan](./plans/implementation-plan.md)
Comprehensive plan for parallel development:
- 9 feature branches with dependencies
- Branch specifications with file structures
- Success criteria for each branch
- Merge strategy and team allocation

---

## Design

### [Dashboard Layouts](./design/dashboard-layouts.md)
Dashboard UI design exploration:
- Multiple layout options (A-H)
- State-aware adaptive layouts
- Voice indicator designs
- Recommendation matrix

### [Data Flow Diagrams](./design/data-flow-diagrams.md)
Visual representations of:
- High-level system overview
- Pose estimation pipeline
- STT pipeline
- Laptop verification flow
- What runs where (local vs cloud)

---

## Hardware

### [Purchase List](./hardware/purchase-list.md)
Complete shopping list with prices and links:
- Jetson Orin Nano Super (~$249)
- Reolink PoE Camera (~$80)
- PoE Switch (~$30-40)
- NVMe SSD (~$25-35)

### [Connection Diagram](./hardware/connection-diagram.md)
Physical setup documentation:
- Pool area layout
- Cable connections
- Network topology
- Power connections

---

## Document Status

| Document | Version | Status |
|----------|---------|--------|
| Technical Spec | 0.3.1 | Active |
| User Journey | 0.1.1 | Active |
| Local Models | 1.0.0 | Active |
| Workout Modes | 0.1.0 | Draft |
| Implementation Plan | 1.0.0 | Active |
| Project Structure | 1.0.0 | Active |
| Dashboard Layouts | 1.0.0 | Active |
| Data Flow Diagrams | 1.0.0 | Active |
| Purchase List | 1.0.0 | Active |
| Connection Diagram | 1.0.0 | Active |

---

## Reading Order

For someone new to the project, recommended reading order:

1. **[User Journey](./specs/user-journey.md)** - Understand what we're building from user perspective
2. **[Technical Spec](./specs/technical-spec.md)** - Understand the architecture
3. **[Local Models](./specs/local-models.md)** - Understand the ML components
4. **[Implementation Plan](./plans/implementation-plan.md)** - Understand how we'll build it
5. **[Project Structure](./project-structure.md)** - Understand the codebase organization
