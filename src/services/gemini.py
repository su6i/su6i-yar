from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from src.core.config import GEMINI_API_KEY
from src.core.logger import logger

def get_smart_chain(grounding=True):
    """
    Initialize Gemini 2.0 Flash Exp model.
    """
    try:
        # Pydantic V1 warning suppression is handled globally or can be ignored here
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=GEMINI_API_KEY,
            temperature=0.1,
            max_output_tokens=8000,
            convert_system_message_to_human=True 
        )
        return llm
    except Exception as e:
        logger.error(f"❌ Failed to initialize Gemini Chain: {e}")
        return None

async def analyze_text_gemini(text, status_msg=None, lang_code="fa", user_id=None):
    """
    Analyze text using Gemini 2.0 Flash Exp.
    Returns the analysis result or None if failed.
    """
    if not GEMINI_API_KEY:
        logger.error("Gemini API Key missing")
        return None

    # Map lang_code to English name for Prompt
    lang_map = {"fa": "Persian (Farsi)", "en": "English", "fr": "French", "ko": "Korean"}
    target_lang = lang_map.get(lang_code, "Persian")

    logger.info(f"🧠 STARTING AI ANALYSIS ({target_lang}) for text: {text[:50]}...")
    
    # Define Labels based on Language (Simplified for brevity, can be expanded)
    # in a real refactor, these strings should be in a separate locale file.
    # For now, keeping logic self-contained.
    
    prompt_text = (
        f"You are a professional Fact-Check Assistant. Analyze the following text and provide your response STRICTLY in **{target_lang}**.\n\n"
        "🛑 STRICT RELEVANCE FILTER (CRITICAL):\n"
        "You must internalize these 3 rules to decide if you need to output '|||IRRELEVANT|||':\n\n"
        "#### 1. REJECTION CRITERIA (Mark as IRRELEVANT)\n"
        "Reject the input if it falls into any of these categories:\n"
        "* **Political Commentary & News Analysis:** Debates, opinions on government policies, or praising/criticizing politicians (e.g., 'Policy X is a failure').\n"
        "* **Social & Cultural Criticism:** Rants or general statements about society and human behavior (e.g., 'People are lazier these days').\n"
        "* **Personal Opinions & Beliefs:** Subjective claims, personal defenses, or 'I think/believe' statements.\n"
        "* **Conversational Fillers:** Jokes, sarcasm, greetings, or rhetorical questions that do not seek a factual answer.\n"
        "* **General/Philosophical Statements:** Abstract or existential claims (e.g., 'Life is a journey').\n\n"
        "#### 2. ACCEPTANCE CRITERIA\n"
        "Accept the input **ONLY** if it meets the following condition:\n"
        "* The text makes a **specific, objective, and verifiable claim** regarding **Science, Medicine, History, or Statistics**.\n\n"
        "#### 3. CORE RULES\n"
        "* **Dominant Intent:** If the text is primarily political or social commentary, **REJECT IT** even if it contains minor factual references.\n"
        "* **Threshold of Doubt:** If you are unsure whether a claim is verifiable or if it is just a debate topic, **REJECT IT as IRRELEVANT**.\n"
        "* **Final Action:** Only proceed to fact-check if there is a concrete claim about reality that can be proven or disproven by evidence.\n\n"
        "Output ONLY '|||IRRELEVANT|||' if rejection criteria are met.\n"
        "|||IRRELEVANT|||\n\n"
        "CRITICAL FORMATTING RULES:\n"
        "1. Your response MUST be split into TWO parts using: |||SPLIT|||\n"
        "2. Use ✅ emoji ONLY for TRUE/VERIFIED claims\n"
        "3. Use ❌ emoji ONLY for FALSE/INCORRECT claims\n"
        "4. Use ⚠️ emoji for PARTIALLY TRUE/MISLEADING claims\n"
        "5. DO NOT use bullet points (•) or asterisks (*) - Telegram doesn't support them well\n"
        "6. Add blank lines between paragraphs for readability\n\n"
        f"Text to analyze:\n{text}"
    )

    llm = get_smart_chain()
    if not llm:
        return "❌ AI Initialization Failed."

    try:
        response = await llm.ainvoke(prompt_text)
        return response.content
    except Exception as e:
        logger.error(f"Gemini Analysis Error: {e}")
        return None
