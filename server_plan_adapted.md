# Kung-Fu-Chess — תכנית שרת מרובה-משתתפים, מותאמת לקוד בפועל

מסמך זה מתאים את [Multiplayer_Server_Architecture_Plan.md](Multiplayer_Server_Architecture_Plan.md) למבנה הקוד האמיתי של הפרויקט (package `game/`), אחרי אימות כל מחלקה/מתודה/נתיב מול הקוד. המסמך המקורי נכתב מול מבנה אחר (`kungfu_chess/`, `EventBus`, `PIECE_RULES`, `advance_time`) — כאן הכל בשמות האמיתיים. מחליף את `server_work_plan.md` הישן (הקל).

> **מוסכמות שכבות מחייבות:** ראו [kung_fu_chess_design_guide.md](kung_fu_chess_design_guide.md) ו-[CLAUDE.md](CLAUDE.md). השרת מוסיף עלים חדשים לעץ התלויות — לא גוזם ולא משנה את `model/`/`pieces/`/`rules/`/`realtime/`/`engine/`.

---

## חלק 1 — תקציר מנהלים

**מה בונים:** שרת WebSocket סמכותי (authoritative), חד-תהליכי, שיושב **מחוץ** ל-`game/model`, `game/pieces`, `game/rules`, `game/realtime`, `game/engine`, ותלוי ב-`GameEngine` דרך ה-API הציבורי הקיים שלו בלבד — בדיוק כפי ש-`Controller`/`GameWindow` עושים היום.

**ה-API שהשרת צריך כבר קיים במלואו:**
- `GameEngine.request_move(source: Position, destination: Position) -> MoveResult` (`.is_accepted`, `.reason`)
- `GameEngine.request_jump(position: Position) -> MoveResult`
- `GameEngine.wait(ms: int)` — קידום זמן מדומה (לא `advance_time` — זה שם המתודה ב-`RealTimeArbiter`)
- `GameEngine.snapshot() -> GameSnapshot` — מצב לוח לשידור
- `GameEngine.is_game_over() -> bool`
- `GameEngine.legal_destinations(source) -> set[Position]`
- `GameEngine.add_observer(observer)` — רישום לאירועים

**שינוי מנוע נדרש: אחד קטן ומאושר.** `GameOverObserver.on_game_over()` **כבר קיים** ומופעל מ-`wait()` בלכידת מלך — אבל היום הוא לא נושא מידע על מי ניצח. **החלטה (2026-07-21):** `on_game_over` יקבל את זהות המלך שנאכל (צבעו), כדי שהאפליקציה תדע מי המנצח לצורך עדכון ה-ELO. זהו שינוי חתימה קטן ל-`GameOverObserver` Protocol + `_notify_game_over` (המנוע כבר מחזיק את המלך שנאכל ב-`_ends_the_game(captured_piece)`, אז אין לוגיקה חדשה — רק העברת ערך). מעדכן גם את `GameOverData` הקיים ואת הבדיקות שלו.

**מנצח (winner):** צבע המלך שנאכל = המפסיד; המנצח = הצבע הנגדי. אין תיקו במשחק (החלטה 2026-07-21), אז ELO מחושב ניצחון/הפסד בלבד, לפי הנוסחה המקובלת (expected score + K-factor) ב-`RatingService`.

**ארכיטקטורה מומלצת:** שכבות — `server/` (WebSocket gateway, connection manager, JSON schemas) → `application/` (שירותים חדשים: `GameService`, `RoomService`, `MatchmakingService`, `AuthService`, `RatingService`, `ConnectionService`) → `engine`/`rules`/`realtime`/`pieces`/`model` (ללא שינוי) — בתוספת `persistence/` (repository interfaces + in-memory ו-SQLite) ו-`messaging/` (bus יישומי חדש, לצד מנגנון ה-Observer הקיים, לא במקומו).

**סיכונים מרכזיים:** (1) פיתוי לתת ל-gateway לקרוא ל-`Board`/`RuleEngine` ישירות במקום דרך `GameEngine.request_move` (שכפול לוגיקת כללים); (2) שתי פקודות מקבילות שמשנות אותו משחק בלי סריאליזציה per-game; (3) עדכון ELO כפול לאותו משחק; (4) המנוע בזמן-אמת (`Motion`, cooldown, airborne) חייב שהזמן יתקדם גם כשאין הודעה מהלקוח — עיצוב "לקדם זמן רק על פקודה נכנסת" יתקע תנועות באוויר; (5) שכחה ש-`on_game_over` כבר קיים ובניית consumers שמסקרים `is_game_over()` בפולינג במקום להירשם כ-observer.

**סדר מימוש:** Phase A (שרת WS חד-תהליכי, שני לקוחות מקומיים, זיהוי username-only מה-shell, `GameSession` בזיכרון, בלי סיסמאות/persistence) → Phase B (SQLite + hashing + ELO) → Phase C (matchmaking) → Phase D (disconnect/reconnect/sync) → Phase E (rooms/spectators/logging דו-צדדי).

**מה אסור לשנות במנוע הקיים:** `Piece`, `Board`, `Position`, `PieceRules` וכל `pieces/*.py`, `PIECE_TYPES`, `RuleEngine`, `Motion`/`Jump`/`Rest`/`RealTimeArbiter`, וה-API הציבורי + ה-Observer Protocols של `GameEngine`. אף אחד מהם לא מקבל מודעות ל-sockets/JSON/users/סיסמאות/SQLite/חדרים.

---

## חלק 2 — הערכת מאגר הקוד (מאומת מול הקבצים)

### מחלקות לשימוש חוזר as-is (תלות של השרת, ללא שינוי)

| מחלקה / מודול | קובץ | למה |
|---|---|---|
| `Piece` | `model/piece.py` | value object, ללא I/O. `id`/`color`/`kind`/`cell`/`state`. |
| `Board` | `model/board.py` | `Board(width, height)`; גישה דרך `piece_at`/`is_empty`/`in_bounds`/`pieces()`/`move_piece` — לא נוגעים ב-`_pieces_by_cell`. |
| `Position` | `model/position.py` | value object hashable `(row, col)`. |
| `PieceRules` + `PIECE_TYPES` | `pieces/*.py`, `pieces/__init__.py` | אסטרטגיות טהורות; `PIECE_TYPES: dict[str, PieceRules]` (letter→strategy). |
| `RuleEngine` | `rules/rule_engine.py` | `validate_move(board, source, destination) -> MoveValidation(is_valid, reason)` + `legal_destinations(board, source)`. DI-friendly (`piece_rules_by_kind=PIECE_TYPES`). |
| `RealTimeArbiter` + `Motion`/`Jump`/`Rest` | `realtime/*.py` | מונע דטרמיניסטי, מונע ע"י `advance_time(ms)` בלבד — מושלם לשעון וירטואלי בשליטת שרת. חושף `has_active_motion`/`is_moving`/`is_resting`/`is_airborne`. |
| `GameEngine` | `engine/game_engine.py` | **ה-API האמיתי של השרת.** ראו חלק 1. Observer Protocols פנימיים: `ArrivalObserver`/`MotionStartedObserver`/`JumpStartedObserver`/`RestStartedObserver`/`GameOverObserver`. |
| `GameSnapshot`/`PiecePlacement` | `engine/game_snapshot.py` | view-model לקריאה בלבד — `board_width`/`board_height` + רשימת `(id, kind, color, cell)`. בסיס ל-payload של `game_state`. |
| `BoardParser`/`BoardPrinter` | `text_io/*.py` | `BoardParser.parse(text) -> Board` לבניית לוח פתיחה; `BoardPrinter.to_text(board)` לשידור טקסטואלי. |

### הממצא של המסמך המקורי על "GameOverEvent חסר" — לא רלוונטי אצלך
המסמך המקורי טען שאין אירוע לסיום משחק ולכן צריך להוסיף `GameOverEvent`. **אצלך זה כבר קיים:** `GameEngine.wait()` → `_ends_the_game(captured_piece)` (בדיקת `King.letter`) → `mark_game_over()` → `_notify_game_over()` → `GameOverObserver.on_game_over()`. השרת רק מיישם את ה-hook. **אין gap, אין שינוי מנוע.**

### מחלקות שלא לשימוש חוזר בשרת
| מחלקה | קובץ | סיבה |
|---|---|---|
| `Controller` | `input/controller.py` | `click(x, y)` פיקסלי, מכונת-מצבים של בחירה בשתי הקלקות למסך מקומי אחד. השרת מקבל מהלך מלא `(source, destination)` → קורא ל-`GameEngine` ישירות. |
| `BoardMapper`, `MouseCommandExtractor`, `commands.py` | `input/*` | פיקסל→תא / Command pattern של ה-GUI. לא רלוונטי כשהלקוח שולח `(row, col)` מובנה. |
| `view/*`, `game_window.py` | `view/`, `game/` | שכבת תצוגה `cv2`; לא רלוונטי צד-שרת. |

### תלויות קיימות (ולמה הן לא חוסמות)
כלום ב-`model/`/`pieces/`/`rules/`/`realtime/`/`engine/` לא מייבא מ-`text_io/`/`input/`/`view/`. השרת מוסיף עלים חדשים בלבד.

---

## חלק 3 — ארכיטקטורה מוצעת

חבילות חדשות תחת `game/` (כדי לשמור על סגנון ה-imports השטוח הקיים, למשל `from application.game_service import GameService`):

```text
game/
├── model/        # ללא שינוי — Piece, Board, Position
├── pieces/       # ללא שינוי — PieceRules + PIECE_TYPES (שכבת אסטרטגיית הכללים)
├── rules/        # ללא שינוי — RuleEngine
├── realtime/     # ללא שינוי — RealTimeArbiter, Motion, Jump, Rest
├── engine/       # ללא שינוי — GameEngine + Observer Protocols, GameSnapshot
├── text_io/      # BoardParser, BoardPrinter (ללא שינוי) + move_notation.py (חדש)
│                 #   MoveNotation.parse("WQe2e5") -> (source: Position, destination: Position)
├── input/        # ללא שינוי — נשאר GUI/CLI בלבד, לא מיובא ע"י server/
├── view/         # ללא שינוי — שכבת תצוגה
│
├── application/                  # חדש — תזמור צד-שרת, בלי ספריות I/O
│   ├── game_session.py           # GameSession: Board+GameEngine+observer+lock למשחק אחד
│   ├── game_service.py           # GameService: move/jump -> GameEngine; observer של on_arrival/on_game_over; מפרסם GameStartedEvent
│   ├── room_service.py           # RoomService: create/join; creator=White, 2nd=Black, rest=spectators
│   ├── matchmaking_service.py    # MatchmakingService: תור, חיפוש ±100 ELO, timeout
│   ├── auth_service.py           # AuthService: identify(username) (A) ואז register/login (B)
│   ├── rating_service.py         # RatingService: ELO, מוחל בדיוק פעם אחת למשחק
│   ├── connection_service.py     # ConnectionService: grace period, טריגר auto-resign
│   └── dto.py                    # dataclasses קטנים: GameStateDTO וכו'
│
├── server/                       # חדש — הפאקג' היחיד שמייבא ספריית WebSocket אסינכרונית
│   ├── websocket_gateway.py      # מקבל חיבורים, קורא/כותב frames, אפס לוגיקת כללים
│   ├── connection_manager.py     # connection_id <-> user_id <-> game_id/room_id
│   ├── schemas.py                # מעטפת JSON: (de)serialization + validation
│   ├── logging_config.py         # לוגים מובנים, שרת + מוסכמה ללקוח
│   └── server_main.py            # composition root: מחבר הכל, מריץ event loop
│
├── persistence/                  # חדש — בלי רשת, בלי כללי משחק
│   ├── repositories.py           # ממשקים אבסטרקטיים (Protocol/ABC)
│   ├── in_memory/                # מימושי Phase A
│   └── sqlite/                   # מימושי Phase B+ (schema.sql, sqlite_repositories.py)
│
└── messaging/                    # חדש — pub/sub יישומי, לצד מנגנון ה-Observer של engine
    ├── application_message_bus.py
    └── application_events.py     # GameStartedEvent, PlayerJoinedRoomEvent, MatchFoundEvent, ...
```

---

## חלק 3ב — ארכיטקטורת הלקוח (Decoupled Adapter)

ה-GUI/CLI הקיימים **לא נזרקים ולא הופכים ל-offline-בלבד** — במקום זה מפרידים את ה-UI מניהול המצב, ומזריקים את מקור הנתונים ויעד הפקודות דרך Adapter. כל שכבת ה-`view/` נשמרת ומשומשת מחדש כמות שהיא.

**נקודות הממשק היחידות בין UI ללוגיקה (כבר קיימות כתפרים):**
- **קבלת מצב לתצוגה:** `GameSnapshot` (מ-`engine/game_snapshot.py`).
- **שליחת פקודות:** `CommandSender` Protocol (מ-`input/commands.py` — ה-comment שם כבר צופה `NetworkCommandSender`).

**שני Adapters (Dependency Injection):**
- **`LocalGameAdapter`** (offline / tests) — מחבר את ה-UI ישירות ל-`GameEngine` מקומי (בדיוק כמו `app.py` היום). מריץ GUI ו-CLI אופליין מלא, בלי שרת — מצוין לבדיקות מהירות ולפיתוח.
- **`NetworkGameAdapter`** (online) — מחבר את ה-UI לשרת: פקודות דרך `NetworkCommandSender` (סריאליזציה ל-JSON ושליחה), ו-`GameSnapshot` נבנה מ-`state_snapshot` שמגיע מהשרת במקום מ-`game_engine.snapshot()` מקומי.

**שתי נקודות כניסה:**
- `app.py` הקיים (או `app_local.py`) → טוען `LocalGameAdapter` (offline/test).
- `app_online.py` חדש → טוען `NetworkGameAdapter` (online).

כך לא מאבדים הרצה מקומית ובדיקות, ומרוויחים מקסימום שימוש חוזר בקוד הציור. ה-`GameWindow` צריך refactor קטן: מקור ה-snapshot ויעד הפקודות עוברים דרך ה-Adapter המוזרק, במקום `GameEngine` ישיר.

---

## חלק 4 — כללי תלות

- `server/` → `application/`, `server/schemas.py`, `messaging/`. **אף פעם** לא ישירות ל-`model/`/`pieces/`/`rules/`/`realtime/`.
- `application/` → `engine/`, `rules/`, `realtime/`, `pieces/`, `model/` (תזמור/קריאה), `persistence/repositories.py` (ממשקים בלבד), `messaging/`.
- `persistence/sqlite/` → `sqlite3` בלבד. מיובא רק מתוך `persistence/` ו-`server_main.py`.
- `engine/`/`rules/`/`realtime/`/`pieces/`/`model/` → זה את זה בלבד, כמו היום. **אף פעם** לא ל-`application/`/`server/`/`persistence/`/`messaging/`.

**imports אסורים (לאכוף ב-test על גרף ה-imports):**
- `game/engine/game_engine.py` לא מייבא `websockets`/`sqlite3`/`bcrypt`/`asyncio`.
- `server/websocket_gateway.py` לא מייבא `model.board.Board`/`rules.rule_engine.RuleEngine` — רק `application/game_service.py`.

---

## חלק 5 — מודל אירועים (מותאם: Observer קיים, לא EventBus)

שלוש משפחות אובייקטים נפרדות:

| שכבה | דוגמה | חי ב | מה נושא |
|---|---|---|---|
| **אירוע דומיין (Observer קיים)** | `on_arrival(event)`, `on_game_over(loser_color)`, `on_motion_started`, `on_jump_started`, `on_rest_started` | `engine/game_engine.py` (Protocols) + `realtime` (`ArrivalEvent`) | `ArrivalEvent`: `piece, source, destination, captured_piece`. `on_game_over(loser_color)`: צבע המלך שנאכל (שינוי חתימה מאושר; המנצח = הצבע הנגדי). ערכי דומיין טהורים, בלי game_id/JSON. |
| **אירוע יישומי** | `GameStartedEvent`, `GameMoveAppliedEvent`, `GameEndedEvent`, `PlayerJoinedRoomEvent`, `MatchFoundEvent`, `PlayerDisconnectedEvent`, `RatingUpdatedEvent` | `messaging/application_events.py` | envelope + `game_id`/`room_id`/`user_id`. |
| **הודעת רשת** | `{"type": "game_state", ...}` JSON | `server/schemas.py` | JSON בלבד, בלי אובייקטי Python. |

**איך זה מתחבר:**
1. `GameEngine.wait()` כבר מפרסם ל-observers: `on_arrival` לכל הגעה, `on_game_over` בלכידת מלך.
2. `GameService` נרשם כ-observer (`engine.add_observer(game_service)`) ומיישם `on_arrival` + `on_game_over`. הוא מתרגם כל אירוע דומיין לאירוע יישומי על `ApplicationMessageBus` — `GameMoveAppliedEvent` מהגעה, `GameEndedEvent` מ-`on_game_over` (עם המנצח שנגזר), ו-`GameStartedEvent` שהוא מפרסם בעצמו ביצירת ה-session.
3. `websocket_gateway` (או `Broadcaster` ייעודי) נרשם ל-`ApplicationMessageBus` ומייצר הודעות רשת ל-connections הרלוונטיים דרך `connection_manager`.

**מיפוי דרישת ה-BUS מהמצגת:** עדכון ניקוד/יומן = `on_arrival` (כבר עובד ב-`ScoreData`/`MovesLogData`); צליל/אנימציית סיום = `on_game_over` (כבר קיים); אנימציית פתיחה = `GameStartedEvent` יישומי.

---

## חלק 6 — פרוטוקול WebSocket

מעטפת JSON אחידה לכל הודעה (שני הכיוונים):
```json
{ "type": "...", "message_id": "uuid", "correlation_id": "uuid", "timestamp": 0, "game_id": "g_...", "payload": {} }
```

**לקוח → שרת:** `connect {username}` (A), `login {username, password}` (B), `join_game {mode|room_id}`, `make_move {move: "WQe2e5"}`, `jump_request {cell: "e2"}`, `play {rated}`, `cancel_matchmaking {}`, `create_room {}` / `join_room {room_id}`, `ping {}`.

**שרת → לקוח:** `state_snapshot {board, game_over, sequence}` (board = מ-`GameSnapshot` או `BoardPrinter.to_text`), `move_accepted {sequence}`, `move_rejected {reason}` (reason = `MoveResult.reason`), `game_event {kind, from, to, captured}`, `game_started {white, black, rated}`, `game_over {winner, reason}`, `player_disconnected {color, grace_period_ms}` (פעם אחת; הלקוח סופר לאחור מקומית), `matchmaking_success`/`matchmaking_timeout`, `room_update {room_id, white, black, spectators}`, `error {code, message}`, `pong {}`.

**מיפוי מהלך → מנוע:** מחרוזת `"WQe2e5"` (צבע+כלי+משבצת-מקור אלגברית+משבצת-יעד) → `MoveNotation.parse` → `(source, destination)` → `engine.request_move(source, destination)`. התשובה `MoveResult(is_accepted, reason)` → `move_accepted`/`move_rejected`. **שים לב למיפוי אלגברי→row/col:** קובץ `a..h` → `col 0..7`; דרגה `1..8` → `row 7..0` (אצלך שורה 0 היא למעלה, שם עומדים השחורים בפתיחה). הצבע+הכלי במחרוזת משמשים לוולידציה מול הכלי שבמקור (או מתעלמים מהם ומסתמכים על source→dest). כל זה נבדק ב-`text_io/move_notation.py` בבידוד.

**Sequencing/duplicates/reconnect:** sequence מונוטוני per-game בכל `state_snapshot`; `message_id` כפול בחלון קצר → משחזר תשובה מ-cache; reconnect = `state_snapshot` מלא אחד (לא replay).

---

## חלק 7 — SQLite (Phase B+)
`users(user_id, username UNIQUE, password_hash, current_rating DEFAULT 1200, created_at)`; `rooms`; `room_members(role IN player|spectator)`; `games(result, end_reason)`; `game_players(color IN w|b)`; `rating_changes(... UNIQUE(game_id, user_id))` — מונע עדכון ELO כפול. `password_hash` = bcrypt/argon2 (כולל salt עצמי, בלי עמודת salt). פירוט זהה למסמך המקורי (חלק 7 שם).

---

## חלק 8 — שירותים (עיקרי המותאם)

- **`GameService`** — היחיד שקורא ל-`GameEngine.request_move`/`request_jump`/`wait`. נרשם כ-observer של כל `GameSession` (מקבל `on_arrival` + `on_game_over(loser_color)`); המנצח = הצבע הנגדי ל-loser_color; מפרסם `GameStartedEvent` ביצירת session ו-`GameEndedEvent`(winner) בסיום. מתודות: `create_session(white, black, rated)`, `handle_move_request(...)`, `handle_jump_request(...)`, `tick(game_id, elapsed_ms)` (קורא `engine.wait`). כל מתודה שנוגעת ב-session תופסת קודם את ה-lock שלו.
- **`RoomService`** — creator=White, 2nd joiner=Black (משחק מתחיל), rest=spectators; חוסם `move_request` מ-spectator בצד השרת. lock per-room להחלטת admission.
- **`MatchmakingService`** — תור ±100 ELO, timeout מוגדר, `MatchFoundEvent`/`MatchmakingTimeoutEvent`.
- **`AuthService`** — `identify(username)` (A, בלי סיסמה/DB) → `register`/`login` (B, SQLite). כישלונות: `USERNAME_TAKEN`, `INVALID_CREDENTIALS`.
- **`RatingService`** — `apply_result(...)`, idempotent מול `rating_changes`.
- **`ConnectionService`** — grace period 20–30ש', טריגר auto-resign; הודעת `player_disconnected` אחת; ביטול טיימר על reconnect תחת אותו per-game lock.

---

## חלק 9 — בעלות על מצב (State Ownership)
`Board`/`GameEngine`/`observer registration`/per-game `lock`/player assignments/spectators/sequence — כולם ב-`GameSession`. sockets האמיתיים ב-`connection_manager` בלבד. תוצאה נשמרת פעם אחת ל-`GameRepository`. סטטוס ELO — מקור אמת בטבלת `rating_changes`. `GameSession` **לא** נשמר כ-blob — שומרים לוח פתיחה (DSL של `BoardParser`) + רשימת מהלכים, או מצב סופי + תוצאה.

**מה ב-`GameSession` מול `GameEngine`:** `GameEngine` נשאר בדיוק כמו היום. `GameSession` מוסיף את מה שאסור במנוע: זהויות רשת, lock, reconnect deadlines, rated flag, room/game IDs, ומושג lifecycle שלישי שהמנוע לא מכיר — "abandoned by disconnect" (הפסד טכני), ברמת ה-session בלבד.

---

## חלק 10 — זמן ומקביליות (Phase A)

**מקביליות:** event loop יחיד (`asyncio`), **`asyncio.Lock` אחד per-`GameSession`** + `asyncio.Queue` + worker coroutine אחד per active game. לא global lock (משחקים לא-קשורים לא יסתדרו בטור לחינם).

**זמן — היברידי, לא lazy בלבד:** הגעות `Motion`, סיום cooldown, ו-airborne-kill חייבים להשתדר ברגע שהם קורים בזמן הווירטואלי, לא רק כשמגיעה פקודה. לכן: קידום lazy על כל פקודה נכנסת (`engine.wait(elapsed)`), **בתוספת** tick תקופתי קל (50–100ms) שקורא `engine.wait` רק ל-sessions שיש בהם תנועה פעילה — תנאי ה-tick = `real_time_arbiter.has_active_motion()` (חשוף היום; פשוט יותר מבדיקת שלוש-המתודות שבמסמך המקורי), ונעצר ברגע שאין תנועה.

**בדיקתיות (חובה, לפי CLAUDE.md §7):** השעון שמזין את `wait(ms)` **מוזרק** — בבדיקות מזריקים שעון מדומה ומריצים ticks ידנית, בלי `time.sleep` אמיתי. כל השירותים (`GameService`/`RoomService`/`MatchmakingService`/`ConnectionService`) נבדקים סינכרונית עם שעון ו-transport מוזרקים; ה-WebSocket הוא adapter דק בלבד.

---

## חלק 11 — מפת דרכים (Phases)

- **Phase A** — שרת WS חד-תהליכי, שני לקוחות מקומיים, prompt ל-username בלבד מה-shell, מחבר-ראשון=White/שני=Black, פרוטוקול JSON, מהלכים סמכותיים, שידור מצב. מודולים חדשים: `application/{game_session,game_service,auth_service}`, `server/{websocket_gateway,connection_manager,schemas,server_main}`, `messaging/*`. **בלי שינוי מנוע** (`on_game_over` כבר קיים). דחוי: auth אמיתי, persistence, matchmaking, rooms, reconnect.
- **Phase B** — register/login מה-shell (username+password), SQLite, ELO=1200. `persistence/*`, `rating_service`. בדיקות: Auth מול in-memory repo לפני SQLite; ELO כפונקציה טהורה.
- **Phase C** — matchmaking ±100 ELO, timeout, ביטול/הוגנות/מרוצים.
- **Phase D** — disconnect → grace 20–30ש' → auto-resign; reconnect משחזר מצב מלא. הלקוח סופר לאחור מ-`player_disconnected` יחיד.
- **Phase E** — rooms (create מחזיר Room ID), join (2nd=Black, rest=spectators), logging דו-צדדי מובנה עם correlation IDs.

---

## חלק 12 — אסטרטגיית בדיקות
- **Domain (קיים):** `tests/unit`/`tests/integration` ממשיכים כמו היום. אין צורך בבדיקת `GameOverEvent` חדשה — `on_game_over` כבר מכוסה.
- **שירותים:** `GameService` (כולל רישום observer + גזירת מנצח), `RatingService` כפונקציה טהורה, `MatchmakingService`, כלל ה-White/Black/spectator של `RoomService`.
- **Repository:** contract tests משותפים ל-in-memory ול-SQLite.
- **WebSocket integration:** רצף מלא `connect(username) → join_game → move_request → move_accepted/state_snapshot`; `game_over` נצפה ע"י שני הלקוחות.
- **מקביליות:** שתי `move_request` בו-זמניות לאותו משחק מעובדות בסדר.
- **imports:** בדיקה ש-`server/websocket_gateway.py` לא מייבא מ-`model`/`rules`.

---

## חלק 13 — החלטות

### נסגרו (2026-07-21)
1. **נוטציית מהלך: מחרוזת `"WQe2e5"`** (כמו [server_desine.md](server_desine.md)). נדרש `text_io/move_notation.py` שממיר מחרוזת→`(source, destination)`, כולל מיפוי אלגברי→row/col (ראו חלק 6). גובר על החלופה המובנית של המסמך המקורי.
2. **מיקום החבילות: תחת `game/`** (`game/server/`, `game/application/`, ...), שומר על סגנון ה-imports השטוח.
3. **async: `websockets`+`asyncio` עם adapter דק.** כל הלוגיקה נבדקת סינכרונית עם שעון מוזרק, בלי `time.sleep`.

4. **מנצח:** `on_game_over(loser_color)` — שינוי חתימה קטן ומאושר במנוע (ראו חלק 1/5). ELO ניצחון/הפסד בלבד.
5. **אין תיקו** במשחק. ELO לא מטפל בתיקו.
6. **ארכיטקטורת הלקוח: Decoupled Adapter** (ראו חלק 3ב).

### עדיין פתוחות
7. **שאלות נוספות** (חלק 16 במסמך המקורי): טווח ה-±100 מתרחב עם הזמן? אובדן משחקים ב-restart מקובל עד Phase D?
