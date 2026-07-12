# Kung Fu Chess — Design Guide: Implementation and Tests

> Source: course design-guide document supplied by the bootcamp instructor (PDF, last modified 2026-07-09). This file is the **authoritative architecture reference** for this project. See [CLAUDE.md](CLAUDE.md) for how it relates to the older feature-requirements doc ([kong_fu_chess_requirements.md](kong_fu_chess_requirements.md)).

## 1. Purpose

This guide governs the design and implementation of Kung Fu Chess using disciplined, test-driven, AI-assisted software engineering. The goal is not only to finish a game but to:

1. Break a vague game idea into small, testable requirements.
2. Separate model, controller, real-time game logic, and rendering.
3. Write unit tests before implementation.
4. Write text-based integration tests that validate visible behavior.
5. Use an LLM as a junior development assistant, not as an uncontrolled authority.
6. Refactor safely under test coverage.
7. Explain design decisions and prove correctness through tests.

## 2. Engineering Rules

Every development step follows the same loop:

```
Requirement → test plan → failing tests → implementation → refactor → AI review → peer review → commit
```

Required habits:

- Keep game logic independent of the drawing library.
- Write unit tests for pure logic before connecting UI.
- Use fake clocks / explicit elapsed-time calls instead of real sleeping in tests.
- Keep rendering thin and replaceable.
- Avoid hidden global state.
- Use small classes with clear responsibility.
- Commit only when tests pass.
- Include a short explanation of each nontrivial design decision.

### AI-assisted development habit

Ask the LLM for small, reviewable steps ("write tests for this requirement", "propose the smallest class boundary", "review this diff for responsibility leakage", "find missing edge cases", "explain why this test fails") — never "build the whole game" or "fix my code" without context.

### AI debugging protocol

Give exact reproduction steps, expected vs. actual behavior, and the smallest relevant code/test. State which layer is suspected: Controller, GameEngine, RuleEngine, RealTimeArbiter, Board, Renderer, or TextTestRunner. Ask the LLM to identify the responsible layer and confirming evidence *before* asking for a fix. Treat large unexplained rewrites as suspicious.

## 3. Scope of the Game

Kung Fu Chess is a real-time chess-like game: pieces move by chess movement patterns, but moves are not instantaneous — a piece travels toward its destination at fixed speed after a click.

### Common Route Rules (required for everyone)

1. Board is any rectangular size inferred from a textual description.
2. Pieces use normal chess letters: K, Q, R, B, N, P.
3. Piece color is encoded by prefix: `w`/`b` (e.g. `wK`, `bR`).
4. `.` means an empty square.
5. No check, checkmate, castling, en passant, or promotion.
6. A king can be captured.
7. Capturing the opponent king ends the game.
8. A piece moves only according to its movement rule.
9. Sliding pieces do not pass through blocking pieces.
10. Movement has a fixed speed.
11. Tests use a fixed cell size in pixels.
12. UI rendering uses only the supplied drawing/image library.
13. The logical board changes only when a moving piece arrives.
14. The text integration DSL contains only `Board`, `click`, `wait`, `print board`.
15. `print board` is the only integration-test assertion mechanism.

**One active motion at a time (common route):** if a legal-looking move is requested while a motion is already active, `GameEngine` rejects it with reason `"motion_in_progress"`. No new motion starts and `Board` remains unchanged.

### Extra Route Rules (one per strong team, after common route is clean)

1. Simultaneous movement of multiple pieces.
2. Cooldown after movement.
3. Collision between moving pieces.
4. Cancellation when the destination becomes occupied before arrival.
5. Replay file support.
6. Basic bot strategy.
7. Visual polish without changing the model.

An extra feature is architecturally acceptable only when it extends the appropriate layer without reversing dependency direction or merging unrelated responsibilities (e.g. cooldown belongs in movement/game-state coordination, not the renderer; replay belongs around command/event recording, not inside `Board`). If a feature can't be added without rewriting the common route, the design is rejected and refactored first.

> **⚠️ Known conflict with [kong_fu_chess_requirements.md](kong_fu_chess_requirements.md):** the older requirements doc lists cooldown, move notation, score, and player-name display as **MVP/mandatory**. This design guide places cooldown in the **extra route** (optional, one-per-team) and does not mention notation/score/player-names at all in the common route. Resolve this with the user before treating those features as in-scope for the refactor's first passes.

## 4. Core Design Decision: Testable Layers

| Layer | Owns | Must not own |
|---|---|---|
| Model | Board coordinates, piece identity, logical occupancy, piece lifecycle state | Pixels, clicks, rendering, script parsing, movement rules, timing |
| Movement rules | Movement geometry per piece type, calculated from Board and Piece data | Game commands, elapsed time, animation, rendering, input handling |
| RuleEngine | Read-only legality validation for a requested move | Board mutation, animation, click interpretation, game-over state |
| GameEngine | Application-service coordination: game-over guard, validation delegation, starting legal motions, wait delegation, snapshots | Piece-specific movement logic, rendering, input parsing, DSL parsing, pixel mapping |
| RealTimeArbiter | Active Motion objects, simulated time advancement, arrival resolution, capture events | Chess legality, clicks, rendering, script parsing |
| Controller | Click interpretation and selected-cell state | Chess legality, Board mutation, rendering, timing |
| Renderer | Visual drawing from a read-only GameSnapshot | Game rules, Board mutation, input parsing, text-test logic |
| TextTestRunner | Script parsing and driving the public command path | Movement rules, direct Board mutation, duplicated game logic |
| Text I/O (BoardParser/BoardPrinter) | Textual setup and logical board output | Movement rules, command execution, rendering, test assertions beyond text comparison |

Every layer must be testable without the layers above it. The dependency direction never points from model to UI.

Pattern vocabulary: `GameEngine` = Application Service, `RuleEngine` = Validation Service, `PieceRules` = Strategy per piece type, `BoardMapper` = Coordinate Adapter, `Renderer` = View Adapter, `GameSnapshot` = read-only view model/DTO, `TextTestRunner` = command-script test harness.

## 5. Package Structure

```
kungfu_chess/
  model/
    position.py
    piece.py
    board.py
    game_state.py
  rules/
    piece_rules.py
    rule_engine.py
  realtime/
    motion.py
    real_time_arbiter.py
  engine/
    game_engine.py
  input/
    board_mapper.py
    controller.py
  io/
    board_parser.py
    board_printer.py
  view/
    renderer.py
    image_view.py
  texttests/
    script_parser.py
    script_runner.py
  app.py

tests/
  unit/
    test_position.py
    test_board.py
    test_piece_rules.py
    test_rule_engine.py
    test_real_time_arbiter.py
    test_game_engine.py
    test_board_mapper.py
    test_controller.py
    test_board_parser.py
    test_board_printer.py
  integration/
    scripts/
      01_board_parsing.kfc
      02_click_to_move.kfc
      03_rook_moves.kfc
      04_invalid_moves.kfc
      05_capture.kfc
      06_game_over.kfc
    test_text_scripts.py
```

Dependency chain: View → GameState snapshots. Controller → BoardMapper + GameEngine. GameEngine → Board, RuleEngine, RealTimeArbiter. RuleEngine → Board, PieceRules. PieceRules → Board, Position data only. BoardParser/BoardPrinter → model data only (not Controller/RuleEngine/RealTimeArbiter/Renderer). TextTestRunner → BoardParser, BoardPrinter, Controller, GameEngine. Model depends on nothing above it.

There is **no** `model/move.py` in the common route — a move request is just source/destination cells at the API boundary; the engine returns a `MoveResult`.

## 6. Model Design

### Position
Value object: `row: int`, `col: int`. Equality + readable repr. No board-bounds checking (that's `Board`'s job). Doesn't know board size, rendering, movement rules, or input coordinates.

### Piece
Fields: `id` (unique stable id), `color` (white/black), `kind` (king/queen/rook/bishop/knight/pawn), `cell: Position`, `state` (idle/moving/captured).

`Piece.state` is **only** a lifecycle flag — it does not store path, destination, elapsed time, speed, interpolation, or arrival logic (that's `Motion`/`RealTimeArbiter`'s job). IDs are assigned at creation time (by `BoardParser` or a `PieceFactory`); duplicate IDs are invalid if stable identity is used for motion tracking/snapshots. A piece never knows about the renderer, mouse clicks, pixels, or text-test syntax.

### Board
Owns: width/height, add/remove piece, query piece at cell, bounds check, `move_piece` (assumes validation already happened — does not call `RuleEngine`), reject duplicate occupancy. Board does **not** contain chess movement rules — it knows what exists, not what's legal.

## 7. Movement Rule Design

Each piece type has a small, **stateless** rule class:

```
legal_destinations(board, piece) -> set[Position]
```

Enemy-occupied destinations may be legal (capture-eligible); the rule class never mutates, captures, or moves pieces itself.

- Rook: horizontal/vertical sliding until blocked.
- Bishop: diagonal sliding until blocked.
- Queen: rook + bishop.
- Knight: L-shaped jumps, ignores blockers.
- King: one square any direction.
- Pawn (simplified): white moves one row up, black one row down; captures one diagonal step forward; **no** two-step start, **no** en passant, **no** promotion.

Fixed implementation order: Rook → Bishop → Queen → Knight → King → Pawn.

## 8. RuleEngine Design

Answers: *given source/destination, is this command legal now?*

- Rejects: outside board, empty source, friendly-occupied destination, illegal-per-piece-rule moves.
- Read-only w.r.t. Board — never mutates, never starts motions, never touches game-over state.
- Result shape: `MoveValidation { is_valid: bool, reason: string }`. `reason` is always present: `"ok"` when valid, else a stable machine-readable string (`"outside_board"`, `"empty_source"`, `"friendly_destination"`, `"illegal_piece_move"`).
- Game-over is **not** RuleEngine's job — `GameEngine.request_move` checks `game_over` before ever calling RuleEngine, short-circuiting with `MoveResult(reason="game_over")`.
- The DSL never asserts these reasons directly — only unit tests do.

## 9. GameEngine Design

The application-service coordinator and public command boundary used by Controller and TextTestRunner. Answers: is the game over? is a motion already active? does this move pass RuleEngine? should a validated move start a Motion? should time advance? what snapshot goes to the renderer?

Responsibilities: hold/reference `GameState` (incl. `game_over`); reject `request_move` when `game_over` (`MoveResult(reason="game_over")`) or when a motion is already active (`MoveResult(reason="motion_in_progress")`); call `RuleEngine.validate_move` only after those guards pass; start motions via `RealTimeArbiter`; delegate `wait(ms)` to `RealTimeArbiter.advance_time(ms)`; receive king-capture notification from arrival resolution and set `game_over`; build `GameSnapshot`.

Must **not** contain piece-specific movement logic, pixel mapping, rendering code, text parsing, or test-runner logic.

`MoveResult { is_accepted: bool, reason: string }` — `"ok"` on success; `"game_over"`/`"motion_in_progress"` are application-level; rule-level invalid reasons are copied straight from `MoveValidation`.

## 10. Real-Time Movement Design

Isolated in `RealTimeArbiter` — not mixed into board/renderer/controller. It receives only already-validated commands and updates active motions as time advances. Active `Motion` objects live **outside** `Board` (Board = logical occupancy only); `RealTimeArbiter` owns that collection and exposes whether any motion is active (used by `GameEngine` to enforce one-active-motion).

**Fixed constants:** `CELL_SIZE = 100` px, `PIECE_SPEED = 100` px/s → moving N squares takes `N × 1000` ms (diagonal uses cell-step duration, not Euclidean distance — 3 diagonal squares = 3000 ms).

**Logical board update rule:** a moving piece stays logically on its source cell until arrival; occupancy changes only on arrival. This makes `print board` deterministic (shows old board before arrival, updated board at/after arrival) while still letting the renderer interpolate pixel position from snapshots.

**Arrival rule (atomic):** 1) remove from source, 2) capture enemy piece at destination if present, 3) place at destination, 4) if captured piece is a king, report king capture to `GameEngine`.

**Time in tests:** never real sleep — `engine.wait(ms)` (DSL: `wait 1000`) delegates to `RealTimeArbiter.advance_time(ms)`; `GameEngine.wait` must not directly touch Board motion state.

## 11. Controller Design

Translates clicks into commands; does **not** decide chess legality.

- Converts pixels → cells via `BoardMapper`. `col = x // 100`, `row = y // 100` (with `CELL_SIZE = 100`).
- Maintains selected-piece state. First click selects a piece (ignore first clicks on empty cells). Second click calls `GameEngine.request_move(source, destination)` and **always** clears selection after, whether legal or not.
- No selection + outside-board click → ignored. Selection active + outside-board click → cancels selection, sends **no** command.
- Must not call `Board.move_piece` directly, and must not call `RuleEngine` directly unless `GameEngine` intentionally exposes a validation-only query for UI feedback.
- No scrolling camera in the common route — pixel coords map directly to board coords. Viewport/camera support, if ever added, belongs in `BoardMapper`, not the model.

## 12. View / Renderer Design

Draws state; does not own rules; does not mutate the board. Wraps the supplied drawing/image library behind a small renderer interface.

Responsibilities: draw grid, draw pieces at pixel positions, highlight selection, draw moving pieces between cells, show game-over message.

Receives a **read-only** `GameSnapshot { board_width, board_height, pieces[kind/color/pixel position/state], selected cell, game_over flag }` — never live `Board`/`Piece` objects (avoids coupling/accidental mutation from the view layer).

## 13. Text-Based Integration Test Language

`BoardParser`/`BoardPrinter` are **shared text I/O adapters**, not test-only helpers — they live in `io/`, not inside `texttests/`, so the application and the tests share the same board setup/output behavior.

The DSL has exactly four commands, **no more**:

```
Board
<textual board rows>

click <x> <y>
wait <milliseconds>
print board
```

Board notation: one row per line, cells space-separated, `.` = empty, `w`/`b` prefix + chess letter (K/Q/R/B/N/P), width/height inferred from text, all rows same length.

`print board` is the **only** integration-test assertion mechanism — it prints logical occupancy, not animation/pixel position. After every `print board` the script contains the exact expected rows; the runner string-compares actual vs. expected.

Example:

```
Board
. wR .
. . .
. . bK

click 150 50
click 150 250
wait 2000
print board
. . .
. . .
. wR bK
```

## 14. Minimal Assertion Strategy

Exactly one assertion style (`print board` + expected rows) is used to cover: board parsing, pixel mapping, legal movement (before/after arrival), illegal movement (unchanged board), blocking (unchanged board), capture (piece disappears), king-capture/game-over (subsequent legal-looking move leaves board unchanged).

Selection state and animation pixel position are **never** asserted by the integration suite — those are unit/renderer-test concerns only.

## 15. How Text Tests Connect to Implementation

`ScriptRunner` never duplicates game logic and never bypasses the real path:

```
Board text -> BoardParser -> GameEngine initial state
click       -> Controller.click(x, y)
wait        -> GameEngine.wait(ms)
print board -> BoardPrinter.print(game_state)
```

**Forbidden shortcut:** `ScriptRunner` calling `Board.move_piece` directly — this bypasses Controller/GameEngine/RuleEngine/RealTimeArbiter and the test no longer proves the real user command path works.

## 16. Unit Test Layers

Both unit tests ("is this component correct in isolation?") and text integration tests ("does the feature work from the outside?") are required — neither replaces the other.

| Component | Primary test type |
|---|---|
| Position / Board | Pure unit tests |
| PieceRules | Pure unit tests for legal destinations |
| RuleEngine | Unit tests for validation results + stable rule-level reasons |
| GameEngine | Unit tests for game-over guard, validation delegation, mutation timing, wait delegation |
| RealTimeArbiter | Unit tests for elapsed time, active motions, arrival, capture events, atomic resolution |
| Controller | Unit tests with a fake GameEngine |
| Renderer | Snapshot-level tests only |
| TextTestRunner | Integration tests through public commands |
| BoardParser / BoardPrinter | Unit tests for rectangular parsing, token validation, stable logical output |

## 17. Iteration Plan (11 iterations, reference)

0. **Project skeleton, text I/O, test runner skeleton** — repo, test framework, shared `BoardParser`/`BoardPrinter` (in `io/`, not hidden in `texttests/`), trivial `print board` round-trip.
1. **Board and Pieces** — pure model; `Piece.state` stays a lifecycle flag only.
2. **Pixel mapping and selection** — `BoardMapper` + Controller selection state, no piece movement yet. Integration tests never assert selection directly.
3. **Rook movement without time** — first `PieceRules` implementation; proves capture *eligibility*, not capture execution.
4. **GameEngine command path without time** — click→click routes through Controller→GameEngine→RuleEngine with `MoveResult`; no `wait`/arrival yet.
5. **Real-time movement** — `wait(ms)`, active motions, arrival, one-motion-at-a-time (`"motion_in_progress"`). First full click-click-wait-print vertical slice.
6. **Captures and king-capture win condition** — arrival-time capture, `game_over` flag, rejection after game over.
7. **More pieces** — bishop, queen, knight, king, pawn; unit tests per piece + one integration test each.
8. **Invalid moves and error stability** — stable validation/application reasons; invalid commands never mutate state or start motions.
9. **Minimal playable UI and renderer** — thin renderer off `GameSnapshot`; no second input path, no new rules in the renderer.
10. **Refactoring, review, and one extra-route feature** — cleanup pass (dedupe piece rules, error messages, board printer, missing negative tests, split large classes) + exactly one extra feature, added only after common route + minimal UI are done, unit-tested first, with a short architecture-impact note (affected layers, new state, public API impact, tests required, layers that must stay unchanged).

## 18. Common Mistakes → Corrections (quick reference)

- Pixel coords in the model → belongs in `BoardMapper`/renderer/snapshots.
- Chess rules in the Controller → Controller only translates intent; `RuleEngine` decides legality.
- Real `sleep()` in tests → use `wait(ms)` / simulated time.
- Implementing all pieces before testing one well → start with rook, prove the architecture first.
- Testing logic manually through the UI → every visible behavior must be reproducible via a text test.
- `RuleEngine` mutating `Board` → RuleEngine validates only; GameEngine/RealTimeArbiter apply state changes.
- Live `Board`/`Piece` objects passed into Renderer → Renderer gets read-only `GameSnapshot` only.
- Active `Motion` objects stored inside `Board` → they belong to `RealTimeArbiter`.
- `BoardParser` hidden inside `texttests` → it's a shared `io/` adapter.
- A second common-route move starting while one is active → reject with `"motion_in_progress"`.
- Outside-board second click treated inconsistently → no selection = ignored; selection active = cancels, sends nothing.
- Testing arrival before real-time movement exists (iteration 4 vs 5 mixed up).

## 19. Minimal Public API Between Layers

```
BoardParser.parse(text) -> Board
BoardPrinter.print(game_state_or_snapshot) -> text
BoardMapper.pixel_to_cell(x, y) -> Position | None
Controller.click(x, y) -> ControllerResult
GameEngine.request_move(source, destination) -> MoveResult
GameEngine.wait(ms) -> None
GameEngine.snapshot() -> GameSnapshot
RuleEngine.validate_move(board, source, destination) -> MoveValidation
RealTimeArbiter.has_active_motion() -> bool
RealTimeArbiter.start_motion(piece, source, destination) -> None
RealTimeArbiter.advance_time(ms) -> ArrivalEvents
```

`GameEngine.request_move` checks `game_over` and `motion_in_progress` **before** delegating to `RuleEngine`; `RuleEngine` doesn't know about either condition.

## 20. Definition of Done

A feature is done only when:

1. Unit tests cover the internal logic.
2. At least one text integration test covers the user-visible behavior through `print board`.
3. The implementation introduces no UI dependency into the model.
4. Tests use no real time.
5. The diff is small enough that each changed class's responsibility is clear.
6. It's possible to state what was asked of the LLM, what was accepted, and what was rejected — backed by the plan written before prompting and the tests used to verify any AI-assisted change.
