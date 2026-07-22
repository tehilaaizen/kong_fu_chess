# תכנית עבודה — מעבר לארכיטקטורת שרת-לקוח (WebSockets)

מקור: [server_desine.md](server_desine.md). מסמך זה מתרגם אותו לתכנית עבודה מעשית, **מעוגנת בקוד הקיים** ובחלוקת השכבות המחייבת של [kung_fu_chess_design_guide.md](kung_fu_chess_design_guide.md).

> ⚠️ **לפני מימוש** — יש כאן החלטות ארכיטקטוניות פתוחות (סעיף 6) שחייבות אישור, כי `server_desine.md` מוסיף היקף שה-design guide **בכלל לא מכסה** (רשת, חדרים, ELO, שידוכים, SQLite). לפי CLAUDE.md, לא מכריעים אותן לבד.

---

## 1. מה כבר קיים ומשרת אותנו (Seams)

הקוד כבר בנוי עם התפרים הנכונים למעבר הזה — **אין צורך לשכתב את הליבה**:

| רכיב קיים | תפקידו בשרת-לקוח |
|---|---|
| `GameEngine` (`engine/game_engine.py`) | הליבה של `GameManager` בצד השרת — כבר ה-command boundary (`request_move`/`request_jump`/`wait`/`snapshot`) |
| `CommandSender` Protocol (`input/commands.py`) | ה-comment שם כבר מנבא `NetworkCommandSender` — זה מסלול הלקוח→שרת (`make_move`) |
| Observers של `GameEngine` (`on_arrival`/`on_motion_started`/`on_rest_started`/`on_game_over`) | מתמפים ישירות לאירועי ה-Bus (`update_scores`/`update_move_logs`/`play_sound`/`game_animation`) |
| `GameSnapshot` (`engine/game_snapshot.py`) + `BoardPrinter` (`text_io/`) | ה-payload של `game_state` (מחרוזת לוח + מי זז) |
| `wait(ms)` + `FrameClock` (`view/frame_clock.py`) | תזמון — אבל **סמכות הזמן עוברת מהלקוח לשרת** (ראו סעיף 6.B) |

**עיקרון מנחה:** שכבת הרשת (`server/` + `client/`) יושבת ב**קצה החיצוני** ביותר, לצד `view/`/`input/`. אסור שהיא תדלוף פנימה ל-`model/`/`rules/`/`engine/`. הליבה נשארת agnostic לרשת — בדיוק כמו שהיא agnostic ל-pygame היום.

---

## 2. מבנה חבילות מוצע (חדש)

```
game/
  server/
    ws_server.py          # שרת WebSocket (adapter דק בלבד)
    game_manager.py       # עוטף GameEngine אחד לכל חדר/משחק
    bus.py                # Pub/Sub פנימי (register/publish)
    room_registry.py      # חדרים, חלוקת תפקידים (white/black/viewers)
    matchmaking.py        # תור שידוכים + ELO ±100 + timeout 60ש'
    disconnect_manager.py # grace period 20ש' + auto-resign
    users/
      user_store.py       # SQLite: שם משתמש + סיסמה מוצפנת
      elo.py              # חישוב ELO (התחלה 1200)
    server_clock.py       # מקור-האמת לזמן בצד השרת (tick loop)
    logging_setup.py      # לוגים עם timestamp (צד שרת)
  client/
    ws_client.py          # לקוח WebSocket
    network_command_sender.py  # ממש CommandSender → JSON → שרת
    shell_login.py        # login/register דרך terminal (ללא GUI)
    home_screen.py        # מסך בית: Play / Room
    server_state_applier.py    # מקבל game_state ומעדכן את ה-view
    client_logging.py     # לוגים צד לקוח
  io/
    move_notation.py      # "WQe2e5" ⇄ (source, destination)  (adapter, כמו BoardParser)
```

הערה: `move_notation.py` שייך ל-`io/` (שכבת adapters טקסטואליים משותפת) — עקבי עם `BoardParser`/`BoardPrinter` שכבר שם. אין לפזר פירסור מחרוזות-מהלך ב-Controller/Server.

---

## 3. שלבי עבודה (ממופים לשלבי server_desine.md)

### שלב 0 — תשתית ובדיקתיות (לפני הכל)
- להחליט על ספריית WebSockets ומודל async (סעיף 6.A).
- להקים `bus.py` — Pub/Sub פנימי טהור (בלי רשת), בדיק ביחידה.
- להקים `server_clock.py` — tick loop שקורא ל-`engine.wait(elapsed)`, עם **clock מוזרק** כדי לשמור על בדיקות זמן-מדומה (בלי `time.sleep`).
- **בדיקות:** unit ל-Bus ול-clock; ה-DSL הטקסטואלי הקיים ממשיך לעבוד ללא שינוי.

### שלב 1 — סנכרון לוח בין שני לקוחות (server_desine צעד 1+2)
- `game_manager.py`: עוטף `GameEngine` יחיד; מנוי כ-observer ומפרסם ל-Bus.
- `ws_server.py`: מקבל `make_move`/`join_room` (JSON), מריץ דרך `GameManager`, משדר `game_state` לכל המחוברים.
- `io/move_notation.py`: פירסור `"WQe2e5"` → Positions → `request_move`. **החלטה 6.C**.
- `client/`: `network_command_sender.py` (ממש `CommandSender`), `ws_client.py`, `server_state_applier.py` שמזין `GameSnapshot` שהתקבל ל-view הקיים.
- חיבור אירועי Bus (`play_sound`/`game_animation`) → הודעות `trigger_event` ללקוח.
- **בדיקות:** integration עם transport מזויף (in-memory), בלי socket אמיתי; שני "לקוחות" רואים אותו לוח.

### שלב 2 — משתמשים ו-ELO (server_desine צעד 3)
- `users/user_store.py`: SQLite, hashing לסיסמה (`bcrypt`/`hashlib`+salt — סעיף 6).
- `users/elo.py`: התחלה 1200, חישוב מחדש בסיום משחק (מנוי ל-`on_game_over`).
- `client/shell_login.py`: register/login דרך terminal לפני פתיחת ה-GUI.
- **בדיקות:** unit ל-ELO ול-user_store (DB זמני מוזרק, לא הקובץ האמיתי).

### שלב 3 — חדרים וצפייה (server_desine צעד 4)
- `room_registry.py`: Create מייצר Room ID; Join מצרף; role assignment: 1=white, 2=black (משחק מתחיל), 3+=viewers.
- חסימת `make_move` מצופים בצד השרת.
- `client/home_screen.py`: כפתורי Play/Room, popup עם Create/Join/Cancel, הצגת Room ID.
- **בדיקות:** unit ל-room_registry (חלוקת תפקידים, חסימת viewer).

### שלב 4 — שידוכים (Matchmaking) (server_desine צעד 4)
- `matchmaking.py`: תור, זיווג לפי ELO ±100, timeout 60ש' → הודעת שגיאה → popup בלקוח.
- **בדיקות:** unit עם clock מוזרק (timeout מדומה, בלי sleep).

### שלב 5 — ניתוקים (server_desine צעד 5)
- `disconnect_manager.py`: ספירה 20ש' על ניתוק, טיימר מוצג ללקוח הנשאר, auto-resign אם לא חזר.
- **בדיקות:** unit עם clock מוזרק.

### שלב רוחבי — לוגים (server_desine שלב 5)
- `logging_setup.py` + `client_logging.py`: כל פעולה (login/move/state/disconnect/error) עם timestamp לקובץ ייעודי. עדיף להקים מוקדם כדי לעזור בדיבאג של שאר השלבים.

---

## 4. פרוטוקול ההודעות (מ-server_desine)

לקוח→שרת: `make_move` (`{"move":"WQe2e5"}`), `join_room` (`{"room_id":"1234"}`).
שרת→לקוח: `game_state` (`{"board":"...","turn":"..."}`), `trigger_event` (`{"event":"move_sound"}`).
מעטפת: `{"type": ..., "payload": {...}}`. פירסור/סריאליזציה במקום אחד (`io/` / שכבת ה-server), לא מפוזר.

---

## 5. עקביות עם דרישות קיימות
- **חותמת זמן שרת** (requirements §2.5, §5): ה-move-log חייב את זמן ה**שרת**, לא הלקוח — מתחבר ל-observer `on_arrival`/Bus `update_move_logs`. הזמן חייב לבוא מ-`server_clock`.
- **שרת כ-source of truth** (requirements §5): כבר תואם — הלקוח רק מציג `game_state`.
- **סקיילביליות** (requirements §3.4): הפרוטוקול תוכנן מראש דק ויעיל; מימוש single-process, אבל בלי צווארי בקבוק מיותרים.

---

## 6. החלטות פתוחות — לאישור לפני מימוש ⚠️

לפי CLAUDE.md, אלה סתירות/פערים מול ה-design guide שאסור להכריע לבד:

**A. ספריית WebSockets ומודל async.**
`websockets`+`asyncio`? זו תלות חדשה. השאלה הקריטית: איך שומרים על הבדיקתיות של הפרויקט (DSL, זמן מדומה, בלי `time.sleep`) כשמכניסים event loop ורשת אמיתית? הכיוון המוצע: כל הלוגיקה (GameManager/Bus/matchmaking/disconnect) נבדקת בבידוד עם clock ו-transport מוזרקים; ה-WebSocket הוא adapter דק בלבד.

**B. סמכות הזמן עוברת לשרת.**
היום ה-`FrameClock` בלקוח מריץ `engine.wait`. במודל שרת-לקוח **השרת** מריץ tick loop ומחזיק את הזמן; הלקוח רק מצייר. זה שינוי אמיתי במי-מריץ-את-`wait`. צריך לאשר את הגישה (real-time tick בשרת + clock מוזרק בבדיקות).

**C. נוטציית מהלך `"WQe2e5"` מול קלט מבוסס-קליק.**
כל שכבת ה-input/Controller עובדת בפיקסלים/קליקים ובלי "צבע במהלך". הפרוטוקול מגדיר מחרוזת מהלך. צריך adapter (`io/move_notation.py`) שממיר מחרוזת→Positions. לאשר את המבנה ואת הפורמט המדויק.

**D. היקף ורצף מול ה-refactor הקיים.**
ה-design guide עדיין לא הושלם (הפרויקט באמצע refactor). האם server_desine הופך לעדיפות העליונה שדוחה איטרציות design-guide שנותרו? מה חתך ה-MVP של server_desine (למשל: שלב 1 בלבד עכשיו) מול מה שנדחה?

**E. היקף ה-UI של הלקוח.**
היום הלקוח = חלון pygame יחיד. server_desine דורש: login ב-shell, מסך בית עם Play/Room, popups, הצגת Room ID, טיימר ניתוק. כמה מזה בהיקף עכשיו מול בהמשך?

**F. הצפנת סיסמאות.**
`bcrypt` (תלות) מול `hashlib`+salt (stdlib). מה מותר/מועדף.
