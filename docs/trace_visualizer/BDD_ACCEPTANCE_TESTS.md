# BDD Acceptance Tests - Trace Visualizer UI

**Feature**: 008-trace-visualizer
**User Story 1**: As a developer, I want to load a trace and see a waterfall visualization
**Test Date**: 2025-12-17
**Test Trace**: `data/traces/basic_conversation.trace.json`

---

## Test Setup

### Prerequisites
1. All UI files exist in `logui/`:
   - ✅ index.html (4.0K)
   - ✅ styles.css (6.7K)
   - ✅ trace-renderer.js (4.9K)
   - ✅ waterfall.js (5.6K)

2. Test trace exists:
   - ✅ data/traces/basic_conversation.trace.json (5.1K, valid JSON)

3. Trace structure:
   - Trace ID: `basic-conversation-demo`
   - Duration: 3137ms
   - Turns: 3
   - Total Steps: 8

### Trace Content Details
**Turn 1** (1822ms, 4 steps):
- Step 1: Logic - Parse user input (12ms)
- Step 2: LLM Call - claude-sonnet-4-5 (501ms)
- Step 3: Tool Call - get_weather (1002ms) ⭐ LONGEST STEP
- Step 4: LLM Call - Format response (305ms)

**Turn 2** (404ms, 1 step):
- Step 1: LLM Call - "What about tomorrow?" (404ms)

**Turn 3** (910ms, 3 steps):
- Step 1: LLM Call - "How about London?" (405ms)
- Step 2: Tool Call - get_weather (504ms, ERROR)
- Step 3: Error - APITimeoutError (0ms)

---

## T042: BDD Test 1.1 - Load Trace with 3 Turns

**Given**: User opens logui/index.html in browser
**When**: User loads data/traces/basic_conversation.trace.json
**Then**: User should see 3 turn bars with labels

### Test Steps
1. Open `logui/index.html` in web browser
2. Click "📁 Carregar Trace" button OR drag-and-drop the trace file
3. Select `data/traces/basic_conversation.trace.json`

### Expected Results
- [ ] File status shows: "✅ basic_conversation.trace.json carregado"
- [ ] Trace Info panel displays:
  - Trace ID: `basic-conversation-demo`
  - Duração: `3137ms`
  - Turns: `3`
  - Steps: `8`
- [ ] Waterfall section visible with 3 turn containers
- [ ] Turn headers show:
  - "Turn 1" with "1822ms" and "4 steps"
  - "Turn 2" with "404ms" and "1 step"
  - "Turn 3" with "910ms" and "3 steps"
- [ ] Each turn has a purple gradient bar below the header
- [ ] Turn bars are scaled by duration (Turn 1 longest, Turn 2 shortest)

### Validation Result
**Status**: ⬜ PENDING (Manual test required)
**Tester**: _____________
**Notes**: _____________

---

## T043: BDD Test 1.2 - Expand Turn and Verify Steps

**Given**: Trace is loaded with 3 turns visible
**When**: User clicks on Turn 1 to expand
**Then**: User should see 4 sub-bars with correct durations

### Test Steps
1. Click on "Turn 1" header
2. Observe the expansion animation
3. Verify step details

### Expected Results
- [ ] Turn toggle changes from "▶" to "▼"
- [ ] Steps container expands smoothly (CSS transition)
- [ ] Turn 1 shows 4 steps:
  1. "⚙️ Logic: Parse user input" - 12ms (Orange bar)
  2. "🤖 LLM Call: claude-sonnet-4-5" - 501ms (Blue bar)
  3. "🔧 Tool: get_weather" - 1002ms (Green bar) ⭐ LONGEST
  4. "🤖 LLM Call: claude-sonnet-4-5" - 305ms (Blue bar)
- [ ] Step bars are color-coded correctly:
  - Logic: Orange (#ed8936)
  - LLM Call: Blue (#4299e1)
  - Tool Call: Green (#48bb78)
- [ ] Step bars are scaled by duration (Tool Call widest)
- [ ] Duration sum validation: 12 + 501 + 1002 + 305 = 1820ms ≈ 1822ms ✅
  - (Small variance expected due to timestamp precision)

### Additional Validation
- [ ] Click Turn 1 again to collapse → Steps hidden, toggle shows "▶"
- [ ] Expand Turn 3 → See 3 steps including error step (red bar)
- [ ] Click on any step → Step highlights with blue background

### Validation Result
**Status**: ⬜ PENDING (Manual test required)
**Tester**: _____________
**Notes**: _____________

---

## T044: BDD Test 1.3 - Identify Slowest Step (Visual Inspection)

**Given**: Turn 1 is expanded showing all 4 steps
**When**: User visually inspects the waterfall bars
**Then**: User can identify the slowest step in <10 seconds

### Test Steps
1. Ensure Turn 1 is expanded
2. Set timer for 10 seconds
3. Visually identify the longest (widest) bar
4. Stop timer

### Expected Results
- [ ] Time to identify: ______ seconds (<10s required)
- [ ] Correctly identified step: "🔧 Tool: get_weather" (1002ms)
- [ ] Visual cue: Green bar is clearly wider than blue/orange bars
- [ ] Duration label visible: "1002ms" displayed next to step name
- [ ] No need to read exact numbers - bar width makes it obvious

### Usability Validation
- [ ] Bar width difference is visually obvious (not requiring precision measurement)
- [ ] Color coding helps distinguish span types at a glance
- [ ] Duration labels provide numerical confirmation
- [ ] Hover effect works (bar slightly dims on mouse over)

### Advanced Scenario (Optional)
- [ ] Expand all 3 turns
- [ ] Identify slowest step across entire trace: Turn 1 → Tool Call (1002ms)
- [ ] Identify turn with error: Turn 3 (red error bar visible)

### Validation Result
**Status**: ⬜ PENDING (Manual test required)
**Tester**: _____________
**Time Taken**: ______ seconds
**Notes**: _____________

---

## Summary Checklist

### File Validation
- [x] All UI files exist and have non-zero size
- [x] Test trace is valid JSON
- [x] Trace has expected structure (3 turns, 8 steps)

### Manual Testing
- [ ] T042: Load trace → See 3 turn bars
- [ ] T043: Expand turn → See steps with correct durations
- [ ] T044: Identify slowest step in <10s

### Expected User Experience
- [ ] No errors in browser console
- [ ] Smooth animations (expand/collapse transitions)
- [ ] Responsive design works on different screen sizes
- [ ] Drag-and-drop works as alternative to file input
- [ ] Error message appears for invalid JSON files

---

## How to Execute Tests

### Option 1: Local File System
```bash
# Open in default browser
open logui/index.html

# Or specify browser
open -a "Google Chrome" logui/index.html
open -a "Firefox" logui/index.html
```

### Option 2: Local Server (Recommended for CORS)
```bash
# Python 3 simple HTTP server
cd logui
python3 -m http.server 8000

# Then open: http://localhost:8000
```

### Test Data Location
```bash
# Absolute path to trace file
/Users/fulvio/Projects/synth-lab/data/traces/basic_conversation.trace.json

# Or navigate from project root
data/traces/basic_conversation.trace.json
```

---

## Sign-Off

**All Tests Passed**: ⬜ YES / ⬜ NO
**Tester Name**: _____________
**Date**: _____________
**Browser Tested**: _____________
**Notes/Issues**: _____________

---

## Next Steps After BDD Tests Pass

1. **Phase 4**: Add detail panel (click step → show JSON attributes)
2. **Phase 5**: Performance optimization for large traces
3. **Phase 6**: Export waterfall as PNG/SVG
4. **Phase 7**: Integration with synth-lab CLI

**Current Progress**: Phase 3 Complete (pending BDD validation) ✅
