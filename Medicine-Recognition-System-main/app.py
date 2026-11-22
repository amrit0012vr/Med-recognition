import os
import io
import base64
from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai
import markdown
from flask import Flask, request, render_template, session

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "medicine-recognition-secret-2026")

# Maximum upload size: 16 MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

def save_api_key_to_env(key):
    """Persists API key into .env files for future runs."""
    if not key or key == "your_google_api_key_here":
        return
    for base_dir in [os.path.dirname(__file__), os.path.join(os.path.dirname(__file__), "Medicine-Recognition-System-main")]:
        env_file = os.path.join(base_dir, ".env")
        try:
            lines = []
            if os.path.exists(env_file):
                with open(env_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            
            key_written = False
            new_lines = []
            for line in lines:
                if line.strip().startswith("GOOGLE_API_KEY="):
                    new_lines.append(f"GOOGLE_API_KEY={key}\n")
                    key_written = True
                else:
                    new_lines.append(line)
            if not key_written:
                new_lines.append(f"\nGOOGLE_API_KEY={key}\n")
                
            with open(env_file, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
        except Exception as e:
            print(f"Notice: Could not write key to {env_file}: {e}")

def get_api_key():
    return (
        request.form.get("api_key", "").strip()
        or session.get("api_key", "")
        or os.getenv("GOOGLE_API_KEY", "").strip()
        or os.getenv("GEMINI_API_KEY", "").strip()
    )

def get_available_models(api_key):
    """
    Queries Google Generative AI to get the live list of models
    that support 'generateContent' for this specific API key.
    """
    genai.configure(api_key=api_key)
    try:
        models = [
            m.name.replace("models/", "")
            for m in genai.list_models()
            if "generateContent" in getattr(m, "supported_generation_methods", [])
        ]
        return models
    except Exception as e:
        print(f"Notice: genai.list_models() failed: {e}")
        return []

def analyze_image_with_fallback(api_key, image, prompt):
    """
    Analyzes the image with smart model discovery and fallback.
    If a model returns 404 (deprecated/not found), automatically falls back
    to active modern models (e.g. gemini-2.0-flash, gemini-2.5-flash).
    """
    genai.configure(api_key=api_key)

    # Priority order of vision-capable models (modern 2.0 / 2.5 series first)
    priority_order = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-exp",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash-002",
        "gemini-1.5-flash-001",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
        "gemini-1.5-pro-latest",
        "gemini-1.5-pro",
        "gemini-2.5-pro"
    ]

    env_model = os.getenv("GEMINI_MODEL", "").strip()
    if env_model:
        if env_model in priority_order:
            priority_order.remove(env_model)
        priority_order.insert(0, env_model)

    # 1. Query live available models for this specific API key
    live_models = get_available_models(api_key)
    print(f"Live models available for this API key: {live_models}")

    candidates = []
    if live_models:
        # First match candidates from priority list that are confirmed available
        for p in priority_order:
            if p in live_models and p not in candidates:
                candidates.append(p)
        # Then add any other live models that support generateContent
        for lm in live_models:
            if lm not in candidates and any(k in lm for k in ["flash", "pro", "gemini"]):
                candidates.append(lm)

    # If live query was empty or failed, use the static priority list
    if not candidates:
        candidates = priority_order

    last_error = None
    for model_name in candidates:
        try:
            print(f"Analyzing with Gemini model: {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content([prompt, image])
            if response and response.text:
                print(f"Successfully generated response with: {model_name}")
                return response.text, model_name, None
        except Exception as e:
            err_msg = str(e)
            print(f"Model {model_name} returned error: {err_msg}")
            last_error = e

            # If 404 (model not found/supported), try next candidate model
            if "404" in err_msg or "not found" in err_msg.lower() or "not supported" in err_msg.lower():
                continue

            # If invalid API key, stop and alert user
            if "API_KEY_INVALID" in err_msg or ("400" in err_msg and "key" in err_msg.lower()):
                return None, model_name, f"Invalid API Key. Please verify your Gemini API key: {err_msg}"

            # For quota or other issues, try next model before giving up
            continue

    return None, None, f"All attempted models failed. Last error: {str(last_error)}"

def validate_medical_content(api_key, model_name, response_text):
    """Validates whether the generated response confirms a medical context."""
    if not response_text:
        return False
    if "NOT_MEDICAL:" in response_text:
        return False

    validation_prompt = f"""
    Determine whether the following text discusses a valid medical, healthcare, anatomical, pharmacological, or clinical context:

    \"\"\"{response_text[:800]}\"\"\"

    Reply ONLY with 'Yes' if it is medical-related, or 'No' if it is not.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        val_response = model.generate_content(validation_prompt)
        text = val_response.text.strip().lower()
        return "yes" in text
    except Exception as e:
        print(f"Validation fallback due to: {e}")
        return not response_text.startswith("NOT_MEDICAL")

@app.route('/', methods=['GET', 'POST'])
def index():
    current_key = get_api_key()
    api_key_configured = bool(current_key and current_key != "your_google_api_key_here")
    response_text = None
    response_html = None
    image_preview = None
    error_message = None
    is_warning = False
    used_model = None

    if request.method == 'POST':
        # Retrieve API key from form or session
        user_key = request.form.get('api_key', '').strip()
        if user_key:
            current_key = user_key
            os.environ["GOOGLE_API_KEY"] = user_key
            session["api_key"] = user_key
            api_key_configured = True
            save_api_key_to_env(user_key)

        if not current_key or current_key == "your_google_api_key_here":
            error_message = "Google API Key is required. Please enter it in the form below or add it to .env."
            return render_template(
                'index.html',
                api_key_configured=False,
                error_message=error_message
            )

        if 'file' not in request.files or request.files['file'].filename == '':
            error_message = "Please select an image file to upload."
            return render_template(
                'index.html',
                api_key_configured=api_key_configured,
                error_message=error_message
            )

        uploaded_file = request.files['file']
        try:
            image_bytes = uploaded_file.read()
            image = Image.open(io.BytesIO(image_bytes))

            # Base64 data URI for image preview
            mime_type = Image.MIME.get(image.format, "image/png")
            b64_str = base64.b64encode(image_bytes).decode('utf-8')
            image_preview = f"data:{mime_type};base64,{b64_str}"

            image_prompt = """
            You are an AI assistant designed to analyze medical and healthcare imagery.
            First, assess if the provided image is related to medicine, healthcare, biology, pharmacy, anatomy, or diagnostic imaging (e.g. X-ray, MRI, CT scan, ultrasound, skin lesion, microscope slide, medicine packaging, prescription, clinic note, lab report, etc.).

            If the image is clearly unrelated to medicine (such as cars, landscapes, animals, memes, electronics, cartoons, general objects):
            Reply strictly with:
            NOT_MEDICAL: This image does not appear to be a medical image. Please upload a valid medical image (such as an X-ray, CT scan, MRI, prescription, medicine box, or clinical photo).

            If the image IS related to medical or healthcare:
            Provide a thorough, professional, and well-structured medical analysis formatted in Markdown:
            ### 1. Document / Image Overview & Modality
            Identify what type of medical image or document this is (e.g., Clinic Prescription Memo, Chest Radiograph, Dermatology close-up, Medication packaging, Lab report).

            ### 2. Clinical Observations & Extracted Details
            Describe all visible findings, medications, dosages, clinic/patient details if legible, anatomical structures, or notable details.

            ### 3. Potential Interpretations / Differential Considerations
            Outline what medical conditions, symptoms, or findings these observations indicate.

            ### 4. Recommended Next Steps & Clinical Correlation
            Suggest standard clinical follow-ups, specialist consultations, or actions that may be appropriate.

            ---
            **Disclaimer:** *This analysis is generated by AI for educational and informational purposes only. It does not replace professional medical advice, diagnosis, or treatment. Always consult a licensed physician or healthcare provider for medical concerns.*
            """

            # Run analysis with automatic model fallback
            raw_response, used_model, err = analyze_image_with_fallback(current_key, image, image_prompt)

            if err:
                error_message = err
            elif raw_response:
                # Step 2: Validate medical context
                is_valid_medical = validate_medical_content(current_key, used_model, raw_response)

                if is_valid_medical:
                    response_text = raw_response
                    response_html = markdown.markdown(
                        response_text,
                        extensions=['extra', 'sane_lists']
                    )
                else:
                    is_warning = True
                    if "NOT_MEDICAL:" in raw_response:
                        response_text = raw_response.replace("NOT_MEDICAL:", "").strip()
                    else:
                        response_text = "The uploaded image does not appear to be related to the medical field. Please provide a valid medical image (e.g., X-ray, MRI, CT scan, prescription, or clinical photo)."
                    response_html = f"<p>{response_text}</p>"

        except Exception as e:
            error_message = f"An error occurred while processing the image: {str(e)}"

    return render_template(
        'index.html',
        api_key_configured=api_key_configured,
        response_text=response_text,
        response_html=response_html,
        image_preview=image_preview,
        error_message=error_message,
        is_warning=is_warning,
        used_model=used_model
    )

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    print(f"Starting Medicine Recognition System on http://127.0.0.1:{port} ...")
    app.run(host="0.0.0.0", port=port, debug=True)
