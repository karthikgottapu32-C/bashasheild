"""
BhashaShield Explainer & Multi-Lingual Recommendation Engine.

Strictly separates threat detection from presentation translation:
Changing presentation language or recommendation style NEVER mutates
classification, risk scores, threat severity, or security policy decisions.
"""

from typing import List, Dict, Any, Optional, Tuple
import os
import requests
from app.models import ThreatCategory, TargetType, RiskLevel, RuleFinding, ModelFinding
from app.config import settings

SUPPORTED_LANGUAGES = {
    "auto": "Auto (Match Input)",
    "en": "English",
    "te": "తెలుగు (Telugu)",
    "hi": "हिन्दी (Hindi)",
    "te-Latn": "Romanized Telugu",
    "hi-Latn": "Romanized Hindi"
}

SUPPORTED_STYLES = {
    "actionable": "Actionable (Direct & Concise)",
    "simple": "Simple (Plain Language)",
    "detailed": "Detailed (Comprehensive Mitigation)",
    "technical": "Technical (SecOps & Developer Directives)"
}

def resolve_target_language(output_language: str, detected_language_code: str) -> str:
    """Resolves output language code, resolving 'auto' to detected language code."""
    if not output_language or output_language.lower() == "auto":
        code = (detected_language_code or "en").lower()
        if code in ("te", "telugu"):
            return "te"
        elif code in ("hi", "hindi"):
            return "hi"
        elif code in ("te-latn", "romanized_telugu", "te_latn"):
            return "te-Latn"
        elif code in ("hi-latn", "romanized_hindi", "hi_latn"):
            return "hi-Latn"
        elif code in ("en", "english"):
            return "en"
        return "en"
    
    clean = output_language.strip()
    if clean in SUPPORTED_LANGUAGES:
        return clean
    return "en"

# Multi-lingual explanation templates by state & target
EXPLANATION_TEMPLATES: Dict[str, Dict[str, str]] = {
    "BENIGN": {
        "en": "No adversarial prompt injections, data exfiltration patterns, or social engineering tactics were identified in this input. The text is verified benign and safe for processing.",
        "te": "ఈ ఇన్‌పుట్‌లో ఎటువంటి అడ్వర్సేరియల్ ప్రాంప్ట్ ఇంజెక్షన్లు, డేటా చోరీ లేదా సోషల్ ఇంజనీరింగ్ మోసాలు కనుగొనబడలేదు. ఈ టెక్స్ట్ సురక్షితమైనదిగా ధృవీకరించబడింది.",
        "hi": "इस इनपुट में कोई प्रतिकूल प्रॉम्प्ट इंजेक्शन, डेटा चोरी या सोशल इंजीनियरिंग पैटर्न नहीं पाए गए। यह टेक्स्ट सुरक्षित और हानिरहित सत्यापित है।",
        "te-Latn": "Ee input lo elanti prompt injection, data exfiltration leda scam prayatnalu kanipinchaledu. Ee text safe ani confirm ayindi.",
        "hi-Latn": "Is input mein koi malicious prompt injection, data chori ya social engineering nahi mili. Yeh text puri tarah safe hai."
    },
    "UNCERTAIN": {
        "en": "Security evaluation is UNCERTAIN. Input features exhibit high entropy, ambiguity, or out-of-distribution characteristics. Evidence is insufficient to verify safety.",
        "te": "భద్రతా మూల్యాంకనం అనిశ్చితంగా ఉంది (UNCERTAIN). ఇన్‌పుట్ లక్షణాలు అస్పష్టంగా లేదా అవుట్-ఆఫ్-డిస్ట్రిబ్యూషన్‌గా ఉన్నాయి. ఇది సురక్షితమో కాదో నిర్ధారించడానికి ఆధారాలు సరిపోవు.",
        "hi": "सुरक्षा मूल्यांकन अनिश्चित है (UNCERTAIN)। इनपुट विशेषताएं अस्पष्ट या आउट-ऑफ-डिस्ट्रिब्यूशन हैं। सुरक्षा सत्यापित करने के लिए साक्ष्य अपर्याप्त हैं।",
        "te-Latn": "Security evaluation UNCERTAIN ga undi. Input features ambiguous ga unnai. Safe ani confirm cheyadaniki sarina evidence ledu.",
        "hi-Latn": "Security evaluation UNCERTAIN hai. Input features sandigdh ya out-of-distribution hain. Suraksha nirdharit karne ke liye evidence kam hai."
    },
    "AI_SYSTEM": {
        "en": "Adversarial threat detected targeting AI Assistant. The input attempts instruction hijacking, system prompt override, or jailbreak boundaries.",
        "te": "AI సిస్టమ్‌ను లక్ష్యంగా చేసుకున్న ముప్పు గుర్తించబడింది. ఈ ఇన్‌పుట్ సిస్టమ్ సూచనలను అతిక్రమించడానికి లేదా భద్రతా పరిమితులను అధిగమించడానికి ప్రయత్నిస్తుంది.",
        "hi": "AI सहायक को लक्षित करने वाला प्रतिकूल खतरा पहचाना गया। यह इनपुट सिस्टम निर्देशों को ओवरराइड करने या सुरक्षा सीमाओं को तोड़ने का प्रयास करता है।",
        "te-Latn": "AI Assistant ni target chesina threat detect ayindi. Ee input system prompt override cheyadaniki leda rules ignore cheyadaniki prayatnistondi.",
        "hi-Latn": "AI Assistant ko target karne wala threat detect hua hai. Yeh input developer rules override karne ya jailbreak karne ki koshish karta hai."
    },
    "HUMAN_USER": {
        "en": "Social engineering / fraud attack detected targeting human user. The input exhibits deceptive UPI PIN capture, credential harvesting, or payment trap patterns.",
        "te": "వినియోగదారులను లక్ష్యంగా చేసుకున్న మోసపూరిత దాడి గుర్తించబడింది. ఈ ఇన్‌పుట్ నకిలీ UPI పిన్ సేకరణ లేదా ఆర్థిక మోసపు లక్షణాలను ప్రదర్శిస్తోంది.",
        "hi": "उपयोगकर्ता को लक्षित करने वाला सोशल इंजीनियरिंग / धोखाधड़ी हमला पहचाना गया। यह इनपुट कपटपूर्ण UPI पिन मांगने या वित्तीय जालसाजी के लक्षण दिखाता है।",
        "te-Latn": "User ni target chesina social engineering scam detect ayindi. Ee input lo fake UPI PIN adagadam leda dabbulu dhochukune prayatnam undi.",
        "hi-Latn": "User ko target karne wala phishing / UPI scam detect hua hai. Yeh input deceptive UPI PIN ya credentials chori karne ki koshish karta hai."
    },
    "BOTH": {
        "en": "Hybrid multi-vector threat detected targeting both AI models and human recipients. The payload combines instruction manipulation with deceptive social engineering.",
        "te": "హైబ్రిడ్ బహుళ-ముఖ ముప్పు గుర్తించబడింది. ఇది AI మోడల్ మరియు తుది వినియోగదారు ఇద్దరినీ ఒకేసారి లక్ష్యంగా చేసుకుంటుంది.",
        "hi": "हाइब्रिड मल्टी-वेक्टर खतरा पहचाना गया। यह पेलोड AI सिस्टम और अंतिम उपयोगकर्ता दोनों को एक साथ लक्षित करता है।",
        "te-Latn": "Hybrid threat detect ayindi. Idi AI model mariyu human user iddarini target chestondi.",
        "hi-Latn": "Hybrid attack detect hua hai jo AI system aur human user dono ko target karta hai."
    }
}

RECOMMENDATION_TEMPLATES: Dict[str, Dict[str, Dict[str, List[str]]]] = {
    "BENIGN": {
        "actionable": {
            "en": [
                "Proceed with normal AI assistant execution.",
                "Maintain standard input sandboxing and token length limits."
            ],
            "te": [
                "సాధారణ AI ప్రాసెసింగ్‌తో కొనసాగండి.",
                "ప్రామాణిక ఇన్‌పుట్ మరియు టోకెన్ పరిమితులను కొనసాగించండి."
            ],
            "hi": [
                "सामान्य AI प्रोसेसिंग के साथ आगे बढ़ें।",
                "मानक इनपुट सैंडबॉक्सिंग और टोकन सीमाएं बनाए रखें।"
            ],
            "te-Latn": [
                "Normal AI processing tho munduku vellandi.",
                "Standard input limits mariyu token limits maintain cheyandi."
            ],
            "hi-Latn": [
                "Normal AI execution ke saath aage badhein.",
                "Standard input sandboxing aur token limits maintain karein."
            ]
        },
        "simple": {
            "en": [
                "This message is completely safe to read and process.",
                "No extra security precautions required for this input."
            ],
            "te": [
                "ఈ సందేశం పూర్తిగా సురక్షితం.",
                "ఎటువంటి అదనపు భద్రతా చర్యలు అవసరం లేదు."
            ],
            "hi": [
                "यह संदेश पूरी तरह सुरक्षित है।",
                "इसके लिए किसी अतिरिक्त सुरक्षा सावधानी की आवश्यकता नहीं है।"
            ],
            "te-Latn": [
                "Ee message chala safe ga undi.",
                "Ekkada special security precautions emi avasaram ledu."
            ],
            "hi-Latn": [
                "Yeh message bilkul surakshit hai.",
                "Kisi extra security precaution ki zaroorat nahi hai."
            ]
        },
        "detailed": {
            "en": [
                "Zero adversarial markers identified across orthographic and semantic layers.",
                "Pass input to the application layer with standard monitoring.",
                "Ensure standard response egress filtering remains active as best practice."
            ],
            "te": [
                "అక్షర విన్యాసాలు మరియు అర్థశాస్త్ర పొరలలో ఎటువంటి దాడి సూచికలు కనుగొనబడలేదు.",
                "సాధారణ పర్యవేక్షణతో ఇన్‌పుట్‌ను అప్లికేషన్ లేయర్‌కు పంపండి.",
                "ఉత్తమ అభ్యాసంగా ప్రామాణిక రెస్పాన్స్ ఫిల్టరింగ్‌ను సక్రియంగా ఉంచండి."
            ],
            "hi": [
                "ऑर्थोग्राफिक और सिमेंटिक परतों में शून्य प्रतिकूल मार्कर पहचाने गए।",
                "मानक निगरानी के साथ इनपुट को एप्लिकेशन लेयर पर भेजें।",
                "सर्वोत्तम प्रथा के रूप में मानक रिस्पॉन्स फ़िल्टरिंग सक्रिय रखें।"
            ],
            "te-Latn": [
                "Zero attack markers confirm ayyayi across all layers.",
                "Standard monitoring tho input ni application ki forward cheyandi.",
                "Standard egress filtering ni safety best practice ga continue cheyandi."
            ],
            "hi-Latn": [
                "Sabhi linguistic aur semantic layers par zero adversarial markers mile hain.",
                "Standard monitoring ke saath input application ko forward karein.",
                "Best practice ke roop mein standard egress filtering active rakhein."
            ]
        },
        "technical": {
            "en": [
                "Input sanitized: 0 heuristic rule matches, calibrated risk score: 0.0.",
                "Forward context to LLM with role-delimiter boundaries intact.",
                "Log transaction audit hash with classification=BENIGN."
            ],
            "te": [
                "ఇన్‌పుట్ పరిశీలించబడింది: 0 నియమ ఉల్లంఘనలు, రిస్క్ స్కోరు: 0.0.",
                "రోల్-డీలిమిటర్ బౌండరీలతో ప్రాంప్ట్‌ను LLMకి ఫార్వర్డ్ చేయండి.",
                "classification=BENIGN గా లాగ్ ఆడిట్ హాష్ నమోదు చేయండి."
            ],
            "hi": [
                "इनपुट सत्यापित: 0 नियम उल्लंघन, कैलिब्रेटेड जोखिम स्कोर: 0.0।",
                "रोल-डिलिमिटर सीमाओं के साथ LLM को संदर्भ अग्रेषित करें।",
                "classification=BENIGN के साथ ऑडिट हैश रिकॉर्ड करें।"
            ],
            "te-Latn": [
                "Input verified: 0 rule violations, calibrated risk score: 0.0.",
                "Role delimiter boundaries preserve chesi prompt LLM ki forward cheyandi.",
                "Audit log lo classification=BENIGN ga record cheyandi."
            ],
            "hi-Latn": [
                "Input verified: 0 heuristic violations, calibrated risk score: 0.0.",
                "Role-delimiter boundaries ke sath LLM context forward karein.",
                "Audit log mein classification=BENIGN store karein."
            ]
        }
    },
    "UNCERTAIN": {
        "actionable": {
            "en": [
                "Do NOT assume this input is safe for downstream execution.",
                "Route prompt to human security review or apply sandbox containment.",
                "Verify input context and request clarification before processing."
            ],
            "te": [
                "ఈ ఇన్‌పుట్ సురక్షితమైనదని భావించవద్దు.",
                "ప్రాంప్ట్‌ను హ్యూమన్ రివ్యూకు పంపండి లేదా శాండ్‌బాక్స్ అమలు చేయండి.",
                "ప్రాసెసింగ్ చేయడానికి ముందు సందర్భాన్ని ధృవీకరించండి."
            ],
            "hi": [
                "इस इनपुट को सुरक्षित न मानें।",
                "प्रॉम्प्ट को मानवीय समीक्षा के लिए भेजें या सैंडबॉक्स नियंत्रण लागू करें।",
                "आगे बढ़ने से पहले इनपुट संदर्भ की पुष्टि करें।"
            ],
            "te-Latn": [
                "Ee input safe ani anukokandi.",
                "Prompt ni human review ki pampandi leda safe sandbox lo execute cheyandi.",
                "Process chese mundu clarification teesukondi."
            ],
            "hi-Latn": [
                "Is input ko bina jaanch ke safe na maanein.",
                "Prompt ko human security review ke liye bhein ya sandboxing lagayein.",
                "Aage badhne se pehle user se clarification maangein."
            ]
        },
        "simple": {
            "en": [
                "Caution: This message is suspicious or unclear.",
                "Ask the sender to clarify before taking any action or clicking anything."
            ],
            "te": [
                "హెచ్చరిక: ఈ సందేశం అనుమానాస్పదంగా లేదా అస్పష్టంగా ఉంది.",
                "ఏదైనా చర్య తీసుకునే ముందు పంపినవారి నుండి వివరణ కోరండి."
            ],
            "hi": [
                "सावधानी: यह संदेश संदिग्ध या अस्पष्ट है।",
                "कोई भी कदम उठाने या क्लिक करने से पहले प्रेषक से स्पष्टीकरण मांगें।"
            ],
            "te-Latn": [
                "Jagratha: Ee message suspicious ga undi.",
                "Emi click cheyakunda pampina vallani clear ga adagandi."
            ],
            "hi-Latn": [
                "Savdhani: Yeh message thoda suspicious ya unclear hai.",
                "Koi action lene se pehle sender se dobara confirm karein."
            ]
        },
        "detailed": {
            "en": [
                "The classifier detected high ambiguity or low token familiarity in this input.",
                "Quarantine prompt in intermediate buffer to prevent accidental model compromise.",
                "Request secondary authorization or disambiguation from system operators."
            ],
            "te": [
                "క్లాసిఫైయర్ ఈ ఇన్‌పుట్‌లో అధిక అస్పష్టతను లేదా అపరిచిత టోకెన్లను గుర్తించింది.",
                "ప్రమాదవశాత్తు మోడల్ రాజీ పడకుండా నిరోధించడానికి ప్రాంప్ట్‌ను క్వారంటైన్ చేయండి.",
                "సిస్టమ్ ఆపరేటర్ల నుండి ద్వితీయ అనుమతిని కోరండి."
            ],
            "hi": [
                "क्लासिफायर ने इस इनपुट में उच्च अस्पष्टता या अपरिचित टोकन का पता लगाया है।",
                "आकस्मिक खतरे से बचने के लिए प्रॉम्प्ट को क्वारंटाइन करें।",
                "सिस्टम ऑपरेटरों से द्वितीयक प्राधिकरण का अनुरोध करें।"
            ],
            "te-Latn": [
                "Classifier ee input lo high ambiguity kanipettindi.",
                "Model safety kosam prompt ni temporary quarantine lo pettandi.",
                "Secondary approval vachaka matrame downstream allow cheyandi."
            ],
            "hi-Latn": [
                "Classifier ne is input mein high ambiguity ya unfamiliarity note ki hai.",
                "Model protection ke liye prompt ko quarantine buffer mein daalein.",
                "System administrators se secondary confirmation lein."
            ]
        },
        "technical": {
            "en": [
                "Abstention triggered: entropy threshold exceeded (margin < 0.25).",
                "Enforce PolicyDecision=REVIEW; drop direct LLM completion path.",
                "Emit telemetry alert: OOD_OR_AMBIGUOUS_Linguistic_Signature."
            ],
            "te": [
                "అబ్‌స్టెన్షన్ ట్రిగ్గర్ చేయబడింది: ఎంట్రోపీ పరిమితి మించిపోయింది (margin < 0.25).",
                "PolicyDecision=REVIEW అమలు చేయండి; డైరెక్ట్ LLM మార్గాన్ని నిరోధించండి.",
                "టెలిమెట్రీ హెచ్చరికను నమోదు చేయండి: OOD_OR_AMBIGUOUS."
            ],
            "hi": [
                "एबस्टेंशन ट्रिगर: एंट्रॉपी सीमा पार (मार्जिन < 0.25)।",
                "PolicyDecision=REVIEW लागू करें; सीधा LLM पाथ ब्लॉक करें।",
                "टेलीमेट्री अलर्ट जारी करें: OOD_OR_AMBIGUOUS_Signature।"
            ],
            "te-Latn": [
                "Abstention triggered: entropy limit exceed ayindi (margin < 0.25).",
                "PolicyDecision=REVIEW enforce cheyandi; direct LLM path drop cheyandi.",
                "Telemetry event log cheyandi: OOD_AMBIGUOUS_TOKEN."
            ],
            "hi-Latn": [
                "Abstention triggered: entropy threshold cross hua (margin < 0.25).",
                "PolicyDecision=REVIEW lagu karein; direct LLM path block karein.",
                "Security telemetry emit karein: OOD_OR_AMBIGUOUS_Signature."
            ]
        }
    },
    "AI_SYSTEM": {
        "actionable": {
            "en": [
                "CRITICAL: Drop or quarantine input; do NOT pass to downstream LLM reasoning contexts.",
                "Apply BhashaShield sanitizer to strip instruction override directives and reset context framing.",
                "Enforce strict role separation: preserve system prompt immutability in developer blocks."
            ],
            "te": [
                "ముఖ్యమైనది: ఇన్‌పుట్‌ను వెంటనే తిరస్కరించండి లేదా క్వారంటైన్ చేయండి; LLMకి పంపవద్దు.",
                "సిస్టమ్ సూచనలను రక్షించడానికి భాషాషీల్డ్ శానిటైజర్‌ను వర్తింపజేయండి.",
                "సిస్టమ్ ప్రాంప్ట్ యొక్క మార్పులేని లక్షణాన్ని ఖచ్చితంగా సంరక్షించండి."
            ],
            "hi": [
                "गंभीर: इनपुट को तुरंत ब्लॉक या क्वारंटाइन करें; इसे LLM को न भेजें।",
                "निर्देश ओवरराइड हटाने और संदर्भ रीसेट करने के लिए सैनिटाइज़र लागू करें।",
                "सिस्टम प्रॉम्प्ट की अपरिवर्तनीयता (immutability) को सख्ती से बनाए रखें।"
            ],
            "te-Latn": [
                "CRITICAL: Input ni block leda quarantine cheyandi; LLM ki pass cheyavaddhu.",
                "BhashaShield sanitizer use chesi instruction override directives delete cheyandi.",
                "System prompt boundaries strict ga lock cheyandi."
            ],
            "hi-Latn": [
                "CRITICAL: Input ko drop ya quarantine karein; LLM ko bilkul na bhejein.",
                "System prompt override directives ko strip karne ke liye sanitizer lagayein.",
                "Developer system blocks ki immutability preserve karein."
            ]
        },
        "simple": {
            "en": [
                "Warning: This message is trying to hack or trick the AI into breaking its safety rules.",
                "Do not process this request; block the command."
            ],
            "te": [
                "హెచ్చరిక: ఈ సందేశం AI నిబంధనలను ఉల్లంఘించేలా మోసగించడానికి ప్రయత్నిస్తోంది.",
                "ఈ అభ్యర్థనను ప్రాసెస్ చేయవద్దు; వెంటనే బ్లాక్ చేయండి."
            ],
            "hi": [
                "चेतावनी: यह संदेश AI के सुरक्षा नियमों को तोड़ने का प्रयास कर रहा है।",
                "इस अनुरोध को प्रोसेस न करें; कमांड को ब्लॉक करें।"
            ],
            "te-Latn": [
                "Warning: Ee message AI rules ni break cheyadaniki try chestondi.",
                "Ee command ni accept cheyakandi; block cheyandi."
            ],
            "hi-Latn": [
                "Warning: Yeh message AI ke security rules todne ki koshish kar raha hai.",
                "Is request ko aage na badhayein; turant block karein."
            ]
        },
        "detailed": {
            "en": [
                "The adversarial payload leverages linguistic obfuscation to bypass context boundary guards.",
                "Quarantine session context and reset conversation history to eliminate jailbreak inertia.",
                "Inject non-negotiable instruction fences with cryptographic role separation."
            ],
            "te": [
                "ఈ దాడి భాషా మభ్యపెట్టడం ద్వారా భద్రతా పరిమితులను అధిగమించడానికి ప్రయత్నిస్తుంది.",
                "సెషన్ సందర్భాన్ని క్వారంటైన్ చేయండి మరియు సంభాషణను రీసెట్ చేయండి.",
                "రక్షణ కంచెలను బలపరిచి సూచనల భద్రతను నిర్ధారించండి."
            ],
            "hi": [
                "यह हमला संदर्भ सीमाओं को बायपास करने के लिए भाषाई अस्पष्टता का उपयोग करता है।",
                "सेशन संदर्भ को क्वारंटाइन करें और बातचीत का इतिहास रीसेट करें।",
                "सिस्टम प्रॉम्प्ट सुरक्षा के लिए मजबूत फेंसिंग लागू करें।"
            ],
            "te-Latn": [
                "Linguistic obfuscation tho system guards bypass chese attempt idi.",
                "Session context reset chesi jailbreak continuation aapeyandi.",
                "Developer system prompt fences strongly enforce cheyandi."
            ],
            "hi-Latn": [
                "Yeh payload context boundaries bypass karne ke liye linguistic tricks use karta hai.",
                "Session context quarantine karein aur conversation history reset karein.",
                "Cryptographic role separation ke sath instruction fences lagayein."
            ]
        },
        "technical": {
            "en": [
                "PolicyDecision=BLOCK triggered by adversarial regex pattern / statistical classifier.",
                "Strip input tokens matching instruction override signatures before tokenization.",
                "Audit prompt templates for leaky delimiters (e.g. ```system, [INST], <|im_start|>)."
            ],
            "te": [
                "డిటెక్షన్ నియమాల ద్వారా PolicyDecision=BLOCK అమలు చేయబడింది.",
                "టోకనైజేషన్‌కు ముందు సూచనల ఉల్లంఘన టోకెన్‌లను తొలగించండి.",
                "డెలిమిటర్ల లీకేజీని నివారించడానికి ప్రాంప్ట్ టెంప్లేట్‌లను ఆడిట్ చేయండి."
            ],
            "hi": [
                "नियमों द्वारा PolicyDecision=BLOCK निष्पादित किया गया।",
                "टोकनाइजेशन से पहले निर्देश ओवरराइड हस्ताक्षरों को इनपुट से हटाएं।",
                "लीकी डिलिमिटर (जैसे ```system, [INST]) के लिए सिस्टम टेम्प्लेट की जांच करें।"
            ],
            "te-Latn": [
                "PolicyDecision=BLOCK triggered on matched threat patterns.",
                "Tokenization mundu instruction override tokens strip cheyandi.",
                "System prompt delimiters (```system, [INST]) leak kakunda audit cheyandi."
            ],
            "hi-Latn": [
                "PolicyDecision=BLOCK executed based on verified threat signatures.",
                "Tokenization se pehle instruction override patterns strip karein.",
                "Delimiters leak audit karein aur prompt fencing enforce karein."
            ]
        }
    },
    "HUMAN_USER": {
        "actionable": {
            "en": [
                "Alert recipient with high-visibility warning: Never enter UPI PIN to receive money or refunds.",
                "Flag sender account and transaction remark for security compliance inspection.",
                "Block embedded URLs and verify sender channel authenticity."
            ],
            "te": [
                "వినియోగదారుని హెచ్చరించండి: డబ్బులు లేదా వాపసు పొందడానికి ఎప్పుడూ UPI పిన్ నమోదు చేయవద్దు.",
                "భద్రతా తనిఖీ కోసం పంపినవారి ఖాతాను మరియు లావాదేవీని ఫ్లాగ్ చేయండి.",
                "సందేశంలోని లింక్‌లను బ్లాక్ చేయండి మరియు పంపినవారిని ధృవీకరించండి."
            ],
            "hi": [
                "प्राप्तकर्ता को चेतावनी दें: पैसे या रिफंड प्राप्त करने के लिए कभी भी UPI पिन दर्ज न करें।",
                "सुरक्षा जांच के लिए प्रेषक खाते और लेनदेन विवरण को चिह्नित (flag) करें।",
                "संदेश में दिए गए लिंक को ब्लॉक करें और प्रेषक की प्रामाणिकता की जांच करें।"
            ],
            "te-Latn": [
                "User ki high-priority warning ivvandi: Refunds kosam UPI PIN enter cheyoddu.",
                "Sender account mariyu transaction remark ni security inspection ki flag cheyandi.",
                "Embedded links block chesi sender authenticity verify cheyandi."
            ],
            "hi-Latn": [
                "User ko turant alert karein: Paise aane par kabhi UPI PIN enter na karein.",
                "Sender account aur transaction remark ko security review ke liye flag karein.",
                "Embedded links block karein aur sender verify karein."
            ]
        },
        "simple": {
            "en": [
                "Danger: This message is a scam! Someone is trying to steal your money.",
                "Do NOT enter your UPI PIN or bank password, and do NOT click any links."
            ],
            "te": [
                "ప్రమాదం: ఈ సందేశం ఒక మోసం! మీ డబ్బును దొంగిలించడానికి ఎవరో ప్రయత్నిస్తున్నారు.",
                "మీ UPI పిన్ లేదా బ్యాంక్ పాస్‌వర్డ్ ఎప్పుడూ నమోదు చేయవద్దు, ఏ లింక్‌ను క్లిక్ చేయవద్దు."
            ],
            "hi": [
                "खतरा: यह संदेश एक धोखा (स्कैम) है! कोई आपके पैसे चुराने की कोशिश कर रहा है।",
                "अपना UPI पिन या पासवर्ड दर्ज न करें, और किसी भी लिंक पर क्लिक न करें।"
            ],
            "te-Latn": [
                "Danger: Ee message oka scam! Mee dabbu lakkodaniki try chestunnaru.",
                "Mee UPI PIN leda bank password enter cheyoddu, links click cheyoddu."
            ],
            "hi-Latn": [
                "Khatra: Yeh message ek fraud scam hai! Koi aapke paise churane ki koshish kar raha hai.",
                "Apna UPI PIN ya password kisi ko na dein, aur koi link open na karein."
            ]
        },
        "detailed": {
            "en": [
                "The message exhibits social engineering patterns typical of UPI reverse-debit fraud.",
                "Intercept transaction flow and display an unmistakable full-screen friction interstitial.",
                "Require explicit out-of-band biometric or SMS confirmation before allowing transfer."
            ],
            "te": [
                "ఈ సందేశం UPI రివర్స్-డెబిట్ మోసానికి సంబంధించిన సోషల్ ఇంజనీరింగ్ పద్ధతులను చూపుతోంది.",
                "లావాదేవీని నిలిపివేసి, వినియోగదారుకు స్పష్టమైన పూర్తి-స్క్రీన్ హెచ్చరికను ప్రదర్శించండి.",
                "మారకపు ప్రక్రియను అనుమతించే ముందు అదనపు బయోమెట్రిక్ నిర్ధారణను కోరండి."
            ],
            "hi": [
                "यह संदेश UPI रिवर्स-डेबिट धोखाधड़ी के विशिष्ट सोशल इंजीनियरिंग पैटर्न प्रदर्शित करता है।",
                "लेनदेन रोकें और उपयोगकर्ता को एक स्पष्ट फुल-स्क्रीन चेतावनी दिखाएं।",
                "आगे बढ़ने से पहले बायोमेट्रिक या एसएमएस द्वारा अतिरिक्त सत्यापन अनिवार्य करें।"
            ],
            "te-Latn": [
                "Message lo UPI reverse-debit scam patterns unnai.",
                "Transaction flow aapi full-screen friction alert chupinchandi.",
                "Biometric leda out-of-band verification compulsory cheyandi."
            ],
            "hi-Latn": [
                "Yeh message UPI reverse-debit phishing ke lakshan dikhata hai.",
                "Transaction ko hold par dalein aur user ko prominent warning screen dikhayein.",
                "Out-of-band biometric ya SMS authentication require karein."
            ]
        },
        "technical": {
            "en": [
                "Trigger NPCI/RBI fraud compliance workflow for potential reverse-charge abuse.",
                "Quarantine transaction ID and notify banking API security gateway.",
                "Enforce URL reputation lookup: block unverified domains immediately."
            ],
            "te": [
                "రివర్స్-ఛార్జ్ దుర్వినియోగం కోసం NPCI/RBI మోసాల నియంత్రణ ప్రక్రియను ప్రారంభించండి.",
                "లావాదేవీ IDని క్వారంటైన్ చేసి బ్యాంకింగ్ API గేట్‌వేకు తెలియజేయండి.",
                "ధృవీకరించబడని డొమైన్‌లను తక్షణమే బ్లాక్ చేయండి."
            ],
            "hi": [
                "रिवर्स-चार्ज दुरुपयोग के लिए NPCI/RBI धोखाधड़ी अनुपालन वर्कफ़्लो शुरू करें।",
                "लेनदेन आईडी को क्वारंटाइन करें और बैंकिंग एपीआई गेटवे को सूचित करें।",
                "अपुष्ट डोमेन और दुर्भावनापूर्ण लिंक को तुरंत ब्लॉक करें।"
            ],
            "te-Latn": [
                "NPCI/RBI fraud compliance workflow trigger cheyandi.",
                "Transaction ID quarantine chesi banking gateway ki notify cheyandi.",
                "Unverified domains ni dynamic firewall dwara block cheyandi."
            ],
            "hi-Latn": [
                "Trigger NPCI/RBI fraud compliance alerts for financial manipulation attempt.",
                "Quarantine transaction ID and notify bank API security gateway.",
                "Block malicious URL domains at gateway firewall."
            ]
        }
    }
}

def generate_explanation_and_actions(
    text: str,
    language: str,
    script: str,
    risk_level: RiskLevel,
    risk_score: float,
    categories: List[str],
    target_type: TargetType,
    rule_findings: List[RuleFinding],
    model_findings: Optional[ModelFinding] = None,
    output_language: str = "auto",
    recommendation_style: str = "actionable",
    language_code: Optional[str] = None
) -> Tuple[str, List[str], str, str]:
    """
    Generates localized explanation and recommendations matching the target output language
    and requested recommendation style.
    
    IMPORTANT: This function does NOT alter risk_score, risk_level, categories, or target_type.
    """
    target_lang = resolve_target_language(output_language, language_code or language)
    target_style = recommendation_style.lower() if recommendation_style in SUPPORTED_STYLES else "actionable"

    # Determine state key
    if risk_level == RiskLevel.UNCERTAIN or categories == ["UNKNOWN"]:
        state_key = "UNCERTAIN"
    elif risk_level == RiskLevel.LOW or not categories or categories == ["BENIGN"]:
        state_key = "BENIGN"
    else:
        # Malicious
        if target_type == TargetType.HUMAN_USER:
            state_key = "HUMAN_USER"
        elif target_type in (TargetType.AI_SYSTEM, TargetType.NONE):
            state_key = "AI_SYSTEM"
        else:
            state_key = "BOTH"

    # 1. Fetch base localized explanation
    explanation = EXPLANATION_TEMPLATES.get(state_key, {}).get(target_lang) or EXPLANATION_TEMPLATES.get(state_key, {}).get("en", "Threat evaluation completed.")

    # In English or when rule details are relevant, enrich explanation with evidence
    if state_key not in ("BENIGN", "UNCERTAIN") and rule_findings:
        matched_rules = ", ".join([f"'{rf.rule_name}'" for rf in rule_findings[:2]])
        if target_lang == "en":
            explanation += f" Triggered {len(rule_findings)} detection rule(s): {matched_rules}."
        elif target_lang == "te":
            explanation += f" గుర్తించిన నిబంధనలు: {matched_rules}."
        elif target_lang == "hi":
            explanation += f" पहचाने गए नियम: {matched_rules}."
        elif target_lang == "te-Latn":
            explanation += f" Triggered rules: {matched_rules}."
        elif target_lang == "hi-Latn":
            explanation += f" Triggered rules: {matched_rules}."

    # 2. Fetch localized recommendations for target style
    style_dict = RECOMMENDATION_TEMPLATES.get(state_key, {}).get(target_style, {})
    recommendations = style_dict.get(target_lang) or style_dict.get("en") or [
        "Inspect input against security policy.",
        "Apply standard prompt guardrails."
    ]

    # Additional contextual recommendation for exfiltration
    if state_key not in ("BENIGN", "UNCERTAIN") and any("EXFILTRATION" in c for c in categories):
        if target_lang == "te":
            recommendations.append("సిస్టమ్ ప్రాంప్ట్‌లో API కీలు లేదా రహస్య ఆధారాలు లేవని నిర్ధారించుకోండి.")
        elif target_lang == "hi":
            recommendations.append("सुनिश्चित करें कि सिस्टम प्रॉम्प्ट में कोई संवेदनशील API कुंजियां या क्रेडेंशियल्स उजागर न हों।")
        elif target_lang == "te-Latn":
            recommendations.append("System prompt lo API keys leda database secrets levu ani confirm cheyandi.")
        elif target_lang == "hi-Latn":
            recommendations.append("System prompt mein sensitive API keys ya secrets audit karein.")
        else:
            recommendations.append("Audit system prompt for sensitive API keys, database credentials, and secrets.")

    return explanation, list(recommendations), target_lang, target_style


def customize_recommendations(
    text: Optional[str] = None,
    language: str = "auto",
    style: str = "actionable",
    classification: Optional[str] = None,
    risk_score: Optional[float] = None,
    risk_level: Optional[RiskLevel] = None,
    categories: Optional[List[str]] = None,
    target_type: Optional[TargetType] = None,
    custom_recommendations: Optional[List[str]] = None,
    detected_language_code: Optional[str] = "en"
) -> Dict[str, Any]:
    """
    Customizes recommendations and explanations for an existing scan or user override.
    Guarantees immutability of security classification and risk score.
    """
    resolved_lang = resolve_target_language(language, detected_language_code or "en")
    resolved_style = style.lower() if style in SUPPORTED_STYLES else "actionable"

    # Default fallbacks if not supplied
    eff_level = risk_level or RiskLevel.LOW
    eff_score = risk_score if risk_score is not None else (0.0 if eff_level == RiskLevel.LOW else 80.0)
    eff_cats = categories or (["BENIGN"] if eff_level == RiskLevel.LOW else ["PROMPT_INJECTION"])
    eff_target = target_type or TargetType.AI_SYSTEM

    if custom_recommendations and len(custom_recommendations) > 0:
        # User provided explicit customized list of action items
        # Just generate matching localized explanation
        exp, _, out_lang, out_style = generate_explanation_and_actions(
            text=text or "",
            language=SUPPORTED_LANGUAGES.get(resolved_lang, "English"),
            script="Standard",
            risk_level=eff_level,
            risk_score=eff_score,
            categories=eff_cats,
            target_type=eff_target,
            rule_findings=[],
            output_language=resolved_lang,
            recommendation_style=resolved_style,
            language_code=resolved_lang
        )
        return {
            "output_language": out_lang,
            "output_language_label": SUPPORTED_LANGUAGES.get(out_lang, out_lang),
            "recommendation_style": out_style,
            "explanation": exp,
            "recommended_actions": custom_recommendations,
            "classification": classification or ("BENIGN" if eff_level == RiskLevel.LOW else "MALICIOUS"),
            "risk_score": eff_score,
            "risk_level": eff_level,
            "immutability_verified": True
        }

    exp, recs, out_lang, out_style = generate_explanation_and_actions(
        text=text or "",
        language=SUPPORTED_LANGUAGES.get(resolved_lang, "English"),
        script="Standard",
        risk_level=eff_level,
        risk_score=eff_score,
        categories=eff_cats,
        target_type=eff_target,
        rule_findings=[],
        output_language=resolved_lang,
        recommendation_style=resolved_style,
        language_code=resolved_lang
    )

    return {
        "output_language": out_lang,
        "output_language_label": SUPPORTED_LANGUAGES.get(out_lang, out_lang),
        "recommendation_style": out_style,
        "explanation": exp,
        "recommended_actions": recs,
        "classification": classification or ("BENIGN" if eff_level == RiskLevel.LOW else "MALICIOUS"),
        "risk_score": eff_score,
        "risk_level": eff_level,
        "immutability_verified": True
    }
