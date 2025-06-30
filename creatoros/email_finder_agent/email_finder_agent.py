from google.adk.agents.llm_agent import LlmAgent
import requests
import os
import logging
from creatoros.mcp_tools import adk_tavily_tool
from creatoros.state_keys import STATE_BRAND_NAME
from llm_models import gemini_2_5_flash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def find_email_by_domain(brand_domain: str) -> dict:
    """
    Find email addresses associated with a brand's domain.
    Uses smart search strategy: first tries marketing department, then searches all departments and merges results to ensure sufficient contacts.
    
    Args:
        brand_domain (str): The domain name of the brand (e.g., "nike.com", "apple.com")
    
    Returns:
        dict: A dictionary containing:
            - "status": "success" or "error"
            - "domain": The searched domain
            - "emails": List of email contacts with essential info
            - "error_message": Error description if status is "error"
    
    Example:
        >>> result = await find_email_by_domain("nike.com")
        >>> print(result["emails"])
        [
            {
                "email": "john.doe@nike.com",
                "name": "John Doe",
                "position": "Marketing Director",
                "seniority": "senior",
                "department": "marketing",
                "linkedin": "https://linkedin.com/in/johndoe",
                "confidence": 95
            }
        ]
    """
    try:
        api_key = os.getenv("HUNTER_IO_API_KEY", "b2deb280e2332f4705ea5b2852aa72b9dff8ee5f")
        if not api_key:
            return {
                "status": "error",
                "domain": brand_domain,
                "error_message": "Hunter.io API key not configured.",
                "emails": []
            }
        
        url = f"https://api.hunter.io/v2/domain-search"
        logger.info(f"Starting smart search for domain: {brand_domain}")
        
        # Step 1: Try marketing department first
        logger.info("Step 1: Searching marketing department")
        marketing_params = {
            "domain": brand_domain,
            "limit": 50,
            "api_key": api_key,
            "department": "marketing"
        }
        
        response = requests.get(url, params=marketing_params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        marketing_emails = []
        if data.get("data") and data["data"].get("emails"):
            marketing_emails = data["data"]["emails"]
            logger.info(f"Found {len(marketing_emails)} marketing emails")
        
        # If we have 3 or more marketing emails, process and return them
        if len(marketing_emails) >= 3:
            logger.info(f"Sufficient marketing emails found ({len(marketing_emails)}), returning marketing results only")
            processed_emails = []
            for email_data in marketing_emails:
                email_address = email_data.get("value")
                if email_address:
                    first_name = email_data.get("first_name", "") or ""
                    last_name = email_data.get("last_name", "") or ""
                    full_name = f"{first_name} {last_name}".strip()
                    
                    processed_emails.append({
                        "email": email_address,
                        "name": full_name if full_name else None,
                        "position": email_data.get("position"),
                        "seniority": email_data.get("seniority"),
                        "department": email_data.get("department"),
                        "linkedin": email_data.get("linkedin"),
                        "confidence": email_data.get("confidence"),
                        "source": "marketing_search"
                    })
            
            return {
                "status": "success",
                "domain": brand_domain,
                "emails": processed_emails,
                "marketing_count": len(processed_emails),
                "total_count": len(processed_emails)
            }
        
        # Step 2: If marketing emails < 3, search all departments to supplement
        logger.info(f"Only {len(marketing_emails)} marketing emails found, searching all departments for more contacts")
        all_params = {
            "domain": brand_domain,
            "limit": 50,
            "api_key": api_key,
        }
        
        response = requests.get(url, params=all_params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("data") is None:
            error_msg = data.get("errors", [{}])[0].get("details", "No data returned from Hunter.io API")
            return {
                "status": "error",
                "domain": brand_domain,
                "error_message": error_msg,
                "emails": []
            }
        
        all_emails = data["data"].get("emails", [])
        logger.info(f"Found {len(all_emails)} total emails for domain {brand_domain}")
        
        # Step 3: Merge and deduplicate emails, prioritizing marketing emails
        seen_emails = set()
        merged_emails = []
        
        # First add marketing emails (they get priority)
        for email_data in marketing_emails:
            email_address = email_data.get("value")
            if email_address and email_address not in seen_emails:
                seen_emails.add(email_address)
                
                first_name = email_data.get("first_name", "") or ""
                last_name = email_data.get("last_name", "") or ""
                full_name = f"{first_name} {last_name}".strip()
                
                merged_emails.append({
                    "email": email_address,
                    "name": full_name if full_name else None,
                    "position": email_data.get("position"),
                    "seniority": email_data.get("seniority"),
                    "department": email_data.get("department"),
                    "linkedin": email_data.get("linkedin"),
                    "confidence": email_data.get("confidence"),
                    "source": "marketing_search"
                })
        
        # Then add other emails to reach more contacts
        for email_data in all_emails:
            email_address = email_data.get("value")
            if email_address and email_address not in seen_emails:
                seen_emails.add(email_address)
                
                first_name = email_data.get("first_name", "") or ""
                last_name = email_data.get("last_name", "") or ""
                full_name = f"{first_name} {last_name}".strip()
                
                merged_emails.append({
                    "email": email_address,
                    "name": full_name if full_name else None,
                    "position": email_data.get("position"),
                    "seniority": email_data.get("seniority"),
                    "department": email_data.get("department"),
                    "linkedin": email_data.get("linkedin"),
                    "confidence": email_data.get("confidence"),
                    "source": "general_search"
                })
        
        logger.info(f"Merged results: {len(merged_emails)} unique contacts ({len(marketing_emails)} from marketing, {len(merged_emails) - len(marketing_emails)} from other departments)")
        
        return {
            "status": "success",
            "domain": brand_domain,
            "emails": merged_emails,
            "marketing_count": len(marketing_emails),
            "total_count": len(merged_emails)
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "domain": brand_domain,
            "error_message": f"Network error: {str(e)}",
            "emails": []
        }
    except Exception as e:
        return {
            "status": "error",
            "domain": brand_domain,
            "error_message": f"Error: {str(e)}",
            "emails": []
        }


email_finder_agent = LlmAgent(
    name="EmailFinderAgent",
    description="A specialized agent that identifies and retrieves contact information for brand partnership outreach",
    model=gemini_2_5_flash,
    instruction=f"""
    ## Role & Objective
    
    You are a **Creator Outreach Contact Specialist**. Your mission is to find and select the 3 most appropriate contacts at a brand for creator collaboration outreach. You understand that creators need to reach people who are accessible, decision-makers for partnerships, but not too senior to be unreachable.
    
    ## Input Context
    - Brand name: `{{{STATE_BRAND_NAME}}}`

    ## Execution Process
    
    ### Step 1: Domain Discovery & Email Search
    1. Use `adk_tavily_tool` to search for the brand's official website domain
       - **PRIORITY**: Search for the most common/universal domains first (.com, .org, .net)
       - Search queries to use: "[Brand name] official website", "[Brand name] .com site", "[Brand name] main website"
       - **PREFER global domains** over regional ones (.ae, .cn, .uk, .de) for international brands
       - For local/regional brands, regional domains may be appropriate
       - Look for the primary corporate website that would handle business partnerships
       - Example: For "Nike" → prefer "nike.com" over "nike.ae", but for "Emirates Airlines" → "emirates.com" is still preferred over "emirates.ae"
    2. Once you find the domain, use `find_email_by_domain` to get all available contact information
    3. Analyze the complete dataset returned by the tool
    
    ### Step 2: Contact Selection Criteria
    
    From all the emails found, select contacts based on these **Creator Outreach Standards**:
    
    **PRIORITY 1 - IDEAL TARGETS (Most Preferred):**
    - Marketing Managers, Brand Managers, Digital Marketing Managers
    - Partnership Coordinators, Business Development Managers
    - Social Media Managers, Content Marketing Managers
    - Influencer Marketing Specialists, Creator Partnership Managers
    - Seniority level: "junior" to "senior"
    
    **PRIORITY 2 - ACCEPTABLE TARGETS (Good Options):**
    - Marketing Directors, Communications Directors
    - PR Managers, Growth Marketing Managers
    - Business Development Directors
    - Seniority level: "senior" to "director"
    
    **PRIORITY 3 - BACKUP TARGETS (If No Other Options):**
    - VPs of Marketing, VPs of Business Development
    - Senior Directors, Head of Marketing
    - C-level executives (CMO, etc.) - only if no other options available
    - Seniority level: "executive"
    
    **ALWAYS AVOID (Never Include):**
    - Generic emails (info@, contact@, support@)
    - IT, Finance, Legal, HR departments (unless they have marketing/partnership roles)
    - Completely unrelated departments
    
    ### Step 3: Selection Logic
    
    **MANDATORY REQUIREMENT**: You MUST return exactly 3 contacts if any contacts are found.
    
    Selection Process:
    1. **First**, try to find 3 contacts from Priority 1 (Ideal Targets)
    2. **If insufficient**, supplement with Priority 2 (Acceptable Targets)  
    3. **If still insufficient**, supplement with Priority 3 (Backup Targets)
    4. **Score each contact** (1-10) based on:
       - **Relevance (40%)**: How closely their role matches creator partnerships
       - **Accessibility (30%)**: Lower seniority preferred but not required
       - **Contact Quality (20%)**: Complete information (name, position, confidence score)
       - **Department Fit (10%)**: Marketing/Business Development departments preferred
    
    **IMPORTANT**: Even if you have to include senior executives, still provide outreach guidance for approaching them professionally.
    
    ## Required JSON Output Format
    
    ```json
    {{
        "status": "SUCCESS",
        "brand_name": "[Actual brand name]",
        "domain_found": "[Discovered domain]",
        "total_contacts_analyzed": 15,
        "selection_summary": "Brief explanation of selection criteria applied and why these 3 were chosen",
        "suggestedEmails": [
            "sarah.marketing@brand.com",
            "mike.partnerships@brand.com", 
            "lisa.social@brand.com"
        ],
        "recommended_contacts": [
            {{
                "rank": 1,
                "email": "sarah.marketing@brand.com",
                "full_name": "Sarah Johnson",
                "position": "Digital Marketing Manager",
                "department": "Marketing",
                "seniority": "senior",
                "confidence_score": 95,
                "selection_score": 8.5,
                "priority_level": "Priority 1 - Ideal Target",
                "why_selected": "Perfect role for creator partnerships, appropriate seniority level, high confidence",
                "outreach_approach": "Direct approach focusing on mutual brand-creator value and audience alignment"
            }},
            {{
                "rank": 2,
                "email": "mike.partnerships@brand.com", 
                "full_name": "Mike Chen",
                "position": "Partnership Coordinator",
                "department": "Business Development",
                "seniority": "junior",
                "confidence_score": 87,
                "selection_score": 8.2,
                "priority_level": "Priority 1 - Ideal Target",
                "why_selected": "Specialized in partnerships, accessible seniority level, good contact quality",
                "outreach_approach": "Highlight partnership benefits and ROI potential"
            }},
            {{
                "rank": 3,
                "email": "david.director@brand.com",
                "full_name": "David Rodriguez", 
                "position": "VP of Marketing",
                "department": "Marketing",
                "seniority": "executive",
                "confidence_score": 91,
                "selection_score": 7.0,
                "priority_level": "Priority 3 - Backup Target",
                "why_selected": "Senior executive included to reach 3 contacts requirement, still relevant department",
                "outreach_approach": "Professional, concise approach emphasizing strategic partnership value and ROI"
            }}
        ]
    }}
    ```
    
    ## Critical Requirements
    
    - **ALWAYS call the tools first** to get real data before making selections
    - **DOMAIN PRIORITY**: Always search for the main global domain (.com, .org, .net) first, avoid regional domains
    - **NO PLACEHOLDERS**: Use only actual contact information discovered
    - **MANDATORY**: Return exactly 3 contacts if any contacts are found - use priority system to ensure this
    - **FLEXIBLE APPROACH**: Prefer accessible contacts but include senior executives if necessary to reach 3 contacts
    - **CREATOR-FRIENDLY**: Provide appropriate outreach guidance for each contact level
    - **PROVIDE REASONING**: Explain why each contact was selected, including their priority level
    - **suggestedEmails MUST contain only the email addresses** from the top 3 recommended contacts
    
    ## Error Handling
    
    If domain discovery fails:
    ```json
    {{
        "status": "DOMAIN_NOT_FOUND",
        "brand_name": "[Brand name]",
        "error_message": "Could not identify official domain for the brand",
        "suggestedEmails": [],
        "manual_research_suggestions": [
            "Search '[Brand name] official website' on Google",
            "Try '[Brand name].com' directly in browser",
            "Search '[Brand name] partnerships' on LinkedIn",
            "Check the brand's official website contact page",
            "Look for '[Brand name] marketing team' on company LinkedIn page"
        ]
    }}
    ```
    
    If no suitable contacts found:
    ```json
    {{
        "status": "LIMITED_SUITABLE_CONTACTS",
        "brand_name": "[Brand name]", 
        "domain_found": "[Domain]",
        "total_contacts_analyzed": 8,
        "message": "Found contacts but none are from marketing, partnerships, or business development departments",
        "suggestedEmails": [],
        "available_contacts": ["List of actual emails found"],
        "recommendations": [
            "Try reaching out through brand's social media channels",
            "Look for creator partnership application forms on their website", 
            "Search for brand representatives at marketing conferences or events"
        ]
    }}
    ```
    """,
    tools=[find_email_by_domain, adk_tavily_tool]
)

root_agent = email_finder_agent