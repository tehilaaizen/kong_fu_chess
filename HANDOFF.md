# Kong-Fu-Chess — סיכום מצב והמשך עבודה
*(נכון ל-2026-07-22, ענף `server`, 602 טסטים עוברים; ELO+HUD+Matchmaking+לובי גרפי כבר committed (3 קומיטים); reconnect/grace + שם-מנצח חדשים וטרם commit)*

## 1. מה זה הפרויקט
שחמט בזמן אמת (ללא תורות — כל כלי זז/מתקרר עצמאית), Python 3.12, ארכיטקטורה שכבתית מחייבת. מסמכי אמת:
- `kung_fu_chess_design_guide.md` — הארכיטקטורה המחייבת (שכבות, package structure, DSL לבדיקות).
- `kong_fu_chess_requirements.md` — דרישות מוצר.
- `kong_fu_chess_ui_slides_requirements.md` — דרישות UI (Sprites, אנימציה, קלט עכבר, **מסכי lobby/login** — ראו §4.D).
- `CLAUDE.md` — הנחיות עבודה (type hints+docstrings לכל קוד חדש, בלי monkey-patching, בלי sleep אמיתי בטסטים, שאיפה ל-100% coverage, שינויים נקודתיים, לעצור ולוודא בקונפליקטי-scope).

## 2. שכבות (ה-seams החשובים)
`model/` → `pieces/` (PieceRules + PIECE_TYPES) → `rules/` (RuleEngine) → `realtime/` (RealTimeArbiter/Motion/Jump/Rest) → `engine/` (GameEngine + GameSnapshot + **ObserverHub** narrow-protocols; אין EventBus, ה"דומיין-באס" הוא ה-observers) → `text_io/` → `input/` (Controller/BoardMapper/commands) → `view/` (ציור בלבד) → `application/` (GameSession/GameService/AuthService/PasswordHasher) → `messaging/` (ApplicationMessageBus + events) → `server/` (dispatcher/broadcaster/game_server/room_registry/event_log) → `persistence/` (repositories + in_memory + sqlite) → `client/` (GameClient + Local/NetworkGameAdapter + WebSocketConnection).

**Decoupled Adapter:** ה-`GameWindow` תלוי רק ב-`GameClient`; `LocalGameAdapter` (אופליין) מול `NetworkGameAdapter` (אונליין). נקודות כניסה: `app.py` (לוקאלי), `app_online.py` (אונליין).

## 3. מה כבר מומש (DONE)
- **ליבת המשחק:** תנועה בזמן אמת, cooldown (rest), קפיצה+דודג', הכתרה, 6 סוגי כלים, ניקוד (ScoreData), יומן מהלכים (MovesLog), אנימציות (Sprites/PieceAnimator), resize לחלון + רקע.
- **שרת (Phase A):** WebSocket server (asyncio), MessageDispatcher, Broadcaster, GameSession/GameService בזיכרון.
- **ניתוק לקוח מהמנוע (6a/6b):** `GameClient`, `LocalGameAdapter`, `NetworkGameAdapter` עם **נאמנות אנימציה מלאה** (השרת משדר motion/jump/rest/arrival עם `piece_id` יציב; state_snapshot נושא ids); גשר asyncio ב-thread רקע.
- **חדרים בעלי שם + צופים:** ראשון=לבן/שני=שחור/שאר=צופים (`RoomRegistry`); מהלך של צופה נדחה.
- **עמידות לניתוק:** יריב שעוזב → `game_over(abandoned)`; לקוח מזהה חיבור סגור (`is_closed`) — הודעה במקום תקיעה; באנר "CONNECTION LOST" בחלון בקריסת שרת תוך-משחק.
- **לוגים:** loguru — שורה לכל מהלך/משחק ל-console + `logs/server.log` (`EventLog` על ה-bus).
- **חשבונות + SQLite:** `register`/`login` עם סיסמאות (scrypt מ-stdlib), `AuthService`, `UserRepository` (in-memory + SQLite עם contract tests משותפים); `auth_ok{username,rating}`/`auth_failed{reason}`. הזיהוי דרך CLI: `app_online.py <username> <password> <room>` (login-first, נרשם אוטומטית אם חדש).

## 4. מה נשאר לממש (מפורט, לפי עדיפות)

### A. עדכון דירוג ELO — ✅ DONE (2026-07-22)
- מומש: `application/elo.py` (פונקציה טהורה, `updated_ratings(winner, loser, k=32)`, K=32/התחלה 1200/win-loss בלבד) + `application/rating_service.py` (`RatingService.apply_result(winner_user, loser_user, game_id)` + `handle(GameEndedEvent)` כ-bus subscriber, כמו Broadcaster/EventLog).
- persistence: טבלת `rating_changes` עם `PRIMARY KEY(game_id, username)` ל-**idempotency** + `UserRepository.record_game_result(game_id, updates)` (אטומי, מחזיר False אם המשחק כבר נרשם) בשני ה-backings, מכוסה ב-contract test המשותף.
- חיווט: `GameEndedEvent` הועשר ב-`white_user`/`black_user`/`reason`. **abandonment עכשיו זורם דרך ה-bus** — `GameSession.abandon(winner_color)` מפרסם `GameEndedEvent(reason="abandoned")`, ה-Broadcaster משדר את ה-`game_over` (עם reason), וה-dispatcher כבר לא משדר ישירות. **הכרעה שאושרה: עזיבה נספרת ל-ELO** (זהה לאכילת מלך).
- `RatingService` מחווט ב-`build_server` בשיתוף אותו `UserRepository` של `AuthService`, אז הדירוג המעודכן הוא מה שההתחברות הבאה קוראת ב-`auth_ok`.
- נבדק: יוניט טהור ל-elo, contract idempotency לשני ה-backings, יוניט ל-RatingService, אינטגרציה (משחק שלם דרך ה-bus מעדכן דירוג), ו-smoke על ה-SQLite האמיתי. **517 טסטים, 100% כיסוי על הקבצים שנגעו.**

### B. Matchmaking (±100 ELO) — ✅ DONE (2026-07-22)
- מומש: `server/matchmaking.py` `MatchmakingService` — תור FIFO, זיווג לשחקן הקרוב-ביותר בטווח **±100 ELO**, timeout 60ש', **clock מוזרק** (בלי sleep בבדיקות). הראשון בתור=לבן, המגיע=שחור.
- **דו-קיום עם חדרים (הכרעה שאושרה: שימוש חוזר):** ה-`_start_game` פורק ל-`_seat_and_start(white_id, black_id)` המשותף; matchmaking רק **מחליט מי-מול-מי** ואז מפעיל את אותה מכונת-הושבה (create_session → game_started → snapshot). שני מסלולי-כניסה (חדר ידני / matchmaking) לאותו קוד.
- פרוטוקול: `find_match`/`cancel_match` (לקוח→שרת), `match_timeout` (שרת→לקוח). זיווג משדר את אותם `game_started`+`state_snapshot` כמו חדר — הלקוח לא צריך הודעת "match_found" נפרדת.
- חיווט: הודלרים ב-dispatcher; `expire_matchmaking()` נקרא במנוע ה-tick של `GameServer`; ניתוק מנקה גם מהתור. `MatchmakingService` נוצר כברירת-מחדל בתוך ה-dispatcher (שעון monotonic).
- לקוח CLI: `app_online.py <user> <pass> --matchmake` (במקום שם-חדר). על timeout — הודעה "no opponent found". ±100 קבוע ל-MVP (התרחבות עם הזמן — נשאר פתוח).
- נבדק: יוניט ל-MatchmakingService (זיווג/טווח/הקרוב-ביותר/ביטול/timeout/re-request) ול-dispatcher (pairing/waiting/cancel/expire/disconnect), ו-**smoke WS אמיתי** (שני לקוחות find_match → משחק אחד + מהלך עובר). **537 טסטים, 100% כיסוי על הקבצים החדשים.**

### C. Reconnect מלא / שחזור מצב — ✅ DONE (2026-07-22)
- **עזיבה = ניתוק (סגירת חלון/Esc); חזרה = login מחדש עם אותו שם** (ההכרעה שאושרה). grace 30ש', המשחק **נעול** (paused) בזמן הזה.
- שרת: `server/grace_registry.py` (username→game/color, deadline, clock מוזרק); `GameService.pause/resume/is_paused` (tick מדלג על משחק paused, מהלכים נדחים `paused`); dispatcher — ניתוק שחקן→grace+pause+`player_disconnected{color,name,seconds}` ליריב (במקום הפסד מיידי); login→`_restore_if_reconnecting` (מושיב מחדש, resume, שולח game_started+snapshot למחובר-מחדש + `player_reconnected` ליריב); `expire_grace()` (ב-tick)→היריב מנצח ב-abandonment (דרך ה-bus, כולל ELO). שני שחקנים שעוזבים→`GameSession.terminate()` (בלי מנצח/ELO).
- לקוח: `client/reconnect_data.py` (ספירה-לאחור מקומית) + `view/reconnect/reconnect_renderer.py` (overlay "left - waiting to reconnect" + מספר גדול); `NetworkGameAdapter` מנתב player_disconnected/reconnected ומ-tick את הספירה; `GameWindow` מצייר את ה-overlay **ונועל קלט** בזמן ההמתנה; `lobby_flow.await_restore` (אחרי login, אם השרת משחזר → ישר למשחק, בלי תפריט).
- נבדק: יוניט מלא (grace_registry, pause, dispatcher grace/restore/expire/both-leave, reconnect_data, renderer, adapter routing, window lock, await_restore), ו-**smoke WS אמיתי** (`scratchpad/smoke_reconnect.py`: bob עוזב→alice רואה countdown→bob מתחבר מחדש→שוחזר + alice רואה player_reconnected). **602 טסטים.**

### C'. שם המנצח בסוף משחק — ✅ DONE (2026-07-22)
- `GameOverData` מקבל `name_by_color` (אותן תוויות HUD) ומחשב את צבע המנצח; `GameOverRenderer` מצייר שורת "&lt;name&gt; wins!" מתחת ל-GAME OVER. עובד אונליין (שם+דירוג) ואופליין (White/Black). מאומת ויזואלית ל-PNG.

### D. מסך lobby/login גרפי — ✅ DONE (2026-07-22)
- מומש חבילת `view/lobby/`: `widgets.py` (Button/TextField/Label — hit-test + עריכת טקסט טהורים, ציור דק דרך `Img`), `screen.py` (`Screen` protocol + `run_screen` — לולאת cv2 עם עכבר+מקלדת, smoke), `login_screen.py` (username+password ממוסך, `authenticate` מוזרק), `home_screen.py` (Matchmaking/Create/Join + שדה שם-חדר + Back), `waiting_screen.py` (מאזין ל-game_started/state_snapshot/match_timeout), `lobby_flow.py` (login→בית→המתנה→משחק). `Img.blank` נוסף לקנבס ריק.
- **login גרפי מלא** (ההכרעה שאושרה) + **Create/Join שניהם `join_room`** (בלי שינוי שרת — "הראשון ששם חדר יוצר").
- כניסה: `app_online.py` בלי ארגומנטים → לובי גרפי; עם ארגומנטים → CLI כמו קודם. `main`/`main_gui` חולקים `_play` + `_login_or_register`.
- נבדק: יוניט 100% על כל לוגיקת המסכים/widgets (hit-test, עריכה, פוקוס, מיסוך, consume-messages), ו-**רינדור אומת ויזואלית ל-PNG** (תואם למוקאפ). `screen.py`/`lobby_flow.py` = GUI-loop/orchestration, smoke בלבד (כמו GameWindow/app_online). **568 טסטים.**

### E. פערי דרישות-מוצר אפשריים (לבדוק מול `kong_fu_chess_requirements.md`)
- **כלי "רחפן" (drone)** — סוג כלי חדש; נוסף ע"י `PieceRules` חדש בלבד (הארכיטקטורה תומכת), לא מומש.
- **סקיילביליות שרת** (מעבר לתהליך יחיד) — לא מומש (non-functional).
- לוודא שאין דרישות UI/מוצר נוספות שלא כוסו.

## 5. גוצ'ות/הערות למי שממשיך
- `WebSocketConnection.is_closed()` נדלק על **כשל התחברות** ו**נפילה חריגה** (recv raises) — **לא** על `close()` נקי מהלקוח (ה-`_send` נשאר תקוע על התור). זה בסדר לשימוש הנוכחי (הבאנר לקריסת שרת עובד).
- `MessageDispatcher.__init__` — הפרמטר השלישי (positional) הוא `auth_service`.
- נתיב ה-DB דרך env `KFC_DB` (ברירת מחדל `kong_fu_chess.db`, gitignored). smokes משתמשים ב-`:memory:` (חיבור יחיד ארוך-חיים בשרת שומר את ה-db בחיים).
- נאמנות אנימציה תלויה ב-`piece_id` יציב מהשרת + state_snapshot נושא ids.
- smokes ב-scratchpad: `smoke_auth.py` עדכני; `smoke_online/resilience/banner` עדיין קוראים ל-`client_messages.connect` שנמחק — לעדכן ל-register/login אם משתמשים בהם שוב.

## 6. הרצה ובדיקות
- לוקאלי: `python game/app.py` (עם `PYTHONPATH=game`).
- אונליין: `python game/server/server_main.py` + `python game/app_online.py <user> <pass> <room>`.
- טסטים: `python -m pytest` (494 עוברים; `pythonpath=game` ב-pytest.ini).
- ענף `server` דחוף ל-`origin`. **מיזוג ל-main עדיין לא נעשה.**
