# app.py - Flask Backend for Signboard Translator with Database
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_migrate import Migrate
import cv2
import numpy as np
import pytesseract
from googletrans import Translator
import os
from werkzeug.utils import secure_filename
import base64
from PIL import Image, ImageDraw, ImageFont
import io
import json
import time
import uuid
from datetime import datetime
from models import db, User, Translation, UserSession
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = Flask(__name__)
CORS(app, supports_credentials=True)  # Enable CORS with credentials

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///signboard_translator.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize database
db.init_app(app)
migrate = Migrate(app, db)

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize translator
translator = Translator()

def get_or_create_session():
    """Get existing session or create new one"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        
        # Create session record
        user_session = UserSession(
            session_id=session['session_id'],
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        db.session.add(user_session)
        db.session.commit()
    
    return session['session_id']

def update_session_activity():
    """Update last activity timestamp"""
    if 'session_id' in session:
        user_session = UserSession.query.filter_by(session_id=session['session_id']).first()
        if user_session:
            user_session.last_activity = datetime.utcnow()
            db.session.commit()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image(image):
    """Preprocess image for better OCR results"""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    
    # Morphological operations to clean up the image
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    return cleaned

def extract_text_with_positions(image):
    """Extract text and their positions from image using OCR"""
    try:
        # Get detailed data including bounding boxes
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        text_blocks = []
        for i in range(len(data['text'])):
            if int(data['conf'][i]) > 1:  # Confidence threshold
                text = data['text'][i].strip()
                if text and len(text) > 1:  # Only process non-empty text with more than 1 character
                    text_blocks.append({
                        'text': text,
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i],
                        'confidence': data['conf'][i]
                    })
        
        return text_blocks
    except Exception as e:
        print(f"OCR Error: {e}")
        return []

def translate_text(text, target_language='en'):
    """Translate text to target language"""
    try:
        if not text.strip():
            return text
        
        # Skip translation if text is too short or contains only numbers/symbols
        if len(text.strip()) < 2 or text.isdigit():
            return text
            
        print(f"Translating: '{text}' to {target_language}")
        
        # Detect source language and translate
        result = translator.translate(text, dest=target_language)
        
        print(f"Translation result: '{result.text}' (detected: {result.src})")
        
        # If source and destination are the same, return original
        if result.src == target_language:
            return text
            
        return result.text
    except Exception as e:
        print(f"Translation Error for '{text}': {e}")
        return text  # Return original text if translation fails
print("Using database:", app.config['SQLALCHEMY_DATABASE_URI'])

def create_translated_image(original_image, text_blocks):
    """Create image with translated text overlaid"""
    try:
        # Convert OpenCV image to PIL
        if len(original_image.shape) == 3:
            image_rgb = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = cv2.cvtColor(original_image, cv2.COLOR_GRAY2RGB)
        
        pil_image = Image.fromarray(image_rgb)
        draw = ImageDraw.Draw(pil_image)
        
        # Try to use a font, fallback to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        for block in text_blocks:
            if block.get('translated_text') and block['translated_text'] != block['text']:
                x, y = block['x'], block['y']
                width, height = block['width'], block['height']
                
                # Create background rectangle for better readability
                draw.rectangle(
                    [x-2, y-2, x + width + 2, y + height + 2], 
                    fill='white', 
                    outline='black'
                )
                
                # Draw translated text
                draw.text(
                    (x, y), 
                    block['translated_text'], 
                    fill='black', 
                    font=font
                )
        
        return pil_image
    except Exception as e:
        print(f"Image creation error: {e}")
        return None

@app.route('/api/translate', methods=['POST'])
def translate_image():
    """Main endpoint to process and translate image"""
    start_time = time.time()
    session_id = get_or_create_session()
    update_session_activity()
    
    try:
        # Check if image is provided
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Get target language from request (default to English)
        target_language = request.form.get('target_language', 'en')
        print(f"Target language: {target_language}")
        
        # Get file info
        original_filename = secure_filename(file.filename)
        file_content = file.read()
        file_size = len(file_content)
        
        # Read image
        file_bytes = np.frombuffer(file_content, np.uint8)
        original_image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        if original_image is None:
            return jsonify({'error': 'Invalid image file'}), 400
        
        # Get image dimensions
        height, width = original_image.shape[:2]
        image_dimensions = f"{width}x{height}"
        
        print(f"Processing image: {original_filename} ({image_dimensions})")
        
        # Preprocess image for better OCR
        processed_image = preprocess_image(original_image)
        
        # Extract text with positions
        text_blocks = extract_text_with_positions(processed_image)
        print(f"Extracted {len(text_blocks)} text blocks")
        
        if not text_blocks:
            # Save translation record even if no text found
            translation_record = Translation.create_from_result(
                filename=original_filename,
                file_size=file_size,
                dimensions=image_dimensions,
                original_texts=[],
                translated_texts=[],
                confidence_scores=[],
                processing_time=time.time() - start_time,
                session_id=session_id
            )
            db.session.add(translation_record)
            db.session.commit()
            
            return jsonify({
                'message': 'No text detected in the image',
                'translation_id': translation_record.id,
                'original_texts': [],
                'translated_texts': [],
                'processed_image': None
            })
        
        # Print original texts
        original_texts = [block['text'] for block in text_blocks]
        print(f"Original texts: {original_texts}")
        
        # Translate each text block
        translated_texts = []
        for i, block in enumerate(text_blocks):
            original_text = block['text']
            translated = translate_text(original_text, target_language)
            block['translated_text'] = translated
            translated_texts.append(translated)
            print(f"Block {i+1}: '{original_text}' -> '{translated}'")
        
        print(f"Final - Original: {original_texts}")
        print(f"Final - Translated: {translated_texts}")
        
        # Create image with translations
        result_image = create_translated_image(original_image, text_blocks)
        
        # Convert result image to base64 for frontend
        processed_image_base64 = None
        if result_image:
            buffer = io.BytesIO()
            result_image.save(buffer, format='PNG')
            processed_image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Prepare confidence scores
        confidence_scores = [block['confidence'] for block in text_blocks]
        
        # Save translation to database
        translation_record = Translation.create_from_result(
            filename=original_filename,
            file_size=file_size,
            dimensions=image_dimensions,
            original_texts=original_texts,
            translated_texts=translated_texts,
            confidence_scores=confidence_scores,
            processing_time=time.time() - start_time,
            session_id=session_id
        )
        db.session.add(translation_record)
        db.session.commit()
        
        return jsonify({
            'message': 'Translation completed successfully',
            'translation_id': translation_record.id,
            'original_texts': original_texts,
            'translated_texts': translated_texts,
            'text_blocks': text_blocks,
            'processed_image': processed_image_base64,
            'processing_time': round(time.time() - start_time, 2)
        })
        
    except Exception as e:
        print(f"Error in translate_image: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/api/history', methods=['GET'])
def get_translation_history():
    """Get translation history for current session"""
    session_id = get_or_create_session()
    update_session_activity()
    
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)  # Max 50 per page
        
        # Query translations for current session
        translations = Translation.query.filter_by(session_id=session_id)\
                                      .order_by(Translation.created_at.desc())\
                                      .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'translations': [t.to_dict() for t in translations.items],
            'total': translations.total,
            'pages': translations.pages,
            'current_page': page,
            'has_next': translations.has_next,
            'has_prev': translations.has_prev
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch history: {str(e)}'}), 500

@app.route('/api/history/<int:translation_id>', methods=['GET'])
def get_translation_detail(translation_id):
    """Get detailed information about a specific translation"""
    session_id = get_or_create_session()
    update_session_activity()
    
    try:
        translation = Translation.query.filter_by(
            id=translation_id, 
            session_id=session_id
        ).first()
        
        if not translation:
            return jsonify({'error': 'Translation not found'}), 404
        
        return jsonify(translation.to_dict())
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch translation: {str(e)}'}), 500

@app.route('/api/history/<int:translation_id>', methods=['DELETE'])
def delete_translation(translation_id):
    """Delete a translation from history"""
    session_id = get_or_create_session()
    update_session_activity()
    
    try:
        translation = Translation.query.filter_by(
            id=translation_id,
            session_id=session_id
        ).first()
        
        if not translation:
            return jsonify({'error': 'Translation not found'}), 404
        
        db.session.delete(translation)
        db.session.commit()
        
        return jsonify({'message': 'Translation deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': f'Failed to delete translation: {str(e)}'}), 500

@app.route('/api/history/clear', methods=['DELETE'])
def clear_history():
    """Clear all translation history for current session"""
    session_id = get_or_create_session()
    update_session_activity()
    
    try:
        deleted_count = Translation.query.filter_by(session_id=session_id).delete()
        db.session.commit()
        
        return jsonify({
            'message': f'Cleared {deleted_count} translations from history'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to clear history: {str(e)}'}), 500

@app.route('/api/stats', methods=['GET'])
def get_session_stats():
    """Get statistics for current session"""
    session_id = get_or_create_session()
    update_session_activity()
    
    try:
        translations = Translation.query.filter_by(session_id=session_id).all()
        
        if not translations:
            return jsonify({
                'total_translations': 0,
                'total_processing_time': 0,
                'average_processing_time': 0,
                'total_texts_translated': 0,
                'languages_detected': []
            })
        
        total_translations = len(translations)
        total_processing_time = sum(t.processing_time or 0 for t in translations)
        total_texts = sum(len(json.loads(t.original_texts)) for t in translations if t.original_texts)
        languages = list(set(t.detected_language for t in translations if t.detected_language))
        
        return jsonify({
            'total_translations': total_translations,
            'total_processing_time': round(total_processing_time, 2),
            'average_processing_time': round(total_processing_time / total_translations, 2),
            'total_texts_translated': total_texts,
            'languages_detected': languages,
            'first_translation': translations[-1].created_at.isoformat() if translations else None,
            'latest_translation': translations[0].created_at.isoformat() if translations else None
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch stats: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Signboard Translator API is running'})

@app.route('/', methods=['GET'])
def home():
    """Root endpoint"""
    return jsonify({
        'message': 'Signboard Translator API with Database',
        'endpoints': {
            '/api/translate': 'POST - Upload image for translation',
            '/api/history': 'GET - Get translation history',
            '/api/history/<id>': 'GET/DELETE - Get or delete specific translation',
            '/api/history/clear': 'DELETE - Clear all history',
            '/api/stats': 'GET - Get session statistics',
            '/api/health': 'GET - Health check'
        }
    })

def create_tables():
    """Create database tables"""
    db.create_all()

if __name__ == '__main__':
    print("Starting Signboard Translator API with Database...")
    print("Make sure you have installed: pip install flask flask-cors flask-sqlalchemy flask-migrate opencv-python pytesseract googletrans==4.0.0-rc1 pillow")
    print("Also install Tesseract OCR on your system")
    
    # Create tables if they don't exist - FIXED: Using app_context instead of before_first_request
    with app.app_context():
        create_tables()
    
    app.run(debug=True, host='0.0.0.0', port=5000)