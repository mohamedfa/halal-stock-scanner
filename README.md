# رادار الأسهم الشرعية ومحرك إشارات ثاندر (EGX 33 Shariah & US Halal)

مشروع بايثون متكامل يعمل تلقائياً عبر [GitHub Actions](https://docs.github.com/actions) لفحص أسهم [مؤشر الشريعة بالبورصة المصرية EGX 33 Shariah](https://www.egx.com.eg/en/currentindexconstituntes.aspx?type=22&nav=22) والأسهم الأمريكية الشرعية المدرجة في [صندوق SPUS المعتمد وفق معايير AAOIFI](https://www.halalterminal.com/etf/spus)، وإرسال إشارات الشراء الفوري وجني الأرباح (Long / Spot Only) إلى تليجرام لتنفيذها يدوياً على [منصة ثاندر (Thndr)](https://thndr.app/).

## محتويات الحزمة
- `scanner.py`: الكود الرئيسي لسحب المؤشرات الفنية عبر مكتبة [`tradingview-ta`](https://pypi.org/project/tradingview-ta/) وسحب الأخبار التلقائي من خلاصات Google News RSS وتحليلها بواسطة **Gemini API** ثم إرسال بطاقة الأمر إلى تليجرام.
- `requirements.txt`: قائمة المكتبات المطلوبة للتشغيل.
- `.github/workflows/stock_scanner.yml`: ملف الجدولة السحابية وفق [توثيق جدولة GitHub Actions](https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions) مع دعم توقيت القاهرة `Africa/Cairo`.

## خطوات التشغيل السريع على GitHub
1. استخرج محتويات الملف المضغوط وارفعها إلى مستودع جديد (Public Repository) على حسابك في GitHub.
2. أنشئ بوت تليجرام عبر `@BotFather` وفق [دليل تليجرام الرسمي](https://core.telegram.org/bots/tutorial) واحصل على `TG_BOT_TOKEN` و`TG_CHAT_ID` كما في [شرح استخراج معرف المحادثة](https://gist.github.com/nafiesl/4ad622f344cd1dc3bb1ecbe468ff9f8a).
3. ادخل إلى `Settings -> Secrets and variables -> Actions` في مستودعك وفق [شرح أسرار GitHub Actions](https://docs.github.com/actions/security-guides/using-secrets-in-github-actions) وأضف:
   - `GEMINI_API_KEY`
   - `TG_BOT_TOKEN`
   - `TG_CHAT_ID`
4. افتح تبويب `Actions` واضغط `Run workflow` لاختبار وصول أول تقرير إشارات إلى موبايلك.
