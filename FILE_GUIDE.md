# מפת קבצים — מה כל קובץ עושה

> כשיש לך באג או שגיאה — חפש כאן את האזור הרלוונטי כדי לדעת לאיזה קובץ לגשת.
> המבנה: כל מודול (auth, catalog, branches, deliveries, orders) בנוי באותה צורה:
> `models` (נתונים) → `repository` (גישה ל-DB) → `service` (לוגיקה) → `router` (כתובות HTTP) → `schemas` (אימות קלט/פלט).

---

## איך לקרוא את הזרימה (חשוב!)

כשמגיעה בקשה, היא עוברת בשכבות לפי הסדר:

```
בקשת HTTP
   ↓
router.py      ← מגדיר את הכתובת (/factory/products) + בודק הרשאות
   ↓
schemas.py     ← מאמת שהקלט תקין (שם לא ריק, כמות חיובית...)
   ↓
service.py     ← הלוגיקה העסקית (כללי 12 שעות, אימותים, החלטות)
   ↓
repository.py  ← קורא/כותב למסד הנתונים
   ↓
models.py      ← מבנה הנתונים במסד (Mongo)
```

**טיפ לדיבוג:** אם שגיאה היא...
- **422** → הבעיה ב-`schemas.py` (קלט לא תקין)
- **401 / 403** → הבעיה בהרשאות, ב-`router.py` או [core/dependencies.py](backend/core/dependencies.py)
- **400 / 404 / 409** → לוגיקה ב-`service.py`
- **500** → באג בקוד, בדרך כלל ב-`service.py` או `repository.py`

---

## שורש הפרויקט

| קובץ | תוכן |
|------|------|
| [README.md](README.md) | סקירה כללית, ארכיטקטורה, רשימת milestones |
| [RUN.md](RUN.md) | מדריך הרצה שלב-אחר-שלב |
| [FILE_GUIDE.md](FILE_GUIDE.md) | הקובץ הזה — מפת הקבצים |
| [docker-compose.yml](docker-compose.yml) | הגדרת MongoDB (ו-API) ב-Docker |
| [Makefile](Makefile) | פקודות קיצור: `make test`, `make lint`, `make check` |
| [.gitignore](.gitignore) | מה לא להעלות ל-git (סודות, cache) |

---

## `backend/` — הליבה

| קובץ | תוכן |
|------|------|
| [backend/main.py](backend/main.py) | **נקודת הכניסה.** מרכיב את כל ה-routers, מחבר ל-DB, מגדיר CORS + הגבלת קצב. אם endpoint לא מופיע ב-Swagger — בדוק שהוא רשום כאן. |
| [backend/pyproject.toml](backend/pyproject.toml) | רשימת החבילות + הגדרות black/mypy/pytest |
| [backend/.env](backend/.env) | סודות מקומיים (SECRET_KEY, חיבור Mongo). **לא ב-git.** |
| [backend/.env.example](backend/.env.example) | תבנית — מתעד אילו משתנים צריך |
| [backend/Dockerfile](backend/Dockerfile) | איך לבנות את ה-API כ-Docker image |

### `backend/core/` — תשתית משותפת

| קובץ | תוכן |
|------|------|
| [core/config.py](backend/core/config.py) | טוען את כל ההגדרות מ-`.env` (SECRET_KEY, אזור זמן, חיבור DB). אזור הזמן של המפעל מוגדר כאן. |
| [core/database.py](backend/core/database.py) | מתחבר ל-MongoDB דרך Beanie. שגיאת חיבור ל-DB? כאן. |
| [core/security.py](backend/core/security.py) | יצירת/אימות טוקני JWT, הצפנת סיסמאות (argon2). באג בטוקנים? כאן. |
| [core/dependencies.py](backend/core/dependencies.py) | "שומרי הסף" — `require_factory_admin`, `require_branch_user`. שגיאות 401/403 מגיעות מכאן. |

### `backend/auth/` — התחברות

| קובץ | תוכן |
|------|------|
| [auth/models.py](backend/auth/models.py) | `User` (משתמש) + `RefreshToken` (טוקן רענון) |
| [auth/schemas.py](backend/auth/schemas.py) | מבנה הבקשות: login, refresh, logout |
| [auth/service.py](backend/auth/service.py) | לוגיקת התחברות, רענון טוקן (עם rotation), התנתקות |
| [auth/router.py](backend/auth/router.py) | הכתובות: `POST /auth/login`, `/auth/refresh`, `/auth/logout` |

### `backend/catalog/` — קטלוג מוצרים

| קובץ | תוכן |
|------|------|
| [catalog/models.py](backend/catalog/models.py) | `Product` (שם, יחידה, פעיל/לא) |
| [catalog/schemas.py](backend/catalog/schemas.py) | אימות יצירה/עדכון מוצר |
| [catalog/service.py](backend/catalog/service.py) | לוגיקת מוצרים |
| [catalog/repository.py](backend/catalog/repository.py) | גישה ל-DB של מוצרים |
| [catalog/router.py](backend/catalog/router.py) | `GET/POST /factory/products`, `PATCH /factory/products/{id}` |

### `backend/branches/` — סניפים

| קובץ | תוכן |
|------|------|
| [branches/models.py](backend/branches/models.py) | `Branch` (קוד, שם, מוצרים משויכים) |
| [branches/schemas.py](backend/branches/schemas.py) | אימות יצירת סניף + הקצאת מוצרים |
| [branches/service.py](backend/branches/service.py) | יצירת סניף **+ הנפקת סיסמה**, הקצאת מוצרים (עם אימות) |
| [branches/repository.py](backend/branches/repository.py) | גישה ל-DB של סניפים |
| [branches/router.py](backend/branches/router.py) | כתובות צד המפעל: `GET/POST /factory/branches` וכו' |
| [branches/branch_router.py](backend/branches/branch_router.py) | כתובות צד הסניף: `GET /branch/products`, `/branch/deliveries/upcoming`. **least-privilege** — סניף רואה רק את שלו. |

### `backend/deliveries/` — משלוחים ולוח זמנים

| קובץ | תוכן |
|------|------|
| [deliveries/models.py](backend/deliveries/models.py) | `DeliverySchedule` (לו"ז שבועי) + `Delivery` (משלוח בודד) |
| [deliveries/schemas.py](backend/deliveries/schemas.py) | אימות לו"ז + משלוחים |
| [deliveries/service.py](backend/deliveries/service.py) | **חישוב ה-cutoff של 12 שעות** + יצירת משלוחים מהלו"ז (מודע לאזור זמן ושעון קיץ). הפונקציות `cutoff_utc`, `is_locked_dt` כאן. |
| [deliveries/repository.py](backend/deliveries/repository.py) | גישה ל-DB של משלוחים |
| [deliveries/router.py](backend/deliveries/router.py) | `GET/PUT /factory/schedule`, CRUD משלוחים, `POST /factory/deliveries/generate` |

### `backend/orders/` — הזמנות (הליבה!)

| קובץ | תוכן |
|------|------|
| [orders/models.py](backend/orders/models.py) | `Order` (סניף + משלוח + פריטים + סטטוס) |
| [orders/schemas.py](backend/orders/schemas.py) | אימות פריטים (כמות חיובית), מבנה הסיכום למפעל |
| [orders/service.py](backend/orders/service.py) | **לב הלוגיקה:** אכיפת נעילת 12 שעות, אימות שמוצר משויך+פעיל, מיזוג כפילויות, סיכום למפעל |
| [orders/repository.py](backend/orders/repository.py) | גישה ל-DB של הזמנות (הזמנה אחת לכל סניף+משלוח) |
| [orders/router.py](backend/orders/router.py) | צד סניף: `GET/PUT /branch/orders/{id}`, `POST .../confirm`. צד מפעל: `GET /factory/deliveries/{id}/summary` |

### `backend/notifications/` , `backend/orders/` ריקים?

| תיקייה | מצב |
|--------|-----|
| [backend/notifications/](backend/notifications/) | ריק — יתמלא ב-Milestone 8 (התראות push) |

### `backend/tests/` — בדיקות

| קובץ | בודק |
|------|------|
| [tests/conftest.py](backend/tests/conftest.py) | תשתית הבדיקות — DB מדומה, fixtures (admin, סניף, טוקנים) |
| [tests/test_auth.py](backend/tests/test_auth.py) | התחברות, רענון, נעילה, + בדיקות שעון קיץ ל-cutoff |
| [tests/test_catalog.py](backend/tests/test_catalog.py) | מוצרים + הרשאות |
| [tests/test_branches.py](backend/tests/test_branches.py) | סניפים, הנפקת סיסמה, בידוד least-privilege |
| [tests/test_deliveries.py](backend/tests/test_deliveries.py) | לו"ז, משלוחים, יצירה אוטומטית, שעון קיץ |
| [tests/test_orders.py](backend/tests/test_orders.py) | **הזמנות + כל מקרי הקצה של נעילת 12 השעות** |

---

## `scripts/` — סקריפטים

| קובץ | תוכן |
|------|------|
| [scripts/bootstrap_admin.py](scripts/bootstrap_admin.py) | יוצר את ה-admin הראשון (בטוח גם ל-production) |
| [scripts/seed_dev.py](scripts/seed_dev.py) | ממלא נתוני דמו (admin + מוצרים + סניף) |
| [scripts/check.sh](scripts/check.sh) | מריץ format + lint + type-check + בדיקות ביחד |
