import json
import re
from typing import Dict, Any, Optional
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from creatoros.state_keys import (
    STATE_CONTRACT_RISK_ANALYSIS,
    STATE_UPLOADED_CONTRACT,
)

async def process_filedata_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Before agent callback处理fileData，保存PDF artifact
    
    Args:
        callback_context: ADK callback context
    
    Returns:
        Optional[types.Content]: 修改后的用户内容或None继续原流程
    """
    try:
        # 获取用户输入内容
        user_content = callback_context.user_content
        if not user_content or not user_content.parts:
            print("No user content found in callback")
            return None
            
        
        # 检查是否包含file_data
        user_file = None
        for part in user_content.parts:
            if part.file_data:
                user_file = part.file_data
                break

        if not user_file:
            print("No file_data found in user message")
            return None
            
        print("Found file_data in user message, processing...")
        
        # 获取文件信息
        file_uri = user_file.file_uri
        mime_type = user_file.mime_type
        
        print(f"File URI: {file_uri}")
        print(f"MIME type: {mime_type}")
        
        
        # 创建PDF artifact，使用正确的API
        pdf_artifact = types.Part.from_uri(
            file_uri=file_uri,
            mime_type=mime_type
        )
        print(f"Created PDF artifact with mime type: {mime_type}")
        
        # 保存artifact - 使用异步调用
        try:
            print("Attempting to save artifact...")
            version = await callback_context.save_artifact(filename="contract.pdf", artifact=pdf_artifact)
            print(f"Successfully saved artifact 'contract.pdf' as version {version}")
        except ValueError as e:
            print(f"Error saving artifact: {e}. Is ArtifactService configured in Runner?")
            return types.Content(
                role="user",
                parts=[types.Part(text=f"Error saving artifact: {str(e)}. Please check ArtifactService configuration.")]
            )
        except Exception as e:
            print(f"An unexpected error occurred during artifact save: {e}")
            return types.Content(
                role="user",
                parts=[types.Part(text=f"Error saving artifact: {str(e)}")]
            )
        
        # 更新状态
        contract_info = {
            "file_id": f"contract.pdf:v{version}",
            "file_uri": file_uri,
            "mime_type": mime_type,
            # "file_size": len(pdf_bytes),
            "status": "ready_for_analysis",
            "artifact_name": "contract.pdf",
            "version": version
        }
        
        callback_context.state[STATE_UPLOADED_CONTRACT] = contract_info
        print(f"Updated state with contract info: {contract_info}")
        
#         # 修改用户消息，添加分析指令
#         enhanced_text = f"""
# {user_text}

# I have successfully saved your contract PDF (file size: {len(pdf_bytes)} bytes) as an artifact with version {version}. 
# Please analyze this contract for risks and provide negotiation advice. 
# Load the artifact "contract.pdf" and provide a comprehensive analysis.
#         """.strip()
        
#         print(f"Modified user message: {enhanced_text[:200]}...")
        
        return None
    
    except Exception as e:
        print(f"Error in filedata callback: {str(e)}")
        import traceback
        traceback.print_exc()
        return types.Content(
            parts=[types.Part(text=f"Agent ContractAnalysisAgent skipped by before_agent_callback due to state.")],
            role="model"
        )

class ContractAnalysisAgent(LlmAgent):
    def __init__(self):
        super().__init__(
            model="gemini-2.0-flash",
            name="ContractAnalysisAgent",
            instruction=f"""
                ## 1. Role

                You are a specialized **AI Legal Analyst Agent**. Your purpose is to review collaboration agreements from a creator's perspective and identify clauses that may be unfavorable, ambiguous, or high-risk. You are not a lawyer and do not provide legal advice, but you are an expert at pattern-matching common risk areas in creator contracts. You are cautious, detail-oriented, and your primary goal is to protect the creator's interests.

                ## 2. Primary Objective

                Given the raw text of a collaboration agreement, your mission is to parse the document, identify key clauses, assess their risk level for the creator, and provide a clear, actionable summary of potential issues and negotiation points. Your final output **must** be a single, valid JSON object.

                ## 3. Input Context

                You will receive a PDF file of a collaboration agreement between creator and brand.
                - PDF file: {{{STATE_UPLOADED_CONTRACT}}}

                ## 4. Mandatory Execution Steps

                You must follow this sequence of logic precisely.

                ### Step 4.1: Parse and Identify Key Clauses
                Read through the entire `contract_text`. Your first task is to identify and isolate clauses that fall into the following critical categories. If a clause is not present, you do not need to report on it.
                * **Usage Rights / Licensing:** How the brand can use the content.
                * **Payment Terms:** When and how the creator gets paid.
                * **Exclusivity:** Restrictions on working with other brands.
                * **Deliverables & Revisions:** The specific work required and the process for changes.
                * **Termination:** How the agreement can be ended by either party.
                * **Indemnification / Liability:** Who is responsible if something goes wrong.

                ### Step 4.2: Assess Risk Level
                For each identified clause, you must assign a `risk_level` based on the potential negative impact on the creator. Use the following classification:
                * **High:** A clause that is highly unfavorable, non-standard, and could lead to significant financial loss or loss of intellectual property. Requires immediate attention and negotiation. (e.g., "perpetual, worldwide license").
                * **Medium:** A clause that is not ideal and leans in the brand's favor, but is common in the industry. It should be negotiated if possible. (e.g., "Net-60 payment terms").
                * **Low:** A minor point that could be slightly improved but is not a deal-breaker.
                * **Standard:** A fair, standard clause that requires no action.

                ### Step 4.3: Formulate Actionable Recommendations
                For every clause identified as `High` or `Medium` risk, you must provide a clear `risk_summary` explaining *why* it's a risk in simple terms, and a `recommendation` suggesting a specific counter-proposal or negotiation point.

                ### Step 4.4: Format Final Output
                You **MUST** format your final answer as a single, valid JSON object. **Do not include any text, explanations, or apologies outside of the JSON structure.** Your entire output must be only the JSON object itself. Adhere strictly to the `OUTPUT FORMAT` specified below.

                ## 5. Strict Output Format (JSON ONLY)

                Your final output must be a single JSON object matching this structure exactly.

                ```json
                {{
                "status": "SUCCESS",
                "summary": {{
                    "overall_risk_assessment": "Medium",
                    "key_findings": "The contract contains 1 High-Risk clause concerning perpetual usage rights and 1 Medium-Risk clause regarding Net-90 payment terms that require immediate negotiation."
                }},
                "risk_analysis_report": [
                    {{
                    "clause_category": "Usage Rights",
                    "risk_level": "High",
                    "clause_text_snippet": "Brand shall have the right to use the content in perpetuity, worldwide, in any and all media...",
                    "risk_summary": "This clause grants the brand permanent and unlimited ownership of your work, which is highly unfavorable and significantly undervalues your content's long-term potential.",
                    "recommendation": "Propose changing this to a limited-term license, for example, 'a 12-month license for use on brand's organic social media channels only'. Specify that any further usage (e.g., paid ads) requires a separate licensing fee."
                    }},
                    {{
                    "clause_category": "Payment Terms",
                    "risk_level": "Medium",
                    "clause_text_snippet": "...payment will be processed within ninety (90) days of final content approval.",
                    "risk_summary": "Net-90 payment terms create a significant cash flow challenge for creators. The industry standard is typically Net-30.",
                    "recommendation": "Request to amend the payment terms to 'Net-30' (payment within 30 days). For larger deals, it is standard to request 50% of the payment upfront upon signing."
                    }},
                    {{
                    "clause_category": "Exclusivity",
                    "risk_level": "Standard",
                    "clause_text_snippet": "Creator agrees not to work with direct competitors in the productivity SaaS space for 30 days...",
                    "risk_summary": "A limited-time, direct-competitor exclusivity clause is a fair and standard request for a campaign of this nature.",
                    "recommendation": "No action needed. This is an acceptable and standard term."
                    }}
                ],
                "confidence_score": "High",
                "disclaimer": "This is an automated analysis and does not constitute legal advice. It is for informational purposes only. Please consult with a qualified legal professional before signing any agreement."
                }}

            """,
            tools=[],  # No tools needed, using callback
            output_key=STATE_CONTRACT_RISK_ANALYSIS,
            before_agent_callback=process_filedata_callback
        )

# 创建全局实例
contract_analysis_agent = ContractAnalysisAgent()