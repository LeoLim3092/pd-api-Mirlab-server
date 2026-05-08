import datetime
import json

from .models import PatientQuestionaireRecord, Results


QUESTION_BANK = {
    1: {
        "text": "請問您的年齡：",
        "options": ["50-54", "55-59", "60-64", "65-69", "70-74", "75-79", ">=80"],
    },
    2: {"text": "(1)\t您的性別：", "options": ["男性", "女性"]},
    3: {
        "text": "(2)\t過去是否曾接觸殺蟲劑(Regular Pesticide Exposure)(例如：>=100次非職業性接觸)： ",
        "options": ["是", "否", "不知道或是無法取得資訊"],
    },
    4: {
        "text": "(3)\t職業或是居住環境是否會接觸到化學溶劑(Occupational Solvent Exposure)：",
        "options": ["是", "否", "不知道或是無法取得資訊"],
    },
    5: {
        "text": "(4)\t是否長期攝取含咖啡因飲料(Consume Caffeinated Beverage)：",
        "options": [
            "是 (每周大於3杯咖啡或是6杯紅茶)",
            "否 (每周小於3杯咖啡或是6杯紅茶)",
            "不知道或是無法取得資訊",
        ],
    },
    6: {
        "text": "(5)\t是否抽菸(Smoking)：",
        "options": [
            "從未 (Never)",
            "已戒菸 (Former)",
            "仍在抽菸（Current）",
            "不知道或是無法取得資訊 (Not Available)",
        ],
    },
    7: {
        "text": "(6)\t家族一等親(父母或是兄弟姊妹)是否有罹患巴金森症的患者：",
        "options": ["是", "否", "不知道或是無法取得資訊"],
    },
    8: {
        "text": "a.\tGBA基因變異 (Anheim 2012, Neurology)：",
        "options": ["是", "否", "不知道或是無法取得資訊"],
    },
    9: {
        "text": "b.\tLRRK2 (p.G2019S)基因變異(Lee 2017, Mov Disord)：",
        "options": ["是", "否", "不知道或是無法取得資訊"],
    },
    10: {
        "text": "(7-2) 多基因風險分數(Polygenetic Risk Score)：",
        "options": [
            "高風險分數(例如: 分數在大型世代追蹤族群中的最前四分之一)",
            "低風險分數(例如: 分數在大型世代追蹤族群中的最後四分之一)",
            "不知道或是無法取得資訊",
        ],
    },
    11: {
        "text": "(8)\t穿顱超音波檢查顯示黑質有高回聲訊號(Documented Substantia Nigra Hyperechogenicity on Transcranial Ultrasound)(例如：訊號強度大於90個百分比的參考樣本的單側或雙側黑質高回聲訊號)：",
        "options": ["是", "否", "不知道或是無法取得資訊"],
    },
    12: {
        "text": "(9)\t是否具有第二型糖尿病：",
        "options": ["是", "否", "不知道或是無法取得資訊"],
    },
    13: {
        "text": "(10)\t是否活動力不足(例如：每週進行能使呼吸及心跳速率上升/流汗的活動次數小於1小時)：",
        "options": ["是", "否", "不知道或是無法取得資訊"],
    },
    14: {
        "text": "(11)\t如果您是男性，血液中尿酸濃度是否偏低：",
        "options": ["是", "否", "不知道或是無法取得資訊"],
    },
    15: {
        "text": "A-1.1 您是否有睡眠多項生理檢查證實的快速動眼期睡眠動作障礙?(睡覺時會對夢境內容大喊大叫，甚至拳打腳踢)：",
        "options": ["是", "否", "不知道或是無法取得資訊"],
    },
    16: {
        "text": "A-1.2 您的快速動眼期睡眠動作障礙 (睡覺時會對夢境內容大喊大叫，甚至拳打腳踢)是否可以排除其他的可能?\n(其他鑑別診斷、藥物誘發/猝睡症相關動作症狀需被排除)：",
        "options": ["是", "否"],
    },
    17: {
        "text": "快速動眼期睡眠動作障礙篩檢結果為：",
        "options": ["陽性。無進一步檢驗確認", "陰性。無進一步檢驗確認", "不知道或是無法取得資訊"],
    },
    18: {
        "text": "A-2 日間嗜睡(可能的藥物誘發嗜睡或是猝睡症相關症狀需被排除)：",
        "options": ["是", "否", "不知道或是無法取得資訊"],
    },
    19: {
        "text": "A-3 您的嗅覺功能是否下降或是喪失? (例如：量化嗅覺測驗，如：Sniffin’ Stick, UPSIT或B-SIT，總分低於年紀及性別調整後之閾值)：",
        "options": ["是", "否", "不知道或是無法取得資訊"],
    },
    20: {
        "text": "A-4 您是否有便秘情況? (便秘症狀至少需要每週一次的吃軟便藥治療，或自然排便頻率低於兩天一次)：",
        "options": ["是", "否", "不知道或是無法取得資訊"],
    },
    21: {
        "text": "A-5 您是否有泌尿功能失調症狀? (排尿不順或是夜間頻尿)：",
        "options": ["是", "否", "不知道或是無法取得資訊"],
    },
    22: {
        "text": "A-6 若您是男性，是否有嚴重勃起障礙(Severe Erectile Dysfunction)：",
        "options": ["是", "否", "不知道或是無法取得資訊", "女性病患"],
    },
    23: {
        "text": "A-7 是否有姿態性低血壓(Orthostatic Hypotension)：",
        "options": ["是", "否"],
    },
    24: {
        "text": "姿態性低血壓(Orthostatic Hypotension)結果：",
        "options": [
            "姿態性低血壓，且經專家全面性評估後無其他可能原因",
            "有姿態性低血壓紀錄，但未經進一步檢查評估",
            "經專家全面性評估後無姿態性低血壓",
            "無姿態性低血壓紀錄，且無進一步檢查評估",
            "不知道或是無法取得資訊",
        ],
    },
    25: {
        "text": "A-8 是否有憂鬱症狀?(有/無合併焦慮症狀) (臨床診斷或是憂鬱量表/問卷達中等以上嚴重程度)：",
        "options": ["是", "否", "不知道或是無法取得資訊"],
    },
    26: {
        "text": "A-9 您是否有認知功能降低? (例如：被診斷輕度認知障礙)：",
        "options": ["是", "否", "不知道或是無法取得資訊"],
    },
    27: {
        "text": "B-1 巴金森氏病量表(UPDRS)第三部分總分大於6分 (需排除動作誘發顫抖及其他潛在干擾因子，例如：關節炎)：",
        "options": ["是", "否", "不知道或是無法取得資訊"],
    },
    28: {
        "text": "B-2 量化動作測驗呈現異常結果 (Abnormal Quantitative Motor Testing) (異常結果應依據不同測試的閾值，低於其年紀調整後常模的1個標準差。選用的量化動作測驗應可清楚呈現巴金森氏病患者的異常，且相較於控制組有80%以上的專一性。若是選用多個量化動作測驗，個案應有超過一半的測驗結果呈現異常。不確定或於臨界值的結果皆不應納入計算)：",
        "options": ["是", "否", "不知道或是無法取得資訊"],
    },
    29: {
        "text": "C-1 多巴胺攝影影像結果呈現明顯異常 (TRODAT 核醫影像) (例如：小於65%的正常結果或是低於平均兩個標準差)：",
        "options": ["是", "否", "不知道或是無法取得資訊"],
    },
}

BASE_EXPORT_FIELDS = [
    "patient_id",
    "app_id",
    "username",
    "questionnaire_time",
    "riskMarker",
    "PLR",
    "TELR",
    "PostProb",
    "PPPD",
    "result_upload_time",
    "gait_result",
    "voice_result",
    "hand_result",
    "multimodal_results",
]


def get_export_fieldnames(extra_columns=None):
    extra_columns = extra_columns or []
    question_columns = [QUESTION_BANK[key]["text"] for key in sorted(QUESTION_BANK)]
    return BASE_EXPORT_FIELDS + question_columns + list(extra_columns)


def _coerce_response_list(response_value):
    if response_value is None:
        return []
    if isinstance(response_value, list):
        return response_value
    if isinstance(response_value, str):
        try:
            parsed = json.loads(response_value)
        except Exception:
            return []
        return parsed if isinstance(parsed, list) else []
    return []


def _normalize_question_id(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_answer_index(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _answer_text(question_id, answer_index):
    question = QUESTION_BANK.get(question_id)
    if question is None or answer_index is None:
        return None
    options = question.get("options", [])
    if 1 <= answer_index <= len(options):
        return options[answer_index - 1]
    return None


def _parse_datetime_value(value):
    if not value:
        return None
    if isinstance(value, datetime.datetime):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d_%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y%m%d_%H%M%S", "%Y%m%d"):
        try:
            return datetime.datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _is_within_date_range(value, from_date=None, to_date=None):
    dt = _parse_datetime_value(value)
    if dt is None:
        return False
    current_date = dt.date()
    if from_date and current_date < from_date:
        return False
    if to_date and current_date > to_date:
        return False
    return True


def _latest_results_by_patient(from_date=None, to_date=None):
    latest_results = {}
    queryset = Results.objects.select_related("patientId").order_by("patientId_id", "-upload_time")
    for result in queryset:
        if not _is_within_date_range(result.upload_time, from_date, to_date):
            continue
        latest_results.setdefault(result.patientId_id, result)
    return latest_results


def _latest_questionnaires_by_patient(from_date=None, to_date=None):
    latest_questionnaires = {}
    queryset = (
        PatientQuestionaireRecord.objects
        .select_related("patientId")
        .order_by("patientId_id", "-time")
    )
    for record in queryset:
        if not _is_within_date_range(record.time, from_date, to_date):
            continue
        latest_questionnaires.setdefault(record.patientId_id, record)
    return latest_questionnaires


def build_results_questionnaire_export_rows(from_date=None, to_date=None):
    latest_results = _latest_results_by_patient(from_date=from_date, to_date=to_date)
    latest_questionnaires = _latest_questionnaires_by_patient(from_date=from_date, to_date=to_date)
    rows = []
    extra_columns = []
    extra_seen = set()

    patient_ids = sorted(set(latest_results) | set(latest_questionnaires))
    for patient_id in patient_ids:
        latest_result = latest_results.get(patient_id)
        record = latest_questionnaires.get(patient_id)
        patient = None
        if record is not None:
            patient = record.patientId
        elif latest_result is not None:
            patient = latest_result.patientId
        if patient is None:
            continue

        row = {field: "" for field in get_export_fieldnames()}
        row.update({
            "patient_id": patient.patientId,
            "app_id": patient.name,
            "username": patient.user_name,
            "questionnaire_time": record.time if record else "",
            "riskMarker": record.riskMarker if record else "",
            "PLR": record.PLR if record else "",
            "TELR": record.TELR if record else "",
            "PostProb": record.PostProb if record else "",
            "PPPD": record.PPPD if record else "",
            "result_upload_time": latest_result.upload_time if latest_result else "",
            "gait_result": latest_result.gait_result if latest_result else "",
            "voice_result": latest_result.voice_result if latest_result else "",
            "hand_result": latest_result.hand_result if latest_result else "",
            "multimodal_results": latest_result.multimodal_results if latest_result else "",
        })

        for item in _coerce_response_list(record.response if record else None):
            question_id = _normalize_question_id(item.get("question"))
            answer_index = _normalize_answer_index(item.get("response"))
            question = QUESTION_BANK.get(question_id)
            if question is None:
                if question_id is None:
                    continue
                column_name = f"Q{question_id}"
                if column_name not in extra_seen:
                    extra_seen.add(column_name)
                    extra_columns.append(column_name)
            else:
                column_name = question["text"]
            answer_text = _answer_text(question_id, answer_index)
            row[column_name] = answer_text if answer_text is not None else (answer_index or "")

        rows.append(row)

    return rows, get_export_fieldnames(extra_columns)
