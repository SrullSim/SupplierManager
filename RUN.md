# איך מריצים את כל המערכת (מדריך הרצה מלא)

> מדריך מעשי, שלב-אחר-שלב, לכל המערכת: מסד נתונים → שרת (backend) → אפליקציה (frontend).
> כל שלב מלווה ב"מה אתה אמור לראות". אם משהו לא תואם — שם הבעיה.
> לאיתור הקובץ הרלוונטי לכל באג, ראה [FILE_GUIDE.md](FILE_GUIDE.md).

המערכת בנויה משלושה חלקים שרצים יחד:

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Flutter (web)  │ ──> │ FastAPI (backend)│ ──> │ MongoDB (Docker)│
│  פורט 5000+     │ HTTP│   פורט 8000      │     │   פורט 27017    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

---

## דרישות מקדימות (התקנה חד-פעמית)

| כלי | בשביל | בדיקה שזה מותקן |
|-----|-------|------------------|
| Docker Desktop | MongoDB | `docker --version` |
| Python 3.12+ | ה-backend | `python --version` |
| Flutter 3.4+ | ה-frontend | `flutter --version` |

> אם Flutter לא מותקן — ראה [frontend/FLUTTER_SETUP.md](frontend/FLUTTER_SETUP.md).

---

# חלק א׳ — Backend (חובה)

## שלב 1 — להפעיל את MongoDB

```bash
cd "C:\Users\User\OneDrive\Desktop\Supplier Manager"
docker compose up -d mongo
```
**אמור לראות:** `Container bakery_mongo Started`.
בדיקה: `docker ps` → `bakery_mongo` עם `Up ... (healthy)`.

## שלב 2 — להתקין חבילות Python (פעם אחת)

```bash
cd "C:\Users\User\OneDrive\Desktop\Supplier Manager\backend"
pip install -e ".[dev]"
```
**אמור לראות:** `Successfully installed ...` בלי שגיאות.

## שלב 3 — נתוני דמו (admin + מוצרים + סניף)

```bash
cd "C:\Users\User\OneDrive\Desktop\Supplier Manager"
python scripts/seed_dev.py
```
**אמור לראות:**
```
Factory admin  -> branch_code=admin    password=admin1234
Demo branch    -> branch_code=jeru01   password=branch1234
```

## שלב 4 — להריץ את השרת

```bash
cd "C:\Users\User\OneDrive\Desktop\Supplier Manager\backend"
uvicorn main:app --reload
```
**אמור לראות:** `Uvicorn running on http://127.0.0.1:8000`.

> ה-`SECRET_KEY` נטען אוטומטית מ-[backend/.env](backend/.env). אין צורך להגדיר ידנית.

## שלב 5 — לבדוק את ה-API ב-Swagger

פתח: **http://127.0.0.1:8000/docs**

1. `POST /auth/login` → Try it out → `{ "branch_code": "admin", "password": "admin1234" }` → Execute
2. העתק את ה-`access_token` מהתשובה.
3. לחץ **🔓 Authorize** (למעלה מימין) → הדבק את הטוקן → Authorize → Close.
4. עכשיו כל קריאה ל-`/factory/...` תעבוד (תקבל **200/201**).

> ⚠️ הדבק רק את הטוקן (בלי המילה `Bearer`). הטוקן חייב לבוא מאותו שרת. תוקף: 30 דק׳.

---

# חלק ב׳ — Frontend (אפליקציית Flutter, web)

> ודא שה-backend (חלק א׳) רץ קודם.

## שלב 6 — הכנה חד-פעמית

```bash
cd "C:\Users\User\OneDrive\Desktop\Supplier Manager\frontend"
flutter create --platforms=web .     # מייצר את תיקיית web/ (לא נוגע ב-lib/)
flutter pub get                       # מתקין חבילות
flutter gen-l10n                      # מייצר את קובצי התרגום
```

## שלב 7 — להריץ בדפדפן

```bash
flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000
```
**אמור לראות:** Chrome נפתח עם מסך התחברות בעברית (RTL).

**התחבר:**
| תפקיד | קוד | סיסמה | מה תראה |
|-------|-----|-------|---------|
| מפעל | `admin` | `admin1234` | דשבורד: סניפים / קטלוג / משלוחים |
| סניף | `jeru01` | `branch1234` | מסך הזמנה עם מוצרים + ספירת נעילה |

---

# בדיקות (לוודא שהכל תקין)

## בדיקות Backend
```bash
cd "C:\Users\User\OneDrive\Desktop\Supplier Manager\backend"
pytest tests/ -q
```
**אמור לראות:** `86 passed`.

## בדיקות Frontend
```bash
cd "C:\Users\User\OneDrive\Desktop\Supplier Manager\frontend"
flutter analyze        # אמור: No issues found!
flutter test           # אמור: All tests passed! (15)
```

## הכל בבת אחת
מתיקיית השורש: `make check` (מריץ format + lint + בדיקות לכל הפרויקט).

---

# זרימת עבודה מלאה (מה המערכת עושה)

1. **מפעל** מתחבר, יוצר מוצרים בקטלוג, יוצר סניף (מקבל סיסמה חד-פעמית), ומשייך מוצרים לסניף.
2. **מפעל** מגדיר לוח זמנים שבועי או יוצר משלוח חד-פעמי.
3. **סניף** מתחבר, רואה רק את המוצרים שלו, ובונה הזמנה למשלוח הקרוב.
4. **כלל 12 השעות:** עד 12 שעות לפני המשלוח הסניף יכול לערוך. אחרי — ההזמנה ננעלת.
5. **בנעילה (אוטומטי):** הזמנה עם פריטים שלא אושרה → מאושרת אוטומטית; סניף בלי הזמנה → מסומן "ריק" והמפעל מקבל התראה.
6. **מפעל** רואה לכל משלוח את כל ההזמנות מכל הסניפים + מי לא הזמין.

---

# בעיות נפוצות

| תסמין | סיבה | פתרון |
|-------|------|-------|
| `401 Not authenticated` ב-Swagger | לא לחצת Authorize | שלב 5 |
| `401` אחרי שכן התחברת | טוקן משרת אחר / פג תוקף | התחבר מחדש מאותו שרת |
| `Connection refused` ל-Mongo | Docker לא רץ | שלב 1 |
| `ModuleNotFoundError` (Python) | חבילות לא הותקנו | שלב 2 |
| `flutter: command not found` | Flutter לא ב-PATH | [frontend/FLUTTER_SETUP.md](frontend/FLUTTER_SETUP.md) |
| `AppLocalizations` לא נמצא | תרגומים לא נוצרו | `flutter gen-l10n` (שלב 6) |
| מסך לבן בדפדפן | שגיאת JS | F12 → Console |
| ההזמנה תמיד "נעולה" | אין משלוח עתידי, או עברת את ה-cutoff | צור משלוח 2+ ימים קדימה |

---

# פריסה ל-Production (סקירה קצרה)

- הגדר `.env.prod` עם `APP_ENV=prod`, `SECRET_KEY` אקראי וארוך, ו-`MONGO_URI` אמיתי. **לעולם לא ב-git.**
- צור את ה-admin הראשון פעם אחת: `BOOTSTRAP_ADMIN_CODE=... BOOTSTRAP_ADMIN_PASSWORD=... python scripts/bootstrap_admin.py`.
- להתראות push אמיתיות: הגדר `FIREBASE_CREDENTIALS_JSON` (בלי זה — המערכת עובדת, רק לא שולחת push בפועל).
- בנה את ה-frontend: `flutter build web` → הקבצים ב-`frontend/build/web`.
