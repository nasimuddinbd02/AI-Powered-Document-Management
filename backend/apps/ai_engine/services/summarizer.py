import os
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from apps.ai_engine.models import AISummary

def generate_summary(document):
    """
    Generates a summary for the given document and stores it in AISummary.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception("OpenAI API Key not configured")

    llm = ChatOpenAI(temperature=0.3, model_name="gpt-4", openai_api_key=api_key)
    
    # We should extract text from the document. For simplicity, we assume
    # document text extraction is done and available (e.g., via OCR or pdf parser)
    # Since we are setting up, we'll fetch its text from its current version.
    current_version = document.current_version
    text_content = ""
    if current_version and current_version.ocr_text:
        text_content = current_version.ocr_text
    else:
        # Fallback to document description if no text
        text_content = document.description or "No content available."

    prompt = PromptTemplate(
        input_variables=["text"],
        template="""Please read the following text and provide a comprehensive summary.
        Also, extract the key topics as a list and entities as a dictionary.
        
        Text:
        {text}
        
        Output format should be structured clearly."""
    )
    
    chain = LLMChain(llm=llm, prompt=prompt)
    summary_result = chain.run(text=text_content)
    
    # Normally we would parse JSON to get key_topics and entities.
    # For now, we will store the raw output.
    
    summary = AISummary.objects.create(
        document=document,
        version_number=current_version.version_number if current_version else 1,
        summary=summary_result,
        key_topics=[],
        entities={},
        model_used="gpt-4"
    )
    return summary
