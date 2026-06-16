# איך מריצים את הפרויקט (מדריך הרצה)

> מדריך מעשי שלב-אחר-שלב. כל פקודה מלווה ב"מה אתה אמור לראות".
> אם משהו לא תואם — שם הבעיה. ראה את [FILE_GUIDE.md](FILE_GUIDE.md) כדי לדעת לאיזה קובץ לגשת.

---

## דרישות מקדימות (פעם אחת)

| כלי | בשביל מה | בדיקה |
|-----|----------|-------|
| Docker Desktop | מסד הנתונים MongoDB | `docker --version` |
| Python 3.12+ | ה-backend | `python --version` |

---

## שלב 1 — להפעיל את MongoDB (Docker)

```bash
cd "C:\Users\User\OneDrive\Desktop\Supplier Manager"
docker compose up -d mongo
```

**מה אתה אמור לראות:** `Container bakery_mongo Started`.

בדיקה שזה באמת רץ:
```bash
docker ps
```
צריך להופיע `bakery_mongo` עם סטטוס `Up ... (healthy)`.

> אם Docker לא רץ — פתח את Docker Desktop וחכה שייטען, ואז נסה שוב.

---

## שלב 2 — להתקין את החבילות של ה-backend (פעם אחת)

```bash
cd "C:\Users\User\OneDrive\Desktop\Supplier Manager\backend"
pip install -e ".[dev]"
```

**מה אתה אמור לראות:** `Successfully installed ...` בלי שגיאות אדומות.

> אם יש שגיאת התקנה — הבעיה ב-[backend/pyproject.toml](backend/pyproject.toml) (רשימת החבילות).

---

## שלב 3 — להכניס נתוני דמו (admin + מוצרים + סניף)

```bash
cd "C:\Users\User\OneDrive\Desktop\Supplier Manager"
python scripts/seed_dev.py
```

**מה אתה אמור לראות:**
```
factory_admin created ...
Seeded 4 products.
Seeded demo branch 'jeru01' ...
Dev seed complete.
  Factory admin  -> branch_code=admin    password=admin1234
  Demo branch    -> branch_code=jeru01   password=branch1234
```

> אפשר להריץ שוב בבטחה — הסקריפט מדלג על מה שכבר קיים.
> אם יש שגיאה — הבעיה ב-[scripts/seed_dev.py](scripts/seed_dev.py) או בחיבור ל-Mongo ([backend/core/database.py](backend/core/database.py)).

---

## שלב 4 — להפעיל את השרת

```bash
cd "C:\Users\User\OneDrive\Desktop\Supplier Manager\backend"
uvicorn main:app --reload
```

**מה אתה אמור לראות:**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

> אין צורך להגדיר `SECRET_KEY` ידנית — הקובץ [backend/.env](backend/.env) מטפל בזה.
> `--reload` = השרת מתעדכן אוטומטית כשאתה משנה קוד.

---

## שלב 5 — לבדוק חי דרך Swagger

פתח בדפדפן: **http://127.0.0.1:8000/docs**

זהו ממשק אינטראקטיבי שמראה את כל ה-endpoints. כך מתחברים:

1. פתח **`POST /auth/login`** → **Try it out** → הדבק:
   ```json
   { "branch_code": "admin", "password": "admin1234" }
   ```
   → **Execute**
2. העתק את הערך של **`access_token`** מהתשובה (רק הטקסט, בלי מרכאות).
3. לחץ על **🔓 Authorize** (למעלה מימין) → הדבק את הטוקן → **Authorize** → **Close**.
4. עכשיו נסה **`GET /factory/products`** → אתה אמור לקבל **200** עם המוצרים בעברית. ✅

> ⚠️ הדבק **רק את הטוקן**, בלי המילה `Bearer` — Swagger מוסיף אותה לבד.
> ⚠️ הטוקן חייב לבוא **מאותו שרת** שאתה קורא אליו. הטוקן תקף 30 דקות.

---

## להריץ את כל הבדיקות (הדרך הכי מהירה לוודא שהכל תקין)

```bash
cd "C:\Users\User\OneDrive\Desktop\Supplier Manager\backend"
pytest tests/ -q
```

**מה אתה אמור לראות:** `73 passed` בסוף.

זה מריץ מסד נתונים מדומה (לא נוגע ב-Mongo האמיתי) ובודק את כל הלוגיקה:
auth, מוצרים, סניפים, משלוחים, הזמנות, ונעילת 12 השעות.

> אם בדיקה נכשלת — שם הקובץ שנכשל אומר לך איפה הבעיה
> (למשל `tests/test_orders.py` → לוגיקת הזמנות ב-[backend/orders/](backend/orders/)).

---

## כלי עזר — פקודות מקוצרות (Makefile)

מתוך תיקיית השורש:
```bash
make test        # מריץ בדיקות
make format      # מסדר את הקוד (black + isort)
make lint        # בודק איכות קוד (pylint)
make check       # הכל ביחד
```

---

## בעיות נפוצות

| תסמין | סיבה | פתרון |
|-------|------|-------|
| `401 Not authenticated` | לא לחצת Authorize ב-Swagger | בצע שלב 5 |
| `401` אחרי שכן התחברת | טוקן משרת אחר / פג תוקף | התחבר מחדש מאותו שרת |
| `Connection refused` ל-Mongo | Docker לא רץ | שלב 1 |
| `ModuleNotFoundError` | החבילות לא הותקנו | שלב 2 |
| שגיאת `SECRET_KEY` חסר | אין קובץ `.env` | ודא ש-[backend/.env](backend/.env) קיים |
