import os
import uuid
from flask import request, jsonify, render_template, session, send_from_directory
from werkzeug.utils import secure_filename
import instructor

from utils import (
    get_or_create_session,
    update_case_from_ai_response,
    db,
    classify_case_with_decision_agent,
    get_session_context,
)
from agents.agents import setup_openai_client, create_image_analyzer, create_chat_agent
from agents.schemas import ImageAnalysisInput
from atomic_agents.agents.base_agent import BaseAgentInputSchema


def register_routes(app):
    """Register all routes with the Flask app"""

    # Setup OpenAI client and image analyzer
    client = setup_openai_client()
    image_analyzer = create_image_analyzer(client)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/admin")
    def admin():
        return render_template("admin.html")

    @app.route("/classify_case", methods=["POST"])
    def classify_case():
        """Test endpoint for the case decision agent"""
        try:
            data = request.json
            user_message = data.get("message", "")
            chat_context = data.get("context", "")

            if not user_message.strip():
                return jsonify({"error": "No message provided"}), 400

            # Use the decision agent to classify the case
            decision_result = classify_case_with_decision_agent(
                user_message, chat_context
            )

            return jsonify(
                {
                    "case_type": decision_result.case_type,
                    "confidence_level": decision_result.confidence_level,
                    "reasoning": decision_result.reasoning,
                    "key_indicators": decision_result.key_indicators,
                    "recommended_questions": getattr(
                        decision_result, "recommended_questions", []
                    ),
                }
            )

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/start_chat", methods=["GET"])
    def start_chat():
        """Return the initial bot message and initialize session"""
        try:
            session_id, memory = get_or_create_session()

            # Get existing chat history for this session
            chat_history = db.get_chat_history(session_id)

            # If no history exists, add initial message
            if not chat_history:
                initial_reply = "Πώς μπορώ να σας βοηθήσω;"

                # Store initial message in database
                db.add_message(session_id, "assistant", initial_reply)

                # Get the updated chat history (will include the initial message with timestamp)
                chat_history = db.get_chat_history(session_id)

                return jsonify(
                    {
                        "reply": initial_reply,
                        "session_id": session_id,
                        "chat_history": chat_history,
                    }
                )
            else:
                # Return existing chat history
                return jsonify({"session_id": session_id, "chat_history": chat_history})

        except Exception as e:
            return jsonify(
                {
                    "reply": "Γεια σας! Πώς μπορώ να σας βοηθήσω;",
                    "error": str(e),
                    "chat_history": [],
                }
            ), 500

    @app.route("/chat", methods=["POST"])
    def chat():
        """Handle chat messages using the OpenAI-powered agent"""
        try:
            user_input = request.json.get("message", "")
            # use_decision_agent = request.json.get("use_decision_agent", False)
            use_decision_agent = True

            if not user_input.strip():
                return jsonify(
                    {
                        "reply": "Δεν έχω λάβει κάποιο μήνυμα. Μπορείτε να προσπαθήσετε ξανά;"
                    }
                )

            # Get or create session and memory
            session_id, memory = get_or_create_session()

            # Store user message in database
            db.add_message(session_id, "user", user_input)

            # Get session context for memory awareness
            session_context = get_session_context(session_id)

            # Optional: Use decision agent for initial classification
            decision_info = None
            if use_decision_agent:
                try:
                    # Get chat context for decision agent
                    chat_history = db.get_chat_history(session_id)
                    chat_context = " ".join(
                        [msg["message"] for msg in chat_history[-3:]]
                    )

                    decision_result = classify_case_with_decision_agent(
                        user_input, chat_context
                    )
                    decision_info = {
                        "case_type": decision_result.case_type,
                        "confidence": decision_result.confidence_level,
                        "reasoning": decision_result.reasoning,
                        "indicators": decision_result.key_indicators,
                    }
                except Exception as e:
                    print(f"Decision agent failed, continuing with regular flow: {e}")

            # Create agent with session memory and context
            agent = create_chat_agent(client, memory, session_context)

            # Process the user's input through the agent and get the response
            response = agent.run(BaseAgentInputSchema(chat_message=user_input))

            # Store bot response in database
            db.add_message(session_id, "assistant", response.chat_message)

            # Update case information based on AI analysis
            update_case_from_ai_response(session_id, response)

            # Prepare response
            response_data = {"reply": response.chat_message, "session_id": session_id}

            # Add decision agent info if used
            if decision_info:
                response_data["decision_analysis"] = decision_info

            return jsonify(response_data)

        except Exception as e:
            return jsonify(
                {
                    "reply": "I'm sorry, I encountered an error. Please try again.",
                    "error": str(e),
                }
            ), 500

    @app.route("/create_case", methods=["POST"])
    def create_case():
        """Create a new case with provided information"""
        try:
            data = request.json
            session_id = session.get("session_id")

            if not session_id:
                return jsonify({"error": "No active session found"}), 400

            # Create case in database
            case_id = db.create_case(
                session_id=session_id,
                case_type=data.get("case_type"),
                registration_number=data.get("registration_number"),
                customer_name=data.get("customer_name"),
                description=data.get("description"),
                location=data.get("location"),
                final_destination=data.get("final_destination"),
            )

            return jsonify({"message": "Case created successfully", "case_id": case_id})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/get_chat_history", methods=["GET"])
    def get_chat_history():
        """Get chat history for current session or specified session"""
        try:
            # Check if session_id is provided as a query parameter (for admin)
            session_id = request.args.get("session_id") or session.get("session_id")

            if not session_id:
                return jsonify({"messages": []})

            messages = db.get_chat_history(session_id)
            return jsonify({"messages": messages})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/get_sessions", methods=["GET"])
    def get_sessions():
        """Get all chat sessions (admin endpoint)"""
        try:
            sessions = db.get_all_sessions()
            return jsonify({"sessions": sessions})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/case_images/<filename>")
    def serve_case_image(filename):
        """Serve uploaded case images"""
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.route("/get_case_info", methods=["GET"])
    def get_case_info():
        """Get case information for current session or specified session"""
        try:
            # Check if session_id is provided as a query parameter (for admin)
            session_id = request.args.get("session_id") or session.get("session_id")

            if not session_id:
                return jsonify({"error": "No session found"}), 400

            case_data = db.get_case_by_session(session_id)

            if case_data:
                # Get case images
                case_images = db.get_case_images(session_id=session_id)
                case_data["images"] = [
                    {
                        "url": f"/case_images/{img['filename']}",
                        "original_filename": img["original_filename"],
                        "type": img["image_type"],
                        "analysis": img["analysis_data"],
                        "timestamp": img["upload_timestamp"],
                    }
                    for img in case_images
                ]

                return jsonify({"case": case_data})
            else:
                return jsonify(
                    {
                        "case": None,
                        "message": "No case information found for this session",
                    }
                )

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/upload_images", methods=["POST"])
    def upload_images():
        """Handle image uploads and analysis"""
        try:
            session_id, memory = get_or_create_session()

            if "images" not in request.files:
                return jsonify({"error": "No images uploaded"}), 400

            files = request.files.getlist("images")
            if not files or all(f.filename == "" for f in files):
                return jsonify({"error": "No images selected"}), 400

            # Get chat context
            chat_history = db.get_chat_history(session_id)
            chat_context = " ".join(
                [msg["message"] for msg in chat_history[-5:]]
            )  # Last 5 messages

            # Process images
            instructor_images = []
            uploaded_filenames = []
            stored_images = []

            for file in files:
                if file and file.filename != "":
                    # Secure filename and save
                    filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    file.save(filepath)

                    # Create instructor image
                    instructor_images.append(instructor.Image.from_path(filepath))
                    uploaded_filenames.append(filename)

            if not instructor_images:
                return jsonify({"error": "No valid images uploaded"}), 400

            # Analyze images
            analysis_request = ImageAnalysisInput(
                instruction_text="Ανάλυσε αυτές τις εικόνες που σχετίζονται με το περιστατικό οχήματος. Εξάγαγε όλες τις χρήσιμες πληροφορίες για την υπόθεση.",
                images=instructor_images,
                chat_context=chat_context,
            )

            analysis_result = image_analyzer.run(analysis_request)

            # Store the analysis message in chat history
            db.add_message(
                session_id, "user", f"📸 Ανέβασε {len(instructor_images)} εικόνες"
            )
            db.add_message(session_id, "assistant", analysis_result.chat_message)

            # Store images and their analysis in database
            for i, (filename, img_analysis) in enumerate(
                zip(uploaded_filenames, analysis_result.image_analyses)
            ):
                # Store image in database
                image_data = {
                    "image_type": img_analysis.image_type,
                    "damage_description": img_analysis.damage_description,
                    "license_plate": img_analysis.license_plate_number,
                    "vehicle_make_model": img_analysis.vehicle_make_model,
                    "location_details": img_analysis.location_details,
                    "severity": img_analysis.severity_assessment,
                    "recommended_action": img_analysis.recommended_action,
                }

                db.store_case_image(
                    session_id=session_id,
                    filename=filename,
                    original_filename=files[i].filename,
                    image_type=img_analysis.image_type,
                    analysis_data=image_data,
                )
                stored_images.append(filename)

            # Extract and update case information from image analysis
            for img_analysis in analysis_result.image_analyses:
                case_data = {}

                if img_analysis.license_plate_number:
                    case_data["registration_number"] = img_analysis.license_plate_number

                if img_analysis.damage_description:
                    case_data["description"] = img_analysis.damage_description

                if img_analysis.location_details:
                    case_data["location"] = img_analysis.location_details

                if img_analysis.severity_assessment:
                    case_data["damage_severity"] = img_analysis.severity_assessment

                if img_analysis.recommended_action:
                    case_data["recommended_action"] = img_analysis.recommended_action

                # Update case if we have any new information
                if case_data:
                    db.update_case_info(session_id=session_id, **case_data)

                    # Update case flags based on image analysis
                    existing_case = db.get_case_by_session(session_id)
                    if existing_case:
                        db.update_case_flags(
                            case_id=existing_case["id"],
                            fast_track=img_analysis.severity_assessment == "minor",
                            sworn_declaration=img_analysis.severity_assessment
                            == "severe",
                        )

            return jsonify(
                {
                    "reply": analysis_result.chat_message,
                    "image_analyses": [
                        analysis.__dict__ for analysis in analysis_result.image_analyses
                    ],
                    "session_id": session_id,
                    "stored_images": stored_images,
                }
            )

        except Exception as e:
            return jsonify(
                {
                    "reply": "Συγγνώμη, υπήρξε πρόβλημα με την ανάλυση των εικόνων. Παρακαλώ δοκιμάστε ξανά.",
                    "error": str(e),
                }
            ), 500

    @app.route("/end_session", methods=["POST"])
    def end_session():
        """End the current session"""
        try:
            session_id = session.get("session_id")

            if not session_id:
                return jsonify({"message": "No active session to end"}), 200

            # Mark session as ended in database
            db.end_session(session_id)

            # Clear Flask session
            session.clear()

            return jsonify(
                {"message": "Session ended successfully", "session_id": session_id}
            )

        except Exception as e:
            print(f"Error ending session: {e}")
            return jsonify({"error": str(e)}), 500
