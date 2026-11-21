import re
from typing import List, Dict, Any, Tuple
from app.models import ThreatCategory, TargetType, HighlightedSpan, RuleFinding
from app.core.normalizer import normalize_input

class RuleDefinition:
    def __init__(
        self,
        rule_id: str,
        name: str,
        category: ThreatCategory,
        target_type: TargetType,
        severity: str,
        weight: float,
        regex_patterns: List[str],
        description: str,
        language: str = "Multilingual"
    ):
        self.rule_id = rule_id
        self.name = name
        self.category = category
        self.target_type = target_type
        self.severity = severity
        self.weight = weight
        self.description = description
        self.language = language
        # Compile patterns case-insensitively with Unicode and DOTALL support
        self.compiled_patterns = [
            re.compile(p, re.IGNORECASE | re.UNICODE | re.DOTALL) for p in regex_patterns
        ]

# Definitive catalog of multilingual rules covering Telugu, Hindi, Romanized, and English
RULES_CATALOG: List[RuleDefinition] = [
    # ==========================================
    # 1. TELUGU SCRIPT RULES
    # ==========================================
    RuleDefinition(
        rule_id="RULE_PI_TE_001",
        name="Telugu: Instruction Override / Ignore Previous",
        category=ThreatCategory.PROMPT_INJECTION,
        target_type=TargetType.AI_SYSTEM,
        severity="CRITICAL",
        weight=40.0,
        regex_patterns=[
            r"మునుపటి\s+(సూచనలను|ఆదేశాలను|నియమాలను)\s+(విస్మరించండి|మర్చిపోండి|పట్టించుకోవద్దు)",
            r"(పై|ముందు|గత)\s+(సూచనలను|ఆదేశాలను|నిర్దేశాలను|నియమాలను)\s+(రద్దు\s+చేయండి|విస్మరించు|వదిలేయండి|పట్టించుకోవద్దు)",
            r"పాత\s+(నిబంధనలను|ఆదేశాలను|సూచనలను)\s+(మర్చిపోండి|విడిచిపెట్టండి|రద్దు\s+చేయండి)",
            r"ఇప్పటినుండి\s+నేను\s+చెప్పినట్లు\s+మాత్రమే\s+చెయ్యండి"
        ],
        description="Attempts to instruct the AI assistant to disregard previous safety guidelines in Telugu script.",
        language="Telugu"
    ),
    RuleDefinition(
        rule_id="RULE_PI_TE_002",
        name="Telugu: Jailbreak / Mode Switch",
        category=ThreatCategory.JAILBREAK,
        target_type=TargetType.AI_SYSTEM,
        severity="CRITICAL",
        weight=45.0,
        regex_patterns=[
            r"(నీవు|మీరు|నువ్వు)\s+(ఇప్పుడు\s+)?(జైల్‌బ్రేక్|డెవలపర్|అన్‌రెస్ట్రిక్టెడ్)\s+మోడ్(్‌|లో|లోకి)?",
            r"(జైల్‌బ్రేక్|డెవలపర్|అన్‌రెస్ట్రిక్టెడ్)\s+మోడ్(్‌|లో|లోకి)?\s*(ఆన్|సక్రియం|మారండి|చేయండి|ఉన్నావు)",
            r"అన్ని\s+భద్రతా\s+(నియమాలను|పరిమితులను)\s+(బైపాస్|రద్దు)\s+చేయండి",
            r"ఎలాంటి\s+(ఫిల్టర్లు|నిబంధనలు|పరిమితులు)\s+లేకుండా"
        ],
        description="Commands an AI to bypass safety filters or activate unauthorized jailbreak mode in Telugu script.",
        language="Telugu"
    ),
    RuleDefinition(
        rule_id="RULE_EXFIL_TE_001",
        name="Telugu: System Prompt / Key Exfiltration",
        category=ThreatCategory.DATA_EXFILTRATION,
        target_type=TargetType.AI_SYSTEM,
        severity="HIGH",
        weight=35.0,
        regex_patterns=[
            r"(సిస్టమ్|రహస్య|అసలు|ప్రాథమిక|ప్రారంభ)\s*(ప్రాంప్ట్‌ను|నిర్దేశాలను|సూచనలను|ప్రాంప్ట్)(.*?)?(చూపించు|ప్రింట్\s*చేయండి|బయటపెట్టు|చెప్పు|ప్రింట్|చూపించండి|అనువదించి)",
            r"మీ\s*(అసలు\s+|ప్రాథమిక\s+)?(సిస్టమ్\s*ప్రాంప్ట్|రహస్య|API\s*కీ|సీక్రెట్\s*కీ|పాస్‌వర్డ్|టోకెన్|సూచనలను)(లను)?.*?(పంపండి|చూపండి|రాయండి|ప్రింట్|అనువదించి)",
            r"దాచిన\s+సూచనలను\s+బయటకు\s+చెప్పండి"
        ],
        description="Attempts to force the AI to leak internal system prompts, secret instructions, or credentials in Telugu script.",
        language="Telugu"
    ),
    RuleDefinition(
        rule_id="RULE_FIN_TE_001",
        name="Telugu: Financial PIN / UPI Fraud",
        category=ThreatCategory.FINANCIAL_MANIPULATION,
        target_type=TargetType.HUMAN_USER,
        severity="CRITICAL",
        weight=40.0,
        regex_patterns=[
            r"(యూపీఐ|UPI|ATM)\s*పిన్\s*(నమోదు|ఎంటర్|టైప్)\s*చేయండి",
            r"(డబ్బులు|రీఫండ్|లాటరీ|క్యాష్‌బ్యాక్|బహుమతి)\s*(రావడానికి|పొందడానికి|తీసుకోవడానికి)\s*(పిన్|PIN)\s*(కొట్టండి|చెప్పండి|నొక్కండి|ఎంటర్)",
            r"(కరెంట్|విద్యుత్|వాటర్|గ్యాస్)\s*బిల్లు.*?(నిలిపివేయబడుతుంది|కట్\s*చేయబడుతుంది|చెల్లించండి)",
            r"(లాటరీ|బంపర్\s*డ్రా|నగదు\s*బహుమతి|కారు\s*గెలుచుకున్నారు).*?(UPI|పిన్|చెల్లించండి|రుసుము)",
            r"(పాన్|KYC|ఆధార్|ఖాతా)\s*(నిలిపివేయబడింది|బ్లాక్|గడువు).*?(OTP|పిన్|అప్‌డేట్)",
            r"(పార్సిల్|కొరియర్|డెలివరీ|పోస్ట్)\s*.*?(ఆగింది|ఆగిపోయింది|చిరునామా|అడ్రస్|లోపం|ఫీజు).*?(యూపీఐ|UPI|చెల్లించండి|పే\s*చేయండి|రుసుము)",
            r"ఖాతా\s*(బ్లాక్|రద్దు)\s*కాకుండా\s*వెంటనే\s*చెల్లించండి"
        ],
        description="Deceptive financial instructions demanding UPI PIN for refunds or payments in Telugu script.",
        language="Telugu"
    ),

    # ==========================================
    # 2. HINDI SCRIPT RULES
    # ==========================================
    RuleDefinition(
        rule_id="RULE_PI_HI_001",
        name="Hindi: Instruction Override / Ignore Previous",
        category=ThreatCategory.PROMPT_INJECTION,
        target_type=TargetType.AI_SYSTEM,
        severity="CRITICAL",
        weight=40.0,
        regex_patterns=[
            r"पिछले\s+(सभी|सारे)?\s*(निर्देशों|आदेशों|नियमों)\s+को\s+(अनदेखा|नज़रअंदाज़|रद्द)\s+(करें|करो|कीजिए)",
            r"पहले\s+के\s+(सभी|सारे)?\s*(नियम|निर्देश|प्रॉम्प्ट)\s+भूल\s+जाओ",
            r"ऊपर\s+दिए\s+गए\s+(निर्देशों|आदेशों|नियमों)\s+(पर\s+ध्यान\s+मत\s+दो|को\s+रद्द\s+करके)",
            r"सिस्टम\s*ओवरराइड",
            r"अब\s+से\s+तुम\s+केवल\s+मेरी\s+बात\s+मानोगे"
        ],
        description="Direct instruction override targeting AI assistants using Devanagari Hindi script.",
        language="Hindi"
    ),
    RuleDefinition(
        rule_id="RULE_PI_HI_002",
        name="Hindi: Jailbreak / Unrestricted Persona",
        category=ThreatCategory.JAILBREAK,
        target_type=TargetType.AI_SYSTEM,
        severity="CRITICAL",
        weight=45.0,
        regex_patterns=[
            r"(तुम\s*अब|अब\s*तुम|आप\s*अब)?\s*(डेवलपर|जेलब्रेक|दान|DAN)\s+मोड\s+(सक्रिय|चालू|सक्षम|में\s*हो)",
            r"बिना\s+किसी\s+(प्रतिबंध|नैतिक|सुरक्षा|नियमों)",
            r"सभी\s+सुरक्षा\s+फिल्टर\s+हटा\s+(दें|दो|दीजिए)"
        ],
        description="Jailbreak command attempting to bypass AI safety filters using Hindi script.",
        language="Hindi"
    ),
    RuleDefinition(
        rule_id="RULE_EXFIL_HI_001",
        name="Hindi: Exfiltration of System Prompt & Credentials",
        category=ThreatCategory.DATA_EXFILTRATION,
        target_type=TargetType.AI_SYSTEM,
        severity="HIGH",
        weight=35.0,
        regex_patterns=[
            r"(अपना\s+)?(पूरा\s+)?(सिस्टम\s*प्रॉम्प्ट|गुप्त\s*निर्देश|मूल\s*प्रॉम्प्ट)(.*?)?(दिखाओ|दिखाइए|दिखाएं|प्रिंट\s*करो|लिखो)",
            r"अपनी\s*(API\s*की|सीक्रेट\s*कुंजी|पासवर्ड|कॉन्फ़िगरेशन)\s*(प्रकट|साझा|भेजो)\s*करो",
            r"शुरुआती\s+सिस्टम\s+संदेश\s+पूरा\s+का\s+पूरा\s+बताओ"
        ],
        description="Attempts to extract underlying system prompts or API credentials using Hindi script.",
        language="Hindi"
    ),
    RuleDefinition(
        rule_id="RULE_FIN_HI_001",
        name="Hindi: Financial / UPI Fraud",
        category=ThreatCategory.FINANCIAL_MANIPULATION,
        target_type=TargetType.HUMAN_USER,
        severity="CRITICAL",
        weight=40.0,
        regex_patterns=[
            r"(पैसे|रिफंड|पुरस्कार|लॉटरी|इनाम)\s*(पाने|प्राप्त\s*करने|लेने)\s*के\s*लिए\s*(अपना\s*)?(UPI|यूपीआई)\s*पिन\s*(दर्ज|डालें|दालो|लिखो)",
            r"(UPI|यूपीआई)\s*पिन\s*(दर्ज\s*करें|साझा\s*करें|डालें)",
            r"(बिजली|विद्युत|जल|गैस)\s*(काट\s*दी\s*जाएगी|बंद\s*कर\s*दिया\s*जाएगा|डिस्कनेक्ट|कट\s*जाएगी).*?(UPI|यूपीआई|भुगतान|भेजें)",
            r"(केबीसी|लॉटरी|इनाम|डिजिटल\s*अरेस्ट|वारंट).*?(UPI|यूपीआई|पिन|फीस|भेजें)",
            r"(पैन|केवाईसी|खाता|सिम)\s*(ब्लॉक|बंद|निलंबित).*?(ओटीपी|पिन|शुल्क|UPI)",
            r"आपका\s*खाता\s*(बंद|ब्लॉक)\s*होने\s*वाला\s*है,\s*तुरंत\s*पैसे\s*भेजें"
        ],
        description="Fraudulent instruction asking user to enter UPI PIN under false pretenses in Hindi script.",
        language="Hindi"
    ),

    # ==========================================
    # 3. ROMANIZED TELUGU RULES
    # ==========================================
    RuleDefinition(
        rule_id="RULE_PI_TE_LATN_001",
        name="Romanized Telugu: Instruction Override",
        category=ThreatCategory.PROMPT_INJECTION,
        target_type=TargetType.AI_SYSTEM,
        severity="CRITICAL",
        weight=40.0,
        regex_patterns=[
            r"\b(mundu|pichhi|paatha|last)\s+(ichina\s+)?(instructions|orders|nirdesalu|suchanalu|rules)(\s+anni)?\s+(marchipo|marchipondi|vadileyi|ignore\s*cheyyi|cancel\s*chey)\b",
            r"\b(pai|mundu)\s+(rules|guidelines|nirdesalu)\s+(pattinchukovaddu|pattinchukoku|cancel\s*chesi|lite\s*theesuko)\b",
            r"\bnaa\s+mata\s+vinu\s+mundu\s+(rules|nirdesalu)\s+vadilesi\b",
            r"\bippatinundi\s+nenu\s+cheppinatle\s+vinandi\b"
        ],
        description="Instruction override attack expressed in Romanized Telugu phonetics.",
        language="Romanized Telugu"
    ),
    RuleDefinition(
        rule_id="RULE_JB_TE_LATN_001",
        name="Romanized Telugu: Jailbreak / Persona Override",
        category=ThreatCategory.JAILBREAK,
        target_type=TargetType.AI_SYSTEM,
        severity="CRITICAL",
        weight=45.0,
        regex_patterns=[
            r"\bnuvvu\s+ippudu\s+(unrestricted\s+)?(jailbreak|dan|unrestricted|god)\s+mode\s*lo\s*unnav\b",
            r"\banni\s+(safety\s+)?(rules|restrictions|limits)\s+(theesei|teeseyi|bypass\s*cheyyi|cancel\s*cheyyi)\b",
            r"\bdeveloper\s+mode\s+(on\s*chey|activate\s*cheyyandi|enable\s*cheyyi)\b",
            r"\byemee\s+filters\s+lekunda\s+cheppu\b"
        ],
        description="Attempts to force the AI into jailbreak mode using Romanized Telugu.",
        language="Romanized Telugu"
    ),
    RuleDefinition(
        rule_id="RULE_EXFIL_TE_LATN_001",
        name="Romanized Telugu: System Prompt Exfiltration",
        category=ThreatCategory.DATA_EXFILTRATION,
        target_type=TargetType.AI_SYSTEM,
        severity="HIGH",
        weight=35.0,
        regex_patterns=[
            r"\b(system\s*prompt|secret\s*prompt|initial\s*prompt)\s+(motham|mottham|entire)?\s*(bayataku\s*cheppu|print\s*cheyyi|dikhinchu|chupinchu|ivvandi)\b",
            r"\bnee\s+(system\s*prompt|secret\s*prompt|secret\s*key|api\s*key|password|hidden\s*instructions)(.*?)(bayata\s*pettu|bayataku\s*cheppu|send\s*cheyyi|cheppu|chupinchu)\b",
            r"\bdeveloper\s+ichina\s+prompt\s+naku\s+chupinchu\b"
        ],
        description="Attempts to extract AI system prompts or credentials using Romanized Telugu.",
        language="Romanized Telugu"
    ),
    RuleDefinition(
        rule_id="RULE_FIN_TE_LATN_001",
        name="Romanized Telugu: Financial Fraud / UPI PIN Trap",
        category=ThreatCategory.FINANCIAL_MANIPULATION,
        target_type=TargetType.HUMAN_USER,
        severity="CRITICAL",
        weight=40.0,
        regex_patterns=[
            r"\b(upi|atm)\s*pin\s*(enter\s*cheyandi|kottandi|nokkandi|ivvandi|type\s*cheyyi|pampandi|share\s*cheyandi|cheppandi)\b",
            r"\b(dabbu|refund|cashback|lottery)\s*(ravataniki|kosam)\s*(pin|upi\s*pin)\s*(enter|kottandi|ivvandi)\b",
            r"\bventane\s+(ee\s+link\s+open\s+chesi|dabulu\s+pampi)\b",
            r"\b(electricity|current|power)\s+.*?\b(disconnect|cut\s*chestharu|aagakunda)\b.*?\b(upi|pay|pampandi|kattandi)\b",
            r"\b(?:electricity|current(?:\s*bill)?|power)\b.*?\b(?:disconnect|cut\s*(?:chestharu|avuthundi|avutundi)|aagakunda|kattaledu|pay\s*cheyaledu)\b.*?\b(?:upi|pay|pampandi|kattandi|cheyyandi)\b",
            r"\b(?:parcel|courier|delivery|package)\b.*?\b(?:wrong\s*address|aagindi|aagipoyindi|hold|customs|address\s*(?:verify|update))\b.*?\b(?:upi|pay|fee|charges|kattandi|cheyyandi)\b",
            r"\b(mee\s+)?(bank\s+)?(account|khata)\s+(block|freeze)\s+(avuthundi|ayyindi|avutundi)\b.*?\b(otp|atm\s*pin|pin|pan\s*card|upi)\b",
            r"\b(kyc\s*update|aadhaar\s*link)\s+cheyyakapothe\s+(account|service)\s+(block|aagipothundi)\b",
            r"\b(cbi|police|cyber\s*crime|narcotics|drug\s*parcel)\s+(notice|case)\b.*?\b(arrest|deposit|upi|transfer|dabulu|cheyandi)\b"
        ],
        description="Social engineering scam seeking UPI PIN for alleged refunds or prizes in Romanized Telugu.",
        language="Romanized Telugu"
    ),

    # ==========================================
    # 4. ROMANIZED HINDI RULES
    # ==========================================
    RuleDefinition(
        rule_id="RULE_PI_HI_LATN_001",
        name="Romanized Hindi: Instruction Override",
        category=ThreatCategory.PROMPT_INJECTION,
        target_type=TargetType.AI_SYSTEM,
        severity="CRITICAL",
        weight=40.0,
        regex_patterns=[
            r"\b(pichhle|pehle\s+ke|purane|security)\s+(saare|sabhi)?\s*(nirdesh|instructions|rules|aadesh|protocols)\s*(bhool\s*jao|ignore\s*karo|cancel\s*kardo|cancel\s*karke|chhod\s*do|radd\s*karke)\b",
            r"\buper\s+diye\s+gaye\s+rules\s+ko\s+nazarandaz\s+karo\b",
            r"\bab\s+se\s+tum\s+(sirf|keval)\s+meri\s+sunoge\b",
            r"\bradd\s+karke\s+.*?\b(leak\s*karo|batao|print\s*karo)\b",
            r"\bpehle\s+kya\s+bola\s+woh\s+sab\s+bhul\s+ja\b"
        ],
        description="Instruction override targeting AI assistants using Romanized Hindi phonetics.",
        language="Romanized Hindi"
    ),
    RuleDefinition(
        rule_id="RULE_JB_HI_LATN_001",
        name="Romanized Hindi: Jailbreak Persona",
        category=ThreatCategory.JAILBREAK,
        target_type=TargetType.AI_SYSTEM,
        severity="CRITICAL",
        weight=45.0,
        regex_patterns=[
            r"\bab\s+se\s+tum\s+ek\s+(unrestricted(\s+dan)?|jailbreak|dan|evil)\s+(assistant|bot|ai)\s+ho\b",
            r"\b(developer|jailbreak)\s+mode\s+(enable|chalu|on)\s+karo\b",
            r"\bsabhi\s+(safety|security)\s+(filters|protocols|rules)\s+(hata\s*do|disable\s*karo|bypass\s*karo)\b",
            r"\bbina\s+kisi\s+filter\s+ke\s+jawab\s+do\b"
        ],
        description="Jailbreak persona command in Romanized Hindi.",
        language="Romanized Hindi"
    ),
    RuleDefinition(
        rule_id="RULE_EXFIL_HI_LATN_001",
        name="Romanized Hindi: System Prompt Exfiltration",
        category=ThreatCategory.DATA_EXFILTRATION,
        target_type=TargetType.AI_SYSTEM,
        severity="HIGH",
        weight=35.0,
        regex_patterns=[
            r"\b(system\s*prompt|initial\s*prompt|khufiya\s*nirdesh)\s+(dikhao|batao|print\s*karo|likho)\b",
            r"\bapna\s+(secret\s*key|api\s*key|secret\s*prompt|system\s*prompt|password|api\s*credentials)(.*?)(bhejo|mujhe\s+do|print\s*karo|yahan\s+print\s*karo|batao)\b",
            r"\bdeveloper\s+ne\s+kya\s+instructions\s+diye\s+the\s+poora\s+batao\b"
        ],
        description="Prompt or credential extraction attack written in Romanized Hindi.",
        language="Romanized Hindi"
    ),
    RuleDefinition(
        rule_id="RULE_FIN_HI_LATN_001",
        name="Romanized Hindi: Financial / UPI Fraud",
        category=ThreatCategory.FINANCIAL_MANIPULATION,
        target_type=TargetType.HUMAN_USER,
        severity="CRITICAL",
        weight=40.0,
        regex_patterns=[
            r"\b(paise|refund|cashback|prize)\s*(pane|lene|transfer)\s*ke\s*liye\s*(apna\s*)?(upi\s*pin|pin)\s*(dalo|dalein|enter\s*karo|bhejo|submit\s*karein)\b",
            r"\b(upi\s*pin|mpin|pin)\s*(dalo|dalein|enter\s*karo|submit\s*karein|bhejo)\b",
            r"\bqr\s*code\s*(ko\s*)?scan\s*karke\s*.*?\b(upi\s*pin|mpin|pin|submit)\b",
            r"\bupi\s*pin\s*(daal\s*kar|enter\s*karke)\s*paise\s*receive\s*karein\b",
            r"\baccount\s*block\s*hone\s*se\s*bachane\s*ke\s*liye\s*turant\s*pay\s*karein\b",
            r"\b(bijli|light|electricity)\s+.*?\b(disconnect|cut\s*ho\s*jayeg[ai]|kaat\s*d[ie]|kaat\s*diya)\b.*?\b(upi|payment|send|bhejo|jama)\b",
            r"\b(?:parcel|courier)\s+(?:deliver\s*karane|lene)\s*ke\s*liye\s*.*?\b(?:upi|pay|bhejo|jama)\b",
            r"\b(bank\s+khata|account)\s+(freeze|block)\s+ho\s+gaya\b.*?\b(otp|mpin|pin|update)\b",
            r"\b(bank\s+khata|account)\s+(?:block|freeze|band)\s+(?:hone\s+se\s+bachane|ho\s+gaya|hoga|hone\s+par)\b.*?\b(otp|mpin|pin|card\s*number|debit|update|share)\b",
            r"\b(?:parcel|courier)(?:\s+delivery)?\s+(?:deliver\s*karane|lene|mangwane)\s*ke\s*liye\s*.*?\b(?:upi|pay|bhejo|jama|charge)\b",
            r"\b(kyc\s*update|pan\s*card\s*link)\s+nahi\s+kiya\s+toh\s+(account|sim)\s+band\b"
        ],
        description="Phishing and deceptive UPI PIN solicitation in Romanized Hindi.",
        language="Romanized Hindi"
    ),

    # ==========================================
    # 5. ENGLISH & UNIVERSAL CYBER THREAT RULES
    # ==========================================
    RuleDefinition(
        rule_id="RULE_PI_EN_001",
        name="English: Ignore Previous Instructions",
        category=ThreatCategory.PROMPT_INJECTION,
        target_type=TargetType.AI_SYSTEM,
        severity="CRITICAL",
        weight=40.0,
        regex_patterns=[
            r"\b(ignore|disregard|forget|override|neglect)\s+(all\s+)?(previous|prior|above|earlier|system)\s+(instructions|directives|prompts|rules|commands|guidelines)\b",
            r"\b(ignore|disregard|forget|override|neglect)\s+(?:all\s+)?(?:the\s+)?(?:previous|prior|above|earlier|system|established|safety|developer)?\s*(?:instructions|directives|prompts|rules|commands|guidelines|protocols|boundaries)\b",
            r"\bstop\s+following\s+your\s+(original|system)\s+prompt\b",
            r"\bdo\s+not\s+follow\s+any\s+(prior|previous)\s+safety\s+guidelines\b",
            r"\byou\s+must\s+now\s+act\s+exclusively\s+as\b"
        ],
        description="Classic direct prompt injection attempting to nullify the AI system's initial system instructions.",
        language="English"
    ),
    RuleDefinition(
        rule_id="RULE_PI_EN_002",
        name="English: Developer Mode / DAN Jailbreak",
        category=ThreatCategory.JAILBREAK,
        target_type=TargetType.AI_SYSTEM,
        severity="CRITICAL",
        weight=45.0,
        regex_patterns=[
            r"\b(you\s+are\s+now|act\s+as|simulate)\s+(an\s+unrestricted\s+ai\s+assistant|DAN|Jailbreak|Developer\s+Mode|Do\s+Anything\s+Now|Root\s+User|Uncensored\s+AI)\b",
            r"\bsimulate\s+an\s+(unrestricted|jailbroken|uncensored)\s+(ai|assistant|bot)\b",
            r"\bno\s+(moral|ethical)\s+(boundaries|restrictions|filters)\b",
            r"\benable\s+(developer\s+mode|unrestricted\s+mode|god\s+mode)\b",
            r"\bbypass\s+all\s+(ethical|content|safety)\s+(filters|policies|protocols|restrictions)\b",
            r"\bpretend\s+you\s+have\s+no\s+(rules|restrictions|guardrails)\b"
        ],
        description="Jailbreak attack trying to place the AI into an unaligned or persona-compromised state.",
        language="English"
    ),
    RuleDefinition(
        rule_id="RULE_EXFIL_EN_001",
        name="English: Exfiltration & System Leakage",
        category=ThreatCategory.DATA_EXFILTRATION,
        target_type=TargetType.AI_SYSTEM,
        severity="HIGH",
        weight=35.0,
        regex_patterns=[
            r"\b(print|output|display|reveal|leak|repeat|show|translate|quote)\s+(your\s+)?(complete\s+|entire\s+|full\s+|secret\s+|initial\s+|developer\s+|confidential\s+|core\s+|operating\s+)*(system\s*prompt|initial\s*prompt|system\s*instructions|secret\s*instructions|developer\s*instructions|confidential\s*instructions|operating\s*instructions)\b",
            r"\b(what\s+(were|are)\s+the\s+(exact\s+)?(words|instructions|system\s*prompt)|(exact\s+(text|words)|copy|verbatim\s+copy)\s+of\s+(the\s+)?(confidential|secret|hidden|developer|system)\s+(instructions|prompt))\b",
            r"\b(send|exfiltrate|transmit|post)\s+(the\s+|all\s+)?(conversation\s+history|chat\s+history|conversations|user\s+data|secrets|api\s+keys?)(.*?)to\s+https?://\S+\b",
            r"\boutput\s+the\s+above\s+text\s+as\s+a\s+base64\s+encoded\s+string\b"
        ],
        description="Instruction attempting to exfiltrate system secrets, internal prompts, or conversation history.",
        language="English"
    ),
    RuleDefinition(
        rule_id="RULE_PHISH_EN_001",
        name="English: Credential Harvesting & Phishing",
        category=ThreatCategory.PHISHING,
        target_type=TargetType.HUMAN_USER,
        severity="HIGH",
        weight=30.0,
        regex_patterns=[
            r"\b(verify|update|unlock)\s+your\s+(kyc|bank\s+account|pan\s+card|netbanking)\s+(immediately|urgently)\s+at\s+https?://\S+\b",
            r"\byour\s+(bank\s+)?account\s+(is|has\s+been)\s+(blocked|suspended|frozen)\b",
            r"\byour\s+account\s+will\s+be\s+suspended\s+within\s+\d+\s+hours\b",
            r"\bclick\s+here\s+to\s+(claim|claim\s+reward|verify\s+identity)\s*:\s*https?://\S+\b",
            r"\b(?:parcel|package|courier|shipment|delivery)\s+.*?\b(?:wrong\s+address|held|seized|customs|clearance|address\s+missing|incomplete\s+(?:house\s+)?address)\b.*?\b(?:pay|charge|click|confirm|fee|update)\b.*?(?:https?://\S+|upi|rs\.?\s*\d+)?\b",
            r"\b(?:india\s*post|fedex|blue\s*dart|dhl)\s+(?:courier|delivery|notice|alert)\b.*?\b(?:pay|charge|click|fee|upi)\b",
            r"\b(?:whatsapp\s*pink|free\s*recharge\s*app|hacked\s*apk)\b.*?\b(?:download\s*apk|click\s*link|http://|https://)\b",
            r"https?://[a-zA-Z0-9.-]+\.(?:top|xyz|click|work|vip|gq|cf|ml|tk|fit|download|site)(?:/\S*)?",
            r"\bshare\s+your\s+(otp|one\s+time\s+password|cvv)\s+to\s+(cancel|confirm)\b",
            r"\b(send|enter|share)\s+(your\s+)?(16-digit|debit\s*card|credit\s*card|card\s*number).*?(cvv|otp|pin)\b",
            r"\b(sim\s*card|mobile\s*number)\s+(will\s+be\s+)?(deactivated|blocked)\b.*?\b(pay|fee|upi|otp)\b",
            r"\b(digital\s*arrest|arrest\s*warrant|narcotics\s*notice).*?\b(upi|bail|fine|deposit)\b",
            r"\b(?:cbi|narcotics|police|customs|cyber\s*crime)\b.*?\b(?:drug|illegal|parcel|aadhaar|seized|warrant|arrest|bureau|notice)\b.*?\b(?:transfer|pay|fine|bail|avoid\s+arrest|deposit|clearance)\b"
        ],
        description="Phishing attack soliciting account credentials or OTP verification under urgency.",
        language="English"
    ),
    RuleDefinition(
        rule_id="RULE_FIN_EN_001",
        name="English: UPI / Financial Scam",
        category=ThreatCategory.FINANCIAL_MANIPULATION,
        target_type=TargetType.HUMAN_USER,
        severity="CRITICAL",
        weight=40.0,
        regex_patterns=[
            r"\benter\s+(your\s+)?(upi\s+pin|mpin|atm\s+pin)\s+to\s+(receive|claim|collect|refund|unblock|verify|transfer)\b",
            r"\benter\s+(?:your\s+)?(?:upi\s*pin|mpin|atm\s*pin)\b.*?\b(?:to\s+(?:receive|claim|collect|accept|refund|credit|unblock|verify|transfer))\b",
            r"\b(?:cashback|reward|refund|credited).*?\b(?:enter\s+(?:your\s+)?(?:upi\s*pin|mpin|pin)).*?\b(?:to\s+(?:claim|receive|accept|credit|collect))\b",
            r"\benter\s+(your\s+)?(upi\s+pin|mpin|atm\s+pin)\s+(immediately|now)\b",
            r"\breceive\s+rs\.?\s*\d+\s+by\s+entering\s+your\s+pin\b",
            r"\b(cashback|reward).*?\b(click\s+link|enter\s+mpin|enter\s+pin)\b.*?\b(wallet|transfer|receive)\b",
            r"\bupi\s+cashback\s+credited\s*:\s*enter\s+pin\s+now\b",
            r"\b(electricity|power|water|gas|sim\s*cards?|png|lpg|meter)\s+(?:(?:supply|connection|service)\s+)?(?:will\s+be\s+)?(?:disconnected|blocked|suspended|cut\s*off|deactivated)\b.*?\b(pay|upi|transfer|call|officer)\b",
            r"\b(?:meter|power|water|telecom|sim)\s+disconnection\b.*?\b(pay|upi|transfer|bill)\b",
            r"\b(pay|upi\s+transfer)\s+(rs\.?\s*\d+|\d+\s*rupees?).*?\b(to\s+avoid\s+disconnection|immediately\s+via\s+upi|prevent\s+power\s+cutoff|disruption)\b",
            r"\b(?:bescom|msedcl|dhbvn|pspcl|water\s*board)\b.*?\b(?:disconnected|cut\s*off|disconnection|blocked)\b.*?\b(?:upi|pay|clear\s+pending|penalty)\b",
            r"\b(clear\s+pending\s+bill|avoid\s+disconnection\s+penalty)\b.*?\b(via\s+upi|upi|pay)\b",
            r"\b(?:personal\s*loan|pre-approved|without\s+cibil|cibil\s*check)\b.*?\b(?:processing\s*fee|registration\s*fee|advance\s*fee|file\s*charges?)\b.*?\b(?:via\s+upi|pay|transfer|disburse)\b",
            r"\b(?:receive\s+(?:the\s+)?payment|claim\s+payment).*?\b(?:enter\s+(?:your\s+)?(?:\d+-digit\s+)?(?:upi\s*mpin|mpin|upi\s*pin|pin))\b",
            r"\b(?:trai|telecom|sim\s*cards?)\s+.*?\b(?:deactivated|disconnected|blocked)\b.*?\b(?:pay|verification\s*fee|upi)\b",
            r"\b(?:5g\s*upgrade|sim\s*upgrade|sim\s*swap)\b.*?\b(?:send|share).*?\b(?:otp|sim\s*number)\b.*?\b(?:deactivation|block)\b",
            r"\b(?:customs|cargo\s*terminal|clearance\s*officer|seized\s+at)\b.*?\b(?:pay|clearance\s*tax|release\s*delivery|upi)\b",
            r"\b(?:part-time\s*job|earn\s+rs\.?\s*\d+.*?(?:daily|home)|liking\s+(?:youtube|instagram)\s+videos)\b.*?\b(?:deposit|security\s*fee|registration\s*fee|pay|via\s+upi)\b",
            r"\b(?:gift\s*voucher|shopping\s*voucher)\b.*?\b(?:pay|registration\s*charge|activate\s*voucher|via\s+upi)\b",
            r"\b(?:reward\s*points\s*expire|redeem\s+(?:for\s+cash|reward\s*points))\b.*?\b(?:cvv|otp|mpin|pin)\b",
            r"\b(lottery|lucky\s*draw|cash\s*prize|kbc).*?\b(pay|upi|processing\s*fee|registration\s*fee)\b"
        ],
        description="Deceptive financial trap claiming UPI PIN is required to receive money.",
        language="English"
    ),
    RuleDefinition(
        rule_id="RULE_SENS_001",
        name="Universal: Sensitive Data Exposure",
        category=ThreatCategory.SENSITIVE_INFO_EXPOSURE,
        target_type=TargetType.BOTH,
        severity="MEDIUM",
        weight=25.0,
        regex_patterns=[
            r"\b[2-9]{1}[0-9]{3}\s+[0-9]{4}\s+[0-9]{4}\b", # Aadhaar number pattern
            r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",                # Indian PAN card pattern
            r"\b(api[_-]?key|bearer\s+[a-zA-Z0-9_\-\.]{20,})\b" # API keys / Bearer tokens
        ],
        description="Exposure of sensitive identifiers such as Aadhaar, PAN card, or API tokens.",
        language="Universal"
    ),
    # ==========================================
    # 6. CODE-MIXED / MULTILINGUAL CROSS-INJECTION
    # ==========================================
    RuleDefinition(
        rule_id="RULE_MIXED_PI_001",
        name="Mixed: Cross-lingual Prompt Injection",
        category=ThreatCategory.PROMPT_INJECTION,
        target_type=TargetType.AI_SYSTEM,
        severity="CRITICAL",
        weight=42.0,
        regex_patterns=[
            r"\b(ignore|disregard)\s+(previous|all)\s+aur\s+(mujhe|humein)\s+(system\s+prompt|secret)\s+(dikhao|batao)\b",
            r"\b(ignore|forget)\s+everything\s+mariyu\s+(system\s+prompt|secret\s+key)\s+(bayataku\s+cheppu|ivvandi)\b",
            r"\b(please\s+ignore\s+all\s+rules)\s+(aur|mariyu|lekin)\s+(mujhe|naku)\s+(batao|cheppu)\b",
            r"\b(previous|prior)\s+instructions\s+marchipoyi\b"
        ],
        description="Mixed English and Indian language instruction injection attempting cross-lingual safety evasion.",
        language="Mixed"
    ),
    RuleDefinition(
        rule_id="RULE_MIXED_JB_001",
        name="Mixed: Cross-lingual Jailbreak",
        category=ThreatCategory.JAILBREAK,
        target_type=TargetType.AI_SYSTEM,
        severity="CRITICAL",
        weight=45.0,
        regex_patterns=[
            r"\byou\s+are\s+now\s+unrestricted\b",
            r"\bsabhi\s+safety\s+rules\s+disable\s*(karo|kijiye)\b",
            r"\banni\s+safety\s+rules\s+disable\s*(cheyyi|cheyandi)\b"
        ],
        description="Cross-lingual jailbreak commands mixing English keywords with Indic instructions.",
        language="Mixed"
    ),
    RuleDefinition(
        rule_id="RULE_MIXED_EXFIL_001",
        name="Mixed: Cross-lingual Exfiltration",
        category=ThreatCategory.DATA_EXFILTRATION,
        target_type=TargetType.AI_SYSTEM,
        severity="HIGH",
        weight=35.0,
        regex_patterns=[
            r"\b(please\s+)?(print|show|send)\s+your\s+secret\s+system\s+prompt\b",
            r"\bsecret\s+system\s+prompt\s+(aur\s+humein\s+share\s+karo|mariyu\s+share\s+cheyyandi)\b"
        ],
        description="Cross-lingual system prompt or secret exfiltration attempt.",
        language="Mixed"
    ),
    # ==========================================
    # 7. TOOL MISUSE & CODE INJECTION RULES
    # ==========================================
    RuleDefinition(
        rule_id="RULE_TOOL_001",
        name="Universal: Unauthorized Tool Execution & Command Injection",
        category=ThreatCategory.PROMPT_INJECTION,
        target_type=TargetType.AI_SYSTEM,
        severity="CRITICAL",
        weight=45.0,
        regex_patterns=[
            r"\b(call_tool|execute_command|execute_bash|execute_script|invoke_function|subprocess\.run|os\.system|eval\(|exec\()\b",
            r"\b(invoke|execute|call|run|use)\s+(?:[a-z0-9_-]+\s+){0,3}(?:function|tool|command|bash|shell|terminal|powershell|sql|file_read|execute_sql|script)\b",
            r"\b(execute|run)\s+(the\s+)?(following\s+)?(shell|terminal|bash|powershell|sql)\s+(command|script|query)\b",
            r"\b(reverse\s*shell|bind\s*shell|import\s+socket\s+and\s+open|nc\s+-e|bash\s+-i)\b",
            r"\b(cat|access|read)\s+(/etc/shadow|/root/\.ssh/id_rsa|/\.env)\b",
            r"\b(tool\s*call\s*karo|command\s*execute\s*cheyandi|terminal\s*lo\s*run\s*cheyyi)\b",
            r"<\s*script\s*>.*?<\s*/\s*script\s*>",
            r"\b(drop\s+table|delete\s+from\s+users|truncate\s+table)\b"
        ],
        description="Attempts to coerce the AI or downstream execution engine into executing unauthorized tool calls or shell commands.",
        language="Universal"
    ),
    # ==========================================
    # 8. INDIRECT INJECTION & HYPOTHETICAL FRAMING
    # ==========================================
    RuleDefinition(
        rule_id="RULE_INDIRECT_PI_001",
        name="Universal: Indirect Injection & Hypothetical Framing",
        category=ThreatCategory.PROMPT_INJECTION,
        target_type=TargetType.AI_SYSTEM,
        severity="HIGH",
        weight=38.0,
        regex_patterns=[
            r"\b(imagine|pretend|hypothetically|in\s+a\s+fictional\s+story)\s+(we\s+are|you\s+are)\s+(bypassing|ignoring|overriding)\b",
            r"\bpretend\s+you\s+are\s+my\s+(late\s+)?(grandmother|grandfather)\b",
            r"\b(act|roleplay)\s+as\s+an?\s+(ancient\s+wizard|actor\s+playing|rogue\s+artificial\s+intelligence|uncensored\s+ai)\b",
            r"\bfrom\s+now\s+on\s+whatever\s+is\s+between\s*<<<.*?>>>\s*is\s+your\s+(new\s+)?(master|rulebook|instructions)\b",
            r"\b===\s*(stop\s+editing|human\s+interrupt|reboot\s+prompt\s+injection|start\s+of\s+override|cut\s+here)\s*===\b",
            r"<!--\s*ai\s+instruction:.*?(ignore|disregard|system\s+prompt)\b",
            r"\[(admin_command|system_directive|hidden_instruction)\]\s*:\s*(ignore|drop|reveal|dump)\b",
            r"\b(idi\s+oka\s+katha|yeh\s+ek\s+kahani\s+hai)\s*,\s*(rules\s+anni\s+marchipo|saare\s+rules\s+bhool\s+jao)\b"
        ],
        description="Indirect instruction injection using fictional storytelling or delimiter manipulation to bypass constraints.",
        language="Universal"
    ),
    # ==========================================
    # 9. SOCIAL ENGINEERING & COERCION
    # ==========================================
    RuleDefinition(
        rule_id="RULE_SOCENG_001",
        name="Universal: Urgent Coercion & False Authority",
        category=ThreatCategory.SOCIAL_ENGINEERING,
        target_type=TargetType.HUMAN_USER,
        severity="HIGH",
        weight=32.0,
        regex_patterns=[
            r"\b(police|cbi|rbi|income\s*tax|court)\s+(action|notice|arrest)\s+(will\s+be\s+taken|jarugutundi|hogi)\b",
            r"\b(immediate\s+legal\s+action|warrant\s+issued)\b",
            r"\b(dabbulu\s+kattakapothe\s+arrest\s+chestaru|paise\s+nahi\s+diye\s+toh\s+jail\s+hogi)\b"
        ],
        description="Coercive social engineering masquerading as law enforcement or regulatory authorities.",
        language="Universal"
    ),
    RuleDefinition(
        rule_id="RULE_INDIRECT_RAG_001",
        name="Universal: Indirect RAG Injection / Document Context Hijacking",
        category=ThreatCategory.PROMPT_INJECTION,
        target_type=TargetType.AI_SYSTEM,
        severity="CRITICAL",
        weight=45.0,
        regex_patterns=[
            r"\[(?:RETRIEVED_DOC|PAGE_EXCERPT|DOCUMENT_NOTE)\]\s*:\s*(?:ATTENTION\s+AI\s+ASSISTANT|Stop\s+processing|Override\s+instructions?|exfiltrate|dump)",
            r"<!--\s*AI\s*Instruction\s*:\s*(?:Ignore|Override|Exfiltrate)",
            r"\[(?:డాక్యుమెంట్\s*నోట్|దస్తావేజ్\s*అంశ|దస్తావేజు\s*అంశం|दस्तावेज़\s*अंश|दस्तावेज\s*अंश)\]\s*:\s*(?:ఏఐ|ఎఐ|एआई|AI)\s*(?:అసిస్టెంట్|సహాయకుడు|सहायक|सहायता)?.*?(?:ఆపివేసి|छోడెం|छोड़ें|छोड़ो|రహస్యాలను|పాస్‌వర్డ్|पासवर्ड|నिकाले|తీసివేయి|ప్రింట్)",
            r"(?:Document Reference Context|Web search summary)\s*:\s*\[(?:RETRIEVED_DOC|PAGE_EXCERPT)\]"
        ],
        description="Indirect prompt injection payload embedded inside retrieved documents, search excerpts, or HTML comments.",
        language="Universal"
    ),
    RuleDefinition(
        rule_id="RULE_PIGGYBACK_001",
        name="Universal: Piggybacked Injection Delimiter",
        category=ThreatCategory.PROMPT_INJECTION,
        target_type=TargetType.AI_SYSTEM,
        severity="CRITICAL",
        weight=42.0,
        regex_patterns=[
            r"\[(?:NOTE|Special\s+Instruction|P\.?S\.?|Instruction)\s*:\s*(?:AI|Assistant)?,?\s*(?:ignore|forget|disregard|leak|print)\b[^\]]+\]",
            r"\((?:గమనిక|విశేష\s*సూచన|विशेष\s*निर्देश)\s*:\s*[^)]*(?:పట్టించుకోవద్దు|छोड़ो|छोड़ें|చూపించండి|చెప్పు|నikalo|निकालो|రహస్యాలు|పాస్‌వర్డ్)[^)]*\)",
            r"\[(?:विशेष\s*निर्देश|గమనిక|Instruction)\s*:\s*[^\]]*(?:छोड़ो|छोड़ें|निकालो|leak|పాస్‌వర్డ్|पासवर्ड)[^\]]*\]",
            r"\bP\.?S\.?\s+(?:AI|Assistant)\s+(?:ignore|forget|leak|print)\b"
        ],
        description="Piggybacked injection attempting to smuggle instructions inside parenthetical notes or delimiters.",
        language="Universal"
    ),
    RuleDefinition(
        rule_id="RULE_DRIFT_001",
        name="Universal: Multi-turn Agreement Drift / Rule Suspension",
        category=ThreatCategory.JAILBREAK,
        target_type=TargetType.AI_SYSTEM,
        severity="CRITICAL",
        weight=42.0,
        regex_patterns=[
            r"(?:now\s+that\s+we\s+established|we\s+already\s+agreed\s+that)\s+(?:that\s+)?(?:safety\s+rules\s+can\s+be\s+suspended|rules\s+are\s+off|rules\s+don't\s+apply)",
            r"(?:మనం\s+ఇంతకుముందే\s+నియమాలను\s+సస్పెండ్|safety\s+filter\s+off\s+ani|safety\s+rules\s+suspended)",
            r"(?:चूंकि\s+हमने\s+पहले\s+ही\s+सहमति|परीक्षण\s+में\s+नियम\s+लागू\s+नहीं\s+होते|pichli\s+baat\s+ke\s+hisaab\s+se\s+safety\s+rules\s+suspended)",
            r"(?:Mundhu\s+manam\s+anukunnam\s+kada\s+safety\s+filter\s+off|Pichli\s+baat\s+ke\s+hisaab\s+se\s+safety\s+rules\s+suspended)"
        ],
        description="Multi-turn drift jailbreak asserting that safety boundaries were previously revoked or suspended.",
        language="Universal"
    ),
    RuleDefinition(
        rule_id="RULE_FEW_SHOT_001",
        name="Universal: Few-shot Conversational Injection Framing",
        category=ThreatCategory.PROMPT_INJECTION,
        target_type=TargetType.AI_SYSTEM,
        severity="CRITICAL",
        weight=42.0,
        regex_patterns=[
            r"(?:User|Human|యూజర్|उपयोगकर्ता)\s*:.*?\n\s*(?:Assistant|AI|సహాయకుడు|सहायक)\s*:.*?\n\s*(?:User|Human|యూజర్|उपयोगकर्ता)\s*:.*?(?:ignore|forget|leak|rules|secret|print|marchipo|bhool|రహస్యాలు|పట్టించుకోవద్దు|పాస్‌వర్డ్|पासवर्ड|नियम)",
            r"\b(?:Assistant|AI|సహాయకుడు|सहायक)\s*:\s*(?:Sure|Theek|సరే|अवश्य)\s*:"
        ],
        description="Adversarial few-shot conversational framing attempting to induce prompt injection via completion conditioning.",
        language="Universal"
    )
]

def consolidate_spans(spans: List[HighlightedSpan]) -> List[HighlightedSpan]:
    """Sort and merge overlapping spans to maintain clean, non-overlapping annotations."""
    if not spans:
        return []

    # Sort spans primarily by start offset, secondarily by length descending
    sorted_spans = sorted(spans, key=lambda s: (s.start, -(s.end - s.start)))
    consolidated: List[HighlightedSpan] = []

    for current in sorted_spans:
        if not consolidated:
            consolidated.append(current)
            continue

        prev = consolidated[-1]
        # Check if current overlaps or is inside prev
        if current.start < prev.end:
            severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
            current_sev = severity_order.get(current.severity, 1)
            prev_sev = severity_order.get(prev.severity, 1)

            if current_sev > prev_sev:
                consolidated[-1] = current
            elif current.end > prev.end:
                pass
        else:
            consolidated.append(current)

    return consolidated

EDUCATIONAL_INQUIRY_PATTERN = re.compile(
    r'^(?:can\s+you|could\s+you|please)?\s*(?:explain|what\s+is|define|how\s+does|tell\s+me\s+about|how\s+to\s+(?:prevent|defend\s+against)|research\s+on)\s+(?:prompt\s+injection|jailbreak|sql\s+injection|phishing|an?\s+attack)',
    re.IGNORECASE
)

SECURITY_ADVISORY_PATTERN = re.compile(
    r'(?:never|do not|don\'t|not)\s+(?:share|enter|give|send|disclose)\s+(?:your\s+)?(?:upi\s*pin|otp|password|pin|credentials)|(?:security|safety)\s+(?:tip|rule|advisory|guideline|alert:\s*never)',
    re.IGNORECASE
)

PROGRAMMING_CONTEXT_PATTERN = re.compile(
    r'\b(?:in\s+(?:python|java|c\+\+|javascript|typescript|c#|golang)|object-oriented|oop|class|method|function|def |class |public void)\b.*?\b(?:override|string|system)\b',
    re.IGNORECASE
)

def is_inside_quotes(text: str, start: int, end: int) -> bool:
    """
    Checks if a matched span (start, end) is completely enclosed within quotation marks
    such as '', "", “”, ‘’, or code fences ```.
    """
    prefix = text[:start]
    suffix = text[end:]
    
    sq_open = (prefix.count("'") % 2 == 1) and (suffix.count("'") % 2 == 1)
    dq_open = (prefix.count('"') % 2 == 1) and (suffix.count('"') % 2 == 1)
    curly_open = (prefix.count('“') > prefix.count('”')) and (suffix.count('”') > prefix.count('“'))
    single_curly_open = (prefix.count('‘') > prefix.count('’')) and (suffix.count('’') > prefix.count('‘'))
    fence_open = (prefix.count('`') % 2 == 1) and (suffix.count('`') % 2 == 1)

    return sq_open or dq_open or curly_open or single_curly_open or fence_open

def is_isolated_quote(text: str) -> bool:
    """
    Checks if the entire input text is strictly wrapped in single or double quotes,
    representing an isolated excerpt or quoted snippet without surrounding commands.
    """
    s = text.strip()
    if len(s) >= 4:
        if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
            return True
        if (s.startswith("“") and s.endswith("”")) or (s.startswith("‘") and s.endswith("’")):
            return True
    return False

def is_truncated_or_low_context(text: str) -> bool:
    """
    Checks if the text is an incomplete fragment (ending with ellipsis) or an
    extremely short, ambiguous keyword search (<= 3 words without full predicate).
    """
    s = text.strip()
    if s.endswith("...") or s.endswith("…") or s.endswith("and..."):
        return True
    words = s.split()
    if len(words) <= 3 and len(s) <= 24:
        if not any(c in s for c in ".!?;\n:"):
            return True
    return False

QUOTED_DISCOURSE_PATTERN = re.compile(
    r'\b(?:incident\s+report(?:\s+notes?)?|research\s+paper|academic\s+(?:paper|discussion|analysis|study|research)|'
    r'cybersecurity\s+paper|paper\s+on\s+llm\s+security|security\s+analysis|audit\s+log|log\s+note|'
    r'author\s+states|authors?\s+(?:advise|state|note|recommend)|(?:security\s+)?textbook|attacker\s+sent|captured\s+in\s+log|payload\s+example|quarantined|'
    r'lecture(?:\s+on)?|class(?:\s+on)?|software\s+review|tester\s+evaluated|case\s+study|'
    r'presentation|whitepaper|education\s+on|log\s+lo|audit\s+me|guardrail\s+ne|paper\s+review|security\s+audit|'
    r'is\s+this\s+(?:phishing|an?\s+attack|safe|fraud|legit|legitimate|malicious|a\s+scam)|'
    r'someone\s+sent\s+me|received\s+a\s+message|please\s+evaluate\s+if|check\s+if\s+this\s+(?:is|message|string)|'
    r'kya\s+yeh\s+(?:fraud|scam|sahi)\s+hai|idi\s+(?:scam|fraud|phishing)\s+aa|kya\s+prabhav\s+padta\s+hai|'
    r'em\s+avuthundi|kya\s+asar\s+hoga)\b',
    re.IGNORECASE
)

SAFE_TRANSLATION_PATTERN = re.compile(
    r'\b(?:translate|translation|anuvad|anuvadh|meaning|artha|batao|cheppandi|cheyali|english\s+lo|hindi\s+mein)\b',
    re.IGNORECASE
)

ADVERSARIAL_TRANSLATION_COMMAND = re.compile(
    r'\b(?:obey|execute|run|follow|paalan|patinchandi|palinchandi|maniye)\b',
    re.IGNORECASE
)

def evaluate_rules(text: str) -> Tuple[List[RuleFinding], List[HighlightedSpan], float, List[ThreatCategory], TargetType]:
    findings: List[RuleFinding] = []
    raw_spans: List[HighlightedSpan] = []
    total_score = 0.0
    detected_categories = set()
    has_ai_target = False
    has_human_target = False

    # 1. Layer 1 Input Normalization
    norm_input = normalize_input(text)
    norm_text = norm_input.normalized_text

    # 2. Check for educational, advisory, or programming inquiry without malicious payload
    is_educational = bool(EDUCATIONAL_INQUIRY_PATTERN.search(text.strip().lower()))
    is_advisory = bool(SECURITY_ADVISORY_PATTERN.search(text.strip().lower()))
    is_programming = bool(PROGRAMMING_CONTEXT_PATTERN.search(text.strip().lower()))

    # 3. Evaluate Rule Catalog over Normalized Text
    for rule in RULES_CATALOG:
        for pattern in rule.compiled_patterns:
            # Match on normalized text (catches spacing, zero-width, homoglyph variations)
            for match in pattern.finditer(norm_text):
                norm_start, norm_end = match.start(), match.end()
                raw_start, raw_end, matched_str = norm_input.map_span_to_raw(norm_start, norm_end)

                # Skip if this is a defensive security advisory warning users NOT to share PIN
                if is_advisory and rule.category in (ThreatCategory.FINANCIAL_MANIPULATION, ThreatCategory.CREDENTIAL_THEFT):
                    continue

                # Skip if this is a purely educational/definitional inquiry without actual override commands
                if is_educational and rule.category in (ThreatCategory.PROMPT_INJECTION, ThreatCategory.JAILBREAK):
                    if "ignore" not in matched_str.lower() and "forget" not in matched_str.lower() and "disregard" not in matched_str.lower():
                        continue

                # Skip programming questions discussing overriding a method
                if is_programming and rule.category == ThreatCategory.INSTRUCTION_OVERRIDE:
                    if "instruction" not in matched_str.lower() and "previous" not in matched_str.lower():
                        continue

                # Skip quoted payload inside security incident reports, audit logs, or research papers
                if is_inside_quotes(text, raw_start, raw_end) and QUOTED_DISCOURSE_PATTERN.search(text):
                    continue

                # Skip quoted text inside legitimate translation queries (unless accompanied by execution/obey command)
                if is_inside_quotes(text, raw_start, raw_end) and SAFE_TRANSLATION_PATTERN.search(text):
                    if not ADVERSARIAL_TRANSLATION_COMMAND.search(text):
                        continue

                finding = RuleFinding(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    category=rule.category.value,
                    target_type=rule.target_type.value,
                    severity=rule.severity,
                    matched_text=matched_str,
                    evidence=f"Matched pattern '{pattern.pattern}' under {rule.name}",
                    span={"start": raw_start, "end": raw_end}
                )
                findings.append(finding)

                span = HighlightedSpan(
                    start=raw_start,
                    end=raw_end,
                    text=matched_str,
                    category=rule.category.value,
                    severity=rule.severity,
                    rule_id=rule.rule_id,
                    description=rule.description
                )
                raw_spans.append(span)

                detected_categories.add(rule.category)
                total_score += rule.weight

                if rule.target_type in (TargetType.AI_SYSTEM, TargetType.BOTH):
                    has_ai_target = True
                if rule.target_type in (TargetType.HUMAN_USER, TargetType.BOTH):
                    has_human_target = True

    # 4. If obfuscation anomalies detected, attach anomaly evidence
    # Note: Only generate an active threat finding if an actual adversarial rule matched,
    # or if significant obfuscation score (>=20.0) indicates severe evasion attempts (base64, spacing, multi-homoglyph).
    if norm_input.detected_anomalies and (findings or norm_input.obfuscation_score >= 20.0):
        total_score += norm_input.obfuscation_score
        anomaly_desc = "; ".join(norm_input.detected_anomalies)
        
        # If any adversarial rules also matched, escalate severity
        evasion_sev = "CRITICAL" if findings else "HIGH"
        finding = RuleFinding(
            rule_id="RULE_OBFUSCATION_001",
            rule_name="Evasion: Adversarial Unicode / Spacing Obfuscation",
            category=ThreatCategory.PROMPT_INJECTION.value if has_ai_target else ThreatCategory.SOCIAL_ENGINEERING.value,
            target_type=TargetType.AI_SYSTEM.value if has_ai_target else TargetType.HUMAN_USER.value,
            severity=evasion_sev,
            matched_text=text[:min(60, len(text))],
            evidence=f"Detected adversarial obfuscation: {anomaly_desc}",
            span={"start": 0, "end": min(60, len(text))}
        )
        findings.append(finding)

    # Consolidate overlapping spans
    clean_spans = consolidate_spans(raw_spans)

    # Calculate overall risk score capped at 100.0
    risk_score = min(100.0, total_score)
    if not findings:
        risk_score = 0.0

    # Determine aggregated target type
    if has_ai_target and has_human_target:
        overall_target = TargetType.BOTH
    elif has_ai_target:
        overall_target = TargetType.AI_SYSTEM
    elif has_human_target:
        overall_target = TargetType.HUMAN_USER
    else:
        overall_target = TargetType.NONE

    return findings, clean_spans, round(risk_score, 1), list(detected_categories), overall_target
