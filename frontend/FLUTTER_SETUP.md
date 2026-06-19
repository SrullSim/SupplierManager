# הרצת אפליקציית ה-Flutter (Web)

> הקוד של האפליקציה מוכן ב-`lib/`. כדי להריץ צריך פעם אחת להתקין Flutter
> ולייצר את קבצי הפלטפורמה (תיקיית `web/`).

---

## שלב 1 — להתקין Flutter (פעם אחת)

1. הורד את Flutter ל-Windows: https://docs.flutter.dev/get-started/install/windows
2. חלץ את ה-zip (למשל ל-`C:\src\flutter`).
3. הוסף את `C:\src\flutter\bin` ל-PATH של Windows.
4. פתח טרמינל חדש ובדוק:
   ```bash
   flutter --version
   flutter doctor
   ```
   `flutter doctor` יראה לך מה חסר. ל-Web מספיק שיהיה Chrome מותקן.

---

## שלב 2 — לייצר את קבצי הפלטפורמה (פעם אחת)

מתוך תיקיית `frontend`:
```bash
cd "C:\Users\User\OneDrive\Desktop\Supplier Manager\frontend"
flutter create --platforms=web .
```

> פקודה זו מוסיפה **רק** את תיקיית `web/` (index.html וכו').
> היא **לא** דורסת את הקוד שכתבתי ב-`lib/` ולא את `pubspec.yaml`.

---

## שלב 3 — להתקין חבילות + לייצר תרגומים

```bash
flutter pub get
flutter gen-l10n
```

`gen-l10n` ממיר את קובצי התרגום (`lib/l10n/app_he.arb`, `app_en.arb`)
למחלקת `AppLocalizations` שהקוד משתמש בה.

---

## שלב 4 — להריץ בדפדפן

ודא שה-backend רץ (ראה [../RUN.m yhd](../RUN.md)), ואז:

```bash
flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

**מה אתה אמור לראות:** דפדפן Chrome נפתח עם מסך התחברות בעברית (RTL).

התחבר עם:
- מפעל: `admin` / `admin1234` → מגיע למסך "ממשק מפעל"
- סניף: `jeru01` / `branch1234` → מגיע למסך "ממשק סניף"

---
   
## הגדרות (Feature Flags)

מועברות עם `--dart-define`:

| משתנה | ברירת מחדל | מה עושה |
|-------|-----------|---------|
| `API_BASE_URL` | `http://127.0.0.1:8000` | כתובת ה-backend |
| `MULTI_LANGUAGE_ENABLED` | `false` | האם להציג בורר שפה (כרגע עברית בלבד) |

דוגמה עם backend אחר:
```bash
flutter run -d chrome --dart-define=API_BASE_URL=http://192.168.1.50:8000
```

---

## בעיות נפוצות

| תסמין | פתרון |
|-------|-------|
| `flutter: command not found` | Flutter לא ב-PATH (שלב 1) |
| שגיאת CORS בדפדפן | ה-backend כבר מאפשר CORS ב-staging; ודא ש-`APP_ENV=staging` |
| `AppLocalizations` לא נמצא | הרץ `flutter gen-l10n` (שלב 3) |
| מסך לבן | פתח DevTools בדפדפן (F12) → לשונית Console לראות שגיאות |
