from flask import session
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.agents.base_agent import BaseAgentInputSchema
from agents.schemas import CustomOutputSchema, CaseDecisionInputSchema
from database.database import ChatDatabase

# Initialize database
db = ChatDatabase()


def get_or_create_session():
    """Get existing session or create a new one"""
    if "session_id" not in session:
        # Create new chat session in database
        session_id = db.create_chat_session()
        session["session_id"] = session_id

        # Create empty memory for new session
        memory = AgentMemory()

        return session_id, memory
    else:
        session_id = session["session_id"]

        # Recreate memory from database history
        memory = AgentMemory()
        chat_history = db.get_chat_history(session_id)

        for msg in chat_history:
            if msg["sender"] == "assistant":
                memory.add_message(
                    "assistant", CustomOutputSchema(chat_message=msg["message"])
                )
            else:
                memory.add_message(
                    "user", BaseAgentInputSchema(chat_message=msg["message"])
                )

        return session_id, memory


def get_session_context(session_id: str) -> str:
    """Generate context string with previously collected information"""
    try:
        # Get session info
        sessions = db.get_all_sessions()
        session_info = next(
            (s for s in sessions if s["session_id"] == session_id), None
        )

        # Get case info
        case_info = db.get_case_by_session(session_id)

        context_parts = []

        # Check for customer name and registration from both session and case
        customer_name = None
        registration_number = None

        if session_info:
            customer_name = session_info.get("customer_name")
            registration_number = session_info.get("registration_number")

        # Fallback to case info if not in session
        if case_info:
            if not customer_name and case_info.get("customer_name"):
                customer_name = case_info["customer_name"]
            if not registration_number and case_info.get("registration_number"):
                registration_number = case_info["registration_number"]

        # Add customer information if available
        if customer_name:
            context_parts.append(f"Customer Name: {customer_name}")
        if registration_number:
            context_parts.append(f"Registration Number: {registration_number}")

        # Add case-specific information
        if case_info:
            if case_info.get("case_type"):
                context_parts.append(f"Case Type: {case_info['case_type']}")
            if case_info.get("location"):
                context_parts.append(f"Location: {case_info['location']}")
            if case_info.get("final_destination"):
                context_parts.append(f"Destination: {case_info['final_destination']}")
            if case_info.get("description"):
                context_parts.append(f"Description: {case_info['description']}")

        if context_parts:
            return (
                "PREVIOUSLY COLLECTED INFORMATION:\n"
                + "\n".join(context_parts)
                + "\n\nNOTE: Do not ask for information that has already been provided above."
            )

        return ""
    except Exception as e:
        print(f"Error generating session context: {e}")
        return ""


def classify_case_with_decision_agent(user_message: str, chat_context: str = None):
    """Use the decision agent to classify if case is AC, RA, or OTHER"""
    try:
        from agents.agents import setup_openai_client, create_case_decision_agent

        # Setup client and agent
        client = setup_openai_client()
        decision_agent = create_case_decision_agent(client)

        # Run decision agent
        decision_input = CaseDecisionInputSchema(
            user_message=user_message, chat_context=chat_context
        )

        decision_result = decision_agent.run(decision_input)

        # Map the case type to database code
        mapped_case_type = get_case_type_code(decision_result.case_type)

        print("🎯 Decision Agent Result:")
        print(f"   Case Type: {mapped_case_type} ({decision_result.case_type})")
        print(f"   Confidence: {decision_result.confidence_level}")
        print(f"   Reasoning: {decision_result.reasoning}")
        print(f"   Key Indicators: {decision_result.key_indicators}")

        # Create a new result object with the mapped case type
        return type(
            "obj",
            (object,),
            {
                "case_type": mapped_case_type,
                "confidence_level": decision_result.confidence_level,
                "reasoning": decision_result.reasoning,
                "key_indicators": decision_result.key_indicators,
            },
        )()

    except Exception as e:
        print(f"❌ Error in decision agent: {str(e)}")
        # Fallback to basic classification
        user_lower = user_message.lower()
        if any(
            word in user_lower
            for word in ["τράκαρα", "χτύπησα", "ατύχημα", "χτύπημα", "ζημιά"]
        ):
            return type(
                "obj",
                (object,),
                {
                    "case_type": "AC",
                    "confidence_level": "MEDIUM",
                    "reasoning": "Fallback classification based on keywords",
                    "key_indicators": ["keyword-based"],
                },
            )()
        elif any(
            word in user_lower
            for word in ["βλάβη", "λάστιχο", "βενζίνη", "μπαταρία", "κινητήρας"]
        ):
            return type(
                "obj",
                (object,),
                {
                    "case_type": "RA",
                    "confidence_level": "MEDIUM",
                    "reasoning": "Fallback classification based on keywords",
                    "key_indicators": ["keyword-based"],
                },
            )()
        else:
            return type(
                "obj",
                (object,),
                {
                    "case_type": "OTHER",
                    "confidence_level": "LOW",
                    "reasoning": "No clear indicators found",
                    "key_indicators": [],
                },
            )()


def get_case_type_code(case_type: str) -> str:
    """Map Greek case types to database codes"""
    if not case_type:
        return None

    case_type = case_type.lower().strip()
    mapping = {
        "ατύχημα": "AC",
        "οδική βοήθεια": "RA",
        "άλλο": "OTHER",
        # Keep English codes for backward compatibility
        "ac": "AC",
        "ra": "RA",
        "other": "OTHER",
    }
    return mapping.get(case_type, "OTHER")


def update_case_from_ai_response(session_id: str, ai_response: CustomOutputSchema):
    """Update case information based on AI analysis from the latest response"""
    try:
        # Check if we have any meaningful case information from AI
        has_case_info = any(
            [
                ai_response.extracted_registration_number,
                ai_response.extracted_customer_name,
                ai_response.case_type,
                ai_response.extracted_location,
                ai_response.extracted_destination,
                ai_response.case_description,
                ai_response.damage_severity,
                ai_response.recommended_action,
                ai_response.is_fast_track is not None,
                ai_response.fraud_risk is not None,
                ai_response.needs_geolocation is not None,
                ai_response.needs_sworn_declaration is not None,
                ai_response.delay_compensation is not None,
                ai_response.out_of_prefecture is not None,
            ]
        )

        if not has_case_info:
            return

        # Update session-level information if provided
        if (
            ai_response.extracted_customer_name
            or ai_response.extracted_registration_number
        ):
            db.update_session_info(
                session_id=session_id,
                customer_name=ai_response.extracted_customer_name,
                registration_number=ai_response.extracted_registration_number,
            )

        # Get existing case to avoid overwriting data
        existing_case = db.get_case_by_session(session_id)

        # Prepare case update data, preserving existing values
        case_data = {}

        if ai_response.case_type:
            case_data["case_type"] = get_case_type_code(ai_response.case_type)

        if ai_response.extracted_registration_number:
            case_data["registration_number"] = ai_response.extracted_registration_number

        if ai_response.extracted_customer_name:
            case_data["customer_name"] = ai_response.extracted_customer_name

        if ai_response.case_description:
            # Append to existing description if it exists and is different
            if existing_case and existing_case.get("description"):
                existing_desc = existing_case["description"]
                if ai_response.case_description not in existing_desc:
                    case_data["description"] = (
                        f"{existing_desc}. {ai_response.case_description}"
                    )
            else:
                case_data["description"] = ai_response.case_description

        if ai_response.extracted_location:
            case_data["location"] = ai_response.extracted_location

        if ai_response.extracted_destination:
            case_data["final_destination"] = ai_response.extracted_destination

        # Update case information if we have new data
        if case_data:
            case_id = db.update_case_info(session_id=session_id, **case_data)
        else:
            case_id = existing_case["id"] if existing_case else None

        if not case_id:
            return

        # Update case analysis with AI insights
        analysis_data = {
            "malfunction": ai_response.case_description
            if get_case_type_code(ai_response.case_type) == "RA"
            else None,
            "resolution": ai_response.recommended_action,
            "repair_shop": "Nearest authorized repair facility"
            if get_case_type_code(ai_response.case_type) == "AC"
            else None,
            "within_prefecture": not ai_response.out_of_prefecture
            if ai_response.out_of_prefecture is not None
            else True,
        }

        # Only update analysis if we have new information
        if any(v is not None for v in analysis_data.values()):
            db.update_case_analysis(case_id=case_id, **analysis_data)

        # Update case flags with AI decisions
        flags_data = {
            "delay_voucher": ai_response.delay_compensation,
            "geolocation_sent": ai_response.needs_geolocation,
            "sworn_declaration": ai_response.needs_sworn_declaration,
            "fast_track": ai_response.is_fast_track,
            "fraud": ai_response.fraud_risk,
        }

        # Only update flags if we have new information
        if any(v is not None for v in flags_data.values()):
            db.update_case_flags(case_id=case_id, **flags_data)

        # Generate case summary
        tags = []
        if ai_response.case_type:
            case_code = get_case_type_code(ai_response.case_type)
            tags.append(case_code.lower())
        if ai_response.is_fast_track:
            tags.append("fast-track")
        if ai_response.fraud_risk:
            tags.append("fraud-risk")
        if ai_response.extracted_location:
            tags.append("location-provided")
        if ai_response.damage_severity:
            tags.append(f"severity-{ai_response.damage_severity}")
        if ai_response.needs_geolocation:
            tags.append("needs-geolocation")
        if ai_response.needs_sworn_declaration:
            tags.append("needs-declaration")
        if ai_response.delay_compensation:
            tags.append("delay-compensation")
        if ai_response.out_of_prefecture:
            tags.append("out-of-prefecture")

        # Generate summary from AI understanding
        summary_parts = []
        case_code = (
            get_case_type_code(ai_response.case_type) if ai_response.case_type else None
        )
        if case_code == "AC":
            summary_parts.append("Accident case")
        elif case_code == "RA":
            summary_parts.append("Road assistance case")

        if ai_response.case_description:
            summary_parts.append(
                f"Description: {ai_response.case_description[:100]}..."
            )

        if ai_response.extracted_location:
            summary_parts.append(f"Location: {ai_response.extracted_location}")

        if ai_response.damage_severity:
            summary_parts.append(f"Severity: {ai_response.damage_severity}")

        if ai_response.recommended_action:
            summary_parts.append(f"Action: {ai_response.recommended_action}")

        summary = (
            ". ".join(summary_parts)
            if summary_parts
            else "Case information being gathered"
        )

        communication_quality = (
            "Good - AI analyzed" if has_case_info else "Pending - gathering information"
        )

        db.update_case_summary(
            case_id=case_id,
            communication_quality=communication_quality,
            tags=tags,
            summary=summary,
        )

        print(f"✅ Case updated from AI analysis for session {session_id[:8]}...")

    except Exception as e:
        print(f"❌ Error updating case from AI: {str(e)}")
