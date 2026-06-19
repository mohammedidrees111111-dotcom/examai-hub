import re
import os
from typing import Optional

_FITZ = None
_PDFPLUMBER = None

try:
    import fitz as _FITZ
except ImportError:
    pass

try:
    import pdfplumber as _PDFPLUMBER
except ImportError:
    pass

_RE_ARABIC = re.compile(r'[\u0600-\u06FF]')

ARABIC_WORD_DICT = frozenset({
    "في","من","على","الى","عن","هذا","هذه","هو","هي","هم","هن","كان","كل","بعض","بين",
    "مع","بعد","قبل","خلال","حول","عند","ليس","لم","لن","لا","ما","ذلك","تلك","الذي",
    "التي","هناك","هنا","حتى","ايضا","فقط","جدا","اخر","اخرى","اي","قد","سوف","يمكن",
    "يجب","يكون","تكون","كما","او","ثم","بل","لكن","ولكن","غير","الى","الي","ان",
    "انها","انه","فان","فقد","لقد","وقد","اصبح","ظل","بقي","صار","قال","كانت","كانوا",
    "الله","رسول","نبي","قران","اسلام","مسلم","مسلمون","عربي","عربية","عرب","لغة",
    "كتاب","كتب","مدرسة","مدارس","جامعة","جامعات","طالب","طلاب","معلم","معلمون",
    "درس","دروس","علم","علوم","تعليم","تعلم","دراسة","مذاكرة","امتحان","اختبار",
    "سؤال","اسئلة","جواب","اجوبة","اجابة","صحيح","خطا","صح","غلط","نتيجة","نتائج",
    "نجاح","رسوب","ممتاز","جيد","ضعيف","مقبول","درجة","درجات","علامة","علامات",
    "فصل","فصول","باب","ابواب","وحدة","وحدات","تدريب","تدريبات","تمرين","تمارين",
    "مسالة","مسائل","حل","حلول","شرح","تفسير","تحليل","نص","نصوص","قراءة","كتابة",
    "استماع","تحدث","محادثة","حوار","مناقشة","قواعد","نحو","صرف","بلاغة","ادب",
    "شعر","نثر","قصة","رواية","مسرحية","مقال","مقالة","بحث","ابحاث","موضوع","مواضيع",
    "فكرة","افكار","راي","اراء","معنى","معان","كلمة","كلمات","جملة","جمل","فقرة",
    "فقرات","نقطة","نقاط","تعريف","تعاريف","مفهوم","مفاهيم","مصطلح","مصطلحات",
    "قانون","قوانين","قاعدة","قواعد","نظرية","نظريات","مبدا","مبادئ","اساس","اسس",
    "اصل","اصول","سبب","اسباب","نتيجة","نتائج","هدف","اهداف","غاية","غايات","وسيلة",
    "وسائل","طريقة","طرق","اسلوب","اساليب","منهج","مناهج","خطة","خطط","برنامج","برامج",
    "اول","ثاني","ثالث","رابع","خامس","سادس","سابع","ثامن","تاسع","عاشر",
    "واحد","اثنان","ثلاثة","اربعة","خمسة","ستة","سبعة","ثمانية","تسعة","عشرة",
    "كبير","صغير","طويل","قصير","جديد","قديم","حديث","معاصر","سهل","صعب",
    "سريع","بطيء","قوي","ضعيف","كثير","قليل","هام","مهم","اساسي","رئيسي",
    "فرعي","ثانوي","عام","خاص","داخلي","خارجي","محلي","عالمي","دولي","وطني",
    "سياسي","اقتصادي","اجتماعي","ثقافي","ديني","علمي","ادبي","فني","رياضي",
    "تاريخ","جغرافيا","فلسفة","منطق","رياضيات","فيزياء","كيمياء","احياء",
    "حاسوب","كمبيوتر","انترنت","تقنية","تكنولوجيا","برمجة","تصميم","هندسة",
    "طب","صيدلة","تمريض","قانون","محاماة","تجارة","اقتصاد","ادارة","محاسبة",
    "الم","امل","حب","كره","فرح","حزن","غضب","خوف","قلق","سعادة","شجاعة",
    "صبر","صدق","كذب","امانة","خيانة","عدل","ظلم","حرية","عبودية","سلام","حرب",
    "يوم","ليلة","اسبوع","شهر","سنة","عام","وقت","زمن","ساعة","دقيقة","ثانية",
    "صباح","مساء","ليل","نهار","امس","اليوم","غدا","ماض","حاضر","مستقبل",
    "شمس","قمر","نجم","سماء","ارض","بحر","نهر","جبل","سهل","صحراء","غابة",
    "ماء","هواء","نار","تراب","شجر","نبات","زهرة","ثمرة","حيوان","انسان",
    "رجل","امراة","طفل","شاب","عجوز","اب","ام","ابن","ابنة","اخ","اخت",
    "بيت","دار","منزل","غرفة","مطبخ","حمام","مكتب","سرير","كرسي","طاولة",
    "باب","شباك","سقف","جدار","طابق","سلم","حديقة","شارع","طريق","مدينة",
    "قرية","بلد","دولة","عاصمة","مطار","ميناء","محطة","مستشفى","مطعم","فندق",
    "اكل","طعام","شراب","خبز","لحم","دجاج","سمك","ارز","سكر","ملح",
    "فاكهة","خضار","تفاح","برتقال","موز","عنب","تمر","حليب","جبن","بيض",
    "لبس","ثوب","قميص","بنطال","حذاء","قبعة","معطف","جاكيت","قماش","صوف",
    "قطن","حرير","ذهب","فضة","حديد","نحاس","خشب","زجاج","ورق","بلاستيك",
    "عين","اذن","انف","فم","لسان","يد","رجل","راس","قلب","دم","عظم","جلد",
    "قول","فعل","عمل","صنع","كتب","قرا","درس","فهم","حفظ","نسي","تذكر",
    "جاء","ذهب","رجع","دخل","خرج","جلس","وقف","مشى","جري","اكل","شرب","نام",
    "ذكاء","اصطناعي","فرع","فروع","علوم","حاسوب","يهدف","تطوير","انظمة","قادرة",
    "محاكاة","بشري","يشمل","مجال","تعلم","الي","عميق","شبكات","عصبية","معالجة",
    "طبيعية","تمكن","فهم","بشرية","توليدها","رؤية","حاسوبية","تسمح","الات","صور",
    "فيديوهات","روبوتات","ذكية","تنفيذ","مهام","فيزيائية","مستقل","اخلاقيات",
    "تهتم","ضمان","استخدام","تقنيات","مسؤول","عادل","معزز","اسلوب","يتعلم","وكيل",
    "تفاعل","بيئة","حصول","مكافات","معلومات","بيانات","تحويل","معرفة","خبرة",
    "تطبيق","تطبيقات","نظام","نظم","اداة","ادوات","خدمة","خدمات","منتج","منتجات",
    "شركة","شركات","مؤسسة","مؤسسات","منظمة","منظمات","حكومة","حكومات","وزارة",
    "وزارات","قطاع","قطاعات","صناعة","صناعات","سوق","اسواق","استثمار","استثمارات",
    "تنمية","تطوير","تحديث","تحسين","تغيير","تبديل","تحول","انتقال","نمو","تقدم",
    "ازدهار","رخاء","فقر","بطالة","تضخم","ركود","انتعاش","تعافي","ازمة","ازمات",
    "مشكلة","مشاكل","تحدي","تحديات","فرصة","فرص","خطر","مخاطر","تهديد","تهديدات",
    "قوة","قوى","نفوذ","سلطة","سلطات","حكم","حكام","شعب","شعوب","امة","امم",
    "مجتمع","مجتمعات","اسرة","اسر","فرد","افراد","جماعة","جماعات","قبيلة","قبائل",
    "ثقافة","ثقافات","حضارة","حضارات","تراث","تراث","هوية","هويات","انتماء","ولاء",
    "قيم","قيمة","مبادئ","اخلاق","سلوك","سلوكيات","عادة","عادات","تقليد","تقاليد",
    "عرف","اعراف","قانون","تشريع","تشريعات","دستور","دساتير","لائحة","لوائح",
    "نص","مادة","بند","فقرة","ملحق","مرفق","توقيع","مصادقة","تصديق","اقرار",
    "موافقة","رفض","اعتراض","استئناف","طعن","نقض","ابطال","الغاء","تعليق","تجميد",
    "تنشيط","تفعيل","تعطيل","ايقاف","استمرار","دوام","بقاء","فناء","زوال","اندثار",
    "ظهور","بروز","انتشار","توسع","امتداد","انحسار","تراجع","انكماش","تقلص","اضمحلال",
    "زيادة","نقصان","ارتفاع","انخفاض","صعود","هبوط","تذبذب","استقرار","ثبات","تغير",
    "حياة","موت","ميلاد","وفاة","صحة","مرض","علاج","دواء","وقاية","مناعة",
    "تغذية","رياضة","لياقة","نشاط","خمول","راحة","تعب","ارهاق","اجهاد","استرخاء",
    "يقظة","نوم","حلم","واقع","خيال","وهم","حقيقة","صدق","كذب","زيف",
    "جمال","قبح","نور","ظلام","بياض","سواد","لون","الوان","شكل","اشكال",
    "حجم","احجام","وزن","اوزان","طول","عرض","ارتفاع","عمق","مساحة","حجم",
    "سرعة","بطء","قوة","ضعف","شدة","لين","صلابة","مرونة","قسوة","رقة",
    "صوت","ضوضاء","هدوء","سكون","حركة","جمود","حرارة","برودة","رطوبة","جفاف",
    "فكر","تفكير","عقل","ذهن","ذاكرة","نسيان","وعي","ادراك","شعور","احساس",
    "انفعال","عاطفة","مشاعر","وجدان","ضمير","نفس","روح","جسد","جسم","بدن",
    "شخصية","طبع","مزاج","خلق","سجية","غريزة","فطرة","طبيعة","بيئة","وراثة",
    "تربية","تنشئة","تعليم","تدريب","تاهيل","اعداد","تحضير","تجهيز","تكوين","صقل",
    "موهبة","قدرة","مهارة","كفاءة","جدارة","اتقان","احتراف","تمكن","براعة","حذق",
    "الفاتحة","البقرة","النساء","المائدة","الانعام","الاعراف","الانفال","التوبة",
    "يونس","هود","يوسف","الرعد","ابراهيم","الحجر","النحل","الاسراء","الكهف",
    "مريم","طه","الانبياء","الحج","المؤمنون","النور","الفرقان","الشعراء","النمل",
    "القصص","العنكبوت","الروم","لقمان","السجدة","الاحزاب","سبا","فاطر","يس",
    "الصافات","ص","الزمر","غافر","فصلت","الشورى","الزخرف","الدخان","الجاثية",
    "الاحقاف","محمد","الفتح","الحجرات","ق","الذاريات","الطور","النجم","القمر",
    "الرحمن","الواقعة","الحديد","المجادلة","الحشر","الممتحنة","الصف","الجمعة",
    "المنافقون","التغابن","الطلاق","التحريم","الملك","القلم","الحاقة","المعارج",
    "نوح","الجن","المزمل","المدثر","القيامة","الانسان","المرسلات","النبأ",
    "النازعات","عبس","التكوير","الانفطار","المطففين","الانشقاق","البروج","الطارق",
    "الاعلى","الغاشية","الفجر","البلد","الشمس","الليل","الضحى","الشرح","التين",
    "العلق","القدر","البينة","الزلزلة","العاديات","القارعة","التكاثر","العصر",
    "الهمزة","الفيل","قريش","الماعون","الكوثر","الكافرون","النصر","المسد","الاخلاص",
    "الفلق","الناس","فعل","ماض","مضارع","امر","مرفوع","منصوب","مجرور","مجزوم",
    "مبني","معرب","اسم","فاعل","مفعول","مبتدا","خبر","نعت","حال","تمييز",
    "مضاف","مضاف","اليه","جار","مجرور","ظرف","زمان","مكان","كان","ان","كاد",
    "حرف","جر","نصب","جزم","رفع","توكيد","نداء","تعجب","استفهام","شرط",
    "نهي","نفي","عطف","استثناء","توكيد","بدل","بيان","بدلية","مفعول","مطلق",
    "مفعول","اجله","مفعول","معه","مفعول","فيه","نائب","فاعل","اسم","تفضيل",
    "عدد","معدود","تمييز","ذات","نسبة","صفة","مشبهة","صيغة","مبالغة","تصغير",
    "منسوب","مقصور","منقوص","ممدود","صحيح","معتل","مثال","اجوف","ناقص",
    "لفيف","مقرون","مفروق","مهموز","سالم","جامد","مشتق","مجرد","مزيد",
    "ثلاثي","رباعي","خماسي","سداسي","لازم","متعد","معلوم","مجهول",
})


def analyze_arabic_fonts(file_path: str) -> dict:
    if not _FITZ:
        return {"has_arabic": False, "embedded_fonts": 0, "risky": False}
    try:
        doc = _FITZ.open(file_path)
        has_arabic = False
        embedded = 0
        custom_cmap = 0
        for i in range(min(20, len(doc))):
            page = doc[i]
            blocks = page.get_text("dict").get("blocks", [])
            for b in blocks:
                if b.get("type") == 0:
                    for line in b.get("lines", []):
                        for span in line.get("spans", []):
                            font = span.get("font", "")
                            text = span.get("text", "")
                            if _RE_ARABIC.search(text):
                                has_arabic = True
                            if font and "embedded" in font.lower():
                                embedded += 1
                            if font and ("custom" in font.lower() or "uni" in font.lower()):
                                custom_cmap += 1
        doc.close()
        return {
            "has_arabic": has_arabic,
            "embedded_fonts": embedded,
            "custom_cmap_hints": custom_cmap,
            "risky": has_arabic and embedded > 0,
            "needs_ocr_fallback": has_arabic and embedded > 5,
        }
    except Exception:
        return {"has_arabic": False, "embedded_fonts": 0, "risky": False}


def extract_arabic_multistrategy(file_path: str, font_analysis: dict) -> dict:
    results = []
    methods_tried = []

    # Strategy 1: PyMuPDF sort=True (default)
    text1 = _extract_fitz_strategy(file_path, sort=True)
    q1 = _score_arabic_quality(text1)
    results.append(("pymupdf_sort", text1, q1))
    methods_tried.append("pymupdf_sort")

    # Strategy 2: PyMuPDF sort=False (raw order)
    text2 = _extract_fitz_strategy(file_path, sort=False)
    q2 = _score_arabic_quality(text2)
    results.append(("pymupdf_raw", text2, q2))
    methods_tried.append("pymupdf_raw")

    # Strategy 3: PyMuPDF blocks mode
    text3 = _extract_fitz_blocks(file_path)
    q3 = _score_arabic_quality(text3)
    results.append(("pymupdf_blocks", text3, q3))
    methods_tried.append("pymupdf_blocks")

    # Strategy 4: pdfplumber
    text4 = _extract_pdfplumber_text(file_path)
    q4 = _score_arabic_quality(text4)
    results.append(("pdfplumber", text4, q4))
    methods_tried.append("pdfplumber")

    best_method, best_text, best_quality = max(results, key=lambda x: x[2])

    return {
        "best_method": best_method,
        "text": best_text,
        "quality_score": best_quality,
        "methods_tried": methods_tried,
        "all_scores": {m: q for m, _, q in results},
    }


def _extract_fitz_strategy(file_path: str, sort: bool) -> str:
    if not _FITZ:
        return ""
    try:
        doc = _FITZ.open(file_path)
        pages = []
        for page in doc:
            text = page.get_text("text", sort=sort)
            if text:
                pages.append(text)
        doc.close()
        return "\n".join(pages)
    except Exception:
        return ""


def _extract_fitz_blocks(file_path: str) -> str:
    if not _FITZ:
        return ""
    try:
        doc = _FITZ.open(file_path)
        pages = []
        for page in doc:
            blocks = page.get_text("blocks")
            page_lines = []
            for b in blocks:
                if len(b) >= 5 and b[6] == 0:
                    text = b[4].strip() if len(b) > 4 else ""
                    if text:
                        page_lines.append(text)
            pages.append("\n".join(page_lines))
        doc.close()
        return "\n".join(pages)
    except Exception:
        return ""


def _extract_pdfplumber_text(file_path: str) -> str:
    if not _PDFPLUMBER:
        return ""
    try:
        with _PDFPLUMBER.open(file_path) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
        return "\n".join(pages)
    except Exception:
        return ""


def _score_arabic_quality(text: str) -> int:
    if not text or len(text) < 50:
        return 0

    words = re.findall(r'[\u0600-\u06FF]{3,}', text)
    total_arabic_words = len(words)
    if total_arabic_words == 0:
        return 0

    real_words = 0
    for w in words:
        variants = _normalize_arabic_word(w)
        if any(v in ARABIC_WORD_DICT for v in variants):
            real_words += 1
    extra_checks = 0

    weird_patterns = re.findall(r'[^\u0600-\u06FF\s\.\,\!\?\:\;\-\(\)\[\]\{\}\d\n\r]', text)
    noise_ratio = len(weird_patterns) / max(len(text), 1)

    if noise_ratio < 0.02:
        extra_checks += 15
    if total_arabic_words > 100:
        extra_checks += 10
    if real_words > 5:
        extra_checks += 10

    dict_ratio = real_words / max(total_arabic_words, 1)
    base_score = dict_ratio * 65 + extra_checks
    return min(100, int(base_score))


def _normalize_arabic_word(word: str) -> list[str]:
    variants = [word]
    if word.startswith("وال"):
        variants.append(word[3:])
        variants.append(word[1:])
    elif word.startswith("فال"):
        variants.append(word[3:])
        variants.append(word[1:])
    elif word.startswith("كال"):
        variants.append(word[3:])
        variants.append(word[1:])
    elif word.startswith("بال"):
        variants.append(word[3:])
        variants.append(word[1:])
    elif word.startswith("لل"):
        variants.append(word[2:])
        variants.append(word[1:])
    elif word.startswith("ال"):
        variants.append(word[2:])
    if word.startswith("و"):
        variants.append(word[1:])
    if word.startswith("ف"):
        variants.append(word[1:])
    if word.startswith("ب"):
        variants.append(word[1:])
    if word.startswith("ك"):
        variants.append(word[1:])
    if word.startswith("ل"):
        variants.append(word[1:])
    return variants


def validate_arabic_text(text: str) -> dict:
    if not text or len(text) < 50:
        return {"valid": False, "score": 0, "arabic_words": 0, "real_words": 0, "corruption_detected": False}

    raw_words = re.findall(r'[\u0600-\u06FF]{3,}', text)
    total = len(raw_words)
    if total == 0:
        return {"valid": False, "score": 0, "arabic_words": 0, "real_words": 0, "corruption_detected": False}

    real = 0
    for w in raw_words:
        variants = _normalize_arabic_word(w)
        if any(v in ARABIC_WORD_DICT for v in variants):
            real += 1
    ratio = real / max(total, 1)
    weird = len(re.findall(r'[^\u0600-\u06FF\s\.\,\!\?\:\;\-\(\)\[\]\{\}\d\n\r\u0660-\u0669]', text[:5000]))
    noise = weird / max(len(text[:5000]), 1)

    corrupted = noise > 0.03 or (ratio < 0.25 and total > 3)
    valid = (ratio > 0.30 and not corrupted) or (total > 50 and noise < 0.01 and ratio > 0.20)

    return {
        "valid": valid,
        "score": int(ratio * 100),
        "arabic_words": total,
        "real_words": real,
        "dictionary_ratio": round(ratio, 2),
        "noise_ratio": round(noise, 4),
        "corruption_detected": corrupted,
        "recommendation": "ok" if valid else ("ocr_recommended" if ratio < 0.3 else "review_needed"),
    }
