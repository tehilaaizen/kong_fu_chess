# מסמך דרישות UI — תמלול מצגת הקורס

> מסמך זה מבוסס על תמלול מצגת הקורס העוסקת ב-UI (תמונות, Sprites, אנימציה, קלט עכבר, Observer). זהו **מקור שלישי** בנוסף ל-[kung_fu_chess_design_guide.md](kung_fu_chess_design_guide.md) (ארכיטקטורה מחייבת) ו-[kong_fu_chess_requirements.md](kong_fu_chess_requirements.md) (פיצ'רים/MVP). ראו section "זיהוי סתירות/פערים מול המסמכים הקיימים" למטה — **אין להכריע סתירות לבד**, יש לוודא עם המשתמשת לפני מימוש (עקרון קבוע ב-CLAUDE.md).

---

## 1. עבודה עם תמונות (רקע תיאורטי, לא דרישת מימוש ישירה)

מושגים שהמצגת מצפה שנכיר לפני עבודה עם UI מבוסס-תמונות: מערכת צירים (X,Y), מבנה פיקסלים, מודל צבע RGB, ייצוג צבעים בזיכרון, ערוץ Alpha (שקיפות), ההבדל PNG מול JPEG, עומק צבע (Bit Depth), שכבות (Layers), Overlay/Flattening, הטמעת טקסט על תמונה. מומלץ Paint.NET לתרגול. **אין כאן דרישת קוד** — זה בסיס להבנת איך אסטים/אנימציות בנויים.

## 2. ספריית גרפיקה קיימת

- **לא** כותבים ספריית ציור מאפס — הקורס מספק ספריית טעינת תמונות + דוגמאות שימוש + repository מוכן.
- מסופקת תיקיית **Assets** עם כל התמונות הדרושות למשחק.
- **עודכן 2026-07-14 — נמצא בפועל:** המשתמשת שיבטה clone מקומי של הריפו `https://github.com/KamaTechOrg/CTD26` בנתיב `C:\tehila\bootcamp\CTD26`. תוכן רלוונטי:
  - **`py/img.py`** — מחלקת `Img` שעוטפת `opencv-python` (`cv2`): `read(path, size=None, keep_aspect=False, interpolation=...)` (טעינה + resize אופציונלי), `draw_on(other_img, x, y)` (blend עם ערוץ alpha אם קיים), `put_text(...)`, `show()`. זו "ספריית טעינת התמונות" מהמצגת — תלות: `opencv-python` (ראה `py/requirements.txt`).
  - **`board.png`** — תמונת רקע ללוח.
  - **`pieces1/` ו-`pieces2/`** — **שני packs חלופיים** של אותם 12 סוגי-כלים (לא ברור עדיין אם לבחור אחד או לתמוך בשניהם כ"סקין" נבחר — ראו שאלה פתוחה בהמשך). כל pack מכיל תיקייה לכל שילוב `<אות-כלי><צבע>`, למשל `PW`, `PB`, `RW`, `RB`, `NW`, `NB`, `BW`, `BB`, `QW`, `QB`, `KW`, `KB` — **שימו לב לסדר ההפוך** מהמוסכמה הפנימית שלנו (`wP`/`bK`, צבע ואז אות) — זו נקודת מיפוי (naming adapter) שצריכה לשבת רק בקוד טעינת ה-assets, לא לדלוף למודל.
  - כל תיקיית כלי מכילה `board.csv` לדוגמת פריסת לוח התחלתית (פורמט `<אות><צבע>`/ריק, מופרד בפסיקים) ו-`states/{idle,move,jump,short_rest,long_rest}/` — **חמישה מצבים בדיוק**, כל אחד עם `config.json` + `sprites/1.png`…`5.png` (5 פריימים נכון להיום).
  - **סכימת `config.json` בפועל** (זהה במבנה לכל מצב/כלי/pack, רק ערכים משתנים):
    ```json
    {
      "physics": { "speed_m_per_sec": 1.5, "next_state_when_finished": "long_rest" },
      "graphics": { "frames_per_sec": 12, "is_loop": true }
    }
    ```
    כלומר: **גם מהירות תנועה וגם גרף-מעברים בין מצבי-אנימציה מוגדרים ב-JSON הזה**, לא רק FPS/loop.
  - ערכים שנמצאו בפועל (זהים בכל 6 סוגי הכלים ובשני ה-packs, נכון לעכשיו): `idle`: speed=0, next=`idle` (loop, 6fps); `move`: speed=1.5, next=`long_rest` (loop, 12fps); `jump`: speed=3.0, next=`short_rest` (לא-loop, 8fps); `short_rest`: speed=0, next=`idle` (לא-loop, 8fps); `long_rest`: speed=0, next=`idle` (לא-loop, 6fps). המהירות אחידה בין כל הכלים/ה-packs — **תואם** לקבוע האחיד `PIECE_SPEED=100px/s` שב-design guide §10 (אין התנגשות היום), אבל הסכימה כן תומכת מהירות-לפי-כלי בעתיד (רלוונטי ל"רחפן" מ-`kong_fu_chess_requirements.md` §3.2).

## 3. Sprites

- אנימציות **לא** נוצרות בקוד — לכל דמות/כלי יש סדרת תמונות מוכנה מראש, מסודרת בתיקיות.
- ה-UI צריך "רק" להציג רצף תמונות בזמן הנכון — לא לצייר צורות.

## 4. מערכת אנימציות

מושגים נדרשים למימוש:
- אנימציה **סדרתית** (Sequential) — רצף פריימים חד-פעמי (לדוגמה: הליכה בין שתי משבצות).
- אנימציה **מחזורית** (Circular/Looping) — רצף שחוזר על עצמו (לדוגמה: Idle).
- **FPS** — קצב החלפת פריימים.
- **קובצי JSON** שמתארים כל אנימציה (כנראה: רשימת קבצי פריימים, FPS, loop:true/false).
- **State Machine** — לכל כלי יש מצב (Idle / Walk / Jump / Rest וכו'), ולפי המצב מוצגת אנימציה שונה.

## 5. בקרת משחק (קלט עכבר)

- טיפול ב-Mouse Events, מיקום יחסי לחלון, חלון בגודל משתנה (resizable window).
- הבחנה בין **פיקסלי מסך** (screen pixels) לבין **פיקסלי תמונה/לוח** (image/board pixels), והמרה ביניהם.
- דרישה לוודא שהמיפוי עובד נכון (איזשהו מנגנון בדיקה/וידוא).

## 6. דרישות תצוגה נוספות

- **יומן מהלכים** (Moves Log).
- **ניקוד** (Score) — מחושב לפי ערך הכלים שנלכדו.
- **שמות שחקנים**.

## 7. Observer

- השקופית האחרונה מזכירה רק את המילה "Observer", בלי פירוט.
- פרשנות סבירה: ה-UI **לא** אמור למשוך מידע מהמנוע (pull) בצורה חופשית/בלתי-מובנית, אלא להתעדכן דרך תבנית Observer כשמצב המשחק משתנה.

---

## מיפוי לארכיטקטורה הקיימת (design guide)

בדיקה מול [kung_fu_chess_design_guide.md](kung_fu_chess_design_guide.md) — מה כבר יש מקום עבורו, ומה חדש:

| דרישה מהמצגת | מקום קיים בארכיטקטורה | הערה |
|---|---|---|
| טעינת תמונות/Assets | `view/image_view.py` (כבר מוגדר ב-§5 Package Structure, עדיין לא ממומש) | תואם — צריך רק את הספרייה/Assets בפועל |
| מיפוי פיקסלים↔לוח, מיקום עכבר | `input/board_mapper.py` (**קיים וממומש** — `game/input/board_mapper.py`) | תואם ישירות; §11 כבר מגדיר `col = x // CELL_SIZE` וכו' |
| Renderer מצייר GameSnapshot | `view/renderer.py` (§12: renderer מקבל `GameSnapshot` read-only) | תואם |
| ניקוד / יומן מהלכים / שמות שחקנים | **אין להם מקום מוגדר** ב-common route של ה-design guide | ראו סתירה #1 למטה — כבר מתועדת ב-[[kong_fu_chess_project_status]], המצגת היא מקור *שלישי* שתומך בהכללתם |
| Sprite + Animation State Machine + JSON | **לא קיים כלל** במבנה ה-packages הנוכחי (§5 מונה רק `renderer.py`/`image_view.py` תחת `view/`) | דורש תוספת ל-`view/` (לא לשכבות אחרות) — ראו שאלה #2 למטה |
| Observer | **לא מוזכר** ב-design guide; §12 מתאר מודל pull (`GameSnapshot` שנמשך) לא push | ראו שאלה #3 למטה |

**חשוב:** לפי סעיף 5 ב-design guide (Extra Route Rule #7: "Visual polish without changing the model") ו-CLAUDE.md, אנימציה/Sprite/Observer שייכים **אך ורק** לשכבת `view/` (ו-נקודת ה-notify מ-`GameEngine`/`Controller` אם צריך Observer) — הם **אסורים** מלדלוף ל-`model/`, `rules/`, `engine/`. בפרט: `Piece.state` (idle/moving/captured) הוא ה-signal היחיד שה-state machine של האנימציה אמור לצרוך — אסור להוסיף ל-`Piece` שדות אנימציה/פריים/FPS.

---

## זיהוי סתירות/פערים מול המסמכים הקיימים

### סתירה #1 (כבר מתועדת, עכשיו עם מקור שלישי תומך)
`kong_fu_chess_requirements.md` §2.4-2.6 מגדיר יומן מהלכים+חותמת זמן, ניקוד, ושמות שחקנים כ-**MVP חובה**. ה-design guide לא מזכיר אותם כלל ב-common route (ורואה cooldown כ-extra route אופציונלי). המצגת הנוכחית (§6 למעלה) **דורשת גם היא** הצגת יומן מהלכים/ניקוד/שמות — זהו קול שלישי בכיוון "כן ליישם", אך זו עדיין לא הכרעה - **יש לוודא עם המשתמשת** אם זה משנה את הסטטוס (עדיין "לתכנן עיצוב UI כך שיהיה מקום, אך לא בהכרח לממש בסבב הראשון של iteration 9").

### פער #2 — Sprite/Animation לא קיים כלל בתכנון הנוכחי
ה-design guide (§5, §12) לא צופה JSON-described sprite animations, FPS, state machine נפרד לאנימציה. זו תוספת אמיתית לתכנון (לא רק "כבר קיים, רק לממש"). לפי CLAUDE.md סעיף 4 ("בלי over-engineering" אך "גמישות רק סביב הרחבות ידועות מראש") - אנימציה **כן** מופיעה ברשימת ההרחבות הידועות (design guide §12 responsibilities include "draw moving pieces between cells"), אז זו תוספת לגיטימית בתוך `view/`, לא over-engineering. עדיין צריך להחליט על מבנה קבצים בפועל (למשל `view/sprite.py` + `view/animation_state_machine.py`, או קובץ אחד) לפני מימוש.

**עודכן 2026-07-14 — ממצא ארכיטקטוני חשוב מבדיקת ה-assets בפועל:** ה-state machine שמוגדר בפועל ב-assets (`idle`/`move`/`jump`/`short_rest`/`long_rest`, עם גרף מעברים מפורש דרך `next_state_when_finished`) הוא **עשיר יותר** מ-`Piece.state` הקיים היום ב-`game/model/piece.py` (רק `idle`/`moving`/`captured` — lifecycle flag בלבד, בכוונה, לפי §6 ב-design guide). באופן קונקרטי:
- **אין עדיין מושג cooldown/rest** בשום שכבה של הקוד הקיים (`short_rest`/`long_rest` לא קיימים לא ב-`Piece.state`, לא ב-`RealTimeArbiter`, לא במקום אחר) — זה עדיין ה-extra-route feature הלא-ממומש שכבר מתועד ב-[[kong_fu_chess_project_status]].
- **jump קיים היום רק כ`realtime/jump.py`'s `Jump`** (מעקב "באוויר עד `until_clock_ms`", לצורך כללי ההתנגשות עם תקיפה) — **לא** כסוג-תנועה נפרד שמובחן מ-move רגיל ברמת ה-snapshot/state שיוצג ל-view.
- **המשמעות:** מנגנון האנימציה **לא יכול** להיות תוספת טהורה בתוך `view/` בלבד שנשענת רק על `Piece.state`/`GameSnapshot` הקיימים — כדי לבחור בין `move`/`jump`/`short_rest`/`long_rest` בפועל, ה-engine/realtime צריך לחשוף מידע נוסף שהיום לא קיים (האם הכלי במנוחה ועד מתי, והאם ה"מנוחה" הנוכחית מקורה בקפיצה או במהלך רגיל). זה בפועל אותו extra-route work (cooldown+jump) שכבר מזוהה — לא לממש את זה כ"עוקף" בתוך שכבת ה-view כדי "לחסוך" את עבודת ה-engine, כי זה בדיוק סוג ה-shortcut שה-design guide/CLAUDE.md אוסרים (Motion/pending-state שייכים ל-realtime, לא ל-view).
- לכן: לפני שבונים את ה-Sprite/Animation-state-machine במלואו (כולל short_rest/long_rest/jump), צריך להחליט את **סדר האיטרציות** — אנימציה בסיסית (idle/move בלבד, תואמת את מה שכבר קיים ב-`Piece.state`) יכולה להיבנות עכשיו; jump/rest-אנימציה תלויה במימוש extra-route של cooldown+jump-cooldown קודם.

### פער #3 — Observer לא מתואר ב-design guide
§12 מתאר מודל pull: ה-Renderer מקבל `GameSnapshot` (ולא נרשם ל-notifications). המצגת מציינת Observer בפירוש. יש כאן שתי אפשרויות ארכיטקטוניות שונות (לא ניתן להכריע לבד):
- **(א)** להשאיר pull — ה-renderer קורא ל-`GameEngine.snapshot()` פעם בכל frame (הפשוט ביותר, תואם למה שכבר כתוב ב-§12/§19, ולא דורש שינוי API).
- **(ב)** להוסיף Observer אמיתי — `GameEngine` (או `Controller`) חושף `add_observer(observer)`/`notify()` וקורא לזה אחרי מהלך מתקבל/tick, וה-Renderer נרשם כ-observer.

---

## הבנה שלי לגבי מימוש (ללא שינוי קוד עדיין)

מבנה מוצע (לדיון, לא להטמעה מיידית) שמתיישב עם השכבות הקיימות:

- **`view/image_view.py`**: עטיפת ספריית טעינת התמונות שהקורס מספק (טעינת קובץ תמונה בודד → אובייקט frame ניתן-לציור).
- **`view/sprite.py`** (חדש): מייצג רצף פריימים + מטא-דאטה (FPS, loop: bool) שנטען מ-JSON; יודע "מה הפריים הנוכחי" לפי זמן שחלף — לא יודע כלום על שחמט/Board/Piece.
- **State machine של אנימציה** (בתוך `view/` בלבד): ממפה `Piece.state`/`Motion` הקיימים (מה-`GameSnapshot`) לבחירת ה-Sprite המתאים (idle/walk/rest) — קריאה בלבד, לא כותב למודל.
- **`view/renderer.py`**: כפי שכבר מוגדר ב-§12 — מצייר grid, כלים (במיקום פיקסל מהסנפשוט), בחירה מסומנת, כלים בתנועה, הודעת game-over. תוספת: ציור יומן מהלכים/ניקוד/שמות אם יוחלט לכלול אותם (סתירה #1).
- **`input/board_mapper.py`**: **כבר קיים וממומש** — אין צורך במימוש חדש למיפוי עכבר↔לוח; רק לחבר אותו לחלון בגודל משתנה בפועל (זה כבר בתחום האחריות המוגדר, §11).
- **Observer**: תלוי בהכרעה בפער #3 לעיל.

זו הבנה כללית של "מה צריך" — **לא** מהווה מימוש. שאלות פתוחות (למטה) חוסמות תחילת מימוש בפועל.

---

## החלטות שהתקבלו (2026-07-14)

בעקבות שאלות הפתיחה למעלה, המשתמשת הכריעה:

1. **ספריית תמונות/Assets** — קיים קישור/קובץ אצל המשתמשת (ספריית הקורס + תיקיית Assets). **טרם צורף/תועד בפועל** — עדיין נדרש הקישור/הנתיב המדויק לפני שמתחילים לכתוב `view/image_view.py`.
2. **סתירה #1 (ניקוד/יומן מהלכים/שמות שחקנים)** — **הוכרע: נכנס ל-scope עכשיו**, לא נשאר extra-route. יש לתכנן את זה כחלק מ-iteration 9 (UI), בכפוף לעקרון "שינויים נקודתיים" ב-CLAUDE.md — לוודא שזה לא דורש לגעת ב-`model`/`rules`/`engine` (הניקוד/היומן נגזרים מ-`ArrivalEvent`/`GameSnapshot` הקיימים, לא מצריכים שדות חדשים ב-`Piece`/`Board`).
3. **פער #3 (Observer)** — **הוכרע: Observer אמיתי (push)**. `GameEngine` (או `Controller`, לפי מי שבאמת "יודע" שמשהו קרה) יחשוף `add_observer(observer)`/`notify()` ויקרא לזה אחרי מהלך שהתקבל/tick; ה-Renderer (וכל צרכן UI אחר — יומן מהלכים, ניקוד) נרשם כ-observer ולא מושך `snapshot()` ביוזמתו בכל frame. שינוי זה **כן** נוגע ל-§12/§19 של ה-design guide (מודל ה-pull המתועד שם) — יש לעדכן שם בהמשך שהמימוש בפועל הוא push, לא רק לסמן את זה כאן.

## שאלות פתוחות שנותרו לפני מימוש בפועל

1. ~~הקישור/הקובץ המדויק לספריית הגרפיקה ותיקיית ה-Assets~~ — **נפתר.** נמצא ב-`C:\tehila\bootcamp\CTD26` (`py/img.py` + `board.png` + `pieces1/`/`pieces2/`), ראו סעיף 2 למעלה.
2. **`pieces1` מול `pieces2`** — שני packs זהים במבנה (12 תיקיות כלים, אותם 5 מצבים) אך זה skin/pack חלופי. לבחור אחד כברירת מחדל, או לתכנן בחירת-skin? (בהיעדר החלטה — ברירת מחדל סבירה: `pieces1`, ולתעד את זה כהחלטה נקודתית קלה-לשינוי, לא ארכיטקטורה.)
3. **סדר מימוש (מ-פער #2 למעלה)** — לאשר: אנימציית idle/move בסיסית עכשיו (מבוססת על `Piece.state` הקיים), ו-jump/short_rest/long_rest רק **אחרי** שה-extra-route של cooldown+jump-cooldown ממומש ב-`realtime`/`engine` (כדי ש-view לא "יעקוף" ויממש בעצמו מידע שצריך לבוא מה-engine).
4. **פער #2 (מבנה קבצים)** — לאשר את מבנה הקבצים המוצע (`view/sprite.py` + state machine בתוך `view/`) לפני שנכתב קוד.
5. **עיצוב ה-Observer בפועל** — האם `add_observer`/`notify` יושבים על `GameEngine` או על `Controller`? (`GameEngine` הוא היחיד שבאמת "יודע" מתי מהלך התקבל/game_over/arrival — נראה המקום הנכון, אך לא סוכם באופן מפורש עדיין.)
6. **תלות חדשה** — `opencv-python` (`cv2`) אינו כרגע ב-dependencies של הפרויקט (אין `requirements.txt`/`pyproject.toml` נבדק כאן) — יש להוסיף אותו כשמתחילים לממש `view/image_view.py`.
